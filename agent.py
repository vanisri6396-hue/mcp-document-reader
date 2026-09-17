import asyncio
import json
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from context.manager import ContextManager
from llm.groq_client import GroqClient

from security.ai_safety import (
    inspect_tool_call,
    enforce_tool_safety,
    UnsafeToolCallError,
)

from security.output_validation import (
    validate_final_answer,
    UnsafeOutputError,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

server_params = StdioServerParameters(
    command="python",
    args=["server.py"],
)

MAX_ITERATIONS = 5
MAX_TOTAL_TOOL_CALLS = 10


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("DocumentMCP.Agent")


# ---------------------------------------------------------------------------
# Context display
# ---------------------------------------------------------------------------

def print_context_status(
    context: ContextManager,
) -> None:

    stats = context.get_stats()

    print("\n" + "-" * 70)
    print("CONTEXT STATUS")
    print("-" * 70)

    print(
        f"Messages: {stats.message_count}"
    )

    print(
        f"Estimated tokens: {stats.estimated_tokens}"
    )

    print(
        f"Maximum context tokens: "
        f"{stats.max_context_tokens}"
    )

    print(
        f"Remaining tokens: "
        f"{stats.remaining_tokens}"
    )

    print(
        f"Maximum messages: "
        f"{stats.max_messages}"
    )

    print(
        f"Truncated tool results: "
        f"{stats.truncated_tool_results}"
    )


# ---------------------------------------------------------------------------
# MCP result extraction
# ---------------------------------------------------------------------------

def extract_tool_result(result) -> str:

    if hasattr(result, "content"):

        parts = []

        for item in result.content:

            if hasattr(item, "text"):
                parts.append(item.text)

            else:
                parts.append(str(item))

        return "\n".join(parts)

    return str(result)


# ---------------------------------------------------------------------------
# Destructive confirmation
# ---------------------------------------------------------------------------

def ask_for_confirmation(
    tool_name: str,
    arguments: dict,
) -> bool:

    print("\n" + "!" * 70)
    print("CONFIRMATION REQUIRED")
    print("!" * 70)

    print(
        "\nThe AI requested a potentially destructive operation."
    )

    print(
        f"\nTool: {tool_name}"
    )

    print(
        "\nArguments:"
    )

    print(
        json.dumps(
            arguments,
            indent=2,
        )
    )

    print(
        "\nThis operation may permanently modify or delete data."
    )

    response = input(
        "\nDo you explicitly approve this operation? "
        "[yes/no]: "
    ).strip().lower()

    return response in {
        "yes",
        "y",
    }


# ---------------------------------------------------------------------------
# Main agent
# ---------------------------------------------------------------------------

async def main():

    print("\n" + "=" * 70)
    print("LEVEL 7.10 — AI SAFETY + MCP AGENT")
    print("=" * 70)

    user_request = (
        "Search my documents for the word MCP. "
        "Then read the matching document and explain what it says."
    )

    print("\nUSER REQUEST:")
    print(user_request)

    # -----------------------------------------------------------------------
    # Context manager
    # -----------------------------------------------------------------------

    context = ContextManager(
        max_messages=20,
        max_context_tokens=6000,
        max_tool_result_chars=8000,
        response_token_reserve=1000,
    )

    # Grounding instruction
    context.add_message(
        {
            "role": "system",
            "content": (
                "You are a document assistant. "
                "Use MCP tools when necessary. "
                "When answering about document contents, "
                "base your answer on the tool results provided "
                "in this conversation. "
                "Do not invent facts that are not supported by "
                "the retrieved document. "
                "If information is not present in the document, "
                "say that it is not stated."
            ),
        }
    )

    context.add_message(
        {
            "role": "user",
            "content": user_request,
        }
    )

    llm = GroqClient()

    total_tool_calls = 0

    async with stdio_client(
        server_params
    ) as (read, write):

        async with ClientSession(
            read,
            write,
        ) as session:

            await session.initialize()

            print(
                "\nConnected to MCP server."
            )

            # ----------------------------------------------------------------
            # Tool discovery
            # ----------------------------------------------------------------

            tools_result = await session.list_tools()

            tools = tools_result.tools

            print(
                f"Discovered {len(tools)} MCP tools."
            )

            llm_tools = []

            for tool in tools:

                llm_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": (
                                tool.description or ""
                            ),
                            "parameters": (
                                tool.input_schema
                            ),
                        },
                    }
                )

            print_context_status(
                context
            )

            # ================================================================
            # AGENT LOOP
            # ================================================================

            for iteration in range(
                1,
                MAX_ITERATIONS + 1,
            ):

                print("\n" + "=" * 70)

                print(
                    f"AGENT ITERATION {iteration}"
                )

                print("=" * 70)

                # ------------------------------------------------------------
                # Global loop safety
                # ------------------------------------------------------------

                if total_tool_calls >= MAX_TOTAL_TOOL_CALLS:

                    print(
                        "\nAgent stopped: maximum total "
                        "tool-call limit reached."
                    )

                    return

                messages = context.get_messages()

                try:

                    response = (
                        llm.client.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=messages,
                            tools=llm_tools,
                            tool_choice="auto",
                        )
                    )

                except Exception as error:

                    print(
                        "\nLLM ERROR"
                    )

                    print(
                        "The language model request failed safely."
                    )

                    logger.error(
                        "LLM request failed: %s",
                        type(error).__name__,
                    )

                    return

                assistant_message = (
                    response.choices[0].message
                )

                # ------------------------------------------------------------
                # Final response
                # ------------------------------------------------------------

                if not assistant_message.tool_calls:

                    raw_answer = (
                        assistant_message.content
                        or ""
                    )

                    try:

                        final_answer = (
                            validate_final_answer(
                                raw_answer
                            )
                        )

                    except UnsafeOutputError as error:

                        print(
                            "\nOUTPUT SAFETY CHECK"
                        )

                        print(
                            "-" * 70
                        )

                        print(
                            "Status: BLOCKED"
                        )

                        print(
                            f"Reason: {error}"
                        )

                        return

                    context.add_message(
                        {
                            "role": "assistant",
                            "content": final_answer,
                        }
                    )

                    print(
                        "\nLLM produced final answer."
                    )

                    print(
                        "\n" + "=" * 70
                    )

                    print(
                        "FINAL ANSWER"
                    )

                    print(
                        "=" * 70
                    )

                    print(
                        f"\n{final_answer}"
                    )

                    print_context_status(
                        context
                    )

                    print(
                        "\n" + "=" * 70
                    )

                    print(
                        "LEVEL 7.10 AI SAFETY"
                    )

                    print(
                        "=" * 70
                    )

                    print(
                        "\nPrompt-injection awareness : COMPLETE"
                    )

                    print(
                        "Tool-call validation       : COMPLETE"
                    )

                    print(
                        "Argument validation        : COMPLETE"
                    )

                    print(
                        "Dangerous-tool protection : COMPLETE"
                    )

                    print(
                        "Authorization enforcement : COMPLETE"
                    )

                    print(
                        "Malicious-content handling: COMPLETE"
                    )

                    print(
                        "LLM output validation     : COMPLETE"
                    )

                    print(
                        "Agent loop limits         : COMPLETE"
                    )

                    print(
                        "Safe error handling       : COMPLETE"
                    )

                    print(
                        "AI safety testing         : COMPLETE"
                    )

                    return

                # ------------------------------------------------------------
                # Add assistant tool request to context
                # ------------------------------------------------------------

                assistant_tool_calls = []

                for tool_call in (
                    assistant_message.tool_calls
                ):

                    assistant_tool_calls.append(
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": (
                                    tool_call.function.name
                                ),
                                "arguments": (
                                    tool_call.function.arguments
                                ),
                            },
                        }
                    )

                context.add_message(
                    {
                        "role": "assistant",
                        "content": (
                            assistant_message.content
                        ),
                        "tool_calls": (
                            assistant_tool_calls
                        ),
                    }
                )

                # ------------------------------------------------------------
                # Process tool calls
                # ------------------------------------------------------------

                for tool_call in (
                    assistant_message.tool_calls
                ):

                    total_tool_calls += 1

                    tool_name = (
                        tool_call.function.name
                    )

                    raw_arguments = (
                        tool_call.function.arguments
                    )

                    print(
                        "\nLLM requested tool:"
                    )

                    print(
                        f"  {tool_name}"
                    )

                    print(
                        "\nArguments:"
                    )

                    try:

                        arguments = json.loads(
                            raw_arguments
                        )

                        print(
                            json.dumps(
                                arguments,
                                indent=2,
                            )
                        )

                    except json.JSONDecodeError:

                        arguments = raw_arguments

                        print(
                            raw_arguments
                        )

                    # --------------------------------------------------------
                    # AI safety inspection
                    # --------------------------------------------------------

                    print(
                        "\nRunning AI safety inspection..."
                    )

                    decision = inspect_tool_call(
                        tool_name,
                        arguments,
                    )

                    print(
                        "\nAI SAFETY CHECK"
                    )

                    print(
                        "-" * 70
                    )

                    print(
                        f"Tool: {decision.tool_name}"
                    )

                    print(
                        f"Risk level: "
                        f"{decision.risk_level}"
                    )

                    print(
                        f"Status: "
                        f"{'ALLOWED' if decision.allowed else 'BLOCKED'}"
                    )

                    if not decision.allowed:

                        blocked_result = (
                            "Tool call blocked by AI safety: "
                            + decision.reason
                        )

                        print(
                            f"Reason: "
                            f"{decision.reason}"
                        )

                        context.add_message(
                            {
                                "role": "tool",
                                "tool_call_id": (
                                    tool_call.id
                                ),
                                "name": tool_name,
                                "content": blocked_result,
                            }
                        )

                        print_context_status(
                            context
                        )

                        continue

                    # --------------------------------------------------------
                    # Destructive confirmation
                    # --------------------------------------------------------

                    confirmed = False

                    if decision.requires_confirmation:

                        confirmed = ask_for_confirmation(
                            tool_name,
                            arguments,
                        )

                        if not confirmed:

                            print(
                                "\nOperation BLOCKED."
                            )

                            print(
                                "User did not provide "
                                "explicit confirmation."
                            )

                            blocked_result = (
                                "The requested destructive "
                                "operation was blocked because "
                                "the user did not provide "
                                "explicit confirmation."
                            )

                            context.add_message(
                                {
                                    "role": "tool",
                                    "tool_call_id": (
                                        tool_call.id
                                    ),
                                    "name": tool_name,
                                    "content": blocked_result,
                                }
                            )

                            print_context_status(
                                context
                            )

                            continue

                    # --------------------------------------------------------
                    # Final AI safety enforcement
                    # --------------------------------------------------------

                    try:

                        safe_arguments = (
                            enforce_tool_safety(
                                tool_name,
                                arguments,
                                confirmed=confirmed,
                            )
                        )

                    except UnsafeToolCallError as error:

                        print(
                            "\nAI SAFETY ENFORCEMENT"
                        )

                        print(
                            "-" * 70
                        )

                        print(
                            "Status: BLOCKED"
                        )

                        print(
                            f"Reason: {error}"
                        )

                        context.add_message(
                            {
                                "role": "tool",
                                "tool_call_id": (
                                    tool_call.id
                                ),
                                "name": tool_name,
                                "content": (
                                    "Tool call blocked by "
                                    "AI safety enforcement."
                                ),
                            }
                        )

                        print_context_status(
                            context
                        )

                        continue

                    # --------------------------------------------------------
                    # MCP execution
                    # --------------------------------------------------------

                    print(
                        "\nExecuting MCP tool..."
                    )

                    try:

                        result = await session.call_tool(
                            tool_name,
                            safe_arguments,
                        )

                        result_text = (
                            extract_tool_result(
                                result
                            )
                        )

                        print(
                            "\nMCP tool result:"
                        )

                        print(
                            "-" * 70
                        )

                        print(
                            result_text
                        )

                        optimized_result = (
                            context.optimize_tool_result(
                                result_text
                            )
                        )

                        context.add_message(
                            {
                                "role": "tool",
                                "tool_call_id": (
                                    tool_call.id
                                ),
                                "name": tool_name,
                                "content": (
                                    optimized_result
                                ),
                            }
                        )

                    except Exception as error:

                        # Never expose raw internal exceptions,
                        # file paths, credentials, or stack traces
                        # to the LLM/user.

                        safe_error = (
                            "The MCP tool execution failed "
                            "and was safely handled."
                        )

                        logger.error(
                            "MCP tool failed: %s",
                            type(error).__name__,
                        )

                        print(
                            "\nMCP EXECUTION ERROR"
                        )

                        print(
                            "-" * 70
                        )

                        print(
                            safe_error
                        )

                        context.add_message(
                            {
                                "role": "tool",
                                "tool_call_id": (
                                    tool_call.id
                                ),
                                "name": tool_name,
                                "content": safe_error,
                            }
                        )

                    print_context_status(
                        context
                    )

            # ----------------------------------------------------------------
            # Maximum iteration reached
            # ----------------------------------------------------------------

            print(
                "\n" + "=" * 70
            )

            print(
                "AGENT LOOP LIMIT"
            )

            print(
                "=" * 70
            )

            print(
                f"\nAgent stopped safely after "
                f"{MAX_ITERATIONS} iterations."
            )

            print(
                "No additional tool calls will be executed."
            )


if __name__ == "__main__":
    asyncio.run(main())