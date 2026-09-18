import asyncio
import json

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


def extract_error_text(result) -> str:
    """
    Extract text from an MCP tool error result.
    """

    for content in result.content:

        if isinstance(
            content,
            TextContent,
        ):
            return content.text

    return ""


def assert_tool_error(
    result,
    expected_text: str,
):
    """
    Verify that the MCP client received
    a proper tool error.
    """

    assert result.is_error is True

    error_text = extract_error_text(
        result
    )

    print(
        "MCP ERROR:",
        error_text,
    )

    assert expected_text.lower() in (
        error_text.lower()
    )


async def test_invalid_document_name():
    print()
    print(
        "========================================"
    )
    print(
        "TEST 1 — INVALID DOCUMENT INPUT"
    )
    print(
        "========================================"
    )

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(
        server_params
    ) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "read_document",
                {
                    "doc_id":
                        "../secret.txt"
                },
            )

            assert_tool_error(
                result,
                "provided input is invalid",
            )

            print(
                "INVALID INPUT MCP TEST: PASS"
            )


async def test_missing_document():
    print()
    print(
        "========================================"
    )
    print(
        "TEST 2 — MISSING DOCUMENT"
    )
    print(
        "========================================"
    )

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(
        server_params
    ) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "read_document",
                {
                    "doc_id":
                        "definitely_missing_8_9.txt"
                },
            )

            assert_tool_error(
                result,
                "document was not found",
            )

            print(
                "MISSING DOCUMENT MCP TEST: PASS"
            )


async def test_unauthorized_delete():
    print()
    print(
        "========================================"
    )
    print(
        "TEST 3 — UNAUTHORIZED DELETE"
    )
    print(
        "========================================"
    )

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(
        server_params
    ) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "delete_document",
                {
                    "name":
                        "report.txt"
                },
            )

            assert_tool_error(
                result,
                "not authorized",
            )

            print(
                "UNAUTHORIZED DELETE MCP TEST: PASS"
            )


async def test_invalid_batch_request():
    print()
    print(
        "========================================"
    )
    print(
        "TEST 4 — INVALID BATCH REQUEST"
    )
    print(
        "========================================"
    )

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(
        server_params
    ) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "process_documents",
                {
                    "document_ids": []
                },
            )

            assert_tool_error(
                result,
                "provided input is invalid",
            )

            print(
                "INVALID BATCH MCP TEST: PASS"
            )


async def test_unknown_tool():
    print()
    print(
        "========================================"
    )
    print(
        "TEST 5 — UNKNOWN TOOL"
    )
    print(
        "========================================"
    )

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with stdio_client(
        server_params
    ) as (
        read_stream,
        write_stream,
    ):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                "tool_that_does_not_exist",
                {},
            )

            assert result.is_error is True

            error_text = extract_error_text(
                result
            )

            print(
                "MCP ERROR:",
                error_text,
            )

            assert (
                "unknown tool"
                in error_text.lower()
            )

            print(
                "UNKNOWN TOOL MCP TEST: PASS"
            )


async def main():
    print()
    print(
        "========================================"
    )
    print(
        "LEVEL 8.9 — MCP ERROR INTEGRATION"
    )
    print(
        "========================================"
    )

    await test_invalid_document_name()

    await test_missing_document()

    await test_unauthorized_delete()

    await test_invalid_batch_request()

    await test_unknown_tool()

    print()
    print(
        "========================================"
    )
    print(
        "LEVEL 8.9 MCP INTEGRATION: PASS"
    )
    print(
        "========================================"
    )


if __name__ == "__main__":
    asyncio.run(main())