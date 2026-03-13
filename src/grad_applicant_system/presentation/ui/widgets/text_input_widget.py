from __future__ import annotations

from typing import Callable

import imgui as im

from .base_widget import BaseWidget


class TextInputWidget(BaseWidget):
    """Simple single-line text input widget."""

    def __init__(
        self,
        label: str,
        text: str = "",
        on_change: Callable[[str], None] | None = None,
        max_size: int = 256,
    ) -> None:
        self._label = label
        self._buffer = im.StrRef(text, maxSize=max_size)
        self._on_change = on_change

    @property
    def text(self) -> str:
        return str(self._buffer)

    def set_text(self, text: str) -> None:
        self._buffer = im.StrRef(text, maxSize=len(text) + 256)

    def set_on_change(self, on_change: Callable[[str], None] | None) -> None:
        self._on_change = on_change

    def render(self) -> None:
        changed = im.InputText(self._label, self._buffer)
        if changed and self._on_change is not None:
            self._on_change(str(self._buffer))