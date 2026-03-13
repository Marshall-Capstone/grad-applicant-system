from __future__ import annotations

from typing import Callable

import imgui as im

from .base_widget import BaseWidget


class ButtonWidget(BaseWidget):
    """Simple clickable button widget."""

    def __init__(
        self,
        label: str,
        on_click: Callable[[], None] | None = None,
        width: float = 0.0,
        height: float = 0.0,
    ) -> None:
        self._label = label
        self._on_click = on_click
        self._width = width
        self._height = height

    @property
    def label(self) -> str:
        return self._label

    def set_label(self, label: str) -> None:
        self._label = label

    def set_on_click(self, on_click: Callable[[], None] | None) -> None:
        self._on_click = on_click

    def render(self) -> None:
        clicked = im.Button(self._label, im.Vec2(self._width, self._height))
        if clicked and self._on_click is not None:
            self._on_click()