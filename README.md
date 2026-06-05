# Bharat Biz-Agent (Enterprise Edition)

> Generalized AI-powered Invoice Processing, Multi-Country Compliance, and Payment Recovery Automation.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docker Support](https://img.shields.io/badge/Docker-Supported-blue.svg)](docker-compose.yml)

## Overview

Bharat Biz-Agent is a production-grade, headless, multi-agent architecture that automates invoice processing, compliance monitoring, and payment recovery for MSMEs globally. Originally built for the Indian MSMED Act, it has been completely generalized using a dynamic **RAG-based Compliance Engine**, supporting any country's late payment laws.

### Enterprise Features

- **Multi-Country Compliance Engine:** Dynamically scrapes and ingests government laws (e.g., US Net 30, UK Late Payment Directive, IN MSMED Act) directly into a ChromaDB vector store using BeautifulSoup.
- **Advanced Multimodal Ingestion:** Extracts data from external SQL databases (PostgreSQL/MySQL), IMAP Email listeners, Watch-folders, PDFs, and Voice Notes.
- **Pluggable AI & Local LLM Support:** Privacy-first design allows swapping between HuggingFace, Google Gemini, or **100% Offline Local LLMs** (like Ollama or vLLM).
- **Pluggable Communication:** Dynamically dispatches recovery notices and internal risk escalations via WhatsApp, Email, or Webhooks.
- **Enterprise Security Hardened:** API includes Rate Limiting, strict CORS/CSP headers, payload validation (10MB limit, strict MIME), and optional UI Auth.
- **Headless Extensibility:** Fully controllable via a REST API, CLI tool, or an MCP (Model Context Protocol) Server for seamless integration with external AI assistants like Claude Desktop.
- **Production Orchestration:** Shipped with a highly available 4-container `docker-compose` topology.

---

## Quick Start (Docker Production)

The fastest and most reliable way to run BBAgent is via Docker Compose. This spins up 4 discrete microservices: `api`, `ui`, `worker`, and `chroma`.

```bash
# 1. Clone repository
git clone https://github.com/your-org/BBAgent.git
cd BBAgent

# 2. Configure environment variables
cp backend/.env.example backend/.env

# 3. Start the Enterprise Cluster
docker-compose up -d --build
```

### Accessing the Services

- **Enterprise Dashboard (Streamlit UI):** [http://localhost:8501](http://localhost:8501)
- **REST API Endpoint:** `http://localhost:5000`
- **Vector DB (Chroma):** `http://localhost:8000`

---

## Configuration (Setup Wizard)

The application is completely manageable without touching code. Navigate to the **Enterprise Dashboard** at `http://localhost:8501` and click **Setup Wizard** on the sidebar to configure:

1.  **AI/LLM Privacy Settings:** Switch between Cloud APIs or connect a local Ollama endpoint (e.g., `http://localhost:11434/api/generate`) for maximum data security.
2.  **External DB Integration:** Input an SQLAlchemy connection string to sync directly with your ERP (PostgreSQL, MySQL, SQL Server) and test the connection live.
3.  **Dynamic RAG Compliance:** Input a Country Code (e.g., `US`) and a URL to a government legal page. The system will automatically scrape, chunk, and embed the laws into the vector database.

---

## Headless Integrations

### 1. Command Line Interface (CLI)
System administrators can interact directly with the agent.
```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
python backend/interfaces/cli.py list --status overdue
python backend/interfaces/cli.py check  # Force compliance loop
```

### 2. Model Context Protocol (MCP) Server
Expose the backend database and RAG engine directly to local LLMs (like Claude Desktop) via the MCP standard.
```bash
export PYTHONPATH="$(pwd):$PYTHONPATH"
python backend/interfaces/mcp_server.py
```

### 3. Secured Webhook API
Integrate with your own internal tools securely.

```bash
# Upload an invoice payload
curl -X POST http://localhost:5000/api/v1/invoice/upload \
  -H "X-API-KEY: your_secure_key" \
  -H "Content-Type: application/json" \
  -d '{"file_data": "base64...", "filename": "invoice.pdf"}'
```

---

## Documentation

For a deep dive into how the multi-agent system and databases communicate, please see the [Architecture Guide](docs/ARCHITECTURE.md).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
