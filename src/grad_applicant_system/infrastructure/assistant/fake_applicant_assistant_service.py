from __future__ import annotations

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)


class FakeApplicantAssistantService(ApplicantAssistantService):
    """Development fallback used when the real assistant is unavailable."""

    def send_message(self, user_message: str) -> AssistantReply:
        """Return a deterministic placeholder reply for local UI testing."""
        text = user_message.strip()

        if not text:
            return AssistantReply(
                user_message="",
                assistant_message="Please enter a message.",
            )

        lowered = text.lower()

        if "list" in lowered and "applicant" in lowered:
            reply = (
                "Fake assistant response: the real assistant is unavailable, "
                "so this is a placeholder for applicant-list queries."
            )
        elif "email" in lowered:
            reply = (
                "Fake assistant response: the real assistant is unavailable, "
                "so this is a placeholder for applicant email lookups."
            )
        else:
            reply = (
                "Fake assistant response: the application is running in "
                "development fallback mode."
            )

        return AssistantReply(
            user_message=text,
            assistant_message=reply,
        )