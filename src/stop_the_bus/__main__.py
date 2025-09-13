import logging

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Log import setup_logging
from stop_the_bus.SimpleAgent import SimpleAgent

setup_logging(level=logging.DEBUG)


def main() -> None:
    discard = SimpleAgent.compute_discard_index(
        [
            Card(Suit.Diamonds, Rank.Seven),
            Card(Suit.Diamonds, Rank.Ace),
            Card(Suit.Hearts, Rank.Six),
            Card(Suit.Spades, Rank.Six),
        ]
    )
    print(f"Discard index: {discard}")
    pass


if __name__ == "__main__":
    main()
