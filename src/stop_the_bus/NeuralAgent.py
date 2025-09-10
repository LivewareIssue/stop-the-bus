import logging

import torch

from stop_the_bus.Card import Card
from stop_the_bus.Encoding import Phase, ViewModule
from stop_the_bus.Game import View

DEFAULT_GREEDY: bool = True
DEFAULT_TEMPERATURE: float = 1.0
DEFAULT_EPSILON: float = 0.0


log: logging.Logger = logging.getLogger(__name__)


class NeuralAgent:
    __slots__ = ("net", "device", "greedy", "temperature", "epsilon")

    def __init__(
        self,
        net: ViewModule,
        greedy: bool = DEFAULT_GREEDY,
        temperature: float = DEFAULT_TEMPERATURE,
        epsilon: float = DEFAULT_EPSILON,
    ) -> None:
        self.device: torch.device = net.device
        self.net: ViewModule = net
        self.net.eval()
        self.greedy: bool = greedy
        self.temperature: float = temperature
        self.epsilon: float = epsilon

    def _forward(self, view: View, phase: Phase) -> torch.Tensor:
        with torch.no_grad():
            return self.net(view, phase)

    def _act_random(self, x: torch.Tensor, mask: torch.Tensor | None) -> int:
        if mask is None:
            return int(torch.randint(low=0, high=x.numel(), size=()).item())
        else:
            valid_indices: torch.Tensor = torch.nonzero(mask, as_tuple=False).squeeze(-1)
            index: int = int(torch.randint(low=0, high=valid_indices.numel(), size=()).item())
            return int(valid_indices[index].item())

    def _act(self, logits: torch.Tensor, mask: torch.Tensor | None) -> int:
        x: torch.Tensor = logits.squeeze(0)
        if mask is not None:
            x = x.masked_fill(~mask.to(self.device), float("-inf"))

        if self.epsilon > 0.0 and torch.rand(()) < self.epsilon:
            return self._act_random(x, mask)

        if self.greedy:
            return int(torch.argmax(x).item())

        temperature: float = max(self.temperature, 1e-6)
        p: torch.Tensor = torch.softmax(x / temperature, dim=-1)
        if torch.isnan(p).any() or torch.isinf(p).any() or p.sum() <= 0.0:
            return self._act_random(x, mask)

        return int(torch.multinomial(p, num_samples=1).item())

    def draw(self, view: View) -> tuple[Card, bool]:
        logits: torch.Tensor = self._forward(view, Phase.DRAW)
        action: int = self._act(logits, None)
        take_deck: bool = action == 0

        if take_deck:
            return view.round.draw_from_deck(), take_deck

        return view.round.draw_from_discard(), take_deck

    def discard(self, view: View) -> Card:
        logits: torch.Tensor = self._forward(view, Phase.DISCARD)
        valid_mask: torch.Tensor = torch.zeros(
            logits.shape[-1], dtype=torch.bool, device=logits.device
        )
        valid_mask[: len(view.hand)] = True
        index: int = self._act(logits, mask=valid_mask)

        return view.round.discard(index)

    def stop_the_bus(self, view: View) -> bool:
        logits: torch.Tensor = self._forward(view, Phase.STOP)
        action: int = self._act(logits, None)

        log.debug(f"Player {view.player}'s hand: {view.hand}")
        log.debug(
            f"Player {view.player} {'can' if view.can_stop_the_bus else 'cannot'} stop the bus"
        )

        return action == 0
