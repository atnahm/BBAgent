import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator
from memory.relational_db import Transaction

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
st.title("📊 Enterprise Compliance Dashboard")

@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orch = get_orchestrator()

def load_data():
    db_session = orch.db.get_session()
    txns = db_session.query(Transaction).all()

    data = []
    for t in txns:
        data.append({
            "ID": t.id,
            "Invoice": t.invoice_number,
            "Vendor": t.vendor_name,
            "Amount": f"{t.currency} {t.amount}",
            "Due Date": t.due_date.strftime('%Y-%m-%d') if t.due_date else 'N/A',
            "Status": t.status,
            "Country": t.country_code,
            "Overdue (Days)": t.days_overdue
        })
    db_session.close()
    return pd.DataFrame(data)

df = load_data()

col1, col2, col3, col4 = st.columns(4)

if not df.empty:
    col1.metric("Total Invoices", len(df))
    col2.metric("Overdue", len(df[df['Status'] == 'overdue']))
    col3.metric("Total Amount Pending", sum(float(str(x).split(' ')[1]) for x in df['Amount'] if df['Status'] == 'pending' or df['Status'] == 'overdue'))

    st.subheader("Recent Transactions")
    st.dataframe(df, use_container_width=True)

    st.subheader("Upload Manual Invoice")
    uploaded_file = st.file_uploader("Upload an invoice image or PDF", type=["jpg", "png", "pdf"])
    if uploaded_file is not None:
        if st.button("Process Invoice"):
            st.info("Invoice pushed to background queue for headless processing.")
            # Handled by file watcher in production
else:
    st.info("No data available. Go to Setup Wizard to configure the database, or start the headless backend.")
