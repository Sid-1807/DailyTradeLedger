# Daily Trade Ledger Agent

An automated Python CLI agent that connects to Gmail via IMAP, retrieves daily stock broker PDF contract notes (specifically IDBI Capital), decrypts them, extracts trade details, and logs Buy and Sell transactions into separate, beautifully styled Excel ledgers organized by Financial Year.

---

## 🌟 Key Features

- 📧 **Automated Gmail Fetcher**: Connects securely via IMAP over SSL to search and download daily PDF contract notes.
- 🎯 **Strict Filtering**:
  - Restricts search strictly to `custcare@idbicapital.com` with email subject containing `"Common Contract Note"`.
  - Downloads **only PDF attachments** (`.pdf`), ignoring all marketing/statement emails and non-PDF files.
- 🔓 **Encrypted PDF Reader**: Automatically decrypts password-protected PDF contract notes (e.g. using PAN number).
- 📊 **Quarterly & Financial Year Excel Ledgers**:
  - Automatically calculates Quarter and Indian Financial Year (e.g., Apr–Jun $\rightarrow$ `Q1`, Jul–Sep $\rightarrow$ `Q2`, Oct–Dec $\rightarrow$ `Q3`, Jan–Mar $\rightarrow$ `Q4`).
  - Maintains separate workbooks per quarter: `Buy_Trades_Q1_FY2026-27.xlsx`, `Sell_Trades_Q1_FY2026-27.xlsx`, `Buy_Trades_Q2_FY2026-27.xlsx`, `Sell_Trades_Q2_FY2026-27.xlsx`, etc.
- 🎨 **Excel Formatting & Styling**:
  - Dates formatted as `dd-mm-yy`.
  - Order numbers & Trade numbers explicitly saved as Text (`@`) to prevent scientific notation.
  - Number & currency formatting (`₹#,##0.00`) with auto-column width adjustment.
  - Automatic `SUM` formula row at the bottom for total quantity and amount.
- 🔄 **Deduplication**: Multi-field trade keying ensures trades are never logged twice even across multiple runs.
- ⏰ **Automated Scheduler**: Includes a helper script to set up a daily Monday–Friday 9:00 PM `cron` job.

---

## 📁 Directory Structure

```
DailyTradeLedger/
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
├── config.py             # Config loader & Financial Year calculator
├── email_fetcher.py      # Gmail IMAP SSL fetcher with strict filters
├── pdf_parser.py         # IDBI Capital PDF table parser with password decryption
├── excel_logger.py       # Excel writer maintaining Buy & Sell FY ledgers
├── main.py               # Main CLI engine
├── setup_cron.sh         # Bash script to install daily Mon-Fri 9:00 PM cron job
├── downloads/            # Temp directory storing downloaded contract note PDFs (gitignored)
├── trades/               # Excel ledgers (gitignored)
└── logs/                 # Execution log directory (gitignored)
```

---

## 🛠️ Prerequisites & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Sid-1807/DailyTradeLedger.git
   cd DailyTradeLedger
   ```

2. **Set Up Python Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```ini
   # Gmail Credentials
   GMAIL_USER=your_email@gmail.com
   GMAIL_APP_PASS=your_16_digit_app_password

   # PDF Password (e.g., PAN Card Number in UPPERCASE)
   PDF_PASSWORD=YOUR_PAN_NUMBER

   # IMAP Settings
   IMAP_SERVER=imap.gmail.com
   IMAP_PORT=993

   # Filter Criteria
   SENDER_EMAIL=custcare@idbicapital.com
   SUBJECT_KEYWORD=Common Contract Note
   ```

   > 💡 **Gmail App Password**: Generated from Google Account $\rightarrow$ Security $\rightarrow$ 2-Step Verification $\rightarrow$ App Passwords.

---

## 🚀 Usage

### 1. Process Downloaded PDFs Locally
If you already have contract note PDFs downloaded in the `downloads/` folder:
```bash
python main.py --process-downloads
```

### 2. Historical Catch-up
Fetch and process all contract notes from April 1st, 2026 to July 23rd, 2026:
```bash
python main.py --catchup
```

### 3. Run Daily Check
Check Gmail for today's contract note (skips automatically on weekends):
```bash
python main.py --daily
```

### 4. Custom Date Range
```bash
python main.py --from-date 2026-04-01 --to-date 2026-05-31
```

### 5. Parse a Single PDF File Directly
```bash
python main.py --pdf /path/to/contract_note.pdf
```

---

## ⏰ Automated Daily Execution (Mon–Fri at 9:00 PM)

Run the cron installer script to schedule daily execution every Monday through Friday at 9:00 PM:
```bash
./setup_cron.sh
```

---

## 📄 License
MIT License
