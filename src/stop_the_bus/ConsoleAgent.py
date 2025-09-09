import logging

from stop_the_bus.Card import Card, Suit
from stop_the_bus.Deck import Deck
from stop_the_bus.Game import Round, View
from stop_the_bus.Hand import Hand

RED_ANSI = "\x1b[31m"
BLUE_ANSI = "\x1b[34m"
RESET_ANSI = "\x1b[0m"
YELLOW_ANSI = "\x1b[33m"


log: logging.Logger = logging.getLogger(__name__)


class ConsoleAgent:
    __slots__ = ("player", "events_since_last_turn")

    def __init__(self) -> None:
        self.events_since_last_turn: list[str] = []

    def on_round_start(self) -> None:
        self.events_since_last_turn.clear()

    def on_turn_start(self, view: View) -> None:
        for event in self.events_since_last_turn:
            print(event)
        self.events_since_last_turn.clear()

        print(f"{BLUE_ANSI}Player {view.player}'s turn{RESET_ANSI}")

        if view.round.turn > 0:
            print()
            _print_discard_pile(view.discard_pile)

    def on_turn_end(self, view: View) -> None:
        clear_console()

    def on_discard(self, agent: int, actor: int, card: Card) -> None:
        if agent != actor:
            self.events_since_last_turn.append(f"Player {actor} discarded {_format_card(card)}")

    def on_draw(self, agent: int, actor: int, card: Card, from_deck: bool) -> None:
        if agent != actor:
            source: str = "deck" if from_deck else "discard pile"
            self.events_since_last_turn.append(
                f"Player {actor} drew "
                f"{_format_card(card) if not from_deck else 'a card'} "
                f"from the {source}"
            )

    def on_stop_the_bus(self, agent: int, actor: int) -> None:
        if agent != actor:
            self.events_since_last_turn.append(
                f"{YELLOW_ANSI}Player {actor} has stopped the bus!{RESET_ANSI}"
            )

    def draw(self, view: View) -> tuple[Card, bool]:
        print()
        _print_hand(view.hand)
        return _prompt_draw(view.round)

    def discard(self, view: View) -> Card:
        print()
        _print_hand(view.hand)
        card: Card = _prompt_discard(view.round, view.hand)
        print()
        _print_hand(view.hand)
        return card

    def stop_the_bus(self, view: View) -> bool:
        return _prompt_stop_the_bus(view.round)


def clear_console() -> None:
    print("\033c", end="")


def _format_card(card: Card) -> str:
    if card.suit in (Suit.Hearts, Suit.Diamonds):
        return f"{RED_ANSI}{card}{RESET_ANSI}"
    else:
        return str(card)


def _print_card(card: Card) -> None:
    print(_format_card(card), end="")


def _print_hand(hand: Hand) -> None:
    hand.sort(key=lambda c: (c.suit.value, c.rank.score))
    print("Hand: ", end="")
    for card in sorted(hand, key=lambda c: (c.suit.value, c.rank.score)):
        _print_card(card)
        print(" ", end="")
    print()


def _print_discard_pile(discard_pile: Deck) -> None:
    if discard_pile:
        print("Pile: ", end="")
        _print_card(discard_pile[-1])
        print()


def _prompt_stop_the_bus(round: Round) -> bool:
    if round.can_stop_the_bus():
        choice = input("Stop the bus? (y/n) ").lower()
        if choice == "y":
            round.stop_the_bus()
            return True
    return False


def _prompt_discard(round: Round, hand: Hand) -> Card:
    while True:
        try:
            index = int(input(f"Chose a card to discard (1-{len(hand)}): ")) - 1
            if index in range(len(hand)):
                return round.discard(index)
        except Exception:
            pass
        print()
        print(f"{RED_ANSI}Invalid input, try again.{RESET_ANSI}")


def _prompt_draw(round: Round) -> tuple[Card, bool]:
    while True:
        choice = input("Draw a card from the (d)eck or (p)ile? ").lower()
        if choice == "d":
            return round.draw_from_deck(), True
        elif choice == "p":
            return round.draw_from_discard(), False
        print(f"{RED_ANSI}Invalid input, try again.{RESET_ANSI}")
