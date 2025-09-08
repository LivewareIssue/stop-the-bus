from __future__ import annotations

from stop_the_bus.Agent import Agent, SupportsBeginTurn
from stop_the_bus.ConsoleAgent import ConsoleAgent, clear_console
from stop_the_bus.Game import Game, Round, View
from stop_the_bus.Hand import hand_value
from stop_the_bus.SimpleAgent import SimpleAgent


class Driver:
    __slots__ = ("agents", "game")

    def __init__(self, agents: list[Agent]) -> None:
        self.agents: list[Agent] = agents
        self.game: Game = Game(len(agents))

    def drive(self) -> None:
        round: Round = self.game.start_round()
        self._drive_first_turn(round)
        while round.has_turns_remaining:
            self._drive_turn(round)
        clear_console()
        print("Round complete!")
        for i in range(round.player_count):
            print(f"Player #{round.players[i]}")
            print(round.hands[i])
            print(f"Score: {hand_value(round.hands[i])}")
            print()

    def _drive_first_turn(self, round: Round) -> None:
        agent: Agent = self.agents[round.current_player]
        view: View = round.current_view()

        if isinstance(agent, SupportsBeginTurn):
            agent.begin_turn(view, show_discard_pile=False)

        agent.discard(view)
        agent.stop_the_bus(view)
        round.advance_turn()

    def _drive_turn(self, round: Round) -> None:
        agent: Agent = self.agents[round.current_player]
        view: View = round.current_view()

        if isinstance(agent, SupportsBeginTurn):
            agent.begin_turn(view)

        agent.draw(view)
        agent.discard(view)
        agent.stop_the_bus(view)
        round.advance_turn()


def main() -> None:
    agents: list[Agent] = [ConsoleAgent(), SimpleAgent()]
    driver: Driver = Driver(agents)
    driver.drive()


if __name__ == "__main__":
    main()
