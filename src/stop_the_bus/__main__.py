from stop_the_bus.Agent import Agent
from stop_the_bus.ConsoleAgent import ConsoleAgent
from stop_the_bus.Driver import Driver
from stop_the_bus.Log import setup_logging
from stop_the_bus.SimpleAgent import SimpleAgent

setup_logging(level="DEBUG")


def main() -> None:
    agents: list[Agent] = [ConsoleAgent(), SimpleAgent(), SimpleAgent(), SimpleAgent()]
    driver = Driver(agents)
    driver.drive()


if __name__ == "__main__":
    main()
