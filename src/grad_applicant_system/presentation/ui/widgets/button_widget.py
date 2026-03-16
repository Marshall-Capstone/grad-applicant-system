from __future__ import annotations

from typing import Callable

import imgui as im

from .base_widget import BaseWidget


Color4 = tuple[float, float, float, float]


class ButtonWidget(BaseWidget):
    """Simple clickable button widget with optional per-instance styling."""

    def __init__(
        self,
        label: str,
        on_click: Callable[[], None] | None = None,
        width: float = 0.0,
        height: float = 0.0,
        *,
        button_color: Color4 | None = None,
        button_hovered_color: Color4 | None = None,
        button_active_color: Color4 | None = None,
        text_color: Color4 | None = None,
        rounding: float | None = None,
    ) -> None:
        self._label = label
        self._on_click = on_click
        self._width = width
        self._height = height

        self._button_color = button_color
        self._button_hovered_color = button_hovered_color
        self._button_active_color = button_active_color
        self._text_color = text_color
        self._rounding = rounding

    @property
    def label(self) -> str:
        return self._label

    def set_label(self, label: str) -> None:
        self._label = label

    def set_on_click(self, on_click: Callable[[], None] | None) -> None:
        self._on_click = on_click

    def render(self) -> None:
        pushed_style_colors = 0
        pushed_style_vars = 0

        if self._button_color is not None:
            im.PushStyleColor(im.Col.Button, im.Vec4(*self._button_color))
            pushed_style_colors += 1

        if self._button_hovered_color is not None:
            im.PushStyleColor(im.Col.ButtonHovered, im.Vec4(*self._button_hovered_color))
            pushed_style_colors += 1

        if self._button_active_color is not None:
            im.PushStyleColor(im.Col.ButtonActive, im.Vec4(*self._button_active_color))
            pushed_style_colors += 1

        if self._text_color is not None:
            im.PushStyleColor(im.Col.Text, im.Vec4(*self._text_color))
            pushed_style_colors += 1

        if self._rounding is not None:
            im.PushStyleVar(im.StyleVar.FrameRounding, self._rounding)
            pushed_style_vars += 1

        clicked = im.Button(self._label, im.Vec2(self._width, self._height))

        if pushed_style_vars:
            im.PopStyleVar(pushed_style_vars)

        if pushed_style_colors:
            im.PopStyleColor(pushed_style_colors)

        if clicked and self._on_click is not None:
            self._on_click()