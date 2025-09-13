from collections import defaultdict

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Datalog import Database

type Hand = list[Card]


MAX_HAND_SIZE: int = 4
MIN_HAND_SIZE: int = 3


def empty_hand() -> Hand:
    return []


def single_high(hand: Hand) -> int:
    return max(card.score for card in hand)


def is_flush(hand: Hand) -> bool:
    return compute_distinct_suit_count(compute_distinct_suits(hand)) == 1


def flush_value(hand: Hand) -> int:
    return sum(card.score for card in hand)


def suit_value(hand: Hand, suit: Suit) -> int:
    return sum(card.score for card in hand if card.suit == suit)


def maximum_suit_value(hand: Hand) -> int:
    return max(suit_value(hand, suit) for suit in Suit)


def is_prile(hand: Hand) -> bool:
    return len({card.rank for card in hand}) == 1


def prile_value(rank: Rank) -> int:
    match rank:
        case Rank.Three:
            return 12
        case Rank.Ace:
            return 11
        case Rank.Two:
            return 0
        case _:
            return int(rank.value) - 3


def hand_value(hand: Hand) -> int:
    if is_prile(hand):
        [rank] = {card.rank for card in hand}
        return prile_value(rank) + 32
    else:
        return maximum_suit_value(hand)


# A map from card indices to their ranks
# e.g. [2D, 4H, 3S, 4C] -> {0: Rank.Two, 1: Rank.Four, 2: Rank.Three, 3: Rank.Four}
def compute_card_indices_to_ranks(hand: Hand) -> dict[int, Rank]:
    return {index: card.rank for index, card in enumerate(hand)}


# A map from card indices to their suits
# e.g. [2D, AD, 3S, 4C] -> {0: Suit.Diamonds, 1: Suit.Diamonds, 2: Suit.Spades, 3: Suit.Clubs}
def compute_card_indices_to_suits(hand: Hand) -> dict[int, Suit]:
    return {index: card.suit for index, card in enumerate(hand)}


# A map from ranks to the list of card indices with that rank
# e.g. [2D, 4H, 2S, 5C] -> {Rank.Two: [0, 2], Rank.Four: [1], Rank.Five: [3]}
def compute_rank_to_card_indices(hand: Hand) -> dict[Rank, list[int]]:
    rank_to_card_indices: dict[Rank, list[int]] = {}
    for index, card in enumerate(hand):
        rank_to_card_indices.setdefault(card.rank, []).append(index)
    return rank_to_card_indices


# A map from suits to the list of card indices with that suit
# e.g. [2D, AD, 3S, 4C] -> {Suit.Diamonds: [0, 1], Suit.Spades: [2], Suit.Clubs: [3]}
def compute_suit_to_card_indices(hand: Hand) -> dict[Suit, list[int]]:
    suit_to_card_indices: dict[Suit, list[int]] = {}
    for index, card in enumerate(hand):
        suit_to_card_indices.setdefault(card.suit, []).append(index)
    return suit_to_card_indices


# A map from ranks to the count of cards with that rank
# e.g. [2D, 4H, 2S, 5C] -> {Rank.Two: 2, Rank.Four: 1, Rank.Five: 1}
def compute_rank_to_counts(rank_to_card_indices: dict[Rank, list[int]]) -> dict[Rank, int]:
    return {rank: len(indices) for rank, indices in rank_to_card_indices.items()}


# A map from suits to the count of cards with that suit
# e.g. [2D, AD, 3S, 4C] -> {Suit.Diamonds: 2, Suit.Spades: 1, Suit.Clubs: 1}
def compute_suit_to_counts(suit_to_card_indices: dict[Suit, list[int]]) -> dict[Suit, int]:
    return {suit: len(indices) for suit, indices in suit_to_card_indices.items()}


# A map from suits to the sum of scores of cards with that suit
# e.g. [2D, AD, 3S, 4C] -> {Suit.Diamonds: 13, Suit.Spades: 3, Suit.Clubs: 4}
def compute_suit_to_suit_score_sums(hand: Hand) -> dict[Suit, int]:
    return {
        suit: sum(card.score for card in hand if card.suit == suit)
        for suit in {card.suit for card in hand}
    }


# The set of ranks in the hand
# e.g. [2D, 4H, 2S, 5C] -> {Rank.Two, Rank.Four, Rank.Five}
def compute_distinct_ranks(hand: Hand) -> set[Rank]:
    return {card.rank for card in hand}


# The number of different ranks in the hand
# e.g. [2D, 4H, 2S, 5C] -> 3
def compute_distinct_rank_count(distinct_ranks: set[Rank]) -> int:
    return len(distinct_ranks)


# The set of suits in the hand
# e.g. [2D, AD, 3S, 4C] -> {Suit.Diamonds, Suit.Spades, Suit.Clubs}
def compute_distinct_suits(hand: Hand) -> set[Suit]:
    return {card.suit for card in hand}


# The number of different suits in the hand
# e.g. [2D, AD, 3S, 4C] -> 3
def compute_distinct_suit_count(distinct_suits: set[Suit]) -> int:
    return len(distinct_suits)


# The lowest scoring card in the hand regardless of suit, and its index in the hand
# e.g. [AD, 5S, 3D, 4C] -> (2, 3D)
def compute_lowest_scoring_card_and_index(hand: Hand) -> tuple[int, Card]:
    return min(enumerate(hand), key=lambda pair: pair[1].score)


# The ranks that only have a single card in the hand
# e.g. [2D, 4H, 2S, 5C] -> [Rank.Four, Rank.Five]
def compute_ranks_with_single_cards(rank_to_counts: dict[Rank, int]) -> list[Rank]:
    return [rank for rank, count in rank_to_counts.items() if count == 1]


# The ranks that have the least number of cards in the hand
# e.g. [2D, 4H, 4S, 5C] -> [Rank.Two, Rank.Five]
def compute_least_common_ranks(rank_to_counts: dict[Rank, int]) -> list[Rank]:
    min_count: int = min(rank_to_counts.values())
    return [rank for rank, count in rank_to_counts.items() if count == min_count]


# Convert a hand into a Datalog database
def database_from_hand(hand: Hand) -> Database:
    db: Database = defaultdict(set)
    for index, card in enumerate(hand):
        db[("card", 3)].add((index, card.suit, card.rank))
    return db
