import logging

import torch

from stop_the_bus.Card import Card
from stop_the_bus.Encoding import Phase, ViewModule
from stop_the_bus.Game import Game, View
from stop_the_bus.SimpleAgent import SimpleAgent

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
            log.warning(f"Invalid probabilities: {p}")
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
        mask: torch.Tensor = torch.tensor([view.can_stop_the_bus, True], device=logits.device)
        action: int = self._act(logits, mask=mask)
        return action == 0 and view.round.stop_the_bus()


class _ImitationAgent(SimpleAgent):
    """A SimpleAgent wrapper that trains a model to imitate its behaviour."""

    def __init__(
        self,
        net: ViewModule,
        optim: torch.optim.Optimizer,
        loss_fn: torch.nn.CrossEntropyLoss,
    ) -> None:
        super().__init__()
        self.net: ViewModule = net
        self.optim: torch.optim.Optimizer = optim
        self.loss_fn: torch.nn.CrossEntropyLoss = loss_fn

    def _update(self, logits: torch.Tensor, target: torch.Tensor) -> None:
        self.optim.zero_grad()
        loss: torch.Tensor = self.loss_fn(logits, target)
        loss.backward()
        self.optim.step()

    def draw(self, view: View) -> tuple[Card, bool]:  # type: ignore[override]
        logits: torch.Tensor = self.net(view, Phase.DRAW)
        card, from_deck = super().draw(view)
        target = torch.tensor([0 if from_deck else 1], device=logits.device)
        self._update(logits, target)
        return card, from_deck

    def discard(self, view: View) -> Card:  # type: ignore[override]
        logits: torch.Tensor = self.net(view, Phase.DISCARD)
        hand_before: list[Card] = list(view.hand)
        card: Card = super().discard(view)
        index: int = hand_before.index(card)
        target = torch.tensor([index], device=logits.device)
        self._update(logits, target)
        return card

    def stop_the_bus(self, view: View) -> bool:  # type: ignore[override]
        logits: torch.Tensor = self.net(view, Phase.STOP)
        stop: bool = super().stop_the_bus(view)
        target = torch.tensor([0 if stop else 1], device=logits.device)
        self._update(logits, target)
        return stop


def train_with_simple_agent(
    net: ViewModule,
    rounds: int = 100,
    max_turns: int = 100,
    lr: float = 1e-3,
) -> ViewModule:
    """Train ``net`` to imitate :class:`SimpleAgent`.

    The network is updated in-place by observing a ``SimpleAgent`` play multiple
    rounds of the game.  For each decision point the SimpleAgent's action is
    treated as the correct label for supervised learning.

    Parameters
    ----------
    net:
        The model to train.
    rounds:
        Number of rounds to simulate for training.
    max_turns:
        Maximum number of turns per round.
    lr:
        Learning rate for Adam optimiser.

    Returns
    -------
    ViewModule
        The trained network (the same instance as ``net``).
    """

    net.train()
    optim: torch.optim.Optimizer = torch.optim.Adam(net.parameters(), lr=lr)
    loss_fn: torch.nn.CrossEntropyLoss = torch.nn.CrossEntropyLoss()

    # Use four imitation agents to gather diverse experiences.
    agents: list[_ImitationAgent] = [
        _ImitationAgent(net, optim, loss_fn) for _ in range(4)
    ]

    for _ in range(rounds):
        game = Game(len(agents))
        round = game.start_round()

        # First turn only has discard and stop phases
        view: View = round.current_view()
        agent: _ImitationAgent = agents[round.current_index]
        agent.discard(view)
        agent.stop_the_bus(view)
        round.advance_turn()

        turns: int = 1
        while round.has_turns_remaining and turns < max_turns:
            view = round.current_view()
            agent = agents[round.current_index]
            agent.draw(view)
            agent.discard(view)
            agent.stop_the_bus(view)
            round.advance_turn()
            turns += 1

    net.eval()
    return net


__all__ = ["NeuralAgent", "train_with_simple_agent"]
