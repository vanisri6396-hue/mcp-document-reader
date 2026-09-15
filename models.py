from pydantic import BaseModel, Field


# ============================================================
# CREATE DOCUMENT
# ============================================================

class CreateDocumentInput(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Filename of the document"
    )

    content: str = Field(
        min_length=1,
        max_length=10000,
        description="Content of the document"
    )


# ============================================================
# UPDATE DOCUMENT
# ============================================================

class UpdateDocumentInput(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Filename of the document"
    )

    content: str = Field(
        min_length=1,
        max_length=10000,
        description="New document content"
    )


# ============================================================
# DOCUMENT INFORMATION
# ============================================================

class DocumentInfo(BaseModel):

    name: str = Field(
        description="Name of the document"
    )

    size: int = Field(
        description="Document size in bytes"
    )


# ============================================================
# DOCUMENT LIST
# ============================================================

class DocumentList(BaseModel):

    documents: list[DocumentInfo] = Field(
        description="List of available documents"
    )

    count: int = Field(
        description="Total number of documents"
    )


# ============================================================
# SEARCH RESULT
# ============================================================

class SearchResult(BaseModel):

    documents: list[str] = Field(
        description="Names of documents matching the search query"
    )

    count: int = Field(
        description="Number of matching documents"
    )


# ============================================================
# OPERATION RESULT
# ============================================================

class OperationResult(BaseModel):

    success: bool = Field(
        description="Whether the operation succeeded"
    )

    message: str = Field(
        description="Human-readable operation result"
    )