from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AssistantReply:
    """One assistant response returned to the presentation layer."""

    user_message: str
    assistant_message: str


class ApplicantAssistantService(Protocol):
    """Application-facing port for conversational applicant assistance.

    Implementations handle chat interactions and may use query tools to answer
    questions about applicant data already stored in the system.

    PDF ingestion is intentionally not part of this port. Applicant documents
    are ingested through the dedicated UI upload workflow and persisted before
    the assistant is asked to query them.
    """

    def send_message(self, user_message: str) -> AssistantReply:
        """Send a user message and return the assistant's reply."""
        ...