from __future__ import annotations

import os

from grad_applicant_system.infrastructure.assistant import (
    AnthropicApplicantAssistantService,
    FakeApplicantAssistantService,
)
from grad_applicant_system.infrastructure.mcp import McpToolClient
from grad_applicant_system.presentation.ui.panes.search_pane import SearchPane
from grad_applicant_system.presentation.ui.panes.transcript_pane import TranscriptPane
from grad_applicant_system.presentation.ui.panes.top_menu_pane import TopMenuPane
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
        self._search_pane_viewmodel: SearchPaneViewModel | None = None
        self._main_view = self._build_main_view()

    def _build_main_view(self) -> MainView:
        assistant_service = self._build_assistant_service()

        search_pane_viewmodel = SearchPaneViewModel(assistant_service)
        self._search_pane_viewmodel = search_pane_viewmodel

        top_menu_pane = TopMenuPane(search_pane_viewmodel)
        transcript_pane = TranscriptPane(search_pane_viewmodel)
        search_pane = SearchPane(search_pane_viewmodel)

        return MainView(
            top_menu_pane=top_menu_pane,
            transcript_pane=transcript_pane,
            search_pane=search_pane,
        )

    def _build_assistant_service(self):
        use_real_assistant = (
            os.getenv("USE_REAL_ASSISTANT", "false").strip().lower() == "true"
        )

        if not use_real_assistant:
            return FakeApplicantAssistantService()

        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
        anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        try:
            mcp_tool_client = McpToolClient(mcp_server_url)
            return AnthropicApplicantAssistantService(
                mcp_tool_client=mcp_tool_client,
                model=anthropic_model,
            )
        except Exception as exc:
            print(f"Falling back to fake assistant: {exc}")
            return FakeApplicantAssistantService()

    def draw_frame(self) -> bool:
        if self._search_pane_viewmodel is not None:
            self._search_pane_viewmodel.update()

        self._main_view.render()
        return False

    def run(self) -> None:
        self._window.run(self.draw_frame)