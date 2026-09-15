import os
from dataclasses import dataclass

from security.authentication import authenticate
from security.authorization import (
    authorize,
    validate_role,
)
from security.rate_limit import check_rate_limit


@dataclass(frozen=True)
class SecurityContext:
    """
    Security information associated with the current MCP request.

    This is a local learning-project security context.
    In a production remote MCP server, identity and credentials
    should come from the authenticated request/session.
    """

    identity: str
    role: str


def get_current_identity() -> str:
    """
    Return the identity associated with the current MCP request.

    For this local learning project, identity is supplied
    through the MCP_USER_ID environment variable.
    """

    identity = os.getenv("MCP_USER_ID")

    if not identity:
        raise ValueError(
            "MCP user identity is not configured."
        )

    identity = identity.strip()

    if not identity:
        raise ValueError(
            "MCP user identity cannot be empty."
        )

    return identity


def authenticate_request() -> str:
    """
    Authenticate the current request and return its identity.

    NOTE:
    This environment-based API-key mechanism is only a
    local learning/demo mechanism. It is not remote
    production authentication.
    """

    api_key = os.getenv("MCP_API_KEY")

    authenticate(api_key)

    return get_current_identity()


def get_security_context() -> SecurityContext:
    """
    Build the security context for the current request.

    Security steps:

    1. Authentication
    2. Identity resolution
    3. Role validation
    """

    identity = authenticate_request()

    role = os.getenv(
        "MCP_USER_ROLE",
        "reader",
    )

    role = validate_role(role)

    return SecurityContext(
        identity=identity,
        role=role,
    )


def secure_request(tool_name: str) -> SecurityContext:
    """
    Apply all security controls before executing an MCP operation.

    Security order:

    1. Validate tool name
    2. Authenticate request
    3. Resolve identity
    4. Apply rate limiting
    5. Resolve and validate role
    6. Authorize the requested tool

    Returns:
        SecurityContext containing the authenticated
        identity and authorized role.
    """

    if not isinstance(tool_name, str):
        raise ValueError(
            "Tool name must be text."
        )

    tool_name = tool_name.strip()

    if not tool_name:
        raise ValueError(
            "Tool name cannot be empty."
        )

    security_context = get_security_context()

    check_rate_limit(
        security_context.identity
    )

    authorize(
        security_context.role,
        tool_name,
    )

    return security_context