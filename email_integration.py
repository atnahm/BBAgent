"""
Email Integration Module
Automatically fetch invoices from email and process them.
"""
import imaplib
import email
from email.header import decode_header
import os
import base64
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import time

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator

class EmailInvoiceProcessor:
    """Process invoices from email automatically."""
    
    def __init__(
        self,
        email_address,
        password,
        imap_server="imap.gmail.com",
        check_interval=300  # 5 minutes
    ):
        """Initialize email processor."""
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.check_interval = check_interval
        self.orchestrator = Orchestrator()
        
        print(f"📧 Email Invoice Processor initialized")
        print(f"   Email: {email_address}")
        print(f"   Server: {imap_server}")
        print(f"   Check interval: {check_interval}s")
    
    def connect(self):
        """Connect to email server."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.password)
            print(f"✅ Connected to {self.imap_server}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def fetch_unread_invoices(self):
        """Fetch unread emails with invoice attachments."""
        try:
            # Select inbox
            self.mail.select("inbox")
            
            # Search for unread emails with subject containing "invoice"
            status, messages = self.mail.search(None, 'UNSEEN SUBJECT "invoice"')
            
            if status != "OK":
                return []
            
            email_ids = messages[0].split()
            
            if not email_ids:
                return []
            
            print(f"\n📬 Found {len(email_ids)} unread invoice emails")
            
            invoices = []
            
            for email_id in email_ids:
                # Fetch email
                status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                
                if status != "OK":
                    continue
                
                # Parse email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Get subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                sender = msg.get("From")
                
                print(f"\n📧 Processing email from {sender}")
                print(f"   Subject: {subject}")
                
                # Process attachments
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    if part.get('Content-Disposition') is None:
                        continue
                    
                    filename = part.get_filename()
                    
                    if not filename:
                        continue
                    
                    # Check if it's an invoice file
                    if not any(filename.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.jpeg', '.png']):
                        continue
                    
                    print(f"   📎 Attachment: {filename}")
                    
                    # Save attachment
                    filepath = Path("temp") / filename
                    filepath.parent.mkdir(exist_ok=True)
                    
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    invoices.append({
                        'filepath': str(filepath),
                        'filename': filename,
                        'sender': sender,
                        'subject': subject,
                        'email_id': email_id
                    })
            
            return invoices
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []
    
    async def process_invoice_email(self, invoice_data):
        """Process a single invoice from email."""
        try:
            print(f"\n🤖 Processing invoice: {invoice_data['filename']}")
            
            # Determine source type
            source_type = 'image'
            
            # Process through orchestrator
            result = await self.orchestrator.process_invoice(
                invoice_data['filepath'],
                source_type
            )
            
            if result['status'] == 'success':
                print(f"✅ Invoice processed successfully!")
                print(f"   Transaction ID: {result['transaction_id']}")
                print(f"   Vendor: {result['ingestion']['extraction']['vendor_name']}")
                print(f"   Amount: ₹{result['ingestion']['extraction']['amount']:,.2f}")
                
                # Mark email as read
                # self.mail.store(invoice_data['email_id'], '+FLAGS', '\\Seen')
                
                return True
            else:
                print(f"❌ Processing failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing invoice: {e}")
            return False
    
    async def process_all_invoices(self, invoices):
        """Process all invoices concurrently."""
        tasks = [self.process_invoice_email(inv) for inv in invoices]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(results)
        print(f"\n📊 Processed {success_count}/{len(invoices)} invoices successfully")
        
        return results
    
    def run(self):
        """Run email processor continuously."""
        if not self.connect():
            return
        
        print(f"\n{'='*60}")
        print(f"📧 EMAIL INVOICE PROCESSOR RUNNING")
        print(f"{'='*60}")
        print(f"Checking for new invoices every {self.check_interval}s")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while True:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Checking for new invoices...")
                
                # Fetch unread invoices
                invoices = self.fetch_unread_invoices()
                
                if invoices:
                    # Process invoices
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.process_all_invoices(invoices))
                    loop.close()
                else:
                    print(f"   No new invoices found")
                
                # Wait before next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Email processor stopped")
        finally:
            self.mail.logout()

def main():
    """CLI interface for email integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Email Invoice Processor')
    parser.add_argument('--email', required=True, help='Email address')
    parser.add_argument('--password', required=True, help='Email password or app password')
    parser.add_argument('--server', default='imap.gmail.com', help='IMAP server')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    
    args = parser.parse_args()
    
    processor = EmailInvoiceProcessor(
        email_address=args.email,
        password=args.password,
        imap_server=args.server,
        check_interval=args.interval
    )
    
    processor.run()

if __name__ == "__main__":
    # Example usage with environment variables
    email_addr = os.getenv('EMAIL_ADDRESS')
    email_pass = os.getenv('EMAIL_PASSWORD')
    
    if email_addr and email_pass:
        processor = EmailInvoiceProcessor(
            email_address=email_addr,
            password=email_pass
        )
        processor.run()
    else:
        print("⚠️  Set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables")
        print("Or run with: python email_integration.py --email your@email.com --password yourpass")
