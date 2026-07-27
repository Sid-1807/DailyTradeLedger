import pdfplumber
import re
import os
import logging
from datetime import datetime
import config

logger = logging.getLogger("TradeAgent")

def parse_date(date_str: str):
    """Parse date from common Indian formats: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD, DD-MMM-YY."""
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y", "%d%m%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    return None

def unlock_pdf(pdf_path: str):
    """Attempts to open PDF with configured password or without password if unencrypted."""
    passwords_to_try = [""]
    if config.PDF_PASSWORD:
        passwords_to_try.insert(0, config.PDF_PASSWORD)
        passwords_to_try.insert(1, config.PDF_PASSWORD.upper())
        passwords_to_try.insert(2, config.PDF_PASSWORD.lower())

    for pwd in passwords_to_try:
        try:
            pdf = pdfplumber.open(pdf_path, password=pwd)
            return pdf
        except Exception:
            continue
            
    raise ValueError(f"Could not open PDF '{pdf_path}'. Decryption failed with provided password.")

def parse_contract_note(pdf_path: str):
    """
    Parses IDBI Capital contract note PDF cleanly.
    Returns list of trade dicts.
    """
    logger.info(f"Parsing PDF contract note: {pdf_path}")
    trades = []
    filename = os.path.basename(pdf_path)

    pdf = unlock_pdf(pdf_path)
    
    full_text = ""
    tables = []

    try:
        for page in pdf.pages:
            p_text = page.extract_text() or ""
            full_text += p_text + "\n"
            page_tables = page.extract_tables() or []
            tables.extend(page_tables)

        # 1. Extract Trade Date from text or filename
        trade_date = None
        date_match = re.search(r'(?:Trade\s*Date)\s*[:\.]?\s*(\d{2}[/-][A-Za-z]{3}[/-]\d{2,4}|\d{2}[/-]\d{2}[/-]\d{4})', full_text, re.IGNORECASE)
        if date_match:
            trade_date = parse_date(date_match.group(1))

        if not trade_date:
            # Check filename pattern _DDMMYYYY.pdf (e.g. _06072026.pdf)
            filename_match = re.search(r'_(\d{2})(\d{2})(\d{4})\.pdf$', filename, re.IGNORECASE)
            if filename_match:
                d_str = f"{filename_match.group(1)}/{filename_match.group(2)}/{filename_match.group(3)}"
                trade_date = parse_date(d_str)

        if not trade_date:
            trade_date = datetime.now().date()
            logger.warning(f"Trade Date not found in {filename}, fallback to current date {trade_date}")

        # 2. Extract Contract Note / Order / Trade Number if present
        contract_no = ""
        cn_match = re.search(r'Contract\s*Note\s*No[^\d]*(\d{10,16})', full_text, re.IGNORECASE)
        if cn_match:
            contract_no = cn_match.group(1)

        # 3. Parse Trades from IDBI Capital Structured Tables
        for tbl in tables:
            for row in tbl:
                if not row or len(row) < 5:
                    continue
                
                # Check if it's an IDBI Capital Equity Row (Starts with ISIN e.g. INE...)
                col0 = str(row[0] or "").strip()
                if col0.startswith("INE") and len(row) >= 12:
                    parsed_trades = parse_idbi_equity_row(row, trade_date, contract_no, filename)
                    trades.extend(parsed_trades)
                    continue

                # Check if it's an IDBI Capital F&O / Derivatives Row
                if len(row) >= 9 and ("BUY" in str(row[1]).upper() or "SELL" in str(row[1]).upper() or "B" in str(row[1]).upper() or "S" in str(row[1]).upper()):
                    if str(row[0]).strip().lower() not in ("no records found", "contract description", "contract description #"):
                        parsed_fno = parse_idbi_fno_row(row, trade_date, contract_no, filename)
                        if parsed_fno:
                            trades.append(parsed_fno)

    finally:
        pdf.close()

    logger.info(f"Extracted {len(trades)} trade records from {filename}.")
    return trades

