# from PyQt5 import QtWidgets
# import keyboard
# from utils.screen import BlurWindow
import cv2
import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="../configs", config_name="main")
def main(cfg: DictConfig):

    # app = QtWidgets.QApplication([])
    blink_detector = hydra.utils.instantiate(cfg.blink_detector)

    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        is_blink = blink_detector(frame)
        if cfg.verbose:
            print(is_blink)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    main() 