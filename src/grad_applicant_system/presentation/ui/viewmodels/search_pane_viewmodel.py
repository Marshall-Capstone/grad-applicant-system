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
    def transcript(self) -> tuple[TranscriptEntry, ...]:
        return tuple(self._transcript)

    def set_query_text(self, text: str) -> None:
        self._query_text = text

    def submit_message(self) -> None:
        message = self._query_text.strip()

        if not message:
            self._status_text = "Please enter a message."
            return

        self._transcript.append(TranscriptEntry(role="user", text=message))

        try:
            reply = self._assistant_service.send_message(message)
        except Exception as exc:
            error_text = f"Assistant request failed: {exc}"
            self._status_text = error_text
            self._transcript.append(TranscriptEntry(role="assistant", text=error_text))
            self._last_reply = None
            return

        self._last_reply = reply
        self._status_text = reply.assistant_message
        self._transcript.append(
            TranscriptEntry(role="assistant", text=reply.assistant_message)
        )
        self._query_text = ""