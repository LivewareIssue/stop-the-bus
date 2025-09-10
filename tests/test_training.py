import random

import torch

from stop_the_bus.Encoding import Phase, ViewModule
from stop_the_bus.Game import Game
from stop_the_bus.NeuralAgent import train_with_simple_agent
from stop_the_bus.SimpleAgent import SimpleAgent


def _evaluate(net: ViewModule) -> float:
    """Return the fraction of actions matching SimpleAgent on a fresh game."""
    teacher = SimpleAgent()
    game = Game(1)
    round = game.start_round()
    correct = 0
    total = 0

    view = round.current_view()
    logits = net(view, Phase.DISCARD)
    pred = int(torch.argmax(logits).item())
    hand_before = list(view.hand)
    card = teacher.discard(view)
    label = hand_before.index(card)
    correct += pred == label
    total += 1

    logits = net(view, Phase.STOP)
    pred = int(torch.argmax(logits).item())
    stop = teacher.stop_the_bus(view)
    label = 0 if stop else 1
    correct += pred == label
    total += 1

    round.advance_turn()
    for _ in range(20):
        if not round.has_turns_remaining:
            break
        view = round.current_view()

        logits = net(view, Phase.DRAW)
        pred = int(torch.argmax(logits).item())
        card, from_deck = teacher.draw(view)
        label = 0 if from_deck else 1
        correct += pred == label
        total += 1

        logits = net(view, Phase.DISCARD)
        pred = int(torch.argmax(logits).item())
        hand_before = list(view.hand)
        card = teacher.discard(view)
        label = hand_before.index(card)
        correct += pred == label
        total += 1

        logits = net(view, Phase.STOP)
        pred = int(torch.argmax(logits).item())
        stop = teacher.stop_the_bus(view)
        label = 0 if stop else 1
        correct += pred == label
        total += 1

        round.advance_turn()

    return correct / total


def test_train_with_simple_agent_improves_accuracy():
    random.seed(0)
    torch.manual_seed(0)
    net = ViewModule()

    train_with_simple_agent(net, rounds=10, max_turns=20, lr=1e-2)
    accuracy = _evaluate(net)

    assert accuracy > 0.4
