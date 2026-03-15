from __future__ import annotations

import imgui

from .base_pane import BasePane
from grad_applicant_system.presentation.ui.viewmodels.search_pane_viewmodel import (
    SearchPaneViewModel,
)
from grad_applicant_system.presentation.ui.widgets import (
    ButtonWidget,
    TextInputWidget,
)


class SearchPane(BasePane):
    """Pane for entering a user message and sending it to the assistant."""

    def __init__(self, viewmodel: SearchPaneViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel

        self._query_input_widget = TextInputWidget(
            label="##MessageInput",
            text=self._viewmodel.query_text,
            on_change=self._viewmodel.set_query_text,
        )
        self._send_button_widget = ButtonWidget(
            label="Send",
            on_click=self._viewmodel.submit_message,
            width=96.0,
        )

    def render(self) -> None:
        if self._query_input_widget.text != self._viewmodel.query_text:
            self._query_input_widget.set_text(self._viewmodel.query_text)

        available_width = imgui.GetContentRegionAvail().x
        button_width = 96.0
        gap = 12.0
        input_width = max(120.0, available_width - button_width - gap)

        imgui.PushStyleVar(imgui.StyleVar.FrameRounding, 12.0)
        imgui.PushStyleVar(imgui.StyleVar.FramePadding, imgui.Vec2(12.0, 10.0))
        imgui.PushStyleVar(imgui.StyleVar.FrameBorderSize, 0.0)

        imgui.PushStyleColor(imgui.Col.FrameBg, imgui.Vec4(0.15, 0.18, 0.23, 1.0))
        imgui.PushStyleColor(imgui.Col.FrameBgHovered, imgui.Vec4(0.17, 0.20, 0.26, 1.0))
        imgui.PushStyleColor(imgui.Col.FrameBgActive, imgui.Vec4(0.18, 0.22, 0.28, 1.0))

        imgui.BeginDisabled(self._viewmodel.is_busy)
        imgui.SetNextItemWidth(input_width)
        self._query_input_widget.render()
        imgui.EndDisabled()

        imgui.PopStyleColor(3)
        imgui.PopStyleVar(3)

        imgui.SameLine()

        imgui.BeginDisabled(not self._viewmodel.can_send)
        self._send_button_widget.render()
        imgui.EndDisabled()

        status_text = self._viewmodel.status_text.strip()
        if not status_text:
            return

        imgui.Dummy(imgui.Vec2(0.0, 8.0))

        if self._viewmodel.last_error is not None:
            imgui.PushStyleColor(imgui.Col.Text, imgui.Vec4(0.92, 0.52, 0.52, 1.0))
        else:
            imgui.PushStyleColor(imgui.Col.Text, imgui.Vec4(0.72, 0.76, 0.84, 1.0))

        imgui.TextWrapped(status_text)
        imgui.PopStyleColor(1)