import torch

from stop_the_bus.Card import Card
from stop_the_bus.Encoding import Phase, ViewModule
from stop_the_bus.Game import View


class NeuralAgent:
    __slots__ = ("net", "device", "greedy", "temperature", "epsilon")

    def __init__(
        self,
        net: ViewModule,
        device: str = "cpu",
        greedy: bool = True,
        temperature: float = 1.0,
        epsilon: float = 0.0,
    ) -> None:
        self.net: ViewModule = net.to(device)
        self.device: str = device
        self.net.eval()
        self.greedy: bool = greedy
        self.temperature: float = temperature
        self.epsilon: float = epsilon

    def _forward(self, view: View, phase: Phase) -> dict[str, torch.Tensor]:
        with torch.no_grad():
            return self.net.forward(view, phase)

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
        output: dict[str, torch.Tensor] = self._forward(view, Phase.DRAW)
        logits: torch.Tensor = output["draw_logits"]
        action: int = self._act(logits, None)
        take_deck: bool = action == 0

        if take_deck:
            return view.round.draw_from_deck(), take_deck

        return view.round.draw_from_discard(), take_deck

    def discard(self, view: View) -> Card:
        output: dict[str, torch.Tensor] = self._forward(view, Phase.DISCARD)
        logits: torch.Tensor = output["discard_logits"]
        valid_mask: torch.Tensor = torch.zeros(
            logits.shape[-1], dtype=torch.bool, device=logits.device
        )
        valid_mask[: len(view.hand)] = True
        index: int = self._act(logits, mask=valid_mask)

        return view.round.discard(index)

    def stop_the_bus(self, view: View) -> bool:
        output: dict[str, torch.Tensor] = self._forward(view, Phase.STOP)
        logits: torch.Tensor = output["stop_logits"]
        action: int = self._act(logits, None)

        return action == 0
