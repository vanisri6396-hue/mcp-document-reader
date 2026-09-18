import asyncio
import time
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from advanced_client import (
    AdvancedMCPClient,
    ToolExecutionError,
    ToolTimeoutError,
)


# ============================================================
# MCP SERVER CONFIGURATION
# ============================================================

SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=["server.py"],
)


# ============================================================
# PERFORMANCE CONFIGURATION
# ============================================================

CACHEABLE_TOOLS = {
    "read_document",
    "list_documents",
    "search_documents",
}

INVALIDATING_TOOLS = {
    "create_document",
    "update_document",
    "delete_document",
}

DEFAULT_CACHE_TTL = 30.0

DEFAULT_MAX_CONCURRENCY = 4

DEFAULT_MAX_CONTEXT_CHARS = 1200


# ============================================================
# CACHE ENTRY
# ============================================================


@dataclass
class CacheEntry:

    value: Any
    created_at: float


# ============================================================
# PERFORMANCE METRICS
# ============================================================


@dataclass
class PerformanceMetrics:

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0

    cache_hits: int = 0
    cache_misses: int = 0

    parallel_calls: int = 0

    total_elapsed_seconds: float = 0.0

    @property
    def cache_hit_rate(self) -> float:

        total_cache_requests = (
            self.cache_hits
            + self.cache_misses
        )

        if total_cache_requests == 0:
            return 0.0

        return (
            self.cache_hits
            / total_cache_requests
        )

    @property
    def average_latency_seconds(self) -> float:

        if self.total_calls == 0:
            return 0.0

        return (
            self.total_elapsed_seconds
            / self.total_calls
        )

    def as_dict(self) -> dict[str, Any]:

        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hit_rate,
            "parallel_calls": self.parallel_calls,
            "total_elapsed_seconds": (
                self.total_elapsed_seconds
            ),
            "average_latency_seconds": (
                self.average_latency_seconds
            ),
        }


# ============================================================
# OPTIMIZED MCP CLIENT
# ============================================================


