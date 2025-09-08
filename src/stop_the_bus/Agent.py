from typing import Protocol

from typing_extensions import runtime_checkable

from stop_the_bus.Game import View


class Agent(Protocol):
    def draw(self, view: View) -> None: ...

    def discard(self, view: View) -> None: ...

    def stop_the_bus(self, view: View) -> None: ...


@runtime_checkable
class SupportsBeginTurn(Protocol):
    def begin_turn(self: Agent, view: "View", show_discard_pile: bool = True) -> None: ...
