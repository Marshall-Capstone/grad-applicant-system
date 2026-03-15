from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from threading import Thread

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)


@dataclass(frozen=True)
class TranscriptEntry:
    role: str
    text: str


@dataclass(frozen=True)
class _WorkerSuccess:
    reply: AssistantReply


@dataclass(frozen=True)
class _WorkerFailure:
    error_text: str


_WorkerResult = _WorkerSuccess | _WorkerFailure


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
        self._worker_results: Queue[_WorkerResult] = Queue()

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
    def can_clear(self) -> bool:
        return (not self._is_busy) and bool(self._transcript)

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
        self._query_text = ""

        worker = Thread(
            target=self._run_assistant_request,
            args=(message,),
            daemon=True,
        )
        worker.start()

    def update(self) -> None:
        """Poll for any finished background assistant result."""
        try:
            result = self._worker_results.get_nowait()
        except Empty:
            return

        if isinstance(result, _WorkerFailure):
            self._last_error = result.error_text
            self._status_text = result.error_text
            self._transcript.append(
                TranscriptEntry(role="assistant", text=result.error_text)
            )
            self._is_busy = False
            return

        self._last_reply = result.reply
        self._status_text = "Ready."
        self._transcript.append(
            TranscriptEntry(role="assistant", text=result.reply.assistant_message)
        )
        self._is_busy = False

    def _run_assistant_request(self, message: str) -> None:
        try:
            reply = self._assistant_service.send_message(message)
        except Exception as exc:
            error_text = f"Assistant request failed: {exc}"
            self._worker_results.put(_WorkerFailure(error_text=error_text))
            return

        self._worker_results.put(_WorkerSuccess(reply=reply))

    def clear_conversation(self) -> None:
        if self._is_busy:
            self._status_text = "Please wait for the current response."
            return

        self._query_text = ""
        self._status_text = "Enter a message and click Send."
        self._last_reply = None
        self._last_error = None
        self._transcript.clear()