from pathlib import Path

from config.settings import (
    DOCUMENTS_DIR,
    MAX_DOCUMENT_CHARS,
    MAX_DOCUMENT_BYTES,
)


# ============================================================
# DOCUMENT NAME VALIDATION
# ============================================================


def validate_document_name(
    name: str,
) -> str:
    """
    Validate that a document identifier
    is a safe filename.
    """

    if not isinstance(name, str):

        raise ValueError(
            "Document name must be text."
        )

    name = name.strip()

    if not name:

        raise ValueError(
            "Document name cannot be empty."
        )

    if name in {".", ".."}:

        raise ValueError(
            "Invalid document name."
        )

    if "/" in name or "\\" in name:

        raise ValueError(
            "Document name cannot contain "
            "path separators."
        )

    if Path(name).name != name:

        raise ValueError(
            "Document name must be a filename, "
            "not a path."
        )

    if not name.lower().endswith(".txt"):

        raise ValueError(
            "Only .txt documents are allowed."
        )

    return name


# ============================================================
# DOCUMENT CONTENT VALIDATION
# ============================================================


def validate_document_content(
    content: str,
) -> str:
    """
    Validate document content before
    writing it to disk.
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
            "Document content contains "
            "an invalid character."
        )

    if len(content) > MAX_DOCUMENT_CHARS:

        raise ValueError(
            "Document content exceeds the maximum "
            f"of {MAX_DOCUMENT_CHARS} characters."
        )

    content_bytes = content.encode(
        "utf-8"
    )

    if len(content_bytes) > MAX_DOCUMENT_BYTES:

        raise ValueError(
            "Document content exceeds the maximum "
            f"size of {MAX_DOCUMENT_BYTES} bytes."
        )

    return content


# ============================================================
# SAFE DOCUMENT PATH
# ============================================================


def get_document_path(
    doc_id: str,
) -> Path:
    """
    Return a safe path inside the
    documents directory.
    """

    doc_id = validate_document_name(
        doc_id
    )

    documents_dir = DOCUMENTS_DIR.resolve()

    file_path = (
        documents_dir / doc_id
    ).resolve()

    # Defense against path traversal
    if documents_dir not in file_path.parents:

        raise ValueError(
            "Invalid document path."
        )

    return file_path