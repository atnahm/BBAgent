import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator
from memory.relational_db import Transaction

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")
st.title("📈 Advanced Analytics & Reporting")

@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orch = get_orchestrator()

def get_data():
    db_session = orch.db.get_session()
    txns = db_session.query(Transaction).all()

    data = []
    for t in txns:
        data.append({
            "vendor": t.vendor_name,
            "amount": t.amount,
            "status": t.status,
            "days_overdue": t.days_overdue,
            "country": t.country_code
        })
    db_session.close()
    return pd.DataFrame(data)

df = get_data()

if df.empty:
    st.info("No transaction data available for analysis.")
else:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Transaction Status Distribution")
        status_counts = df['status'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index,
                    color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 5 Overdue Accounts")
        overdue_df = df[df['days_overdue'] > 0].nlargest(5, 'days_overdue')
        if len(overdue_df) > 0:
            fig = px.bar(overdue_df, x='vendor', y='days_overdue', color='amount',
                         title="Days Overdue per Vendor")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No overdue transactions found!")

    st.markdown("---")
    st.subheader("Country Compliance Breakdown")
    country_counts = df['country'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Transaction Count']
    fig_map = px.bar(country_counts, x='Country', y='Transaction Count', color='Country')
    st.plotly_chart(fig_map, use_container_width=True)
