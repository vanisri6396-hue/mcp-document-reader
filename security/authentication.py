from config.settings import MCP_API_KEY


def authenticate(
    api_key: str,
) -> None:
    """
    Validate an API key.

    This is prepared for authenticated
    remote MCP deployments.
    """

    if not MCP_API_KEY:

        raise RuntimeError(
            "Authentication is not configured."
        )

    if not api_key:

        raise ValueError(
            "Authentication required."
        )

    if api_key != MCP_API_KEY:

        raise ValueError(
            "Invalid authentication credentials."
        )