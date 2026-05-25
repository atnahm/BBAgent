"""Main Entry Point for the Refactored Streamlit UI."""
import streamlit as st
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

st.set_page_config(
    page_title="BBAgent Setup & Dashboard",
    page_icon="🤖",
    layout="wide",
)

st.title("Welcome to Bharat Biz-Agent (Enterprise Edition)")
st.write("Navigate using the sidebar to configure the system or view the dashboard.")

# We don't implement the full multipage app navigation here manually.
# Streamlit does this automatically via the `pages/` directory.

st.info("👈 Please select a page from the sidebar to continue.")
