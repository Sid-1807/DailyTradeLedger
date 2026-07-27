import os
from datetime import datetime
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS", "")
PDF_PASSWORD = os.getenv("PDF_PASSWORD", "")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "custcare@idbicapital.com")
SUBJECT_KEYWORD = os.getenv("SUBJECT_KEYWORD", "Common Contract Note")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
TRADES_DIR = os.path.join(BASE_DIR, "trades")

for directory in [DOWNLOADS_DIR, LOGS_DIR, TRADES_DIR]:
    os.makedirs(directory, exist_ok=True)

def get_financial_year(dt: datetime) -> str:
    """
    Calculates the Indian Financial Year string (Apr 1 - Mar 31).
    Example: 2026-07-23 -> 'FY2026-27'
             2026-02-15 -> 'FY2025-26'
    """
    if dt.month >= 4:
        start_year = dt.year
        end_year = (dt.year + 1) % 100
    else:
        start_year = dt.year - 1
        end_year = dt.year % 100
    
    return f"FY{start_year}-{end_year:02d}"
