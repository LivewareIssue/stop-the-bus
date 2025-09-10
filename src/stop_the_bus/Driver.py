import logging
from logging import Logger

from stop_the_bus.Agent import Agent, Observer
from stop_the_bus.Card import Card
from stop_the_bus.Game import Game, Round, View

log: Logger = logging.getLogger(__name__)


DEFAULT_MAX_TURN_COUNT: int = 100


class Driver:
    __slots__ = ("agents", "game", "max_turn_count")

    def __init__(
        self, agents: list[Agent], lives: int = 5, max_turn_count: int = DEFAULT_MAX_TURN_COUNT
    ) -> None:
        self.agents: list[Agent] = agents
        self.game: Game = Game(len(agents), lives)
        self.max_turn_count: int = max_turn_count

    def drive(self) -> int:
        while self.game.live_player_count > 1:
            log.info("Starting new round")
            log.info(f"Dealer is player {self.game.dealer}")
            round: Round = self.game.start_round()

            for agent in self.agents:
                if isinstance(agent, Observer):
                    agent.on_round_start()

            self._drive_first_turn(round)
            while round.has_turns_remaining:
                if round.turn > self.max_turn_count:
                    log.error("Maximum turn limit reached, aborting game")
                    return -1
                self._drive_turn(round)
            round.end_round()
            self.game.rotate_dealer()
        [winner] = self.game.live_players
        log.info(f"Player {winner} wins the game!")
        return winner

    def _drive_discard(self, round: Round, view: View, agent: Agent) -> None:
        card: Card = agent.discard(view)
        for i, a in enumerate(self.agents):
            if isinstance(a, Observer):
                a.on_discard(agent=i, actor=round.current_player, card=card)

        if agent.stop_the_bus(view):
            for i, a in enumerate(self.agents):
                if isinstance(a, Observer):
                    a.on_stop_the_bus(agent=i, actor=round.current_player)

        if isinstance(agent, Observer):
            agent.on_turn_end(view)

        round.advance_turn()

    def _drive_first_turn(self, round: Round) -> None:
        agent: Agent = self.agents[round.current_player]
        view: View = round.current_view()

        if isinstance(agent, Observer):
            agent.on_turn_start(view)

        self._drive_discard(round, view, agent)

    def _drive_turn(self, round: Round) -> None:
        agent: Agent = self.agents[round.current_player]
        view: View = round.current_view()

        if isinstance(agent, Observer):
            agent.on_turn_start(view)

        card, from_deck = agent.draw(view)
        for i, a in enumerate(self.agents):
            if isinstance(a, Observer):
                a.on_draw(agent=i, actor=round.current_player, card=card, from_deck=from_deck)

        self._drive_discard(round, view, agent)
