import logging
from collections.abc import Callable
from typing import cast

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Datalog import Atom, Database, Inequality, Rule, query
from stop_the_bus.Game import STOP_THE_BUS_HAND_VALUE_THRESHOLD, View
from stop_the_bus.Hand import (
    Hand,
    compute_distinct_rank_count,
    compute_distinct_ranks,
    compute_distinct_suit_count,
    compute_distinct_suits,
    compute_least_common_ranks,
    compute_lowest_scoring_card_and_index,
    compute_rank_to_card_indices,
    compute_ranks_with_single_cards,
    database_from_hand,
)

log: logging.Logger = logging.getLogger(__name__)

PRILE_SIZE: int = 3

PAIR_IN_SHORT_SUITS: Rule = Rule(
    head=Atom(
        "pair_in_short_suits",
        (
            "index_of_a_of_x",
            "index_of_b_of_x",
            "index_of_c_of_y",
            "index_of_c_of_z",
            "suit_x",
            "suit_y",
            "suit_z",
            "rank_a",
            "rank_b",
            "rank_c",
        ),
    ),
    body=(
        Atom("card", ("index_of_a_of_x", "suit_x", "rank_a")),
        Atom("card", ("index_of_b_of_x", "suit_x", "rank_b")),
        Atom("card", ("index_of_c_of_y", "suit_y", "rank_c")),
        Atom("card", ("index_of_c_of_z", "suit_z", "rank_c")),
        Inequality("suit_x", "suit_y"),
        Inequality("suit_x", "suit_z"),
        Inequality("suit_y", "suit_z"),
        Inequality("index_of_a_of_x", "index_of_b_of_x"),
        Inequality("index_of_a_of_x", "index_of_c_of_y"),
        Inequality("index_of_a_of_x", "index_of_c_of_z"),
        Inequality("index_of_b_of_x", "index_of_c_of_y"),
        Inequality("index_of_b_of_x", "index_of_c_of_z"),
        Inequality("index_of_c_of_y", "index_of_c_of_z"),
    ),
)

ONE_OF_PAIR_IN_LONG_SUIT: Rule = Rule(
    head=Atom(
        "one_of_pair_in_long_suit",
        (
            "index_of_a_of_x",
            "index_of_b_of_x",
            "index_of_a_of_y",
            "index_of_c_of_z",
            "suit_x",
            "suit_y",
            "suit_z",
            "rank_a",
            "rank_b",
            "rank_c",
        ),
    ),
    body=(
        Atom("card", ("index_of_a_of_x", "suit_x", "rank_a")),
        Atom("card", ("index_of_b_of_x", "suit_x", "rank_b")),
        Atom("card", ("index_of_a_of_y", "suit_y", "rank_a")),
        Atom("card", ("index_of_c_of_z", "suit_z", "rank_c")),
        Inequality("suit_x", "suit_y"),
        Inequality("suit_x", "suit_z"),
        Inequality("suit_y", "suit_z"),
        Inequality("index_of_a_of_x", "index_of_b_of_x"),
        Inequality("index_of_a_of_x", "index_of_a_of_y"),
        Inequality("index_of_a_of_x", "index_of_c_of_z"),
        Inequality("index_of_b_of_x", "index_of_a_of_y"),
        Inequality("index_of_b_of_x", "index_of_c_of_z"),
        Inequality("index_of_a_of_y", "index_of_c_of_z"),
    ),
)

