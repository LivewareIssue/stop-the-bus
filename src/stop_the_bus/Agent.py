from typing import Protocol

from typing_extensions import runtime_checkable

from stop_the_bus.Card import Card
from stop_the_bus.Game import View


class Agent(Protocol):
    def draw(self, view: View) -> tuple[Card, bool]: ...

    def discard(self, view: View) -> Card: ...

    def stop_the_bus(self, view: View) -> bool: ...


@runtime_checkable
class SupportsBeginTurn(Protocol):
    def begin_turn(self: Agent, view: "View") -> None: ...
