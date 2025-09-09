from collections import deque

import hypothesis.strategies as st
from hypothesis import given
from hypothesis.strategies import from_type

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Deck import Deck, deal, standard_deck
from stop_the_bus.Hand import Hand, hand_value, is_flush, is_prile, single_high, suit_count


@st.composite
def card_of_suit(draw: st.DrawFn, suit: Suit) -> Card:
    rank: Rank = draw(from_type(Rank))
    card: Card = Card(suit, rank)

    assert card.suit == suit

    return card


@st.composite
def not_greater_rank_card(draw: st.DrawFn, than: Card) -> Card:
    lower_ranks: list[Rank] = [rank for rank in Rank if rank.score <= than.rank.score]
    rank: Rank = draw(st.sampled_from(lower_ranks))
    suit: Suit = draw(
        from_type(Suit)
        if rank != than.rank
        else st.sampled_from([s for s in Suit if s != than.suit])
    )
    card: Card = Card(suit, rank)

    assert card != than
    assert card.score <= than.score

    return card


@st.composite
def known_high_card_hand(draw: st.DrawFn) -> tuple[Hand, Card]:
    high_card: Card = draw(from_type(Card))
    other_cards: list[Card] = draw(
        st.lists(
            not_greater_rank_card(than=high_card),
            min_size=2,
            max_size=3,
            unique=True,
        )
    )
    hand: Hand = other_cards + [high_card]

    assert len(hand) == 3 or len(hand) == 4
    assert high_card in hand
    assert all(card.score <= high_card.score for card in hand)
    assert len(set(hand)) == len(hand)

    return hand, high_card


def fixed_suit_count_hand(draw: st.DrawFn, suit_count: int) -> Hand:
    suits: deque[Suit] = deque(
        draw(st.lists(from_type(Suit), min_size=suit_count, max_size=suit_count, unique=True))
    )
    hand: Hand = []
    hand_size: int = draw(st.integers(min_value=max(suit_count, 3), max_value=4))
    while len(hand) < hand_size:
        suit: Suit = suits.pop()
        cards: list[Card] = draw(
            st.lists(
                card_of_suit(suit=suit),
                min_size=1 if len(suits) > 0 else hand_size - len(hand),
                max_size=hand_size - len(hand) - len(suits),
                unique=True,
            )
        )
        hand.extend(cards)

    assert len(hand) == hand_size
    assert len({card.suit for card in hand}) == suit_count
    assert len(set(hand)) == len(hand)

    return hand


@st.composite
def known_suit_count_hand(draw: st.DrawFn) -> tuple[Hand, int]:
    suit_count: int = draw(st.integers(min_value=1, max_value=4))
    hand: Hand = fixed_suit_count_hand(draw, suit_count)

    assert len(hand) == 3 or len(hand) == 4
    assert len({card.suit for card in hand}) == suit_count
    assert len(set(hand)) == len(hand)

    return hand, suit_count


@st.composite
def known_flush_hand(draw: st.DrawFn) -> Hand:
    suit: Suit = draw(from_type(Suit))
    hand: list[Card] = draw(st.lists(card_of_suit(suit=suit), min_size=3, max_size=4, unique=True))

    assert len(hand) == 3 or len(hand) == 4
    assert len({card.suit for card in hand}) == 1
    assert len(set(hand)) == len(hand)

    return hand


@st.composite
def known_not_flush_hand(draw: st.DrawFn) -> Hand:
    suit_count: int = draw(st.integers(min_value=2, max_value=4))
    hand: Hand = fixed_suit_count_hand(draw, suit_count)

    assert len(hand) == 3 or len(hand) == 4
    assert len({card.suit for card in hand}) > 1
    assert len(set(hand)) == len(hand)

    return hand


@st.composite
def known_prile_hand(draw: st.DrawFn) -> Hand:
    rank: Rank = draw(from_type(Rank))
    suit_count: int = draw(st.integers(min_value=3, max_value=4))
    suits: list[Suit] = draw(
        st.lists(from_type(Suit), min_size=suit_count, max_size=suit_count, unique=True)
    )
    hand: Hand = [Card(s, rank) for s in suits]

    assert len(hand) == 3 or len(hand) == 4
    assert len({card.rank for card in hand}) == 1
    assert len(set(hand)) == len(hand)

    return hand


