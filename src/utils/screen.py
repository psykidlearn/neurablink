from PyQt6 import QtWidgets, QtGui, QtCore
import cv2
from .widgets import CameraSelectionWidget, BlinkTimerWidget, DetectionSensitivityWidget, ButtonLayout   


class ControlWindow(QtWidgets.QWidget):
    def __init__(self, blur_windows, icon_path:str, change_camera_func, blink_detector):
        super().__init__()
        self.blur_windows = blur_windows
        self.change_camera_func = change_camera_func # Function to change the camera feed
        self.blink_detector = blink_detector
        self.available_cameras = self.get_available_cameras()
        self.initUI(icon_path)
        self.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        self.is_running = False  # track application state

    def initUI(self, icon_path:str):
        self.setWindowTitle('Neurablink - Control Panel')
        self.setGeometry(100, 100, 400, 300)  # Slightly larger default size

        # Set window icon
        icon = QtGui.QIcon(icon_path) 
        self.setWindowIcon(icon)

        # Main layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)  # margins
        self.layout.setSpacing(15)  # spacing between widgets

        # Title label
        self.title_label = QtWidgets.QLabel('Neurablink - Blink Detector')
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86C1;")
        self.layout.addWidget(self.title_label)

        # Define common minimum width for widget alignment
        common_min_width = 200

        # Camera selection layout   
        self.camera_selection_widget = CameraSelectionWidget(
            available_cameras=self.available_cameras, 
            parent=None,
            common_min_width=common_min_width
            )
        self.layout.addWidget(self.camera_selection_widget)
        self.camera_selection_widget.camera_combo.currentIndexChanged.connect(self.on_camera_selection_changed) # Connect camera selection change signal

        # Blink Timer setting layout
        self.blink_timer_widget = BlinkTimerWidget(
            initial_delay_seconds=5,
            parent=None,
            common_min_width=common_min_width,
            connect_func=self.update_initial_delay
            )
        self.layout.addWidget(self.blink_timer_widget)

        # Quantile setting layout
        self.detection_sensitivity_widget = DetectionSensitivityWidget(
            initial_quantile_index=4,
            parent=None,
            common_min_width=common_min_width,
            connect_func=self.update_quantile
            )
        self.layout.addWidget(self.detection_sensitivity_widget)

        # Add camera live feed
        self.camera_label = QtWidgets.QLabel()
        self.camera_label.setMinimumSize(320, 240)  # Adjust size as needed
        self.camera_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.camera_label)

        # Description label
        self.description_label = QtWidgets.QLabel(
            'Press "Start" to begin the blink detection tracking.\n'
            'Press "Stop" to halt the process and clear the screen.'
        )
        self.description_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.description_label.setStyleSheet("font-size: 14px; color: #5D6D7E;")
        self.layout.addWidget(self.description_label)

        # Button layout
        self.button_layout = ButtonLayout(
            start_callback=self.start_application, 
            stop_callback=self.stop_application
            )
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)
        self.update_styles()
        self.show()

    def resizeEvent(self, event):
        self.update_styles()
        super().resizeEvent(event)

    def update_styles(self):
        width = self.width()

        # Update font sizes based on window size
        title_font_size = max(14, width // 20)
        description_font_size = max(12, width // 30)

        # Update styles
        self.title_label.setStyleSheet(f"font-size: {title_font_size}px; font-weight: bold; color: #2E86C1;")
        self.description_label.setStyleSheet(f"font-size: {description_font_size}px; color: #5D6D7E;")
        self.button_layout.update_styles(width)
        self.camera_selection_widget.update_styles(width)   
        self.blink_timer_widget.update_styles(width)
        self.detection_sensitivity_widget.update_styles(width)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Space):
            event.ignore()  # Ignore the Enter and Space key presses
        else:
            super().keyPressEvent(event)

    def start_application(self):
        self.is_running = True # update application state
        reset_all_windows(self.blur_windows)  # Reset all windows before starting
        for window in self.blur_windows:
            window.showFullScreen()
            window.start_opacity()  # Start the blurring process

        # Disable Start button, camera switching, blink timer and detection sensitivity changes
        self.camera_selection_widget.start()
        self.blink_timer_widget.start()
        self.detection_sensitivity_widget.start()
        self.button_layout.start()

    def stop_application(self):
        self.is_running = False # update application state
        for window in self.blur_windows:
            window.hide()

        # Re-enable the start button, restore its original appearance, and update its text
        self.camera_selection_widget.stop()
        self.blink_timer_widget.stop()
        self.detection_sensitivity_widget.stop()
        self.button_layout.stop()   

    def closeEvent(self, event):
        #Closing control window will stop the application
        self.stop_application()  
        event.accept()  
    
    def update_initial_delay(self, value):
        self.initial_delay_seconds = value
        for window in self.blur_windows:
            window.initial_delay_seconds = value 

    def get_available_cameras(self):
        """Get a list of available cameras"""
        available_cameras = []
        # We assume that users have not more than 5 cameras
        for index in range(5):  
            try:
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # Specify backend
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        available_cameras.append(f"Camera {index}")
                    cap.release()
            except:
                continue
        
        # If no cameras found, add "No camera found" option
        if not available_cameras:
            available_cameras.append("No camera found")
        
        return available_cameras
    
    def on_camera_selection_changed(self, index):
        """Handle camera selection change."""
        self.change_camera_func(index)

    def update_camera_feed(self, frame):
        # Convert frame to QImage
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QtGui.QImage(frame.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        # Convert to QPixmap and scale to fit the label
        pixmap = QtGui.QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.camera_label.setPixmap(scaled_pixmap)
    
    def update_quantile(self, value):
        quantile_values = [0.99, 0.975, 0.96, 0.945, 0.93]
        selected_quantile = quantile_values[value - 1]
        self.blink_detector.module.calibrator.quantile = selected_quantile #affects detector as it is passed by reference

    
class BlurWindow(QtWidgets.QWidget):
    def __init__(self, screen):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint | QtCore.Qt.WindowType.ToolTip)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Get screen size
        self.setGeometry(screen.geometry())

        # Timer for gradual blur
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.increase_opacity)

        # Opacity settings
        self.opacity_level = 0
        self.max_opacity_level = 155  # Maximum opacity level
        self.opacity_step = 3  # Opacity increment per step

        # Timer for initial delay
        self.initial_delay_timer = QtCore.QTimer()
        self.initial_delay_timer.timeout.connect(self.start_opacity_increase)
        self.initial_delay_seconds = 5  # Delay in seconds before opacity starts increasing

        # Start the initial delay timer
        #self.initial_delay_timer.start(self.initial_delay_seconds * 1000)

    def start_opacity(self):
        #Called by control window to start the application
        self.reset_opacity()  # Ensure opacity is reset before starting
        self.initial_delay_timer.start(self.initial_delay_seconds * 1000)  # Start the initial delay timer
    
    def start_opacity_increase(self):
        self.initial_delay_timer.stop()
        self.timer.start(50)  # Start the opacity increase timer

    @QtCore.pyqtSlot()
    def reset_opacity(self):
        self.opacity_level = 0
        self.timer.stop()  # Stop the opacity increase timer
        self.initial_delay_timer.start(self.initial_delay_seconds * 1000)  # Restart the initial delay timer
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, self.opacity_level))
        painter.end()
    
    def increase_opacity(self): 
        if self.opacity_level < self.max_opacity_level:
            self.opacity_level += self.opacity_step
            self.update()
        else:
            self.timer.stop()


def reset_all_windows(blur_windows):  
    for window in blur_windows:
        # Use invokeMethod to ensure the method is called in the correct thread
        QtCore.QMetaObject.invokeMethod(window, "reset_opacity", QtCore.Qt.ConnectionType.QueuedConnection)


def main():
    app = QtWidgets.QApplication([])
    app.setWindowIcon(QtGui.QIcon("C:/Users/s_gue/Desktop/projects/neurablink/src/files/icon.png"))
    blur_windows = []
    for screen in app.screens():
        blur_window = BlurWindow(screen)
        blur_window.setGeometry(screen.geometry())  # Set the geometry to the screen's geometry
        blur_window.showFullScreen()  # Show the window in full screen mode
        blur_windows.append(blur_window)

    control_window = ControlWindow(blur_windows)
    #keyboard.add_hotkey('space', reset_all_windows, args=(blur_windows,)) # Debugging
    app.exec()

if __name__ == "__main__":
    main() 