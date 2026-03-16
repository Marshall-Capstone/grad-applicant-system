from __future__ import annotations

import imgui

from .base_pane import BasePane
from grad_applicant_system.presentation.ui.viewmodels.message_composer_viewmodel import (
    MessageComposerViewModel,
)


class TranscriptPane(BasePane):
    """
    Display-only pane for conversation history.

    Responsibility:
    - Render the running conversation transcript.
    - Show both user and assistant messages in order.
    - Handle transcript auto-scroll behavior in a user-friendly way.

    Architectural role:
    - This is a presentation-layer Pane.
    - It does not own business logic.
    - It reads transcript state from MessageComposerViewModel.
    - It is display-focused: it does not submit actions back to the ViewModel.
    """

    def __init__(self, viewmodel: MessageComposerViewModel) -> None:
        """
        Initialize the transcript pane.

        viewmodel:
            Shared conversation/composer ViewModel that exposes the transcript.

        _last_transcript_count:
            Tracks how many transcript entries existed on the previous frame.
            This lets the pane detect when a new message has been appended so it
            can decide whether to auto-scroll.
        """
        super().__init__()
        self._viewmodel = viewmodel
        self._last_transcript_count = 0
        self._last_transcript_text_length = 0
        self._bubble_width_ratio = 0.72
        self._bubble_min_width = 56.0
        self._bubble_padding = imgui.Vec2(14.0, 10.0)
        self._bubble_rounding = 16.0
        self._bubble_gap = 10.0

    def render(self) -> None:
        """
        Render the transcript pane for the current frame.

        High-level flow:
        1. Read the current transcript snapshot from the ViewModel.
        2. Open a scrollable child region for transcript content.
        3. Detect whether the user was already near the bottom before rendering.
        4. If a new message arrived and the user was near the bottom, auto-scroll.
        5. Otherwise, preserve the user's manual scroll position.

        This behavior is important because:
        - If the user is following the live conversation, new messages should
          naturally appear at the bottom.
        - If the user scrolls upward to read older messages, the UI should not
          forcibly yank them back down.
        """
        transcript = self._viewmodel.transcript
        transcript_count = len(transcript)
        transcript_text_length = sum(len(entry.text) for entry in transcript)

        # Create a scrollable child region that fills the available transcript panel.
        # Width/height of 0.0 means "use all remaining available space".
        imgui.BeginChild("TranscriptScrollRegion", imgui.Vec2(0.0, 0.0))

        # Capture whether the user was already near the bottom before we render
        # the current frame's transcript contents.
        was_near_bottom = self._is_near_bottom()

        # Only auto-scroll when:
        # - the transcript grew since the previous frame
        # - and the user was already near the bottom
        #
        # This avoids disrupting the user if they intentionally scrolled upward.
        should_auto_scroll = ((transcript_count > self._last_transcript_count
                or transcript_text_length > self._last_transcript_text_length) and was_near_bottom)

        if not transcript:
            # Empty-state placeholder shown before the first message is sent.
            imgui.TextWrapped("Start a conversation to see messages here.")
        else:
            for index, entry in enumerate(transcript):
                self._render_message_bubble(index, entry.role, entry.text)

                # If we decided to auto-scroll this frame, only do it when the
                # final transcript item has been rendered.
                if should_auto_scroll and index == transcript_count - 1:
                    imgui.SetScrollHereY(1.0)

                # Add vertical spacing between transcript entries, but not after
                # the final message.
                if index < transcript_count - 1:
                    imgui.Dummy(imgui.Vec2(0.0, self._bubble_gap))

        imgui.EndChild()

        # Store the count from this frame so the next frame can detect whether
        # a new transcript entry has been appended.
        self._last_transcript_count = transcript_count
        self._last_transcript_text_length = transcript_text_length

    def _render_message_bubble(
        self,
        index: int,
        role: str,
        text: str,
    ) -> None:
        """
        Render one transcript entry as a left/right aligned chat bubble.

        user:
            Right-aligned, slightly lighter bubble.

        assistant:
            Left-aligned, slightly darker bubble.
        """
        available_width = imgui.GetContentRegionAvail().x
        start_x = imgui.GetCursorPosX()

        max_bubble_width = max(
            self._bubble_min_width,
            available_width * self._bubble_width_ratio,
        )

        # For short messages, let the bubble shrink somewhat.
        # For long messages, cap it and let TextWrapped handle line wrapping.
        unwrapped_text_width = imgui.CalcTextSize(text).x if text else 0.0
        bubble_width = min(
            max_bubble_width,
            max(
                self._bubble_min_width,
                unwrapped_text_width + (self._bubble_padding.x * 2.0),
            ),
        )

        is_user = role == "user"

        if is_user:
            bubble_x = start_x + max(0.0, available_width - bubble_width)
            bubble_bg = imgui.Vec4(0.18, 0.18, 0.18, 1.0)
            border_color = imgui.Vec4(0.28, 0.28, 0.28, 1.0)
            text_color = imgui.Vec4(0.95, 0.95, 0.95, 1.0)
        else:
            bubble_x = start_x
            bubble_bg = imgui.Vec4(0.13, 0.13, 0.13, 1.0)
            border_color = imgui.Vec4(0.22, 0.22, 0.22, 1.0)
            text_color = imgui.Vec4(0.93, 0.93, 0.93, 1.0)

        imgui.SetCursorPosX(bubble_x)

        imgui.PushStyleVar(imgui.StyleVar.ChildRounding, self._bubble_rounding)
        imgui.PushStyleVar(imgui.StyleVar.ChildBorderSize, 1.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, self._bubble_padding)

        imgui.PushStyleColor(imgui.Col.ChildBg, bubble_bg)
        imgui.PushStyleColor(imgui.Col.Border, border_color)
        imgui.PushStyleColor(imgui.Col.Text, text_color)

        imgui.BeginChild(
            f"TranscriptBubble{index}",
            imgui.Vec2(bubble_width, 0.0),
            imgui.ChildFlags.Borders
            | imgui.ChildFlags.AlwaysUseWindowPadding
            | imgui.ChildFlags.AutoResizeY,
            0,
        )
        imgui.TextWrapped(text)
        imgui.EndChild()

        imgui.PopStyleColor(3)
        imgui.PopStyleVar(3)

    def _is_near_bottom(self, threshold: float = 16.0) -> bool:
        """
        Return whether the transcript scroll position is near the bottom.

        threshold:
            Small tolerance in pixels so the user does not need to be exactly at
            the mathematical maximum scroll position to count as "at bottom".

        Why this helper exists:
        - ImGui reports current scroll offset and max scroll offset.
        - If the current position is within `threshold` of the bottom, we treat
          that as "the user is following the live conversation".
        - If there is no scrollable overflow yet, we also treat that as being
          effectively at the bottom.

        Returns:
            True if the pane is scrolled near the bottom, otherwise False.
        """
        scroll_y = imgui.GetScrollY()
        scroll_max_y = imgui.GetScrollMaxY()
        return scroll_max_y <= 0.0 or scroll_y >= (scroll_max_y - threshold)