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
        )

    def render(self) -> None:
        if self._query_input_widget.text != self._viewmodel.query_text:
            self._query_input_widget.set_text(self._viewmodel.query_text)

        available_width = imgui.GetContentRegionAvail().x
        button_width = 96.0
        gap = 12.0
        input_width = max(120.0, available_width - button_width - gap)

        imgui.BeginDisabled(self._viewmodel.is_busy)
        imgui.SetNextItemWidth(input_width)
        self._query_input_widget.render()
        imgui.EndDisabled()

        imgui.SameLine()

        imgui.BeginDisabled(not self._viewmodel.can_send)
        self._send_button_widget.render()
        imgui.EndDisabled()

        imgui.Dummy(imgui.Vec2(0.0, 8.0))
        imgui.TextWrapped(self._viewmodel.status_text)