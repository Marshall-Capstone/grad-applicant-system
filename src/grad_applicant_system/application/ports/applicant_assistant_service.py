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

    def send_message(self, user_message: str, available_files: list[str] | None = None) -> AssistantReply:
        """Send a user message and return the assistant's reply.

        available_files:
            Optional list of file paths that have been uploaded in the UI. If
            provided, the assistant may choose to call MCP tools (for example
            `ingest_pdfs`) referencing these paths.
        """
        ...

    def parse_applicant_pdf(self, file_path: str) -> dict:
        """Parse an applicant PDF and return extracted applicant data."""
        ...

    def parse_applicant_pdfs(self, file_paths: list[str]) -> dict:
        """Parse multiple applicant PDFs and return a mapping of file->extracted data."""
        ...