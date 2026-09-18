from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from models.document import (
    DocumentList,
    DocumentReadResult,
    OperationResult,
    SearchResult,
)

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


TOOL_METADATA = {
    "create_document": {
        "description": "Create a new text document.",
        "read_only": False,
        "write": True,
        "destructive": False,
        "idempotent": False,
        "confirmation_required": False,
        "safety": "Creates a new document.",
    },
    "read_document": {
        "description": "Read the contents of an existing text document.",
        "read_only": True,
        "write": False,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": "Read-only operation. Does not modify document data.",
    },
    "update_document": {
        "description": "Update the contents of an existing text document.",
        "read_only": False,
        "write": True,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": "Modifies an existing document.",
    },
    "delete_document": {
        "description": "Permanently delete an existing text document.",
        "read_only": False,
        "write": True,
        "destructive": True,
        "idempotent": True,
        "confirmation_required": True,
        "safety": (
            "Destructive operation. Permanently removes a document "
            "and requires explicit user intent."
        ),
    },
    "list_documents": {
        "description": "List available text documents with pagination.",
        "read_only": True,
        "write": False,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": "Read-only operation.",
    },
    "search_documents": {
        "description": "Search documents for matching text.",
        "read_only": True,
        "write": False,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": "Read-only operation.",
    },
    "process_documents": {
        "description": (
            "Process multiple documents while reporting progress "
            "for each document."
        ),
        "read_only": True,
        "write": False,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": (
            "Read-only batch operation. Does not modify document data."
        ),
    },
}


def get_tool_metadata(tool_name: str) -> dict:
    """
    Return metadata for a single MCP tool.
    """

    if not isinstance(tool_name, str):
        raise ValueError("Tool name must be text.")

    tool_name = tool_name.strip()

    if not tool_name:
        raise ValueError("Tool name cannot be empty.")

    metadata = TOOL_METADATA.get(tool_name)

    if metadata is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    return metadata.copy()


def get_all_tool_metadata() -> dict:
    """
    Return metadata for all registered MCP tools.
    """

    return {
        name: metadata.copy()
        for name, metadata in TOOL_METADATA.items()
    }


def _calculate_truncation(
    content: str,
    max_chars: int,
) -> tuple[int, bool]:
    """
    Calculate the number of returned characters and whether
    the content is considered truncated.

    This helper currently assumes the repository/service layer
    returns at most max_chars characters.
    """

    characters_returned = len(content)

    truncated = characters_returned >= max_chars

    return characters_returned, truncated


