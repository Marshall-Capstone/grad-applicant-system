from __future__ import annotations

import imgui

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
        self._last_transcript_count = 0

        self._title_widget = TextWidget("Transcript")
        self._separator_widget = SeparatorWidget()

    def render(self) -> None:
        transcript = self._viewmodel.transcript
        transcript_count = len(transcript)

        self._title_widget.render()
        self._separator_widget.render()

        imgui.BeginChild("TranscriptScrollRegion", imgui.Vec2(0.0, 0.0))

        was_near_bottom = self._is_near_bottom()
        should_auto_scroll = (
            transcript_count > self._last_transcript_count and was_near_bottom
        )

        if not transcript:
            imgui.Text("No messages yet.")
        else:
            for index, entry in enumerate(transcript):
                prefix = "You" if entry.role == "user" else "Assistant"
                imgui.TextWrapped(f"{prefix}: {entry.text}")

                if should_auto_scroll and index == transcript_count - 1:
                    imgui.SetScrollHereY(1.0)

                if index < transcript_count - 1:
                    imgui.Spacing()

        imgui.EndChild()
        self._last_transcript_count = transcript_count

    def _is_near_bottom(self, threshold: float = 16.0) -> bool:
        scroll_y = imgui.GetScrollY()
        scroll_max_y = imgui.GetScrollMaxY()
        return scroll_max_y <= 0.0 or scroll_y >= (scroll_max_y - threshold)