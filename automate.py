"""
Automated Agent System Runner
Continuously monitors for new invoices and processes them automatically.
"""
import asyncio
import sys
import time
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

class InvoiceHandler(FileSystemEventHandler):
    """Handles new invoice file uploads."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.processing = set()
    
    def on_created(self, event):
        """Process new invoice files automatically."""
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
        
        # Process asynchronously
        asyncio.run(self._process_invoice(file_path, source_type))
        
        self.processing.remove(file_path)
    
    async def _process_invoice(self, file_path, source_type):
        """Process invoice through full workflow."""
        try:
            print(f"  🤖 Starting automated workflow...")
            
            result = await self.orchestrator.process_invoice(file_path, source_type)
            
            if result['status'] == 'success':
                print(f"  ✅ Invoice processed successfully!")
                print(f"     Transaction ID: {result['transaction_id']}")
                print(f"     Vendor: {result['ingestion']['extraction']['vendor_name']}")
                print(f"     Amount: ₹{result['ingestion']['extraction']['amount']:,.2f}")
                print(f"     Strategy: {result['strategy']['recommendation']}")
                
                if result.get('message') and result['message'].get('requires_hitl_approval'):
                    print(f"  ⏳ Message queued for HITL approval")
                else:
                    print(f"  📤 Message sent automatically")
            else:
                print(f"  ❌ Error: {result.get('error')}")
                
        except Exception as e:
            print(f"  ❌ Processing error: {str(e)}")

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
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Checking {len(pending_txns)} transactions...")
            
            for txn in pending_txns:
                # Check compliance
                compliance_result = await self.orchestrator.compliance.run(
                    task="check_transaction",
                    context={
                        'invoice_date': txn.invoice_date.strftime('%Y-%m-%d'),
                        'due_date': txn.due_date.strftime('%Y-%m-%d'),
                        'amount': txn.amount,
                        'payment_date': txn.payment_date.strftime('%Y-%m-%d') if txn.payment_date else None
                    }
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

class AutomatedSystem:
    """Main automation controller."""
    
    def __init__(self):
        print("🚀 Initializing Automated Agent System...")
        self.orchestrator = Orchestrator()
        self.invoice_handler = InvoiceHandler(self.orchestrator)
        self.compliance_monitor = ComplianceMonitor(self.orchestrator)
        
        # Setup file watcher
        self.observer = Observer()
        watch_dir = Path("temp")
        watch_dir.mkdir(exist_ok=True)
        
        self.observer.schedule(self.invoice_handler, str(watch_dir), recursive=False)
        
        print(f"✅ Watching directory: {watch_dir.absolute()}")
        print(f"✅ Compliance monitoring: Every 1 hour")
        print(f"✅ Auto-approval: Enabled for low-risk actions")
        print("\n" + "="*60)
        print("SYSTEM READY - Drop invoices in 'temp' folder")
        print("="*60 + "\n")
    
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
                    if comm.message_type == 'friendly_reminder' and txn.amount < 10000:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ Auto-approving friendly reminder (₹{txn.amount:,.2f})")
                        
                        # Send message
                        send_result = await self.orchestrator.collector.send_whatsapp_message(
                            txn.customer.phone_number if txn.customer else None,
                            comm.message_text,
                            comm.id
                        )
                        
                        comm.delivery_status = send_result.get('delivery_status', 'sent')
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
        # Start file watcher
        self.observer.start()
        
        # Run async tasks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run both compliance monitoring and auto-approval concurrently
            loop.run_until_complete(asyncio.gather(
                self.run_compliance_loop(),
                self.auto_approve_messages()
            ))
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down automated system...")
            self.observer.stop()
        
        self.observer.join()
        loop.close()

if __name__ == "__main__":
    system = AutomatedSystem()
    system.start()
