from pathlib import Path
from typing import Annotated
import logging

from pydantic import BaseModel, Field
from mcp.server import MCPServer


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("DocumentMCP")


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer("DocumentMCP")


# ============================================================
# STORAGE
# ============================================================

DOCUMENTS_DIR = Path(__file__).parent / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)


# ============================================================
# PYDANTIC MODELS
# ============================================================

class CreateDocumentInput(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Filename of the document",
    )

    content: str = Field(
        min_length=1,
        max_length=10000,
        description="Content of the document",
    )


class UpdateDocumentInput(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Filename of the document",
    )

    content: str = Field(
        min_length=1,
        max_length=10000,
        description="New document content",
    )


class DocumentInfo(BaseModel):
    name: str = Field(
        description="Name of the document"
    )

    size: int = Field(
        description="Document size in bytes"
    )


class DocumentList(BaseModel):
    documents: list[DocumentInfo] = Field(
        description="Documents on the requested page"
    )

    page: int = Field(
        description="Current page number"
    )

    page_size: int = Field(
        description="Number of documents requested per page"
    )

    total_documents: int = Field(
        description="Total number of documents"
    )

    total_pages: int = Field(
        description="Total number of pages"
    )

    has_next_page: bool = Field(
        description="Whether another page exists"
    )


class SearchResult(BaseModel):
    documents: list[str] = Field(
        description="Names of documents matching the search"
    )

    count: int = Field(
        description="Number of matching documents"
    )


class OperationResult(BaseModel):
    success: bool = Field(
        description="Whether the operation succeeded"
    )

    message: str = Field(
        description="Human-readable result message"
    )


# ============================================================
# REPOSITORY LAYER
# ============================================================

def get_document_path(doc_id: str) -> Path:
    """
    Safely resolve a document path.

    Prevents path traversal such as:
        ../../secret.txt
    """

    if not doc_id.strip():
        raise ValueError("Document ID cannot be empty.")

    documents_dir = DOCUMENTS_DIR.resolve()

    file_path = (documents_dir / doc_id).resolve()

    if file_path != documents_dir and documents_dir not in file_path.parents:
        raise ValueError("Invalid document path.")

    return file_path


def repository_create_document(
    name: str,
    content: str,
) -> None:

    file_path = get_document_path(name)

    if file_path.exists():
        raise ValueError(
            f"Document '{name}' already exists."
        )

    file_path.write_text(
        content,
        encoding="utf-8",
    )

    logger.info(
        "Document created: %s",
        name,
    )


def repository_read_document(
    doc_id: str,
) -> str:

    file_path = get_document_path(doc_id)

    if not file_path.exists():
        raise ValueError(
            f"Document '{doc_id}' not found."
        )

    if not file_path.is_file():
        raise ValueError(
            f"'{doc_id}' is not a file."
        )

    return file_path.read_text(
        encoding="utf-8"
    )


def repository_update_document(
    name: str,
    content: str,
) -> None:

    file_path = get_document_path(name)

    if not file_path.exists():
        raise ValueError(
            f"Document '{name}' not found."
        )

    if not file_path.is_file():
        raise ValueError(
            f"'{name}' is not a file."
        )

    file_path.write_text(
        content,
        encoding="utf-8",
    )

    logger.info(
        "Document updated: %s",
        name,
    )


def repository_delete_document(
    doc_id: str,
) -> None:

    file_path = get_document_path(doc_id)

    if not file_path.exists():
        raise ValueError(
            f"Document '{doc_id}' not found."
        )

    if not file_path.is_file():
        raise ValueError(
            f"'{doc_id}' is not a file."
        )

    file_path.unlink()

    logger.info(
        "Document deleted: %s",
        doc_id,
    )


def repository_list_documents() -> list[DocumentInfo]:

    documents: list[DocumentInfo] = []

    for file_path in DOCUMENTS_DIR.iterdir():

        if not file_path.is_file():
            continue

        try:
            documents.append(
                DocumentInfo(
                    name=file_path.name,
                    size=file_path.stat().st_size,
                )
            )

        except OSError as error:

            logger.warning(
                "Could not read metadata for %s: %s",
                file_path.name,
                error,
            )

    documents.sort(
        key=lambda document: document.name.lower()
    )

    return documents


# ============================================================
# SERVICE LAYER
# ============================================================

def service_create_document(
    name: str,
    content: str,
) -> OperationResult:

    data = CreateDocumentInput(
        name=name,
        content=content,
    )

    repository_create_document(
        data.name,
        data.content,
    )

    return OperationResult(
        success=True,
        message=f"Document '{data.name}' created successfully.",
    )


def service_read_document(
    doc_id: str,
    max_chars: int,
) -> str:

    if max_chars < 100 or max_chars > 10000:
        raise ValueError(
            "max_chars must be between 100 and 10000."
        )

    content = repository_read_document(
        doc_id
    )

    return content[:max_chars]


