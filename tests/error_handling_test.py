from security.errors import (
    DocumentMCPError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    DocumentOperationError,
    RateLimitError,
    TimeoutError,
    CancellationError,
    build_error_response,
    classify_error,
    handle_tool_error,
)


def test_error_hierarchy():
    error = ValidationError()

    assert isinstance(
        error,
        DocumentMCPError,
    )

    print(
        "ERROR HIERARCHY TEST: PASS"
    )


def test_validation_error():
    error = ValidationError()

    assert (
        error.error_code
        == "VALIDATION_ERROR"
    )

    assert error.retryable is False

    response = build_error_response(
        error
    )

    assert response.success is False

    assert (
        response.error_code
        == "VALIDATION_ERROR"
    )

    assert response.retryable is False

    print(
        "VALIDATION ERROR TEST: PASS"
    )


def test_authentication_error():
    error = AuthenticationError()

    assert (
        error.error_code
        == "AUTHENTICATION_ERROR"
    )

    assert error.retryable is False

    print(
        "AUTHENTICATION ERROR TEST: PASS"
    )


def test_authorization_error():
    error = AuthorizationError()

    assert (
        error.error_code
        == "AUTHORIZATION_ERROR"
    )

    assert error.retryable is False

    print(
        "AUTHORIZATION ERROR TEST: PASS"
    )


def test_not_found_error():
    error = DocumentNotFoundError()

    assert (
        error.error_code
        == "DOCUMENT_NOT_FOUND"
    )

    assert error.retryable is False

    print(
        "DOCUMENT NOT FOUND ERROR TEST: PASS"
    )


def test_already_exists_error():
    error = DocumentAlreadyExistsError()

    assert (
        error.error_code
        == "DOCUMENT_ALREADY_EXISTS"
    )

    assert error.retryable is False

    print(
        "DOCUMENT ALREADY EXISTS ERROR TEST: PASS"
    )


def test_retryable_operation_error():
    error = DocumentOperationError()

    assert (
        error.error_code
        == "DOCUMENT_OPERATION_ERROR"
    )

    assert error.retryable is True

    print(
        "RETRYABLE OPERATION ERROR TEST: PASS"
    )


def test_rate_limit_error():
    error = RateLimitError()

    assert (
        error.error_code
        == "RATE_LIMIT_EXCEEDED"
    )

    assert error.retryable is True

    print(
        "RATE LIMIT ERROR TEST: PASS"
    )


def test_timeout_error():
    error = TimeoutError()

    assert (
        error.error_code
        == "TIMEOUT"
    )

    assert error.retryable is True

    print(
        "TIMEOUT ERROR TEST: PASS"
    )


def test_cancellation_error():
    error = CancellationError()

    assert (
        error.error_code
        == "CANCELLED"
    )

    assert error.retryable is False

    print(
        "CANCELLATION ERROR TEST: PASS"
    )


def test_error_classification():
    error = RateLimitError()

    result = classify_error(
        error
    )

    assert (
        result["error_code"]
        == "RATE_LIMIT_EXCEEDED"
    )

    assert result["retryable"] is True

    print(
        "ERROR CLASSIFICATION TEST: PASS"
    )


def test_unexpected_error_sanitization():
    error = RuntimeError(
        "Internal database connection "
        "password=super-secret"
    )

    result = classify_error(
        error
    )

    assert (
        result["error_code"]
        == "INTERNAL_ERROR"
    )

    assert result["retryable"] is False

    assert (
        result["message"]
        == "An unexpected error occurred."
    )

    assert (
        "super-secret"
        not in result["message"]
    )

    print(
        "UNEXPECTED ERROR SANITIZATION TEST: PASS"
    )


def test_value_error_conversion():
    error = ValueError(
        "Document name cannot contain "
        "path separators."
    )

    converted = handle_tool_error(
        "read_document",
        error,
    )

    assert isinstance(
        converted,
        ValidationError,
    )

    assert (
        converted.error_code
        == "VALIDATION_ERROR"
    )

    print(
        "VALUE ERROR CONVERSION TEST: PASS"
    )


def test_not_found_conversion():
    error = ValueError(
        "Document 'missing.txt' not found."
    )

    converted = handle_tool_error(
        "read_document",
        error,
    )

    assert isinstance(
        converted,
        DocumentNotFoundError,
    )

    assert (
        converted.error_code
        == "DOCUMENT_NOT_FOUND"
    )

    print(
        "NOT FOUND CONVERSION TEST: PASS"
    )


def test_already_exists_conversion():
    error = ValueError(
        "Document 'report.txt' already exists."
    )

    converted = handle_tool_error(
        "create_document",
        error,
    )

    assert isinstance(
        converted,
        DocumentAlreadyExistsError,
    )

    assert (
        converted.error_code
        == "DOCUMENT_ALREADY_EXISTS"
    )

    print(
        "ALREADY EXISTS CONVERSION TEST: PASS"
    )


def test_authorization_conversion():
    error = PermissionError(
        "Role 'reader' is not authorized "
        "to use 'delete_document'."
    )

    converted = handle_tool_error(
        "delete_document",
        error,
    )

    assert isinstance(
        converted,
        AuthorizationError,
    )

    assert (
        converted.error_code
        == "AUTHORIZATION_ERROR"
    )

    print(
        "AUTHORIZATION CONVERSION TEST: PASS"
    )


def test_rate_limit_conversion():
    error = PermissionError(
        "Rate limit exceeded. "
        "Maximum 5 requests are allowed."
    )

    converted = handle_tool_error(
        "read_document",
        error,
    )

    assert isinstance(
        converted,
        RateLimitError,
    )

    assert (
        converted.error_code
        == "RATE_LIMIT_EXCEEDED"
    )

    assert converted.retryable is True

    print(
        "RATE LIMIT CONVERSION TEST: PASS"
    )


def test_safe_exception_message():
    internal_error = ValueError(
        "Internal filesystem path: "
        "C:\\secret\\private\\document.txt"
    )

    converted = handle_tool_error(
        "read_document",
        internal_error,
    )

    assert (
        str(converted)
        == converted.user_message
    )

    assert (
        "C:\\secret"
        not in str(converted)
    )

    print(
        "SAFE EXCEPTION MESSAGE TEST: PASS"
    )


def main():
    print()
    print(
        "========================================"
    )
    print(
        "LEVEL 8.9 — ERROR HANDLING TEST SUITE"
    )
    print(
        "========================================"
    )

    test_error_hierarchy()
    test_validation_error()
    test_authentication_error()
    test_authorization_error()
    test_not_found_error()
    test_already_exists_error()
    test_retryable_operation_error()
    test_rate_limit_error()
    test_timeout_error()
    test_cancellation_error()
    test_error_classification()
    test_unexpected_error_sanitization()
    test_value_error_conversion()
    test_not_found_conversion()
    test_already_exists_conversion()
    test_authorization_conversion()
    test_rate_limit_conversion()
    test_safe_exception_message()

    print()
    print(
        "========================================"
    )
    print(
        "LEVEL 8.9 ERROR MODEL: PASS"
    )
    print(
        "========================================"
    )


if __name__ == "__main__":
    main()