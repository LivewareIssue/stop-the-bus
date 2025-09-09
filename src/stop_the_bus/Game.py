from __future__ import annotations

import logging
from collections import defaultdict, deque
from collections.abc import Generator
from dataclasses import dataclass

from stop_the_bus.Card import Card, Rank
from stop_the_bus.Deck import Deck, deal, empty_deck, shuffled_deck
from stop_the_bus.Hand import Hand, empty_hand, flush_value, hand_value, is_flush, is_prile

log: logging.Logger = logging.getLogger(__name__)


class Game:
    __slots__ = (
        "player_count",
        "lives",
        "dealer",
    )

    def __init__(self, player_count: int) -> None:
        self.player_count: int = player_count
        self.lives: list[int] = [5] * player_count
        self.dealer: int = 0

    @property
    def live_players(self) -> Generator[int, None, None]:
        players: deque[int] = deque(range(self.player_count))
        players.rotate(-self.dealer - 1)
        return (p for p in players if self.lives[p] > 0)

    def rotate_dealer(self) -> None:
        self.dealer = next(self.live_players)

    def start_round(self) -> Round:
        return Round(self, list(self.live_players))


class Round:
    __slots__ = (
        "game",
        "deck",
        "discard_pile",
        "players",
        "turn",
        "hands",
        "certain_holds",
        "turns_remaining",
    )

    def __init__(self, game: Game, players: list[int]) -> None:
        self.game: Game = game
        self.deck: Deck = shuffled_deck()
        self.discard_pile: Deck = empty_deck()
        self.players: list[int] = players
        self.turn: int = 0
        self.hands: list[Hand] = [empty_hand() for _ in players]
        self.certain_holds: list[Hand] = [empty_hand() for _ in players]
        self.turns_remaining: int | None = None

        for _ in range(3):
            for hand in self.hands:
                deal(self.deck, hand)

        deal(self.deck, self.hands[0])

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def _current_index(self) -> int:
        return self.turn % self.player_count

    @property
    def current_player(self) -> int:
        return self.players[self._current_index]

    @property
    def current_hand(self) -> Hand:
        return self.hands[self._current_index]

    @property
    def bus_is_stopped(self) -> bool:
        return self.turns_remaining is not None

    @property
    def has_turns_remaining(self) -> bool:
        return self.turns_remaining is None or self.turns_remaining > 0

    def current_view(self) -> View:
        return View(self, self._current_index)

    def discard(self, card_index: int) -> Card:
        card: Card = self.current_hand.pop(card_index)
        self.discard_pile.append(card)
        if card in self.certain_holds[self._current_index]:
            self.certain_holds[self._current_index].remove(card)
        log.debug(f"Player #{self.current_player} discarded {card}")
        return card

    def draw_from_deck(self) -> Card:
        card: Card = deal(self.deck, self.current_hand)
        log.debug(f"Player #{self.current_player} drew {card} from the deck")
        return card

    def draw_from_discard(self) -> Card:
        card: Card = self.discard_pile.pop()
        self.current_hand.append(card)
        self.certain_holds[self._current_index].append(card)
        log.debug(f"Player #{self.current_player} drew {card} from the discard pile")
        return card

    def stop_the_bus(self) -> None:
        self.turns_remaining = self.player_count

    def can_stop_the_bus(self) -> bool:
        hand: Hand = self.current_hand
        return not self.bus_is_stopped and (
            (is_flush(hand) and flush_value(hand) >= 21) or is_prile(hand)
        )

    def advance_turn(self) -> None:
        self.turn += 1
        if self.turns_remaining is not None:
            self.turns_remaining -= 1

    def end_round(self) -> None:
        players_to_scores: dict[int, int] = {
            player_index: hand_value(hand) for player_index, hand in enumerate(self.hands)
        }

        scores_to_player_indices: defaultdict[int, list[int]] = defaultdict(list)
        for player_index, score in players_to_scores.items():
            scores_to_player_indices[score].append(player_index)

        high_score: int = max(scores_to_player_indices.keys())
        [winning_player_index] = scores_to_player_indices[high_score]
        winning_hand: Hand = self.hands[winning_player_index]

        if is_prile(winning_hand):
            [rank] = {card.rank for card in winning_hand}
            self.prile_penalty(winning_player_index, rank)
        else:
            low_score: int = min(scores_to_player_indices.keys())
            loser_indices: list[int] = scores_to_player_indices[low_score]
            self.standard_penalty(loser_indices)

    def standard_penalty(self, loser_indices: list[int]) -> None:
        for i in loser_indices:
            self.game.lives[self.players[i]] -= 1

    def prile_penalty(self, winner_index: int, rank: Rank) -> None:
        penalty: int = 2 if rank == Rank.Three else 1
        for i, player in enumerate(self.players):
            if i != winner_index:
                self.game.lives[player] -= penalty


@dataclass(frozen=True, slots=True)
class View:
    round: Round
    player_index: int

    @property
    def turn(self) -> int:
        """The current turn number, starting at 0."""
        return self.round.turn

    @property
    def player(self) -> int:
        """The viewer's player ID."""
        return self.round.players[self.player_index]

    @property
    def hand(self) -> Hand:
        """The viewer's current hand."""
        return self.round.hands[self.player_index]

    @property
    def lives(self) -> list[int]:
        """The number of lives remaining for each player."""
        return self.round.game.lives

    @property
    def discard_pile(self) -> Deck:
        """The discard pile, with the top card at the end of the list."""
        return self.round.discard_pile

    @property
    def deck_size(self) -> int:
        """The number of cards remaining in the deck."""
        return len(self.round.deck)

    @property
    def certain_holds(self) -> dict[int, Hand]:
        """A mapping of players to cards that the viewer knows they definitely hold.
        That is, cards they have drawn from the discard pile and not yet discarded.
        """
        return {
            self.round.players[i]: hand
            for i, hand in enumerate(self.round.certain_holds)
            if i != self.player_index and hand
        }
