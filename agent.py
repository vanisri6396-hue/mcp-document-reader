import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from llm.groq_client import GroqClient
from ai_client import extract_mcp_tools, convert_to_llm_tools
from context.manager import ContextManager

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)


async def run_agent(user_message: str):

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # --------------------------------------------------
            # 1. CONNECT TO MCP SERVER
            # --------------------------------------------------

            await session.initialize()

            print("\nConnected to MCP server.")

            # --------------------------------------------------
            # 2. DISCOVER MCP TOOLS
            # --------------------------------------------------

            tools_result = await session.list_tools()
            tools = tools_result.tools

            print(f"Discovered {len(tools)} MCP tools.")

            mcp_tools = extract_mcp_tools(tools)
            llm_tools = convert_to_llm_tools(mcp_tools)

            # --------------------------------------------------
            # 3. CREATE LLM CLIENT
            # --------------------------------------------------

            llm = GroqClient()

            # --------------------------------------------------
            # 4. INITIAL MESSAGE
            # --------------------------------------------------

            context_manager = ContextManager(max_messages=20)
            context_manager.add_message(
                {
                    "role": "user",
                    "content": user_message,
                }
            )

            # --------------------------------------------------
            # 5. AGENT LOOP
            # --------------------------------------------------

            max_iterations = 5

            for iteration in range(1, max_iterations + 1):
                print(
                    f"\nContext messages: "
                    f"{context_manager.message_count()}"
                )

                print("\n" + "=" * 70)
                print(f"AGENT ITERATION {iteration}")
                print("=" * 70)

                # Ask LLM
                response = llm.client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=context_manager.get_messages(),
                    tools=llm_tools,
                    tool_choice="auto",
                )

                message = response.choices[0].message

                # --------------------------------------------------
                # 6. CHECK WHETHER LLM WANTS A TOOL
                # --------------------------------------------------

                if not message.tool_calls:

                    print("\nLLM produced final answer.")

                    print("\n" + "=" * 70)
                    print("FINAL ANSWER")
                    print("=" * 70)

                    print("\n" + (message.content or ""))

                    return

                # --------------------------------------------------
                # 7. ADD ASSISTANT TOOL-CALL MESSAGE
                # --------------------------------------------------

                assistant_tool_calls = []

                for tool_call in message.tool_calls:

                    assistant_tool_calls.append(
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    )

                context_manager.add_and_trim(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": assistant_tool_calls,
                    }
                )

                # --------------------------------------------------
                # 8. EXECUTE EVERY REQUESTED TOOL
                # --------------------------------------------------

                for tool_call in message.tool_calls:

                    tool_name = tool_call.function.name

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    print("\nLLM requested tool:")
                    print(f"  {tool_name}")

                    print("\nArguments:")
                    print(json.dumps(arguments, indent=2))

                    print("\nExecuting MCP tool...")

                    tool_result = await session.call_tool(
                        tool_name,
                        arguments,
                    )

                    # --------------------------------------------------
                    # 9. EXTRACT TOOL RESULT
                    # --------------------------------------------------

                    result_parts = []

                    for content in tool_result.content:

                        if hasattr(content, "text"):
                            result_parts.append(content.text)

                    tool_output = "\n".join(result_parts)

                    print("\nMCP tool result:")
                    print("-" * 70)
                    print(tool_output)

                    # --------------------------------------------------
                    # 10. SEND RESULT BACK TO LLM
                    # --------------------------------------------------

                    context_manager.add_and_trim(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_output,
                        }
                    )

            # --------------------------------------------------
            # 11. SAFETY LIMIT
            # --------------------------------------------------

            print("\n" + "=" * 70)
            print("AGENT STOPPED")
            print("=" * 70)

            print(
                f"\nMaximum of {max_iterations} iterations reached."
            )


async def main():

    print("\n" + "=" * 70)
    print("LEVEL 7.8 — MULTI-STEP MCP AGENT")
    print("=" * 70)

    user_message = (
        "Search my documents for the word MCP. "
        "Then read the matching document and explain what it says."
    )

    print("\nUSER REQUEST:")
    print(user_message)

    await run_agent(user_message)


if __name__ == "__main__":
    asyncio.run(main())