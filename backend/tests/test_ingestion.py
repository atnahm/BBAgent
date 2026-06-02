import pytest
import asyncio
from backend.ingestion.db_connector import GenericDBConnector

class MockOrchestrator:
    class DB:
        def get_session(self):
            class MockSession:
                def query(self, *args):
                    class MockQuery:
                        def filter_by(self, **kwargs):
                            return self
                        def first(self):
                            return None
                    return MockQuery()
                def add(self, *args):
                    pass
                def flush(self):
                    pass
                def commit(self):
                    pass
                def rollback(self):
                    pass
                def close(self):
                    pass
            return MockSession()
    def __init__(self):
        self.db = self.DB()

@pytest.mark.asyncio
async def test_db_connector_query():
    orch = MockOrchestrator()
    # Simple SQLite in-memory mock
    connector = GenericDBConnector(orch, "sqlite:///:memory:", "SELECT 'Vendor' as vendor_name, '123' as tax_id, 100.0 as amount, 'USD' as currency, 'INV-1' as invoice_number, '2023-01-01' as invoice_date, '2023-01-31' as due_date, 'US' as country_code")

    # We test the private _fetch_rows equivalent by executing the engine directly
    with connector.engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text(connector.query))
        rows = result.fetchall()

    assert len(rows) == 1
    assert rows[0].vendor_name == "Vendor"
    assert rows[0].invoice_number == "INV-1"
