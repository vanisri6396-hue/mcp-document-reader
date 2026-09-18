import asyncio
from dataclasses import dataclass
from typing import Any

from advanced_client import (
    AdvancedMCPClient,
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError,
)


# ============================================================
# FAKE MCP CONTENT
# ============================================================


@dataclass
class FakeContent:
    text: str


# ============================================================
# FAKE MCP RESULT
# ============================================================


@dataclass
class FakeResult:
    is_error: bool = False
    content: list[Any] | None = None
    structured_content: dict[str, Any] | None = None

    def __post_init__(self):

        if self.content is None:
            self.content = []


# ============================================================
# FAKE TOOL
# ============================================================


@dataclass
class FakeTool:
    name: str
    description: str
    input_schema: dict[str, Any]


# ============================================================
# FAKE LIST TOOLS RESULT
# ============================================================


@dataclass
class FakeToolsResult:
    tools: list[FakeTool]


# ============================================================
# FAKE SESSION
# ============================================================


class FakeSession:

    def __init__(self):

        self.tools = [
            FakeTool(
                name="read_document",
                description=(
                    "Read a document."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string"
                        },
                        "max_chars": {
                            "type": "integer"
                        },
                    },
                    "required": [
                        "doc_id"
                    ],
                },
            ),
            FakeTool(
                name="list_documents",
                description=(
                    "List documents."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer"
                        }
                    },
                },
            ),
        ]

        self.calls = []

    async def list_tools(self):

        return FakeToolsResult(
            tools=self.tools
        )

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ):

        self.calls.append(
            {
                "tool": tool_name,
                "arguments": arguments,
            }
        )

        if tool_name == "read_document":

            return FakeResult(
                is_error=False,
                structured_content={
                    "success": True,
                    "operation": "read_document",
                    "document_id": (
                        arguments["doc_id"]
                    ),
                },
            )

        return FakeResult(
            is_error=False,
            structured_content={
                "success": True
            },
        )


# ============================================================
# SLOW SESSION
# ============================================================


class SlowSession(FakeSession):

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ):

        await asyncio.sleep(2)

        return await super().call_tool(
            tool_name,
            arguments,
        )


# ============================================================
# ERROR SESSION
# ============================================================


class ErrorSession(FakeSession):

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ):

        return FakeResult(
            is_error=True,
            content=[
                FakeContent(
                    text=(
                        "The requested document "
                        "was not found."
                    )
                )
            ],
        )


# ============================================================
# TEST 1 — DISCOVERY
# ============================================================


async def test_tool_discovery():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    registry = await client.discover_tools()

    assert client.discovered is True
    assert len(registry) == 2
    assert "read_document" in registry
    assert "list_documents" in registry

    print(
        "TOOL DISCOVERY TEST: PASS"
    )


# ============================================================
# TEST 2 — TOOL REGISTRY
# ============================================================


async def test_tool_registry():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    assert client.has_tool(
        "read_document"
    )

    assert not client.has_tool(
        "unknown_tool"
    )

    print(
        "TOOL REGISTRY TEST: PASS"
    )


# ============================================================
# TEST 3 — ROUTING
# ============================================================


async def test_tool_routing():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    tool = client.route_tool(
        "read_document"
    )

    assert tool.name == "read_document"

    print(
        "TOOL ROUTING TEST: PASS"
    )


# ============================================================
# TEST 4 — ROUTING BEFORE DISCOVERY
# ============================================================


async def test_routing_before_discovery():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    try:

        client.route_tool(
            "read_document"
        )

    except Exception as error:

        assert (
            "discovery"
            in str(error).lower()
        )

    else:

        raise AssertionError(
            "Routing should require discovery."
        )

    print(
        "DISCOVERY GUARD TEST: PASS"
    )


# ============================================================
# TEST 5 — UNKNOWN TOOL
# ============================================================


async def test_unknown_tool():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    try:

        client.route_tool(
            "does_not_exist"
        )

    except ToolNotFoundError:

        pass

    else:

        raise AssertionError(
            "Unknown tool was not rejected."
        )

    print(
        "UNKNOWN TOOL TEST: PASS"
    )


# ============================================================
# TEST 6 — ARGUMENT VALIDATION
# ============================================================


async def test_argument_validation():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    try:

        await client.call_tool(
            "read_document",
            arguments=["invalid"],
        )

    except ValueError:

        pass

    else:

        raise AssertionError(
            "Invalid arguments were accepted."
        )

    print(
        "ARGUMENT VALIDATION TEST: PASS"
    )


# ============================================================
# TEST 7 — SUCCESSFUL TOOL EXECUTION
# ============================================================


