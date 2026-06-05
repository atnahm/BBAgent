import pytest
import asyncio
from backend.compliance.web_scraper import WebScraper

class MockVectorMemory:
    def __init__(self):
        self.rules = []

    def add_compliance_rule(self, country_code, rule_text, metadata):
        self.rules.append({
            "country_code": country_code,
            "rule_text": rule_text,
            "metadata": metadata
        })

def test_web_scraper_chunking():
    vm = MockVectorMemory()
    scraper = WebScraper(vm)

    # Test chunking logic natively
    text = "This is a simple test text that we want to chunk based on a very small limit."
    chunks = scraper._chunk_text(text, chunk_size=20)

    # "This is a simple test" -> length 21 (split before 'test' -> "This is a simple")
    # Actually chunk logic splits on spaces.
    assert len(chunks) > 1
    assert "test" in chunks[1] or "test" in chunks[0]

@pytest.mark.asyncio
async def test_web_scraper_ingestion(monkeypatch):
    vm = MockVectorMemory()
    scraper = WebScraper(vm)

    # Mock the synchronous fetch to prevent real internet requests during CI tests
    def mock_fetch(url):
        return "Mocked Government Rule Text for Net 30 payments."

    monkeypatch.setattr(scraper, "_fetch_url_text", mock_fetch)

    await scraper.ingest_compliance_url("US", "https://mock.gov")

    assert len(vm.rules) == 1
    assert vm.rules[0]["country_code"] == "US"
    assert "Mocked Government" in vm.rules[0]["rule_text"]
    assert vm.rules[0]["metadata"]["source"] == "https://mock.gov"
