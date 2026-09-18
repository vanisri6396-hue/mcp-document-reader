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
        """
        Expose a document through the MCP resource template.

        Resource URI pattern:
            document://{doc_id}

        Example:
            document://report.txt

        The resource identifier is validated before it is
        resolved to a document. Filesystem paths are never
        accepted directly through the resource URI.
        """

        try:

            # ------------------------------------------------
            # 1. Security
            # ------------------------------------------------
            secure_request(
                "document_resource"
            )

            # ------------------------------------------------
            # 2. Validate resource identifier
            # ------------------------------------------------
            doc_id = validate_document_name(
                doc_id
            )

            # ------------------------------------------------
            # 3. Read document through repository layer
            # ------------------------------------------------
            document_content = (
                repository_read_document(
                    doc_id
                )
            )

            # ------------------------------------------------
            # 4. Return resource contents
            # ------------------------------------------------
            return document_content

        except Exception as error:

            # ------------------------------------------------
            # 5. Convert internal errors into safe MCP errors
            # ------------------------------------------------
            raise handle_tool_error(
                "document_resource",
                error,
            )