TWO_IN_LONG_SUIT_TWO_SINGLETONS: Rule = Rule(
    head=Atom(
        "two_in_long_suit_two_singletons",
        (
            "index_of_a_of_x",
            "index_of_b_of_x",
            "index_of_c_of_y",
            "index_of_d_of_z",
            "suit_x",
            "suit_y",
            "suit_z",
            "rank_a",
            "rank_b",
            "rank_c",
            "rank_d",
        ),
    ),
    body=(
        Atom("card", ("index_of_a_of_x", "suit_x", "rank_a")),
        Atom("card", ("index_of_b_of_x", "suit_x", "rank_b")),
        Atom("card", ("index_of_c_of_y", "suit_y", "rank_c")),
        Atom("card", ("index_of_d_of_z", "suit_z", "rank_d")),
        Inequality("suit_x", "suit_y"),
        Inequality("suit_x", "suit_z"),
        Inequality("suit_y", "suit_z"),
        Inequality("index_of_a_of_x", "index_of_b_of_x"),
    ),
)

THREE_IN_LONG_SUIT_ONE_SINGLETON: Rule = Rule(
    head=Atom(
        "three_in_long_suit_one_singleton",
        (
            "index_of_a_of_x",
            "index_of_b_of_x",
            "index_of_c_of_x",
            "index_of_d_of_y",
            "suit_x",
            "suit_y",
            "rank_a",
            "rank_b",
            "rank_c",
            "rank_d",
        ),
    ),
    body=(
        Atom("card", ("index_of_a_of_x", "suit_x", "rank_a")),
        Atom("card", ("index_of_b_of_x", "suit_x", "rank_b")),
        Atom("card", ("index_of_c_of_x", "suit_x", "rank_c")),
        Atom("card", ("index_of_d_of_y", "suit_y", "rank_d")),
        Inequality("suit_x", "suit_y"),
        Inequality("index_of_a_of_x", "index_of_b_of_x"),
        Inequality("index_of_a_of_x", "index_of_c_of_x"),
        Inequality("index_of_b_of_x", "index_of_c_of_x"),
    ),
)

TWO_IN_EACH_SUIT: Rule = Rule(
    head=Atom(
        "two_in_each_suit",
        (
            "index_of_a_of_x",
            "index_of_b_of_x",
            "index_of_c_of_y",
            "index_of_d_of_y",
            "suit_x",
            "suit_y",
            "rank_a",
            "rank_b",
            "rank_c",
            "rank_d",
        ),
    ),
    body=(
        Atom("card", ("index_of_a_of_x", "suit_x", "rank_a")),
        Atom("card", ("index_of_b_of_x", "suit_x", "rank_b")),
        Atom("card", ("index_of_c_of_y", "suit_y", "rank_c")),
        Atom("card", ("index_of_d_of_y", "suit_y", "rank_d")),
        Inequality("suit_x", "suit_y"),
        Inequality("index_of_a_of_x", "index_of_b_of_x"),
        Inequality("index_of_c_of_y", "index_of_d_of_y"),
    ),
)

PAIR_WITH_THREE_IN_LONG_SUIT: Rule = Rule(
    head=Atom(
        "pair_with_three_in_long_suit",
        (
            "index_of_a_of_x",
            "index_of_b_of_x",
            "index_of_c_of_x",
            "index_of_a_of_y",
            "suit_x",
            "suit_y",
            "rank_a",
            "rank_b",
            "rank_c",
        ),
    ),
    body=(
        Atom("card", ("index_of_a_of_x", "suit_x", "rank_a")),
        Atom("card", ("index_of_b_of_x", "suit_x", "rank_b")),
        Atom("card", ("index_of_c_of_x", "suit_x", "rank_c")),
        Atom("card", ("index_of_a_of_y", "suit_y", "rank_a")),
        Inequality("suit_x", "suit_y"),
        Inequality("index_of_a_of_x", "index_of_b_of_x"),
        Inequality("index_of_a_of_x", "index_of_c_of_x"),
        Inequality("index_of_b_of_x", "index_of_c_of_x"),
    ),
)

