from enum import IntEnum, auto

import torch
from torch import nn

from stop_the_bus.Card import Card, Rank, Suit
from stop_the_bus.Deck import DECK_SIZE, standard_deck
from stop_the_bus.Game import View
from stop_the_bus.Hand import MAX_HAND_SIZE, Hand


def encode_hand(hand: Hand, dtype: torch.dtype = torch.float32) -> torch.Tensor:
    tensor: torch.Tensor = torch.zeros(52, dtype=dtype)
    for card in hand:
        tensor[card.index] = 1

    return tensor


def decode_hand(tensor: torch.Tensor) -> Hand:
    hand: Hand = []
    nonzero_indices: list[int] = tensor.nonzero(as_tuple=False).view(-1).tolist()  # type: ignore

    for i in nonzero_indices:
        hand.append(Card.from_index(i))

    return hand


def encode_card(card: Card) -> torch.Tensor:
    rank_one_hot: torch.Tensor = torch.zeros(len(Rank), dtype=torch.float32)
    rank_one_hot[card.rank.index] = 1

    suit_one_hot: torch.Tensor = torch.zeros(4, dtype=torch.float32)
    suit_one_hot[card.suit.index] = 1

    return torch.cat((rank_one_hot, suit_one_hot))


MAX_RANK_SUM: int = sum(
    r.score for r in sorted(Rank, key=lambda r: r.score, reverse=True)[:MAX_HAND_SIZE]
)


def decode_card(tensor: torch.Tensor) -> Card:
    rank_index: int = int(tensor[: Rank.size()].argmax().item())
    suit_index: int = int(tensor[Rank.size() :].argmax().item())

    rank: Rank = Rank.from_index(rank_index)
    suit: Suit = Suit.from_index(suit_index)

    return Card(suit, rank)


def feature_matrices() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    hand_rank_count_matrix: torch.Tensor = torch.zeros(
        (DECK_SIZE, Rank.size()), dtype=torch.float32
    )
    hand_suit_count_matrix: torch.Tensor = torch.zeros(DECK_SIZE, Suit.size(), dtype=torch.float32)
    hand_rank_sum_matrix: torch.Tensor = torch.zeros((DECK_SIZE, Suit.size()), dtype=torch.float32)

    for card in standard_deck():
        hand_rank_count_matrix[card.index, card.rank.index] = 1
        hand_suit_count_matrix[card.index, card.suit.index] = 1
        hand_rank_sum_matrix[card.index, card.suit.index] = float(card.score)

    return (
        hand_rank_count_matrix / MAX_HAND_SIZE,
        hand_suit_count_matrix / MAX_HAND_SIZE,
        hand_rank_sum_matrix / MAX_RANK_SUM,
    )


HAND_RANK_COUNT_MATRIX, HAND_SUIT_COUNT_MATRIX, HAND_RANK_SUM_MATRIX = feature_matrices()


class Phase(IntEnum):
    DRAW = auto()
    DISCARD = auto()
    STOP = auto()


def encode_view(view: View, phase: Phase) -> torch.Tensor:
    hand_tensor: torch.Tensor = encode_hand(view.hand, dtype=torch.float32)
    hand_rank_count_tensor: torch.Tensor = hand_tensor @ HAND_RANK_COUNT_MATRIX
    hand_suit_count_tensor: torch.Tensor = hand_tensor @ HAND_SUIT_COUNT_MATRIX
    hand_rank_sum_tensor: torch.Tensor = hand_tensor @ HAND_RANK_SUM_MATRIX
    discard_tensor: torch.Tensor = (
        encode_card(view.discard_pile[-1])
        if view.discard_pile
        else torch.zeros(
            ViewModule.DISCARD_RANK_DIM + ViewModule.DISCARD_SUIT_DIM, dtype=torch.float32
        )
    )
    flag_tensor: torch.Tensor = torch.tensor(
        [
            float(phase == Phase.DRAW),
            float(phase == Phase.DISCARD),
            float(phase == Phase.STOP),
            float(view.bus_is_stopped),
        ],
        dtype=torch.float32,
    )

    return torch.cat(
        (
            hand_tensor,
            hand_rank_count_tensor,
            hand_suit_count_tensor,
            hand_rank_sum_tensor,
            discard_tensor,
            flag_tensor,
        )
    )


class ViewModule(nn.Module):
    # 52-dim multi-hot encoding of viewer's current hand
    HAND_DIM: int = DECK_SIZE

    # 13-dim rank count feature
    HAND_RANK_COUNT_DIM: int = Rank.size()

    # 4-dim suit count feature
    HAND_SUIT_COUNT_DIM: int = Suit.size()

    # 4-dim suit rank sum feature
    HAND_RANK_SUM_DIM: int = Suit.size()

    # one-hot encoding of the card on the top of the discard pile
    DISCARD_SUIT_DIM: int = Suit.size()
    DISCARD_RANK_DIM: int = Rank.size()

    # Draw-phase flag
    DRAW_PHASE_DIM: int = 1

    # Discard-phase flag
    DISCARD_PHASE_DIM: int = 1

    # Stop-the-bus phase flag
    STOP_PHASE_DIM: int = 1

    # Bus-has-been-stopped flag
    BUS_STOPPED_DIM: int = 1

    INPUT_DIMS: list[int] = [
        HAND_DIM,
        HAND_RANK_COUNT_DIM,
        HAND_SUIT_COUNT_DIM,
        HAND_RANK_SUM_DIM,
        DISCARD_SUIT_DIM,
        DISCARD_RANK_DIM,
        DRAW_PHASE_DIM,
        DISCARD_PHASE_DIM,
        STOP_PHASE_DIM,
        BUS_STOPPED_DIM,
    ]

    INPUT_DIM: int = sum(INPUT_DIMS)

    def __init__(self, hidden_dim: int = 128) -> None:
        super().__init__()  # type: ignore
        self.backbone = nn.Sequential(
            nn.Linear(self.INPUT_DIM, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        self.draw_head = nn.Linear(hidden_dim, 2)
        self.discard_head = nn.Linear(hidden_dim, MAX_HAND_SIZE)
        self.stop_head = nn.Linear(hidden_dim, 2)

    @staticmethod
    def _init(module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.kaiming_uniform_(module.weight, nonlinearity="relu")
            nn.init.zeros_(module.bias)

    def forward(self, view: View, phase: Phase) -> dict[str, torch.Tensor]:
        view_tensor: torch.Tensor = encode_view(view, phase)

        if view_tensor.dim() == 1:
            view_tensor = view_tensor.unsqueeze(0)

        x = self.backbone(view_tensor)

        return {
            "draw_logits": self.draw_head(x),
            "discard_logits": self.discard_head(x),
            "stop_logits": self.stop_head(x),
        }
