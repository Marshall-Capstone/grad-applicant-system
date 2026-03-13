from __future__ import annotations

from grad_applicant_system.presentation.ui.panes.search_pane import SearchPane
from .base_view import BaseView


class MainView(BaseView):
    """Main application view."""

    def __init__(self, search_pane: SearchPane) -> None:
        super().__init__([search_pane])