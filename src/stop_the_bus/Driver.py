import logging
from logging import Logger

from stop_the_bus.Agent import Agent, SupportsBeginTurn
from stop_the_bus.Game import Game, Round, View

log: Logger = logging.getLogger(__name__)


class Driver:
    __slots__ = ("agents", "game")

    def __init__(self, agents: list[Agent], lives: int = 5) -> None:
        self.agents: list[Agent] = agents
        self.game: Game = Game(len(agents), lives)

    def drive(self) -> int:
        while self.game.live_player_count > 1:
            log.info("Starting new round")
            log.info(f"Dealer is player {self.game.dealer}")
            round: Round = self.game.start_round()
            self._drive_first_turn(round)
            while round.has_turns_remaining:
                if round.turn > 100:
                    log.error("Maximum turn limit reached, aborting game")
                    return -1
                self._drive_turn(round)
            round.end_round()
            self.game.rotate_dealer()
        [winner] = self.game.live_players
        log.info(f"Player {winner} wins the game!")
        return winner

    def _drive_first_turn(self, round: Round) -> None:
        agent: Agent = self.agents[round.current_player]
        view: View = round.current_view()

        if isinstance(agent, SupportsBeginTurn):
            agent.begin_turn(view)

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
