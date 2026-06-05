# System Architecture

Bharat Biz-Agent uses a highly decoupled, headless, event-driven architecture designed to operate across 4 core microservices.

## 1. Top-Level Topology

The system is deployed using `docker-compose.yml` into 4 distinct containers:

1.  **`bbagent-worker`**: Runs `automate.py`. This is the brain of the system. It continuously polls external SQL databases, IMAP email inboxes, and local watch-folders. It runs the compliance checks and auto-approves communication.
2.  **`bbagent-api`**: Runs `webhook_server.py`. A hardened Flask REST API providing external webhooks for ingestion.
3.  **`bbagent-ui`**: Runs `frontend/app.py`. A multi-page Streamlit application serving as the control plane (Setup Wizard, Dashboard, Analytics).
4.  **`bbagent-chroma`**: The official ChromaDB image acting as our persistent Vector Database for RAG and semantic search.

## 2. Hybrid Database Layer

To support any type of invoice and country logic without complex schema migrations, data is split:

*   **Relational DB (SQLite/SQLAlchemy):** Stores heavily structured, generalized transaction data (`vendor_name`, `amount`, `currency`, `tax_id`, `country_code`, `status`).
*   **Vector DB (ChromaDB):** Stores unstructured semantic data. Critically, we maintain strict separation of collections:
    *   `invoices_unstructured`: Raw text extracted from invoices (OCR).
    *   `compliance_rules`: Chunks of text scraped from government compliance sites via `web_scraper.py`.

## 3. Data Ingestion Pipeline

Data can enter the system through multiple headless routes:

*   **Web Scraper (Compliance Rules):** The `WebScraper` class takes a URL, fetches the HTML, uses `BeautifulSoup` to strip boilerplate, chunks the text, and embeds it into ChromaDB.
*   **Generic DB Connector:** Polls external ERP databases (PostgreSQL/MySQL) safely using a connection pool, ingesting new rows directly into the internal Relational DB.
*   **IMAP Email Listener:** Listens to a configured inbox for Unseen emails, stripping PDF/Image attachments and saving them to the `temp/` folder.
*   **Watchdog (File Watcher):** Monitors the `temp/` folder and triggers the `Orchestrator` when a file is dropped.
*   **REST API:** Accepts Base64 encoded files via HTTP POST.

## 4. Multi-Agent Orchestration

The `Orchestrator` manages four primary AI agents:

1.  **JanitorAgent:** Extracts structured JSON from raw files/voice notes (using Vision Models like Qwen2.5-VL).
2.  **ComplianceAgent:** Queries the `compliance_rules` collection in ChromaDB (RAG) based on the transaction's `country_code` to calculate interest and determine legal violations.
3.  **ArbitratorAgent:** The governance brain. Evaluates relationship scores vs. transaction risk. If the risk is high (>80), it triggers the `NotificationDispatcher` to escalate to an internal human team.
4.  **CollectorAgent:** Formats the final communication message (Friendly Reminder, Formal Notice, etc.).

## 5. Security & Privacy

*   **Local LLM Support:** `utils.py/AIModelClient` natively supports routing requests to a local `Ollama` or `vLLM` endpoint, keeping 100% of PII data offline.
*   **API Hardening:** `webhook_server.py` enforces Rate Limiting, HTTP Security Headers (HSTS, CSP), Payload sizing (10MB), and MIME validation.
*   **UI Auth:** Streamlit UI can be password-locked via `config.yaml` to prevent unauthorized database configuration.