class OptimizedMCPClient(AdvancedMCPClient):
    """
    Performance-optimized MCP client.

    Features:

    - TTL-based client-side caching
    - Cache invalidation
    - Compact AI context
    - Pagination helper
    - Bounded parallel execution
    - Performance metrics
    - Result reuse
    """

    def __init__(
        self,
        session: ClientSession,
        default_timeout: float = 10.0,
        cache_ttl: float = DEFAULT_CACHE_TTL,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    ) -> None:

        super().__init__(
            session=session,
            default_timeout=default_timeout,
        )

        if cache_ttl < 0:
            raise ValueError(
                "cache_ttl cannot be negative."
            )

        if max_concurrency < 1:
            raise ValueError(
                "max_concurrency must be at least 1."
            )

        self.cache_ttl = cache_ttl

        self.max_concurrency = (
            max_concurrency
        )

        self._cache: dict[
            tuple[str, tuple[tuple[str, Any], ...]],
            CacheEntry,
        ] = {}

        self.metrics = PerformanceMetrics()

        self._concurrency_semaphore = (
            asyncio.Semaphore(
                self.max_concurrency
            )
        )

    # ========================================================
    # CACHE KEY
    # ========================================================

    @staticmethod
    def _make_cache_key(
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[
        str,
        tuple[tuple[str, Any], ...],
    ]:

        normalized_arguments = []

        for key, value in sorted(
            arguments.items()
        ):

            try:

                hash(value)

                normalized_value = value

            except TypeError:

                normalized_value = repr(
                    value
                )

            normalized_arguments.append(
                (
                    str(key),
                    normalized_value,
                )
            )

        return (
            tool_name,
            tuple(normalized_arguments),
        )

    # ========================================================
    # CACHE CHECK
    # ========================================================

    def _get_cached(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any | None:

        if tool_name not in CACHEABLE_TOOLS:
            return None

        key = self._make_cache_key(
            tool_name,
            arguments,
        )

        entry = self._cache.get(key)

        if entry is None:

            self.metrics.cache_misses += 1

            return None

        age = (
            time.perf_counter()
            - entry.created_at
        )

        if age > self.cache_ttl:

            self._cache.pop(
                key,
                None,
            )

            self.metrics.cache_misses += 1

            return None

        self.metrics.cache_hits += 1

        return entry.value

    # ========================================================
    # CACHE STORE
    # ========================================================

    def _store_cache(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        value: Any,
    ) -> None:

        if tool_name not in CACHEABLE_TOOLS:
            return

        key = self._make_cache_key(
            tool_name,
            arguments,
        )

        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.perf_counter(),
        )

    # ========================================================
    # CACHE INVALIDATION
    # ========================================================

    def invalidate_document(
        self,
        document_id: str,
    ) -> None:
        """
        Remove cache entries associated with
        a particular document.
        """

        keys_to_remove = []

        for key in self._cache:

            tool_name, arguments = key

            if tool_name == "read_document":

                arguments_dict = dict(
                    arguments
                )

                if (
                    arguments_dict.get(
                        "doc_id"
                    )
                    == document_id
                ):

                    keys_to_remove.append(
                        key
                    )

        for key in keys_to_remove:

            self._cache.pop(
                key,
                None,
            )

    def invalidate_all(self) -> None:

        self._cache.clear()

    # ========================================================
    # OVERRIDE TOOL CALL
    # ========================================================

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:

        validated_arguments = (
            self.validate_arguments(
                arguments
            )
        )

        # ----------------------------------------------------
        # CACHE LOOKUP
        # ----------------------------------------------------

        cached_result = self._get_cached(
            tool_name,
            validated_arguments,
        )

        if cached_result is not None:

            return cached_result

        # ----------------------------------------------------
        # REAL MCP CALL
        # ----------------------------------------------------

        start_time = (
            time.perf_counter()
        )

        self.metrics.total_calls += 1

        try:

            result = await super().call_tool(
                tool_name,
                validated_arguments,
                timeout,
            )

            self.metrics.successful_calls += 1

            elapsed = (
                time.perf_counter()
                - start_time
            )

            self.metrics.total_elapsed_seconds += (
                elapsed
            )

            # ------------------------------------------------
            # CACHE READ-ONLY RESULTS
            # ------------------------------------------------

            if tool_name in CACHEABLE_TOOLS:

                self._store_cache(
                    tool_name,
                    validated_arguments,
                    result,
                )

            # ------------------------------------------------
            # INVALIDATE AFTER WRITES
            # ------------------------------------------------

            if tool_name in INVALIDATING_TOOLS:

                document_id = (
                    validated_arguments.get(
                        "doc_id"
                    )
                    or validated_arguments.get(
                        "name"
                    )
                )

                if document_id:

                    self.invalidate_document(
                        document_id
                    )

                else:

                    self.invalidate_all()

            return result

        except (
            ToolExecutionError,
            ToolTimeoutError,
        ):

            self.metrics.failed_calls += 1

            elapsed = (
                time.perf_counter()
                - start_time
            )

            self.metrics.total_elapsed_seconds += (
                elapsed
            )

            raise

        except Exception:

            self.metrics.failed_calls += 1

            elapsed = (
                time.perf_counter()
                - start_time
            )

            self.metrics.total_elapsed_seconds += (
                elapsed
            )

            raise

    # ========================================================
    # PARALLEL TOOL EXECUTION
    # ========================================================

    async def call_tools_parallel(
        self,
        requests: list[
            tuple[
                str,
                dict[str, Any] | None,
            ]
        ],
        timeout: float | None = None,
    ) -> list[Any]:
        """
        Execute independent MCP tool calls concurrently.

        Concurrency is bounded to avoid overwhelming
        the MCP server or triggering excessive load.
        """

        if not isinstance(
            requests,
            list,
        ):

            raise ValueError(
                "requests must be a list."
            )

        if not requests:

            return []

        async def execute_request(
            request: tuple[
                str,
                dict[str, Any] | None,
            ],
        ):

            tool_name, arguments = request

            async with (
                self._concurrency_semaphore
            ):

                return await self.call_tool(
                    tool_name,
                    arguments,
                    timeout,
                )

        self.metrics.parallel_calls += len(
            requests
        )

        return await asyncio.gather(
            *[
                execute_request(request)
                for request in requests
            ]
        )

    # ========================================================
    # PAGINATION HELPER
    # ========================================================

    async def list_all_documents(
        self,
        page_size: int = 10,
        max_pages: int = 100,
    ) -> list[Any]:
        """
        Automatically retrieve all document pages.

        Stops when the server reports that no next page exists.
        """

        if page_size < 1:
            raise ValueError(
                "page_size must be at least 1."
            )

        if max_pages < 1:
            raise ValueError(
                "max_pages must be at least 1."
            )

        all_documents = []

        page = 1

        while page <= max_pages:

            result = await self.call_tool(
                "list_documents",
                {
                    "page": page,
                    "page_size": page_size,
                },
            )

            structured = (
                getattr(
                    result,
                    "structured_content",
                    None,
                )
            )

            if structured:

                documents = structured.get(
                    "documents",
                    [],
                )

                all_documents.extend(
                    documents
                )

                has_next_page = structured.get(
                    "has_next_page",
                    False,
                )

            else:

                break

            if not has_next_page:

                break

            page += 1

        return all_documents

    # ========================================================
    # COMPACT AI CONTEXT
    # ========================================================

    def build_compact_context(
        self,
        max_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
    ) -> dict[str, Any]:

        if max_chars < 100:
            raise ValueError(
                "max_chars must be at least 100."
            )

        compact_tools = []

        total_chars = 0

        for tool in self._tools.values():

            description = (
                tool.description
                or ""
            )

            if len(description) > 160:

                description = (
                    description[:157]
                    + "..."
                )

            entry = {
                "name": tool.name,
                "description": description,
            }

            entry_size = len(
                str(entry)
            )

            if (
                total_chars
                + entry_size
                > max_chars
            ):

                break

            compact_tools.append(
                entry
            )

            total_chars += entry_size

        return {
            "tool_count": len(
                self._tools
            ),
            "included_tools": len(
                compact_tools
            ),
            "tools": compact_tools,
            "context_characters": total_chars,
        }

    # ========================================================
    # CACHE INFORMATION
    # ========================================================

    def get_cache_info(
        self,
    ) -> dict[str, Any]:

        return {
            "entries": len(
                self._cache
            ),
            "ttl_seconds": self.cache_ttl,
        }

    # ========================================================
    # PERFORMANCE REPORT
    # ========================================================

    def get_performance_report(
        self,
    ) -> dict[str, Any]:

        return {
            "metrics": self.metrics.as_dict(),
            "cache": self.get_cache_info(),
            "max_concurrency": (
                self.max_concurrency
            ),
        }


# ============================================================
# REAL MCP DEMONSTRATION
# ============================================================


async def main() -> None:

    print("=" * 70)
    print(
        "LEVEL 8.11 — MCP PERFORMANCE & OPTIMIZATION"
    )
    print("=" * 70)

    async with stdio_client(
        SERVER_PARAMS
    ) as (read, write):

        async with ClientSession(
            read,
            write,
        ) as session:

            await session.initialize()

            print(
                "\nMCP SESSION INITIALIZED"
            )

            client = OptimizedMCPClient(
                session=session,
                default_timeout=10.0,
                cache_ttl=30.0,
                max_concurrency=4,
            )

            # ------------------------------------------------
            # DISCOVERY
            # ------------------------------------------------

            print("\n[1] TOOL DISCOVERY")
            print("-" * 70)

            await client.discover_tools()

            print(
                f"Discovered "
                f"{len(client.get_tool_registry())} "
                f"tools."
            )

            # ------------------------------------------------
            # COMPACT CONTEXT
            # ------------------------------------------------

            print(
                "\n[2] COMPACT AI CONTEXT"
            )
            print("-" * 70)

            compact_context = (
                client.build_compact_context()
            )

            print(
                compact_context
            )

            # ------------------------------------------------
            # FIRST READ — CACHE MISS
            # ------------------------------------------------

            print(
                "\n[3] FIRST DOCUMENT READ"
            )
            print("-" * 70)

            start = time.perf_counter()

            await client.call_tool(
                "read_document",
                {
                    "doc_id": "report.txt",
                    "max_chars": 5000,
                },
            )

            first_latency = (
                time.perf_counter()
                - start
            )

            print(
                f"First read latency: "
                f"{first_latency:.6f}s"
            )

            # ------------------------------------------------
            # SECOND READ — CACHE HIT
            # ------------------------------------------------

            print(
                "\n[4] SECOND DOCUMENT READ"
            )
            print("-" * 70)

            start = time.perf_counter()

            await client.call_tool(
                "read_document",
                {
                    "doc_id": "report.txt",
                    "max_chars": 5000,
                },
            )

            second_latency = (
                time.perf_counter()
                - start
            )

            print(
                f"Second read latency: "
                f"{second_latency:.6f}s"
            )

            # ------------------------------------------------
            # PAGINATION
            # ------------------------------------------------

            print(
                "\n[5] PAGINATION OPTIMIZATION"
            )
            print("-" * 70)

            documents = (
                await client.list_all_documents(
                    page_size=10
                )
            )

            print(
                f"Retrieved "
                f"{len(documents)} "
                f"document(s)."
            )

            # ------------------------------------------------
            # PARALLEL EXECUTION
            # ------------------------------------------------

            print(
                "\n[6] PARALLEL EXECUTION"
            )
            print("-" * 70)

            requests = [
                (
                    "read_document",
                    {
                        "doc_id": "report.txt",
                        "max_chars": 5000,
                    },
                ),
                (
                    "search_documents",
                    {
                        "query": "MCP",
                        "case_sensitive": False,
                    },
                ),
            ]

            parallel_start = (
                time.perf_counter()
            )

            results = (
                await client.call_tools_parallel(
                    requests
                )
            )

            parallel_elapsed = (
                time.perf_counter()
                - parallel_start
            )

            print(
                f"Parallel operations: "
                f"{len(results)}"
            )

            print(
                f"Parallel elapsed time: "
                f"{parallel_elapsed:.6f}s"
            )

            # ------------------------------------------------
            # PERFORMANCE REPORT
            # ------------------------------------------------

            print(
                "\n[7] PERFORMANCE REPORT"
            )
            print("-" * 70)

            print(
                client.get_performance_report()
            )

    print(
        "\n" + "=" * 70
    )

    print(
        "LEVEL 8.11 PERFORMANCE "
        "DEMONSTRATION COMPLETED"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    asyncio.run(main())