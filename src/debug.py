from utils.main import main_func
from omegaconf import DictConfig
import hydra


@hydra.main(version_base=None, config_path="../configs", config_name="debug")
def main_debug(cfg: DictConfig):
    main_func(cfg)


if __name__ == "__main__":
    main_debug()