def clean_num(val) -> float:
    """Helper to convert cell value to float."""
    if not val:
        return 0.0
    s = str(val).replace(",", "").replace("Rs.", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0

def parse_idbi_equity_row(row, trade_date, contract_no, filename):
    """
    Parses an IDBI Capital Equity table row starting with ISIN.
    Table structure:
    Col 0: ISIN (e.g. INE028A01039)
    Col 1: Security Name / Symbol (e.g. BANK OF BARODA-BANKBARODAEQ)
    Col 2: BUY Qty
    Col 3: BUY WAP / Gross Rate
    Col 4: BUY Brokerage per share
    Col 5: BUY WAP after brokerage / Net Rate
    Col 6: BUY Total Value
    Col 7: SELL Qty
    Col 8: SELL WAP / Gross Rate
    Col 9: SELL Brokerage per share
    Col 10: SELL WAP after brokerage / Net Rate
    Col 11: SELL Total Value
    """
    results = []
    isin = str(row[0]).strip()
    sec_name_raw = str(row[1]).replace("\n", " ").strip()
    
    # Clean symbol (e.g. "BANK OF BARODA-BANKBARODAEQ" -> "BANK OF BARODA")
    symbol = sec_name_raw.split("-")[0].strip() if "-" in sec_name_raw else sec_name_raw

    buy_qty = int(clean_num(row[2]))
    sell_qty = int(clean_num(row[7]))

    trade_date_str = trade_date.strftime("%Y-%m-%d")

    # If BUY Trade
    if buy_qty > 0:
        gross_rate = clean_num(row[3])
        brokerage = clean_num(row[4])
        net_rate = clean_num(row[5])
        total_amount = clean_num(row[6])
        if total_amount == 0.0:
            total_amount = round(buy_qty * net_rate, 2)

        results.append({
            "trade_date": trade_date_str,
            "order_no": contract_no if contract_no else f"ORD_{trade_date.strftime('%Y%m%d')}_{isin}",
            "trade_no": isin,
            "exchange": "NSE",
            "symbol": symbol,
            "action": "BUY",
            "quantity": buy_qty,
            "gross_rate": gross_rate,
            "brokerage": brokerage,
            "net_rate": net_rate,
            "total_amount": total_amount,
            "contract_note_file": filename
        })

    # If SELL Trade
    if sell_qty > 0:
        gross_rate = clean_num(row[8])
        brokerage = clean_num(row[9])
        net_rate = clean_num(row[10])
        total_amount = clean_num(row[11])
        if total_amount == 0.0:
            total_amount = round(sell_qty * net_rate, 2)

        results.append({
            "trade_date": trade_date_str,
            "order_no": contract_no if contract_no else f"ORD_{trade_date.strftime('%Y%m%d')}_{isin}",
            "trade_no": isin,
            "exchange": "NSE",
            "symbol": symbol,
            "action": "SELL",
            "quantity": sell_qty,
            "gross_rate": gross_rate,
            "brokerage": brokerage,
            "net_rate": net_rate,
            "total_amount": total_amount,
            "contract_note_file": filename
        })

    return results

def parse_idbi_fno_row(row, trade_date, contract_no, filename):
    """
    Parses an IDBI Capital F&O / Derivative row.
    """
    contract_desc = str(row[0]).replace("\n", " ").strip()
    act_raw = str(row[1]).strip().upper()
    action = "BUY" if "B" in act_raw else "SELL"
    
    qty = int(clean_num(row[2]))
    if qty <= 0:
        return None

    gross_rate = clean_num(row[4]) if len(row) > 4 else clean_num(row[3])
    brokerage = clean_num(row[5]) if len(row) > 5 else 0.0
    net_rate = clean_num(row[6]) if len(row) > 6 else gross_rate
    total_amount = clean_num(row[8]) if len(row) > 8 else round(qty * net_rate, 2)
    exchange = str(row[9]).strip().upper() if len(row) > 9 and row[9] else "NSE"

    return {
        "trade_date": trade_date.strftime("%Y-%m-%d"),
        "order_no": contract_no if contract_no else f"ORD_{trade_date.strftime('%Y%m%d')}",
        "trade_no": f"FNO_{len(contract_desc)}",
        "exchange": exchange,
        "symbol": contract_desc,
        "action": action,
        "quantity": qty,
        "gross_rate": gross_rate,
        "brokerage": brokerage,
        "net_rate": net_rate,
        "total_amount": total_amount,
        "contract_note_file": filename
    }
