import logging

from config.settings import DOCUMENTS_DIR

from models.document import DocumentInfo

from security.validation import (
    get_document_path,
    validate_document_name,
    validate_document_content,
)


logger = logging.getLogger(
    "DocumentMCP"
)


# ============================================================
# CREATE
# ============================================================


def repository_create_document(
    name: str,
    content: str,
) -> None:

    name = validate_document_name(
        name
    )

    content = validate_document_content(
        content
    )

    file_path = get_document_path(
        name
    )

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


# ============================================================
# READ
# ============================================================


def repository_read_document(
    doc_id: str,
) -> str:

    file_path = get_document_path(
        doc_id
    )

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
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        logger.exception(
            "Invalid UTF-8 document: %s",
            doc_id,
        )

        raise ValueError(
            "Document could not be decoded "
            "as UTF-8."
        )

    except OSError:

        logger.exception(
            "Failed to read document: %s",
            doc_id,
        )

        raise ValueError(
            "Unable to read document."
        )


# ============================================================
# UPDATE
# ============================================================


def repository_update_document(
    name: str,
    content: str,
) -> None:

    name = validate_document_name(
        name
    )

    content = validate_document_content(
        content
    )

    file_path = get_document_path(
        name
    )

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


# ============================================================
# DELETE
# ============================================================


def repository_delete_document(
    doc_id: str,
) -> None:

    file_path = get_document_path(
        doc_id
    )

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


# ============================================================
# LIST
# ============================================================


def repository_list_documents() -> list[DocumentInfo]:

    documents: list[DocumentInfo] = []

    try:

        for file_path in DOCUMENTS_DIR.iterdir():

            if not file_path.is_file():
                continue

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
        key=lambda document:
        document.name.lower()
    )

    return documents