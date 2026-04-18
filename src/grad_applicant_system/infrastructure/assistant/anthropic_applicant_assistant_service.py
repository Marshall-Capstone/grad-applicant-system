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
    - This is stateless across calls because the current application port
      only accepts a single user message and returns a single reply.
    - The UI transcript is therefore visual only for now; it is not yet fed
      back into the model as conversation history.
    """

    def __init__(
        self,
        mcp_tool_client: McpToolClient,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        system_prompt: str | None = None,
    ) -> None:
        # Resolve credentials/config from explicit arguments first, then env.
        resolved_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY.")
        # Anthropic client used for all model requests.
        self._client = anthropic.Anthropic(api_key=resolved_api_key)
        # Thin MCP client used to discover tools and invoke them when Claude
        # responds with tool_use blocks.
        self._mcp_tool_client = mcp_tool_client
        # Default model can be overridden by constructor or environment
        self._model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        # Token cap for a single assistant response.
        self._max_tokens = max_tokens
        # Default system behavior for the assistant. This keeps the assistant
        # scoped to the applicant domain and nudges it toward MCP tool usage
        # instead of inventing answers.
        self._system_prompt = system_prompt or (
            "You are an applicant-assistant for a graduate applicant system. "
            "Use the available MCP tools whenever they help answer questions about applicants. "
            "Do not answer general knowledge questions or provide information unrelated to applicants. "
            "If a user asks anything outside the applicant domain, respond with an error message stating the request is unsupported. "
            "Do not invent applicant data. "
            "If the current tools are insufficient, explain that limitation clearly."
        )


    def _message_is_file_related(self, text: str) -> bool:
        """
        Lightweight heuristic used to decide whether uploaded-file context
        should be added to the request-level system prompt.
        This is intentionally simple for now: if the user's wording suggests
        they are talking about files/PDF ingestion, we expose the available
        uploaded file paths to the model for that request.
        """
        normalized = text.lower()
        return any(word in normalized for word in ["file", "files", "pdf", "upload", "uploaded", "ingest", "parse", "process"])
    

    def send_message(self, user_message: str, available_files: list[str] | None = None) -> AssistantReply:
        """
        Send a single user message to Anthropic, allow Claude to call local
        MCP tools if needed, and return the final assistant text.

        Flow:
        1. Validate / normalize user input.
        2. Reject obvious out-of-domain prompts early.
        3. Build a request-local system prompt.
        4. Ask Claude for a response.
        5. If Claude requests tools, execute them and feed results back.
        6. Return the final assistant text to the UI.
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
        messages: list[dict[str, Any]] = []

        # Start with the base system prompt, then optionally augment it for
        # this request only.
        request_system = self._system_prompt

        # If uploaded files are available *and* the user is talking about files,
        # add a short instruction to the request-level system prompt telling
        # Claude those files exist and how to invoke the batch-ingest tool.
        #
        # Important: we keep this in `request_system` rather than appending a
        # "role": "system" message into `messages`. That earlier approach
        # caused failures in the Anthropic flow after file upload.
        if available_files and self._message_is_file_related(text):
            try:
                files_list = json.dumps(list(available_files))
            except Exception:
                # Fall back to a string representation if JSON serialization
                # fails for any reason.
                files_list = str(list(available_files))

            request_system += (
            "\n\nAvailable uploaded files: "
            + files_list
            + ". If the user asks to process uploaded files, call `ingest_pdfs` "
            "with {'file_paths': [...]}.")

        # Add the user's prompt as the first request message.
        messages.append({"role": "user", "content": text})

        # Initial model call. We pass the request-local system prompt so any
        # file-related context stays attached across the full lifecycle of
        # this single request.
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=request_system,
            tools=claude_tools,
            messages=messages,
        )

        # Continue until Claude returns a normal final response rather than
        # asking for another tool or pausing the turn.
        while True:
            if response.stop_reason == "tool_use":
                # Preserve Claude's tool-use response in the message history
                # for this request before sending tool results back.
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

                # Re-call the model with the updated local request history.
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=request_system,
                    tools=claude_tools,
                    messages=messages,
                )
                continue

            if response.stop_reason == "pause_turn":
                # Preserve the paused response content and immediately resume.
                # This keeps the request-local context intact when the model
                # needs another pass before returning final text.
                messages.append(
                    {
                        "role": response.role,
                        "content": response.content,
                    }
                )

                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    system=request_system,
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
            assistant_text = ("I completed the request, but no assistant text was returned.")

        return AssistantReply(
            user_message=text,
            assistant_message=assistant_text,)

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
            r"\b(applicant|application|program|advisor|gpa|term|admission|transcript|student|file|pdf|email|name|user id|degree|major|school)\b",
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