from security.authentication import authenticate
from config.settings import MCP_API_KEY


test_keys = [
    "",
    "wrong-key",
    MCP_API_KEY,
]


print("=" * 70)
print("AUTHENTICATION SECURITY TEST")
print("=" * 70)


for key in test_keys:
    print("\nTesting authentication...")

    try:
        authenticate(key)
        print("ALLOWED → Authentication successful.")

    except (ValueError, RuntimeError) as error:
        print(f"BLOCKED → {error}")


print()
print("=" * 70)
print("AUTHENTICATION TEST COMPLETED")
print("=" * 70)