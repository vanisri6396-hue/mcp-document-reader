from typing import Annotated

from pydantic import Field

from mcp.server import MCPServer

from security.context import (
    secure_request,
)

from config.settings import (
    MAX_DOCUMENT_CHARS,
)

from models.document import (
    DocumentList,
    OperationResult,
    SearchResult,
)

from security.errors import (
    handle_tool_error,
)

from services.document_service import (
    service_create_document,
    service_read_document,
    service_update_document,
    service_delete_document,
    service_list_documents,
    service_search_documents,
)


def register_tools(
    mcp: MCPServer,
) -> None:

    # ========================================================
    # CREATE
    # ========================================================

    @mcp.tool()
    def create_document(
        name: Annotated[
            str,
            Field(
                description="Filename of the document",
                min_length=1,
                max_length=100,
            ),
        ],
        content: Annotated[
            str,
            Field(
                description="Content of the document",
                min_length=1,
                max_length=MAX_DOCUMENT_CHARS,
            ),
        ],
    ) -> OperationResult:

        try:

            # Centralized security layer
            secure_request(
                "create_document"
            )

            # Business logic
            return service_create_document(
                name,
                content,
            )

        except Exception as error:

            raise handle_tool_error(
                "create_document",
                error,
            )

    # ========================================================
    # READ
    # ========================================================

    @mcp.tool()
    def read_document(
        doc_id: Annotated[
            str,
            Field(
                description="Filename of the document",
                min_length=1,
                max_length=100,
            ),
        ],
        max_chars: Annotated[
            int,
            Field(
                description=(
                    "Maximum number of characters "
                    "to return"
                ),
                ge=100,
                le=10000,
            ),
        ] = 5000,
    ) -> str:

        try:

            # Centralized security layer
            secure_request(
                "read_document"
            )

            # Business logic
            return service_read_document(
                doc_id,
                max_chars,
            )

        except Exception as error:

            raise handle_tool_error(
                "read_document",
                error,
            )

    # ========================================================
    # UPDATE
    # ========================================================

    @mcp.tool()
    def update_document(
        name: Annotated[
            str,
            Field(
                description="Filename of the document",
                min_length=1,
                max_length=100,
            ),
        ],
        content: Annotated[
            str,
            Field(
                description="New document content",
                min_length=1,
                max_length=MAX_DOCUMENT_CHARS,
            ),
        ],
    ) -> OperationResult:

        try:

            # Centralized security layer
            secure_request(
                "update_document"
            )

            # Business logic
            return service_update_document(
                name,
                content,
            )

        except Exception as error:

            raise handle_tool_error(
                "update_document",
                error,
            )

    # ========================================================
    # DELETE
    # ========================================================

    @mcp.tool()
    def delete_document(
        doc_id: Annotated[
            str,
            Field(
                description=(
                    "Filename of the document "
                    "to delete"
                ),
                min_length=1,
                max_length=100,
            ),
        ],
    ) -> OperationResult:

        try:

            # Centralized security layer
            secure_request(
                "delete_document"
            )

            # Business logic
            return service_delete_document(
                doc_id
            )

        except Exception as error:

            raise handle_tool_error(
                "delete_document",
                error,
            )

    # ========================================================
    # LIST
    # ========================================================

    @mcp.tool()
    def list_documents(
        page: Annotated[
            int,
            Field(
                description=(
                    "Page number starting from 1"
                ),
                ge=1,
                le=100000,
            ),
        ] = 1,
        page_size: Annotated[
            int,
            Field(
                description=(
                    "Number of documents per page"
                ),
                ge=1,
                le=100,
            ),
        ] = 10,
    ) -> DocumentList:

        try:

            # Centralized security layer
            secure_request(
                "list_documents"
            )

            # Business logic
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
    # SEARCH
    # ========================================================

    @mcp.tool()
    def search_documents(
        query: Annotated[
            str,
            Field(
                description="Text to search for",
                min_length=1,
                max_length=200,
            ),
        ],
        case_sensitive: Annotated[
            bool,
            Field(
                description=(
                    "Whether search is case-sensitive"
                ),
            ),
        ] = False,
    ) -> SearchResult:

        try:

            # Centralized security layer
            secure_request(
                "search_documents"
            )

            # Business logic
            return service_search_documents(
                query,
                case_sensitive,
            )

        except Exception as error:

            raise handle_tool_error(
                "search_documents",
                error,
            )