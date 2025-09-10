import logging

import torch

from stop_the_bus.Agent import Agent
from stop_the_bus.ConsoleAgent import ConsoleAgent
from stop_the_bus.Driver import Driver
from stop_the_bus.Encoding import ViewModule
from stop_the_bus.Log import setup_logging
from stop_the_bus.NeuralAgent import NeuralAgent, train_with_simple_agent
from stop_the_bus.SimpleAgent import SimpleAgent

setup_logging(level=logging.WARN)


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main() -> None:
    console_game()
    # training_run()


def console_game() -> None:
    agents: list[Agent] = [ConsoleAgent(), SimpleAgent(), SimpleAgent(), SimpleAgent()]
    driver: Driver = Driver(agents, max_turn_count=300)
    driver.drive()


def training_run(device: torch.device = DEVICE) -> None:
    net = ViewModule(device=device)
    trained_net: ViewModule = train_with_simple_agent(net, games=1000, max_turns=300)
    torch.save(trained_net.state_dict(), "trained_model.pth")

    trained_net.eval()
    agents: list[Agent] = [
        ConsoleAgent(),
        NeuralAgent(trained_net, greedy=True),
        SimpleAgent(),
        NeuralAgent(trained_net, greedy=False, temperature=0.3),
    ]

    driver: Driver = Driver(agents, max_turn_count=100)
    driver.drive()


if __name__ == "__main__":
    main()
