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
        should_auto_scroll = (
            transcript_count > self._last_transcript_count and was_near_bottom
        )

        if not transcript:
            # Empty-state placeholder shown before the first message is sent.
            imgui.TextWrapped("Start a conversation to see messages here.")
        else:
            for index, entry in enumerate(transcript):
                # Translate the stored transcript role into a user-facing prefix.
                prefix = "You" if entry.role == "user" else "Assistant"

                # Render one transcript line.
                # This is currently a simple text-based conversation display.
                imgui.TextWrapped(f"{prefix}: {entry.text}")

                # If we decided to auto-scroll this frame, only do it when the
                # final transcript item has been rendered.
                #
                # SetScrollHereY(1.0) means:
                # "scroll so this item is visible, aligned near the bottom".
                if should_auto_scroll and index == transcript_count - 1:
                    imgui.SetScrollHereY(1.0)

                # Add vertical spacing between transcript entries, but not after
                # the final message.
                if index < transcript_count - 1:
                    imgui.Dummy(imgui.Vec2(0.0, 10.0))

        imgui.EndChild()

        # Store the count from this frame so the next frame can detect whether
        # a new transcript entry has been appended.
        self._last_transcript_count = transcript_count

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