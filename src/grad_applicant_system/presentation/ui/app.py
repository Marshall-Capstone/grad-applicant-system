from __future__ import annotations

import os
from pathlib import Path
import imgui

from grad_applicant_system.application.ports import ApplicantAssistantService
from grad_applicant_system.infrastructure.assistant import (
    AnthropicApplicantAssistantService,
    FakeApplicantAssistantService,
)
from grad_applicant_system.infrastructure.mcp import McpToolClient
from grad_applicant_system.presentation.ui.panes.message_composer_pane import (
    MessageComposerPane,
)
from grad_applicant_system.presentation.ui.panes.top_menu_pane import TopMenuPane
from grad_applicant_system.presentation.ui.panes.transcript_pane import TranscriptPane
from grad_applicant_system.presentation.ui.viewmodels.message_composer_viewmodel import (
    MessageComposerViewModel,
)
from grad_applicant_system.presentation.ui.views.main_view import MainView
from grad_applicant_system.presentation.ui.window import Window


class App:
    """Owns the presentation-layer object graph and UI execution."""

    def __init__(self) -> None:
        self._window = Window(title="Grad Applicant System", width=1280, height=720)
        self._message_composer_viewmodel: MessageComposerViewModel | None = None
        #self._emblem_texture = self._load_emblem_texture()
        self._emblem_texture = None
        self._emblem_load_attempted = False
        self._main_view = self._build_main_view()

    def _load_emblem_texture(self):
        """
        Load the shell emblem texture once at startup.

        Returns None if the asset is missing or the texture load fails, so the
        UI can continue running without the emblem.
        """
        asset_path = (
            Path(__file__).resolve().parents[4]
            / "assets"
            / "ui"
            / "emblem.png"
        )

        if not asset_path.exists():
            print(f"Emblem asset not found: {asset_path}")
            return None

        try:
            return imgui.LoadTextureFile(str(asset_path))
        except Exception as exc:
            print(f"Failed to load emblem texture: {exc}")
            return None

    def _build_main_view(self) -> MainView:
        assistant_service = self._build_assistant_service()

        message_composer_viewmodel = MessageComposerViewModel(assistant_service)
        self._message_composer_viewmodel = message_composer_viewmodel

        top_menu_pane = TopMenuPane(message_composer_viewmodel)
        transcript_pane = TranscriptPane(message_composer_viewmodel)
        message_composer_pane = MessageComposerPane(message_composer_viewmodel)

        return MainView(
            top_menu_pane=top_menu_pane,
            transcript_pane=transcript_pane,
            message_composer_pane=message_composer_pane,
            emblem_texture=self._emblem_texture,)
        

    def _build_assistant_service(self) -> ApplicantAssistantService:
        use_real_assistant = (os.getenv("USE_REAL_ASSISTANT", "false").strip().lower() == "true")

        if not use_real_assistant:
            return FakeApplicantAssistantService()

        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
        anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

        try:
            mcp_tool_client = McpToolClient(mcp_server_url)
            return AnthropicApplicantAssistantService(mcp_tool_client=mcp_tool_client,model=anthropic_model)
        except Exception as exc:
            print(f"Falling back to fake assistant: {exc}")
            return FakeApplicantAssistantService()

    def draw_frame(self) -> bool:
        if not self._emblem_load_attempted:
            self._emblem_load_attempted = True
            self._emblem_texture = self._load_emblem_texture()
            if self._emblem_texture is not None:
                self._main_view.set_emblem_texture(self._emblem_texture)

        if self._message_composer_viewmodel is not None:
            self._message_composer_viewmodel.update()

        self._main_view.render()
        return False

    def run(self) -> None:
        self._window.run(self.draw_frame)