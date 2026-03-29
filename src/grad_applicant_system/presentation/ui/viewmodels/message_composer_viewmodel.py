from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Thread
from time import perf_counter

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)


@dataclass(frozen=True)
class TranscriptEntry:
    """
    One chat/transcript item displayed in the conversation history.

    role:
        Indicates who produced the message, e.g. "user" or "assistant".

    text:
        The actual text shown in the transcript pane.
    """
    role: str
    text: str


@dataclass(frozen=True)
class _WorkerSuccess:
    """
    Internal success payload returned from the background worker thread.

    The thread does not directly mutate UI state. Instead, it packages its
    result and places it into a queue for the ViewModel to consume later
    during the normal UI update cycle.
    """
    reply: AssistantReply


@dataclass(frozen=True)
class _WorkerFailure:
    """
    Internal failure payload returned from the background worker thread.

    This keeps exception-handling thread-safe and lets the ViewModel decide
    how that failure should be reflected in the UI.
    """
    error_text: str


# A queued worker result can be either a successful assistant reply
# or a failure payload describing what went wrong.
_WorkerResult = _WorkerSuccess | _WorkerFailure


class MessageComposerViewModel:
    """
    ViewModel for the conversation composer and transcript state.

    Responsibility:
    - Hold current UI-facing state for the message composer.
    - Accept user input edits.
    - Submit messages to the assistant service.
    - Manage busy/disabled state while a response is in progress.
    - Maintain transcript history for the conversation pane.
    - Expose short status text for the composer area.

    Architectural role:
    - This is presentation-layer state, not business/domain logic.
    - It depends on an application port (`ApplicantAssistantService`),
      not on infrastructure details directly.
    - It is consumed by one or more Panes (composer pane, transcript pane,
      top menu pane).

    Important design note:
    - The assistant request runs off the UI thread so the interface stays
      responsive.
    - The background thread places results in a queue.
    - update() is called once per frame by the App and applies any finished
      result back into ViewModel state.
    """

    def __init__(self, assistant_service: ApplicantAssistantService) -> None:
        """
        Initialize UI state for a new conversation session.

        assistant_service:
            The application-facing assistant abstraction used to send
            natural-language messages and receive replies.
        """
        # Application/service dependency used to perform assistant requests.
        self._assistant_service = assistant_service

        # Current draft text in the composer input box.
        self._query_text = ""

        # Short UI message shown near the composer.
        # Examples:
        # - "Thinking..."
        # - "Please enter a message."
        # - "Assistant request failed."
        self._status_text = ""

        # Most recent successful assistant reply object.
        # Useful if later you want richer metadata than just transcript text.
        self._last_reply: AssistantReply | None = None

        # Most recent error message, if one occurred.
        # This helps the view decide how to style status/error feedback.
        self._last_error: str | None = None

        # Indicates whether a background assistant request is currently running.
        # While busy, the input and send button should be disabled.
        self._is_busy = False

        # In-memory transcript for the current conversation session.
        self._transcript: list[TranscriptEntry] = []

        # Thread-safe queue used to hand results from worker thread -> UI thread.
        self._worker_results: Queue[_WorkerResult] = Queue()

        # Typewriter-reveal state for assistant responses.
        #
        # First slice design:
        # - the full assistant response still arrives all at once
        # - the ViewModel reveals it gradually over subsequent frames
        # - the UI remains responsive because reveal happens in update()
        self._reveal_chars_per_second = 90.0
        self._active_reveal_text: str | None = None
        self._active_reveal_entry_index: int | None = None
        self._revealed_char_count = 0
        self._reveal_char_budget = 0.0

        # Used to measure per-frame elapsed time for reveal pacing.
        self._last_update_time = perf_counter()

    @property
    def query_text(self) -> str:
        """Current draft text shown in the composer input."""
        return self._query_text

    @property
    def status_text(self) -> str:
        """Short status/help/error text shown near the composer."""
        return self._status_text

    @property
    def last_reply(self) -> AssistantReply | None:
        """
        Most recent successful assistant reply object.

        This is presentation-useful state if later you want to surface extra
        metadata beyond the plain assistant message text.
        """
        return self._last_reply

    @property
    def last_error(self) -> str | None:
        """Most recent error text, if the assistant request failed."""
        return self._last_error

    @property
    def is_busy(self) -> bool:
        """Whether an assistant request is currently in progress."""
        return self._is_busy

    @property
    def can_send(self) -> bool:
        """
        Whether the current draft can be submitted.

        A message can be sent only when:
        - the assistant is not already busy
        - the current draft is not blank/whitespace
        """
        return (not self._is_busy) and bool(self._query_text.strip())

    @property
    def can_clear(self) -> bool:
        """
        Whether the conversation can currently be cleared.

        Clearing is disabled during an in-flight assistant request so the UI
        state does not change underneath a running background operation.
        """
        return (not self._is_busy) and bool(self._transcript)

    @property
    def transcript(self) -> tuple[TranscriptEntry, ...]:
        """
        Read-only transcript snapshot for the UI.

        Returning a tuple prevents outside code from mutating the underlying
        list directly.
        """
        return tuple(self._transcript)

    def set_query_text(self, text: str) -> None:
        """
        Update the current composer draft text.

        Called by the text input widget as the user types.

        Behavior:
        - Ignores edits while busy.
        - Clears short status/error feedback when the user starts typing a
          non-empty message again.
        """
        if self._is_busy:
            return

        self._query_text = text

        # Once the user starts typing a fresh message, clear lightweight
        # composer feedback so the UI feels responsive and non-sticky.
        if text.strip():
            self._status_text = ""
            self._last_error = None

    def submit_message(self) -> None:
        """
        Submit the current draft to the assistant.

        High-level flow:
        1. Validate that the assistant is not already busy.
        2. Validate that the user entered a non-empty message.
        3. Update immediate UI state (busy flag, transcript, status text).
        4. Clear the input field.
        5. Start a background worker thread to call the assistant service.

        Important:
        - This method does not directly wait for the assistant reply.
        - The actual assistant call happens in `_run_assistant_request()`.
        - The result is applied later by `update()`.
        """
        if self._is_busy:
            self._status_text = "Please wait for the current response."
            return

        # Normalize the outgoing message by stripping surrounding whitespace.
        message = self._query_text.strip()

        if not message:
            self._status_text = "Please enter a message."
            return

        # Reset prior result/error state for the new request.
        self._last_error = None
        self._last_reply = None

        # Mark UI as busy and show lightweight activity feedback.
        self._is_busy = True
        self._status_text = "Thinking..."

        # Immediately append the user's message to the visible transcript.
        # This gives instant feedback before the assistant finishes responding.
        self._transcript.append(TranscriptEntry(role="user", text=message))

        # Clear the input box now that the message has been submitted.
        self._query_text = ""

        # Launch the assistant request off the UI thread so the window remains
        # responsive while waiting on the model / MCP / network activity.
        worker = Thread(
            target=self._run_assistant_request,
            args=(message,),
            daemon=True,
        )
        worker.start()

    def update(self) -> None:
        """
        Advance any active assistant typewriter reveal and apply a finished
        background worker result, if one is available.

        This should be called once per frame by the App.

        Why this exists:
        - The worker thread performs the blocking assistant request.
        - The worker thread does NOT directly mutate UI-facing state.
        - Instead, it places either success/failure into a queue.
        - This method consumes any finished result and also advances the
          assistant typewriter effect using frame-to-frame elapsed time.
        """
        now = perf_counter()
        delta_seconds = now - self._last_update_time
        self._last_update_time = now

        self._apply_finished_worker_result()
        self._advance_active_reveal(delta_seconds)

    def _apply_finished_worker_result(self) -> None:
        """
        Consume at most one finished worker result from the queue.

        Success behavior for the current slice:
        - store the full assistant reply immediately
        - append an empty assistant transcript entry
        - begin gradually revealing the reply text into that entry

        Failure behavior:
        - append the failure message immediately
        - release busy state so the user can continue
        """
        try:
            result = self._worker_results.get_nowait()
        except Empty:
            return

        if isinstance(result, _WorkerFailure):
            self._last_error = result.error_text
            self._status_text = "Assistant request failed."
            self._transcript.append(
                TranscriptEntry(role="assistant", text=result.error_text)
            )
            self._is_busy = False
            return

        self._last_reply = result.reply
        self._last_error = None

        assistant_text = result.reply.assistant_message

        # Start a gradual reveal instead of appending the full text at once.
        self._transcript.append(TranscriptEntry(role="assistant", text=""))
        self._active_reveal_text = assistant_text
        self._active_reveal_entry_index = len(self._transcript) - 1
        self._revealed_char_count = 0
        self._reveal_char_budget = 0.0

        # Keep the UI locked during the reveal for this first slice.
        # We can relax this later if desired.
        self._status_text = "Typing..."

        # Edge case: empty assistant message.
        if not assistant_text:
            self._finish_active_reveal()

    def _advance_active_reveal(self, delta_seconds: float) -> None:
        """
        Reveal more of the active assistant message based on elapsed time.

        delta_seconds:
            Seconds elapsed since the previous UI update frame.
        """
        if self._active_reveal_text is None:
            return

        if self._active_reveal_entry_index is None:
            return

        self._reveal_char_budget += (
            max(delta_seconds, 0.0) * self._reveal_chars_per_second
        )

        chars_to_add = int(self._reveal_char_budget)
        if chars_to_add <= 0:
            return

        self._reveal_char_budget -= chars_to_add
        self._revealed_char_count = min(
            self._revealed_char_count + chars_to_add,
            len(self._active_reveal_text),
        )

        visible_text = self._active_reveal_text[: self._revealed_char_count]
        self._transcript[self._active_reveal_entry_index] = TranscriptEntry(
            role="assistant",
            text=visible_text,
        )

        if self._revealed_char_count >= len(self._active_reveal_text):
            self._finish_active_reveal()

    def _finish_active_reveal(self) -> None:
        """
        Finalize the current assistant typewriter reveal and release busy state.
        """
        if (
            self._active_reveal_text is not None
            and self._active_reveal_entry_index is not None
        ):
            self._transcript[self._active_reveal_entry_index] = TranscriptEntry(
                role="assistant",
                text=self._active_reveal_text,
            )

        self._active_reveal_text = None
        self._active_reveal_entry_index = None
        self._revealed_char_count = 0
        self._reveal_char_budget = 0.0

        self._status_text = ""
        self._is_busy = False        

    def _run_assistant_request(self, message: str) -> None:
        """
        Worker-thread entry point for the assistant request.

        This runs outside the UI thread.

        Responsibility:
        - Call the assistant service.
        - Convert success/failure into queue payloads.
        - Never directly touch ImGui widgets or UI render code.
        """
        try:
            reply = self._assistant_service.send_message(message)
        except Exception as exc:
            error_text = f"Assistant request failed: {exc}"
            self._worker_results.put(_WorkerFailure(error_text=error_text))
            return

        self._worker_results.put(_WorkerSuccess(reply=reply))

    def clear_conversation(self) -> None:
        """
        Clear the current conversation session.

        Behavior:
        - Disabled while an assistant request is in progress.
        - Clears the draft text, short status, last result/error, and transcript.
        """
        if self._is_busy:
            self._status_text = "Please wait for the current response."
            return

        self._query_text = ""
        self._status_text = ""
        self._last_reply = None
        self._last_error = None
        self._transcript.clear()
        self._active_reveal_text = None
        self._active_reveal_entry_index = None
        self._revealed_char_count = 0
        self._reveal_char_budget = 0.0

    def ingest_pdf(self, file_path: str) -> None:
        """
        Ingest a PDF file, extract text and structured fields, and append
        a summary to the transcript.

        This method is defensive and performs work synchronously on the UI
        thread. It catches and surfaces any errors as a transcript entry
        rather than raising.
        """
        if self._is_busy:
            self._status_text = "Please wait for the current response."
            return

        if not file_path:
            self._status_text = "No file selected."
            return

        # Show lightweight feedback
        self._status_text = "Processing PDF..."

        try:
            # Local imports to avoid hard dependency at module import time
            from grad_applicant_system.infrastructure.parsing.pdf_document_parser import (
                PDFDocumentParser,
            )
            from grad_applicant_system.infrastructure.parsing.simple_extraction_processor import (
                SimpleExtractionProcessor,
            )

            parser = PDFDocumentParser()
            extractor = SimpleExtractionProcessor()

            text = parser.extract_text(file_path) or ""
            data = extractor.extract(text)

            # Append a transcript summary with the parsed fields
            summary_lines = [f"Uploaded: {file_path}"]
            if data.get("name"):
                summary_lines.append(f"Name: {data['name']}")
            if data.get("email"):
                summary_lines.append(f"Email: {data['email']}")
            if data.get("gpa"):
                summary_lines.append(f"GPA: {data['gpa']}")
            if not (data.get("name") or data.get("email") or data.get("gpa")):
                # Fallback: include a text excerpt if structured fields missing
                excerpt = (text or "").strip().replace("\n", " ")[:400]
                if excerpt:
                    summary_lines.append(f"Excerpt: {excerpt}")
                else:
                    summary_lines.append("No extractable content found.")

            self._transcript.append(
                TranscriptEntry(role="system", text="\n".join(summary_lines))
            )
            self._status_text = ""

        except Exception as exc:
            err = f"PDF ingestion failed: {exc}"
            self._transcript.append(TranscriptEntry(role="system", text=err))
            self._status_text = "PDF ingestion failed."