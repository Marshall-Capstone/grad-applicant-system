from __future__ import annotations

import imgui

from grad_applicant_system.presentation.ui.panes.message_composer_pane import (
    MessageComposerPane,
)
from grad_applicant_system.presentation.ui.panes.top_menu_pane import TopMenuPane
from grad_applicant_system.presentation.ui.panes.transcript_pane import TranscriptPane
from .base_view import BaseView


class MainView(BaseView):
    """
    Main conversation view for the desktop UI.

    Responsibility:
    - Render the top-level conversation screen.
    - Arrange the major visual regions:
        - top menu bar
        - transcript panel
        - message composer panel
    - Apply the outer shell styling for the app surface.

    Architectural role:
    - This is a presentation-layer View.
    - It owns Pane references compositionally as part of the visible layout tree.
    - It does not contain business logic; it is responsible for layout and styling.
    """

    def __init__(
        self,
        top_menu_pane: TopMenuPane,
        transcript_pane: TranscriptPane,
        message_composer_pane: MessageComposerPane,
    ) -> None:
        """
        Initialize the main view with its major panes.

        top_menu_pane:
            Renders the menu bar controls at the top.

        transcript_pane:
            Renders the conversation history.

        message_composer_pane:
            Renders the unified composer capsule and short status feedback.
        """
        super().__init__([top_menu_pane, transcript_pane, message_composer_pane])

        self._top_menu_pane = top_menu_pane
        self._transcript_pane = transcript_pane
        self._message_composer_pane = message_composer_pane

        # Vertical spacing between the transcript panel and composer panel.
        self._panel_spacing = 14.0

        # Preferred composer region height inside the shell.
        #
        # This is slightly taller than before so the short status line below the
        # composer capsule has room to fit without pushing the shell into a
        # scrollable state.
        self._composer_region_height = 156.0

        # Composer width controls.
        #
        # The centered composer region uses the smaller of:
        # - this absolute max width
        # - this percentage of available shell width
        self._composer_max_width = 680.0
        self._composer_width_ratio = 0.78

        # Transcript width controls.
        #
        # The transcript should still be the dominant visual region, but not so
        # wide that it feels disproportionate relative to the centered composer.
        self._transcript_max_width = 980.0
        self._transcript_width_ratio = 0.92

    def render(self) -> None:
        """
        Render the full main view for the current frame.

        High-level flow:
        1. Render the top menu bar.
        2. Render the main shell window underneath it.
        """
        self._top_menu_pane.render()
        self._render_shell()

    def _render_shell(self) -> None:
        """
        Render the main application shell under the top menu bar.

        This shell is the large background region that contains the transcript
        panel and composer region.

        Layout approach:
        - Fill the window beneath the menu bar.
        - Split the available vertical space into:
            - a large transcript region
            - a smaller composer region
        - Draw the transcript as a centered rounded panel.
        - Draw the composer as a centered region with no outer card.
        """
        display_size = imgui.GetIO().DisplaySize
        menu_bar_height = imgui.GetFrameHeight()

        # Position the shell directly below the menu bar.
        imgui.SetNextWindowPos(imgui.Vec2(0.0, menu_bar_height))

        # Make the shell fill the remainder of the window.
        imgui.SetNextWindowSize(
            imgui.Vec2(
                display_size.x,
                max(0.0, display_size.y - menu_bar_height),
            )
        )

        # This shell is intended to feel like a fixed app surface, not a normal
        # floating ImGui window, so most interactive window chrome is removed.
        #
        # NoScrollbar / NoScrollWithMouse are added so the shell behaves like a
        # fixed layout surface instead of showing an unnecessary outer scrollbar.
        window_flags = (
            imgui.WindowFlags.NoTitleBar
            | imgui.WindowFlags.NoResize
            | imgui.WindowFlags.NoMove
            | imgui.WindowFlags.NoCollapse
            | imgui.WindowFlags.NoSavedSettings
            | imgui.WindowFlags.NoScrollbar
            | imgui.WindowFlags.NoScrollWithMouse
        )

        # Style the outer shell.
        #
        # WindowRounding = 0.0:
        #   The shell itself is a full rectangular app surface.
        #
        # WindowBorderSize = 0.0:
        #   No border line around the shell.
        #
        # WindowPadding:
        #   Inset for the child regions inside the shell.
        imgui.PushStyleVar(imgui.StyleVar.WindowRounding, 0.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowBorderSize, 0.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, imgui.Vec2(22.0, 18.0))
        imgui.PushStyleColor(imgui.Col.WindowBg, imgui.Vec4(0.1294, 0.1294, 0.1294, 1.0))

        began = imgui.Begin("MainShell", flags=window_flags)
        should_render = began[0] if isinstance(began, tuple) else bool(began)

        if should_render:
            available = imgui.GetContentRegionAvail()

            # Compute the runtime composer height responsively.
            #
            # Rules:
            # - prefer self._composer_region_height
            # - but keep it from shrinking too small
            # - and keep it from consuming too much vertical space
            composer_region_height = min(
                self._composer_region_height,
                max(116.0, available.y * 0.24),
            )

            # Give the transcript region the remaining vertical space after
            # accounting for the composer region and spacing gap.
            transcript_height = max(
                180.0,
                available.y - composer_region_height - self._panel_spacing,
            )

            # Compute a centered transcript width.
            #
            # The transcript remains wider than the composer, but is no longer
            # stretched to the full shell width.
            transcript_width = min(
                self._transcript_max_width,
                available.x * self._transcript_width_ratio,
            )
            transcript_width = max(520.0, transcript_width)

            # Top: transcript panel (centered, still card-like)
            self._render_centered_panel(
                panel_id="TranscriptPanel",
                pane=self._transcript_pane,
                width=transcript_width,
                height=transcript_height,
                padding=imgui.Vec2(25.0, 20.0),
            )

            # Spacer between transcript and composer sections.
            imgui.Dummy(imgui.Vec2(0.0, self._panel_spacing))

            # Compute a centered composer width.
            composer_available = imgui.GetContentRegionAvail()
            composer_width = min(
                self._composer_max_width,
                composer_available.x * self._composer_width_ratio,
            )
            composer_width = max(320.0, composer_width)

            # Bottom: composer region (centered, no outer panel)
            self._render_centered_pane(
                pane_id="ComposerRegion",
                pane=self._message_composer_pane,
                width=composer_width,
                height=composer_region_height,
            )

        imgui.End()
        imgui.PopStyleColor(1)
        imgui.PopStyleVar(3)

    def _render_panel(
        self,
        panel_id: str,
        pane,
        height: float,
        padding: imgui.Vec2,
    ) -> None:
        """
        Render one rounded child panel inside the shell.

        panel_id:
            Unique ImGui child identifier.

        pane:
            The pane object whose render() method will draw inside this panel.

        height:
            Requested panel height.
            - 0.0 means "use the remaining available space"
            - positive value means fixed child height

        padding:
            Internal padding for the panel's contents.

        Purpose:
        This helper centralizes the shared panel styling so transcript and
        other full-width card panels can feel visually related.
        """
        # Shared panel appearance:
        # - rounded corners
        # - custom internal padding
        # - dark card-like background
        imgui.PushStyleVar(imgui.StyleVar.ChildRounding, 20.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, padding)
        imgui.PushStyleColor(imgui.Col.ChildBg, imgui.Vec4(0.0941, 0.0941, 0.0941, 1.0))

        imgui.BeginChild(panel_id, imgui.Vec2(0.0, height))
        pane.render()
        imgui.EndChild()

        imgui.PopStyleColor(1)
        imgui.PopStyleVar(2)

    def _render_centered_panel(
        self,
        panel_id: str,
        pane,
        width: float,
        height: float,
        padding: imgui.Vec2,
        ) -> None:
        """
        Render a centered rounded panel with a constrained width.

        This is used for the transcript so it can remain visually dominant
        while no longer spanning the full shell width.
        """
        available = imgui.GetContentRegionAvail()
        start_x = imgui.GetCursorPosX()
        left_offset = max(0.0, (available.x - width) / 2.0)

        imgui.SetCursorPosX(start_x + left_offset)

        # Shared card-like styling for the centered transcript panel.
        imgui.PushStyleVar(imgui.StyleVar.ChildRounding, 20.0)
        imgui.PushStyleVar(imgui.StyleVar.ChildBorderSize, 1.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, padding)

        imgui.PushStyleColor(imgui.Col.ChildBg, imgui.Vec4(0.0941, 0.0941, 0.0941, 1.0))
        imgui.PushStyleColor(imgui.Col.Border, imgui.Vec4(0.20, 0.20, 0.20, 1.0))

        imgui.BeginChild(
        panel_id,
        imgui.Vec2(width, height),
        imgui.ChildFlags.AlwaysUseWindowPadding | imgui.ChildFlags.Borders,
        0,
    )
        pane.render()
        imgui.EndChild()

        imgui.PopStyleColor(2)
        imgui.PopStyleVar(3)

    def _render_centered_pane(
        self,
        pane_id: str,
        pane,
        width: float,
        height: float,
    ) -> None:
        """
        Render a centered pane region with constrained width.

        Unlike _render_centered_panel(), this helper does not draw a visible
        outer card/background. It simply constrains width and centers the pane.
        """
        available = imgui.GetContentRegionAvail()
        start_x = imgui.GetCursorPosX()
        left_offset = max(0.0, (available.x - width) / 2.0)

        imgui.SetCursorPosX(start_x + left_offset)

        # No visible card/background here; this region only constrains width
        # and centers the composer pane under the transcript panel.
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, imgui.Vec2(0.0, 0.0))
        imgui.PushStyleColor(imgui.Col.ChildBg, imgui.Vec4(0.0, 0.0, 0.0, 0.0))

        imgui.BeginChild(pane_id, imgui.Vec2(width, height))
        pane.render()
        imgui.EndChild()

        imgui.PopStyleColor(1)
        imgui.PopStyleVar(1)