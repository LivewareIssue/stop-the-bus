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

    @property
    def index(self) -> int:
        match self:
            case Suit.Spades:
                return 0
            case Suit.Diamonds:
                return 1
            case Suit.Clubs:
                return 2
            case Suit.Hearts:
                return 3

    @staticmethod
    def from_index(index: int) -> "Suit":
        match index:
            case 0:
                return Suit.Spades
            case 1:
                return Suit.Diamonds
            case 2:
                return Suit.Clubs
            case 3:
                return Suit.Hearts
            case _:
                raise ValueError(f"Invalid suit index: {index}")

    @staticmethod
    def size() -> int:
        return len(Suit.__members__)


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

    @property
    def score(self) -> int:
        match self:
            case Rank.Ace:
                return 11
            case Rank.King | Rank.Queen | Rank.Jack:
                return 10
            case _:
                return int(self.value)

    @property
    def index(self) -> int:
        return self.value - 1

    @staticmethod
    def from_index(index: int) -> "Rank":
        return Rank(index + 1)

    @staticmethod
    def size() -> int:
        return len(Rank.__members__)


@dataclass(frozen=True, slots=True)
class Card:
    suit: Suit
    rank: Rank

    @property
    def score(self) -> int:
        return self.rank.score

    def __str__(self) -> str:
        return f"{self.rank}{self.suit.value}"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def index(self) -> int:
        return self.suit.index * Rank.size() + self.rank.index

    @staticmethod
    def from_index(index: int) -> "Card":
        rank_index: int = index % Rank.size()
        suit_index: int = index // Rank.size()

        rank: Rank = Rank.from_index(rank_index)
        suit: Suit = Suit.from_index(suit_index)

        return Card(suit, rank)
