import asyncio

import anyio

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

    # ========================================================
    # DOCUMENT TOOLS
    # ========================================================

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
        "description": (
            "Read the contents of an existing text document."
        ),
        "read_only": True,
        "write": False,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": (
            "Read-only operation. "
            "Does not modify document data."
        ),
    },

    "update_document": {
        "description": (
            "Update the contents of an existing text document."
        ),
        "read_only": False,
        "write": True,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": "Modifies an existing document.",
    },

    "delete_document": {
        "description": (
            "Permanently delete an existing text document."
        ),
        "read_only": False,
        "write": True,
        "destructive": True,
        "idempotent": True,
        "confirmation_required": True,
        "safety": (
            "Destructive operation. "
            "Permanently removes a document and "
            "requires explicit user intent."
        ),
    },

    "list_documents": {
        "description": (
            "List available text documents with pagination."
        ),
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

    # ========================================================
    # LONG-RUNNING OPERATIONS
    # ========================================================

    "process_documents": {
        "description": (
            "Process multiple documents while reporting "
            "progress for each document."
        ),
        "read_only": True,
        "write": False,
        "destructive": False,
        "idempotent": True,
        "confirmation_required": False,
        "safety": (
            "Read-only batch operation. "
            "Does not modify document data."
        ),
    },
}


# ============================================================
# METADATA HELPERS
# ============================================================


def get_tool_metadata(
    tool_name: str,
) -> dict:

    if not isinstance(
        tool_name,
        str,
    ):
        raise ValueError(
            "Tool name must be text."
        )

    tool_name = tool_name.strip()

    if not tool_name:
        raise ValueError(
            "Tool name cannot be empty."
        )

    metadata = TOOL_METADATA.get(
        tool_name
    )

    if metadata is None:
        raise ValueError(
            f"Unknown tool: {tool_name}"
        )

    return metadata.copy()


def get_all_tool_metadata() -> dict:

    return {
        name: metadata.copy()
        for name, metadata
        in TOOL_METADATA.items()
    }


# ============================================================
# READ RESULT HELPER
# ============================================================


def _calculate_truncation(
    content: str,
    max_chars: int,
) -> tuple[int, bool]:

    characters_returned = len(
        content
    )

    truncated = (
        characters_returned >= max_chars
    )

    return (
        characters_returned,
        truncated,
    )


# ============================================================
# MCP TOOL REGISTRATION
# ============================================================


def register_tools(
    mcp: MCPServer,
) -> None:

    # ========================================================
    # CREATE DOCUMENT
    # ========================================================

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
                message=(
                    f"Document '{name}' "
                    "created successfully."
                ),
            )

        except Exception as error:

            raise handle_tool_error(
                "create_document",
                error,
            )

    # ========================================================
    # READ DOCUMENT
    # ========================================================

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
                characters_returned=(
                    characters_returned
                ),
                truncated=truncated,
            )

        except Exception as error:

            raise handle_tool_error(
                "read_document",
                error,
            )

    # ========================================================
    # UPDATE DOCUMENT
    # ========================================================

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
                message=(
                    f"Document '{name}' "
                    "updated successfully."
                ),
            )

        except Exception as error:

            raise handle_tool_error(
                "update_document",
                error,
            )

    # ========================================================
    # DELETE DOCUMENT
    # ========================================================

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
                message=(
                    f"Document '{name}' "
                    "deleted successfully."
                ),
            )

        except Exception as error:

            raise handle_tool_error(
                "delete_document",
                error,
            )

    # ========================================================
    # LIST DOCUMENTS
    # ========================================================

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

    # ========================================================
    # SEARCH DOCUMENTS
    # ========================================================

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

    # ========================================================
    # PROCESS DOCUMENTS
    #
    # Demonstrates:
    # - Context injection
    # - Progress reporting
    # - Cancellation handling
    # ========================================================

    @mcp.tool()
    async def process_documents(
        document_ids: list[str],
        ctx: Context,
    ) -> dict:

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
                    "A maximum of 50 documents "
                    "can be processed at once."
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
                    "Starting processing of "
                    f"{total_documents} "
                    "document(s)."
                ),
            )

            try:

                for index, doc_id in enumerate(
                    validated_document_ids,
                    start=1,
                ):

                    # ------------------------------------------------
                    # Simulate a genuinely long-running processing
                    # step so cancellation can be observed.
                    #
                    # This sleep is intentionally short and exists
                    # only for the Level 8.8 demonstration.
                    # ------------------------------------------------

                    await asyncio.sleep(
                        0.5
                    )

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
                                f"({index}/"
                                f"{total_documents})."
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
                                f"({index}/"
                                f"{total_documents})."
                            ),
                        )

            except (
                anyio.get_cancelled_exc_class()
            ):

                # ------------------------------------------------
                # Cancellation reached the server.
                #
                # Perform any required cleanup here.
                # Then re-raise the cancellation exception.
                #
                # IMPORTANT:
                # Never swallow cancellation.
                # ------------------------------------------------

                await ctx.report_progress(
                    progress=len(
                        processed_documents
                    ),
                    total=total_documents,
                    message=(
                        "Processing cancelled. "
                        "Cleaning up."
                    ),
                )

                raise

            return {
                "success": (
                    len(failed_documents) == 0
                ),
                "operation": (
                    "process_documents"
                ),
                "total_documents": (
                    total_documents
                ),
                "processed_count": (
                    len(processed_documents)
                ),
                "failed_count": (
                    len(failed_documents)
                ),
                "processed_documents": (
                    processed_documents
                ),
                "failed_documents": (
                    failed_documents
                ),
            }

        except (
            anyio.get_cancelled_exc_class()
        ):

            # ----------------------------------------------------
            # Cancellation must propagate to the MCP dispatcher.
            # Do NOT convert cancellation into a normal tool error.
            # ----------------------------------------------------

            raise

        except Exception as error:

            raise handle_tool_error(
                "process_documents",
                error,
            )