from __future__ import annotations

import imgui

from .base_widget import BaseWidget


class TextWidget(BaseWidget):
    """Simple text display widget."""

    def __init__(self, text: str = "") -> None:
        self._text = text

    @property
    def text(self) -> str:
        return self._text

    def set_text(self, text: str) -> None:
        self._text = text

    def render(self) -> None:
        imgui.Text(self._text)