@st.composite
def known_not_prile_hand(draw: st.DrawFn) -> Hand:
    hand_size: int = draw(st.sampled_from([3, 4]))
    patterns: list[tuple[int, ...]] = (
        [(2, 1), (1, 1, 1)] if hand_size == 3 else [(3, 1), (2, 2), (2, 1, 1), (1, 1, 1, 1)]
    )
    counts: tuple[int, ...] = draw(st.sampled_from(patterns))
    ranks: list[Rank] = draw(
        st.lists(from_type(Rank), min_size=len(counts), max_size=len(counts), unique=True)
    )

    hand: list[Card] = []
    for r, k in zip(ranks, counts, strict=True):
        suits: list[Suit] = draw(st.lists(from_type(Suit), min_size=k, max_size=k, unique=True))
        hand.extend(Card(s, r) for s in suits)

    assert len(hand) == hand_size
    assert len({card.rank for card in hand}) > 1
    assert len(set(hand)) == hand_size

    return hand


@st.composite
def known_prile_of_threes(draw: st.DrawFn) -> Hand:
    suits: list[Suit] = draw(st.lists(from_type(Suit), min_size=3, max_size=4, unique=True))
    hand: Hand = [Card(s, Rank.Three) for s in suits]

    assert len(hand) == 3 or len(hand) == 4
    assert len({card.rank for card in hand}) == 1
    assert len(set(hand)) == len(hand)

    [rank] = {card.rank for card in hand}
    assert rank == Rank.Three

    return hand


@st.composite
def known_prile_of_not_threes(draw: st.DrawFn) -> Hand:
    suits: list[Suit] = draw(st.lists(from_type(Suit), min_size=3, max_size=4, unique=True))
    rank: Rank = draw(st.sampled_from([r for r in Rank if r != Rank.Three]))
    hand: Hand = [Card(s, rank) for s in suits]

    assert len(hand) == 3 or len(hand) == 4
    assert len({card.rank for card in hand}) == 1
    [hand_rank] = {card.rank for card in hand}
    assert hand_rank == rank
    assert hand_rank != Rank.Three
    assert len(set(hand)) == len(hand)

    return hand


@st.composite
def deck(draw: st.DrawFn, min_size: int = 0, max_size: int = 52) -> Deck:
    return deque(draw(st.lists(from_type(Card), min_size=min_size, max_size=max_size, unique=True)))


@st.composite
def hand(draw: st.DrawFn) -> Hand:
    return draw(st.lists(from_type(Card), min_size=0, max_size=4, unique=True))


@given(from_type(Card))
def test_card_value(card: Card) -> None:
    match card.rank:
        case Rank.Ace:
            assert card.score == 11
        case Rank.King | Rank.Queen | Rank.Jack:
            assert card.score == 10
        case _:
            assert card.score == card.rank.score


@given(known_high_card_hand())
def test_single_high(data: tuple[Hand, Card]) -> None:
    hand, expected_high_card = data
    assert single_high(hand) == expected_high_card.score


@given(known_suit_count_hand())
def test_suit_count(data: tuple[Hand, int]) -> None:
    hand, expected_suit_count = data
    assert suit_count(hand) == expected_suit_count


@given(known_flush_hand())
def test_is_flush_when_flush(hand: Hand) -> None:
    assert is_flush(hand)


@given(known_not_flush_hand())
def test_is_flush_when_not_flush(hand: Hand) -> None:
    assert not is_flush(hand)


@given(known_prile_hand())
def test_is_prile_when_prile(hand: Hand) -> None:
    assert is_prile(hand)


@given(known_not_prile_hand())
def test_is_prile_when_not_prile(hand: Hand) -> None:
    assert not is_prile(hand)


@given(known_prile_hand(), known_not_prile_hand())
def test_is_prile_beats_non_prile(prile_hand: Hand, not_prile_hand: Hand) -> None:
    assert hand_value(prile_hand) > hand_value(not_prile_hand)


def is_prile_of_threes(hand: Hand) -> bool:
    return is_prile(hand) and all(card.rank == Rank.Three for card in hand)


@given(
    known_prile_of_threes(),
    st.lists(from_type(Card), min_size=3, max_size=4, unique=True).filter(
        lambda h: not is_prile_of_threes(h)
    ),
)
def test_prile_of_threes_beats_everything(prile_of_threes: Hand, other_hand: Hand) -> None:
    assert hand_value(prile_of_threes) > hand_value(other_hand)


@given(known_prile_of_not_threes(), known_not_prile_hand())
def test_prile_of_not_threes_beats_non_prile(
    prile_of_not_threes: Hand, not_prile_hand: Hand
) -> None:
    assert hand_value(prile_of_not_threes) > hand_value(not_prile_hand)


def test_standard_deck() -> None:
    deck: Deck = standard_deck()

    assert len(deck) == 52
    assert len(set(deck)) == 52


@given(deck(min_size=1), hand())
def test_deal(deck: Deck, hand: Hand) -> None:
    deck_size: int = len(deck)
    hand_size: int = len(hand)
    card: Card = deal(deck, hand)

    assert card not in deck
    assert card in hand
    assert len(deck) == deck_size - 1
    assert len(hand) == hand_size + 1
