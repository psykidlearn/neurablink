import cv2
import numpy as np
import mediapipe as mp


class EyeLandmarksDetector:
    LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]
    
    def __init__(self, mask_size=16):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=True
            )
        self.mask_size = mask_size

    def get_eye_landmarks(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        eye_landmarks = {'left_eye': [], 'right_eye': []}

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]
            eye_landmarks['left_eye'] = [(
                int(face_landmarks.landmark[i].x * frame.shape[1]),
                int(face_landmarks.landmark[i].y * frame.shape[0])) 
                for i in self.LEFT_EYE_LANDMARKS]
            eye_landmarks['right_eye'] = [(
                int(face_landmarks.landmark[i].x * frame.shape[1]),
                int(face_landmarks.landmark[i].y * frame.shape[0])) 
                for i in self.RIGHT_EYE_LANDMARKS]
        return eye_landmarks

    def create_eye_mask(self, frame, side='left+right'):
        landmarks = self.get_eye_landmarks(frame)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        if landmarks['left_eye'] and 'left' in side:
            cv2.fillPoly(mask, [np.array(landmarks['left_eye'], dtype=np.int32)], 1)
        if landmarks['right_eye'] and 'right' in side:
            cv2.fillPoly(mask, [np.array(landmarks['right_eye'], dtype=np.int32)], 1)
        
        return mask.astype(bool)
    
    def create_eye_center_mask(self, frame):
        landmarks = self.get_eye_landmarks(frame)
        mask = np.zeros(frame.shape[:2], dtype=bool)
        center_right = np.array(landmarks['right_eye'], dtype=np.int32).mean(0)
        center_left = np.array(landmarks['left_eye'], dtype=np.int32).mean(0)

        slice_right_y = slice(
            int(center_right[0]) - self.mask_size // 2, 
            int(center_right[0]) + self.mask_size // 2)
        slice_right_x = slice(
            int(center_right[1]) - self.mask_size // 2, 
            int(center_right[1]) + self.mask_size // 2)
        slice_left_y = slice(
            int(center_left[0]) - self.mask_size // 2, 
            int(center_left[0]) + self.mask_size // 2)
        slice_left_x = slice(
            int(center_left[1]) - self.mask_size // 2, 
            int(center_left[1]) + self.mask_size // 2)
        
        mask[slice_left_x, slice_left_y] = True
        mask[slice_right_x, slice_right_y] = True
        return mask


class FramewiseBlinkDetector:

    def __init__(self, eye_detector, threshold=None):
        self.eye_detector = eye_detector
        self.threshold = threshold

    def auto_compute_threshold(self, frames, quantile=0.95):
        assert len(frames) > 250, "need at least about 10 sec of frames"
        framewise_changes = self.compute_framewise_changes(frames)
        self.threshold = np.quantile(framewise_changes.ravel(), quantile)

    def is_event(self, frames):
        assert self.threshold, """
        either initialize with the threshold or use auto_compute_threshold
        """
        mean_intensity_changes = self.compute_framewise_changes(frames)
        return (mean_intensity_changes > self.threshold).any()

    def compute_framewise_changes(self, frames):
        raise NotImplementedError
    

class IntensityBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames):
        mean_intensity = []
        for frame in frames:
            mask = self.eye_detector.create_eye_mask(frame)
            mean_intensity.append(frame[mask].mean())
        
        mean_intensity = np.stack(mean_intensity)
        return np.abs(np.diff(mean_intensity, axis=0))
    

class SymmetryBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames):
        mean_intensity_left = []
        mean_intensity_right = []
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


class PixelBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames):
        pixels = []
        for frame in frames:
            mask = self.eye_detector.create_eye_center_mask(frame)
            pixels.append(frame[mask])
        
        pixels = np.stack(pixels)
        return np.abs(np.diff(pixels, axis=0)).mean()


if __name__ == "__main__":
    pass