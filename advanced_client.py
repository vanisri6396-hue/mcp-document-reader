import asyncio
from dataclasses import dataclass
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ============================================================
# MCP SERVER CONFIGURATION
# ============================================================

SERVER_PARAMS = StdioServerParameters(
    command="python",
    args=["server.py"],
)


# ============================================================
# CLIENT ERROR
# ============================================================


class MCPClientError(Exception):
    """Base error for the advanced MCP client."""


class ToolNotFoundError(MCPClientError):
    """Raised when a requested tool does not exist."""


class ToolExecutionError(MCPClientError):
    """Raised when an MCP tool returns an error."""


class ToolTimeoutError(MCPClientError):
    """Raised when a tool exceeds its timeout."""


# ============================================================
# TOOL INFORMATION
# ============================================================


@dataclass(frozen=True)
class ToolInfo:
    name: str
    description: str
    input_schema: dict[str, Any]


# ============================================================
# ADVANCED MCP CLIENT
# ============================================================


class AdvancedMCPClient:
    """
    Advanced MCP client orchestration layer.

    Responsibilities:

    1. MCP session management
    2. Tool discovery
    3. Tool registry
    4. Tool routing
    5. Tool existence validation
    6. Timeout management
    7. Error normalization
    8. Context-aware execution
    """

    def __init__(
        self,
        session: ClientSession,
        default_timeout: float = 10.0,
    ) -> None:

        if default_timeout <= 0:
            raise ValueError(
                "default_timeout must be greater than zero."
            )

        self.session = session
        self.default_timeout = default_timeout

        # Local client-side tool registry.
        self._tools: dict[str, ToolInfo] = {}

        # Tracks whether discovery has happened.
        self._discovered = False

        # Lightweight execution history.
        self._execution_history: list[dict[str, Any]] = []

    # ========================================================
    # DISCOVERY
    # ========================================================

    async def discover_tools(self) -> dict[str, ToolInfo]:
        """
        Discover all tools exposed by the MCP server.

        The server remains the source of truth.
        The client caches the discovered metadata locally.
        """

        result = await self.session.list_tools()

        discovered_tools: dict[str, ToolInfo] = {}

        for tool in result.tools:

            name = str(tool.name)

            description = (
                str(tool.description)
                if tool.description
                else ""
            )

            input_schema = (
                tool.input_schema
                if isinstance(tool.input_schema, dict)
                else {}
            )

            discovered_tools[name] = ToolInfo(
                name=name,
                description=description,
                input_schema=input_schema,
            )

        self._tools = discovered_tools
        self._discovered = True

        return self.get_tool_registry()

    # ========================================================
    # REGISTRY
    # ========================================================

    def get_tool_registry(self) -> dict[str, ToolInfo]:
        """
        Return a copy of the current client-side tool registry.
        """

        return dict(self._tools)

    # ========================================================
    # DISCOVERY STATE
    # ========================================================

    @property
    def discovered(self) -> bool:
        return self._discovered

    # ========================================================
    # TOOL LOOKUP
    # ========================================================

    def has_tool(self, tool_name: str) -> bool:

        if not isinstance(tool_name, str):
            return False

        return tool_name.strip() in self._tools

    def get_tool(self, tool_name: str) -> ToolInfo:

        if not isinstance(tool_name, str):
            raise ToolNotFoundError(
                "Tool name must be text."
            )

        tool_name = tool_name.strip()

        if not tool_name:
            raise ToolNotFoundError(
                "Tool name cannot be empty."
            )

        tool = self._tools.get(tool_name)

        if tool is None:
            raise ToolNotFoundError(
                f"Unknown MCP tool: {tool_name}"
            )

        return tool

    # ========================================================
    # ROUTING
    # ========================================================

    def route_tool(
        self,
        tool_name: str,
    ) -> ToolInfo:
        """
        Route a requested operation to a discovered MCP tool.

        In a multi-server system this method can later become
        server-aware routing logic.
        """

        if not self._discovered:
            raise MCPClientError(
                "Tool discovery has not been performed."
            )

        return self.get_tool(tool_name)

    # ========================================================
    # ARGUMENT VALIDATION
    # ========================================================

    def validate_arguments(
        self,
        arguments: dict[str, Any] | None,
    ) -> dict[str, Any]:

        if arguments is None:
            return {}

        if not isinstance(arguments, dict):
            raise ValueError(
                "Tool arguments must be a dictionary."
            )

        return dict(arguments)

    # ========================================================
    # EXECUTION
    # ========================================================

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """
        Execute an MCP tool through the orchestration layer.
        """

        tool = self.route_tool(tool_name)

        validated_arguments = self.validate_arguments(
            arguments
        )

        effective_timeout = (
            self.default_timeout
            if timeout is None
            else timeout
        )

        if effective_timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

        start_time = asyncio.get_running_loop().time()

        try:

            result = await asyncio.wait_for(
                self.session.call_tool(
                    tool.name,
                    validated_arguments,
                ),
                timeout=effective_timeout,
            )

        except asyncio.TimeoutError as error:

            elapsed = (
                asyncio.get_running_loop().time()
                - start_time
            )

            self._record_execution(
                tool_name=tool_name,
                success=False,
                elapsed=elapsed,
                error_type="timeout",
            )

            raise ToolTimeoutError(
                f"Tool '{tool_name}' exceeded "
                f"the {effective_timeout} second timeout."
            ) from error

        except asyncio.CancelledError:

            elapsed = (
                asyncio.get_running_loop().time()
                - start_time
            )

            self._record_execution(
                tool_name=tool_name,
                success=False,
                elapsed=elapsed,
                error_type="cancelled",
            )

            raise

        except Exception as error:

            elapsed = (
                asyncio.get_running_loop().time()
                - start_time
            )

            self._record_execution(
                tool_name=tool_name,
                success=False,
                elapsed=elapsed,
                error_type=type(error).__name__,
            )

            raise ToolExecutionError(
                f"Tool '{tool_name}' execution failed."
            ) from error

        elapsed = (
            asyncio.get_running_loop().time()
            - start_time
        )

        if getattr(result, "is_error", False):

            self._record_execution(
                tool_name=tool_name,
                success=False,
                elapsed=elapsed,
                error_type="mcp_tool_error",
            )

            raise ToolExecutionError(
                self._extract_error_message(result)
            )

        self._record_execution(
            tool_name=tool_name,
            success=True,
            elapsed=elapsed,
            error_type=None,
        )

        return result

    # ========================================================
    # ERROR MESSAGE EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_error_message(result: Any) -> str:

        content = getattr(
            result,
            "content",
            None,
        )

        if content:

            for item in content:

                text = getattr(
                    item,
                    "text",
                    None,
                )

                if text:
                    return str(text)

        return "MCP tool execution failed."

    # ========================================================
    # EXECUTION HISTORY
    # ========================================================

    def _record_execution(
        self,
        tool_name: str,
        success: bool,
        elapsed: float,
        error_type: str | None,
    ) -> None:

        self._execution_history.append(
            {
                "tool": tool_name,
                "success": success,
                "elapsed_seconds": elapsed,
                "error_type": error_type,
            }
        )

    def get_execution_history(
        self,
    ) -> list[dict[str, Any]]:

        return [
            entry.copy()
            for entry in self._execution_history
        ]

    # ========================================================
    # CONTEXT SUMMARY
    # ========================================================

    def get_client_context(self) -> dict[str, Any]:
        """
        Return a compact context object that an AI agent can use
        when deciding which tool to call.
        """

        tools = []

        for tool in self._tools.values():

            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
            )

        return {
            "discovered": self._discovered,
            "tool_count": len(self._tools),
            "tools": tools,
        }


