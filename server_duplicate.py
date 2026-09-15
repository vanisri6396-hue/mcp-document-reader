from pathlib import Path
from typing import Annotated
import logging
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from mcp.server import MCPServer


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# SECURITY CONFIGURATION
# ============================================================

MAX_DOCUMENT_CHARS = 100_000
MAX_DOCUMENT_BYTES = 200_000

MCP_API_KEY = os.getenv("MCP_API_KEY")


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
        max_length=MAX_DOCUMENT_CHARS,
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
        max_length=MAX_DOCUMENT_CHARS,
        description="New document content",
    )


class DocumentInfo(BaseModel):
    name: str = Field(
        description="Name of the document",
    )

    size: int = Field(
        description="Document size in bytes",
    )


class DocumentList(BaseModel):
    documents: list[DocumentInfo] = Field(
        description="Documents on the requested page",
    )

    page: int = Field(
        description="Current page number",
    )

    page_size: int = Field(
        description="Number of documents requested per page",
    )

    total_documents: int = Field(
        description="Total number of documents",
    )

    total_pages: int = Field(
        description="Total number of pages",
    )

    has_next_page: bool = Field(
        description="Whether another page exists",
    )


class SearchResult(BaseModel):
    documents: list[str] = Field(
        description="Names of documents matching the search",
    )

    count: int = Field(
        description="Number of matching documents",
    )


class OperationResult(BaseModel):
    success: bool = Field(
        description="Whether the operation succeeded",
    )

    message: str = Field(
        description="Human-readable result message",
    )


# ============================================================
# SECURITY HELPERS
# ============================================================


def validate_document_name(name: str) -> str:
    """
    Validate that a document identifier is a safe filename.

    Security controls:
    - Reject empty names
    - Reject "." and ".."
    - Reject Unix path separators
    - Reject Windows path separators
    - Reject directory paths
    - Allow only .txt files
    """

    if not isinstance(name, str):
        raise ValueError("Document name must be text.")

    name = name.strip()

    if not name:
        raise ValueError("Document name cannot be empty.")

    if name in {".", ".."}:
        raise ValueError("Invalid document name.")

    if "/" in name or "\\" in name:
        raise ValueError(
            "Document name cannot contain path separators."
        )

    if Path(name).name != name:
        raise ValueError(
            "Document name must be a filename, not a path."
        )

    if not name.lower().endswith(".txt"):
        raise ValueError(
            "Only .txt documents are allowed."
        )

    return name

# ============================================================
# SECURITY CONTEXT
# ============================================================

DEFAULT_ROLE = "reader"


def get_current_role() -> str:
    """
    Get the current user's role.

    In this local STDIO learning project, the role is supplied
    through MCP_USER_ROLE.

    Production remote MCP deployments should obtain the role
    from the authenticated identity/session instead.
    """

    role = os.getenv("MCP_USER_ROLE", DEFAULT_ROLE)

    return validate_role(role)
def check_tool_permission(tool_name: str) -> None:
    """
    Authorize the currently authenticated role to use a tool.
    """

    role = get_current_role()

    authorize(role, tool_name)
def validate_document_content(content: str) -> str:
    """
    Validate document content before writing it to disk.

    Security controls:
    - Must be a string
    - Must not be empty
    - Reject NUL characters
    - Maximum character limit
    - Maximum UTF-8 byte limit
    """

    if not isinstance(content, str):
        raise ValueError(
            "Document content must be text."
        )

    if not content.strip():
        raise ValueError(
            "Document content cannot be empty."
        )

    if "\x00" in content:
        raise ValueError(
            "Document content contains an invalid character."
        )

    if len(content) > MAX_DOCUMENT_CHARS:
        raise ValueError(
            "Document content exceeds the maximum "
            f"of {MAX_DOCUMENT_CHARS} characters."
        )

    content_bytes = content.encode("utf-8")

    if len(content_bytes) > MAX_DOCUMENT_BYTES:
        raise ValueError(
            "Document content exceeds the maximum "
            f"size of {MAX_DOCUMENT_BYTES} bytes."
        )

    return content


