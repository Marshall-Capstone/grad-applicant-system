from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AssistantReply:
    """One assistant response returned to the presentation layer."""

    user_message: str
    assistant_message: str


class ApplicantAssistantService(Protocol):
    """Application-facing port for conversational applicant assistance."""

    def send_message(self, user_message: str) -> AssistantReply:
        """Send a user message and return the assistant's reply."""
        ...

    def parse_applicant_pdf(self, file_path: str) -> dict:
        """Parse an applicant PDF and return extracted applicant data."""
        ...