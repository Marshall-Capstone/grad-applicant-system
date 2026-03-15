from __future__ import annotations

from grad_applicant_system.presentation.ui.panes.search_pane import SearchPane
from grad_applicant_system.presentation.ui.panes.top_menu_pane import TopMenuPane
from grad_applicant_system.presentation.ui.panes.transcript_pane import TranscriptPane
from .base_view import BaseView


class MainView(BaseView):
    """Main application view."""

    def __init__(
        self,
        top_menu_pane: TopMenuPane,
        transcript_pane: TranscriptPane,
        search_pane: SearchPane,
    ) -> None:
        super().__init__([top_menu_pane, transcript_pane, search_pane])