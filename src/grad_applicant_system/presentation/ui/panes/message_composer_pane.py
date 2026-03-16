from __future__ import annotations

import imgui

from .base_pane import BasePane
from grad_applicant_system.presentation.ui.viewmodels.message_composer_viewmodel import (
    MessageComposerViewModel,
)
from grad_applicant_system.presentation.ui.widgets import (
    ButtonWidget,
    TextInputWidget,
)


class MessageComposerPane(BasePane):
    """
    Conversation composer pane.

    Responsibility:
    - Render the unified message-entry capsule at the bottom of the UI.
    - Bind the text input and send button to MessageComposerViewModel.
    - Reflect interaction state such as busy/disabled/status text.

    Architectural role:
    - This is a presentation-layer Pane.
    - It owns its Widgets compositionally.
    - It references a ViewModel aggregately.
    - It should not contain business logic; it only renders and forwards UI actions.
    """

    def __init__(self, viewmodel: MessageComposerViewModel) -> None:
        """
        Build the pane and compose its child widgets.

        The pane keeps:
        - one multiline text input widget for the current draft message
        - one round send button widget for submission

        The widgets are initialized from the ViewModel so the pane stays
        synchronized with the current UI state.
        """
        super().__init__()
        self._viewmodel = viewmodel

        # Multiline input field used as the message draft area.
        # `on_change` pushes user edits back into the ViewModel.
        self._query_input_widget = TextInputWidget(
            label="##MessageInput",
            text=self._viewmodel.query_text,
            on_change=self._viewmodel.set_query_text,
            max_size=1024,
            multiline=True,
            flags=(
                imgui.InputTextFlags.EnterReturnsTrue
                | imgui.InputTextFlags.CtrlEnterForNewLine
                | imgui.InputTextFlags.NoHorizontalScroll),)

        self._composer_placeholder_text = ("Ask about applicants, programs, GPA, or review status...")

        # Request keyboard focus for the composer input.
        #
        # Start as True so the user can type immediately on first launch
        # without clicking into the composer first.
        self._should_focus_input = True

        # Accent send button placed inside the composer capsule.
        # These values are primarily visual styling knobs.
        self._send_button_widget = ButtonWidget(
        label="##SendButton",
        on_click=self._submit_message,
        width=40.0,
        height=40.0,
        button_color=(0.18, 0.66, 0.43, 1.0),
        button_hovered_color=(0.22, 0.73, 0.48, 1.0),
        button_active_color=(0.14, 0.58, 0.37, 1.0),
        text_color=(0.97, 0.99, 0.98, 1.0),
        rounding=20.0,
        icon="send_arrow",
        icon_color=(0.97, 0.99, 0.98, 1.0),)

    def render(self) -> None:
        """
        Render the composer pane for the current frame.

        High-level flow:
        1. Sync widget text from the ViewModel if the ViewModel changed externally.
        2. Render a rounded "capsule" child region as the unified composer surface.
        3. Render the multiline text input inside the capsule.
        4. Render the round send button inside the same capsule.
        5. Render short status text below the capsule, if present.

        Notes on ImGui:
        - ImGui is immediate-mode, so this whole method runs every frame.
        - Layout is controlled by the current ImGui cursor position.
        - The button is manually positioned inside the capsule using SetCursorPos().
        """
        # Keep the widget's local text buffer aligned with the ViewModel.
        # This matters if the ViewModel clears or changes the text outside direct typing.
        if self._query_input_widget.text != self._viewmodel.query_text:
            self._query_input_widget.set_text(self._viewmodel.query_text)

        # ===== Composer capsule layout constants =====
        #
        # These are the main "tweak to taste" values for the overall look.
        #
        # capsule_height:
        #   Total height of the rounded composer container.
        #
        # inner_pad_x / inner_pad_y:
        #   Padding from the capsule edge to internal content.
        #
        # button_size:
        #   Intended visual size of the send button inside the capsule.
        #   This should generally match the widget's width/height above.
        #
        # button_right_inset / button_bottom_inset:
        #   Distance from the capsule's right/bottom edges to the button.
        #
        # button_gap:
        #   Reserved spacing between the text region and the button region.
        capsule_height = 76.0
        inner_pad_x = 14.0
        inner_pad_y = 12.0
        button_size = 40.0
        button_right_inset = 10.0
        button_bottom_inset = 10.0
        button_gap = 12.0

        # Style the outer composer capsule itself.
        # ChildRounding controls the rounded-capsule look.
        # ChildBorderSize + Border color create a subtle trim.
        # WindowPadding is set to zero so we can fully control internal placement.
        imgui.PushStyleVar(imgui.StyleVar.ChildRounding, 22.0)
        imgui.PushStyleVar(imgui.StyleVar.ChildBorderSize, 1.0)
        imgui.PushStyleVar(imgui.StyleVar.WindowPadding, imgui.Vec2(0.0, 0.0))

        imgui.PushStyleColor(imgui.Col.ChildBg, imgui.Vec4(0.1882, 0.1882, 0.1882, 1.0))
        imgui.PushStyleColor(imgui.Col.Border, imgui.Vec4(0.26, 0.26, 0.26, 1.0))

        # Create a dedicated child region to act as the unified composer surface.
        # Width 0.0 means "use all available width".
        imgui.BeginChild(
            "ComposerCapsule",
            imgui.Vec2(0.0, capsule_height),
            imgui.ChildFlags.Borders,
            0,
        )

        # The available width inside the child determines how much room the
        # input gets after leaving space for the trailing send button.
        inner_width = imgui.GetContentRegionAvail().x

        # Reserve room for:
        # - left padding
        # - the send button
        # - right inset for the button
        # - spacing gap between input and button
        #
        # The max(120.0, ...) keeps the input from collapsing too small.
        input_width = max(
            120.0,
            inner_width - inner_pad_x - (button_size + button_right_inset + button_gap),
        )

        # Input height fills most of the capsule vertically, minus top/bottom padding.
        input_height = capsule_height - (inner_pad_y * 2.0)

        # Push the computed size down into the input widget before rendering.
        self._query_input_widget.set_size(input_width, input_height)

        # Style the text input so it visually blends into the capsule.
        # We keep the frame color very close to the capsule background so the
        # whole control feels like one unified surface instead of separate boxes.
        imgui.PushStyleVar(imgui.StyleVar.FrameRounding, 18.0)
        imgui.PushStyleVar(imgui.StyleVar.FramePadding, imgui.Vec2(10.0, 10.0))
        imgui.PushStyleVar(imgui.StyleVar.FrameBorderSize, 0.0)

        imgui.PushStyleColor(imgui.Col.FrameBg, imgui.Vec4(0.1882, 0.1882, 0.1882, 1.0))
        imgui.PushStyleColor(imgui.Col.FrameBgHovered, imgui.Vec4(0.1882, 0.1882, 0.1882, 1.0))
        imgui.PushStyleColor(imgui.Col.FrameBgActive, imgui.Vec4(0.1882, 0.1882, 0.1882, 1.0))

        # Manually place the input inside the capsule.
        # In ImGui, SetCursorPos controls where the NEXT submitted widget appears.
        imgui.SetCursorPos(imgui.Vec2(inner_pad_x, inner_pad_y))

        # When requested, restore focus to the input once the UI is idle again.
        # SetKeyboardFocusHere applies to the next submitted widget.
        if self._should_focus_input and not self._viewmodel.is_busy:
            imgui.SetKeyboardFocusHere()

        # Disable typing while the assistant is processing a request.
        imgui.BeginDisabled(self._viewmodel.is_busy)
        input_activated = self._query_input_widget.render()
        imgui.EndDisabled()

        input_is_focused = imgui.IsItemFocused()

        # Once focus has actually landed on the input, clear the request.
        if self._should_focus_input and input_is_focused:
            self._should_focus_input = False

        # Show the placeholder whenever the composer is empty and idle.
        # This keeps the empty-state hint consistent for both click-send and
        # Enter-send flows, even when the field is focused.
        if (not self._viewmodel.is_busy) and (not self._viewmodel.query_text.strip()):
            self._draw_input_placeholder(
                self._composer_placeholder_text,
                x_padding=12.0,
                y_padding=12.0,
            )

        # Clean up input field styling.
        imgui.PopStyleColor(3)
        imgui.PopStyleVar(3)

        should_submit_from_keyboard = (
            input_activated
            and self._viewmodel.can_send
            and not self._viewmodel.is_busy
        )

        if should_submit_from_keyboard:
            self._submit_message()

        # Compute send button position relative to the capsule.
        #
        # button_x:
        #   Anchor from the right edge inward.
        #
        # button_y:
        #   Anchor from the bottom edge upward.
        #
        # This is what makes the button feel like it lives in the lower-right
        # corner of the capsule instead of in a normal row layout.
        button_x = inner_width - button_right_inset - button_size
        button_y = capsule_height - button_bottom_inset - button_size

        # Move the ImGui layout cursor so the next widget (the send button)
        # is drawn at the desired anchored position inside the capsule.
        imgui.SetCursorPos(imgui.Vec2(button_x, button_y))

        # Keep the send button visually active whenever the UI is idle.
        # Only mute it while an assistant response is in progress.
        imgui.BeginDisabled(self._viewmodel.is_busy)
        self._send_button_widget.render()
        imgui.EndDisabled()

        # Close and clean up the outer capsule region.
        imgui.EndChild()
        imgui.PopStyleColor(2)
        imgui.PopStyleVar(3)

        # Short helper/status text shown underneath the composer.
        # Examples:
        # - "Thinking..."
        # - "Please enter a message."
        # - "Assistant request failed."
        status_text = self._viewmodel.status_text.strip()
        if not status_text:
            return

        # Small spacer between the capsule and the status line.
        imgui.Dummy(imgui.Vec2(0.0, 8.0))

        # Render errors in red; informational state in muted light text.
        if self._viewmodel.last_error is not None:
            imgui.PushStyleColor(imgui.Col.Text, imgui.Vec4(0.92, 0.52, 0.52, 1.0))
        else:
            imgui.PushStyleColor(imgui.Col.Text, imgui.Vec4(0.72, 0.76, 0.84, 1.0))

        imgui.TextWrapped(status_text)
        imgui.PopStyleColor(1)

    def _submit_message(self) -> None:
        """
        Submit the current message and request that the composer input regain
        focus when the UI becomes idle again.

        This keeps the chat flow smooth across both mouse-click sends and
        keyboard Enter sends.
        """
        self._viewmodel.submit_message()
        self._should_focus_input = True

    def _draw_input_placeholder(self, text: str, *, x_padding: float, y_padding: float,) -> None:
        """
        Draw lightweight placeholder text over the empty multiline input.

        Dear ImGui does not provide a native multiline "with hint" widget, so
        this is rendered manually as an overlay when the input is empty and not
        focused.
        """
        rect_min = imgui.GetItemRectMin()
        draw_list = imgui.GetWindowDrawList()

        draw_list.AddText(
            imgui.Vec2(rect_min.x + x_padding, rect_min.y + y_padding),
            imgui.GetColorU32(imgui.Vec4(0.52, 0.55, 0.60, 1.0)),
            text,
        )