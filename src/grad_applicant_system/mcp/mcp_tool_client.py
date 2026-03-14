from __future__ import annotations

import asyncio
from typing import Any

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


class McpToolClientError(RuntimeError):
    """Raised when the local MCP server cannot be reached or used."""


class McpToolClient:
    """
    Small synchronous façade over the async MCP Streamable HTTP client.

    This keeps the current UI/ViewModel code simple for now.
    """

    def __init__(self, server_url: str) -> None:
        self._server_url = server_url

    def list_tools(self) -> list[types.Tool]:
        return asyncio.run(self._list_tools())

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> types.CallToolResult:
        return asyncio.run(self._call_tool(tool_name, arguments or {}))

    @staticmethod
    def to_claude_tools(tools: list[types.Tool]) -> list[dict[str, Any]]:
        """
        Convert MCP tool definitions into Claude tool definitions.

        Anthropic expects `input_schema`, while MCP exposes `inputSchema`.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in tools
        ]

    async def _list_tools(self) -> list[types.Tool]:
        try:
            async with streamable_http_client(self._server_url) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    response = await session.list_tools()
                    return list(response.tools)
        except Exception as exc:
            raise McpToolClientError(
                f"Failed to list MCP tools from {self._server_url}: {exc}"
            ) from exc

    async def _call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> types.CallToolResult:
        try:
            async with streamable_http_client(self._server_url) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await session.call_tool(tool_name, arguments=arguments)
        except Exception as exc:
            raise McpToolClientError(
                f"Failed to call MCP tool '{tool_name}' at {self._server_url}: {exc}"
            ) from exc