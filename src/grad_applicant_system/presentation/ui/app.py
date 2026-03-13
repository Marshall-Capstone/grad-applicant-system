from __future__ import annotations

from grad_applicant_system.presentation.ui.panes.search_pane import SearchPane
from grad_applicant_system.presentation.ui.viewmodels.search_pane_viewmodel import (
    SearchPaneViewModel,
)
from grad_applicant_system.presentation.ui.views.main_view import MainView
from grad_applicant_system.presentation.ui.window import Window


class App:
    """Owns the presentation-layer object graph and UI execution."""

    def __init__(self) -> None:
        self._window = Window(
            title="Grad Applicant System",
            width=1280,
            height=720,
        )

        self._main_view = self._build_main_view()

    def _build_main_view(self) -> MainView:
        search_pane_viewmodel = SearchPaneViewModel()
        search_pane = SearchPane(search_pane_viewmodel)
        return MainView(search_pane)

    def draw_frame(self) -> bool:
        self._main_view.render()
        return False

    def run(self) -> None:
        self._window.run(self.draw_frame)