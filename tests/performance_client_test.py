import asyncio
import time
from dataclasses import dataclass
from typing import Any

from performance_client import (
    OptimizedMCPClient,
    CACHEABLE_TOOLS,
    INVALIDATING_TOOLS,
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
# FAKE TOOLS RESPONSE
# ============================================================


@dataclass
class FakeToolsResult:

    tools: list[FakeTool]


# ============================================================
# FAKE SESSION
# ============================================================


class FakeSession:

    def __init__(
        self,
        delay: float = 0.0,
    ):

        self.delay = delay

        self.calls: list[
            dict[str, Any]
        ] = []

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
                },
            ),

            FakeTool(
                name="search_documents",
                description=(
                    "Search documents."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        },
                    },
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
                        },
                        "page_size": {
                            "type": "integer"
                        },
                    },
                },
            ),

            FakeTool(
                name="update_document",
                description=(
                    "Update a document."
                ),
                input_schema={
                    "type": "object"
                },
            ),

            FakeTool(
                name="create_document",
                description=(
                    "Create a document."
                ),
                input_schema={
                    "type": "object"
                },
            ),

            FakeTool(
                name="delete_document",
                description=(
                    "Delete a document."
                ),
                input_schema={
                    "type": "object"
                },
            ),
        ]

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
                "arguments": arguments.copy(),
            }
        )

        if self.delay:

            await asyncio.sleep(
                self.delay
            )

        if tool_name == "read_document":

            return FakeResult(
                structured_content={
                    "success": True,
                    "operation": (
                        "read_document"
                    ),
                    "document_id": (
                        arguments["doc_id"]
                    ),
                    "content": (
                        "Test document"
                    ),
                    "characters_returned": 14,
                    "truncated": False,
                }
            )

        if tool_name == "search_documents":

            return FakeResult(
                structured_content={
                    "success": True,
                    "operation": (
                        "search_documents"
                    ),
                    "query": arguments["query"],
                    "documents": [
                        "report.txt"
                    ],
                    "count": 1,
                }
            )

        if tool_name == "list_documents":

            page = arguments.get(
                "page",
                1,
            )

            page_size = arguments.get(
                "page_size",
                10,
            )

            all_documents = [
                {
                    "name": "report.txt",
                    "size": 100,
                },
                {
                    "name": "notes.txt",
                    "size": 200,
                },
                {
                    "name": "summary.txt",
                    "size": 300,
                },
            ]

            start = (
                (page - 1)
                * page_size
            )

            end = (
                start
                + page_size
            )

            page_documents = (
                all_documents[
                    start:end
                ]
            )

            total_documents = len(
                all_documents
            )

            total_pages = (
                (
                    total_documents
                    + page_size
                    - 1
                )
                // page_size
            )

            return FakeResult(
                structured_content={
                    "success": True,
                    "operation": (
                        "list_documents"
                    ),
                    "documents": (
                        page_documents
                    ),
                    "page": page,
                    "page_size": page_size,
                    "total_documents": (
                        total_documents
                    ),
                    "total_pages": (
                        total_pages
                    ),
                    "has_next_page": (
                        page < total_pages
                    ),
                }
            )

        return FakeResult(
            structured_content={
                "success": True,
                "operation": tool_name,
            }
        )


# ============================================================
# TEST 1 — CACHEABLE TOOLS
# ============================================================


async def test_cacheable_tools():

    assert "read_document" in (
        CACHEABLE_TOOLS
    )

    assert "list_documents" in (
        CACHEABLE_TOOLS
    )

    assert "search_documents" in (
        CACHEABLE_TOOLS
    )

    print(
        "CACHEABLE TOOLS TEST: PASS"
    )


# ============================================================
# TEST 2 — INVALIDATING TOOLS
# ============================================================


async def test_invalidating_tools():

    assert "create_document" in (
        INVALIDATING_TOOLS
    )

    assert "update_document" in (
        INVALIDATING_TOOLS
    )

    assert "delete_document" in (
        INVALIDATING_TOOLS
    )

    print(
        "CACHE INVALIDATION TOOLS TEST: PASS"
    )


