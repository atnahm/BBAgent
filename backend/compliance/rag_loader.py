"""RAG-based Compliance Loader for different countries."""
from backend.memory.vector_store import VectorMemory
import logging

logger = logging.getLogger(__name__)

class ComplianceRAGLoader:
    """Simulates loading generalized compliance rules from internet into Vector DB."""

    def __init__(self, vector_memory: VectorMemory):
        self.vector_memory = vector_memory

    def load_mock_rules(self):
        """Loads sample rules for US, UK, IN to demonstrate generalization."""

        rules = [
            {
                "country_code": "US",
                "text": "In the United States, commercial invoices commonly follow 'Net 30' terms if not specified. Late payment interest is typically subject to state laws, but a standard 1.5% monthly (18% annually) is common. There is no federal mandate on commercial late fees like the Prompt Payment Act applies strictly to federal contracts.",
                "metadata": {"source": "mock_us_commercial_law", "topic": "payment_terms"}
            },
            {
                "country_code": "UK",
                "text": "Under the UK Late Payment of Commercial Debts (Interest) Act 1998, businesses can charge statutory interest at 8% plus the Bank of England base rate for late payments. The standard payment period is 30 days for public authorities and 60 days for business transactions unless otherwise agreed.",
                "metadata": {"source": "mock_uk_late_payment_directive", "topic": "payment_terms"}
            },
            {
                "country_code": "IN",
                "text": "Under the MSMED Act 2006, payments to micro and small enterprises must be made within 45 days. If delayed, the buyer is liable to pay compound interest with monthly rests at three times the bank rate notified by the RBI.",
                "metadata": {"source": "mock_in_msmed_act", "topic": "payment_terms"}
            }
        ]

        for rule in rules:
            self.vector_memory.add_compliance_rule(
                country_code=rule["country_code"],
                rule_text=rule["text"],
                metadata=rule["metadata"]
            )

        logger.info(f"Loaded {len(rules)} mock compliance rules into Vector DB.")

    def fetch_rules_for_country(self, country_code: str, query: str = "payment terms and interest"):
        """Fetches compliance rules for a specific country."""
        return self.vector_memory.search_compliance_rules(query=query, country_code=country_code)
