import logging

import trueskill  # type: ignore

from stop_the_bus.Agent import Agent
from stop_the_bus.Driver import NO_WINNER, Driver

log: logging.Logger = logging.getLogger(__name__)


def trial(env: trueskill.TrueSkill, agents: list[Agent], ratings: list[trueskill.Rating]) -> None:
    driver = Driver(agents)
    winner: int = driver.drive()

    if winner == NO_WINNER:
        log.info("Game ended without a winner, leaving ratings unchanged")
        return

    # TrueSkill ranks are ordered best-first, so the winner takes rank 0 and everyone else
    # ties for rank 1
    ranks: list[int] = [1] * len(agents)
    ranks[winner] = 0
    teams: list[tuple[trueskill.Rating,]] = [(ratings[i],) for i in range(len(agents))]
    new_ratings: list[tuple[trueskill.Rating,]] = env.rate(teams, ranks=ranks)  # type: ignore
    log.info(ratings)
    for i in range(len(agents)):
        ratings[i] = new_ratings[i][0]
    log.info(new_ratings)
