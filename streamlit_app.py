"""Streamlit Dashboard - Google ADK Powered."""
import streamlit as st
import sys
import os
import tempfile
import asyncio
from pathlib import Path
import plotly.express as px
import pandas as pd
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Import orchestrator
from core.orchestrator import Orchestrator
from memory.relational_db import Transaction, Communication

# Page config
st.set_page_config(
    page_title="Bharat Biz-Agent | Enterprise Compliance",
    page_icon="🇮🇳",
    layout="wide",
    menu_items={
        'About': "Enterprise-grade MSMED Act compliance and recovery platform"
    }
)

# Initialize orchestrator
@st.cache_resource
def get_orchestrator():
    """Initialize orchestrator (cached)."""
    print("Initializing Orchestrator...")
    return Orchestrator()

orchestrator = get_orchestrator()

# Sidebar - Professional Design
st.sidebar.title("🇮🇳 Bharat Biz-Agent")
st.sidebar.caption("Enterprise Compliance Platform")

# Advanced Features Section
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Advanced Features")

# Check if advanced features are configured
import os
hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
advanced_enabled = hf_api_key and hf_api_key != 'your_huggingface_api_key_here'

if advanced_enabled:
    st.sidebar.success("✅ Advanced Analytics Enabled")
    
    # Feature toggles with professional naming
    use_predictive_risk = st.sidebar.checkbox("Predictive Risk Analysis", value=True, help="Advanced risk assessment with predictive modeling")
    use_smart_messages = st.sidebar.checkbox("Smart Message Composer", value=True, help="Intelligent message generation with context awareness")
    use_strategic_insights = st.sidebar.checkbox("Strategic Insights", value=True, help="Data-driven strategic recommendations")
    
    # Store in session state
    st.session_state['use_ai_risk'] = use_predictive_risk
    st.session_state['use_ai_messages'] = use_smart_messages
    st.session_state['use_ai_strategy'] = use_strategic_insights
else:
    st.sidebar.info("ℹ️ Standard Mode Active")
    st.sidebar.caption("Contact admin to enable advanced features")
    st.session_state['use_ai_risk'] = False
    st.session_state['use_ai_messages'] = False
    st.session_state['use_ai_strategy'] = False

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📤 Upload Invoice", "✅ Approve Messages", "📝 Manual Entry", "📈 Reports"]
)

# Dashboard Page
if page == "📊 Dashboard":
    st.title("📊 Business Intelligence Dashboard")
    st.caption("Real-time compliance monitoring and analytics")
    
    # Get stats directly (synchronous database queries)
    db_session = orchestrator.db.get_session()
    
    all_transactions = db_session.query(Transaction).all()
    pending_approvals = db_session.query(Communication).filter_by(
        delivery_status='pending_approval'
    ).all()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_txns = len(all_transactions)
    overdue_txns = len([t for t in all_transactions if t.status == 'overdue'])
    pending_msgs = len(pending_approvals)
    compliance_rate = ((total_txns - overdue_txns) / total_txns * 100) if total_txns > 0 else 100

    with col1:
        st.metric("Total Transactions", total_txns)
    
    with col2:
        st.metric("Overdue Payments", overdue_txns, delta=f"-{overdue_txns}")
    
    with col3:
        st.metric("Pending Approvals", pending_msgs)
    
    with col4:
        total_amount = sum([t.amount for t in all_transactions if t.status != 'paid'])
        st.metric("Total Receivables", f"₹{total_amount:,.0f}")
    
    # Pending approvals alert
    if len(pending_approvals) > 0:
        st.warning(f"⚠️ {len(pending_approvals)} messages pending HITL approval")
    
    # System Status - Professional Layout
    st.subheader("🔧 System Components")
    agent_cols = st.columns(4)
    
    # Check advanced features status
    mode_label = "Advanced" if advanced_enabled else "Standard"
    
    agents = [
        ("📄 Data Extraction", "Invoice Processing", "✅ Operational", "OCR Enabled"),
        ("⚖️ Compliance Monitor", "MSMED Act Tracking", "✅ Operational", f"{mode_label} Analytics"),
        ("📧 Communication", "Recovery Management", "✅ Operational", f"{mode_label} Composer"),
        ("🎯 Strategy Engine", "Decision Support", "✅ Operational", f"{mode_label} Insights")
    ]
    
    for col, (name, role, status, feature) in zip(agent_cols, agents):
        with col:
            st.info(f"**{name}**\n\n{role}\n\n{status}\n\n{feature}")
    
    # Advanced Features Overview
    if advanced_enabled:
        st.markdown("---")
        st.subheader("🎯 Advanced Capabilities")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 Compliance Analytics**")
            st.markdown("""
            - Predictive Risk Modeling
            - Pattern Recognition
            - Executive Summaries
            - Anomaly Detection
            """)
        
        with col2:
            st.markdown("**💼 Smart Communications**")
            st.markdown("""
            - Context-Aware Messaging
            - Tone Optimization
            - Multi-Language Support
            - Cultural Adaptation
            """)
        
        with col3:
            st.markdown("**📈 Strategic Intelligence**")
            st.markdown("""
            - Data-Driven Recommendations
            - Negotiation Strategies
            - Relationship Analytics
            - Risk-Benefit Analysis
            """)
    
    db_session.close()

