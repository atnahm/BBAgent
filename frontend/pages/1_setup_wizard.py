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

    st.subheader("2. Communication Channels")
    whatsapp_api = st.text_input("WhatsApp API Key", value=config_data.get("whatsapp", {}).get("api_key", ""), type="password")

    st.subheader("3. RAG / Web Scraper Rules")
    mock_url = st.text_input("Enter Compliance URL to Scrape", placeholder="https://example.com/law")

    submit = st.form_submit_button("Save & Apply")

    if submit:
        config_data.setdefault("relational_db", {})["path"] = db_path
        config_data.setdefault("vector_db", {})["path"] = chroma_path
        config_data.setdefault("whatsapp", {})["api_key"] = whatsapp_api
        save_config(config_data)

        if mock_url:
            st.info(f"Triggering background scrape for {mock_url} (Check CLI logs)")
            # Normally we'd call `WebScraper.ingest_compliance_url` here.
