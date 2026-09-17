import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llm.groq_client import GroqClient
from ai_client import extract_mcp_tools, convert_to_llm_tools


server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)


async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Connect to MCP server
            await session.initialize()

            print("\n" + "=" * 70)
            print("LEVEL 7.5 — LLM TOOL CALLING")
            print("=" * 70)

            print("\nConnected to MCP server.")

            # Discover MCP tools
            tools_result = await session.list_tools()
            tools = tools_result.tools

            print(f"MCP server exposed {len(tools)} tools.")

            # Convert MCP tools → LLM tools
            mcp_tools = extract_mcp_tools(tools)
            llm_tools = convert_to_llm_tools(mcp_tools)

            print("\nSending MCP tools to the LLM...")

            # Connect to LLM
            llm = GroqClient()

            user_message = "Read my report.txt document."

            print(f"\nUser request:")
            print(user_message)

            # Ask LLM with MCP tools available
            response = llm.ask_with_tools(
                user_message,
                llm_tools,
            )

            message = response.choices[0].message

            print("\n" + "=" * 70)
            print("LLM RESPONSE")
            print("=" * 70)

            print(f"\nText response:")
            print(message.content)

            # Check whether LLM requested a tool
            if message.tool_calls:

                print("\n" + "=" * 70)
                print("TOOL CALL REQUESTED")
                print("=" * 70)

                for tool_call in message.tool_calls:

                    print(f"\nTool name:")
                    print(tool_call.function.name)

                    print("\nArguments:")

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    print(json.dumps(arguments, indent=2))

            else:

                print("\nNo tool call was requested.")

            print("\n" + "=" * 70)
            print("LEVEL 7.5 TEST COMPLETE")
            print("=" * 70)

            print("\nIMPORTANT:")
            print("The LLM requested the tool.")
            print("The MCP tool has NOT been executed yet.")
            print("Execution will be implemented in Level 7.6.")


if __name__ == "__main__":
    asyncio.run(main())