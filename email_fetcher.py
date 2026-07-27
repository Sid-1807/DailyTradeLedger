import imaplib
import email
from email.header import decode_header
import os
import logging
from datetime import datetime, date
import config

logger = logging.getLogger("TradeAgent")

def decode_mime_words(s):
    """Safely decode MIME header string."""
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    fragments = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            try:
                fragments.append(fragment.decode(encoding or "utf-8", errors="replace"))
            except Exception:
                fragments.append(fragment.decode("utf-8", errors="replace"))
        else:
            fragments.append(str(fragment))
    return "".join(fragments)

def connect_imap():
    """Establishes SSL IMAP connection."""
    if not config.GMAIL_USER or not config.GMAIL_APP_PASS:
        raise ValueError("GMAIL_USER and GMAIL_APP_PASS must be configured in .env file.")
    
    logger.info(f"Connecting to IMAP server {config.IMAP_SERVER}:{config.IMAP_PORT}...")
    mail = imaplib.IMAP4_SSL(config.IMAP_SERVER, config.IMAP_PORT)
    mail.login(config.GMAIL_USER, config.GMAIL_APP_PASS)
    logger.info("IMAP connection and login successful.")
    return mail

def fetch_contract_notes_range(start_date: date, end_date: date):
    """
    Fetches PDF contract notes received between start_date and end_date (inclusive).
    """
    mail = connect_imap()
    downloaded_files = []
    
    try:
        mail.select("INBOX")
        
        # IMAP date format: DD-Mon-YYYY (e.g., 01-Apr-2026)
        since_str = start_date.strftime("%d-%b-%Y")
        # IMAP BEFORE is exclusive, so we use end_date + 1 day
        from datetime import timedelta
        before_dt = end_date + timedelta(days=1)
        before_str = before_dt.strftime("%d-%b-%Y")
        
        search_criterion = f'(SINCE "{since_str}" BEFORE "{before_str}")'
        logger.info(f"Searching IMAP emails with criterion: {search_criterion}")
        
        status, messages = mail.search(None, search_criterion)
        if status != "OK" or not messages[0]:
            logger.info("No messages found matching search criterion.")
            return downloaded_files

        msg_ids = messages[0].split()
        logger.info(f"Found {len(msg_ids)} potential email messages.")

        for msg_id in msg_ids:
            res, msg_data = mail.fetch(msg_id, "(RFC822)")
            if res != "OK" or not msg_data:
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_mime_words(msg.get("Subject", ""))
                    sender = decode_mime_words(msg.get("From", ""))
                    date_header = msg.get("Date", "")

                    # Strict filtering: MUST match both sender AND subject keyword
                    is_sender_match = config.SENDER_EMAIL.lower() in sender.lower() if config.SENDER_EMAIL else True
                    is_subject_match = config.SUBJECT_KEYWORD.lower() in subject.lower() if config.SUBJECT_KEYWORD else True

                    if not (is_sender_match and is_subject_match):
                        logger.debug(f"Skipping non-matching email: '{subject}' from '{sender}'")
                        continue

                    logger.info(f"Processing matching email: '{subject}' from '{sender}' ({date_header})")

                    # Extract attachments
                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart":
                            continue
                        if part.get("Content-Disposition") is None:
                            continue

                        filename = part.get_filename()
                        if filename:
                            filename = decode_mime_words(filename)
                            if filename.lower().endswith(".pdf"):
                                # Save attachment with caching check
                                safe_filename = f"{msg_id.decode('utf-8')}_{filename}"
                                save_path = os.path.join(config.DOWNLOADS_DIR, safe_filename)
                                
                                if not os.path.exists(save_path):
                                    with open(save_path, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    logger.info(f"Downloaded attachment: {save_path}")
                                else:
                                    logger.info(f"Attachment already exists locally, using cached file: {save_path}")
                                downloaded_files.append({
                                    "pdf_path": save_path,
                                    "subject": subject,
                                    "sender": sender,
                                    "date_header": date_header,
                                    "filename": filename
                                })

    finally:
        try:
            mail.close()
            mail.logout()
        except Exception:
            pass

    return downloaded_files

def fetch_contract_notes_daily(target_date: date):
    """Fetches contract notes for a single target date."""
    return fetch_contract_notes_range(target_date, target_date)
