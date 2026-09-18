from typing import Any

from pydantic import BaseModel, Field

from config.settings import MAX_DOCUMENT_CHARS


# ============================================================
# CREATE DOCUMENT INPUT
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


# ============================================================
# UPDATE DOCUMENT INPUT
# ============================================================


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


# ============================================================
# DOCUMENT INFORMATION
# ============================================================


class DocumentInfo(BaseModel):

    name: str = Field(
        description="Name of the document",
    )

    size: int = Field(
        description="Document size in bytes",
    )


# ============================================================
# DOCUMENT LIST
# ============================================================


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


# ============================================================
# SEARCH RESULT
# ============================================================


class SearchResult(BaseModel):

    documents: list[str] = Field(
        description="Names of documents matching the search",
    )

    count: int = Field(
        description="Number of matching documents",
    )


# ============================================================
# OPERATION RESULT
# ============================================================


class OperationResult(BaseModel):

    success: bool = Field(
        description="Whether the operation succeeded",
    )

    message: str = Field(
        description="Human-readable result message",
    )


# ============================================================
# STRUCTURED TOOL RESULT METADATA
# ============================================================


class ToolResultMetadata(BaseModel):

    operation: str = Field(
        min_length=1,
        description="Name of the operation that produced the result",
    )

    tool_name: str = Field(
        min_length=1,
        description="MCP tool that produced the result",
    )

    success: bool = Field(
        description="Whether the tool operation succeeded",
    )


# ============================================================
# STRUCTURED DOCUMENT OPERATION RESULT
# ============================================================


class StructuredOperationResult(BaseModel):

    success: bool = Field(
        description="Whether the operation succeeded",
    )

    operation: str = Field(
        min_length=1,
        description="Operation performed by the tool",
    )

    message: str = Field(
        description="Human-readable result message",
    )

    document_id: str | None = Field(
        default=None,
        description="Document identifier associated with the operation",
    )


# ============================================================
# STRUCTURED DOCUMENT READ RESULT
# ============================================================


class DocumentReadResult(BaseModel):

    success: bool = Field(
        description="Whether the read operation succeeded",
    )

    operation: str = Field(
        default="read_document",
        description="Operation performed",
    )

    document_id: str = Field(
        min_length=1,
        description="Document identifier",
    )

    content: str = Field(
        description="Document contents returned by the tool",
    )

    characters_returned: int = Field(
        ge=0,
        description="Number of characters returned",
    )

    truncated: bool = Field(
        description="Whether the returned content was truncated",
    )


# ============================================================
# STRUCTURED SEARCH RESULT
# ============================================================


class StructuredSearchResult(BaseModel):

    success: bool = Field(
        description="Whether the search succeeded",
    )

    operation: str = Field(
        default="search_documents",
        description="Operation performed",
    )

    query: str = Field(
        min_length=1,
        description="Search query",
    )

    case_sensitive: bool = Field(
        description="Whether the search was case-sensitive",
    )

    documents: list[str] = Field(
        description="Names of matching documents",
    )

    count: int = Field(
        ge=0,
        description="Number of matching documents",
    )


# ============================================================
# STRUCTURED PAGINATED DOCUMENT RESULT
# ============================================================


class StructuredDocumentList(BaseModel):

    success: bool = Field(
        description="Whether the listing succeeded",
    )

    operation: str = Field(
        default="list_documents",
        description="Operation performed",
    )

    documents: list[DocumentInfo] = Field(
        description="Documents on the requested page",
    )

    page: int = Field(
        ge=1,
        description="Current page number",
    )

    page_size: int = Field(
        ge=1,
        description="Number of documents requested per page",
    )

    total_documents: int = Field(
        ge=0,
        description="Total number of documents",
    )

    total_pages: int = Field(
        ge=0,
        description="Total number of pages",
    )

    has_next_page: bool = Field(
        description="Whether another page exists",
    )


# ============================================================
# GENERIC TOOL RESULT
# ============================================================


class GenericToolResult(BaseModel):

    success: bool = Field(
        description="Whether the operation succeeded",
    )

    operation: str = Field(
        min_length=1,
        description="Operation performed by the tool",
    )

    message: str = Field(
        description="Human-readable result message",
    )

    data: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured operation data",
    )