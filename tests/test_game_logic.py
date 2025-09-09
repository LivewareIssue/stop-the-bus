from collections import deque

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Game import Game


def test_discarding_card_moves_to_discard_pile_and_updates_hand() -> None:
    game = Game(2)
    round_ = game.start_round()
    starting_hand = list(round_.current_hand)
    starting_discard_size = len(round_.discard_pile)

    card = round_.current_hand[0]
    round_.discard(0)

    assert card not in round_.current_hand
    assert len(round_.current_hand) == len(starting_hand) - 1
    assert len(round_.discard_pile) == starting_discard_size + 1
    assert round_.discard_pile[-1] == card


def test_draw_from_deck_changes_hand_and_deck_size() -> None:
    game = Game(2)
    round_ = game.start_round()
    starting_hand_len = len(round_.current_hand)
    starting_deck_size = len(round_.deck)

    card = round_.draw_from_deck()

    assert len(round_.current_hand) == starting_hand_len + 1
    assert len(round_.deck) == starting_deck_size - 1
    assert round_.current_hand[-1] == card


def test_draw_from_discard_pile_adds_to_hand_and_certain_holds() -> None:
    game = Game(2)
    round_ = game.start_round()
    original_length = len(round_.current_hand)
    card = round_.current_hand[0]
    round_.discard(0)

    drawn = round_.draw_from_discard()

    assert drawn == card
    assert len(round_.current_hand) == original_length
    assert round_.current_hand[-1] == card
    assert card in round_.certain_holds[0]


def test_drawing_from_empty_deck_reshuffles_discard_pile() -> None:
    game = Game(1)
    round_ = game.start_round()

    card1 = Card(Suit.Spades, Rank.Ace)
    card2 = Card(Suit.Diamonds, Rank.Two)
    round_.deck = deque()
    round_.discard_pile = deque([card1, card2])
    round_.hands[0] = []

    drawn = round_.draw_from_deck()

    assert drawn == card1
    assert drawn in round_.current_hand
    assert len(round_.deck) == 0
    assert list(round_.discard_pile) == [card2]


def test_prile_win_penalty() -> None:
    game = Game(3)
    game.dealer = game.player_count - 1
    round_ = game.start_round()
    round_.hands = [
        [
            Card(Suit.Spades, Rank.Four),
            Card(Suit.Diamonds, Rank.Four),
            Card(Suit.Clubs, Rank.Four),
        ],
        [
            Card(Suit.Spades, Rank.Ace),
            Card(Suit.Hearts, Rank.Two),
            Card(Suit.Clubs, Rank.Three),
        ],
        [
            Card(Suit.Spades, Rank.Five),
            Card(Suit.Diamonds, Rank.Six),
            Card(Suit.Clubs, Rank.Seven),
        ],
    ]

    round_.end_round()

    assert game.lives == [5, 4, 4]


def test_prile_of_threes_win_penalty() -> None:
    game = Game(3)
    game.dealer = game.player_count - 1
    round_ = game.start_round()
    round_.hands = [
        [
            Card(Suit.Spades, Rank.Three),
            Card(Suit.Diamonds, Rank.Three),
            Card(Suit.Clubs, Rank.Three),
        ],
        [
            Card(Suit.Spades, Rank.Four),
            Card(Suit.Hearts, Rank.Five),
            Card(Suit.Clubs, Rank.Six),
        ],
        [
            Card(Suit.Spades, Rank.Seven),
            Card(Suit.Diamonds, Rank.Eight),
            Card(Suit.Clubs, Rank.Nine),
        ],
    ]

    round_.end_round()

    assert game.lives == [5, 3, 3]


def test_normal_hand_win_penalty() -> None:
    game = Game(3)
    game.dealer = game.player_count - 1
    round_ = game.start_round()
    round_.hands = [
        [
            Card(Suit.Hearts, Rank.King),
            Card(Suit.Hearts, Rank.Queen),
            Card(Suit.Hearts, Rank.Ten),
        ],
        [Card(Suit.Spades, Rank.Two), Card(Suit.Diamonds, Rank.Three), Card(Suit.Clubs, Rank.Four)],
        [Card(Suit.Hearts, Rank.Two), Card(Suit.Diamonds, Rank.Four), Card(Suit.Clubs, Rank.Five)],
    ]

    round_.end_round()

    assert game.lives == [5, 4, 5]


def test_standard_penalty_multiple_losers() -> None:
    game = Game(3)
    game.dealer = game.player_count - 1
    round_ = game.start_round()
    round_.hands = [
        [
            Card(Suit.Hearts, Rank.King),
            Card(Suit.Hearts, Rank.Queen),
            Card(Suit.Hearts, Rank.Ten),
        ],
        [Card(Suit.Spades, Rank.Two), Card(Suit.Diamonds, Rank.Three), Card(Suit.Clubs, Rank.Four)],
        [Card(Suit.Spades, Rank.Four), Card(Suit.Diamonds, Rank.Two), Card(Suit.Clubs, Rank.Three)],
    ]

    round_.end_round()

    assert game.lives == [5, 4, 4]
