from collections import deque
from collections.abc import Sequence

import hypothesis.strategies as st
import torch
from hypothesis import given
from hypothesis.strategies import from_type

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Datalog import Database, query
from stop_the_bus.Deck import Deck, deal, standard_deck
from stop_the_bus.Encoding import (
    MAX_RANK_SUM,
    decode_card,
    decode_hand,
    encode_card,
    encode_hand,
    feature_matrices,
)
from stop_the_bus.Game import Game, Round, View
from stop_the_bus.Hand import (
    MAX_HAND_SIZE,
    Hand,
    compute_distinct_suit_count,
    compute_distinct_suits,
    database_from_hand,
    flush_value,
    hand_value,
    is_flush,
    is_prile,
    single_high,
)
from stop_the_bus.SimpleAgent import RULE_3_SUIT_3_RANK_3_PRILE

# from stop_the_bus.SimpleAgent import SimpleAgent


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


@st.composite
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
    hand: Hand = draw(fixed_suit_count_hand(suit_count))

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
    hand: Hand = draw(fixed_suit_count_hand(suit_count))

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
def known_not_prile_hand(draw: st.DrawFn, hand_size: int | None = None) -> Hand:
    hand_size = hand_size or draw(st.sampled_from([3, 4]))
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
def known_prile_of_not_threes(draw: st.DrawFn, hand_size: int | None = None) -> Hand:
    suits: list[Suit] = draw(
        st.lists(from_type(Suit), min_size=hand_size or 3, max_size=4, unique=True)
    )
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


@st.composite
def lives(draw: st.DrawFn, player_count: int, min_lives: int = 0) -> list[int]:
    return draw(
        st.lists(
            st.integers(min_value=min_lives, max_value=5),
            min_size=player_count,
            max_size=player_count,
        )
    )


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
    distinct_suits: set[Suit] = compute_distinct_suits(hand)
    assert compute_distinct_suit_count(distinct_suits) == expected_suit_count


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


@given(known_prile_hand(), known_not_prile_hand(hand_size=3))
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


@given(known_prile_of_not_threes(), known_not_prile_hand(hand_size=3))
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


EXPECTED_FIRST_PLAYER_HAND_COUNT: int = 4
EXPECTED_OTHER_PLAYER_HAND_COUNT: int = 3


@given(st.integers(min_value=2, max_value=6))
def test_round_initialisation(player_count: int) -> None:
    game: Game = Game(player_count)
    round: Round = game.start_round()

    # Ensure the round has the expected number of players
    assert len(round.players) == player_count

    # Ensure there are the same number of hands as players
    assert len(round.hands) == player_count

    # Ensure the first player has 4 cards, and the rest have 3
    assert len(round.hands[0]) == EXPECTED_FIRST_PLAYER_HAND_COUNT
    for i in range(1, player_count):
        assert len(round.hands[i]) == EXPECTED_OTHER_PLAYER_HAND_COUNT

    # Ensure the discard pile is empty
    assert len(round.discard_pile) == 0

    # Ensure the deck has the expected number of cards
    expected_hand_count: int = EXPECTED_FIRST_PLAYER_HAND_COUNT + (
        EXPECTED_OTHER_PLAYER_HAND_COUNT * (player_count - 1)
    )
    assert len(round.deck) == len(standard_deck()) - expected_hand_count

    # Ensure the turn is set to 0
    assert round.turn == 0

    # Ensure the current player is the first player
    assert round.current_player == round.players[0]

    # Ensure all dealt cards are unique
    dealt_cards: set[Card] = {card for hand in round.hands for card in hand}
    assert len(dealt_cards) == expected_hand_count

    # Ensure the cards remaining in the deck are unique
    assert len(set(round.deck)) == len(round.deck)

    # Ensure no cards are duplicated between hands and the deck
    assert len(dealt_cards.intersection(set(round.deck))) == 0


@given(st.integers(min_value=2, max_value=6), st.integers(min_value=0, max_value=3))
def test_discard_moves_card(player_count: int, card_index: int) -> None:
    game: Game = Game(player_count)
    round: Round = game.start_round()
    card: Card = round.discard(card_index)

    assert card not in round.current_hand
    assert card in round.discard_pile
    assert len(round.discard_pile) == 1
    assert len(round.current_hand) == EXPECTED_FIRST_PLAYER_HAND_COUNT - 1


@given(st.integers(min_value=2, max_value=6))
def test_draw_from_deck(player_count: int) -> None:
    game: Game = Game(player_count)
    round: Round = game.start_round()
    deck_size: int = len(round.deck)
    hand_size: int = len(round.current_hand)
    card: Card = round.draw_from_deck()

    assert card in round.current_hand
    assert len(round.deck) == deck_size - 1
    assert len(round.current_hand) == hand_size + 1


