from __future__ import annotations

from abc import ABC
from typing import Iterable

from grad_applicant_system.presentation.ui.widgets import BaseWidget


class BasePane(ABC):
    """Base container for a reusable section of UI composed from widgets."""

    def __init__(self, widgets: Iterable[BaseWidget] | None = None) -> None:
        self._widgets: list[BaseWidget] = list(widgets or [])

    @property
    def widgets(self) -> tuple[BaseWidget, ...]:
        """Read-only view of the pane's widgets."""
        return tuple(self._widgets)

    def add_widget(self, widget: BaseWidget) -> None:
        self._widgets.append(widget)

    def extend_widgets(self, widgets: Iterable[BaseWidget]) -> None:
        self._widgets.extend(widgets)

    def clear_widgets(self) -> None:
        self._widgets.clear()

    def render(self) -> None:
        """Default pane rendering: render widgets in order."""
        self.render_widgets()

    def render_widgets(self) -> None:
        for widget in self._widgets:
            widget.render()