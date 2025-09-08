import itertools
import random
from collections import deque
from collections.abc import Generator

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Hand import Hand

type Deck = deque[Card]


def empty_deck() -> Deck:
    return deque()


def new_deck_order() -> Generator[Card, None, None]:
    for suit, rank in itertools.product([Suit.Spades, Suit.Diamonds], Rank):
        yield Card(suit, rank)
    for suit, rank in itertools.product([Suit.Clubs, Suit.Hearts], reversed(Rank)):
        yield Card(suit, rank)


def standard_deck() -> Deck:
    return deque(new_deck_order())


def shuffled_deck() -> Deck:
    cards: list[Card] = list(new_deck_order())
    random.shuffle(cards)
    return deque(cards)


def deal(deck: Deck, hand: Hand) -> Card:
    card: Card = deck.pop()
    hand.append(card)
    return card
