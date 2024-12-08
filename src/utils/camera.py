from PyQt6 import QtWidgets, QtGui, QtCore
import cv2
import sys


class CameraManager:
    """
    Manage camera operations, like stopping and changing cameras.
    """
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


class CameraFeed(QtWidgets.QLabel):
    """
    Widget to display the camera feed in the application.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)  # Adjust size as needed
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def update_camera_feed(self, frame):
        # Convert frame to QImage
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        # Convert to QPixmap and scale to fit the label
        pixmap = QtGui.QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(scaled_pixmap)