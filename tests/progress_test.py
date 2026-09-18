import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:

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
                    ],
                },
                progress_callback=progress_callback,
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
                    "No progress notifications were received."
                )

            print(
                "PROGRESS CALLBACK TEST SUCCESSFUL"
            )


if __name__ == "__main__":

    asyncio.run(
        main()
    )