"""Scrapes web pages for legal compliance text to feed into the RAG engine."""
import logging
import asyncio
import urllib.request
from urllib.error import URLError
from bs4 import BeautifulSoup
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, vector_memory):
        self.vector_memory = vector_memory

    def _fetch_url_text(self, url: str) -> str:
        """Synchronously fetch and parse text from a URL."""
        try:
            req = urllib.request.Request(
                url,
                data=None,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read()
                soup = BeautifulSoup(html, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.extract()

                text = soup.get_text(separator=' ', strip=True)
                return text
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Naively chunk text into smaller segments."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) > chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    async def ingest_compliance_url(self, country_code: str, url: str):
        """Scrape URL, chunk text, and save into vector DB."""
        logger.info(f"Scraping compliance rules from {url} for country: {country_code}")

        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._fetch_url_text, url)

        if not text:
            logger.warning(f"No text extracted from {url}")
            return

        chunks = self._chunk_text(text)
        logger.info(f"Split {url} into {len(chunks)} chunks. Saving to RAG...")

        for i, chunk in enumerate(chunks):
            self.vector_memory.add_compliance_rule(
                country_code=country_code,
                rule_text=chunk,
                metadata={"source": url, "chunk_index": i}
            )

        logger.info(f"✅ Successfully ingested compliance rules from {url}.")
