import cv2
import sys
from PyQt6 import QtWidgets

class CameraManager:
    def __init__(self, cap: cv2.VideoCapture, app: QtWidgets.QApplication) -> None:
        self.cap = cap
        self.app = app

    def stop(self):
        if self.cap.isOpened():
            self.cap.release()
        self.app.quit()
        sys.exit()

    def change(self, camera_index):
        """Change the camera feed to the selected camera."""
        if self.cap.isOpened():
            self.cap.release()
        self.cap.open(camera_index)
        if not self.cap.isOpened():
            print(f"Error: Could not access camera {camera_index}.")
            self.stop()