import logging
from dataclasses import dataclass

from mcp.server.mcpserver.exceptions import ToolError


logger = logging.getLogger("DocumentMCP")


class DocumentMCPError(ToolError):
    """
    Base class for expected application-level MCP tool errors.

    These errors are intentionally subclasses of MCP ToolError so that
    MCPServer returns them to the client as:

        CallToolResult(is_error=True)

    rather than exposing an internal server exception.
    """

    error_code = "DOCUMENT_MCP_ERROR"
    retryable = False
    user_message = "The operation could not be completed."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: str | None = None,
    ):
        self.internal_message = (
            message or self.user_message
        )

        self.details = details

        # IMPORTANT:
        # Only the safe user-facing message becomes
        # the actual exception message.
        #
        # This prevents internal implementation details
        # from accidentally reaching the MCP client.
        super().__init__(
            self.user_message
        )


class ValidationError(DocumentMCPError):
    """
    Invalid user or tool input.
    """

    error_code = "VALIDATION_ERROR"
    retryable = False
    user_message = (
        "The provided input is invalid."
    )


class AuthenticationError(DocumentMCPError):
    """
    Authentication failure.
    """

    error_code = "AUTHENTICATION_ERROR"
    retryable = False
    user_message = (
        "Authentication failed."
    )


class AuthorizationError(DocumentMCPError):
    """
    Authorization failure.
    """

    error_code = "AUTHORIZATION_ERROR"
    retryable = False
    user_message = (
        "You are not authorized to perform this operation."
    )


class DocumentNotFoundError(DocumentMCPError):
    """
    Requested document does not exist.
    """

    error_code = "DOCUMENT_NOT_FOUND"
    retryable = False
    user_message = (
        "The requested document was not found."
    )


class DocumentAlreadyExistsError(DocumentMCPError):
    """
    Document already exists.
    """

    error_code = "DOCUMENT_ALREADY_EXISTS"
    retryable = False
    user_message = (
        "The document already exists."
    )


class DocumentOperationError(DocumentMCPError):
    """
    Expected document operation failure.
    """

    error_code = "DOCUMENT_OPERATION_ERROR"
    retryable = True
    user_message = (
        "The document operation could not be completed."
    )


class RateLimitError(DocumentMCPError):
    """
    Rate limit exceeded.
    """

    error_code = "RATE_LIMIT_EXCEEDED"
    retryable = True
    user_message = (
        "Too many requests. Please try again later."
    )


class TimeoutError(DocumentMCPError):
    """
    Operation exceeded its allowed time.
    """

    error_code = "TIMEOUT"
    retryable = True
    user_message = (
        "The operation timed out."
    )


class CancellationError(DocumentMCPError):
    """
    Operation was cancelled.
    """

    error_code = "CANCELLED"
    retryable = False
    user_message = (
        "The operation was cancelled."
    )


@dataclass(frozen=True)
class ErrorResponse:
    """
    Safe structured representation of an application error.
    """

    success: bool
    error_code: str
    message: str
    retryable: bool


def build_error_response(
    error: DocumentMCPError,
) -> ErrorResponse:
    """
    Convert an internal application error into
    a safe response representation.
    """

    return ErrorResponse(
        success=False,
        error_code=error.error_code,
        message=error.user_message,
        retryable=error.retryable,
    )


def log_error(
    error: Exception,
    *,
    tool_name: str | None = None,
) -> None:
    """
    Log technical error information internally.

    The caller-facing exception remains sanitized.
    """

    logger.error(
        "Tool error | tool=%s | error_type=%s | error=%s",
        tool_name or "unknown",
        type(error).__name__,
        str(error),
        exc_info=logger.isEnabledFor(
            logging.DEBUG
        ),
    )


def _message_contains(
    error: Exception,
    *phrases: str,
) -> bool:
    """
    Check whether an exception message contains
    one of the supplied phrases.
    """

    message = str(error).lower()

    return any(
        phrase.lower() in message
        for phrase in phrases
    )


def handle_tool_error(
    tool_name: str,
    error: Exception,
) -> DocumentMCPError:
    """
    Convert low-level exceptions into safe,
    categorized MCP tool errors.
    """

    # --------------------------------------------------------
    # Already classified error
    # --------------------------------------------------------

    if isinstance(
        error,
        DocumentMCPError,
    ):
        log_error(
            error,
            tool_name=tool_name,
        )

        return error

    # --------------------------------------------------------
    # Document-specific errors
    # --------------------------------------------------------

    if _message_contains(
        error,
        "not found",
        "does not exist",
    ):
        converted_error = (
            DocumentNotFoundError(
                str(error)
            )
        )

    elif _message_contains(
        error,
        "already exists",
    ):
        converted_error = (
            DocumentAlreadyExistsError(
                str(error)
            )
        )

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    elif _message_contains(
        error,
        "not authorized",
        "permission denied",
        "unauthorized",
    ):
        converted_error = (
            AuthorizationError(
                str(error)
            )
        )

    # --------------------------------------------------------
    # Rate limiting
    # --------------------------------------------------------

    elif _message_contains(
        error,
        "rate limit exceeded",
    ):
        converted_error = (
            RateLimitError(
                str(error)
            )
        )

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    elif _message_contains(
        error,
        "authentication required",
        "invalid authentication",
        "authentication failed",
        "authentication is not configured",
    ):
        converted_error = (
            AuthenticationError(
                str(error)
            )
        )

    # --------------------------------------------------------
    # Timeout
    # --------------------------------------------------------

    elif isinstance(
        error,
        TimeoutError,
    ):
        converted_error = TimeoutError(
            str(error)
        )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    elif isinstance(
        error,
        ValueError,
    ):
        converted_error = ValidationError(
            str(error)
        )

    # --------------------------------------------------------
    # PermissionError fallback
    # --------------------------------------------------------

    elif isinstance(
        error,
        PermissionError,
    ):
        converted_error = AuthorizationError(
            str(error)
        )

    # --------------------------------------------------------
    # Unexpected operation failure
    # --------------------------------------------------------

    else:
        converted_error = (
            DocumentOperationError(
                str(error)
            )
        )

    log_error(
        error,
        tool_name=tool_name,
    )

    return converted_error


def classify_error(
    error: Exception,
) -> dict:
    """
    Return machine-readable error information.
    """

    if isinstance(
        error,
        DocumentMCPError,
    ):
        return {
            "error_code": error.error_code,
            "message": error.user_message,
            "retryable": error.retryable,
        }

    return {
        "error_code": "INTERNAL_ERROR",
        "message": (
            "An unexpected error occurred."
        ),
        "retryable": False,
    }