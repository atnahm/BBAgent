"""IMAP Email Listener to fetch invoice attachments automatically."""
import imaplib
import email
from email.header import decode_header
import os
import asyncio
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailListener:
    """Connects to IMAP server, searches for unread emails with invoices, and downloads them."""

    def __init__(self, orchestrator, imap_server: str, email_user: str, email_pass: str, watch_dir: str = "temp"):
        self.orchestrator = orchestrator
        self.imap_server = imap_server
        self.email_user = email_user
        self.email_pass = email_pass
        self.watch_dir = Path(watch_dir)
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.poll_interval = 300 # 5 minutes

    def _get_imap_connection(self):
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_pass)
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            return None

    def fetch_unread_invoices(self):
        """Fetches unread emails and extracts PDF/Image attachments."""
        mail = self._get_imap_connection()
        if not mail:
            return

        try:
            mail.select("inbox")
            status, messages = mail.search(None, "UNSEEN")
            if status != "OK" or not messages[0]:
                return

            email_ids = messages[0].split()
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] 📧 Found {len(email_ids)} unread emails.")

            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        logger.info(f"  Checking email: {subject}")

                        # Check attachments
                        for part in msg.walk():
                            if part.get_content_maintype() == 'multipart':
                                continue
                            if part.get('Content-Disposition') is None:
                                continue

                            filename = part.get_filename()
                            if filename:
                                ext = os.path.splitext(filename)[1].lower()
                                if ext in ['.pdf', '.png', '.jpg', '.jpeg']:
                                    filepath = self.watch_dir / f"email_{email_id.decode()}_{filename}"

                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))

                                    logger.info(f"  ✅ Saved attachment: {filename}")
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        finally:
            mail.logout()

    async def poll_emails(self):
        """Continuously polls the email inbox."""
        while True:
            # We run the synchronous IMAP library in an executor to avoid blocking the event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.fetch_unread_invoices)
            await asyncio.sleep(self.poll_interval)
