from mcp.server import MCPServer

from repository.document_repository import (
    repository_read_document,
)

from security.context import (
    secure_request,
)

from security.errors import (
    handle_tool_error,
)

from security.validation import (
    validate_document_name,
)


def register_resources(
    mcp: MCPServer,
) -> None:

    @mcp.resource(
        "document://{doc_id}"
    )
    def document_resource(
        doc_id: str,
    ) -> str:

        try:

            # Centralized security layer
            secure_request(
                "document_resource"
            )

            # Validation
            doc_id = validate_document_name(
                doc_id
            )

            # Repository access
            return repository_read_document(
                doc_id
            )

        except Exception as error:

            raise handle_tool_error(
                "document_resource",
                error,
            )