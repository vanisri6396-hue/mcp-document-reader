from security.validation import get_document_path


test_paths = [
    "report.txt",
    "../report.txt",
    "../../report.txt",
    "../../../report.txt",
    "..\\report.txt",
    "..\\..\\report.txt",
    "folder/report.txt",
    "folder\\report.txt",
    "secret.pdf",
    "",
    ".",
    "..",
]


for doc_id in test_paths:
    print(f"\nTesting: {doc_id}")

    try:
        path = get_document_path(doc_id)
        print(f"ALLOWED → {path}")
    except ValueError as e:
        print(f"BLOCKED → {e}")