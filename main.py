import argparse
import logging
import os
import sys
from datetime import datetime, date

import config
from email_fetcher import fetch_contract_notes_range, fetch_contract_notes_daily
from pdf_parser import parse_contract_note
from excel_logger import log_trades_to_excel

def setup_logging():
    log_file = os.path.join(config.LOGS_DIR, "trade_agent.log")
    
    logger = logging.getLogger("TradeAgent")
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File Handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def is_weekend(dt: date) -> bool:
    """Returns True if date is Saturday (5) or Sunday (6)."""
    return dt.weekday() in (5, 6)

def main():
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Starting Daily Trade Ledger Agent")
    logger.info("=" * 60)

    parser = argparse.ArgumentParser(description="Automated Trade Ledger Agent for Stock Contract Notes")
    parser.add_argument("--catchup", action="store_true", help="Run historical catch-up from 01-Apr-2026 to 23-Jul-2026")
    parser.add_argument("--daily", action="store_true", help="Run daily contract note check (Skips weekends)")
    parser.add_argument("--process-downloads", action="store_true", help="Process all PDFs currently in the downloads directory without fetching from email")
    parser.add_argument("--from-date", type=str, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--to-date", type=str, help="End date in YYYY-MM-DD format")
    parser.add_argument("--pdf", type=str, help="Directly parse a local PDF file")

    args = parser.parse_args()

    # Process local downloads directory directly
    if args.process_downloads:
        logger.info(f"Scanning downloads directory: {config.DOWNLOADS_DIR}")
        pdf_files = [
            os.path.join(config.DOWNLOADS_DIR, f)
            for f in os.listdir(config.DOWNLOADS_DIR)
            if f.lower().endswith(".pdf")
        ]
        
        if not pdf_files:
            logger.warning("No PDF files found in downloads directory.")
            return

        logger.info(f"Found {len(pdf_files)} PDF contract notes in downloads directory.")
        all_trades = []
        for pdf_path in pdf_files:
            trades = parse_contract_note(pdf_path)
            all_trades.extend(trades)

        added = log_trades_to_excel(all_trades)
        logger.info(f"Downloads processing completed. {len(pdf_files)} PDFs parsed, {added} new trades logged.")
        return
    if args.pdf:
        if not os.path.exists(args.pdf):
            logger.error(f"Specified PDF file does not exist: {args.pdf}")
            sys.exit(1)
        logger.info(f"Direct PDF parsing mode selected for file: {args.pdf}")
        trades = parse_contract_note(args.pdf)
        added = log_trades_to_excel(trades)
        logger.info(f"Finished processing local PDF. {added} new trades recorded.")
        return

    # 2. Daily mode
    if args.daily:
        today = datetime.now().date()
        if is_weekend(today):
            logger.info(f"Today ({today.strftime('%A')}, {today}) is a weekend. No trading today. Skipping.")
            return

        logger.info(f"Running Daily Contract Note Check for date: {today}")
        pdf_list = fetch_contract_notes_daily(today)
        if not pdf_list:
            logger.warning("No matching contract note found from 'custcare@idbicapital.com' with subject containing 'Common Contract Note'. Exiting gracefully.")
            return

        all_trades = []
        for pdf_info in pdf_list:
            trades = parse_contract_note(pdf_info["pdf_path"])
            all_trades.extend(trades)

        added = log_trades_to_excel(all_trades)
        logger.info(f"Daily processing completed. {len(pdf_list)} PDFs processed, {added} new trades logged.")
        return

    # 3. Historical Catch-up mode (01 April 2026 to 23 July 2026)
    if args.catchup:
        start_date = date(2026, 4, 1)
        end_date = date(2026, 7, 23)
        logger.info(f"Running Historical Catch-up from {start_date} to {end_date}...")
        
        pdf_list = fetch_contract_notes_range(start_date, end_date)
        if not pdf_list:
            logger.warning("No matching contract notes found from 'custcare@idbicapital.com' with subject containing 'Common Contract Note'. Exiting gracefully.")
            return

        all_trades = []
        for pdf_info in pdf_list:
            trades = parse_contract_note(pdf_info["pdf_path"])
            all_trades.extend(trades)

        added = log_trades_to_excel(all_trades)
        logger.info(f"Catch-up completed. {len(pdf_list)} PDFs downloaded, {added} new trades logged.")
        return

    # 4. Custom Date Range mode
    if args.from_date and args.to_date:
        try:
            start_date = datetime.strptime(args.from_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(args.to_date, "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD.")
            sys.exit(1)

        logger.info(f"Running Custom Date Range check from {start_date} to {end_date}...")
        pdf_list = fetch_contract_notes_range(start_date, end_date)
        if not pdf_list:
            logger.warning("No matching contract notes found from 'custcare@idbicapital.com' with subject containing 'Common Contract Note'. Exiting gracefully.")
            return

        all_trades = []
        for pdf_info in pdf_list:
            trades = parse_contract_note(pdf_info["pdf_path"])
            all_trades.extend(trades)

        added = log_trades_to_excel(all_trades)
        logger.info(f"Range processing completed. {len(pdf_list)} PDFs downloaded, {added} new trades logged.")
        return

    # Default if no flags passed: show help
    parser.print_help()

if __name__ == "__main__":
    main()
