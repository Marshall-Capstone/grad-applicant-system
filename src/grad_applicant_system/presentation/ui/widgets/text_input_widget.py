from __future__ import annotations

from typing import Callable

import imgui as im

from .base_widget import BaseWidget


class TextInputWidget(BaseWidget):
    """Text input widget that can render as single-line or multiline."""

    def __init__(
        self,
        label: str,
        text: str = "",
        on_change: Callable[[str], None] | None = None,
        max_size: int = 256,
        *,
        multiline: bool = False,
        width: float = 0.0,
        height: float = 0.0,
        flags: int = 0,
    ) -> None:
        self._label = label
        self._buffer = im.StrRef(text, maxSize=max_size)
        self._on_change = on_change
        self._multiline = multiline
        self._width = width
        self._height = height
        self._flags = flags

    @property
    def text(self) -> str:
        return str(self._buffer)

    def set_text(self, text: str) -> None:
        self._buffer = im.StrRef(text, maxSize=len(text) + 256)

    def set_on_change(self, on_change: Callable[[str], None] | None) -> None:
        self._on_change = on_change

    def set_size(self, width: float, height: float = 0.0) -> None:
        self._width = width
        self._height = height

    def set_flags(self, flags: int) -> None:
        self._flags = flags

    def render(self) -> bool:
        previous_text = str(self._buffer)

        if self._multiline:
            activated = im.InputTextMultiline(
                self._label,
                self._buffer,
                im.Vec2(self._width, self._height),
                self._flags,
            )
        else:
            activated = im.InputText(
                self._label,
                self._buffer,
                self._flags,
            )

        current_text = str(self._buffer)

        if current_text != previous_text and self._on_change is not None:
            self._on_change(current_text)

        return bool(activated)