from PyQt6 import QtWidgets, QtGui, QtCore
import cv2
import sys


class CameraManager(QtCore.QThread):
    """
    Thread to manage camera access and change.
    """
    camera_changed = QtCore.pyqtSignal(bool)

    def __init__(self, cap: cv2.VideoCapture, app: QtWidgets.QApplication) -> None:
        super().__init__()
        self.cap = cap
        self.app = app
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) if self.cap else None
        self.camera_index = None

    def stop(self):
        """Release the camera and perform cleanup."""
        if self.cap.isOpened():
            self.cap.release()
        self.quit()  # Stop the QThread
        self.wait()  # Wait for the thread to finish
        
    def change(self, camera_index):
        """Initiate the camera change in a separate thread."""
        if hasattr(self, 'control_window'):
            self.control_window.disable_ui_components()  # Disable UI components
            self.control_window.camera_feed.show_initial_message()  # Show initializing message
        self.camera_index = camera_index
        self.start()  # This triggers the run() method

    def run(self):
        """Perform the camera change operation."""
        if self.cap.isOpened():
            self.cap.release()
        success = self.cap.open(self.camera_index)
        self.camera_changed.emit(success)

    def on_camera_changed(self, success):
        """Handle the result of the camera change."""
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) if success else None
        if not success:
            print(f"Error: Could not access camera {self.camera_index}.")
            self.stop()
        else:
            if hasattr(self, 'control_window'):
                self.control_window.enable_ui_components()
                self.control_window.camera_feed.hide_initial_message()  # Hide initializing message


class CameraFeed(QtWidgets.QWidget):
    """
    Widget to display the camera feed in the application.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)  # Adjust size as needed

        # Camera feed label
        self.camera_label = QtWidgets.QLabel()
        self.camera_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Initial message widget
        self.message_widget = QtWidgets.QWidget()
        self.message_widget.setStyleSheet("background-color: black;")

        # Main message label
        self.message_label = QtWidgets.QLabel("Initializing your camera. \nThis may take a few seconds.", self.message_widget)
        self.message_label.setStyleSheet("color: white; font-size: 16px;")
        self.message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Dots label
        self.dots_label = QtWidgets.QLabel("", self.message_widget)
        self.dots_label.setStyleSheet("color: white; font-size: 32px;")
        self.dots_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Layout to position labels in message_widget
        message_layout = QtWidgets.QVBoxLayout(self.message_widget)
        message_layout.addStretch()
        message_layout.addWidget(self.message_label)
        message_layout.addWidget(self.dots_label)
        message_layout.addStretch()
        self.message_widget.setLayout(message_layout)

        # Stack layout to switch between camera feed and message
        self.stack_layout = QtWidgets.QStackedLayout(self)
        self.stack_layout.addWidget(self.message_widget)  # Index 0
        self.stack_layout.addWidget(self.camera_label)     # Index 1
        self.setLayout(self.stack_layout)

        # Timer for animated text
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.update_initial_message)
        
        self.show_initial_message()

    def show_initial_message(self):
        """Display the initializing message and start the animation."""
        self.stack_layout.setCurrentIndex(0)  # Show message_widget
        self.message_label.show()
        self.dots_label.show()
        self.animation_timer.start(500)  # Update every 500ms

    def update_initial_message(self):
        """Animate the dots below the initial message."""
        current_text = self.dots_label.text()
        if current_text.endswith("..."):
            self.dots_label.setText("")
        else:
            self.dots_label.setText(current_text + ".")

    def hide_initial_message(self):
        """Hide the initializing message and stop the animation."""
        self.animation_timer.stop()
        self.message_label.hide()
        self.dots_label.hide()
        self.stack_layout.setCurrentIndex(1)  # Show camera_label
       
    def update_camera_feed(self, frame):
        """Update the camera feed with the new frame."""
        # Display the camera feed only if the initializing message is hidden
        if self.stack_layout.currentIndex() != 1:
            self.hide_initial_message()  # Stop animation once camera feed is ready

        # Convert frame to QImage
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        
        # Convert to QPixmap and scale to fit the label
        pixmap = QtGui.QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.camera_label.setPixmap(scaled_pixmap)