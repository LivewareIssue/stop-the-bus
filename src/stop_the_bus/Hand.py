from stop_the_bus.Card import Card, Rank, Suit

type Hand = list[Card]


def empty_hand() -> Hand:
    return []


def single_high(hand: Hand) -> int:
    return max(card.score for card in hand)


def suit_count(hand: Hand) -> int:
    return len({card.suit for card in hand})


def is_flush(hand: Hand) -> bool:
    return suit_count(hand) == 1


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
