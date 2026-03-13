from __future__ import annotations


class SearchPaneViewModel:
    """UI state and actions for the search pane."""

    def __init__(self) -> None:
        self._query_text = ""
        self._status_text = "Enter a query and click Search."

    @property
    def query_text(self) -> str:
        return self._query_text

    @property
    def status_text(self) -> str:
        return self._status_text

    def set_query_text(self, text: str) -> None:
        self._query_text = text

    def submit_search(self) -> None:
        query = self._query_text.strip()

        if not query:
            self._status_text = "Please enter a query."
            return

        self._status_text = f"Search requested for: {query}"