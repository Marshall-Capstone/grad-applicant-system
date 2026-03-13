from __future__ import annotations

from grad_applicant_system.presentation.ui.panes import BasePane
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
    """Pane for entering a search query and triggering a search action."""

    def __init__(self, viewmodel: SearchPaneViewModel) -> None:
        super().__init__()
        self._viewmodel = viewmodel

        self._title_widget = TextWidget("Applicant Search")
        self._separator_widget = SeparatorWidget()
        self._query_input_widget = TextInputWidget(
            label="Query",
            text=self._viewmodel.query_text,
            on_change=self._viewmodel.set_query_text,
        )
        self._search_button_widget = ButtonWidget(
            label="Search",
            on_click=self._viewmodel.submit_search,
        )
        self._status_widget = TextWidget(self._viewmodel.status_text)

        self.extend_widgets(
            [
                self._title_widget,
                self._separator_widget,
                self._query_input_widget,
                self._search_button_widget,
                self._status_widget,
            ]
        )

    def render(self) -> None:
        self._status_widget.set_text(self._viewmodel.status_text)
        self.render_widgets()