def register_tools(
    mcp: MCPServer,
) -> None:

    @mcp.tool()
    def create_document(
        name: str,
        content: str,
    ) -> OperationResult:

        try:

            secure_request(
                "create_document"
            )

            from services.document_service import (
                service_create_document,
            )

            service_create_document(
                name,
                content,
            )

            return OperationResult(
                success=True,
                message=f"Document '{name}' created successfully.",
            )

        except Exception as error:

            raise handle_tool_error(
                "create_document",
                error,
            )

    @mcp.tool()
    def read_document(
        doc_id: str,
    ) -> DocumentReadResult:

        try:

            secure_request(
                "read_document"
            )

            from services.document_service import (
                service_read_document,
            )

            content = service_read_document(
                doc_id
            )

            characters_returned, truncated = (
                _calculate_truncation(
                    content,
                    100_000,
                )
            )

            return DocumentReadResult(
                success=True,
                operation="read_document",
                document_id=doc_id,
                content=content,
                characters_returned=characters_returned,
                truncated=truncated,
            )

        except Exception as error:

            raise handle_tool_error(
                "read_document",
                error,
            )

    @mcp.tool()
    def update_document(
        name: str,
        content: str,
    ) -> OperationResult:

        try:

            secure_request(
                "update_document"
            )

            from services.document_service import (
                service_update_document,
            )

            service_update_document(
                name,
                content,
            )

            return OperationResult(
                success=True,
                message=f"Document '{name}' updated successfully.",
            )

        except Exception as error:

            raise handle_tool_error(
                "update_document",
                error,
            )

    @mcp.tool()
    def delete_document(
        name: str,
    ) -> OperationResult:

        try:

            secure_request(
                "delete_document"
            )

            from services.document_service import (
                service_delete_document,
            )

            service_delete_document(
                name
            )

            return OperationResult(
                success=True,
                message=f"Document '{name}' deleted successfully.",
            )

        except Exception as error:

            raise handle_tool_error(
                "delete_document",
                error,
            )

    @mcp.tool()
    def list_documents(
        page: int = 1,
        page_size: int = 10,
    ) -> DocumentList:

        try:

            secure_request(
                "list_documents"
            )

            from services.document_service import (
                service_list_documents,
            )

            return service_list_documents(
                page,
                page_size,
            )

        except Exception as error:

            raise handle_tool_error(
                "list_documents",
                error,
            )

    @mcp.tool()
    def search_documents(
        query: str,
        case_sensitive: bool = False,
    ) -> SearchResult:

        try:

            secure_request(
                "search_documents"
            )

            from services.document_service import (
                service_search_documents,
            )

            return service_search_documents(
                query,
                case_sensitive,
            )

        except Exception as error:

            raise handle_tool_error(
                "search_documents",
                error,
            )

    @mcp.tool()
    async def process_documents(
        document_ids: list[str],
        ctx: Context,
    ) -> dict:
        """
        Process multiple documents while reporting progress.

        This tool demonstrates MCP progress notifications.

        Progress is reported once for every successfully processed
        document.

        The Context parameter is injected automatically by the
        MCP SDK and is not visible to the LLM as a tool argument.
        """

        try:

            secure_request(
                "process_documents"
            )

            if not isinstance(
                document_ids,
                list,
            ):
                raise ValueError(
                    "document_ids must be a list."
                )

            if not document_ids:
                raise ValueError(
                    "At least one document ID is required."
                )

            if len(document_ids) > 50:
                raise ValueError(
                    "A maximum of 50 documents can be processed at once."
                )

            validated_document_ids = []

            for doc_id in document_ids:

                validated_doc_id = (
                    validate_document_name(
                        doc_id
                    )
                )

                validated_document_ids.append(
                    validated_doc_id
                )

            total_documents = len(
                validated_document_ids
            )

            processed_documents = []

            failed_documents = []

            await ctx.report_progress(
                progress=0,
                total=total_documents,
                message=(
                    f"Starting processing of "
                    f"{total_documents} document(s)."
                ),
            )

            for index, doc_id in enumerate(
                validated_document_ids,
                start=1,
            ):

                try:

                    repository_read_document(
                        doc_id
                    )

                    processed_documents.append(
                        doc_id
                    )

                    await ctx.report_progress(
                        progress=index,
                        total=total_documents,
                        message=(
                            f"Processed "
                            f"{doc_id} "
                            f"({index}/{total_documents})."
                        ),
                    )

                except Exception as document_error:

                    failed_documents.append(
                        {
                            "document_id": doc_id,
                            "error": str(
                                document_error
                            ),
                        }
                    )

                    await ctx.report_progress(
                        progress=index,
                        total=total_documents,
                        message=(
                            f"Failed to process "
                            f"{doc_id} "
                            f"({index}/{total_documents})."
                        ),
                    )

            return {
                "success": len(
                    failed_documents
                ) == 0,
                "operation": "process_documents",
                "total_documents": total_documents,
                "processed_count": len(
                    processed_documents
                ),
                "failed_count": len(
                    failed_documents
                ),
                "processed_documents": (
                    processed_documents
                ),
                "failed_documents": (
                    failed_documents
                ),
            }

        except Exception as error:

            raise handle_tool_error(
                "process_documents",
                error,
            )