import cv2
import numpy as np
import mediapipe as mp


class EyeLandmarksDetector:
    LEFT_EYE_LANDMARKS = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE_LANDMARKS = [362, 385, 387, 263, 373, 380]
    
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=True
            )

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

    def create_eye_mask(self, frame):
        landmarks = self.get_eye_landmarks(frame)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        if landmarks['left_eye'] and landmarks['right_eye']:
            cv2.fillPoly(mask, [np.array(landmarks['left_eye'], dtype=np.int32)], 1)
            cv2.fillPoly(mask, [np.array(landmarks['right_eye'], dtype=np.int32)], 1)
        
        return mask.astype(bool)


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
    

class FramewiseIntensityBlinkDetector(FramewiseBlinkDetector):

    def compute_framewise_changes(self, frames):
        mean_intensity = []
        for frame in frames:
            mask = self.eye_detector.create_eye_mask(frame)
            mean_intensity.append(frame[mask].mean())
        
        mean_intensity = np.stack(mean_intensity)
        return np.abs(np.diff(mean_intensity, axis=0))


if __name__ == "__main__":
    pass