@given(st.integers(min_value=2, max_value=6), st.integers(min_value=0, max_value=3))
def test_draw_from_discard_adds_certain_hold(player_count: int, card_index: int) -> None:
    game: Game = Game(player_count)
    round: Round = game.start_round()
    card: Card = round.discard(card_index)
    round.advance_turn()
    drawn_card: Card = round.draw_from_discard()

    assert drawn_card == card
    assert drawn_card in round.current_hand
    assert drawn_card in round.certain_holds[round.current_index]
    assert len(round.discard_pile) == 0


@given(st.integers(min_value=2, max_value=6), st.integers(min_value=0, max_value=3))
def test_discard_removes_certain_hold(player_count: int, card_index: int) -> None:
    game: Game = Game(player_count)
    round: Round = game.start_round()
    round.discard(card_index)
    round.advance_turn()

    drawn_card: Card = round.draw_from_discard()

    # Ensure the card drawn from the discard pile is in certain holds
    assert drawn_card in round.certain_holds[round.current_index]

    drawn_card_index: int = round.current_hand.index(drawn_card)
    round.discard(drawn_card_index)

    # Ensure the discarded card is no longer in certain holds
    assert drawn_card not in round.certain_holds[round.current_index]


@given(known_flush_hand().filter(lambda h: flush_value(h) >= 21))
def test_can_stop_bus_with_high_flush(hand: Hand) -> None:
    game: Game = Game(1)
    round: Round = game.start_round()
    round.hands[0] = hand
    assert round.can_stop_the_bus()


@given(known_flush_hand().filter(lambda h: flush_value(h) < 21))
def test_can_stop_bus_with_low_flush(hand: Hand) -> None:
    game: Game = Game(1)
    round: Round = game.start_round()
    round.hands[0] = hand
    assert not round.can_stop_the_bus()


@given(known_prile_hand())
def test_can_stop_bus_with_prile(hand: Hand) -> None:
    game: Game = Game(1)
    round: Round = game.start_round()
    round.hands[0] = hand
    assert round.can_stop_the_bus()


@given(known_not_flush_hand().filter(lambda h: not is_prile(h)))
def test_cannot_stop_bus_without_flush_or_prile(hand: Hand) -> None:
    game: Game = Game(1)
    round: Round = game.start_round()
    round.hands[0] = hand
    assert not round.can_stop_the_bus()


PRILE_OF_THREES_PENALTY: int = 2


@given(
    known_prile_of_threes(),
    known_not_prile_hand(hand_size=3),
    known_not_prile_hand(hand_size=3),
    lives(3, min_lives=1),
)
def test_end_round_prile_of_threes_penalty(
    winner_hand: Hand, hand1: Hand, hand2: Hand, lives: list[int]
) -> None:
    player_count: int = 3
    expected_lives: list[int] = lives.copy()

    game: Game = Game(player_count)
    game.lives = lives

    round: Round = game.start_round()
    round.hands = [winner_hand, hand1, hand2]

    round.end_round()
    winner: int = round.players[0]

    for player_index in range(player_count):
        if player_index != winner:
            expected_lives[player_index] -= PRILE_OF_THREES_PENALTY

    assert game.lives == expected_lives


PRILE_PENALTY: int = 1


@given(
    known_prile_of_not_threes(hand_size=3),
    known_not_prile_hand(hand_size=3),
    known_not_prile_hand(hand_size=3),
    lives(3, min_lives=1),
)
def test_end_round_prile_of_not_threes_penalty(
    winner_hand: Hand, hand1: Hand, hand2: Hand, lives: list[int]
) -> None:
    player_count: int = 3
    expected_lives: list[int] = lives.copy()

    game: Game = Game(player_count)
    game.lives = lives

    round: Round = game.start_round()
    round.hands = [winner_hand, hand1, hand2]

    round.end_round()
    winner: int = round.players[0]

    for player_index in range(player_count):
        if player_index != winner:
            expected_lives[player_index] -= PRILE_PENALTY

    assert game.lives == expected_lives


@given(st.integers(min_value=2, max_value=6))
def test_view_reports_certain_holds(player_count: int) -> None:
    game: Game = Game(player_count)
    round: Round = game.start_round()
    card: Card = round.current_hand[0]
    round.discard(0)
    round.draw_from_discard()
    view: View = View(round, 1)
    assert view.certain_holds == {round.players[0]: [card]}
    assert view.player == round.players[1]
    assert view.hand == round.hands[1]
    assert view.turn == round.turn


