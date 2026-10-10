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

def get_quarter_and_fy(dt: datetime) -> tuple[str, str]:
    """
    Returns (quarter_str, fy_str).
    Example: 2026-05-15 -> ('Q1', 'FY2026-27')
             2026-08-20 -> ('Q2', 'FY2026-27')
             2026-10-05 -> ('Q3', 'FY2026-27')
             2027-01-15 -> ('Q4', 'FY2026-27')
    """
    if dt.month in (4, 5, 6):
        q = "Q1"
        start_year = dt.year
    elif dt.month in (7, 8, 9):
        q = "Q2"
        start_year = dt.year
    elif dt.month in (10, 11, 12):
        q = "Q3"
        start_year = dt.year
    else:
        q = "Q4"
        start_year = dt.year - 1
        
    end_year = (start_year + 1) % 100
    fy_str = f"FY{start_year}-{end_year:02d}"
    return q, fy_str

def get_financial_year(dt: datetime) -> str:
    """
    Calculates the Indian Financial Year string (Apr 1 - Mar 31).
    Example: 2026-07-23 -> 'FY2026-27'
             2026-02-15 -> 'FY2025-26'
    """
    _, fy_str = get_quarter_and_fy(dt)
    return fy_str
