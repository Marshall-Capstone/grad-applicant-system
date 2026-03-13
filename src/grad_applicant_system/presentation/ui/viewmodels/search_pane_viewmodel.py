from __future__ import annotations

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)


class SearchPaneViewModel:
    """UI state and actions for the current input/send pane."""

    def __init__(self, assistant_service: ApplicantAssistantService) -> None:
        self._assistant_service = assistant_service
        self._query_text = ""
        self._status_text = "Enter a message and click Send."
        self._last_reply: AssistantReply | None = None

    @property
    def query_text(self) -> str:
        return self._query_text

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def last_reply(self) -> AssistantReply | None:
        return self._last_reply

    def set_query_text(self, text: str) -> None:
        self._query_text = text

    def submit_message(self) -> None:
        message = self._query_text.strip()

        if not message:
            self._status_text = "Please enter a message."
            self._last_reply = None
            return

        try:
            reply = self._assistant_service.send_message(message)
        except Exception as exc:
            self._status_text = f"Assistant request failed: {exc}"
            self._last_reply = None
            return

        self._last_reply = reply
        self._status_text = reply.assistant_message