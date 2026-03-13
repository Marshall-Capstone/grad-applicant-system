from __future__ import annotations

from .base_pane import BasePane
from grad_applicant_system.presentation.ui.viewmodels.search_pane_viewmodel import (
    SearchPaneViewModel,
)
from grad_applicant_system.presentation.ui.widgets import (
    SeparatorWidget,
    TextWidget,
)


class TranscriptPane(BasePane):
    """Display-only pane for assistant conversation history."""

    def __init__(self, viewmodel: SearchPaneViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel

        self._title_widget = TextWidget("Transcript")
        self._separator_widget = SeparatorWidget()

    def render(self) -> None:
        self.clear_widgets()
        self.extend_widgets([self._title_widget, self._separator_widget])

        if not self._viewmodel.transcript:
            self.add_widget(TextWidget("No messages yet."))
            self.render_widgets()
            return

        for entry in self._viewmodel.transcript:
            prefix = "You" if entry.role == "user" else "Assistant"
            self.add_widget(TextWidget(f"{prefix}: {entry.text}"))

        self.render_widgets()