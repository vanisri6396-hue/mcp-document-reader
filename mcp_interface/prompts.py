from mcp.server import MCPServer

from security.context import (
    secure_request,
)

from security.errors import (
    handle_tool_error,
)

from security.validation import (
    validate_document_name,
)


def register_prompts(
    mcp: MCPServer,
) -> None:

    @mcp.prompt()
    def summarize_document(
        doc_id: str,
        focus: str = "main ideas",
        style: str = "concise",
    ) -> str:
        """
        Generate a reusable prompt for summarizing a document.

        This demonstrates an MCP Prompt with arguments.

        Arguments:
            doc_id:
                The document filename to summarize.

            focus:
                What the LLM should concentrate on.

            style:
                How the final summary should be written.

        Example:

            summarize_document(
                "report.txt",
                "key technical concepts",
                "detailed"
            )
        """

        try:

            # ------------------------------------------------
            # 1. Security
            # ------------------------------------------------
            secure_request(
                "summarize_document"
            )

            # ------------------------------------------------
            # 2. Validate document identifier
            # ------------------------------------------------
            doc_id = validate_document_name(
                doc_id
            )

            # ------------------------------------------------
            # 3. Validate prompt arguments
            # ------------------------------------------------
            if not isinstance(focus, str):
                raise ValueError(
                    "Focus must be text."
                )

            if not isinstance(style, str):
                raise ValueError(
                    "Style must be text."
                )

            focus = focus.strip()
            style = style.strip()

            if not focus:
                raise ValueError(
                    "Focus cannot be empty."
                )

            if not style:
                raise ValueError(
                    "Style cannot be empty."
                )

            # Prevent excessively large prompt arguments.
            if len(focus) > 200:
                raise ValueError(
                    "Focus cannot exceed 200 characters."
                )

            if len(style) > 50:
                raise ValueError(
                    "Style cannot exceed 50 characters."
                )

            # ------------------------------------------------
            # 4. Generate reusable MCP prompt
            # ------------------------------------------------
            prompt = f"""
You are an AI document assistant.

Analyze the document:

Document: {doc_id}

Your task is to summarize the document.

Focus specifically on:
{focus}

Summary style:
{style}

Follow these instructions:

1. Identify the main topic.
2. Extract the most important points.
3. Identify important facts, concepts, or findings.
4. Highlight important conclusions.
5. Do not invent information that is not present in the document.
6. Clearly distinguish facts from assumptions.
7. Keep the response organized and easy to understand.

Recommended output structure:

## Summary

Brief overview of the document.

## Key Points

- Important point 1
- Important point 2
- Important point 3

## Important Facts

- Fact 1
- Fact 2

## Conclusions

Summarize the major conclusions supported by the document.

If the document does not contain enough information to answer a particular section, explicitly say so.
""".strip()

            # ------------------------------------------------
            # 5. Return generated prompt
            # ------------------------------------------------
            return prompt

        except Exception as error:

            # ------------------------------------------------
            # 6. Convert internal errors into safe MCP errors
            # ------------------------------------------------
            raise handle_tool_error(
                "summarize_document",
                error,
            )