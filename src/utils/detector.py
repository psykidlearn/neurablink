import cv2
import numpy as np
import mediapipe as mp
import pickle
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Callable, Dict, List, Optional, Tuple
import copy

class BaseEyeLandmarksDetector:

    def get_eye_landmarks(self, frame: np.ndarray) -> Dict[str, List[Tuple[int, int]]]:
        raise NotImplementedError

    def create_eye_mask(self, frame: np.ndarray, side: str = 'left+right') -> np.ndarray:
        raise NotImplementedError


class FaceMeshLandmarksDetector(BaseEyeLandmarksDetector):
    LEFT_EYE_LANDMARKS: List[int] = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_LANDMARKS: List[int] = [362, 385, 387, 263, 373, 380]

    def __init__(self, mask_size: int, default_landmarks_path: str) -> None:
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=True
        )
        self.mask_size = mask_size
        with open(default_landmarks_path, "rb") as f:
            self.face_landmarks = pickle.load(f)

    def get_eye_landmarks(self, frame: np.ndarray) -> Dict[str, List[Tuple[int, int]]]:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        eye_landmarks = {'left_eye': [], 'right_eye': []}

        if results.multi_face_landmarks:  # use prev landmarks as default
            self.face_landmarks = results.multi_face_landmarks[0]

        eye_landmarks['left_eye'] = [
            (int(self.face_landmarks.landmark[i].x * frame.shape[1]),
             int(self.face_landmarks.landmark[i].y * frame.shape[0]))
            for i in self.LEFT_EYE_LANDMARKS
        ]
        eye_landmarks['right_eye'] = [
            (int(self.face_landmarks.landmark[i].x * frame.shape[1]),
             int(self.face_landmarks.landmark[i].y * frame.shape[0]))
            for i in self.RIGHT_EYE_LANDMARKS
        ]
        return eye_landmarks

    def create_eye_mask(self, frame: np.ndarray, side: str = 'left+right') -> np.ndarray:
        landmarks = self.get_eye_landmarks(frame)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)

        if landmarks['left_eye'] and 'left' in side:
            cv2.fillPoly(mask, [np.array(landmarks['left_eye'], dtype=np.int32)], 1)
        if landmarks['right_eye'] and 'right' in side:
            cv2.fillPoly(mask, [np.array(landmarks['right_eye'], dtype=np.int32)], 1)

        return mask.astype(bool)

    def create_eye_center_mask(self, frame: np.ndarray) -> np.ndarray:
        landmarks = self.get_eye_landmarks(frame)
        mask = np.zeros(frame.shape[:2], dtype=bool)
        center_right = np.array(landmarks['right_eye'], dtype=np.int32).mean(0)
        center_left = np.array(landmarks['left_eye'], dtype=np.int32).mean(0)

        slice_right_y = slice(
            int(center_right[0]) - self.mask_size // 2,
            int(center_right[0]) + self.mask_size // 2
        )
        slice_right_x = slice(
            int(center_right[1]) - self.mask_size // 2,
            int(center_right[1]) + self.mask_size // 2
        )
        slice_left_y = slice(
            int(center_left[0]) - self.mask_size // 2,
            int(center_left[0]) + self.mask_size // 2
        )
        slice_left_x = slice(
            int(center_left[1]) - self.mask_size // 2,
            int(center_left[1]) + self.mask_size // 2
        )

        mask[slice_left_x, slice_left_y] = True
        mask[slice_right_x, slice_right_y] = True
        return mask


class BaseCalibrator:

    def reset(self) -> None:
        raise NotImplementedError

    def set_threshold(self) -> None:
        self.threshold = np.quantile(
            np.stack(self.buffer, axis=0).ravel(), self.quantile
        )

    def __call__(self, changes: np.ndarray) -> float:
        raise NotImplementedError


class OneTimeCalibrator(BaseCalibrator):

    def __init__(self, buffer_size: int, quantile: float) -> None:
        self.quantile = quantile
        self.buffer_size = buffer_size
        self.reset()

    def reset(self) -> None:
        self.buffer: List[np.ndarray] = []
        self.threshold: Optional[float] = None

    def __call__(self, changes: np.ndarray) -> float:
        if len(self.buffer) == self.buffer_size:
            if not self.threshold:
                self.set_threshold()
            return self.threshold
        self.buffer.append(changes)
        return -np.inf


class PeriodicCalibrator(BaseCalibrator):

    def __init__(self, every_nth_frame: int, buffer_size: int, quantile: float) -> None:
        self.quantile = quantile
        self.buffer_size = buffer_size
        self.every_nth_frame = every_nth_frame
        self.reset()

    def reset(self) -> None:
        self.buffer: List[np.ndarray] = []
        self.threshold: Optional[float] = None
        self.counter = 0

    def __call__(self, changes: np.ndarray) -> float:

        self.counter += 1
        if self.counter == self.every_nth_frame:
            self.reset()

        if len(self.buffer) == self.buffer_size:
            self.set_threshold()
            return self.threshold

        self.buffer.append(changes)
        return -np.inf


class ContinuousCalibrator(BaseCalibrator):

    def __init__(self, buffer_size: int, quantile: float) -> None:
        self.quantile = quantile
        self.buffer_size = buffer_size
        self.reset()

    def reset(self) -> None:
        self.buffer: List[np.ndarray] = []
        self.threshold: Optional[float] = None

    def __call__(self, changes: np.ndarray) -> float:
        self.buffer.append(changes)
        if len(self.buffer) == self.buffer_size:
            self.set_threshold()
            self.buffer.pop(0)
            return self.threshold
        return -np.inf


