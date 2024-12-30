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
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap else None  # Used for frame processing

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
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)  # Update FPS when camera changes
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

        # Main message label
        self.message_label = QtWidgets.QLabel("Initializing your camera. \n This may take a few seconds.", self)
        self.message_label.setStyleSheet("color: white; font-size: 16px;")
        self.message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Dots label
        self.dots_label = QtWidgets.QLabel("", self)
        self.dots_label.setStyleSheet("color: white; font-size: 32px;")
        self.dots_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Layout to position labels
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.message_label)
        layout.addWidget(self.dots_label)
        self.setLayout(layout)

        self.show_initial_message()

    def show_initial_message(self):
        """Display a black box with an initializing message and start the animation."""
        self.setStyleSheet("background-color: black;")
        
        # Timer for animated text
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.update_initial_message)
        self.animation_timer.start(500)  # Update every 500ms

    def update_initial_message(self):
        """Animate the dots below the initial message."""
        current_text = self.dots_label.text()
        if current_text.endswith("..."):
            self.dots_label.setText("")
        else:
            self.dots_label.setText(current_text + ".")

    def update_camera_feed(self, frame):
        # Stop the animation once the camera feed is ready
        self.animation_timer.stop()

        # Clear the initial message
        self.setStyleSheet("")
        self.message_label.hide()
        self.dots_label.hide()

        # Convert frame to QImage
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        
        # Convert to QPixmap and scale to fit the label
        pixmap = QtGui.QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(scaled_pixmap)