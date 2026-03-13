from __future__ import annotations

from abc import ABC, abstractmethod


class BaseWidget(ABC):
    """Base contract for all UI widgets."""

    @abstractmethod
    def render(self) -> None:
        """Render the widget for the current ImGui frame."""
        raise NotImplementedError