def get_document_path(doc_id: str) -> Path:
    """
    Return a safe path inside the documents directory.

    Uses both filename validation and resolved-path
    verification for defense in depth.
    """

    doc_id = validate_document_name(doc_id)

    documents_dir = DOCUMENTS_DIR.resolve()

    file_path = (documents_dir / doc_id).resolve()

    # Defense-in-depth path traversal protection
    if documents_dir not in file_path.parents:
        raise ValueError(
            "Invalid document path."
        )

    return file_path


def handle_tool_error(
    tool_name: str,
    error: Exception,
) -> ValueError:
    """
    Log detailed internal information while returning
    a controlled error to the MCP client.
    """

    logger.error(
        "%s failed: %s",
        tool_name,
        error,
        exc_info=True,
    )

    if isinstance(error, ValueError):
        return ValueError(str(error))

    return ValueError(
        f"{tool_name} failed. Please try again."
    )


def authenticate(api_key: str) -> None:
    """
    Validate an API key.

    This helper is prepared for authenticated remote
    MCP deployments. The current local STDIO server
    does not expose the API key through every tool.
    """

    if not MCP_API_KEY:
        raise RuntimeError(
            "Authentication is not configured."
        )

    if not api_key:
        raise ValueError(
            "Authentication required."
        )

    if api_key != MCP_API_KEY:
        raise ValueError(
            "Invalid authentication credentials."
        )

# ============================================================
# AUTHORIZATION / RBAC
# ============================================================

VALID_ROLES = {"reader", "editor", "admin"}

TOOL_PERMISSIONS = {
    # Read-only operations
    "read_document": {"reader", "editor", "admin"},
    "list_documents": {"reader", "editor", "admin"},
    "search_documents": {"reader", "editor", "admin"},
    "document_resource": {"reader", "editor", "admin"},
    "summarize_document": {"reader", "editor", "admin"},

    # Write operations
    "create_document": {"editor", "admin"},
    "update_document": {"editor", "admin"},

    # Destructive operation
    "delete_document": {"admin"},
}


def validate_role(role: str) -> str:
    """Validate that the supplied role is supported."""

    if not isinstance(role, str):
        raise ValueError("Invalid role.")

    role = role.strip().lower()

    if role not in VALID_ROLES:
        raise ValueError("Invalid role.")

    return role


def authorize(role: str, tool_name: str) -> None:
    """
    Check whether a role is allowed to execute a tool.

    Raises:
        PermissionError: if the role does not have permission.
        ValueError: if the role/tool is invalid.
    """

    role = validate_role(role)

    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ValueError("Tool name cannot be empty.")

    tool_name = tool_name.strip()

    allowed_roles = TOOL_PERMISSIONS.get(tool_name)

    if allowed_roles is None:
        raise ValueError("Unknown tool.")

    if role not in allowed_roles:
        raise PermissionError(
            f"Role '{role}' is not authorized to use '{tool_name}'."
        )

    logger.info(
        "Authorization successful | role=%s | tool=%s",
        role,
        tool_name,
    )
# ============================================================
# REPOSITORY LAYER
# ============================================================


