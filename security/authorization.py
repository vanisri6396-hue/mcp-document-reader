import logging
import os


from config.settings import DEFAULT_ROLE


logger = logging.getLogger(
    "DocumentMCP"
)


# ============================================================
# ROLES
# ============================================================


VALID_ROLES = {
    "reader",
    "editor",
    "admin",
}


# ============================================================
# TOOL PERMISSIONS
# ============================================================


TOOL_PERMISSIONS = {

    # -----------------------------
    # READ OPERATIONS
    # -----------------------------

    "read_document": {
        "reader",
        "editor",
        "admin",
    },

    "list_documents": {
        "reader",
        "editor",
        "admin",
    },

    "search_documents": {
        "reader",
        "editor",
        "admin",
    },

    "document_resource": {
        "reader",
        "editor",
        "admin",
    },

    "summarize_document": {
        "reader",
        "editor",
        "admin",
    },

    # -----------------------------
    # WRITE OPERATIONS
    # -----------------------------

    "create_document": {
        "editor",
        "admin",
    },

    "update_document": {
        "editor",
        "admin",
    },

    # -----------------------------
    # DESTRUCTIVE OPERATION
    # -----------------------------

    "delete_document": {
        "admin",
    },
}


# ============================================================
# ROLE VALIDATION
# ============================================================


def validate_role(
    role: str,
) -> str:

    if not isinstance(role, str):

        raise ValueError(
            "Invalid role."
        )

    role = role.strip().lower()

    if role not in VALID_ROLES:

        raise ValueError(
            "Invalid role."
        )

    return role


# ============================================================
# AUTHORIZATION
# ============================================================


def authorize(
    role: str,
    tool_name: str,
) -> None:

    role = validate_role(
        role
    )

    if (
        not isinstance(tool_name, str)
        or not tool_name.strip()
    ):

        raise ValueError(
            "Tool name cannot be empty."
        )

    tool_name = tool_name.strip()

    allowed_roles = (
        TOOL_PERMISSIONS.get(
            tool_name
        )
    )

    if allowed_roles is None:

        raise ValueError(
            "Unknown tool."
        )

    if role not in allowed_roles:

        raise PermissionError(
            f"Role '{role}' is not authorized "
            f"to use '{tool_name}'."
        )

    logger.info(
        "Authorization successful | role=%s | tool=%s",
        role,
        tool_name,
    )


# ============================================================
# SECURITY CONTEXT
# ============================================================


def get_current_role() -> str:

    role = os.getenv(
        "MCP_USER_ROLE",
        DEFAULT_ROLE,
    )

    return validate_role(
        role
    )


# ============================================================
# TOOL PERMISSION CHECK
# ============================================================


def check_tool_permission(
    tool_name: str,
) -> None:

    role = get_current_role()

    authorize(
        role,
        tool_name,
    )