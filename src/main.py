# from PyQt5 import QtWidgets
# import keyboard
# from utils.screen import BlurWindow
import cv2
import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path="../configs", config_name="main")
def main(cfg: DictConfig):

    blink_detector = hydra.utils.instantiate(cfg.blink_detector)

    # app = QtWidgets.QApplication([])

    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if blink_detector(frame):
            cv2.imshow(frame)



if __name__ == "__main__":
    main() 