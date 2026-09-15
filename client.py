import asyncio

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
# HELPER — PRINT TOOL RESULT
# ============================================================

def print_tool_result(result):
    print("\nTool Result")
    print("-" * 60)

    if result.is_error:
        print("Tool returned an error.")
        print(result)
        return

    for content in result.content:

        if hasattr(content, "text"):
            print(content.text)

        else:
            print(content)


# ============================================================
# HELPER — PRINT STRUCTURED OUTPUT
# ============================================================

def print_structured_output(result):
    print("\nStructured Content")
    print("-" * 60)

    if result.structured_content:
        print(result.structured_content)

    else:
        print("No structured content returned.")


# ============================================================
# HELPER — PRINT RESOURCE RESULT
# ============================================================

def print_resource_result(result):
    print("\nResource Result")
    print("-" * 60)

    for content in result.contents:
        print(content)


# ============================================================
# MAIN CLIENT
# ============================================================

async def main():

    # --------------------------------------------------------
    # CONNECT TO MCP SERVER USING STDIO
    # --------------------------------------------------------

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # ------------------------------------------------
            # INITIALIZE MCP SESSION
            # ------------------------------------------------

            await session.initialize()

            print("\nConnected to MCP server!")
            print("=" * 70)


            # =================================================
            # 1. LIST AVAILABLE TOOLS
            # =================================================

            print("\n[1] AVAILABLE TOOLS")
            print("-" * 70)

            tools_result = await session.list_tools()

            if tools_result.tools:

                for tool in tools_result.tools:

                    print(f"\nName: {tool.name}")

                    print(
                        f"Description: "
                        f"{tool.description}"
                    )

                    # MCP SDK v2 uses input_schema
                    if tool.input_schema:

                        print("Input Schema:")
                        print(tool.input_schema)

            else:

                print("No tools found.")


            # =================================================
            # 2. CALL create_document
            # =================================================

            print("\n\n[2] CALLING create_document")
            print("-" * 70)

            result = await session.call_tool(
                "create_document",
                {
                    "name": "test.txt",
                    "content": (
                        "This document was created "
                        "through the MCP client."
                    )
                }
            )

            print_tool_result(result)
            print_structured_output(result)


            # =================================================
            # 3. CALL read_document
            # =================================================

            print("\n\n[3] CALLING read_document")
            print("-" * 70)

            result = await session.call_tool(
                "read_document",
                {
                    "doc_id": "test.txt",
                    "max_chars": 5000
                }
            )

            print_tool_result(result)


            # =================================================
            # 4. CALL update_document
            # =================================================

            print("\n\n[4] CALLING update_document")
            print("-" * 70)

            result = await session.call_tool(
                "update_document",
                {
                    "name": "test.txt",
                    "content": (
                        "This document has been "
                        "updated through the MCP client."
                    )
                }
            )

            print_tool_result(result)
            print_structured_output(result)


            # =================================================
            # 5. READ UPDATED DOCUMENT
            # =================================================

            print("\n\n[5] READING UPDATED DOCUMENT")
            print("-" * 70)

            result = await session.call_tool(
                "read_document",
                {
                    "doc_id": "test.txt",
                    "max_chars": 5000
                }
            )

            print_tool_result(result)


            # =================================================
            # 6. LIST DOCUMENTS — PAGE 1
            # =================================================

            print("\n\n[6] LIST DOCUMENTS — PAGE 1")
            print("-" * 70)

            result = await session.call_tool(
                "list_documents",
                {
                    "page": 1,
                    "page_size": 10
                }
            )

            print_tool_result(result)
            print_structured_output(result)


            # =================================================
            # 7. LIST DOCUMENTS — PAGE 2
            # =================================================

            print("\n\n[7] LIST DOCUMENTS — PAGE 2")
            print("-" * 70)

            result = await session.call_tool(
                "list_documents",
                {
                    "page": 2,
                    "page_size": 10
                }
            )

            print_tool_result(result)
            print_structured_output(result)


            # =================================================
            # 8. SEARCH DOCUMENTS
            # =================================================

            print("\n\n[8] CALLING search_documents")
            print("-" * 70)

            result = await session.call_tool(
                "search_documents",
                {
                    "query": "MCP",
                    "case_sensitive": False
                }
            )

            print_tool_result(result)
            print_structured_output(result)


            # =================================================
            # 9. LIST FIXED RESOURCES
            # =================================================

            print("\n\n[9] AVAILABLE RESOURCES")
            print("-" * 70)

            resources_result = await session.list_resources()

            if resources_result.resources:

                for resource in resources_result.resources:

                    print(
                        f"\nURI: "
                        f"{resource.uri}"
                    )

                    print(
                        f"Name: "
                        f"{resource.name}"
                    )

                    print(
                        f"Description: "
                        f"{resource.description}"
                    )

            else:

                print("No fixed resources found.")


            # =================================================
            # 10. LIST RESOURCE TEMPLATES
            # =================================================

            print("\n\n[10] RESOURCE TEMPLATES")
            print("-" * 70)

            templates_result = (
                await session.list_resource_templates()
            )

            if templates_result.resource_templates:

                for template in (
                    templates_result.resource_templates
                ):

                    print(
                        f"\nURI Template: "
                        f"{template.uri_template}"
                    )

                    print(
                        f"Name: "
                        f"{template.name}"
                    )

                    print(
                        f"Description: "
                        f"{template.description}"
                    )

            else:

                print(
                    "No resource templates found."
                )


            # =================================================
            # 11. READ DOCUMENT RESOURCE
            # =================================================

            print("\n\n[11] READING DOCUMENT RESOURCE")
            print("-" * 70)

            resource_result = await session.read_resource(
                "document://test.txt"
            )

            print_resource_result(
                resource_result
            )


            # =================================================
            # 12. LIST AVAILABLE PROMPTS
            # =================================================

            print("\n\n[12] AVAILABLE PROMPTS")
            print("-" * 70)

            prompts_result = await session.list_prompts()

            if prompts_result.prompts:

                for prompt in prompts_result.prompts:

                    print(
                        f"\nName: "
                        f"{prompt.name}"
                    )

                    print(
                        f"Description: "
                        f"{prompt.description}"
                    )

            else:

                print("No prompts found.")


            # =================================================
            # 13. GET PROMPT
            # =================================================

            print("\n\n[13] GETTING PROMPT")
            print("-" * 70)

            prompt_result = await session.get_prompt(
                "summarize_document",
                {
                    "doc_id": "test.txt"
                }
            )

            print("\nPrompt Result")
            print("-" * 60)

            for message in prompt_result.messages:

                print(
                    f"\nRole: "
                    f"{message.role}"
                )

                print(
                    f"Content: "
                    f"{message.content}"
                )


            # =================================================
            # 14. DELETE DOCUMENT
            # =================================================

            print("\n\n[14] CALLING delete_document")
            print("-" * 70)

            result = await session.call_tool(
                "delete_document",
                {
                    "doc_id": "test.txt"
                }
            )

            print_tool_result(result)
            print_structured_output(result)


            # =================================================
            # 15. VERIFY DELETION
            # =================================================

            print("\n\n[15] VERIFYING DELETION")
            print("-" * 70)

            result = await session.call_tool(
                "read_document",
                {
                    "doc_id": "test.txt"
                }
            )

            if result.is_error:

                print(
                    "Expected error: "
                    "document no longer exists."
                )

                print(
                    "Delete verification PASSED."
                )

            else:

                print(
                    "ERROR: Deleted document "
                    "can still be read."
                )


            # =================================================
            # COMPLETION MESSAGE
            # =================================================

            print("\n\n" + "=" * 70)

            print(
                "LEVEL 5 V4 MCP CLIENT TEST "
                "COMPLETED SUCCESSFULLY"
            )

            print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())