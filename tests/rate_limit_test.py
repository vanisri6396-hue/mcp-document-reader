from security.rate_limit import (
    MAX_REQUESTS,
    WINDOW_SECONDS,
    check_rate_limit,
    reset_rate_limit,
)


IDENTITY = "test-user"


print("=" * 70)
print("RATE LIMIT SECURITY TEST")
print("=" * 70)

reset_rate_limit(IDENTITY)


# ============================================================
# TEST ALLOWED REQUESTS
# ============================================================

print()
print("Testing allowed requests...")

for request_number in range(1, MAX_REQUESTS + 1):

    try:
        check_rate_limit(IDENTITY)
        print(
            f"Request {request_number}: "
            f"ALLOWED → PASS"
        )

    except PermissionError as error:
        print(
            f"Request {request_number}: "
            f"BLOCKED → FAIL | {error}"
        )


# ============================================================
# TEST RATE LIMIT
# ============================================================

print()
print("Testing request beyond the limit...")

try:
    check_rate_limit(IDENTITY)

    print(
        "Extra request: "
        "ALLOWED → FAIL (should have been blocked)"
    )

except PermissionError as error:

    print(
        f"Extra request: "
        f"BLOCKED → PASS | {error}"
    )


print()
print("=" * 70)
print(
    f"RATE LIMIT: {MAX_REQUESTS} requests "
    f"per {WINDOW_SECONDS} seconds"
)
print("=" * 70)

print()
print("RATE LIMIT TEST COMPLETED")
print("=" * 70)