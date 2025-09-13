from typing import cast

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Datalog import Atom, Database, Inequality, Rule, query
from stop_the_bus.Game import View
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
    is_prile,
)

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


class SimpleAgent:
    def draw(self, view: View) -> tuple[Card, bool]:
        raise NotImplementedError()

    @staticmethod
    def compute_discard_index(hand: Hand) -> int:
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
                return ARBITRARY

            if distinct_rank_count == 2:
                # If we have a prile, discard the (guaranteed single) card from the least common
                # rank (i.e. the card that isn't part of the prile)
                # e.g. [4D, 4H, 4S, 7C] -> discard 7C
                if is_prile(hand):
                    [least_common_rank] = compute_least_common_ranks(rank_to_counts)
                    [card_index] = rank_to_card_indices[least_common_rank]
                    return card_index

                # Otherwise, we have to pairs, so arbitrarily discard one of the
                # cards from the pair with the lowest rank
                # e.g. [4D, 4H, 7S, 7C] -> discard 4D or 4H
                lowest_rank_card_indices: list[int] = rank_to_card_indices[lowest_card.rank]
                return lowest_rank_card_indices[ARBITRARY]

            # If we have 3 different ranks, we must have a pair and two singletons,
            # keep the pair and discard the lowest rank card from either singleton suits
            # e.g. [3D, 3H, 5S, 7C] -> discard 5S
            if distinct_rank_count == 3:
                lowest_rank_singleton: Rank = min(single_card_ranks, key=lambda rank: rank.value)
                [card_index] = rank_to_card_indices[lowest_rank_singleton]
                return card_index

            # Otherwise, we have 4 ranks across 4 suits, so discard the lowest scoring card
            # regardless of suit
            # e.g. [2D, 4H, 3S, 5C] -> discard 2D
            return lowest_card_index

        if distinct_suit_count == 3:
            if distinct_rank_count == 4:
                raise NotImplementedError()

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
                                return index_of_c_of_z

                            if c.score >= Rank.Seven.score:
                                return index_of_b_of_x

                            return index_of_c_of_z

                        if (a.score + b.score) < 11 and c.score > 6:
                            return index_of_b_of_x

                        return index_of_c_of_z

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

                        print(hand)
                        print(f"a: {a}, b: {b}, c: {c}")
                        print(f"index_of_a_of_x: {index_of_a_of_x}")
                        print(f"index_of_b_of_x: {index_of_b_of_x}")
                        print(f"index_of_c_of_z: {index_of_c_of_z}")

                        if c == Rank.Three:
                            # Discard the lowest value card in the long suit (X)
                            return index_of_a_of_x if a.score < b.score else index_of_b_of_x

                        print(f"a.score + b.score: {a.score + b.score}")
                        if (a.score + b.score) > 16:
                            return index_of_c_of_z

                        print(f"a.score: {a.score}")
                        print(f"b.score: {b.score}")
                        return index_of_b_of_x if b.score < a.score else index_of_a_of_x

                    case _:
                        raise Exception("Invalid hand")

            # We must have 2 pairs of the same rank.
            # Arbitrarily discard one of the cards from the pair with the lowest rank
            # e.g. [3C, 5C, 3D ,5S] -> discard 3C or 3D
            if distinct_rank_count == 2:
                lowest_rank_card_indices: list[int] = rank_to_card_indices[lowest_card.rank]
                return lowest_rank_card_indices[ARBITRARY]

            raise Exception("Invalid hand: 4 cards of the same rank across 3 suits")

        if distinct_suit_count == 2:
            if distinct_rank_count == 4:
                raise NotImplementedError()

            if distinct_rank_count == 3:
                raise NotImplementedError()

            if distinct_rank_count == 2:
                raise NotImplementedError()

            if distinct_rank_count == 1:
                raise Exception("Invalid hand: 4 cards of the same rank across 2 suits")

        # We have a flush, so discard the lowest scoring card
        # e.g. [2D, 4D, 3D, 5D] -> discard 2D
        return lowest_card_index

    def discard(self, view: View) -> Card:
        return view.round.discard(SimpleAgent.compute_discard_index(view.hand))

    def stop_the_bus(self, view: View) -> bool:
        raise NotImplementedError()
