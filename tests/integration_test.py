import asyncio
import os
import sys

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


# ============================================================
# CONFIGURATION
# ============================================================

SERVER_FILE = "server.py"

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[SERVER_FILE],
    env={
        **os.environ,
        "MCP_USER_ROLE": "reader",
        "MCP_USER_ID": "integration-test-user",
    },
)


# ============================================================
# HELPERS
# ============================================================


def extract_text(result) -> str:
    """
    Extract all text content from an MCP result.
    """

    text_parts = []

    for content in getattr(result, "content", []):

        if isinstance(content, TextContent):
            text_parts.append(content.text)

    return "\n".join(text_parts)


def print_header(title: str) -> None:

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


async def create_session():

    transport = stdio_client(SERVER_PARAMS)

    read_stream, write_stream = await transport.__aenter__()

    session = ClientSession(
        read_stream,
        write_stream,
    )

    await session.__aenter__()

    await session.initialize()

    return transport, session


async def close_session(transport, session):

    await session.__aexit__(
        None,
        None,
        None,
    )

    await transport.__aexit__(
        None,
        None,
        None,
    )


# ============================================================
# TEST 1 — SERVER INITIALIZATION
# ============================================================


async def test_server_initialization():

    print_header(
        "TEST 1 — SERVER INITIALIZATION"
    )

    transport, session = await create_session()

    try:

        assert session is not None

        print(
            "MCP server initialized successfully."
        )

        print(
            "SERVER INITIALIZATION TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 2 — MCP CONNECTION
# ============================================================


async def test_mcp_connection():

    print_header(
        "TEST 2 — MCP CONNECTION"
    )

    transport, session = await create_session()

    try:

        assert session is not None

        print(
            "MCP client successfully connected "
            "through STDIO transport."
        )

        print(
            "MCP CONNECTION TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 3 — TOOL DISCOVERY
# ============================================================


async def test_tool_discovery():

    print_header(
        "TEST 3 — TOOL DISCOVERY"
    )

    transport, session = await create_session()

    try:

        result = await session.list_tools()

        tool_names = [
            tool.name
            for tool in result.tools
        ]

        expected_tools = {
            "create_document",
            "read_document",
            "update_document",
            "delete_document",
            "list_documents",
            "search_documents",
            "process_documents",
        }

        print(
            "DISCOVERED TOOLS:"
        )

        for tool_name in tool_names:

            print(
                f"  - {tool_name}"
            )

        assert expected_tools.issubset(
            set(tool_names)
        )

        assert len(tool_names) >= 7

        print(
            f"Tool count: {len(tool_names)}"
        )

        print(
            "TOOL DISCOVERY TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 4 — READ DOCUMENT TOOL
# ============================================================


async def test_read_document():

    print_header(
        "TEST 4 — READ DOCUMENT TOOL"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "read_document",
            {
                "doc_id": "report.txt",
            },
        )

        assert result.is_error is False

        text = extract_text(result)

        print(
            "READ RESULT:"
        )

        print(
            text
        )

        assert (
            "report.txt"
            in text
        )

        print(
            "READ DOCUMENT TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 5 — LIST DOCUMENTS
# ============================================================


async def test_list_documents():

    print_header(
        "TEST 5 — LIST DOCUMENTS"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "list_documents",
            {
                "page": 1,
                "page_size": 10,
            },
        )

        assert result.is_error is False

        text = extract_text(result)

        print(
            "LIST RESULT:"
        )

        print(
            text
        )

        assert (
            "report.txt"
            in text
        )

        print(
            "LIST DOCUMENTS TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 6 — SEARCH DOCUMENTS
# ============================================================


async def test_search_documents():

    print_header(
        "TEST 6 — SEARCH DOCUMENTS"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "search_documents",
            {
                "query": "MCP",
                "case_sensitive": False,
            },
        )

        assert result.is_error is False

        text = extract_text(result)

        print(
            "SEARCH RESULT:"
        )

        print(
            text
        )

        assert (
            "report.txt"
            in text
        )

        print(
            "SEARCH DOCUMENTS TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 7 — STRUCTURED OUTPUT
# ============================================================


async def test_structured_output():

    print_header(
        "TEST 7 — STRUCTURED OUTPUT"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "read_document",
            {
                "doc_id": "report.txt",
                "max_chars": 10000,
            },
        )

        assert result.is_error is False

        structured = (
            getattr(
                result,
                "structured_content",
                None,
            )
        )

        print(
            "STRUCTURED CONTENT:"
        )

        print(
            structured
        )

        assert structured is not None

        print(
            "STRUCTURED OUTPUT TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 8 — RESOURCE DISCOVERY
# ============================================================


async def test_resource_discovery():

    print_header(
        "TEST 8 — RESOURCE DISCOVERY"
    )

    transport, session = await create_session()

    try:

        result = await session.list_resources()

        resource_uris = [
            str(resource.uri)
            for resource in result.resources
        ]

        print(
            "STATIC RESOURCES:"
        )

        for uri in resource_uris:

            print(
                f"  - {uri}"
            )

        template_result = (
            await session.list_resource_templates()
        )

        template_uris = [
            str(template.uri_template)
            for template in (
                template_result.resource_templates
            )
        ]

        print(
            "RESOURCE TEMPLATES:"
        )

        for uri in template_uris:

            print(
                f"  - {uri}"
            )

        assert any(
            "document://"
            in uri
            for uri in template_uris
        )

        print(
            "RESOURCE DISCOVERY TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 9 — RESOURCE TEMPLATE
# ============================================================


async def test_resource_template():

    print_header(
        "TEST 9 — RESOURCE TEMPLATE"
    )

    transport, session = await create_session()

    try:

        result = await session.read_resource(
            "document://report.txt"
        )

        print(
            "RESOURCE RESULT:"
        )

        print(
            result
        )

        assert result is not None

        print(
            "RESOURCE TEMPLATE TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 10 — PROMPT DISCOVERY
# ============================================================


async def test_prompt_discovery():

    print_header(
        "TEST 10 — PROMPT DISCOVERY"
    )

    transport, session = await create_session()

    try:

        result = await session.list_prompts()

        prompt_names = [
            prompt.name
            for prompt in result.prompts
        ]

        print(
            "DISCOVERED PROMPTS:"
        )

        for prompt_name in prompt_names:

            print(
                f"  - {prompt_name}"
            )

        assert (
            "summarize_document"
            in prompt_names
        )

        print(
            "PROMPT DISCOVERY TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 11 — PROMPT EXECUTION
# ============================================================


async def test_prompt_execution():

    print_header(
        "TEST 11 — PROMPT EXECUTION"
    )

    transport, session = await create_session()

    try:

        result = await session.get_prompt(
            "summarize_document",
            {
                "doc_id": "report.txt",
                "focus": "main technical concepts",
                "style": "concise",
            },
        )

        print(
            "PROMPT RESULT:"
        )

        print(
            result
        )

        assert result is not None

        print(
            "PROMPT EXECUTION TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 12 — AUTHORIZATION
# ============================================================


async def test_authorization():

    print_header(
        "TEST 12 — AUTHORIZATION"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "delete_document",
            {
                "name": "report.txt",
            },
        )

        assert result.is_error is True

        text = extract_text(result)

        print(
            "AUTHORIZATION ERROR:"
        )

        print(
            text
        )

        assert (
            "authorized"
            in text.lower()
            or
            "permission"
            in text.lower()
        )

        print(
            "AUTHORIZATION TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 13 — INPUT VALIDATION
# ============================================================


async def test_input_validation():

    print_header(
        "TEST 13 — INPUT VALIDATION"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "read_document",
            {
                "doc_id": "../secret.txt",
            },
        )

        assert result.is_error is True

        text = extract_text(result)

        print(
            "VALIDATION ERROR:"
        )

        print(
            text
        )

        assert (
            "invalid"
            in text.lower()
        )

        print(
            "INPUT VALIDATION TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 14 — ERROR HANDLING
# ============================================================


async def test_error_handling():

    print_header(
        "TEST 14 — ERROR HANDLING"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "read_document",
            {
                "doc_id":
                    "integration_missing_document.txt",
            },
        )

        assert result.is_error is True

        text = extract_text(result)

        print(
            "MCP ERROR:"
        )

        print(
            text
        )

        assert (
            "not found"
            in text.lower()
        )

        print(
            "ERROR HANDLING TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 15 — PAGINATION
# ============================================================


async def test_pagination():

    print_header(
        "TEST 15 — PAGINATION"
    )

    transport, session = await create_session()

    try:

        page_one = await session.call_tool(
            "list_documents",
            {
                "page": 1,
                "page_size": 1,
            },
        )

        assert page_one.is_error is False

        page_two = await session.call_tool(
            "list_documents",
            {
                "page": 2,
                "page_size": 1,
            },
        )

        assert page_two.is_error is False

        text_one = extract_text(
            page_one
        )

        text_two = extract_text(
            page_two
        )

        print(
            "PAGE 1:"
        )

        print(
            text_one
        )

        print(
            "PAGE 2:"
        )

        print(
            text_two
        )

        assert text_one != text_two

        print(
            "PAGINATION TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 16 — BATCH PROCESSING
# ============================================================


async def test_batch_processing():

    print_header(
        "TEST 16 — BATCH PROCESSING"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "process_documents",
            {
                "document_ids": [
                    "report.txt",
                    "report.txt",
                ],
            },
        )

        assert result.is_error is False

        text = extract_text(result)

        print(
            "BATCH RESULT:"
        )

        print(
            text
        )

        assert (
            "process_documents"
            in text
            or
            "report.txt"
            in text
        )

        print(
            "BATCH PROCESSING TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 17 — UNKNOWN TOOL
# ============================================================


async def test_unknown_tool():

    print_header(
        "TEST 17 — UNKNOWN TOOL"
    )

    transport, session = await create_session()

    try:

        result = await session.call_tool(
            "tool_that_does_not_exist",
            {},
        )

        assert result.is_error is True

        text = extract_text(result)

        print(
            "UNKNOWN TOOL ERROR:"
        )

        print(
            text
        )

        assert (
            "unknown tool"
            in text.lower()
        )

        print(
            "UNKNOWN TOOL TEST: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# TEST 18 — END-TO-END READ WORKFLOW
# ============================================================


async def test_end_to_end_workflow():

    print_header(
        "TEST 18 — END-TO-END MCP WORKFLOW"
    )

    transport, session = await create_session()

    try:

        # ----------------------------------------------------
        # Step 1 — Discover tools
        # ----------------------------------------------------

        tools = await session.list_tools()

        tool_names = {
            tool.name
            for tool in tools.tools
        }

        assert (
            "read_document"
            in tool_names
        )

        print(
            "[1] Tool discovery: PASS"
        )

        # ----------------------------------------------------
        # Step 2 — Read document
        # ----------------------------------------------------

        read_result = await session.call_tool(
            "read_document",
            {
                "doc_id": "report.txt",
            },
        )

        assert (
            read_result.is_error
            is False
        )

        read_text = extract_text(
            read_result
        )

        assert (
            "MCP"
            in read_text
        )

        print(
            "[2] Document read: PASS"
        )

        # ----------------------------------------------------
        # Step 3 — Search document
        # ----------------------------------------------------

        search_result = await session.call_tool(
            "search_documents",
            {
                "query": "MCP",
                "case_sensitive": False,
            },
        )

        assert (
            search_result.is_error
            is False
        )

        print(
            "[3] Document search: PASS"
        )

        # ----------------------------------------------------
        # Step 4 — Read through resource
        # ----------------------------------------------------

        resource_result = (
            await session.read_resource(
                "document://report.txt"
            )
        )

        assert (
            resource_result
            is not None
        )

        print(
            "[4] Resource access: PASS"
        )

        # ----------------------------------------------------
        # Step 5 — Generate prompt
        # ----------------------------------------------------

        prompt_result = (
            await session.get_prompt(
                "summarize_document",
                {
                    "doc_id":
                        "report.txt",
                    "focus":
                        "main ideas",
                    "style":
                        "concise",
                },
            )
        )

        assert (
            prompt_result
            is not None
        )

        print(
            "[5] Prompt generation: PASS"
        )

        print()
        print(
            "END-TO-END WORKFLOW: PASS"
        )

    finally:

        await close_session(
            transport,
            session,
        )


# ============================================================
# MAIN TEST RUNNER
# ============================================================


async def main():

    print()
    print(
        "=" * 70
    )
    print(
        "LEVEL 8.12 — MCP INTEGRATION & TESTING SUITE"
    )
    print(
        "=" * 70
    )

    tests = [
        test_server_initialization,
        test_mcp_connection,
        test_tool_discovery,
        test_read_document,
        test_list_documents,
        test_search_documents,
        test_structured_output,
        test_resource_discovery,
        test_resource_template,
        test_prompt_discovery,
        test_prompt_execution,
        test_authorization,
        test_input_validation,
        test_error_handling,
        test_pagination,
        test_batch_processing,
        test_unknown_tool,
        test_end_to_end_workflow,
    ]

    passed = 0
    failed = 0

    for test in tests:

        try:

            await test()

            passed += 1

        except Exception as error:

            failed += 1

            print()
            print(
                f"{test.__name__}: FAIL"
            )

            print(
                f"ERROR: {error}"
            )

    print()
    print(
        "=" * 70
    )

    print(
        f"TESTS PASSED: {passed}"
    )

    print(
        f"TESTS FAILED: {failed}"
    )

    print(
        f"TOTAL TESTS : {len(tests)}"
    )

    print(
        "=" * 70
    )

    if failed == 0:

        print()
        print(
            "LEVEL 8.12 MCP INTEGRATION & TESTING: PASS"
        )
        print()

    else:

        print()
        print(
            "LEVEL 8.12 MCP INTEGRATION & TESTING: FAIL"
        )
        print()


if __name__ == "__main__":

    asyncio.run(main())