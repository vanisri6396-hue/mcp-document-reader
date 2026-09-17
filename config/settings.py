from pathlib import Path
import os

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = BASE_DIR / "documents"

DOCUMENTS_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# SECURITY CONFIGURATION
# ============================================================

MAX_DOCUMENT_CHARS = 100_000

MAX_DOCUMENT_BYTES = 200_000

MCP_API_KEY = os.getenv(
    "MCP_API_KEY"
)

DEFAULT_ROLE = "reader"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")