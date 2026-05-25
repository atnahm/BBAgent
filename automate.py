"""
Automated Agent System Runner
Continuously monitors for new invoices and processes them automatically.
Optimized for concurrency and proper configuration usage.
"""
import asyncio
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator
from memory.relational_db import Transaction, Communication, Customer
from config_loader import CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class InvoiceHandler(FileSystemEventHandler):
    """Handles new invoice file uploads."""
    
    def __init__(self, orchestrator, loop):
        self.orchestrator = orchestrator
        self.loop = loop
        self.processing = set()
    
    def on_created(self, event):
        """
        Process new invoice files automatically.
        This runs in a thread pool managed by watchdog.
        We must schedule the async task on the main event loop thread-safely.
        """
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if it's an invoice file
        if not any(file_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.pdf', '.mp3', '.wav', '.m4a']):
            return
        
        # Avoid duplicate processing
        if file_path in self.processing:
            return
        
        self.processing.add(file_path)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📄 New file detected: {Path(file_path).name}")
        
        # Determine source type
        source_type = 'voice' if file_path.lower().endswith(('.mp3', '.wav', '.m4a')) else 'image'
        
        # Schedule the coroutine one the main loop
        # We use run_coroutine_threadsafe because on_created is called from a different thread
        asyncio.run_coroutine_threadsafe(
            self._process_invoice(file_path, source_type), 
            self.loop
        )
    
    async def _process_invoice(self, file_path, source_type):
        """Process invoice through full workflow."""
        try:
            print(f"  🤖 Starting automated workflow...")
            
            result = await self.orchestrator.process_invoice(file_path, source_type)
            
            if result['status'] == 'success':
                print(f"  ✅ Invoice processed successfully!")
                print(f"     Transaction ID: {result['transaction_id']}")
                val = result['ingestion']['extraction']['amount']
                print(f"     Amount: ₹{val:,.2f}" if isinstance(val, (int, float)) else f"     Amount: {val}")
                print(f"     Strategy: {result['strategy']['recommendation']}")
                
                if result.get('message') and result['message'].get('requires_hitl_approval'):
                    print(f"  ⏳ Message queued for HITL approval")
                else:
                    print(f"  📤 Message sent automatically")
            else:
                print(f"  ❌ Error: {result.get('error')}")
        
        except Exception as e:
            print(f"  ❌ Processing error: {str(e)}")
        finally:
            if file_path in self.processing:
                self.processing.remove(file_path)

class ComplianceMonitor:
    """Monitors transactions for compliance violations."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    async def check_all_transactions(self):
        """Check all pending transactions for compliance."""
        db_session = self.orchestrator.db.get_session()
        
        try:
            pending_txns = db_session.query(Transaction).filter(
                Transaction.status.in_(['pending', 'overdue'])
            ).all()
            
            if not pending_txns:
                return

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Checking {len(pending_txns)} transactions...")
            
            for txn in pending_txns:
                # Check compliance
                # context format needs to match what agent expects
                context = {
                    'invoice_date': txn.invoice_date.strftime('%Y-%m-%d') if txn.invoice_date else None,
                    'due_date': txn.due_date.strftime('%Y-%m-%d') if txn.due_date else None,
                    'amount': txn.amount,
                    'payment_date': txn.payment_date.strftime('%Y-%m-%d') if txn.payment_date else None,
                    'country_code': txn.country_code
                }

                if not context['invoice_date']:
                    continue

                compliance_result = await self.orchestrator.compliance.run(
                    task="check_transaction",
                    context=context
                )
                
                # Update transaction
                old_status = txn.status
                txn.days_overdue = compliance_result['days_overdue']
                txn.interest_amount = compliance_result['interest_amount']
                txn.legal_flag = compliance_result['legal_flag']
                
                if compliance_result['status'] == 'overdue' and old_status != 'overdue':
                    txn.status = 'overdue'
                    print(f"  ⚠️  Transaction {txn.id} now OVERDUE ({txn.days_overdue} days)")
                    
                    # Trigger message generation
                    await self._generate_recovery_message(txn, compliance_result, db_session)
            
            db_session.commit()
            
        finally:
            db_session.close()
    
    async def _generate_recovery_message(self, txn, compliance_status, db_session):
        """Generate recovery message for overdue transaction."""
        try:
            # Get communication history
            comm_history = db_session.query(Communication).filter_by(
                transaction_id=txn.id
            ).all()
            
            # Determine tier
            tier_result = await self.orchestrator.collector.run(
                task="determine_tier",
                context={
                    'compliance_status': compliance_status,
                    'communication_history': [{'message_type': c.message_type} for c in comm_history]
                }
            )
            
            tier = tier_result if isinstance(tier_result, str) else tier_result.get('tier', 'none')
            
            if tier != 'none':
                # Generate message
                message_result = await self.orchestrator.collector.run(
                    task="generate_message",
                    context={
                        'tier': tier,
                        'transaction': {
                            'id': txn.id,
                            'vendor_name': txn.vendor_name,
                            'amount': txn.amount,
                            'invoice_number': txn.invoice_number
                        },
                        'compliance_status': compliance_status,
                        'customer': {'phone_number': txn.customer.phone_number if txn.customer else None}
                    }
                )
                
                # Save communication
                comm = Communication(
                    transaction_id=txn.id,
                    message_type=tier,
                    message_text=message_result['message_text'],
                    delivery_status='pending_approval' if message_result['requires_hitl_approval'] else 'sent'
                )
                db_session.add(comm)
                
                print(f"     📧 {tier.upper()} message generated")
                
        except Exception as e:
            print(f"     ❌ Message generation error: {str(e)}")

from backend.ingestion.db_connector import GenericDBConnector

class AutomatedSystem:
    """Main automation controller."""
    
    def __init__(self):
        print("🚀 Initializing Automated Agent System...")
        self.orchestrator = Orchestrator()
        
        # Get threshold from config
        self.auto_approve_limit = CONFIG.get('automation', {}).get('auto_approve_limit', 10000)
        
        # Setup file watcher will be done in start() where we have the loop
        self.observer = Observer()
        self.watch_dir = Path("temp")
        self.watch_dir.mkdir(exist_ok=True)
        
        # Setup generic DB poller from config
        db_config = CONFIG.get("ingestion", {}).get("database", {})
        self.db_poller = None
        if db_config.get("enabled"):
            self.db_poller = GenericDBConnector(
                orchestrator=self.orchestrator,
                connection_string=db_config.get("connection_string", "sqlite:///:memory:"),
                query=db_config.get("query", "SELECT 1 WHERE 1=0")
            )

        from backend.communications.dispatcher import NotificationDispatcher
        self.notification_dispatcher = NotificationDispatcher()

        # Setup IMAP Email Listener from config
        email_config = CONFIG.get("ingestion", {}).get("email", {})
        self.email_listener = None
        if email_config.get("enabled"):
            from backend.ingestion.email_listener import EmailListener
            self.email_listener = EmailListener(
                orchestrator=self.orchestrator,
                imap_server=email_config.get("imap_server", ""),
                email_user=email_config.get("username", ""),
                email_pass=email_config.get("password", ""),
                watch_dir=str(self.watch_dir)
            )

    async def run_compliance_loop(self):
        """Run compliance checks periodically."""
        while True:
            try:
                await self.compliance_monitor.check_all_transactions()
            except Exception as e:
                print(f"❌ Compliance check error: {str(e)}")
            
            # Wait 1 hour
            await asyncio.sleep(3600)
    
    async def auto_approve_messages(self):
        """Automatically approve low-risk messages."""
        while True:
            try:
                db_session = self.orchestrator.db.get_session()
                
                pending = db_session.query(Communication).filter_by(
                    delivery_status='pending_approval'
                ).all()
                
                for comm in pending:
                    txn = db_session.query(Transaction).get(comm.transaction_id)
                    
                    # Auto-approve friendly reminders for low-value transactions
                    # Configurable Limit
                    if comm.message_type == 'friendly_reminder' and txn.amount < self.auto_approve_limit:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ Auto-approving friendly reminder ({txn.currency} {txn.amount:,.2f})")

                        # Send message via Dispatcher instead of hardcoded WhatsApp
                        target_channel = "email" if txn.customer and txn.customer.email else "whatsapp"
                        recipient = txn.customer.email if target_channel == "email" else (txn.customer.phone_number if txn.customer else "unknown")

                        send_result = await self.notification_dispatcher.dispatch(
                            channel_name=target_channel,
                            recipient=recipient,
                            message=comm.message_text
                        )
                        
                        comm.delivery_status = 'sent' if send_result.get('status') == 'success' else 'failed'
                        comm.approved_by = 'AutoSystem'
                        comm.approved_at = datetime.utcnow()
                        comm.sent_at = datetime.utcnow()
                        
                        db_session.commit()
                
                db_session.close()
                
            except Exception as e:
                print(f"❌ Auto-approval error: {str(e)}")
            
            # Check every 5 minutes
            await asyncio.sleep(300)
    
    def start(self):
        """Start the automated system."""
        # Create event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        self.invoice_handler = InvoiceHandler(self.orchestrator, loop)
        self.compliance_monitor = ComplianceMonitor(self.orchestrator)
        
        # Schedule the watcher
        self.observer.schedule(self.invoice_handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        
        print(f"✅ Watching directory: {self.watch_dir.absolute()}")
        print(f"✅ Compliance monitoring: Every 1 hour")
        print(f"✅ Auto-approval: Enabled (< ₹{self.auto_approve_limit:,.0f})")
        print("\n" + "="*60)
        print("SYSTEM READY - Drop invoices in 'temp' folder")
        print("="*60 + "\n")
        
        try:
            # Gather tasks dynamically based on what is configured
            tasks = [
                self.run_compliance_loop(),
                self.auto_approve_messages()
            ]
            if self.db_poller:
                tasks.append(self.db_poller.poll_external_db())
            if self.email_listener:
                tasks.append(self.email_listener.poll_emails())

            # Run compliance monitoring, auto-approval, DB polling, and email listener concurrently
            loop.run_until_complete(asyncio.gather(*tasks))
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down automated system...")
            self.observer.stop()
        finally:
            self.observer.join()
            loop.close()

if __name__ == "__main__":
    system = AutomatedSystem()
    system.start()