PAIR_WITH_TWO_IN_EACH_SUIT: Rule = Rule(
    head=Atom(
        "pair_with_two_in_each_suit",
        (
            "index_of_a_of_x",
            "index_of_b_of_x",
            "index_of_a_of_y",
            "index_of_c_of_y",
            "suit_x",
            "suit_y",
            "rank_a",
            "rank_b",
            "rank_c",
        ),
    ),
    body=(
        Atom("card", ("index_of_a_of_x", "suit_x", "rank_a")),
        Atom("card", ("index_of_b_of_x", "suit_x", "rank_b")),
        Atom("card", ("index_of_a_of_y", "suit_y", "rank_a")),
        Atom("card", ("index_of_c_of_y", "suit_y", "rank_c")),
        Inequality("suit_x", "suit_y"),
        Inequality("index_of_a_of_x", "index_of_b_of_x"),
        Inequality("index_of_a_of_y", "index_of_c_of_y"),
    ),
)

DrawFunction = Callable[[View], bool]


class SimpleAgent:
    next_draw_function: DrawFunction | None = None

    def draw(self, view: View) -> tuple[Card, bool]:
        if self.next_draw_function is not None:
            if self.next_draw_function(view):
                return (view.round.draw_from_deck(), True)
            else:
                return (view.round.draw_from_discard(), False)

        log.warning("No next_draw_function set, defaulting to drawing from deck")
        return (view.round.draw_from_deck(), True)

    @staticmethod
    def draw_flush(view: View) -> bool:
        raise NotImplementedError()

    @staticmethod
    def compute_discard_index(hand: Hand) -> tuple[int, DrawFunction | None]:
        ARBITRARY: int = 0

        rank_to_card_indices: dict[Rank, list[int]] = compute_rank_to_card_indices(hand)

        rank_to_counts: dict[Rank, int] = {
            rank: len(indices) for rank, indices in rank_to_card_indices.items()
        }

        distinct_ranks: set[Rank] = compute_distinct_ranks(hand)
        distinct_suits: set[Suit] = compute_distinct_suits(hand)

        distinct_rank_count: int = compute_distinct_rank_count(distinct_ranks)
        distinct_suit_count: int = compute_distinct_suit_count(distinct_suits)

        single_card_ranks: list[Rank] = compute_ranks_with_single_cards(rank_to_counts)

        lowest_card_index, lowest_card = compute_lowest_scoring_card_and_index(hand)

        hand_database: Database = database_from_hand(hand)

        if distinct_suit_count == 4:
            # If all cards are the same rank, discard an arbitrary card
            # e.g. [4D, 4H, 4S, 4C]
            if distinct_rank_count == 1:
                return (ARBITRARY, None)

            if distinct_rank_count == 2:
                # If we have a prile, discard the (guaranteed single) card from the least common
                # rank (i.e. the card that isn't part of the prile)
                # e.g. [4D, 4H, 4S, 7C] -> discard 7C
                if PRILE_SIZE in rank_to_counts.values():
                    [least_common_rank] = compute_least_common_ranks(rank_to_counts)
                    [card_index] = rank_to_card_indices[least_common_rank]
                    return (card_index, None)

                # Otherwise, we have two pairs, so arbitrarily discard one of the
                # cards from the pair with the lowest rank
                # e.g. [4D, 4H, 7S, 7C] -> discard 4D or 4H
                lowest_rank_card_indices: list[int] = rank_to_card_indices[lowest_card.rank]
                return (lowest_rank_card_indices[ARBITRARY], None)

            # If we have 3 different ranks, we must have a pair and two singletons,
            # keep the pair and discard the lowest scoring card from either singleton suits
            # e.g. [3D, 3H, 5S, 7C] -> discard 5S, [3D, 3H, AS, 7C] -> discard 7C
            if distinct_rank_count == 3:
                lowest_rank_singleton: Rank = min(single_card_ranks, key=lambda rank: rank.score)
                [card_index] = rank_to_card_indices[lowest_rank_singleton]
                return (card_index, None)

            # Otherwise, we have 4 ranks across 4 suits, so discard the lowest scoring card
            # regardless of suit
            # e.g. [2D, 4H, 3S, 5C] -> discard 2D
            return (lowest_card_index, None)

        if distinct_suit_count == 3:
            # With 4 ranks across 3 suits, we have no pair. We must have one long suit holding
            # two cards, and two singletons
            # e.g. [A of X, B of X, C of Y, D of Z]
            if distinct_rank_count == 4:
                return SimpleAgent._discard_3_suits_4_ranks(hand_database)

            # With 3 ranks across 3 suits, we must have a pair. We must also have one long suit
            # and two singletons
            if distinct_rank_count == 3:
                match query(hand_database, ONE_OF_PAIR_IN_LONG_SUIT):
                    case [result, *_rest]:
                        # We have a pair of rank A across suits X and Y, the long suit is X
                        # e.g. [A of X, B of X, A of Y, C of Z]

                        a: Rank = cast(Rank, result["rank_a"])
                        b: Rank = cast(Rank, result["rank_b"])
                        c: Rank = cast(Rank, result["rank_c"])

                        index_of_b_of_x: int = cast(int, result["index_of_b_of_x"])
                        index_of_c_of_z: int = cast(int, result["index_of_c_of_z"])

                        if a == Rank.Three:
                            if b.score >= Rank.Seven.score:
                                return (index_of_c_of_z, None)

                            if c.score >= Rank.Seven.score:
                                return (index_of_b_of_x, None)

                            return (index_of_c_of_z, None)

                        if (a.score + b.score) < 11 and c.score > 6:
                            return (index_of_b_of_x, None)

                        return (index_of_c_of_z, None)

                    case _:
                        pass

                match query(hand_database, PAIR_IN_SHORT_SUITS):
                    case [result, *_rest]:
                        # We have a pair of rank C across two singleton suits Y and Z
                        # e.g. [A of X, B of X, C of Y, C of Z]

                        a: Rank = cast(Rank, result["rank_a"])
                        b: Rank = cast(Rank, result["rank_b"])
                        c: Rank = cast(Rank, result["rank_c"])

                        index_of_a_of_x: int = cast(int, result["index_of_a_of_x"])
                        index_of_b_of_x: int = cast(int, result["index_of_b_of_x"])
                        index_of_c_of_z: int = cast(int, result["index_of_c_of_z"])

                        if c == Rank.Three:
                            # Discard the lowest value card in the long suit (X)
                            return (index_of_a_of_x if a.score < b.score else index_of_b_of_x, None)

                        if (a.score + b.score) > 16:
                            return (index_of_c_of_z, None)

                        return (index_of_b_of_x if b.score < a.score else index_of_a_of_x, None)

                    case _:
                        raise Exception("Invalid hand")

            if distinct_rank_count == 2:
                # If we have a prile, discard the (guaranteed single) card that isn't part of it
                # e.g. [4D, 4H, 4S, 7D] -> discard 7D
                if PRILE_SIZE in rank_to_counts.values():
                    [least_common_rank] = compute_least_common_ranks(rank_to_counts)
                    [card_index] = rank_to_card_indices[least_common_rank]
                    return (card_index, None)

                # Otherwise, we must have 2 pairs.
                # Arbitrarily discard one of the cards from the pair with the lowest rank
                # e.g. [3C, 5C, 3D ,5S] -> discard 3C or 3D
                lowest_rank_card_indices: list[int] = rank_to_card_indices[lowest_card.rank]
                return (lowest_rank_card_indices[ARBITRARY], None)

            raise Exception("Invalid hand: 4 cards of the same rank across 3 suits")

        if distinct_suit_count == 2:
            # With 4 ranks across 2 suits, we have no pair. The suits split either 3-1 or 2-2
            if distinct_rank_count == 4:
                return SimpleAgent._discard_2_suits_4_ranks(hand_database, lowest_card_index)

            # With 3 ranks across 2 suits, we must have a pair split across both suits.
            # The suits split either 3-1 or 2-2
            if distinct_rank_count == 3:
                return SimpleAgent._discard_2_suits_3_ranks(hand_database)

            if distinct_rank_count == 2:
                # We have two pairs of the same rank across two suits
                # Arbitrarily discard one of the cards from the pair with the lowest rank
                # e.g. [3D, 3H, 7D, 7H] -> discard 3D or 3H
                lowest_rank_card_indices: list[int] = rank_to_card_indices[lowest_card.rank]
                return (lowest_rank_card_indices[ARBITRARY], None)

            if distinct_rank_count == 1:
                raise Exception("Invalid hand: 4 cards of the same rank across 2 suits")

        # We have a flush, so discard the lowest scoring card
        # e.g. [2D, 4D, 3D, 5D] -> discard 2D
        return (lowest_card_index, SimpleAgent.draw_flush)

    @staticmethod
    def _discard_3_suits_4_ranks(hand_database: Database) -> tuple[int, DrawFunction | None]:
        match query(hand_database, TWO_IN_LONG_SUIT_TWO_SINGLETONS):
            case [result, *_rest]:
                # We have two cards in the long suit X and singletons in suits Y and Z
                # e.g. [A of X, B of X, C of Y, D of Z]

                a: Rank = cast(Rank, result["rank_a"])
                b: Rank = cast(Rank, result["rank_b"])
                c: Rank = cast(Rank, result["rank_c"])
                d: Rank = cast(Rank, result["rank_d"])

                index_of_a_of_x: int = cast(int, result["index_of_a_of_x"])
                index_of_b_of_x: int = cast(int, result["index_of_b_of_x"])
                index_of_c_of_y: int = cast(int, result["index_of_c_of_y"])
                index_of_d_of_z: int = cast(int, result["index_of_d_of_z"])

                lowest_singleton: Rank = c if c.score < d.score else d

                # If the long suit is weak and both singletons are strong, break the
                # long suit and keep three high cards
                # e.g. [2S, 5S, 9D, KC] -> discard 2S
                if (a.score + b.score) < 11 and lowest_singleton.score > 6:
                    return (index_of_a_of_x if a.score < b.score else index_of_b_of_x, None)

                # Otherwise, keep the long suit and discard the lowest singleton
                # e.g. [6S, 8S, 4D, KC] -> discard 4D
                return (index_of_c_of_y if c.score < d.score else index_of_d_of_z, None)

            case _:
                raise Exception("Invalid hand")

    @staticmethod
    def _discard_2_suits_4_ranks(
        hand_database: Database, lowest_card_index: int
    ) -> tuple[int, DrawFunction | None]:
        match query(hand_database, THREE_IN_LONG_SUIT_ONE_SINGLETON):
            case [result, *_rest]:
                # We have three cards in the long suit X and a singleton in suit Y
                # e.g. [A of X, B of X, C of X, D of Y]

                a: Rank = cast(Rank, result["rank_a"])
                b: Rank = cast(Rank, result["rank_b"])
                c: Rank = cast(Rank, result["rank_c"])
                d: Rank = cast(Rank, result["rank_d"])

                index_of_d_of_y: int = cast(int, result["index_of_d_of_y"])

                # If the long suit is weak and the singleton is strong, discard the
                # lowest card in the long suit
                # e.g. [2S, 3S, 6S, KD] -> discard 2S
                if (a.score + b.score + c.score) < 14 and d.score > 6:
                    lowest_long_suit_index: int = min(
                        (
                            (a.score, cast(int, result["index_of_a_of_x"])),
                            (b.score, cast(int, result["index_of_b_of_x"])),
                            (c.score, cast(int, result["index_of_c_of_x"])),
                        )
                    )[1]
                    return (lowest_long_suit_index, None)

                # Otherwise, discard the singleton and keep the flush
                # e.g. [5S, 8S, QS, KD] -> discard KD
                return (index_of_d_of_y, SimpleAgent.draw_flush)

            case _:
                pass

        match query(hand_database, TWO_IN_EACH_SUIT):
            case [result, *_rest]:
                # We have two cards in each of the suits X and Y
                # e.g. [A of X, B of X, C of Y, D of Y]

                a = cast(Rank, result["rank_a"])
                b = cast(Rank, result["rank_b"])
                c = cast(Rank, result["rank_c"])
                d = cast(Rank, result["rank_d"])

                index_of_a_of_x: int = cast(int, result["index_of_a_of_x"])
                index_of_b_of_x: int = cast(int, result["index_of_b_of_x"])
                index_of_c_of_y: int = cast(int, result["index_of_c_of_y"])
                index_of_d_of_y = cast(int, result["index_of_d_of_y"])

                # If the suits are equally strong, discard the lowest scoring card
                # e.g. [2S, AS, 6D, 7D] -> discard 2S
                if (a.score + b.score) == (c.score + d.score):
                    return (lowest_card_index, None)

                # Otherwise, keep the strongest suit and discard the lowest card
                # from the weakest suit
                # e.g. [9S, KS, 4D, 7D] -> discard 4D
                if (a.score + b.score) < (c.score + d.score):
                    return (index_of_a_of_x if a.score < b.score else index_of_b_of_x, None)

                return (index_of_c_of_y if c.score < d.score else index_of_d_of_y, None)

            case _:
                raise Exception("Invalid hand")

    @staticmethod
    def _discard_2_suits_3_ranks(hand_database: Database) -> tuple[int, DrawFunction | None]:
        match query(hand_database, PAIR_WITH_THREE_IN_LONG_SUIT):
            case [result, *_rest]:
                # We have a pair of rank A across suits X and Y, the long suit is X
                # e.g. [A of X, B of X, C of X, A of Y]

                a: Rank = cast(Rank, result["rank_a"])
                b: Rank = cast(Rank, result["rank_b"])
                c: Rank = cast(Rank, result["rank_c"])

                index_of_b_of_x: int = cast(int, result["index_of_b_of_x"])
                index_of_c_of_x: int = cast(int, result["index_of_c_of_x"])
                index_of_a_of_y: int = cast(int, result["index_of_a_of_y"])

                # If the flush is strong enough to stop the bus, break the pair and
                # keep the flush
                # e.g. [5S, 7S, KS, 5D] -> discard 5D
                if (a.score + b.score + c.score) >= STOP_THE_BUS_HAND_VALUE_THRESHOLD:
                    return (index_of_a_of_y, SimpleAgent.draw_flush)

                # Otherwise, keep the pair and discard the lowest of the other two
                # cards in the long suit
                # e.g. [5S, 4S, 9S, 5D] -> discard 4S
                return (index_of_b_of_x if b.score < c.score else index_of_c_of_x, None)

            case _:
                pass

        match query(hand_database, PAIR_WITH_TWO_IN_EACH_SUIT):
            case [result, *_rest]:
                # We have a pair of rank A across suits X and Y, each suit also holds
                # one other card
                # e.g. [A of X, B of X, A of Y, C of Y]

                b = cast(Rank, result["rank_b"])
                c = cast(Rank, result["rank_c"])

                index_of_b_of_x = cast(int, result["index_of_b_of_x"])
                index_of_c_of_y: int = cast(int, result["index_of_c_of_y"])

                # Keep the pair and discard the lowest of the other two cards
                # e.g. [5S, 4S, 5D, 9D] -> discard 4S
                return (index_of_b_of_x if b.score < c.score else index_of_c_of_y, None)

            case _:
                raise Exception("Invalid hand")

    def discard(self, view: View) -> Card:
        discard_index, self.next_draw_function = SimpleAgent.compute_discard_index(view.hand)
        return view.round.discard(discard_index)

    def stop_the_bus(self, view: View) -> bool:
        raise NotImplementedError()
