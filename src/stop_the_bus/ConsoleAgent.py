from stop_the_bus.Card import Card, Suit
from stop_the_bus.Deck import Deck
from stop_the_bus.Game import Round, View
from stop_the_bus.Hand import Hand

RED_ANSI = "\x1b[31m"
BLUE_ANSI = "\x1b[34m"
RESET_ANSI = "\x1b[0m"


class ConsoleAgent:
    def begin_turn(self, view: View, show_discard_pile: bool = True) -> None:
        clear_console()
        print(f"{BLUE_ANSI}Player #{view.player}'s turn:{RESET_ANSI}")
        _print_bus_stopped(view.round.turns_remaining)
        if show_discard_pile:
            print()
            _print_discard_pile(view.discard_pile)

    def draw(self, view: View) -> None:
        print()
        _print_hand(view.hand)
        _prompt_draw(view.round)

    def discard(self, view: View) -> None:
        print()
        _print_hand(view.hand)
        _prompt_discard(view.round, view.hand)
        print()
        _print_hand(view.hand)

    def stop_the_bus(self, view: View) -> None:
        _prompt_stop_the_bus(view.round)


def clear_console() -> None:
    print("\033c", end="")


def _print_card(card: Card) -> None:
    if card.suit in (Suit.Hearts, Suit.Diamonds):
        print(f"{RED_ANSI}{card}{RESET_ANSI}", end="")
    else:
        print(card, end="")


def _print_hand(hand: Hand) -> None:
    print("Hand: ", end="")
    for card in hand:
        _print_card(card)
        print(" ", end="")
    print()


def _print_discard_pile(discard_pile: Deck) -> None:
    if discard_pile:
        print("Pile: ", end="")
        _print_card(discard_pile[-1])
        print()


def _print_bus_stopped(turns_remaining: int | None) -> None:
    if turns_remaining is not None:
        print(f"{RED_ANSI}The bus has been stopped!{RESET_ANSI}")


def _prompt_stop_the_bus(round: Round) -> None:
    if round.can_stop_the_bus():
        choice = input("Stop the bus? (y/n) ").lower()
        if choice == "y":
            round.stop_the_bus()


def _prompt_discard(round: Round, hand: Hand) -> None:
    while True:
        try:
            index = int(input(f"Chose a card to discard (1-{len(hand)}): ")) - 1
            if index in range(len(hand)):
                round.discard(index)
                return
        except Exception:
            pass
        print()
        print(f"{RED_ANSI}Invalid input, try again.{RESET_ANSI}")


def _prompt_draw(round: Round) -> None:
    while True:
        choice = input("Draw a card from the (d)eck or (p)ile? ").lower()
        if choice == "d":
            round.draw_from_deck()
            return
        elif choice == "p":
            round.draw_from_discard()
            return
        print(f"{RED_ANSI}Invalid input, try again.{RESET_ANSI}")
