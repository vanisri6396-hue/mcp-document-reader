import asyncio
import anyio

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_normal_completion():
    print("\n========================================")
    print("TEST 1 — NORMAL COMPLETION")
    print("========================================")

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    progress_events = []

    async def progress_callback(progress, total, message):
        event = {
            "progress": progress,
            "total": total,
            "message": message,
        }

        progress_events.append(event)

        print(
            f"PROGRESS: {progress}/{total} | {message}"
        )

    async with stdio_client(server_params) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("MCP SESSION INITIALIZED")

            result = await session.call_tool(
                "process_documents",
                {
                    "document_ids": [
                        "report.txt",
                        "report.txt",
                        "report.txt",
                    ]
                },
                progress_callback=progress_callback,
            )

            print("TOOL CALL COMPLETED")

            print(
                "PROGRESS EVENTS:",
                len(progress_events),
            )

            print("FINAL RESULT:")
            print(result)

            if not progress_events:
                raise RuntimeError(
                    "No progress notifications received."
                )

            print("NORMAL COMPLETION TEST: PASS")


async def test_cancellation():
    print("\n========================================")
    print("TEST 2 — CANCELLATION")
    print("========================================")

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    progress_events = []

    async def progress_callback(
        progress,
        total,
        message,
    ):
        event = {
            "progress": progress,
            "total": total,
            "message": message,
        }

        progress_events.append(event)

        print(
            f"PROGRESS: {progress}/{total} | {message}"
        )

        if progress >= 1 and total is not None:
            cancel_scope.cancel()

    async with stdio_client(server_params) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("MCP SESSION INITIALIZED")

            async with anyio.create_task_group() as task_group:

                cancel_scope = task_group.cancel_scope

                async def run_tool():
                    await session.call_tool(
                        "process_documents",
                        {
                            "document_ids": [
                                "report.txt",
                                "report.txt",
                                "report.txt",
                                "report.txt",
                                "report.txt",
                            ]
                        },
                        progress_callback=progress_callback,
                    )

                task_group.start_soon(run_tool)

            print("CLIENT CANCEL SCOPE COMPLETED")

            if not progress_events:
                raise RuntimeError(
                    "Cancellation test received no progress events."
                )

            print("CANCELLATION TEST: PASS")


async def test_timeout_success():
    print("\n========================================")
    print("TEST 3 — TIMEOUT WITH ENOUGH TIME")
    print("========================================")

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    progress_events = []

    async def progress_callback(
        progress,
        total,
        message,
    ):
        progress_events.append(
            {
                "progress": progress,
                "total": total,
                "message": message,
            }
        )

        print(
            f"PROGRESS: {progress}/{total} | {message}"
        )

    async with stdio_client(server_params) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("MCP SESSION INITIALIZED")

            try:
                with anyio.fail_after(5):
                    result = await session.call_tool(
                        "process_documents",
                        {
                            "document_ids": [
                                "report.txt",
                                "report.txt",
                                "report.txt",
                            ]
                        },
                        progress_callback=progress_callback,
                    )

                print("TOOL COMPLETED BEFORE TIMEOUT")
                print("FINAL RESULT:")
                print(result)

            except TimeoutError:
                raise RuntimeError(
                    "Unexpected timeout during successful timeout test."
                )

            if not progress_events:
                raise RuntimeError(
                    "No progress notifications received."
                )

            print(
                "TIMEOUT SUCCESS TEST: PASS"
            )


async def test_timeout_triggered():
    print("\n========================================")
    print("TEST 4 — TIMEOUT TRIGGERED")
    print("========================================")

    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    progress_events = []

    async def progress_callback(
        progress,
        total,
        message,
    ):
        progress_events.append(
            {
                "progress": progress,
                "total": total,
                "message": message,
            }
        )

        print(
            f"PROGRESS: {progress}/{total} | {message}"
        )

    async with stdio_client(server_params) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("MCP SESSION INITIALIZED")

            timeout_triggered = False

            try:
                with anyio.fail_after(1):
                    await session.call_tool(
                        "process_documents",
                        {
                            "document_ids": [
                                "report.txt",
                                "report.txt",
                                "report.txt",
                                "report.txt",
                                "report.txt",
                            ]
                        },
                        progress_callback=progress_callback,
                    )

            except TimeoutError:
                timeout_triggered = True

                print(
                    "TIMEOUT TRIGGERED: "
                    "operation exceeded 1 second."
                )

            if not timeout_triggered:
                raise RuntimeError(
                    "Expected timeout did not occur."
                )

            if not progress_events:
                raise RuntimeError(
                    "Timeout test received no progress events."
                )

            print(
                "TIMEOUT TRIGGERED TEST: PASS"
            )


async def main():
    await test_normal_completion()

    await test_cancellation()

    await test_timeout_success()

    await test_timeout_triggered()

    print("\n========================================")
    print("LEVEL 8.8 TIMEOUT TEST SUITE: PASS")
    print("========================================")


if __name__ == "__main__":
    asyncio.run(main())