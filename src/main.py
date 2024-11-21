import cv2
import hydra
from omegaconf import DictConfig
from PyQt5 import QtWidgets, QtGui, QtCore
from utils.screen import ControlWindow, BlurWindow, reset_all_windows
import sys


@hydra.main(version_base=None, config_path="../configs", config_name="main")
def main(cfg: DictConfig):

    # app = QtWidgets.QApplication([])
    blink_detector = hydra.utils.instantiate(cfg.blink_detector)

    # Get camera stream
    print("Getting your camera stream. This may take a second...")
    cap = cv2.VideoCapture(0)

    # Initialize screen projection
    icon_path = "../files/icon.png"
    app = QtWidgets.QApplication([])
    app.setWindowIcon(QtGui.QIcon(icon_path))

    blur_windows = []
    for screen in app.screens():
        blur_window = BlurWindow(screen)
        blur_window.setGeometry(screen.geometry())  # Set the geometry to the screen's geometry
        blur_window.showFullScreen()  # Show the window in full screen mode
        blur_windows.append(blur_window)

    def stop_camera():
        cap.release()
        app.quit()
        sys.exit() 

    control_window = ControlWindow(blur_windows, icon_path=icon_path)
    control_window.closeEvent = lambda event: stop_camera()
    blink_detector.module.blink_detected.connect(lambda: reset_all_windows(blur_windows))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        is_blink = blink_detector(frame)

        if cfg.verbose:
            print(is_blink)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    app.exec_()
    cap.release()


if __name__ == "__main__":
    main() 