# Upload Invoice Page  
elif page == "📤 Upload Invoice":
    # Sidebar specific options for Upload Invoice
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Processing Options")
    
    # HuggingFace is the only provider now
    provider_code = "huggingface"  # Always use HuggingFace
    st.sidebar.info("Using HuggingFace Vision OCR for extraction")

    st.title("📤 Invoice Processing")
    st.caption("Automated data extraction and compliance analysis")
    
    from PIL import Image
    import io
    
    tab1, tab2 = st.tabs(["📷 Image Upload", "🎤 Voice Note"])
    
    with tab1:
        st.write("Upload invoice image or PDF for processing")
        uploaded_file = st.file_uploader("Upload Invoice Image", type=['jpg', 'jpeg', 'png', 'pdf'])
        
        if uploaded_file:
            # Show preview
            if uploaded_file.type == "application/pdf":
                st.error("❌ PDF files are not supported. Please upload an image (JPG/PNG) instead.")
                st.stop()  # Stop execution for PDFs
            else:
                try:
                    # Reset pointer and open image
                    uploaded_file.seek(0)
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Uploaded Invoice", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying image: {e}")
            
            if st.button("🔍 Process Invoice", type="primary"):
                with st.spinner("Analyzing with HuggingFace Vision OCR..."):
                    # Create temp file
                    suffix = ".pdf" if uploaded_file.type == "application/pdf" else ".jpg"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        uploaded_file.seek(0)
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    try:
                        # Process with ADK Orchestrator using selected provider
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(
                            orchestrator.process_invoice(
                                tmp_path, 
                                provider=provider_code
                            )
                        )
                        loop.close()
                        
                        # Clean up
                        os.unlink(tmp_path)
                        
                        if result['status'] == 'success':
                            st.success("✅ Invoice processed successfully!")
                            
                            # Create tabs for organized display
                            result_tabs = st.tabs(["📋 Extraction", "⚖️ Compliance", "💬 Message", "🎯 Strategy"])
                            
                            with result_tabs[0]:
                                st.subheader("Extracted Data")
                                extraction = result['ingestion']['extraction']
                                st.json(extraction)
                            
                            with result_tabs[1]:
                                st.subheader("Compliance Analysis")
                                compliance = result['compliance']['compliance']
                                
                                # Alert level
                                if compliance['alert_level'] != 'none':
                                    st.warning(f"⚠️ Alert Level: {compliance['alert_level'].upper()}")
                                else:
                                    st.success("✅ No compliance issues")
                                
                                # Display compliance details
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Days Overdue", compliance.get('days_overdue', 0))
                                    st.metric("Interest Amount", f"₹{compliance.get('interest_amount', 0):,.2f}")
                                with col2:
                                    st.metric("Status", compliance.get('status', 'N/A'))
                                    legal_flag = "Yes" if compliance.get('legal_flag') else "No"
                                    st.metric("Legal Flag", legal_flag)
                                
                                # Advanced Risk Analysis (if available)
                                if result['compliance'].get('ai_risk_analysis'):
                                    st.markdown("---")
                                    st.markdown("**📊 Predictive Risk Analysis**")
                                    ai_analysis = result['compliance']['ai_risk_analysis']
                                    if ai_analysis.get('status') == 'success':
                                        st.info(ai_analysis.get('ai_analysis', 'No analysis available'))
                                        st.caption("Powered by Advanced Analytics Engine")
                            
                            with result_tabs[2]:
                                st.subheader("Recovery Message")
                                if result.get('message'):
                                    msg = result['message']
                                    
                                    # Show message type
                                    if msg.get('ai_generated'):
                                        st.success("✨ Smart Composer - Context-Optimized Message")
                                    else:
                                        st.info("📋 Standard Template Message")
                                    
                                    st.code(msg['message_text'], language=None)
                                    
                                    # HITL status
                                    if msg['requires_hitl_approval']:
                                        st.warning("🔒 Message queued for HITL approval")
                                    else:
                                        st.success("✅ Auto-approved")
                                    
                                    # Message details
                                    st.caption(f"Tier: {msg.get('tier', 'N/A')} | Phone: {msg.get('phone_number', 'N/A')}")
                                else:
                                    st.info("No message generated")
                            
                            with result_tabs[3]:
                                st.subheader("Strategic Recommendation")
                                strategy = result['strategy']
                                
                                # Show strategy type
                                if strategy.get('ai_recommendation'):
                                    st.success("📈 Strategic Intelligence - Advanced Analysis")
                                    st.markdown(strategy['ai_recommendation'])
                                    
                                    # Additional metrics
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Relationship Score", f"{strategy.get('relationship_score', 0)}/100")
                                    with col2:
                                        st.metric("Risk Score", f"{strategy.get('transaction_risk_score', 0)}/100")
                                    with col3:
                                        st.metric("Customer Tier", strategy.get('customer_tier', 'N/A').upper())
                                else:
                                    st.info("📋 Standard Analysis")
                                    st.markdown(f"**Recommendation:** {strategy['recommendation']}")
                                    st.markdown(f"**Reasoning:** {strategy['reasoning']}")
                        else:
                            st.error(f"Error: {result.get('error')}")
                    
                    except Exception as e:
                        st.error(f"An error occurred during processing: {e}")
    
    with tab2:
        audio_file = st.file_uploader(
            "Upload voice note",
            type=['mp3', 'wav', 'm4a']
        )
        
        if audio_file and st.button("🎙️ Transcribe & Extract"):
            with st.spinner("Processing voice note..."):
                temp_path = Path("temp") / audio_file.name
                temp_path.write_bytes(audio_file.read())
                
                result = orchestrator.run_sync(
                    orchestrator.process_invoice(
                        str(temp_path),
                        source_type='voice'
                    )
                )
                
                if result['status'] == 'success':
                    st.success("✅ Voice note processed!")
                    st.json(result['ingestion']['extraction'])
                    
                    # Compliance status
                    compliance = result['compliance']['compliance']
                    if compliance['alert_level'] != 'none':
                        st.warning(f"⚠️ Alert: {compliance['alert_level']}")
                    
                    # Strategy
                    strategy = result['strategy']
                    st.info(f"**Strategy**: {strategy['recommendation']}\n\n{strategy['reasoning']}")

