"""Generic Database Connector for continuous polling of external systems."""
import asyncio
from datetime import datetime
from sqlalchemy import create_engine, text
from backend.memory.relational_db import Transaction, Customer
from backend.config_loader import CONFIG

class GenericDBConnector:
    """Connects to external MSME SQL databases to poll for new invoices."""

    def __init__(self, orchestrator, connection_string: str, query: str):
        self.orchestrator = orchestrator
        self.engine = create_engine(connection_string)
        self.query = query
        self.poll_interval = 3600  # Poll every hour by default

    async def poll_external_db(self):
        """Continuously polls the external database for new invoices."""
        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Polling external database for invoices...")
                loop = asyncio.get_running_loop()

                # Execute blocking DB call in an executor thread
                def _fetch_rows():
                    with self.engine.connect() as conn:
                        result = conn.execute(text(self.query))
                        return result.fetchall()

                rows = await loop.run_in_executor(None, _fetch_rows)

                if rows:
                    print(f"  Found {len(rows)} potential invoices from external DB.")
                    await self._process_rows(rows)
            except Exception as e:
                print(f"❌ Database polling error: {str(e)}")

            await asyncio.sleep(self.poll_interval)

    async def _process_rows(self, rows):
        """Processes the structured rows and inserts them into the hybrid system."""
        db_session = self.orchestrator.db.get_session()
        try:
            for row in rows:
                # Assuming the external query maps to these standard fields:
                # id, vendor_name, tax_id, amount, currency, invoice_number, invoice_date, due_date, country_code
                invoice_number = str(row.invoice_number)

                # Skip if already exists
                existing = db_session.query(Transaction).filter_by(invoice_number=invoice_number).first()
                if existing:
                    continue

                # Fetch or create Customer
                customer = db_session.query(Customer).filter_by(tax_id=row.tax_id).first()
                if not customer:
                    customer = Customer(
                        name=row.vendor_name,
                        tax_id=row.tax_id,
                        country_code=getattr(row, 'country_code', 'US')
                    )
                    db_session.add(customer)
                    db_session.flush()

                # Insert Transaction
                txn = Transaction(
                    vendor_name=row.vendor_name,
                    tax_id=row.tax_id,
                    amount=row.amount,
                    currency=getattr(row, 'currency', 'USD'),
                    invoice_number=invoice_number,
                    invoice_date=row.invoice_date,
                    due_date=row.due_date,
                    country_code=getattr(row, 'country_code', 'US'),
                    status='pending',
                    source_type='external_db_poll',
                    customer_id=customer.id
                )
                db_session.add(txn)
                print(f"  ✅ Ingested invoice {invoice_number} from DB.")

            db_session.commit()
        except Exception as e:
            print(f"  ❌ Error processing DB rows: {str(e)}")
            db_session.rollback()
        finally:
            db_session.close()
