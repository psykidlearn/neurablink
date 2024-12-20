import cv2
import hydra
from omegaconf import DictConfig
from PyQt6 import QtWidgets, QtGui, QtCore
import sys
from .screen import ControlWindow, BlurWindow, reset_all_windows



def main_func(cfg: DictConfig):
    # Instantiate the blink detector from configuration
    blink_detector = hydra.utils.instantiate(cfg.blink_detector)

    # Initialize OpenCV VideoCapture
    print("Getting your camera stream. This may take a second...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access the camera.")
        sys.exit(1)

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

    # Create the camera manager
    camera_manager = hydra.utils.instantiate(cfg.camera_manager, cap=cap, app=app)

    # Create the control window
    control_window = ControlWindow(
        blur_windows=blur_windows,
        icon_path=icon_path,
        change_camera_func=camera_manager.change,
        blink_detector=blink_detector,
        frame_processor=None #frame processor will be instantiated later
        )
    control_window.closeEvent = lambda event: camera_manager.stop()

    # Instantiate the frame processor
    frame_processor = hydra.utils.instantiate(
        cfg.frame_processor,
        blink_detector=blink_detector,
        cap=cap,
        app=app,
        control_window=control_window,
        camera_manager=camera_manager
    )
    control_window.frame_processor = frame_processor 

    # Timer to periodically process frames (non-blocking GUI)
    timer = QtCore.QTimer()
    timer.timeout.connect(frame_processor.process_frames)
    timer.start(16)  # Approximately 60 FPS

    # Run application
    control_window.show()
    app.exec()

    # Release camera on exit
    if cap.isOpened():
        cap.release()


if __name__ == "__main__":
    main_func()