# Approve Messages Page
elif page == "✅ Approve Messages":
    st.title("✅ Approve Messages (HITL)")
    st.caption("Human-in-the-Loop approval workflow")
    
    db_session = orchestrator.db.get_session()
    pending = db_session.query(Communication).filter_by(
        delivery_status='pending_approval'
    ).all()
    
    try:
        if len(pending) == 0:
            st.info("✨ No messages pending approval")
        else:
            for comm in pending:
                transaction = db_session.query(Transaction).get(comm.transaction_id)
                
                with st.expander(f"📧 {comm.message_type.upper()} - {transaction.vendor_name} (₹{transaction.amount:,.0f})"):
                    # ... (content same as before)
                    st.write(f"**Transaction ID:** {transaction.id}")
                    st.write(f"**Amount:** ₹{transaction.amount:,.0f}")
                    st.write(f"**Days Overdue:** {transaction.days_overdue}")
                    
                    st.write("**Message:**")
                    st.code(comm.message_text, language=None)
                    
                    col1, col2, col3 = st.columns([1, 1, 3])
                    
                    with col1:
                        if st.button("✅ Approve", key=f"approve_{comm.id}"):
                            comm.approval_status = 'approved'
                            comm.approved_by = 'User'
                            comm.approved_at = datetime.utcnow()
                            
                            # Send message (async)
                            send_result = orchestrator.run_sync(
                                orchestrator.collector.send_whatsapp_message(
                                    transaction.customer.phone_number,
                                    comm.message_text,
                                    comm.id
                                )
                            )
                            
                            comm.delivery_status = send_result.get('delivery_status', 'sent')
                            comm.sent_at = datetime.utcnow()
                            
                            db_session.commit()
                            st.success("✅ Approved and sent!")
                            st.rerun()
                    
                    with col2:
                        if st.button("✗ Reject", key=f"reject_{comm.id}"):
                            comm.approval_status = 'rejected'
                            comm.approved_by = 'User'
                            comm.approved_at = datetime.utcnow()
                            db_session.commit()
                            st.rerun()
                            
    finally:
        db_session.close()