class BufferedModule:

    def __init__(self, module: Callable[[List[np.ndarray]], np.ndarray], buffer_size: int) -> None:
        self.module = module
        self.buffer_size = buffer_size
        self.buffer: List[np.ndarray] = []

    def __call__(self, x: np.ndarray) -> np.ndarray:
        self.buffer.append(copy.deepcopy(x))
        if self.buffer_size == len(self.buffer):
            out = self.module(self.buffer)
            self.buffer.pop(0)
            return out


class FramewiseBlinkDetector(QObject):
    blink_detected = pyqtSignal()

    def __init__(self, eye_detector: BaseEyeLandmarksDetector, calibrator: BaseCalibrator) -> None:
        super().__init__()
        self.eye_detector = eye_detector
        self.calibrator = calibrator

    def __call__(self, frames: List[np.ndarray]) -> bool:
        changes = self.compute_framewise_changes(frames)
        self.threshold = self.calibrator(changes)
        if self.is_above_threshold(changes):
            self.blink_detected.emit()
            return True
        return False

    def is_above_threshold(self, changes: np.ndarray) -> bool:
        return (changes > self.threshold).any()

    def compute_framewise_changes(self, frames: List[np.ndarray]) -> np.ndarray:
        raise NotImplementedError


class IntensityBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames: List[np.ndarray]) -> np.ndarray:
        mean_intensity: List[float] = []
        for frame in frames:
            mask = self.eye_detector.create_eye_mask(frame)
            mean_intensity.append(frame[mask].mean())
        
        mean_intensity = np.stack(mean_intensity)
        return np.abs(np.diff(mean_intensity, axis=0))


class SymmetryBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames: List[np.ndarray]) -> np.ndarray:
        mean_intensity_left: List[float] = []
        mean_intensity_right: List[float] = []
        for frame in frames:
            mask = self.eye_detector.create_eye_mask(frame, side='left')
            mean_intensity_left.append(frame[mask].mean())
            mask = self.eye_detector.create_eye_mask(frame, side='right')
            mean_intensity_right.append(frame[mask].mean())

        mean_intensity_left = np.stack(mean_intensity_left)
        changes_left = np.abs(np.diff(mean_intensity_left, axis=0))

        mean_intensity_right = np.stack(mean_intensity_right)
        changes_right = np.abs(np.diff(mean_intensity_right, axis=0))
        return changes_left * changes_right


class SurfaceBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames: List[np.ndarray]) -> np.ndarray:
        mean_size_left: List[int] = []
        mean_size_right: List[int] = []
        for frame in frames:
            mask = self.eye_detector.create_eye_mask(frame, side='left')
            mean_size_left.append(mask.sum())
            mask = self.eye_detector.create_eye_mask(frame, side='right')
            mean_size_right.append(mask.sum())

        mean_size_left = np.stack(mean_size_left)
        changes_left = np.abs(np.diff(mean_size_left, axis=0))

        mean_size_right = np.stack(mean_size_right)
        changes_right = np.abs(np.diff(mean_size_right, axis=0))
        return changes_left + changes_right


class PixelBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames: List[np.ndarray]) -> np.ndarray:
        pixels: List[np.ndarray] = []
        for frame in frames:
            mask = self.eye_detector.create_eye_center_mask(frame)
            pixels.append(frame[mask])
        
        pixels = np.stack(pixels)
        return np.abs(np.diff(pixels, axis=0)).mean()


class VerticalDistanceBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames: List[np.ndarray]) -> np.ndarray:
        vertical_distances: List[float] = []
        for frame in frames:
            landmarks = self.eye_detector.get_eye_landmarks(frame)
            if landmarks['left_eye'] and landmarks['right_eye']:
                left_eye_top = min(landmarks['left_eye'], key=lambda x: x[1])[1]
                left_eye_bottom = max(landmarks['left_eye'], key=lambda x: x[1])[1]
                right_eye_top = min(landmarks['right_eye'], key=lambda x: x[1])[1]
                right_eye_bottom = max(landmarks['right_eye'], key=lambda x: x[1])[1]

                left_eye_distance = left_eye_bottom - left_eye_top
                right_eye_distance = right_eye_bottom - right_eye_top

                vertical_distances.append((left_eye_distance + right_eye_distance) / 2)

        vertical_distances = np.array(vertical_distances)
        return np.abs(np.diff(vertical_distances, axis=0))


class UniformityBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames: List[np.ndarray]) -> np.ndarray:
        mean_size_left: List[float] = []
        mean_size_right: List[float] = []
        for frame in frames:
            mask = self.eye_detector.create_eye_mask(frame, side='left')
            mean_size_left.append(frame[mask].var(0))
            mask = self.eye_detector.create_eye_mask(frame, side='right')
            mean_size_right.append(frame[mask].var(0))

        mean_size_left = np.stack(mean_size_left)
        changes_left = np.abs(np.diff(mean_size_left, axis=0))

        mean_size_right = np.stack(mean_size_right)
        changes_right = np.abs(np.diff(mean_size_right, axis=0))
        return changes_left + changes_right


if __name__ == "__main__":
    pass