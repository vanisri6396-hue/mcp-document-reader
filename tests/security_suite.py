import os

from security.validation import (
    get_document_path,
    validate_document_name,
    validate_document_content,
)

from security.authentication import authenticate
from security.authorization import check_tool_permission
from security.rate_limit import (
    MAX_REQUESTS,
    check_rate_limit,
    reset_rate_limit,
)

from security.secure_logging import sanitize_value
from config.settings import MCP_API_KEY


PASSED = 0
FAILED = 0


def test(name: str, expected_exception=None, function=None):
    global PASSED, FAILED

    print(f"\n[TEST] {name}")

    try:
        function()

        if expected_exception is None:
            print("PASS")
            PASSED += 1
        else:
            print(
                f"FAIL | Expected {expected_exception.__name__}, "
                "but operation succeeded."
            )
            FAILED += 1

    except Exception as error:

        if expected_exception and isinstance(
            error,
            expected_exception,
        ):
            print(
                f"PASS | Blocked safely: {error}"
            )
            PASSED += 1

        else:
            print(
                f"FAIL | Unexpected error: {error}"
            )
            FAILED += 1


def set_test_role(role: str):
    """Set the role used by the MCP authorization layer."""
    os.environ["MCP_USER_ROLE"] = role


print("=" * 70)
print("MCP SECURITY TEST SUITE")
print("=" * 70)


# ============================================================
# 1. PATH TRAVERSAL TESTS
# ============================================================

print("\n" + "=" * 70)
print("1. PATH TRAVERSAL TESTING")
print("=" * 70)

test(
    "Normal document path",
    function=lambda: get_document_path(
        "report.txt"
    ),
)

test(
    "Parent directory traversal",
    expected_exception=ValueError,
    function=lambda: get_document_path(
        "../report.txt"
    ),
)

test(
    "Deep path traversal",
    expected_exception=ValueError,
    function=lambda: get_document_path(
        "../../secret.txt"
    ),
)

test(
    "Windows path traversal",
    expected_exception=ValueError,
    function=lambda: get_document_path(
        "..\\secret.txt"
    ),
)

test(
    "Nested path",
    expected_exception=ValueError,
    function=lambda: get_document_path(
        "folder/report.txt"
    ),
)


# ============================================================
# 2. FILENAME VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("2. FILENAME VALIDATION TESTING")
print("=" * 70)

test(
    "Valid TXT filename",
    function=lambda: validate_document_name(
        "notes.txt"
    ),
)

test(
    "Empty filename",
    expected_exception=ValueError,
    function=lambda: validate_document_name(
        ""
    ),
)

test(
    "Directory name",
    expected_exception=ValueError,
    function=lambda: validate_document_name(
        "."
    ),
)

test(
    "Parent directory name",
    expected_exception=ValueError,
    function=lambda: validate_document_name(
        ".."
    ),
)

test(
    "PDF file",
    expected_exception=ValueError,
    function=lambda: validate_document_name(
        "document.pdf"
    ),
)

test(
    "Executable file",
    expected_exception=ValueError,
    function=lambda: validate_document_name(
        "malware.exe"
    ),
)


# ============================================================
# 3. CONTENT SECURITY
# ============================================================

print("\n" + "=" * 70)
print("3. CONTENT SECURITY TESTING")
print("=" * 70)

test(
    "Normal content",
    function=lambda: validate_document_content(
        "Hello MCP"
    ),
)

test(
    "Empty content",
    expected_exception=ValueError,
    function=lambda: validate_document_content(
        ""
    ),
)

test(
    "Whitespace-only content",
    expected_exception=ValueError,
    function=lambda: validate_document_content(
        "   "
    ),
)

test(
    "Null byte",
    expected_exception=ValueError,
    function=lambda: validate_document_content(
        "Hello\x00World"
    ),
)

test(
    "Oversized content",
    expected_exception=ValueError,
    function=lambda: validate_document_content(
        "A" * 100_001
    ),
)


# ============================================================
# 4. AUTHENTICATION TESTING
# ============================================================

print("\n" + "=" * 70)
print("4. AUTHENTICATION TESTING")
print("=" * 70)

test(
    "Missing API key",
    expected_exception=ValueError,
    function=lambda: authenticate(""),
)

test(
    "Incorrect API key",
    expected_exception=ValueError,
    function=lambda: authenticate(
        "wrong-key"
    ),
)

if MCP_API_KEY:

    test(
        "Correct API key",
        function=lambda: authenticate(
            MCP_API_KEY
        ),
    )

else:

    print(
        "\n[INFO] MCP_API_KEY is not configured."
    )


# ============================================================
# 5. AUTHORIZATION TESTING
# ============================================================

print("\n" + "=" * 70)
print("5. AUTHORIZATION TESTING")
print("=" * 70)


