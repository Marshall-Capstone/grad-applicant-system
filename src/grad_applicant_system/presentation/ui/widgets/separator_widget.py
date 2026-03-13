from __future__ import annotations

import imgui

from .base_widget import BaseWidget


class SeparatorWidget(BaseWidget):
    """Simple horizontal separator widget."""

    def render(self) -> None:
        imgui.Separator()