"""
Real-Time Monitoring Dashboard
Track automation system performance and health.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time
import psutil
import json

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from memory.relational_db import Transaction, Customer, Communication, DatabaseManager
from config_loader import CONFIG

class SystemMonitor:
    """Monitor automation system health and performance."""
    
    def __init__(self):
        self.db = DatabaseManager(CONFIG['relational_db']['path'])
        self.start_time = datetime.now()
    
    def get_system_metrics(self):
        """Get system resource usage."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
    
    def get_processing_metrics(self):
        """Get invoice processing metrics."""
        db_session = self.db.get_session()
        
        try:
            # Last hour metrics
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            recent_txns = db_session.query(Transaction).filter(
                Transaction.created_at >= one_hour_ago
            ).all()
            
            # Last 24 hours
            one_day_ago = datetime.now() - timedelta(days=1)
            
            daily_txns = db_session.query(Transaction).filter(
                Transaction.created_at >= one_day_ago
            ).all()
            
            return {
                'last_hour': {
                    'total': len(recent_txns),
                    'by_source': self._count_by_source(recent_txns),
                    'avg_amount': sum(t.amount for t in recent_txns) / len(recent_txns) if recent_txns else 0
                },
                'last_24h': {
                    'total': len(daily_txns),
                    'by_source': self._count_by_source(daily_txns),
                    'avg_amount': sum(t.amount for t in daily_txns) / len(daily_txns) if daily_txns else 0
                }
            }
            
        finally:
            db_session.close()
    
    def get_compliance_metrics(self):
        """Get compliance status metrics."""
        db_session = self.db.get_session()
        
        try:
            all_txns = db_session.query(Transaction).all()
            
            pending = len([t for t in all_txns if t.status == 'pending'])
            overdue = len([t for t in all_txns if t.status == 'overdue'])
            paid = len([t for t in all_txns if t.status == 'paid'])
            
            total_receivables = sum(t.amount for t in all_txns if t.status != 'paid')
            total_interest = sum(t.interest_amount or 0 for t in all_txns)
            
            # MSMED violations
            violations = len([t for t in all_txns if (t.days_overdue or 0) > 45])
            
            return {
                'total_transactions': len(all_txns),
                'pending': pending,
                'overdue': overdue,
                'paid': paid,
                'total_receivables': total_receivables,
                'total_interest': total_interest,
                'msmed_violations': violations,
                'compliance_rate': ((len(all_txns) - overdue) / len(all_txns) * 100) if all_txns else 100
            }
            
        finally:
            db_session.close()
    
    def get_automation_metrics(self):
        """Get automation performance metrics."""
        db_session = self.db.get_session()
        
        try:
            # Message metrics
            all_comms = db_session.query(Communication).all()
            
            pending_approval = len([c for c in all_comms if c.delivery_status == 'pending_approval'])
            auto_approved = len([c for c in all_comms if c.approved_by == 'AutoSystem'])
            manual_approved = len([c for c in all_comms if c.approved_by and c.approved_by != 'AutoSystem'])
            
            auto_approval_rate = (auto_approved / len(all_comms) * 100) if all_comms else 0
            
            return {
                'total_messages': len(all_comms),
                'pending_approval': pending_approval,
                'auto_approved': auto_approved,
                'manual_approved': manual_approved,
                'auto_approval_rate': auto_approval_rate
            }
            
        finally:
            db_session.close()
    
    def get_customer_metrics(self):
        """Get customer relationship metrics."""
        db_session = self.db.get_session()
        
        try:
            customers = db_session.query(Customer).all()
            
            if not customers:
                return {
                    'total_customers': 0,
                    'avg_transactions_per_customer': 0,
                    'avg_customer_value': 0,
                    'top_customers': []
                }
            
            # Sort by value
            top_customers = sorted(customers, key=lambda c: c.total_value, reverse=True)[:5]
            
            return {
                'total_customers': len(customers),
                'avg_transactions_per_customer': sum(c.total_transactions for c in customers) / len(customers),
                'avg_customer_value': sum(c.total_value for c in customers) / len(customers),
                'top_customers': [
                    {
                        'name': c.name,
                        'total_value': c.total_value,
                        'transactions': c.total_transactions
                    }
                    for c in top_customers
                ]
            }
            
        finally:
            db_session.close()
    
    def _count_by_source(self, transactions):
        """Count transactions by source type."""
        sources = {}
        for txn in transactions:
            source = txn.source_type or 'unknown'
            sources[source] = sources.get(source, 0) + 1
        return sources
    
    def print_dashboard(self):
        """Print monitoring dashboard to console."""
        print("\033[2J\033[H")  # Clear screen
        
        print("="*80)
        print(f"{'BHARAT BIZ-AGENT MONITORING DASHBOARD':^80}")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^80}")
        print("="*80)
        
        # System metrics
        system = self.get_system_metrics()
        print(f"\n🖥️  SYSTEM HEALTH")
        print(f"   CPU Usage:    {system['cpu_percent']:.1f}%")
        print(f"   Memory Usage: {system['memory_percent']:.1f}%")
        print(f"   Disk Usage:   {system['disk_percent']:.1f}%")
        print(f"   Uptime:       {system['uptime_seconds']/3600:.1f} hours")
        
        # Processing metrics
        processing = self.get_processing_metrics()
        print(f"\n📊 PROCESSING METRICS")
        print(f"   Last Hour:    {processing['last_hour']['total']} invoices")
        print(f"   Last 24h:     {processing['last_24h']['total']} invoices")
        print(f"   Avg Amount:   ₹{processing['last_24h']['avg_amount']:,.2f}")
        
        # Compliance metrics
        compliance = self.get_compliance_metrics()
        print(f"\n⚖️  COMPLIANCE STATUS")
        print(f"   Total Transactions: {compliance['total_transactions']}")
        print(f"   Pending:            {compliance['pending']}")
        print(f"   Overdue:            {compliance['overdue']}")
        print(f"   Paid:               {compliance['paid']}")
        print(f"   Total Receivables:  ₹{compliance['total_receivables']:,.2f}")
        print(f"   Interest Accrued:   ₹{compliance['total_interest']:,.2f}")
        print(f"   MSMED Violations:   {compliance['msmed_violations']}")
        print(f"   Compliance Rate:    {compliance['compliance_rate']:.1f}%")
        
        # Automation metrics
        automation = self.get_automation_metrics()
        print(f"\n🤖 AUTOMATION PERFORMANCE")
        print(f"   Total Messages:     {automation['total_messages']}")
        print(f"   Pending Approval:   {automation['pending_approval']}")
        print(f"   Auto-Approved:      {automation['auto_approved']}")
        print(f"   Manual Approved:    {automation['manual_approved']}")
        print(f"   Auto-Approval Rate: {automation['auto_approval_rate']:.1f}%")
        
        # Customer metrics
        customers = self.get_customer_metrics()
        print(f"\n👥 CUSTOMER METRICS")
        print(f"   Total Customers:    {customers['total_customers']}")
        print(f"   Avg Transactions:   {customers['avg_transactions_per_customer']:.1f}")
        print(f"   Avg Customer Value: ₹{customers['avg_customer_value']:,.2f}")
        
        if customers['top_customers']:
            print(f"\n   Top 5 Customers:")
            for i, c in enumerate(customers['top_customers'], 1):
                print(f"   {i}. {c['name']}: ₹{c['total_value']:,.2f} ({c['transactions']} txns)")
        
        print("\n" + "="*80)
        print("Press Ctrl+C to stop monitoring")
        print("="*80)
    
    def export_metrics(self, filepath='monitoring_report.json'):
        """Export metrics to JSON file."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self.get_system_metrics(),
            'processing': self.get_processing_metrics(),
            'compliance': self.get_compliance_metrics(),
            'automation': self.get_automation_metrics(),
            'customers': self.get_customer_metrics()
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        print(f"📊 Metrics exported to {filepath}")
    
    def run(self, refresh_interval=10):
        """Run monitoring dashboard with auto-refresh."""
        print("🚀 Starting monitoring dashboard...")
        print(f"   Refresh interval: {refresh_interval}s")
        
        try:
            while True:
                self.print_dashboard()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='System Monitoring Dashboard')
    parser.add_argument('--interval', type=int, default=10, help='Refresh interval in seconds')
    parser.add_argument('--export', action='store_true', help='Export metrics to JSON and exit')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    if args.export:
        monitor.export_metrics()
    else:
        monitor.run(refresh_interval=args.interval)