# ============================================================
# DEMONSTRATION CLIENT
# ============================================================


async def main() -> None:

    print("=" * 70)
    print("LEVEL 8.10 — ADVANCED MCP CLIENT")
    print("=" * 70)

    async with stdio_client(
        SERVER_PARAMS
    ) as (read, write):

        async with ClientSession(
            read,
            write,
        ) as session:

            await session.initialize()

            print("\nMCP SESSION INITIALIZED")

            client = AdvancedMCPClient(
                session=session,
                default_timeout=10.0,
            )

            # ------------------------------------------------
            # DISCOVERY
            # ------------------------------------------------

            print("\n[1] TOOL DISCOVERY")
            print("-" * 70)

            registry = await client.discover_tools()

            for tool_name, tool_info in registry.items():

                print(
                    f"{tool_name}: "
                    f"{tool_info.description}"
                )

            print(
                f"\nDiscovered {len(registry)} tools."
            )

            # ------------------------------------------------
            # CLIENT CONTEXT
            # ------------------------------------------------

            print("\n[2] CLIENT CONTEXT")
            print("-" * 70)

            context = client.get_client_context()

            print(
                f"Discovered: "
                f"{context['discovered']}"
            )

            print(
                f"Tool count: "
                f"{context['tool_count']}"
            )

            # ------------------------------------------------
            # ROUTING
            # ------------------------------------------------

            print("\n[3] TOOL ROUTING")
            print("-" * 70)

            routed_tool = client.route_tool(
                "read_document"
            )

            print(
                f"Routed to: "
                f"{routed_tool.name}"
            )

            # ------------------------------------------------
            # TOOL EXECUTION
            # ------------------------------------------------

            print("\n[4] TOOL EXECUTION")
            print("-" * 70)

            result = await client.call_tool(
                "read_document",
                {
                    "doc_id": "report.txt",
                    "max_chars": 5000,
                },
            )

            print("Tool execution successful.")

            if result.structured_content:

                print(
                    "Structured output:"
                )

                print(
                    result.structured_content
                )

            # ------------------------------------------------
            # EXECUTION HISTORY
            # ------------------------------------------------

            print("\n[5] EXECUTION HISTORY")
            print("-" * 70)

            for entry in (
                client.get_execution_history()
            ):

                print(entry)

    print("\n" + "=" * 70)
    print("LEVEL 8.10 CLIENT DEMONSTRATION COMPLETED")
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(main())