def service_update_document(
    name: str,
    content: str,
) -> OperationResult:

    data = UpdateDocumentInput(
        name=name,
        content=content,
    )

    repository_update_document(
        data.name,
        data.content,
    )

    return OperationResult(
        success=True,
        message=f"Document '{data.name}' updated successfully.",
    )


def service_delete_document(
    doc_id: str,
) -> OperationResult:

    repository_delete_document(
        doc_id
    )

    return OperationResult(
        success=True,
        message=f"Document '{doc_id}' deleted successfully.",
    )


def service_list_documents(
    page: int,
    page_size: int,
) -> DocumentList:

    if page < 1:
        raise ValueError(
            "Page must be at least 1."
        )

    if page_size < 1 or page_size > 100:
        raise ValueError(
            "page_size must be between 1 and 100."
        )

    all_documents = repository_list_documents()

    total_documents = len(all_documents)

    total_pages = (
        (total_documents + page_size - 1)
        // page_size
    )

    start_index = (page - 1) * page_size

    end_index = start_index + page_size

    page_documents = all_documents[
        start_index:end_index
    ]

    has_next_page = page < total_pages

    return DocumentList(
        documents=page_documents,
        page=page,
        page_size=page_size,
        total_documents=total_documents,
        total_pages=total_pages,
        has_next_page=has_next_page,
    )


def service_search_documents(
    query: str,
    case_sensitive: bool,
) -> SearchResult:

    if not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    results: list[str] = []

    for file_path in DOCUMENTS_DIR.iterdir():

        if not file_path.is_file():
            continue

        try:

            content = file_path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:

            logger.warning(
                "Skipping non-UTF8 file: %s",
                file_path.name,
            )

            continue

        if case_sensitive:

            searchable_content = content
            searchable_query = query

        else:

            searchable_content = content.lower()
            searchable_query = query.lower()

        if searchable_query in searchable_content:

            results.append(
                file_path.name
            )

    return SearchResult(
        documents=results,
        count=len(results),
    )


# ============================================================
# MCP TOOLS
# ============================================================

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
            max_length=10000,
        ),
    ],
) -> OperationResult:

    try:

        return service_create_document(
            name,
            content,
        )

    except Exception as error:

        logger.error(
            "create_document failed: %s",
            error,
        )

        raise


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
            description="Maximum number of characters to return",
            ge=100,
            le=10000,
        ),
    ] = 5000,
) -> str:

    try:

        return service_read_document(
            doc_id,
            max_chars,
        )

    except Exception as error:

        logger.error(
            "read_document failed: %s",
            error,
        )

        raise


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
            max_length=10000,
        ),
    ],
) -> OperationResult:

    try:

        return service_update_document(
            name,
            content,
        )

    except Exception as error:

        logger.error(
            "update_document failed: %s",
            error,
        )

        raise


@mcp.tool()
def delete_document(
    doc_id: Annotated[
        str,
        Field(
            description="Filename of the document to delete",
            min_length=1,
            max_length=100,
        ),
    ],
) -> OperationResult:

    try:

        return service_delete_document(
            doc_id
        )

    except Exception as error:

        logger.error(
            "delete_document failed: %s",
            error,
        )

        raise


@mcp.tool()
def list_documents(
    page: Annotated[
        int,
        Field(
            description="Page number starting from 1",
            ge=1,
            le=100000,
        ),
    ] = 1,

    page_size: Annotated[
        int,
        Field(
            description="Number of documents per page",
            ge=1,
            le=100,
        ),
    ] = 10,
) -> DocumentList:

    try:

        return service_list_documents(
            page,
            page_size,
        )

    except Exception as error:

        logger.error(
            "list_documents failed: %s",
            error,
        )

        raise


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
            description="Whether search is case-sensitive",
        ),
    ] = False,
) -> SearchResult:

    try:

        return service_search_documents(
            query,
            case_sensitive,
        )

    except Exception as error:

        logger.error(
            "search_documents failed: %s",
            error,
        )

        raise


# ============================================================
# MCP RESOURCE
# ============================================================

@mcp.resource("document://{doc_id}")
def document_resource(
    doc_id: str,
) -> str:

    logger.info(
        "Reading resource: document://%s",
        doc_id,
    )

    return repository_read_document(
        doc_id
    )


# ============================================================
# MCP PROMPT
# ============================================================

@mcp.prompt()
def summarize_document(
    doc_id: str,
) -> str:

    return (
        f"Please summarize the document '{doc_id}'.\n\n"

        "Focus on:\n"

        "1. Main topic\n"

        "2. Important points\n"

        "3. Key facts\n"

        "4. Important conclusions\n\n"

        "Keep the summary clear and concise."
    )


# ============================================================
# SERVER START
# ============================================================

if __name__ == "__main__":

    logger.info(
        "Starting DocumentMCP server..."
    )

    mcp.run()