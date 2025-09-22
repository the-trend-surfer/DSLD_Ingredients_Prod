"""
Configuration module for DLSD Evidence Collector
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the application"""

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    NCBI_API_KEY = os.getenv("NCBI_API_KEY")
    NCBI_EMAIL = os.getenv("NCBI_EMAIL", "your-email@example.com")

    # Google Sheets Configuration
    SHEET_ID_ING = "1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA"
    INGREDIENTS_RANGE = "C2:C"
    SYNONYMS_RANGE = "E2:E"
    RESULTS_SHEET = "Results_Main"

    # Processing Configuration
    BATCH_SIZE = 10
    DELAY_BETWEEN_REQUESTS = 2
    MAX_RETRIES = 3
    TIMEOUT = 30

    # Output Configuration
    OUTPUT_DIR = Path("output")
    BACKUP_DIR = Path("backup")

    # Create directories if they don't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)

    # AI Model Configuration
    MODELS = {
        "openai": {
            "primary": "gpt-5-mini",
            "fallback": "gpt-4o-mini"
        },
        "claude": {
            "primary": "claude-sonnet-4-20250514",
            "fallback": "claude-3-5-sonnet-20241022"
        },
        "gemini": {
            "primary": "gemini-2.5-flash-lite",
            "fallback": "gemini-1.5-flash"
        }
    }

    # Model priority order (first = highest priority)
    MODEL_PRIORITY = ["claude", "openai", "gemini"]

    # Allowed domains for sources
    ALLOWED_DOMAINS = [
        "nih.gov", "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov",
        "efsa.europa.eu", "fda.gov", "mskcc.org",
        "examine.com", "consumerlab.com",
        "sciencedirect.com", "nature.com", "springer.com",
        "wiley.com", "taylor francis.com", "ahcc.net",
        "wikipedia.org", "en.wikipedia.org"
    ]

    # Source priority levels
    SOURCE_LEVELS = {
        1: ["nih.gov", "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "efsa.europa.eu", "fda.gov", "mskcc.org"],
        2: ["nature.com", "sciencedirect.com", "springer.com", "en.wikipedia.org", "wikipedia.org"],
        3: ["examine.com", "wiley.com"],
        4: ["consumerlab.com", "ahcc.net"]
    }

# Validation
def validate_config():
    """Validate required configuration"""
    errors = []
    warnings = []

    # Check if at least one AI API is available
    ai_apis = []
    if Config.OPENAI_API_KEY:
        ai_apis.append("OpenAI")
    if Config.CLAUDE_API_KEY:
        ai_apis.append("Claude")
    if Config.GEMINI_API_KEY:
        ai_apis.append("Gemini")

    if not ai_apis:
        errors.append("At least one AI API key is required (OpenAI, Claude, or Gemini)")
    else:
        warnings.append(f"Available AI APIs: {', '.join(ai_apis)}")

    if not Config.NCBI_EMAIL or Config.NCBI_EMAIL == "your-email@example.com":
        errors.append("NCBI_EMAIL must be set to a valid email")

    if warnings:
        for warning in warnings:
            print(f"[WARNING] {warning}")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

    return True