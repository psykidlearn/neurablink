import cv2
import hydra
from omegaconf import DictConfig
from PyQt6 import QtWidgets, QtGui, QtCore
import sys
from .screen import ControlWindow, BlurWindow, reset_all_windows


class CameraLoader(QtCore.QThread):
    camera_loaded = QtCore.pyqtSignal(cv2.VideoCapture)

    def run(self):
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            self.camera_loaded.emit(cap)
        else:
            print("Error: Could not access the camera.")
            sys.exit(1)


def on_camera_loaded(cap, cfg, app, control_window):
    # Create the camera manager
    camera_manager = hydra.utils.instantiate(cfg.camera_manager, cap=cap, app=app)
    camera_manager.control_window = control_window  # Pass control window reference
    control_window.change_camera_func = camera_manager.change
    camera_manager.camera_changed.connect(camera_manager.on_camera_changed)
    control_window.closeEvent = lambda event: camera_manager.stop()

    # Instantiate the frame processor
    frame_processor = hydra.utils.instantiate(
        cfg.frame_processor,
        blink_detector=control_window.blink_detector,
        cap=cap,
        app=app,
        control_window=control_window,
        camera_manager=camera_manager
    )
    control_window.frame_processor = frame_processor 

    # Initialize and start the timer for frame processing
    control_window.frame_timer = QtCore.QTimer(control_window)
    control_window.frame_timer.timeout.connect(control_window.frame_processor.process_frames)
    control_window.frame_timer.start(16)  # Approximately 60 FPS
    control_window.enable_ui_components() # Enable Start/Stop buttons + cam selector once camera is live


def main_func(cfg: DictConfig):
    # Instantiate the blink detector from configuration
    blink_detector = hydra.utils.instantiate(cfg.blink_detector)

    # Initialize the Qt application and setup UI components
    try:
        icon_path = hydra.utils.instantiate(cfg.icon_path)
    except Exception as e:
        print(e)
        icon_path = cfg.icon_path
    app = QtWidgets.QApplication([])
    if not QtGui.QIcon(icon_path).isNull():
        app.setWindowIcon(QtGui.QIcon(icon_path))
    else:
        print(f"Warning: Icon file not found at {icon_path}")

    # Create blur windows for all screens
    blur_windows = [
        BlurWindow(screen) for screen in app.screens()
    ]
    for blur_window in blur_windows:
        blur_window.setGeometry(blur_window.screen().geometry())
        blur_window.hide()  # Initially hidden

    # Connect the blink detector signal to reset blur windows
    try:
        blink_detector.module.blink_detected.connect(lambda: reset_all_windows(blur_windows))
    except AttributeError as e:
        print(f"Blink detector signal connection failed: {e}")

    # Create the control window
    control_window = ControlWindow(
        blur_windows=blur_windows,
        icon_path=icon_path,
        change_camera_func=None,
        blink_detector=blink_detector,
        frame_processor=None #frame processor will be instantiated later
        )
    control_window.show()
    app.processEvents()  # Force the GUI to update

    # Initialize OpenCV VideoCapture
    print("Getting your camera stream. This may take a second...")
    camera_loader = CameraLoader()
    camera_loader.camera_loaded.connect(lambda cap: on_camera_loaded(cap, cfg, app, control_window))
    camera_loader.start()

    # Run application
    control_window.show()
    app.exec()

    # Release camera on exit
    # if cap.isOpened():
    #     cap.release()


if __name__ == "__main__":
    main_func()