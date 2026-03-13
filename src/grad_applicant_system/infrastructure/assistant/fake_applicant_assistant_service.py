from __future__ import annotations

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)


class FakeApplicantAssistantService(ApplicantAssistantService):
    """Temporary development implementation for the conversational assistant."""

    def send_message(self, user_message: str) -> AssistantReply:
        text = user_message.strip()

        if not text:
            return AssistantReply(
                user_message="",
                assistant_message="Please enter a message.",
            )

        lowered = text.lower()

        if "list" in lowered and "applicant" in lowered:
            reply = (
                "Fake assistant response: later this will ask the LLM to use "
                "the MCP tools to list applicants."
            )
        elif "email" in lowered:
            reply = (
                "Fake assistant response: later this will ask the LLM to use "
                "the MCP tools to look up an applicant by email."
            )
        else:
            reply = (
                "Fake assistant response: the UI-to-assistant boundary is now "
                "conversation-oriented. Real Anthropic + MCP integration will "
                "be added next."
            )

        return AssistantReply(
            user_message=text,
            assistant_message=reply,
        )