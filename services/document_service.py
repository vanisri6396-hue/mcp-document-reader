import logging

from config.settings import DOCUMENTS_DIR

from models.document import (
    CreateDocumentInput,
    UpdateDocumentInput,
    DocumentList,
    OperationResult,
    SearchResult,
)

from repository.document_repository import (
    repository_create_document,
    repository_read_document,
    repository_update_document,
    repository_delete_document,
    repository_list_documents,
)

from security.validation import (
    validate_document_name,
)


logger = logging.getLogger(
    "DocumentMCP"
)


# ============================================================
# CREATE
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


# ============================================================
# READ
# ============================================================


def service_read_document(
    doc_id: str,
    max_chars: int,
) -> str:

    if max_chars < 100 or max_chars > 10000:

        raise ValueError(
            "max_chars must be between "
            "100 and 10000."
        )

    doc_id = validate_document_name(
        doc_id
    )

    content = repository_read_document(
        doc_id
    )

    return content[:max_chars]


# ============================================================
# UPDATE
# ============================================================


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


# ============================================================
# DELETE
# ============================================================


def service_delete_document(
    doc_id: str,
) -> OperationResult:

    doc_id = validate_document_name(
        doc_id
    )

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


# ============================================================
# LIST
# ============================================================


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
            "page_size must be between "
            "1 and 100."
        )

    all_documents = (
        repository_list_documents()
    )

    total_documents = len(
        all_documents
    )

    total_pages = (
        (
            total_documents
            + page_size
            - 1
        )
        // page_size
    )

    start_index = (
        (page - 1)
        * page_size
    )

    end_index = (
        start_index
        + page_size
    )

    page_documents = all_documents[
        start_index:end_index
    ]

    has_next_page = (
        page < total_pages
    )

    return DocumentList(
        documents=page_documents,
        page=page,
        page_size=page_size,
        total_documents=total_documents,
        total_pages=total_pages,
        has_next_page=has_next_page,
    )


# ============================================================
# SEARCH
# ============================================================


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
            "Search query cannot exceed "
            "200 characters."
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

                searchable_content = (
                    content.lower()
                )

                searchable_query = (
                    query.lower()
                )

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