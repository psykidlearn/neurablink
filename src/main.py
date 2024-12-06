import cv2
import hydra
from omegaconf import DictConfig
from PyQt6 import QtWidgets, QtGui, QtCore
from utils.screen import ControlWindow, BlurWindow, reset_all_windows
import sys


@hydra.main(version_base=None, config_path="../configs", config_name="main")
def main(cfg: DictConfig):
    # Instantiate the blink detector from configuration
    blink_detector = hydra.utils.instantiate(cfg.blink_detector)

    # Initialize OpenCV VideoCapture
    print("Getting your camera stream. This may take a second...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access the camera.")
        sys.exit(1)

    # Initialize the Qt application and setup UI components
    app = QtWidgets.QApplication([])
    icon_path = "../files/icon.png"
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

    # Function to stop the camera and quit the application
    def stop_camera():
        if cap.isOpened():
            cap.release()
        app.quit()
        sys.exit()

    # Create the control window
    control_window = ControlWindow(blur_windows, icon_path=icon_path)
    control_window.closeEvent = lambda event: stop_camera()

    # Connect the blink detector signal to reset blur windows
    try:
        blink_detector.module.blink_detected.connect(lambda: reset_all_windows(blur_windows))
    except AttributeError as e:
        print(f"Blink detector signal connection failed: {e}")

    # Function to process frames from the camera
    def process_frames():
        if cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to read from the camera.")
                stop_camera()
                return

            eye_mask = blink_detector.module.eye_detector.create_eye_mask(frame)
            frame[eye_mask] = (0, 255, 0)  # Color the eyes area for visualization

            #Detect blink
            is_blink = blink_detector(frame)

            # If blink detected, make the eyes area red
            if is_blink:
                frame[eye_mask] = (0, 0, 255)

            # Convert BGR to RGB for Qt display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
            
            # Update the camera feed in the control window
            control_window.update_camera_feed(rgb_frame)


    # Timer to periodically process frames (non-blocking GUI)
    timer = QtCore.QTimer()
    timer.timeout.connect(process_frames)
    timer.start(16)  # Approximately 60 FPS

    # Run the application
    control_window.show()
    app.exec()

    # Release camera on exit
    if cap.isOpened():
        cap.release()


if __name__ == "__main__":
    main()
