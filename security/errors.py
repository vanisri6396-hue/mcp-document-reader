import logging


logger = logging.getLogger(
    "DocumentMCP"
)


def handle_tool_error(
    tool_name: str,
    error: Exception,
) -> ValueError:
    """
    Log detailed internal information while
    returning controlled errors to the client.
    """

    logger.error(
        "%s failed: %s",
        tool_name,
        error,
        exc_info=True,
    )

    # Don't expose authorization details
    if isinstance(
        error,
        PermissionError,
    ):

        return ValueError(
            "Permission denied."
        )

    # Validation errors are safe to expose
    if isinstance(
        error,
        ValueError,
    ):

        return ValueError(
            str(error)
        )

    # Hide unexpected internal errors
    return ValueError(
        f"{tool_name} failed. "
        "Please try again."
    )