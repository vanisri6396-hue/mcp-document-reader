import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ============================================================
# MCP SERVER CONFIGURATION
# ============================================================

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)


# ============================================================
# MCP → INTERNAL TOOL FORMAT
# ============================================================

def extract_mcp_tools(tools):
    """
    Convert MCP tool objects into a simple internal format.

    This separates the MCP SDK representation from
    the AI/LLM layer.
    """

    extracted_tools = []

    for tool in tools:

        extracted_tools.append(
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.input_schema,
            }
        )

    return extracted_tools


# ============================================================
# INTERNAL FORMAT → LLM TOOL FORMAT
# ============================================================

def convert_to_llm_tools(mcp_tools):
    """
    Convert MCP tool definitions into a generic
    function-calling format understood by many LLM APIs.
    """

    llm_tools = []

    for tool in mcp_tools:

        llm_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
        )

    return llm_tools


# ============================================================
# DISPLAY MCP TOOLS
# ============================================================

def display_mcp_tools(mcp_tools):

    print("\n" + "=" * 70)
    print("MCP TOOL DEFINITIONS")
    print("=" * 70)

    for index, tool in enumerate(
        mcp_tools,
        start=1,
    ):

        print(f"\n[{index}] {tool['name']}")
        print("-" * 70)

        print(
            f"Description:\n"
            f"{tool['description']}"
        )

        print("\nInput Schema:")

        print(
            json.dumps(
                tool["input_schema"],
                indent=2,
            )
        )


# ============================================================
# DISPLAY LLM TOOLS
# ============================================================

def display_llm_tools(llm_tools):

    print("\n" + "=" * 70)
    print("LLM-FRIENDLY TOOL DEFINITIONS")
    print("=" * 70)

    print(
        json.dumps(
            llm_tools,
            indent=2,
        )
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    async with stdio_client(
        server_params
    ) as (read, write):

        async with ClientSession(
            read,
            write,
        ) as session:

            # ------------------------------------------------
            # INITIALIZE MCP SESSION
            # ------------------------------------------------

            await session.initialize()

            print("\n" + "=" * 70)
            print("LEVEL 7.3 — MCP → LLM TOOL PIPELINE")
            print("=" * 70)

            print("\nConnected to MCP server.")

            # ------------------------------------------------
            # DISCOVER MCP TOOLS
            # ------------------------------------------------

            tools_result = await session.list_tools()

            tools = tools_result.tools

            print(
                f"\nMCP server exposed "
                f"{len(tools)} tools."
            )

            # ------------------------------------------------
            # EXTRACT MCP TOOLS
            # ------------------------------------------------

            mcp_tools = extract_mcp_tools(
                tools
            )

            # ------------------------------------------------
            # DISPLAY MCP TOOLS
            # ------------------------------------------------

            display_mcp_tools(
                mcp_tools
            )

            # ------------------------------------------------
            # CONVERT MCP → LLM
            # ------------------------------------------------

            llm_tools = convert_to_llm_tools(
                mcp_tools
            )

            # ------------------------------------------------
            # DISPLAY LLM FORMAT
            # ------------------------------------------------

            display_llm_tools(
                llm_tools
            )

            # ------------------------------------------------
            # FINAL STATUS
            # ------------------------------------------------

            print("\n" + "=" * 70)
            print("LEVEL 7.3 COMPLETE")
            print("=" * 70)

            print(
                "\nMCP tools successfully discovered."
            )

            print(
                "MCP schemas successfully extracted."
            )

            print(
                "MCP tools successfully converted "
                "to LLM function-tool format."
            )

            print(
                "\nReady for Level 7.4 — Connect the LLM."
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())