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
    ) -> str:

        try:

            # Centralized security layer
            secure_request(
                "summarize_document"
            )

            # Validation
            doc_id = validate_document_name(
                doc_id
            )

            # Prompt generation
            return (
                f"Please summarize the document "
                f"'{doc_id}'.\n\n"

                "Focus on:\n"

                "1. Main topic\n"

                "2. Important points\n"

                "3. Key facts\n"

                "4. Important conclusions\n\n"

                "Keep the summary clear and concise."
            )

        except Exception as error:

            raise handle_tool_error(
                "summarize_document",
                error,
            )