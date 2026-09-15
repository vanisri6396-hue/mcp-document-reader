from pydantic import BaseModel, Field

from config.settings import MAX_DOCUMENT_CHARS


# ============================================================
# CREATE DOCUMENT
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
# UPDATE DOCUMENT
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