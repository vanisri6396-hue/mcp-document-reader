from security.validation import validate_document_content


test_contents = [
    "Hello MCP",
    "",
    "   ",
    "Hello\x00World",
    "A" * 100_001,
]


for content in test_contents:
    print("\nTesting content...")

    try:
        validate_document_content(content)
        print("ALLOWED")
    except ValueError as e:
        print(f"BLOCKED → {e}")