import cv2
import numpy as np
from PyQt6 import QtWidgets
from utils.screen import ControlWindow
from utils.detector import BufferedModule
from utils.camera import CameraManager

class FrameProcessor:
    def __init__(
            self, 
            blink_detector: 'BufferedModule', 
            cap: cv2.VideoCapture, 
            app: QtWidgets.QApplication, 
            control_window: 'ControlWindow', 
            camera_manager: 'CameraManager',
            highlight_intensity: int = 100
            ) -> None:
        self.blink_detector = blink_detector
        self.cap = cap
        self.app = app
        self.control_window = control_window
        self.camera_manager = camera_manager
        self.highlight_intensity = highlight_intensity  # Adjust to reduce or increase highlight intensity

    def process_frames(self):
        """
        Process frames from the camera and update the camera feed in the control window.
        """
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read from the camera.")
                self.camera_manager.stop()
                return
            
            is_blink = self.blink_detector(frame) # Detect blink
            eye_mask = self.blink_detector.module.eye_detector.create_eye_mask(frame)

            # Highlight eyes area
            if is_blink:
                frame[eye_mask, 2] = np.clip(frame[eye_mask, 2] + self.highlight_intensity, 0, 255) # Increase red
            else:
                frame[eye_mask, 1] = np.clip(frame[eye_mask, 0] + self.highlight_intensity, 0, 255) # Increase green

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # Convert BGR to RGB for Qt display
            self.control_window.update_camera_feed(rgb_frame) # Update camera feed