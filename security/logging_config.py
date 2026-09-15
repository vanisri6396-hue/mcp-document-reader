import logging


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def configure_logging() -> logging.Logger:
    """
    Configure centralized secure logging for the MCP server.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
    )

    return logging.getLogger("DocumentMCP")


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger for a specific MCP component.
    """

    return logging.getLogger(f"DocumentMCP.{name}")