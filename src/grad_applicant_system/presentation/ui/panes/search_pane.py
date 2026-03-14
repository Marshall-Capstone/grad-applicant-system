from __future__ import annotations

import imgui

from .base_pane import BasePane
from grad_applicant_system.presentation.ui.viewmodels.search_pane_viewmodel import (
    SearchPaneViewModel,
)
from grad_applicant_system.presentation.ui.widgets import (
    ButtonWidget,
    SeparatorWidget,
    TextInputWidget,
    TextWidget,
)


class SearchPane(BasePane):
    """Pane for entering a user message and sending it to the assistant."""

    def __init__(self, viewmodel: SearchPaneViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel

        self._title_widget = TextWidget("Applicant Assistant")
        self._separator_widget = SeparatorWidget()
        self._query_input_widget = TextInputWidget(
            label="Message",
            text=self._viewmodel.query_text,
            on_change=self._viewmodel.set_query_text,
        )
        self._send_button_widget = ButtonWidget(
            label="Send",
            on_click=self._viewmodel.submit_message,
        )
        self._status_widget = TextWidget(self._viewmodel.status_text)

        self.extend_widgets(
            [
                self._title_widget,
                self._separator_widget,
                self._query_input_widget,
                self._send_button_widget,
                self._status_widget,
            ]
        )

    def render(self) -> None:
        if self._query_input_widget.text != self._viewmodel.query_text:
            self._query_input_widget.set_text(self._viewmodel.query_text)

        self._status_widget.set_text(self._viewmodel.status_text)

        self._title_widget.render()
        self._separator_widget.render()

        imgui.BeginDisabled(self._viewmodel.is_busy)
        self._query_input_widget.render()
        imgui.EndDisabled()

        imgui.BeginDisabled(not self._viewmodel.can_send)
        self._send_button_widget.render()
        imgui.EndDisabled()

        self._status_widget.render()