# Manual Entry Page
elif page == "📝 Manual Entry":
    st.title("📝 Manual Transaction Entry")
    
    with st.form("manual_entry"):
        col1, col2 = st.columns(2)
        
        with col1:
            vendor_name = st.text_input("Vendor Name*")
            gstin = st.text_input("GSTIN")
            invoice_number = st.text_input("Invoice Number*")
        
        with col2:
            amount = st.number_input("Amount (₹)*", min_value=0.0, step=100.0)
            invoice_date = st.date_input("Invoice Date*")
            payment_terms = st.selectbox("Payment Terms", ["30 days", "45 days", "60 days", "90 days"])
        
        notes = st.text_area("Additional Notes")
        
        submitted = st.form_submit_button("💾 Save Transaction", type="primary")
        
        if submitted and vendor_name and invoice_number and amount > 0:
            db_session = orchestrator.db.get_session()
            try:
                from datetime import timedelta
                from memory.relational_db import Customer
                
                # Find or create customer
                customer = db_session.query(Customer).filter_by(name=vendor_name).first()
                if not customer:
                    customer = Customer(
                        name=vendor_name,
                        gstin=gstin,
                        total_transactions=0,
                        total_value=0.0
                    )
                    db_session.add(customer)
                    db_session.commit()
                
                # Calculate due date
                days = int(payment_terms.split()[0])
                due_date = invoice_date + timedelta(days=days)
                
                # Create transaction
                transaction = Transaction(
                    vendor_name=vendor_name,
                    gstin=gstin,
                    amount=amount,
                    invoice_number=invoice_number,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    source_type='manual',
                    customer_id=customer.id,
                    status='pending'
                )
                db_session.add(transaction)
                
                # Update customer
                customer.total_transactions += 1
                customer.total_value += amount
                
                db_session.commit()
                
                st.success(f"✅ Transaction saved! ID: {transaction.id}")
                
            except Exception as e:
                db_session.rollback()
                st.error(f"Error: {str(e)}")
            finally:
                db_session.close()

# Reports Page
elif page == "📈 Reports":
    st.title("📈 Compliance Reports")
    st.caption("Agent-generated analytics")
    
    db_session = orchestrator.db.get_session()
    transactions = db_session.query(Transaction).all()
    
    if len(transactions) > 0:
        # Prepare data
        txn_data = [{
            'id': t.id,
            'vendor': t.vendor_name,
            'amount': t.amount,
            'status': t.status,
            'days_overdue': t.days_overdue or 0,
            'interest': t.interest_amount or 0
        } for t in transactions]
        
        df = pd.DataFrame(txn_data)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Payment Status")
            status_counts = df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top 5 Overdue")
            overdue_df = df[df['days_overdue'] > 0].nlargest(5, 'days_overdue')
            if len(overdue_df) > 0:
                fig = px.bar(overdue_df, x='vendor', y='days_overdue', color='amount')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No overdue transactions")
        
        # Summary table
        st.subheader("Transaction Summary")
        st.dataframe(df, use_container_width=True)
        
    else:
        st.info("No transactions to report")
    
    db_session.close()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("🚀 Powered by Google ADK v1.25.0")
st.sidebar.caption("Built for Indian MSMEs")
