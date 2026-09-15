import logging

from security.logging_config import configure_logging
from security.secure_logging import (
    sanitize_value,
    log_tool_call,
    log_permission_denied,
    log_tool_error,
)


logger = configure_logging()


print("=" * 70)
print("SECURE LOGGING TEST")
print("=" * 70)


# ============================================================
# TEST 1 — NORMAL VALUE
# ============================================================

print()
print("Test 1: Normal values")

result = sanitize_value("report.txt")

print(f"Input: report.txt")
print(f"Output: {result}")


# ============================================================
# TEST 2 — API KEY REDACTION
# ============================================================

print()
print("Test 2: API key redaction")

data = {
    "name": "report.txt",
    "api_key": "super-secret-api-key",
}

result = sanitize_value(data)

print(f"Sanitized output: {result}")


# ============================================================
# TEST 3 — CONTENT REDACTION
# ============================================================

print()
print("Test 3: Document content protection")

data = {
    "name": "report.txt",
    "content": "This is sensitive document content.",
}

result = sanitize_value(data)

print(f"Sanitized output: {result}")


# ============================================================
# TEST 4 — LARGE CONTENT
# ============================================================

print()
print("Test 4: Large content protection")

large_content = "A" * 1000

result = sanitize_value(large_content)

print(f"Sanitized output: {result}")


# ============================================================
# TEST 5 — TOOL LOGGING
# ============================================================

print()
print("Test 5: Tool logging")

log_tool_call(
    logger,
    "create_document",
    {
        "name": "report.txt",
        "content": "Sensitive document content",
        "api_key": "secret-key",
    },
)


# ============================================================
# TEST 6 — AUTHORIZATION LOGGING
# ============================================================

print()
print("Test 6: Permission-denied logging")

log_permission_denied(
    logger,
    "reader",
    "delete_document",
)


# ============================================================
# TEST 7 — ERROR LOGGING
# ============================================================

print()
print("Test 7: Safe error logging")

log_tool_error(
    logger,
    "read_document",
)


print()
print("=" * 70)
print("SECURE LOGGING TEST COMPLETED")
print("=" * 70)