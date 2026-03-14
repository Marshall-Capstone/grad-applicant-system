from __future__ import annotations

from dataclasses import dataclass

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)


@dataclass(frozen=True)
class TranscriptEntry:
    role: str
    text: str


class SearchPaneViewModel:
    """UI state and actions for the current input/send pane."""

    def __init__(self, assistant_service: ApplicantAssistantService) -> None:
        self._assistant_service = assistant_service
        self._query_text = ""
        self._status_text = "Enter a message and click Send."
        self._last_reply: AssistantReply | None = None
        self._last_error: str | None = None
        self._is_busy = False
        self._transcript: list[TranscriptEntry] = []

    @property
    def query_text(self) -> str:
        return self._query_text

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def last_reply(self) -> AssistantReply | None:
        return self._last_reply

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def is_busy(self) -> bool:
        return self._is_busy

    @property
    def can_send(self) -> bool:
        return (not self._is_busy) and bool(self._query_text.strip())

    @property
    def transcript(self) -> tuple[TranscriptEntry, ...]:
        return tuple(self._transcript)

    def set_query_text(self, text: str) -> None:
        if self._is_busy:
            return
        self._query_text = text

    def submit_message(self) -> None:
        if self._is_busy:
            self._status_text = "Please wait for the current response."
            return

        message = self._query_text.strip()

        if not message:
            self._status_text = "Please enter a message."
            return

        self._last_error = None
        self._last_reply = None
        self._is_busy = True
        self._status_text = "Thinking..."
        self._transcript.append(TranscriptEntry(role="user", text=message))

        try:
            reply = self._assistant_service.send_message(message)
        except Exception as exc:
            error_text = f"Assistant request failed: {exc}"
            self._last_error = error_text
            self._status_text = error_text
            self._transcript.append(TranscriptEntry(role="assistant", text=error_text))
            self._is_busy = False
            return

        self._last_reply = reply
        self._status_text = "Ready."
        self._transcript.append(
            TranscriptEntry(role="assistant", text=reply.assistant_message)
        )
        self._query_text = ""
        self._is_busy = False