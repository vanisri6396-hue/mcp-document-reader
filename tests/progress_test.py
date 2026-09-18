import asyncio

import anyio

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_normal_completion() -> None:

    print(
        "\n========================================"
    )
    print(
        "TEST 1 — NORMAL COMPLETION"
    )
    print(
        "========================================"
    )

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    progress_events = []

    async def progress_callback(
        progress: float,
        total: float | None,
        message: str | None,
    ) -> None:

        event = {
            "progress": progress,
            "total": total,
            "message": message,
        }

        progress_events.append(
            event
        )

        print(
            f"PROGRESS: "
            f"{progress}/{total} "
            f"| {message}"
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

            print(
                "MCP SESSION INITIALIZED"
            )

            result = await session.call_tool(
                "process_documents",
                {
                    "document_ids": [
                        "report.txt",
                        "report.txt",
                        "report.txt",
                    ],
                },
                progress_callback=(
                    progress_callback
                ),
            )

            print(
                "TOOL CALL COMPLETED"
            )

            print(
                "PROGRESS EVENTS:",
                len(progress_events),
            )

            print(
                "FINAL RESULT:"
            )

            print(
                result
            )

            if not progress_events:

                raise RuntimeError(
                    "No progress notifications received."
                )

            print(
                "NORMAL COMPLETION TEST: PASS"
            )


async def test_cancellation() -> None:

    print(
        "\n========================================"
    )
    print(
        "TEST 2 — CANCELLATION"
    )
    print(
        "========================================"
    )

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    progress_events = []

    async def progress_callback(
        progress: float,
        total: float | None,
        message: str | None,
    ) -> None:

        event = {
            "progress": progress,
            "total": total,
            "message": message,
        }

        progress_events.append(
            event
        )

        print(
            f"PROGRESS: "
            f"{progress}/{total} "
            f"| {message}"
        )

        # Cancel after the first actual
        # document-processing progress event.

        if (
            progress >= 1
            and total is not None
        ):
            cancel_scope.cancel()

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

            print(
                "MCP SESSION INITIALIZED"
            )

            async with anyio.create_task_group() as task_group:

                cancel_scope = task_group.cancel_scope

                async def run_tool() -> None:

                    await session.call_tool(
                        "process_documents",
                        {
                            "document_ids": [
                                "report.txt",
                                "report.txt",
                                "report.txt",
                                "report.txt",
                                "report.txt",
                            ],
                        },
                        progress_callback=(
                            progress_callback
                        ),
                    )

                task_group.start_soon(
                    run_tool
                )

            print(
                "CLIENT CANCEL SCOPE COMPLETED"
            )

            if not progress_events:

                raise RuntimeError(
                    "Cancellation test received no progress events."
                )

            print(
                "CANCELLATION TEST: PASS"
            )


async def main() -> None:

    await test_normal_completion()

    await test_cancellation()

    print(
        "\n========================================"
    )
    print(
        "LEVEL 8.8 CANCELLATION TEST SUITE: PASS"
    )
    print(
        "========================================"
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )