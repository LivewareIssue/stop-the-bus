from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    Spades = "♠"
    Diamonds = "♦"
    Clubs = "♣"
    Hearts = "♥"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.__str__()


class Rank(Enum):
    Ace = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5
    Six = 6
    Seven = 7
    Eight = 8
    Nine = 9
    Ten = 10
    Jack = 11
    Queen = 12
    King = 13

    def __str__(self) -> str:
        match self:
            case Rank.Ten:
                return "T"
            case Rank.Jack:
                return "J"
            case Rank.Queen:
                return "Q"
            case Rank.King:
                return "K"
            case Rank.Ace:
                return "A"
            case _:
                return str(self.value)

    def __repr__(self) -> str:
        return self.__str__()


@dataclass(frozen=True, slots=True)
class Card:
    suit: Suit
    rank: Rank

    @property
    def value(self) -> int:
        match self.rank:
            case Rank.Jack | Rank.Queen | Rank.King:
                return 10
            case Rank.Ace:
                return 11
            case _:
                return int(self.rank.value)

    def __str__(self) -> str:
        return f"{self.rank}{self.suit.value}"

    def __repr__(self) -> str:
        return self.__str__()
