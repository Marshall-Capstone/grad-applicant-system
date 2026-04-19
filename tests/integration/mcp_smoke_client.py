import asyncio

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    """Smoke test the MCP query tools over streamable HTTP."""
    url = "http://127.0.0.1:8000/mcp"
    print(f"Connecting to {url}")

    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            result = await session.call_tool("list_applicants", arguments={"limit": 5})
            print("structuredContent:", result.structuredContent)

            for content_item in result.content:
                if isinstance(content_item, types.TextContent):
                    print("textContent:", content_item.text)


if __name__ == "__main__":
    asyncio.run(main())