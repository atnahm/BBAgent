# Bharat Biz-Agent (Enterprise Edition)

> Generalized AI-powered Invoice Processing, Multi-Country Compliance, and Payment Recovery Automation.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker Support](https://img.shields.io/badge/Docker-Supported-blue.svg)](docker-compose.yml)

## Overview

Bharat Biz-Agent is a production-grade, headless, multi-agent architecture that automates invoice processing, compliance monitoring, and payment recovery for MSMEs globally. Originally built for the Indian MSMED Act, it has been generalized using a dynamic **RAG-based Compliance Engine**, supporting any country's late payment laws.

### Enterprise Features

- **Multi-Country Compliance Engine:** Dynamically scrapes and ingests government laws (e.g., US Net 30, UK Late Payment Directive, IN MSMED Act) directly into a ChromaDB vector store.
- **Advanced Multimodal Ingestion:** Extracts data from SQL databases, IMAP Email listeners, Watch-folders, PDFs, and Voice Notes.
- **Pluggable AI & Local LLM Support:** Privacy-first design allows swapping between HuggingFace, Google Gemini, or **100% Offline Local LLMs** (like Ollama or vLLM).
- **Pluggable Communication:** Dynamically dispatches recovery notices via WhatsApp, Email, or Webhooks based on customer data.
- **Enterprise Security Hardened:** API includes Rate Limiting, strict CORS/CSP headers, payload validation, and optional Streamlit UI Auth.
- **Headless Extensibility:** Fully controllable via a REST API, CLI tool, or an MCP (Model Context Protocol) Server for integration with external AI assistants.
- **Production Orchestration:** Shipped with a highly available 4-container `docker-compose` topology.

## Production Quick Start (Docker)

The fastest and most reliable way to run BBAgent is via Docker Compose. This spins up the 4 discrete microservices: `api`, `ui`, `worker`, and `chroma`.

```bash
# 1. Clone repository
git clone <repository-url>
cd BBAgent

# 2. Configure environment (Optional: add your HF/Gemini keys)
cp backend/.env.example backend/.env

# 3. Start the Enterprise Cluster
docker-compose up -d --build
```

**Accessing the Cluster:**
- **Enterprise Dashboard (UI):** [http://localhost:8501](http://localhost:8501)
- **REST API Endpoint:** `http://localhost:5000`
- **Vector DB (Chroma):** `http://localhost:8000`

## Configuration (Setup Wizard)

Navigate to the **Enterprise Dashboard** at `http://localhost:8501` and click **Setup Wizard** on the sidebar. From here, non-technical admins can configure:

1.  **AI/LLM Privacy Settings:** Switch between Cloud APIs or connect a local Ollama endpoint (e.g., `http://localhost:11434/api/generate`) for maximum data security.
2.  **External DB Integration:** Input an SQLAlchemy connection string to sync directly with your ERP (PostgreSQL, MySQL, SQL Server) and test the connection live.
3.  **Dynamic RAG Compliance:** Input a Country Code (e.g., `US`) and a URL to a government legal page. The system will automatically scrape, chunk, and embed the laws into the database.

## System Architecture

```text
┌─────────────────┐       ┌─────────────────┐      ┌───────────────┐
│ External ERP DB │  ───▶ │                 │ ───▶ │ Vector DB     │
├─────────────────┤       │   Orchestrator  │      │ (ChromaDB)    │
│ IMAP Inboxes    │  ───▶ │    (Worker)     │ ◀─── │ - RAG Rules   │
├─────────────────┤       │                 │      │ - Semantic Txn│
│ Watch Folders   │  ───▶ │                 │      └───────────────┘
└─────────────────┘       └───────┬─────────┘
                                  │                ┌───────────────┐
                                  ▼                │ Communications│
                          ┌───────────────┐        │ - Webhooks    │
                          │ SQLite DB     │ ──────▶│ - SMTP Email  │
                          │ (Structured)  │        │ - WhatsApp    │
                          └───────────────┘        └───────────────┘
```

## Security Hardening (Stage Three)

The REST API (`webhook_server.py`) has been hardened for production:
- **Rate Limiting:** Protects against DDoS (e.g., 10 uploads/minute).
- **Payload Validation:** Enforces strict 10MB file limits and MIME type checking (`.pdf`, `.jpg`, `.png`).
- **Security Headers:** Enforces `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, and XSS blocking.
- **UI Auth:** Toggle `auth_enabled: true` in `config.yaml` to lock down the Streamlit Dashboard.

## Headless Integrations

### 1. Command Line Interface (CLI)
View transaction statuses directly from the terminal.
```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
python backend/interfaces/cli.py list --status overdue
```

### 2. Model Context Protocol (MCP) Server
Expose the backend database and RAG engine directly to local LLMs (like Claude Desktop) via the MCP standard.
```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
python backend/interfaces/mcp_server.py
```

### 3. Webhook API
```bash
# Example Payload Upload
curl -X POST http://localhost:5000/api/v1/invoice/upload \
  -H "X-API-KEY: your_secure_key" \
  -H "Content-Type: application/json" \
  -d '{"file_data": "base64...", "filename": "invoice.pdf"}'
```

## Contributing

1. Fork the repository
2. Install testing dependencies (`pip install pytest pytest-asyncio`)
3. Run tests before submitting a PR: `python test_automation.py` and `python -m pytest backend/tests/`
4. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
