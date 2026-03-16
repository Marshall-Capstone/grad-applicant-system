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
        icon: str | None = None,
        icon_color: Color4 | None = None,
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

        # Optional custom-drawn icon rendered on top of the button.
        # Example: "send_arrow"
        self._icon = icon
        self._icon_color = icon_color

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

        # Draw a custom icon after the button has been submitted so we can use
        # the final item rectangle as our drawing bounds.
        if self._icon == "send_arrow":
            self._draw_send_arrow()

        if pushed_style_vars:
            im.PopStyleVar(pushed_style_vars)

        if pushed_style_colors:
            im.PopStyleColor(pushed_style_colors)

        if clicked and self._on_click is not None:
            self._on_click()

    def _draw_send_arrow(self) -> None:
        """Draw a simple upward send arrow centered inside the last button."""
        draw_list = im.GetWindowDrawList()
        rect_min = im.GetItemRectMin()
        rect_max = im.GetItemRectMax()

        center_x = (rect_min.x + rect_max.x) * 0.5
        center_y = (rect_min.y + rect_max.y) * 0.5 + 1.5
        width = rect_max.x - rect_min.x
        height = rect_max.y - rect_min.y

        # Arrow sizing is proportional to the button size so it scales cleanly.
        shaft_half_height = height * 0.18
        head_height = height * 0.18
        head_half_width = width * 0.14
        line_thickness = max(2.0, width * 0.06)

        shaft_bottom_y = center_y + shaft_half_height
        shaft_top_y = center_y - shaft_half_height
        head_tip_y = shaft_top_y - head_height

        color = self._resolve_icon_color()

        # Vertical shaft
        draw_list.AddLine(
            im.Vec2(center_x, shaft_bottom_y),
            im.Vec2(center_x, shaft_top_y),
            color,
            line_thickness,
        )

        # Filled triangular arrow head
        draw_list.AddTriangleFilled(
            im.Vec2(center_x, head_tip_y),
            im.Vec2(center_x - head_half_width, shaft_top_y),
            im.Vec2(center_x + head_half_width, shaft_top_y),
            color,
        )

    def _resolve_icon_color(self):
        """Choose the icon color as packed ImGui color."""
        if self._icon_color is not None:
            return im.GetColorU32(im.Vec4(*self._icon_color))

        if self._text_color is not None:
            return im.GetColorU32(im.Vec4(*self._text_color))

        return im.GetColorU32(im.Vec4(1.0, 1.0, 1.0, 1.0))