def repository_create_document(
    name: str,
    content: str,
) -> None:

    # Defense in depth:
    # validate again at the repository boundary.
    name = validate_document_name(name)
    content = validate_document_content(content)

    file_path = get_document_path(name)

    if file_path.exists():
        raise ValueError(
            f"Document '{name}' already exists."
        )

    try:
        file_path.write_text(
            content,
            encoding="utf-8",
        )

    except OSError:
        logger.exception(
            "Failed to create document: %s",
            name,
        )

        raise ValueError(
            "Unable to save document."
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

    try:
        return file_path.read_text(
            encoding="utf-8",
        )

    except UnicodeDecodeError:
        logger.exception(
            "Invalid UTF-8 document: %s",
            doc_id,
        )

        raise ValueError(
            "Document could not be decoded as UTF-8."
        )

    except OSError:
        logger.exception(
            "Failed to read document: %s",
            doc_id,
        )

        raise ValueError(
            "Unable to read document."
        )


def repository_update_document(
    name: str,
    content: str,
) -> None:

    # Defense in depth
    name = validate_document_name(name)
    content = validate_document_content(content)

    file_path = get_document_path(name)

    if not file_path.exists():
        raise ValueError(
            f"Document '{name}' not found."
        )

    if not file_path.is_file():
        raise ValueError(
            f"'{name}' is not a file."
        )

    try:
        file_path.write_text(
            content,
            encoding="utf-8",
        )

    except OSError:
        logger.exception(
            "Failed to update document: %s",
            name,
        )

        raise ValueError(
            "Unable to update document."
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

    try:
        file_path.unlink()

    except OSError:
        logger.exception(
            "Failed to delete document: %s",
            doc_id,
        )

        raise ValueError(
            "Unable to delete document."
        )

    logger.info(
        "Document deleted: %s",
        doc_id,
    )


def repository_list_documents() -> list[DocumentInfo]:

    documents: list[DocumentInfo] = []

    try:
        for file_path in DOCUMENTS_DIR.iterdir():

            if not file_path.is_file():
                continue

            # Only expose .txt files
            if file_path.suffix.lower() != ".txt":
                continue

            try:
                documents.append(
                    DocumentInfo(
                        name=file_path.name,
                        size=file_path.stat().st_size,
                    )
                )

            except OSError:
                logger.warning(
                    "Could not read metadata for %s",
                    file_path.name,
                )

    except OSError:
        logger.exception(
            "Unable to list documents."
        )

        raise ValueError(
            "Unable to list documents."
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
        message=(
            f"Document '{data.name}' "
            "created successfully."
        ),
    )


def service_read_document(
    doc_id: str,
    max_chars: int,
) -> str:

    if max_chars < 100 or max_chars > 10000:
        raise ValueError(
            "max_chars must be between 100 and 10000."
        )

    # Validate before repository access
    doc_id = validate_document_name(doc_id)

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
        message=(
            f"Document '{data.name}' "
            "updated successfully."
        ),
    )


def service_delete_document(
    doc_id: str,
) -> OperationResult:

    doc_id = validate_document_name(doc_id)

    repository_delete_document(
        doc_id
    )

    return OperationResult(
        success=True,
        message=(
            f"Document '{doc_id}' "
            "deleted successfully."
        ),
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

    query = query.strip()

    if not query:
        raise ValueError(
            "Search query cannot be empty."
        )

    if len(query) > 200:
        raise ValueError(
            "Search query cannot exceed 200 characters."
        )

    results: list[str] = []

    try:
        for file_path in DOCUMENTS_DIR.iterdir():

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() != ".txt":
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

            except OSError:
                logger.warning(
                    "Unable to read file: %s",
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

    except OSError:
        logger.exception(
            "Unable to search documents."
        )

        raise ValueError(
            "Unable to search documents."
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
            max_length=MAX_DOCUMENT_CHARS,
        ),
    ],
) -> OperationResult:

    try:

        return service_create_document(
            name,
            content,
        )

    except Exception as error:

        raise handle_tool_error(
            "create_document",
            error,
        )


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

        return service_read_document(
            doc_id,
            max_chars,
        )

    except Exception as error:

        raise handle_tool_error(
            "read_document",
            error,
        )


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

        return service_update_document(
            name,
            content,
        )

    except Exception as error:

        raise handle_tool_error(
            "update_document",
            error,
        )


@mcp.tool()
def delete_document(
    doc_id: Annotated[
        str,
        Field(
            description=(
                "Filename of the document to delete"
            ),
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

        raise handle_tool_error(
            "delete_document",
            error,
        )


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

        raise handle_tool_error(
            "list_documents",
            error,
        )


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

        return service_search_documents(
            query,
            case_sensitive,
        )

    except Exception as error:

        raise handle_tool_error(
            "search_documents",
            error,
        )


# ============================================================
# MCP RESOURCE
# ============================================================


@mcp.resource("document://{doc_id}")
def document_resource(
    doc_id: str,
) -> str:

    try:

        doc_id = validate_document_name(
            doc_id
        )

        logger.info(
            "Reading document resource: %s",
            doc_id,
        )

        return repository_read_document(
            doc_id
        )

    except Exception as error:

        raise handle_tool_error(
            "document_resource",
            error,
        )


# ============================================================
# MCP PROMPT
# ============================================================


@mcp.prompt()
def summarize_document(
    doc_id: str,
) -> str:

    doc_id = validate_document_name(
        doc_id
    )

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


# ============================================================
# SERVER START
# ============================================================


if __name__ == "__main__":

    logger.info(
        "Starting DocumentMCP server..."
    )

    mcp.run()