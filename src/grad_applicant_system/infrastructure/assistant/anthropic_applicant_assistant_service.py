from __future__ import annotations

import json
import os
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
        resolved_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not resolved_api_key:
            raise RuntimeError("Missing ANTHROPIC_API_KEY.")

        self._client = anthropic.Anthropic(api_key=resolved_api_key)
        self._mcp_tool_client = mcp_tool_client
        self._model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
        self._max_tokens = max_tokens
        self._system_prompt = system_prompt or (
            "You are an applicant-assistant for a graduate applicant system. "
            "Use the available MCP tools whenever they help answer questions about applicants. "
            "Do not invent applicant data. "
            "If the current tools are insufficient, explain that limitation clearly."
        )

    def send_message(self, user_message: str, available_files: list[str] | None = None) -> AssistantReply:
        text = user_message.strip()
        if not text:
            return AssistantReply(
                user_message="",
                assistant_message="Please enter a message.",
            )

        claude_tools = self._mcp_tool_client.to_claude_tools(
            self._mcp_tool_client.list_tools()
        )

        messages: list[dict[str, Any]] = []

        # If the UI has uploaded files, provide them as an explicit system
        # message so the model can reference them and call the `ingest_pdfs`
        # MCP tool when appropriate.
        if available_files:
            try:
                files_list = json.dumps(list(available_files))
            except Exception:
                files_list = str(list(available_files))

            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Available uploaded files: "
                        + files_list
                        + ". If you want to process these files, call the MCP tool `ingest_pdfs` with argument `{'file_paths': [<paths>]}`."
                    ),
                }
            )

        messages.append({"role": "user", "content": text})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=self._system_prompt,
            tools=claude_tools,
            messages=messages,
        )

        while True:
            if response.stop_reason == "tool_use":
                messages.append(
                    {
                        "role": response.role,
                        "content": response.content,
                    }
                )

                tool_results: list[dict[str, Any]] = []
                for block in response.content:
                    if getattr(block, "type", None) != "tool_use":
                        continue

                    result = self._mcp_tool_client.call_tool(
                        tool_name=block.name,
                        arguments=dict(block.input or {}),
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": self._format_tool_result_content(result),
                        }
                    )

                if not tool_results:
                    break

                messages.append(
                    {
                        "role": "user",
                        "content": tool_results,
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

            if response.stop_reason == "pause_turn":
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

            break

        assistant_text = self._extract_text_from_response(response)

        if not assistant_text:
            assistant_text = (
                "I completed the request, but no assistant text was returned."
            )

        return AssistantReply(
            user_message=text,
            assistant_message=assistant_text,
        )

    def _extract_text_from_response(self, response: Any) -> str:
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

        We normalize everything to text blocks for now. That keeps the first
        integration step simple and robust.
        """
        raw_content = getattr(result, "content", None)
        if raw_content:
            blocks: list[dict[str, str]] = []

            for item in raw_content:
                item_type = getattr(item, "type", None)

                if item_type == "text":
                    text_value = getattr(item, "text", "")
                    blocks.append(
                        {
                            "type": "text",
                            "text": text_value,
                        }
                    )
                    continue

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
        if hasattr(value, "model_dump"):
            return value.model_dump()

        if hasattr(value, "__dict__"):
            return value.__dict__

        return str(value)