import torch

from stop_the_bus.Agent import Agent
from stop_the_bus.Driver import Driver
from stop_the_bus.Encoding import ViewModule
from stop_the_bus.Log import setup_logging
from stop_the_bus.NeuralAgent import NeuralAgent

setup_logging(level="DEBUG")


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    temperature: float = 0.2
    agents: list[Agent] = [
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=temperature),
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=temperature),
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=temperature),
        NeuralAgent(ViewModule(device=device), greedy=False, temperature=temperature),
    ]
    driver: Driver = Driver(agents, max_turn_count=300)
    driver.drive()


if __name__ == "__main__":
    main()
