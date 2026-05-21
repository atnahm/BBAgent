"""CLI tool for administrating the Headless BBAgent system."""
import argparse
import asyncio
from backend.core.orchestrator import Orchestrator
from backend.memory.relational_db import Transaction

async def list_transactions(status=None):
    orchestrator = Orchestrator()
    db_session = orchestrator.db.get_session()

    query = db_session.query(Transaction)
    if status:
        query = query.filter(Transaction.status == status)

    transactions = query.all()

    print(f"\n--- {len(transactions)} Transactions {'(' + status + ')' if status else ''} ---")
    for t in transactions:
        print(f"ID: {t.id} | Vendor: {t.vendor_name} | Amount: {t.currency} {t.amount} | Status: {t.status} | Overdue: {t.days_overdue} days")

    db_session.close()

async def trigger_compliance():
    # Reuse automate.py logic
    from automate import ComplianceMonitor
    orchestrator = Orchestrator()
    monitor = ComplianceMonitor(orchestrator)
    print("Forcing compliance check on pending/overdue invoices...")
    await monitor.check_all_transactions()
    print("Done.")

def main():
    parser = argparse.ArgumentParser(description="Headless BBAgent CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Subparser for listing
    list_parser = subparsers.add_parser("list", help="List invoices")
    list_parser.add_argument("--status", type=str, help="Filter by status (e.g. pending, overdue)")

    # Subparser for checking compliance
    subparsers.add_parser("check", help="Run compliance check on all pending transactions")

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    if args.command == "list":
        loop.run_until_complete(list_transactions(args.status))
    elif args.command == "check":
        loop.run_until_complete(trigger_compliance())
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