# ============================================================
# TEST 3 — FIRST REQUEST IS CACHE MISS
# ============================================================


async def test_cache_miss():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
            "max_chars": 5000,
        },
    )

    assert len(session.calls) == 1

    assert (
        client.metrics.cache_misses
        == 1
    )

    print(
        "CACHE MISS TEST: PASS"
    )


# ============================================================
# TEST 4 — SECOND REQUEST IS CACHE HIT
# ============================================================


async def test_cache_hit():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    first = await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
            "max_chars": 5000,
        },
    )

    second = await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
            "max_chars": 5000,
        },
    )

    assert len(session.calls) == 1

    assert (
        client.metrics.cache_hits
        == 1
    )

    assert first is second

    print(
        "CACHE HIT TEST: PASS"
    )


# ============================================================
# TEST 5 — CACHE TTL
# ============================================================


async def test_cache_ttl():

    session = FakeSession()

    client = OptimizedMCPClient(
        session,
        cache_ttl=0.05,
    )

    await client.discover_tools()

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
        },
    )

    await asyncio.sleep(
        0.08
    )

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
        },
    )

    assert len(session.calls) == 2

    print(
        "CACHE TTL TEST: PASS"
    )


# ============================================================
# TEST 6 — DOCUMENT INVALIDATION
# ============================================================


async def test_document_invalidation():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
        },
    )

    assert len(session.calls) == 1

    client.invalidate_document(
        "report.txt"
    )

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
        },
    )

    assert len(session.calls) == 2

    print(
        "DOCUMENT CACHE INVALIDATION TEST: PASS"
    )


# ============================================================
# TEST 7 — ALL CACHE INVALIDATION
# ============================================================


async def test_invalidate_all():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
        },
    )

    assert (
        client.get_cache_info()["entries"]
        == 1
    )

    client.invalidate_all()

    assert (
        client.get_cache_info()["entries"]
        == 0
    )

    print(
        "FULL CACHE INVALIDATION TEST: PASS"
    )


# ============================================================
# TEST 8 — PARALLEL EXECUTION
# ============================================================


