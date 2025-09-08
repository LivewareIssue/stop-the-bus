from collections import Counter

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Game import Round, View
from stop_the_bus.Hand import Hand, flush_value, is_prile


class SimpleAgent:
    def draw(self, view: View) -> None:
        round: Round = view.round
        hand = view.hand
        discard_pile = view.discard_pile

        if discard_pile:
            top: Card = discard_pile[-1]
            ranks: set[Rank] = {card.rank for card in hand}
            suit_counts: Counter[Suit] = Counter(card.suit for card in hand)

            if top.rank in ranks:
                round.draw_from_discard()
                return
            if suit_counts[top.suit] >= 2:
                round.draw_from_discard()
                return

        round.draw_from_deck()

    def discard(self, view: View) -> None:
        round: Round = view.round
        hand: Hand = view.hand
        rank_indices: dict[Rank, list[int]] = {}

        for i, card in enumerate(hand):
            rank_indices.setdefault(card.rank, []).append(i)

        pair_indices: list[list[int]] = [idxs for idxs in rank_indices.values() if len(idxs) >= 2]
        if pair_indices:
            keep: set[int] = set(pair_indices[0])
            candidates: list[int] = [i for i in range(len(hand)) if i not in keep]
            if candidates:
                index: int = min(candidates, key=lambda i: hand[i].value)
                round.discard(index)
                return

        suit_values: dict[Suit, int] = {}
        for card in hand:
            suit_values[card.suit] = suit_values.get(card.suit, 0) + card.value

        best_suit: Suit = max(suit_values, key=suit_values.__getitem__)
        candidates: list[int] = [i for i in range(len(hand)) if hand[i].suit != best_suit]
        if not candidates:
            candidates = list(range(len(hand)))

        index: int = min(candidates, key=lambda i: hand[i].value)
        round.discard(index)

    def stop_the_bus(self, view: View) -> None:
        round: Round = view.round
        hand: Hand = view.hand
        if round.can_stop_the_bus() and (is_prile(hand) or flush_value(hand) >= 27):
            round.stop_the_bus()
