# Bharat Biz-Agent POC

**Digital Munim for Indian MSMEs** - AI-powered ledger automation system

## 🎯 Overview

This POC demonstrates a multi-agent system that transforms "messy" MSME ledgers into structured financial automation, addressing the ₹30 Lakh Crore credit gap through intelligent automation.

### Key Features
- ✅ **Multimodal Data Ingestion**: Extract data from images, voice notes (Hinglish)
- ✅ **MSMED Act Compliance**: Automatic tracking of 45-day payment limits
- ✅ **Section 43B(h) Monitoring**: Tax disallowance risk alerts
- ✅ **WhatsApp Automation**: Tiered recovery messages
- ✅ **Human-in-the-Loop**: Safety gates for critical decisions
- ✅ **Relationship Preservation**: AI governance balancing recovery vs. relationships

## 🏗️ Architecture

### Four-Agent System

1. **Janitor Agent** - Multimodal data extraction
   - OCR for invoice images (Gemini 1.5 Flash Vision)
   - Voice note transcription (Hinglish support)
   - GSTIN validation

2. **Compliance Agent** - Regulatory monitoring
   - 45-day payment limit tracking (MSMED Act Section 16)
   - 3x Bank Rate interest calculation
   - Section 43B(h) tax risk alerts

3. **Collector Agent** - Recovery automation
   - Tiered WhatsApp messages (friendly → formal → legal)
   - Mock WhatsApp integration for POC
   - HITL approval for sensitive communications

4. **Arbitrator Agent** - Governance & relationship management
   - Customer value scoring
   - Risk-based decision matrix
   - Approval gates for high-value/high-risk actions

### Hybrid Memory Architecture
- **Vector DB** (ChromaDB): Semantic memory for transaction context
- **Relational DB** (SQLite): Structured facts (amounts, dates, status)

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Google Gemini API Key (free tier)

### Installation

1. **Clone & Navigate**
   ```bash
   cd d:\BBAgent
   ```

2. **Install Dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp backend/.env.example backend/.env
   ```
   
   Edit `backend/.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
   
   Get free API key: https://makersuite.google.com/app/apikey

4. **Run Streamlit Dashboard**
   ```bash
   streamlit run streamlit_app.py
   ```

## 📁 Project Structure

```
d:/BBAgent/
├── backend/
│   ├── agents/
│   │   ├── janitor_agent.py       # OCR + Voice extraction
│   │   ├── compliance_agent.py    # MSMED Act logic
│   │   ├── collector_agent.py     # WhatsApp messages
│   │   └── arbitrator_agent.py    # Governance
│   ├── core/
│   │   └── orchestrator.py        # Agent coordination
│   ├── memory/
│   │   ├── relational_db.py       # SQLite schemas
│   │   └── vector_store.py        # ChromaDB integration
│   ├── config.yaml                # System configuration
│   ├── config_loader.py           # Config parser
│   └── requirements.txt           # Dependencies
├── streamlit_app.py               # Dashboard UI
├── data/                          # Database files (auto-created)
└── temp/                          # Uploaded files (auto-created)
```

## 🎮 Usage

### 1. Upload Invoice
- Go to **"📤 Upload Invoice"** page
- Choose image or voice note
- AI extracts: Vendor, GSTIN, Amount, Dates
- Auto-validates GSTIN format

### 2. Compliance Monitoring
- System automatically checks 45-day payment limits
- Calculates interest (3x Bank Rate) for overdue payments
- Flags Section 43B(h) violations

### 3. Approve Messages
- Go to **"✅ Approve Messages"** page
- Review AI-generated WhatsApp messages
- Approve or reject before sending

### 4. Dashboard
- View payment status distribution
- Track total receivables
- Monitor pending approvals

## 🧪 Testing with Sample Data

### Test Invoice Image
Upload any invoice image with visible:
- Vendor name
- Amount
- Date
- GSTIN (optional)

### Test Voice Note (Hinglish Example)
Record: *"Sharma ji ko paanch hazaar rupaye diye, invoice number 123, date 10 February"*

## ⚙️ Configuration

Edit `backend/config.yaml` to customize:

```yaml
compliance:
  msmed_act:
    payment_limit_days: 45      # MSMED Act threshold
    interest_multiplier: 3       # 3x Bank Rate
    bank_rate_percent: 6.5       # Current RBI rate

safety:
  high_value_threshold: 50000   # INR threshold for HITL
  fraud_detection_enabled: true
```

## 🔒 Safety Features

- **Mock Mode**: WhatsApp integration runs in mock mode (no real messages sent)
- **GSTIN Validation**: Format validation + mock business lookup
- **HITL Gates**: Legal notices require human approval
- **Audit Trail**: All decisions logged to database

## 📊 Compliance Calculations

### Interest Calculation (MSMED Act Section 16)
```
Annual Interest Rate = 3 × Bank Rate (6.5%) = 19.5%
Interest = Amount × 0.195 × (Days Overdue / 365)
```

### Section 43B(h) Risk
Payments beyond 45 days may result in tax deduction disallowance for the buyer.

## 🛠️ Technology Stack (Free Tier)

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM | Google Gemini 1.5 Flash | Free (15 RPM) |
| Vector DB | ChromaDB | Free (local) |
| Database | SQLite | Free (local) |
| UI | Streamlit | Free |
| WhatsApp | Mock (POC) | Free |

## 📝 Roadmap

- [ ] Real WhatsApp Web integration (`wwebjs`)
- [ ] Production GSTIN API integration
- [ ] Multi-user authentication
- [ ] PDF invoice support
- [ ] Bulk upload processing
- [ ] Advanced analytics dashboard
- [ ] Email notifications

## 🤝 Contributing

This is a POC for demonstration purposes. For production deployment, consider:
- Real WhatsApp Business API
- Secure user authentication
- Cloud database (PostgreSQL)
- Production monitoring

## 📄 License

POC for educational and demonstration purposes.

## 🙏 Acknowledgments

- MSMED Act 2006 compliance logic
- Indian MSME sector research
- Gemini API for multimodal processing
