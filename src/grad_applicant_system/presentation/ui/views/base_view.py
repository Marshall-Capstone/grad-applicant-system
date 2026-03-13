from __future__ import annotations

from abc import ABC
from typing import Iterable

from grad_applicant_system.presentation.ui.panes import BasePane


class BaseView(ABC):
    """Base container for a screen-level UI view composed from panes."""

    def __init__(self, panes: Iterable[BasePane] | None = None) -> None:
        self._panes: list[BasePane] = list(panes or [])

    @property
    def panes(self) -> tuple[BasePane, ...]:
        """Read-only view of the view's panes."""
        return tuple(self._panes)

    def add_pane(self, pane: BasePane) -> None:
        self._panes.append(pane)

    def extend_panes(self, panes: Iterable[BasePane]) -> None:
        self._panes.extend(panes)

    def clear_panes(self) -> None:
        self._panes.clear()

    def render(self) -> None:
        """Default view rendering: render panes in order."""
        self.render_panes()

    def render_panes(self) -> None:
        for pane in self._panes:
            pane.render()