async def test_parallel_execution():

    session = FakeSession(
        delay=0.2
    )

    client = OptimizedMCPClient(
        session,
        max_concurrency=4,
    )

    await client.discover_tools()

    requests = [

        (
            "read_document",
            {
                "doc_id": "report.txt"
            },
        ),

        (
            "read_document",
            {
                "doc_id": "notes.txt"
            },
        ),

        (
            "search_documents",
            {
                "query": "MCP"
            },
        ),

    ]

    start = time.perf_counter()

    results = (
        await client.call_tools_parallel(
            requests
        )
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    assert len(results) == 3

    assert len(session.calls) == 3

    # Three 0.2-second operations should
    # complete close to one delay period
    # rather than three sequential delays.

    assert elapsed < 0.5

    assert (
        client.metrics.parallel_calls
        == 3
    )

    print(
        "PARALLEL EXECUTION TEST: PASS"
    )


# ============================================================
# TEST 9 — CONCURRENCY LIMIT
# ============================================================


async def test_concurrency_limit():

    session = FakeSession(
        delay=0.1
    )

    client = OptimizedMCPClient(
        session,
        max_concurrency=2,
    )

    await client.discover_tools()

    requests = [

        (
            "read_document",
            {
                "doc_id": "a.txt"
            },
        ),

        (
            "read_document",
            {
                "doc_id": "b.txt"
            },
        ),

        (
            "read_document",
            {
                "doc_id": "c.txt"
            },
        ),

        (
            "read_document",
            {
                "doc_id": "d.txt"
            },
        ),

    ]

    start = time.perf_counter()

    await client.call_tools_parallel(
        requests
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    assert len(session.calls) == 4

    # With concurrency=2, four 0.1-second
    # operations require approximately
    # two waves.

    assert elapsed >= 0.18

    print(
        "CONCURRENCY LIMIT TEST: PASS"
    )


# ============================================================
# TEST 10 — PAGINATION
# ============================================================


async def test_pagination():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    documents = (
        await client.list_all_documents(
            page_size=2
        )
    )

    assert len(documents) == 3

    assert (
        documents[0]["name"]
        == "report.txt"
    )

    assert (
        documents[2]["name"]
        == "summary.txt"
    )

    print(
        "PAGINATION OPTIMIZATION TEST: PASS"
    )


# ============================================================
# TEST 11 — COMPACT CONTEXT
# ============================================================


async def test_compact_context():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    context = (
        client.build_compact_context()
    )

    assert (
        context["tool_count"]
        == 6
    )

    assert (
        context["included_tools"]
        <= context["tool_count"]
    )

    assert (
        "input_schema"
        not in context["tools"][0]
    )

    print(
        "COMPACT CONTEXT TEST: PASS"
    )


# ============================================================
# TEST 12 — COMPACT CONTEXT LIMIT
# ============================================================


async def test_compact_context_limit():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    context = (
        client.build_compact_context(
            max_chars=150
        )
    )

    assert (
        context["context_characters"]
        <= 150
    )

    print(
        "CONTEXT SIZE LIMIT TEST: PASS"
    )


# ============================================================
# TEST 13 — PERFORMANCE METRICS
# ============================================================


async def test_performance_metrics():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt"
        },
    )

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt"
        },
    )

    report = (
        client.get_performance_report()
    )

    metrics = report["metrics"]

    assert metrics["total_calls"] == 1

    assert metrics["successful_calls"] == 1

    assert metrics["cache_hits"] == 1

    assert metrics["cache_misses"] == 1

    assert (
        metrics["cache_hit_rate"]
        == 0.5
    )

    print(
        "PERFORMANCE METRICS TEST: PASS"
    )


# ============================================================
# TEST 14 — INVALID CONFIGURATION
# ============================================================


async def test_invalid_configuration():

    session = FakeSession()

    try:

        OptimizedMCPClient(
            session,
            cache_ttl=-1,
        )

    except ValueError:

        pass

    else:

        raise AssertionError(
            "Negative cache TTL accepted."
        )

    try:

        OptimizedMCPClient(
            session,
            max_concurrency=0,
        )

    except ValueError:

        pass

    else:

        raise AssertionError(
            "Invalid concurrency accepted."
        )

    print(
        "PERFORMANCE CONFIGURATION TEST: PASS"
    )


# ============================================================
# TEST 15 — CACHE KEY ARGUMENT DIFFERENCE
# ============================================================


async def test_cache_key_arguments():

    session = FakeSession()

    client = OptimizedMCPClient(
        session
    )

    await client.discover_tools()

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
            "max_chars": 1000,
        },
    )

    await client.call_tool(
        "read_document",
        {
            "doc_id": "report.txt",
            "max_chars": 5000,
        },
    )

    assert len(session.calls) == 2

    print(
        "CACHE KEY ARGUMENT TEST: PASS"
    )


# ============================================================
# MAIN TEST RUNNER
# ============================================================


async def main():

    print()
    print("=" * 70)
    print(
        "LEVEL 8.11 — PERFORMANCE & "
        "OPTIMIZATION TEST SUITE"
    )
    print("=" * 70)

    await test_cacheable_tools()

    await test_invalidating_tools()

    await test_cache_miss()

    await test_cache_hit()

    await test_cache_ttl()

    await test_document_invalidation()

    await test_invalidate_all()

    await test_parallel_execution()

    await test_concurrency_limit()

    await test_pagination()

    await test_compact_context()

    await test_compact_context_limit()

    await test_performance_metrics()

    await test_invalid_configuration()

    await test_cache_key_arguments()

    print()
    print("=" * 70)
    print(
        "LEVEL 8.11 PERFORMANCE & "
        "OPTIMIZATION: PASS"
    )
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(main())