# -----------------------------
# READER
# -----------------------------

set_test_role("reader")

test(
    "Reader can read",
    function=lambda: check_tool_permission(
        "read_document"
    ),
)

test(
    "Reader cannot create",
    expected_exception=PermissionError,
    function=lambda: check_tool_permission(
        "create_document"
    ),
)

test(
    "Reader cannot update",
    expected_exception=PermissionError,
    function=lambda: check_tool_permission(
        "update_document"
    ),
)

test(
    "Reader cannot delete",
    expected_exception=PermissionError,
    function=lambda: check_tool_permission(
        "delete_document"
    ),
)


# -----------------------------
# EDITOR
# -----------------------------

set_test_role("editor")

test(
    "Editor can read",
    function=lambda: check_tool_permission(
        "read_document"
    ),
)

test(
    "Editor can create",
    function=lambda: check_tool_permission(
        "create_document"
    ),
)

test(
    "Editor can update",
    function=lambda: check_tool_permission(
        "update_document"
    ),
)

test(
    "Editor cannot delete",
    expected_exception=PermissionError,
    function=lambda: check_tool_permission(
        "delete_document"
    ),
)


# -----------------------------
# ADMIN
# -----------------------------

set_test_role("admin")

test(
    "Admin can read",
    function=lambda: check_tool_permission(
        "read_document"
    ),
)

test(
    "Admin can create",
    function=lambda: check_tool_permission(
        "create_document"
    ),
)

test(
    "Admin can update",
    function=lambda: check_tool_permission(
        "update_document"
    ),
)

test(
    "Admin can delete",
    function=lambda: check_tool_permission(
        "delete_document"
    ),
)


# -----------------------------
# INVALID ROLE
# -----------------------------

set_test_role("guest")

test(
    "Invalid role rejected",
    expected_exception=ValueError,
    function=lambda: check_tool_permission(
        "read_document"
    ),
)


# -----------------------------
# UNKNOWN TOOL
# -----------------------------

set_test_role("admin")

test(
    "Unknown tool rejected",
    expected_exception=ValueError,
    function=lambda: check_tool_permission(
        "unknown_tool"
    ),
)


# ============================================================
# 6. RATE LIMITING
# ============================================================

print("\n" + "=" * 70)
print("6. RATE LIMIT SECURITY TESTING")
print("=" * 70)

RATE_LIMIT_IDENTITY = "security-suite-user"

reset_rate_limit(
    RATE_LIMIT_IDENTITY
)

for request_number in range(
    1,
    MAX_REQUESTS + 1,
):

    test(
        f"Rate-limit request {request_number}",
        function=lambda: check_rate_limit(
            RATE_LIMIT_IDENTITY
        ),
    )


test(
    "Request beyond rate limit",
    expected_exception=PermissionError,
    function=lambda: check_rate_limit(
        RATE_LIMIT_IDENTITY
    ),
)


# ============================================================
# 7. SECURE LOGGING
# ============================================================

print("\n" + "=" * 70)
print("7. SECURE LOGGING TESTING")
print("=" * 70)


test(
    "Normal value remains visible",
    function=lambda: (
        sanitize_value(
            "report.txt"
        ) == "report.txt"
        or (_ for _ in ()).throw(
            AssertionError(
                "Normal value was changed."
            )
        )
    ),
)


test(
    "API key is redacted",
    function=lambda: (
        "[REDACTED]"
        in sanitize_value(
            {
                "api_key":
                    "super-secret-key"
            }
        )
        or (_ for _ in ()).throw(
            AssertionError(
                "API key was not redacted."
            )
        )
    ),
)


test(
    "Document content is redacted",
    function=lambda: (
        "[REDACTED]"
        in sanitize_value(
            {
                "content":
                    "Sensitive document content"
            }
        )
        or (_ for _ in ()).throw(
            AssertionError(
                "Document content was not redacted."
            )
        )
    ),
)


test(
    "Large content is protected",
    function=lambda: (
        "<text length=1000>"
        == sanitize_value(
            "A" * 1000
        )
        or (_ for _ in ()).throw(
            AssertionError(
                "Large content was not protected."
            )
        )
    ),
)


# ============================================================
# RESTORE DEFAULT ROLE
# ============================================================

os.environ["MCP_USER_ROLE"] = "reader"


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 70)
print("SECURITY TEST SUMMARY")
print("=" * 70)

print(f"PASSED : {PASSED}")
print(f"FAILED : {FAILED}")
print(f"TOTAL  : {PASSED + FAILED}")

print()

if FAILED == 0:

    print("SECURITY STATUS: PASS")
    print(
        "All security tests passed successfully."
    )

else:

    print("SECURITY STATUS: FAIL")
    print(
        "One or more security tests failed."
    )

print("=" * 70)