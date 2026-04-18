from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic

from grad_applicant_system.application.ports import (
    ApplicantAssistantService,
    AssistantReply,
)
from grad_applicant_system.infrastructure.mcp import McpToolClient


class AnthropicApplicantAssistantService(ApplicantAssistantService):
    """
    Real assistant implementation backed by Anthropic + MCP tools.

    Current limitation:
    - This service is stateless across calls because the current
      application port only accepts a single user message and returns
      a single reply.
    - The UI transcript is therefore visual only for now; it is not yet
      replayed to the model as prior conversation history.

    Important design note:
    - PDF upload/ingestion is no longer orchestrated through the assistant.
    - The UI upload path is now the authoritative ingest step.
    - This assistant is therefore focused on applicant-domain querying and
      MCP-backed lookup operations, not file-ingest prompting.
    """

    def __init__(
        self,
        mcp_tool_client: McpToolClient,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        system_prompt: str | None = None,
    ) -> None:
        """
        Initialize the Anthropic-backed assistant service.

        Resolution order:
        - explicit constructor arguments first
        - environment variables second

        Raises:
            RuntimeError: if no Anthropic API key can be resolved.
        """
        # Resolve credentials/config from explicit arguments first, then env.
        resolved_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY.")

        # Anthropic client used for all model requests.
        self._client = anthropic.Anthropic(api_key=resolved_api_key)

        # Thin MCP client used to discover tools and invoke them when Claude
        # responds with tool_use blocks.
        self._mcp_tool_client = mcp_tool_client

        # Default model can be overridden by constructor or environment.
        self._model = model or os.getenv(
            "ANTHROPIC_MODEL",
            "claude-sonnet-4-5-20250929",
        )

        # Token cap for a single assistant response.
        self._max_tokens = max_tokens

        # Default system behavior for the assistant. This keeps the assistant
        # scoped to the applicant domain and nudges it toward MCP query tools
        # instead of inventing answers.
        self._system_prompt = system_prompt or (
            "You are an applicant-assistant for a graduate applicant system. "
            "Use the available MCP tools whenever they help answer questions about applicants. "
            "Do not answer general knowledge questions or provide information unrelated to applicants. "
            "If a user asks anything outside the applicant domain, respond with an error message stating the request is unsupported. "
            "Do not invent applicant data. "
            "If the current tools are insufficient, explain that limitation clearly. "

            "When a user asks for all applicants or another large broad listing, do not try to print every row in full. "
            "Instead, use the appropriate MCP tool, report the exact total count returned by the tool, "
            "and then provide a concise sample of up to 10 applicants. "
            "State the basis of the sample ordering if it is known from the tool output. "
            "If the user wants a specific applicant or subset, encourage narrower filtering. "
            "If the tool returns only a limited page of results, say so explicitly."
        )

    def send_message(self, user_message: str) -> AssistantReply:
        """
        Send a single user message to Anthropic, allow Claude to call local
        MCP tools if needed, and return the final assistant text.

        Flow:
        1. Validate / normalize user input.
        2. Reject obvious out-of-domain prompts early.
        3. Ask Claude for a response using the base system prompt.
        4. If Claude requests tools, execute them and feed results back.
        5. Return the final assistant text to the UI.

        Note:
        - Uploaded-file context is intentionally not passed here anymore.
        - PDF upload/ingestion is handled by the UI/upload workflow directly.
        """
        # Trim whitespace so empty/blank submissions can be handled cleanly.
        text = user_message.strip()
        if not text:
            return AssistantReply(
                user_message="",
                assistant_message="Please enter a message.",
            )

        # Fast-path reject for prompts that appear to be general knowledge
        # rather than graduate-applicant related.
        if self._is_general_knowledge_query(text):
            return AssistantReply(
                user_message=text,
                assistant_message=(
                    "ERROR: unsupported request. "
                    "This assistant only handles graduate applicant data."
                ),
            )

        # Convert MCP tool metadata into Anthropic's expected tool schema.
        claude_tools = self._mcp_tool_client.to_claude_tools(
            self._mcp_tool_client.list_tools()
        )

        # `messages` contains the request-local message exchange sent to Claude.
        # This service is stateless, so we start fresh on every call.
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": text}
        ]

        # Initial model call using the base system prompt.
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._system_prompt,
            tools=claude_tools,
            messages=messages,
        )

        # Continue until Claude returns a normal final response rather than
        # asking for another tool or pausing the turn.
        while True:
            if response.stop_reason == "tool_use":
                # Preserve Claude's tool-use response in the request-local
                # history before sending tool results back.
                messages.append(
                    {
                        "role": response.role,
                        "content": response.content,
                    }
                )

                tool_results: list[dict[str, Any]] = []

                # Anthropic responses can contain multiple content blocks.
                # Only tool_use blocks should trigger MCP tool execution.
                for block in response.content:
                    if getattr(block, "type", None) != "tool_use":
                        continue

                    # Call the named MCP tool with the model-provided arguments.
                    result = self._mcp_tool_client.call_tool(
                        tool_name=block.name,
                        arguments=dict(block.input or {}),
                    )

                    # Convert the tool result into Anthropic's expected
                    # `tool_result` block structure.
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": self._format_tool_result_content(result),
                        }
                    )

                # Safety exit: if Claude asked for tool_use but no actual
                # tool_result blocks were assembled, stop looping.
                if not tool_results:
                    break

                # Anthropic expects tool results to be returned in a user-role
                # message containing `tool_result` content blocks.
                messages.append(
                    {
                        "role": "user",
                        "content": tool_results,
                    }
                )

                # Re-call the model with the updated request-local history.
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=self._system_prompt,
                    tools=claude_tools,
                    messages=messages,
                )
                continue

            if response.stop_reason == "pause_turn":
                # Preserve the paused response content and immediately resume.
                messages.append(
                    {
                        "role": response.role,
                        "content": response.content,
                    }
                )

                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=self._system_prompt,
                    tools=claude_tools,
                    messages=messages,
                )
                continue

            # Any other stop reason means we're done with the tool loop.
            break

        # Pull only human-readable text blocks out of the final response.
        assistant_text = self._extract_text_from_response(response)

        # Provide a fallback message so the UI does not end up blank if the
        # model returned only tool content or an unexpected empty response.
        if not assistant_text:
            assistant_text = (
                "I completed the request, but no assistant text was returned."
            )

        return AssistantReply(
            user_message=text,
            assistant_message=assistant_text,
        )

    def _extract_text_from_response(self, response: Any) -> str:
        """
        Extract only text blocks from an Anthropic response object and return
        them as a single newline-joined string.
        """
        parts: list[str] = []

        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "text":
                block_text = getattr(block, "text", "")
                if block_text:
                    parts.append(block_text)

        return "\n".join(parts).strip()

    def _format_tool_result_content(self, result: Any) -> list[dict[str, str]]:
        """
        Convert an MCP CallToolResult into Anthropic tool_result content blocks.

        For now, everything is normalized to text blocks. Native text blocks
        are passed through directly; other objects are safely JSON-dumped so
        the model can still inspect the result in a readable form.
        """
        raw_content = getattr(result, "content", None)
        if raw_content:
            blocks: list[dict[str, str]] = []

            for item in raw_content:
                item_type = getattr(item, "type", None)

                # Preserve plain text tool output when available.
                if item_type == "text":
                    text_value = getattr(item, "text", "")
                    blocks.append(
                        {
                            "type": "text",
                            "text": text_value,
                        }
                    )
                    continue

                # For non-text MCP result items, serialize a safe representation
                # into a text block so Claude can still consume it.
                blocks.append(
                    {
                        "type": "text",
                        "text": json.dumps(
                            self._safe_dump(item),
                            indent=2,
                            default=str,
                        ),
                    }
                )

            if blocks:
                return blocks

        # Fallback: serialize the whole result if no structured content blocks
        # were present.
        return [
            {
                "type": "text",
                "text": json.dumps(
                    self._safe_dump(result),
                    indent=2,
                    default=str,
                ),
            }
        ]

    def _safe_dump(self, value: Any) -> Any:
        """
        Return a JSON-friendly representation of an object.

        Preference order:
        1. Pydantic-like `.model_dump()`
        2. Plain object `__dict__`
        3. String fallback
        """
        if hasattr(value, "model_dump"):
            return value.model_dump()

        if hasattr(value, "__dict__"):
            return value.__dict__

        return str(value)

    def _is_general_knowledge_query(self, text: str) -> bool:
        """
        Heuristic filter for obviously out-of-domain prompts.

        This is not a perfect classifier. It simply tries to reject common
        general-knowledge questions before they reach the model when they
        contain no applicant-domain keywords.
        """
        normalized = text.strip().lower()
        if not normalized:
            return False

        # If the message contains applicant-domain terms, treat it as in-scope.
        domain_keywords = re.compile(
            r"\b(applicant|application|program|advisor|gpa|term|admission|"
            r"transcript|student|email|name|user id|degree|major|school)\b",
            re.IGNORECASE,
        )
        if domain_keywords.search(text):
            return False

        # Otherwise, reject common general-question openings / phrases.
        general_question = bool(
            re.match(r"^(what|who|where|when|why|how|define|explain)\b", normalized)
            or "capital of" in normalized
            or "what is" in normalized
            or "who is" in normalized
            or "where is" in normalized
        )

        return general_question