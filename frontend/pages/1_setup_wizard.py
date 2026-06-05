import streamlit as st
import yaml
from pathlib import Path

st.set_page_config(page_title="Setup Wizard", page_icon="⚙️", layout="wide")

st.title("⚙️ First-time Setup Wizard")
st.markdown("Configure your headless agent. This will update the `backend/config.yaml` file.")

config_path = Path(__file__).parent.parent.parent / "backend" / "config.yaml"

def load_config():
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def save_config(new_config):
    with open(config_path, 'w') as f:
        yaml.safe_dump(new_config, f, default_flow_style=False)
    st.success("Configuration saved successfully!")

config_data = load_config()

with st.form("setup_form"):
    st.subheader("1. General Database Settings")
    db_path = st.text_input("Relational DB Path", value=config_data.get("relational_db", {}).get("path", "${DATABASE_PATH}"))
    chroma_path = st.text_input("Vector DB Path", value=config_data.get("vector_db", {}).get("path", "${CHROMA_DB_PATH}"))

    st.subheader("2. External Database Ingestion")
    st.write("Configure connection to your existing MSME ERP or Accounting Database (PostgreSQL, MySQL, SQL Server).")
    ext_db_enabled = st.checkbox("Enable External Polling", value=config_data.get("ingestion", {}).get("database", {}).get("enabled", False))
    ext_db_conn = st.text_input("SQLAlchemy Connection String", value=config_data.get("ingestion", {}).get("database", {}).get("connection_string", "postgresql://user:pass@localhost:5432/erp"))
    ext_db_query = st.text_area("SQL Query to Poll Invoices", value=config_data.get("ingestion", {}).get("database", {}).get("query", "SELECT vendor_name, tax_id, amount, currency, invoice_number, invoice_date, due_date, country_code FROM invoices WHERE status = 'unprocessed'"))

    st.subheader("3. AI / LLM Provider (Privacy Settings)")
    current_provider = config_data.get("llm", {}).get("provider", "huggingface")
    provider_idx = ["huggingface", "gemini", "local"].index(current_provider) if current_provider in ["huggingface", "gemini", "local"] else 0
    llm_provider = st.selectbox("LLM Provider", ["huggingface", "gemini", "local"], index=provider_idx, help="Choose 'local' for 100% offline, privacy-preserving AI inference (e.g., Ollama).")
    local_endpoint = st.text_input("Local LLM Endpoint (if applicable)", value=config_data.get("llm", {}).get("local", {}).get("endpoint_url", "http://localhost:11434/api/generate"))

    st.subheader("3. Communication Channels")
    whatsapp_api = st.text_input("WhatsApp API Key", value=config_data.get("whatsapp", {}).get("api_key", ""), type="password")

    st.subheader("5. RAG / Web Scraper Rules")
    scrape_country = st.text_input("Country Code (e.g. US, UK, IN)", placeholder="US", max_chars=2)
    scrape_url = st.text_input("Enter Compliance URL to Scrape", placeholder="https://example.com/law")

    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("Save & Apply Configuration", type="primary")
    with col2:
        test_db = st.form_submit_button("Test External DB Connection")

    if test_db:
        if ext_db_enabled and ext_db_conn:
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent.parent.parent / 'backend'
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            from backend.ingestion.db_connector import GenericDBConnector
            try:
                if GenericDBConnector.test_connection(ext_db_conn):
                    st.success("✅ External Database Connection Successful!")
            except Exception as e:
                st.error(f"❌ Connection Failed: {e}")
        else:
            st.warning("Please enable external polling and provide a connection string first.")

    if submit:
        config_data.setdefault("relational_db", {})["path"] = db_path
        config_data.setdefault("vector_db", {})["path"] = chroma_path

        config_data.setdefault("ingestion", {}).setdefault("database", {})["enabled"] = ext_db_enabled
        config_data.setdefault("ingestion", {}).setdefault("database", {})["connection_string"] = ext_db_conn
        config_data.setdefault("ingestion", {}).setdefault("database", {})["query"] = ext_db_query

        config_data.setdefault("llm", {})["provider"] = llm_provider
        config_data.setdefault("llm", {}).setdefault("local", {})["endpoint_url"] = local_endpoint

        config_data.setdefault("whatsapp", {})["api_key"] = whatsapp_api
        save_config(config_data)

        if scrape_url and scrape_country:
            with st.spinner(f"Scraping {scrape_url}..."):
                import sys
                import asyncio
                from pathlib import Path
                backend_path = Path(__file__).parent.parent.parent / 'backend'
                if str(backend_path) not in sys.path:
                    sys.path.insert(0, str(backend_path))

                from backend.compliance.web_scraper import WebScraper
                from backend.memory.vector_store import VectorMemory
                from backend.config_loader import CONFIG

                # Resolve actual chroma path
                db_path_resolved = config_data.get("vector_db", {}).get("path", "")
                if "${CHROMA_DB_PATH}" in db_path_resolved:
                    import os
                    db_path_resolved = os.environ.get("CHROMA_DB_PATH", "./data/chroma")

                vm = VectorMemory(db_path=db_path_resolved)
                scraper = WebScraper(vm)

                try:
                    asyncio.run(scraper.ingest_compliance_url(scrape_country.upper(), scrape_url))
                    st.success(f"Successfully scraped and ingested rules for {scrape_country.upper()}!")
                except Exception as e:
                    st.error(f"Failed to scrape URL: {e}")
