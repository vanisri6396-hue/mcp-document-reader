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

            # --------------------------------------------------
            # 1. CONNECT TO MCP SERVER
            # --------------------------------------------------

            await session.initialize()

            print("\n" + "=" * 70)
            print("LEVEL 7.6 + 7.7 — MCP TOOL EXECUTION + RESULT → LLM")
            print("=" * 70)

            print("\nConnected to MCP server.")

            # --------------------------------------------------
            # 2. DISCOVER MCP TOOLS
            # --------------------------------------------------

            tools_result = await session.list_tools()
            tools = tools_result.tools

            print(f"MCP server exposed {len(tools)} tools.")

            # MCP → LLM tool format
            mcp_tools = extract_mcp_tools(tools)
            llm_tools = convert_to_llm_tools(mcp_tools)

            # --------------------------------------------------
            # 3. CREATE LLM CLIENT
            # --------------------------------------------------

            llm = GroqClient()

            user_message = "Read my report.txt document."

            print("\n" + "=" * 70)
            print("USER REQUEST")
            print("=" * 70)

            print(user_message)

            # --------------------------------------------------
            # 4. FIRST LLM REQUEST
            # --------------------------------------------------

            response = llm.ask_with_tools(
                user_message,
                llm_tools,
            )

            message = response.choices[0].message

            # --------------------------------------------------
            # 5. CHECK FOR TOOL CALL
            # --------------------------------------------------

            if not message.tool_calls:

                print("\nLLM did not request a tool.")

                if message.content:
                    print("\nLLM response:")
                    print(message.content)

                return

            print("\n" + "=" * 70)
            print("7.5 — LLM TOOL CALL")
            print("=" * 70)

            tool_call = message.tool_calls[0]

            tool_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            print(f"\nTool requested: {tool_name}")

            print("\nArguments:")
            print(json.dumps(arguments, indent=2))

            # --------------------------------------------------
            # 6. LEVEL 7.6 — EXECUTE MCP TOOL
            # --------------------------------------------------

            print("\n" + "=" * 70)
            print("7.6 — EXECUTING MCP TOOL")
            print("=" * 70)

            print(f"\nCalling MCP tool: {tool_name}")

            tool_result = await session.call_tool(
                tool_name,
                arguments,
            )

            print("\nMCP tool executed successfully.")

            # --------------------------------------------------
            # 7. EXTRACT TOOL RESULT
            # --------------------------------------------------

            result_parts = []

            for content in tool_result.content:

                if hasattr(content, "text"):
                    result_parts.append(content.text)

            tool_output = "\n".join(result_parts)

            print("\nMCP TOOL RESULT:")
            print("-" * 70)
            print(tool_output)

            # --------------------------------------------------
            # 8. LEVEL 7.7 — SEND RESULT BACK TO LLM
            # --------------------------------------------------

            print("\n" + "=" * 70)
            print("7.7 — SENDING TOOL RESULT BACK TO LLM")
            print("=" * 70)

            messages = [
                {
                    "role": "user",
                    "content": user_message,
                },
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                },
            ]

            final_response = llm.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages,
            )

            final_message = final_response.choices[0].message

            # --------------------------------------------------
            # 9. FINAL LLM ANSWER
            # --------------------------------------------------

            print("\n" + "=" * 70)
            print("FINAL LLM RESPONSE")
            print("=" * 70)

            print("\n" + (final_message.content or ""))

            # --------------------------------------------------
            # 10. COMPLETE
            # --------------------------------------------------

            print("\n" + "=" * 70)
            print("LEVEL 7.6 + 7.7 COMPLETE")
            print("=" * 70)

            print("\nFlow completed:")
            print("User request")
            print("    ↓")
            print("LLM selected MCP tool")
            print("    ↓")
            print("AI Client executed MCP tool")
            print("    ↓")
            print("MCP returned tool result")
            print("    ↓")
            print("Result sent back to LLM")
            print("    ↓")
            print("LLM generated final answer")


if __name__ == "__main__":
    asyncio.run(main())