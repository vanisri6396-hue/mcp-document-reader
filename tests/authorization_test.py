from security.authorization import authorize


def test_permission(role: str, tool: str, should_allow: bool):
    print()
    print(f"Role: {role}")
    print(f"Tool: {tool}")

    try:
        authorize(role, tool)

        if should_allow:
            print("ALLOWED → PASS")
        else:
            print("ALLOWED → FAIL (should have been blocked)")

    except PermissionError as error:

        if not should_allow:
            print(f"BLOCKED → PASS | {error}")
        else:
            print(f"BLOCKED → FAIL | {error}")

    except Exception as error:
        print(f"ERROR → {error}")


print("=" * 70)
print("AUTHORIZATION / RBAC SECURITY TEST")
print("=" * 70)


# ============================================================
# READER TESTS
# ============================================================

test_permission(
    "reader",
    "read_document",
    True,
)

test_permission(
    "reader",
    "list_documents",
    True,
)

test_permission(
    "reader",
    "search_documents",
    True,
)

test_permission(
    "reader",
    "document_resource",
    True,
)

test_permission(
    "reader",
    "summarize_document",
    True,
)

test_permission(
    "reader",
    "create_document",
    False,
)

test_permission(
    "reader",
    "update_document",
    False,
)

test_permission(
    "reader",
    "delete_document",
    False,
)


# ============================================================
# EDITOR TESTS
# ============================================================

test_permission(
    "editor",
    "read_document",
    True,
)

test_permission(
    "editor",
    "list_documents",
    True,
)

test_permission(
    "editor",
    "search_documents",
    True,
)

test_permission(
    "editor",
    "create_document",
    True,
)

test_permission(
    "editor",
    "update_document",
    True,
)

test_permission(
    "editor",
    "delete_document",
    False,
)


# ============================================================
# ADMIN TESTS
# ============================================================

test_permission(
    "admin",
    "read_document",
    True,
)

test_permission(
    "admin",
    "list_documents",
    True,
)

test_permission(
    "admin",
    "search_documents",
    True,
)

test_permission(
    "admin",
    "create_document",
    True,
)

test_permission(
    "admin",
    "update_document",
    True,
)

test_permission(
    "admin",
    "delete_document",
    True,
)


# ============================================================
# INVALID ROLE
# ============================================================

test_permission(
    "guest",
    "read_document",
    False,
)


# ============================================================
# UNKNOWN TOOL
# ============================================================

test_permission(
    "admin",
    "unknown_tool",
    False,
)


print()
print("=" * 70)
print("AUTHORIZATION TEST COMPLETED")
print("=" * 70)