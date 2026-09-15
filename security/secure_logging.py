import logging
from typing import Any


SENSITIVE_FIELDS = {
    "api_key",
    "password",
    "token",
    "secret",
    "authorization",
    "content",
}


def sanitize_value(value: Any) -> str:
    """
    Convert potentially sensitive values into safe log representations.
    """

    if value is None:
        return "None"

    if isinstance(value, dict):
        sanitized = {}

        for key, item in value.items():

            if str(key).lower() in SENSITIVE_FIELDS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_value(item)

        return str(sanitized)

    if isinstance(value, str):

        # Never log extremely large strings.
        if len(value) > 200:
            return f"<text length={len(value)}>"

        return value

    return str(value)


def log_tool_call(
    logger: logging.Logger,
    tool_name: str,
    arguments: dict | None = None,
) -> None:
    """
    Safely log an MCP tool invocation.

    Sensitive fields are redacted.
    """

    safe_arguments = sanitize_value(arguments or {})

    logger.info(
        "Tool called: %s | arguments=%s",
        tool_name,
        safe_arguments,
    )


def log_permission_denied(
    logger: logging.Logger,
    role: str,
    tool_name: str,
) -> None:
    """
    Log authorization failures without exposing sensitive data.
    """

    logger.warning(
        "Permission denied: role=%s | tool=%s",
        role,
        tool_name,
    )


def log_tool_error(
    logger: logging.Logger,
    tool_name: str,
) -> None:
    """
    Log a tool failure without logging user input or document content.
    """

    logger.error(
        "Tool failed: %s",
        tool_name,
    )