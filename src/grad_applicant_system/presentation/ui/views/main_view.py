from __future__ import annotations

import imgui

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
        self._top_menu_pane = top_menu_pane
        self._transcript_pane = transcript_pane
        self._search_pane = search_pane
        self._panel_spacing = 16.0
        self._composer_height = 170.0

    def render(self) -> None:
        self._top_menu_pane.render()
        self._render_shell()

    def _render_shell(self) -> None:
        display_size = imgui.GetIO().DisplaySize
        menu_bar_height = imgui.GetFrameHeight()

        imgui.SetNextWindowPos(imgui.Vec2(0.0, menu_bar_height))
        imgui.SetNextWindowSize(
            imgui.Vec2(
                display_size.x,
                max(0.0, display_size.y - menu_bar_height),
            )
        )

        window_flags = (
            imgui.WindowFlags.NoTitleBar
            | imgui.WindowFlags.NoResize
            | imgui.WindowFlags.NoMove
            | imgui.WindowFlags.NoCollapse
            | imgui.WindowFlags.NoSavedSettings
        )

        imgui.PushStyleVar(imgui.StyleVar.WindowRounding, 0.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowBorderSize, 0.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, imgui.Vec2(24.0, 20.0))
        imgui.PushStyleColor(imgui.Col.WindowBg, imgui.Vec4(0.07, 0.09, 0.12, 1.0))

        began = imgui.Begin("MainShell", flags=window_flags)
        should_render = began[0] if isinstance(began, tuple) else bool(began)

        if should_render:
            available = imgui.GetContentRegionAvail()
            composer_height = min(self._composer_height, max(140.0, available.y * 0.28))
            transcript_height = max(
                160.0,
                available.y - composer_height - self._panel_spacing,
            )

            self._render_panel(
                panel_id="TranscriptPanel",
                pane=self._transcript_pane,
                height=transcript_height,
            )

            imgui.Dummy(imgui.Vec2(0.0, self._panel_spacing))

            self._render_panel(
                panel_id="ComposerPanel",
                pane=self._search_pane,
                height=0.0,
            )

        imgui.End()
        imgui.PopStyleColor(1)
        imgui.PopStyleVar(3)

    def _render_panel(self, panel_id: str, pane, height: float) -> None:
        imgui.PushStyleVar(imgui.StyleVar.ChildRounding, 18.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, imgui.Vec2(18.0, 16.0))
        imgui.PushStyleColor(imgui.Col.ChildBg, imgui.Vec4(0.11, 0.13, 0.17, 1.0))

        imgui.BeginChild(panel_id, imgui.Vec2(0.0, height))
        pane.render()
        imgui.EndChild()

        imgui.PopStyleColor(1)
        imgui.PopStyleVar(2)