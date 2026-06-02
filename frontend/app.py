"""Main Entry Point for the Refactored Streamlit UI with Authentication."""
import streamlit as st
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from backend.config_loader import CONFIG

def check_password():
    """Returns `True` if the user had the correct password."""
    ui_config = CONFIG.get("ui", {})
    if not ui_config.get("auth_enabled", False):
        return True

    def password_entered():
        if (
            st.session_state["username"] == ui_config.get("username", "admin")
            and st.session_state["password"] == ui_config.get("password", "password")
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Username", on_change=password_entered, key="username")
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

if not check_password():
    st.stop()

st.set_page_config(
    page_title="BBAgent Setup & Dashboard",
    page_icon="🤖",
    layout="wide",
)

st.title("Welcome to Bharat Biz-Agent (Enterprise Edition)")
st.write("Navigate using the sidebar to configure the system or view the dashboard.")
st.info("👈 Please select a page from the sidebar to continue.")
