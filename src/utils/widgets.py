from PyQt6 import QtWidgets, QtGui, QtCore
import cv2

class CameraSelectionWidget(QtWidgets.QWidget):
    """
    Widget for selecting the camera from a list of available cameras.
    """
    def __init__(self, parent=None, common_min_width:int=200):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout()
        self.camera_label = QtWidgets.QLabel("Select Camera:")
        self.camera_label.setStyleSheet("font-size: 16px; color: #2E86C1;")
        self.layout.addWidget(self.camera_label, 3)
        self.camera_combo = QtWidgets.QComboBox()
        self.camera_combo.addItems(self.get_available_cameras())
        self.camera_combo.setStyleSheet(f"""
            QComboBox {{
                font-size: 14px;
                padding: 5px;
                border: 1px solid #BDC3C7;
                border-radius: 9px;
                min-width: {common_min_width}px;
            }}
        """)
        self.layout.addWidget(self.camera_combo)
        self.setLayout(self.layout)

    def start(self):
        self.camera_combo.setEnabled(False)  

    def stop(self):
        self.camera_combo.setEnabled(True)  

    def update_styles(self, width, height):
        camera_font_size = max(12, min(width // 40, height // 30)) 
        self.camera_label.setStyleSheet(f"font-size: {camera_font_size}px; color: #2E86C1;")
        self.camera_combo.setStyleSheet(f"""
            QComboBox {{
                font-size: {camera_font_size}px;
                padding: 5px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                min-width: {width // 3}px;
            }}
        """)
    
    def get_available_cameras(self):
        """
        Get a list of available cameras
        Note: First camera is initialized in main.py
        """
        available_cameras = []

        #Add default (first) camera
        available_cameras.append("Camera 0")

        # We assume that users have not more than 5 cameras
        for index in range(1,5):  
            #try:
            cap = cv2.VideoCapture(index)  
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(f"Camera {index}")
                cap.release()
            # except:
            #     continue
        
        # If no cameras found, raise an error and exit
        if not available_cameras:
            raise RuntimeError("No camera found. Please connect a camera and try again.")
        
        return available_cameras


class BlinkTimerWidget(QtWidgets.QWidget):
    """
    Widget for setting the blink timer.
    """
    def __init__(self, initial_delay_seconds:int=5, parent=None, common_min_width:int=200, connect_func:callable=None):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout()
        self.delay_label = QtWidgets.QLabel("Blink Timer (seconds):")
        self.delay_label.setStyleSheet("font-size: 16px; color: #2E86C1;")
        self.layout.addWidget(self.delay_label, 3)
        self.delay_spin_box = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.delay_spin_box.setRange(1, 15)
        self.delay_spin_box.setValue(initial_delay_seconds)
        self.delay_spin_box.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.delay_spin_box.setTickInterval(1)
        self.delay_spin_box.setStyleSheet(f"""
            QSlider {{
                min-width: {common_min_width}px;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #BDC3C7;
                height: 8px;
                background: #F2F3F4;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #2E86C1;
                border: 1px solid #BDC3C7;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
        """)
        self.layout.addWidget(self.delay_spin_box, 3)
        self.delay_value_label = QtWidgets.QLabel(f"{initial_delay_seconds}")
        self.delay_value_label.setStyleSheet("font-size: 14px; min-width: 30px;")
        self.delay_spin_box.valueChanged.connect(self.on_value_changed)
        self.connect_func = connect_func 
        self.layout.addWidget(self.delay_value_label)
        self.setLayout(self.layout)

    def start(self):
        self.delay_spin_box.setEnabled(False)

    def stop(self):
        self.delay_spin_box.setEnabled(True)  

    def update_styles(self, width, height):
        slider_font_size = max(12, min(width // 40, height // 30))
        self.delay_label.setStyleSheet(f"font-size: {slider_font_size}px; color: #2E86C1;")
        self.delay_value_label.setStyleSheet(f"font-size: {slider_font_size}px; min-width: 30px;")
        self.delay_spin_box.setStyleSheet(f"""
            QSlider {{
                min-width: {width // 3}px;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #BDC3C7;
                height: 8px;
                background: #F2F3F4;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #2E86C1;
                border: 1px solid #BDC3C7;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
        """)

    def on_value_changed(self, value):
        self.delay_value_label.setText(str(value))
        if self.connect_func:
            self.connect_func(value)


class DetectionSensitivityWidget(QtWidgets.QWidget):
    """
    Widget for setting the detection sensitivity.
    """
    def __init__(self, initial_quantile_index:int=4, parent=None, common_min_width:int=200, connect_func:callable=None):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout()
        self.quantile_label = QtWidgets.QLabel("Detection Sensitivity: ")
        self.quantile_label.setStyleSheet("font-size: 16px; color: #2E86C1;")
        self.layout.addWidget(self.quantile_label, 3)
        self.quantile_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.quantile_slider.setRange(1, 5)
        self.quantile_slider.setValue(initial_quantile_index)
        self.quantile_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.quantile_slider.setTickInterval(1)
        self.quantile_slider.setStyleSheet("""
            QSlider {
                min-width: 500px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #BDC3C7;
                height: 8px;
                background: #F2F3F4;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2E86C1;
                border: 1px solid #BDC3C7;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        self.layout.addWidget(self.quantile_slider, 3)
        self.quantile_value_label = QtWidgets.QLabel(str(initial_quantile_index))
        self.quantile_value_label.setStyleSheet("font-size: 14px; min-width: 30px;")
        self.quantile_slider.valueChanged.connect(self.on_value_changed)
        self.connect_func = connect_func
        self.layout.addWidget(self.quantile_value_label)
        self.setLayout(self.layout)

    def start(self):
        self.quantile_slider.setEnabled(False)

    def stop(self):
        self.quantile_slider.setEnabled(True)

    def update_styles(self, width, height):
        slider_font_size = max(12, min(width // 40, height // 30))
        self.quantile_label.setStyleSheet(f"font-size: {slider_font_size}px; color: #2E86C1;")
        self.quantile_value_label.setStyleSheet(f"font-size: {slider_font_size}px; min-width: 30px;")
        self.quantile_slider.setStyleSheet(f"""
            QSlider {{
                min-width: {width // 3}px;
            }}
            QSlider::groove:horizontal {{
                border: 1px solid #BDC3C7;
                height: 8px;
                background: #F2F3F4;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: #2E86C1;
                border: 1px solid #BDC3C7;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
        """)

    def on_value_changed(self, value):
        self.quantile_value_label.setText(str(value))  # Update the label with the current slider value
        if self.connect_func:
            self.connect_func(value)


class ButtonLayout(QtWidgets.QHBoxLayout):
    """
    Layout for the start and stop buttons.
    """
    def __init__(self, start_callback, stop_callback):
        super().__init__()
        self.setSpacing(10)

        # Start button
        self.start_button = QtWidgets.QPushButton('Start')
        self.start_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.start_button.setMinimumSize(100, 40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28B463; 
                color: white; 
                font-size: 14px; 
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #239B56;
            }
        """)
        self.start_button.clicked.connect(start_callback)
        self.addWidget(self.start_button)

        # Stop button
        self.stop_button = QtWidgets.QPushButton('Stop')
        self.stop_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.stop_button.setMinimumSize(100, 40)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #CB4335; 
                color: white; 
                font-size: 14px; 
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #B03A2E;
            }
        """)
        self.stop_button.clicked.connect(stop_callback)
        self.addWidget(self.stop_button)

    def upon_start(self):
        """Set the buttons to a disabled state with a grey appearance (until camera is loaded)."""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
    
    def start(self):
        self.start_button.setEnabled(False)
        self.start_button.setText("Detecting your Blinks...")
        self.start_button.setStyleSheet("background-color: #A9A9A9; color: grey; font-size: 14px;")

    def stop(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.start_button.setText("Start")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28B463; 
                color: white; 
                font-size: 14px; 
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #239B56;
            }
        """)

    def update_styles(self, width, height):
        button_font_size = max(12, min(width // 40, height // 30))
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #28B463; 
                color: white; 
                font-size: {button_font_size}px; 
                border-radius: 10px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #239B56;
            }}
        """)
        self.stop_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #CB4335; 
                color: white; 
                font-size: {button_font_size}px; 
                border-radius: 10px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #B03A2E;
            }}
        """)