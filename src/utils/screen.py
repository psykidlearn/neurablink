from PyQt6 import QtWidgets, QtGui, QtCore
from .widgets import CameraSelectionWidget, BlinkTimerWidget, DetectionSensitivityWidget, ButtonLayout   
from .camera import CameraFeed


class ControlWindow(QtWidgets.QWidget):
    """
    Main window for controlling the application.
    """
    def __init__(self, blur_windows, icon_path:str, change_camera_func, blink_detector, frame_processor):
        super().__init__()
        self.blur_windows = blur_windows
        self.change_camera_func = change_camera_func # Function to change the camera feed
        self.blink_detector = blink_detector
        self.frame_processor = frame_processor
        self.initUI(icon_path)
        self.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
        self.is_running = False  # track application state

    def initUI(self, icon_path:str):
        """
        Initialize the UI of the control window.
        """
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
            parent=None,
            common_min_width=common_min_width
            )
        self.layout.addWidget(self.camera_selection_widget)
        self.camera_selection_widget.camera_combo.currentIndexChanged.connect(self.on_camera_selection_changed) # Connect camera selection change signal
        self.camera_selection_widget.start()  # Initially disable camera selection

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
        self.camera_feed = CameraFeed(parent=None)
        self.layout.addWidget(self.camera_feed, stretch=3)

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
        self.button_layout.upon_start() #Initially disable buttons until camera is live

        self.setLayout(self.layout)
        self.update_styles()
        self.show()

    def update_styles(self):
        """
        Update the styles of the widgets based on the window size.
        """
        width = self.width()
        height = self.height()

        # Update font sizes based on window size
        title_font_size = max(14, min(width // 20, height // 15))
        description_font_size = max(12, min(width // 40, height // 30))

        # Update styles
        self.title_label.setStyleSheet(f"font-size: {title_font_size}px; font-weight: bold; color: #2E86C1;")
        self.description_label.setStyleSheet(f"font-size: {description_font_size}px; color: #5D6D7E;")
        self.button_layout.update_styles(width, height)
        self.camera_selection_widget.update_styles(width, height)   
        self.blink_timer_widget.update_styles(width, height)
        self.detection_sensitivity_widget.update_styles(width, height)

    def start_application(self):
        """
        Behavior when the start button is pressed.
        """
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
        """
        Behavior when the stop button is pressed.
        """
        self.is_running = False # update application state
        for window in self.blur_windows:
            window.hide()

        # Re-enable the start button, restore its original appearance, and update its text
        self.camera_selection_widget.stop()
        self.blink_timer_widget.stop()
        self.detection_sensitivity_widget.stop()
        self.button_layout.stop()   

    def keyPressEvent(self, event):
        """
        Ignore the Enter and Space key presses.
        """
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter, QtCore.Qt.Key.Key_Space):
            event.ignore()  # Ignore the Enter and Space key presses
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """
        Update the styles of the widgets when the window is resized.
        """
        self.update_styles()
        super().resizeEvent(event)

    def closeEvent(self, event):
        """
        Behavior when the window is closed. 
        Closing Control Window will stop the application.
        """
        self.stop_application()  
        event.accept()  
    
    def on_camera_selection_changed(self, index):
        """Handle camera selection change."""
        self.change_camera_func(index)
        self.frame_processor.update_blink_persist_frames() #update blink persist frames based on new camera FPS

    def update_camera_feed(self, frame):
        """
        Update the camera feed with the new frame.
        """
        self.camera_feed.update_camera_feed(frame)

    def update_initial_delay(self, value):
        """
        Update the initial delay for the blurring process.
        """
        self.initial_delay_seconds = value
        for window in self.blur_windows:
            window.initial_delay_seconds = value 

    def update_quantile(self, value):
        """
        Update the quantile for the blink detection process.
        """
        quantile_values = [0.99, 0.975, 0.96, 0.945, 0.93]
        selected_quantile = quantile_values[value - 1]
        self.blink_detector.module.calibrator.quantile = selected_quantile #affects detector as it is passed by reference

    
    
class BlurWindow(QtWidgets.QWidget):
    """
    Window that blurs the screen to create blinking awareness.
    """
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

    def start_opacity(self):
        """
        Behavior when the application starts.
        """
        self.reset_opacity()  # Ensure opacity is reset before starting
        self.initial_delay_timer.start(self.initial_delay_seconds * 1000)  # Start the initial delay timer
    
    def start_opacity_increase(self):
        """
        Start the opacity increase timer.
        """
        self.initial_delay_timer.stop()
        self.timer.start(50)  # Start the opacity increase timer

    @QtCore.pyqtSlot()
    def reset_opacity(self):
        """
        Reset the opacity of the blur window.
        """
        self.opacity_level = 0
        self.timer.stop()  # Stop the opacity increase timer
        self.initial_delay_timer.start(self.initial_delay_seconds * 1000)  # Restart the initial delay timer
        self.update()

    def paintEvent(self, event):
        """
        Paint the blur window.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, self.opacity_level))
        painter.end()
    
    def increase_opacity(self): 
        """
        Increase the opacity of the blur window.
        """
        if self.opacity_level < self.max_opacity_level:
            self.opacity_level += self.opacity_step
            self.update()
        else:
            self.timer.stop()


def reset_all_windows(blur_windows):  
    """
    Reset the opacity of all blur windows.
    """
    for window in blur_windows:
        # Use invokeMethod to ensure the method is called in the correct thread
        QtCore.QMetaObject.invokeMethod(window, "reset_opacity", QtCore.Qt.ConnectionType.QueuedConnection)