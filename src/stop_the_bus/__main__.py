import logging

import torch

from stop_the_bus.Log import setup_logging

setup_logging(level=logging.DEBUG)


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main() -> None:
    pass


if __name__ == "__main__":
    main()
