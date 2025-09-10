import torch

from stop_the_bus.Agent import Agent
from stop_the_bus.Driver import Driver
from stop_the_bus.Encoding import ViewModule
from stop_the_bus.Log import setup_logging
from stop_the_bus.NeuralAgent import NeuralAgent

setup_logging(level="DEBUG")


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agents: list[Agent] = [
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=0.5),
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=0.5),
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=0.5),
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=0.5),
    ]
    driver: Driver = Driver(agents)
    driver.drive()


if __name__ == "__main__":
    main()