async def test_successful_execution():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    result = await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
            "max_chars": 5000,
        },
    )

    assert result.is_error is False

    assert (
        result.structured_content[
            "document_id"
        ]
        == "report.txt"
    )

    assert len(session.calls) == 1

    print(
        "SUCCESSFUL TOOL EXECUTION TEST: PASS"
    )


# ============================================================
# TEST 8 — MCP TOOL ERROR
# ============================================================


async def test_mcp_tool_error():

    session = ErrorSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    try:

        await client.call_tool(
            "read_document",
            {
                "doc_id": "missing.txt"
            },
        )

    except ToolExecutionError as error:

        assert (
            "document"
            in str(error).lower()
        )

    else:

        raise AssertionError(
            "MCP tool error was not converted."
        )

    print(
        "MCP TOOL ERROR TEST: PASS"
    )


# ============================================================
# TEST 9 — TIMEOUT
# ============================================================


async def test_timeout():

    session = SlowSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    try:

        await client.call_tool(
            "read_document",
            {
                "doc_id": "report.txt"
            },
            timeout=0.1,
        )

    except ToolTimeoutError:

        pass

    else:

        raise AssertionError(
            "Timeout was not triggered."
        )

    history = (
        client.get_execution_history()
    )

    assert history[-1]["error_type"] == (
        "timeout"
    )

    print(
        "TIMEOUT TEST: PASS"
    )


# ============================================================
# TEST 10 — CANCELLATION
# ============================================================


async def test_cancellation():

    session = SlowSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    task = asyncio.create_task(
        client.call_tool(
            "read_document",
            {
                "doc_id": "report.txt"
            },
            timeout=10,
        )
    )

    await asyncio.sleep(0.1)

    task.cancel()

    try:

        await task

    except asyncio.CancelledError:

        pass

    else:

        raise AssertionError(
            "Cancellation was not propagated."
        )

    history = (
        client.get_execution_history()
    )

    assert history[-1]["error_type"] == (
        "cancelled"
    )

    print(
        "CANCELLATION TEST: PASS"
    )


# ============================================================
# TEST 11 — CLIENT CONTEXT
# ============================================================


async def test_client_context():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    context = (
        client.get_client_context()
    )

    assert context["discovered"] is True
    assert context["tool_count"] == 2
    assert len(context["tools"]) == 2

    print(
        "CLIENT CONTEXT TEST: PASS"
    )


# ============================================================
# TEST 12 — EXECUTION HISTORY
# ============================================================


async def test_execution_history():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt"
        },
    )

    history = (
        client.get_execution_history()
    )

    assert len(history) == 1
    assert (
        history[0]["tool"]
        == "read_document"
    )
    assert history[0]["success"] is True

    print(
        "EXECUTION HISTORY TEST: PASS"
    )


# ============================================================
# TEST 13 — INVALID TIMEOUT
# ============================================================


async def test_invalid_timeout():

    session = FakeSession()

    client = AdvancedMCPClient(
        session,
    )

    await client.discover_tools()

    try:

        await client.call_tool(
            "read_document",
            {
                "doc_id": "report.txt"
            },
            timeout=0,
        )

    except ValueError:

        pass

    else:

        raise AssertionError(
            "Invalid timeout was accepted."
        )

    print(
        "INVALID TIMEOUT TEST: PASS"
    )


# ============================================================
# TEST 14 — CLIENT DEFAULT TIMEOUT
# ============================================================


async def test_default_timeout():

    session = SlowSession()

    client = AdvancedMCPClient(
        session,
        default_timeout=0.1,
    )

    await client.discover_tools()

    try:

        await client.call_tool(
            "read_document",
            {
                "doc_id": "report.txt"
            },
        )

    except ToolTimeoutError:

        pass

    else:

        raise AssertionError(
            "Default timeout was not applied."
        )

    print(
        "DEFAULT TIMEOUT TEST: PASS"
    )


# ============================================================
# MAIN TEST RUNNER
# ============================================================


async def main():

    print()
    print("=" * 70)
    print(
        "LEVEL 8.10 — ADVANCED MCP CLIENT TEST SUITE"
    )
    print("=" * 70)

    await test_tool_discovery()
    await test_tool_registry()
    await test_tool_routing()
    await test_routing_before_discovery()
    await test_unknown_tool()
    await test_argument_validation()
    await test_successful_execution()
    await test_mcp_tool_error()
    await test_timeout()
    await test_cancellation()
    await test_client_context()
    await test_execution_history()
    await test_invalid_timeout()
    await test_default_timeout()

    print()
    print("=" * 70)
    print(
        "LEVEL 8.10 ADVANCED MCP CLIENT: PASS"
    )
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(main())