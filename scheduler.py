"""
Scheduled Task Runner for Agent System
Runs periodic tasks like daily compliance reports, weekly summaries, etc.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import schedule
import time

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator
from memory.relational_db import Transaction, Customer, Communication

class ScheduledTasks:
    """Manages scheduled automation tasks."""
    
    def __init__(self):
        print("📅 Initializing Scheduled Task System...")
        self.orchestrator = Orchestrator()
    
    async def daily_compliance_report(self):
        """Generate daily compliance report."""
        print(f"\n{'='*60}")
        print(f"📊 DAILY COMPLIANCE REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")
        
        db_session = self.orchestrator.db.get_session()
        
        try:
            # Get all transactions
            all_txns = db_session.query(Transaction).all()
            overdue_txns = [t for t in all_txns if t.status == 'overdue']
            pending_txns = [t for t in all_txns if t.status == 'pending']
            
            # Calculate totals
            total_receivables = sum(t.amount for t in all_txns if t.status != 'paid')
            overdue_amount = sum(t.amount for t in overdue_txns)
            total_interest = sum(t.interest_amount or 0 for t in overdue_txns)
            
            # Print report
            print(f"📈 SUMMARY:")
            print(f"   Total Transactions: {len(all_txns)}")
            print(f"   Pending: {len(pending_txns)}")
            print(f"   Overdue: {len(overdue_txns)}")
            print(f"   Total Receivables: ₹{total_receivables:,.2f}")
            print(f"   Overdue Amount: ₹{overdue_amount:,.2f}")
            print(f"   Interest Accrued: ₹{total_interest:,.2f}")
            
            # Critical alerts
            critical_txns = [t for t in overdue_txns if t.days_overdue > 45]
            if critical_txns:
                print(f"\n⚠️  CRITICAL ALERTS ({len(critical_txns)}):")
                for txn in critical_txns[:5]:  # Show top 5
                    print(f"   • {txn.vendor_name}: ₹{txn.amount:,.2f} ({txn.days_overdue} days overdue)")
            
            # Pending approvals
            pending_approvals = db_session.query(Communication).filter_by(
                delivery_status='pending_approval'
            ).count()
            
            if pending_approvals > 0:
                print(f"\n📧 PENDING APPROVALS: {pending_approvals} messages")
            
            print(f"\n{'='*60}\n")
            
        finally:
            db_session.close()
    
    async def weekly_customer_analysis(self):
        """Analyze customer payment patterns weekly."""
        print(f"\n{'='*60}")
        print(f"👥 WEEKLY CUSTOMER ANALYSIS - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*60}\n")
        
        db_session = self.orchestrator.db.get_session()
        
        try:
            customers = db_session.query(Customer).all()
            
            # Sort by total value
            top_customers = sorted(customers, key=lambda c: c.total_value, reverse=True)[:10]
            
            print(f"🏆 TOP 10 CUSTOMERS BY VALUE:")
            for i, customer in enumerate(top_customers, 1):
                print(f"   {i}. {customer.name}")
                print(f"      Total Value: ₹{customer.total_value:,.2f}")
                print(f"      Transactions: {customer.total_transactions}")
                print(f"      Avg Delay: {customer.avg_payment_delay_days:.1f} days")
                
                # Get relationship score
                scores = self.orchestrator.arbitrator.calculate_customer_scores(
                    customer={
                        'total_value': customer.total_value,
                        'total_transactions': customer.total_transactions,
                        'avg_payment_delay_days': customer.avg_payment_delay_days
                    }
                )
                print(f"      Tier: {scores['customer_value_tier'].upper()}")
                print()
            
            print(f"{'='*60}\n")
            
        finally:
            db_session.close()
    
    async def hourly_overdue_check(self):
        """Check for newly overdue transactions every hour."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ Running hourly overdue check...")
        
        db_session = self.orchestrator.db.get_session()
        
        try:
            # Get transactions due today or overdue
            today = datetime.utcnow()
            
            pending_txns = db_session.query(Transaction).filter(
                Transaction.status == 'pending',
                Transaction.due_date <= today
            ).all()
            
            if pending_txns:
                print(f"   Found {len(pending_txns)} newly overdue transactions")
                
                for txn in pending_txns:
                    # Update status
                    txn.status = 'overdue'
                    
                    # Calculate compliance
                    compliance_result = await self.orchestrator.compliance.run(
                        task="check_transaction",
                        context={
                            'invoice_date': txn.invoice_date.strftime('%Y-%m-%d'),
                            'due_date': txn.due_date.strftime('%Y-%m-%d'),
                            'amount': txn.amount,
                            'payment_date': None
                        }
                    )
                    
                    txn.days_overdue = compliance_result['days_overdue']
                    txn.interest_amount = compliance_result['interest_amount']
                    
                    print(f"   ⚠️  {txn.vendor_name}: ₹{txn.amount:,.2f} now overdue")
                
                db_session.commit()
            else:
                print(f"   ✅ No new overdue transactions")
        
        finally:
            db_session.close()
    
    async def monthly_compliance_summary(self):
        """Generate monthly compliance summary."""
        print(f"\n{'='*60}")
        print(f"📅 MONTHLY COMPLIANCE SUMMARY - {datetime.now().strftime('%B %Y')}")
        print(f"{'='*60}\n")
        
        db_session = self.orchestrator.db.get_session()
        
        try:
            # Get transactions from last month
            last_month = datetime.utcnow() - timedelta(days=30)
            
            monthly_txns = db_session.query(Transaction).filter(
                Transaction.created_at >= last_month
            ).all()
            
            # Calculate compliance metrics
            total = len(monthly_txns)
            on_time = len([t for t in monthly_txns if (t.days_overdue or 0) == 0])
            overdue = total - on_time
            
            compliance_rate = (on_time / total * 100) if total > 0 else 0
            
            print(f"📊 MONTHLY METRICS:")
            print(f"   Total Transactions: {total}")
            print(f"   On-Time Payments: {on_time}")
            print(f"   Overdue Payments: {overdue}")
            print(f"   Compliance Rate: {compliance_rate:.1f}%")
            
            # MSMED Act violations
            violations = len([t for t in monthly_txns if (t.days_overdue or 0) > 45])
            print(f"\n⚖️  MSMED ACT COMPLIANCE:")
            print(f"   Section 16 Violations: {violations}")
            print(f"   Total Interest Accrued: ₹{sum(t.interest_amount or 0 for t in monthly_txns):,.2f}")
            
            print(f"\n{'='*60}\n")
            
        finally:
            db_session.close()
    
    def run_async_task(self, coro):
        """Helper to run async tasks in sync context."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def setup_schedule(self):
        """Setup all scheduled tasks."""
        # Hourly tasks
        schedule.every().hour.do(lambda: self.run_async_task(self.hourly_overdue_check()))
        
        # Daily tasks
        schedule.every().day.at("09:00").do(lambda: self.run_async_task(self.daily_compliance_report()))
        
        # Weekly tasks
        schedule.every().monday.at("09:00").do(lambda: self.run_async_task(self.weekly_customer_analysis()))
        
        # Monthly tasks
        schedule.every().day.at("00:00").do(self._check_monthly_task)
        
        print("✅ Scheduled tasks configured:")
        print("   • Hourly: Overdue check")
        print("   • Daily 9 AM: Compliance report")
        print("   • Monday 9 AM: Customer analysis")
        print("   • 1st of month: Monthly summary")
        print()
    
    def _check_monthly_task(self):
        """Check if it's the 1st of the month."""
        if datetime.now().day == 1:
            self.run_async_task(self.monthly_compliance_summary())
    
    def start(self):
        """Start the scheduler."""
        self.setup_schedule()
        
        print(f"📅 Scheduler started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 Scheduler stopped")

if __name__ == "__main__":
    scheduler = ScheduledTasks()
    scheduler.start()