def test_end_round_handles_tie_without_prile() -> None:
    player_count: int = 3
    game: Game = Game(player_count)
    game.lives = [3, 3, 3]

    round: Round = game.start_round()

    hand_a: Hand = [
        Card(Suit.Spades, Rank.Ace),
        Card(Suit.Spades, Rank.King),
        Card(Suit.Spades, Rank.Queen),
    ]
    hand_b: Hand = [
        Card(Suit.Hearts, Rank.Ace),
        Card(Suit.Hearts, Rank.King),
        Card(Suit.Hearts, Rank.Queen),
    ]
    hand_c: Hand = [
        Card(Suit.Spades, Rank.Five),
        Card(Suit.Spades, Rank.Seven),
        Card(Suit.Spades, Rank.Nine),
    ]

    assert hand_value(hand_a) == hand_value(hand_b)
    assert hand_value(hand_a) > hand_value(hand_c)

    round.hands = [hand_a, hand_b, hand_c]
    round.end_round()

    expected_lives: list[int] = [3, 3, 3]
    loser: int = round.players[2]
    expected_lives[loser] -= 1

    assert game.lives == expected_lives


@given(hand())
def test_hand_encoding_roundtrip(hand: Hand) -> None:
    tensor: torch.Tensor = encode_hand(hand)
    decoded_hand: Hand = decode_hand(tensor)
    assert set(hand) == set(decoded_hand)


@given(from_type(Card))
def test_card_encoding_roundtrip(card: Card) -> None:
    tensor: torch.Tensor = encode_card(card)
    decoded_card: Card = decode_card(tensor)
    assert card == decoded_card


def _compute_rank_feature(hand: Hand) -> torch.Tensor:
    rank_feature: torch.Tensor = torch.zeros(13, dtype=torch.float32)
    for card in hand:
        rank_feature[card.rank.index] += 1
    return rank_feature / MAX_HAND_SIZE


def _compute_suit_feature(hand: Hand) -> torch.Tensor:
    suit_feature: torch.Tensor = torch.zeros(4, dtype=torch.float32)
    for card in hand:
        suit_feature[card.suit.index] += 1
    return suit_feature / MAX_HAND_SIZE


def _compute_suit_rank_sum_feature(hand: Hand) -> torch.Tensor:
    suit_rank_sum_feature: torch.Tensor = torch.zeros(4, dtype=torch.float32)
    for card in hand:
        suit_rank_sum_feature[card.suit.index] += float(card.score)
    return suit_rank_sum_feature / MAX_RANK_SUM


@given(hand())
def test_hand_features(hand: Hand) -> None:
    rank_matrix, suit_matrix, suit_rank_sum_matrix = feature_matrices()
    hand_tensor: torch.Tensor = encode_hand(hand, dtype=torch.float32)

    rank_features: torch.Tensor = hand_tensor @ rank_matrix
    expected_rank_features: torch.Tensor = _compute_rank_feature(hand)
    torch.testing.assert_close(rank_features, expected_rank_features)

    suit_features: torch.Tensor = hand_tensor @ suit_matrix
    expected_suit_features: torch.Tensor = _compute_suit_feature(hand)
    torch.testing.assert_close(suit_features, expected_suit_features)

    suit_rank_sum_features: torch.Tensor = hand_tensor @ suit_rank_sum_matrix
    expected_suit_rank_sum_features: torch.Tensor = _compute_suit_rank_sum_feature(hand)
    torch.testing.assert_close(suit_rank_sum_features, expected_suit_rank_sum_features)


@st.composite
def distinct_suits(draw: st.DrawFn, count: int) -> list[Suit]:
    return draw(st.lists(from_type(Suit), min_size=count, max_size=count, unique=True))


@st.composite
def rank_except(draw: st.DrawFn, exclude: Sequence[Rank]) -> Rank:
    return draw(st.sampled_from([r for r in Rank if r not in exclude]))


@st.composite
def hand_three_suit_3_rank_3_prile(draw: st.DrawFn) -> tuple[Hand, Card, Card]:
    [suit1, suit2, suit3] = draw(distinct_suits(3))

    rank1: Rank = draw(rank_except([Rank.Three]))
    rank2: Rank = draw(rank_except([Rank.Three, rank1]))

    card1: Card = Card(suit1, rank1)
    card2: Card = Card(suit3, rank2)

    cards: list[Card] = [
        Card(suit1, Rank.Three),
        Card(suit1, rank1),
        Card(suit2, Rank.Three),
        Card(suit3, rank2),
    ]

    return draw(st.permutations(cards)), card1, card2


@given(hand_three_suit_3_rank_3_prile())
def test_query(data: tuple[Hand, Card, Card]) -> None:
    hand, _, _ = data
    database: Database = database_from_hand(hand)
    results = query(database, RULE_3_SUIT_3_RANK_3_PRILE)
    assert len(results) == 1
