# 🤖 Agent System Automation Guide

Complete automation setup for hands-free invoice processing and compliance monitoring.

---

## 🚀 Quick Start

### Windows
```bash
run_automation.bat
```

### Manual Start
```bash
# Option 1: File Watcher (Auto-process new invoices)
python automate.py

# Option 2: Scheduled Tasks (Reports)
python scheduler.py

# Option 3: Batch Processing
python batch_processor.py ./invoices

# Option 4: Webhook API
python webhook_server.py
```

---

## 📋 Automation Modes

### 1. File Watcher (`automate.py`)

**What it does:**
- Monitors `temp/` folder for new invoice files
- Automatically processes images and voice notes
- Runs full agent workflow (Janitor → Compliance → Arbitrator → Collector)
- Auto-approves low-risk messages (< ₹10,000 friendly reminders)
- Checks compliance every hour

**Usage:**
```bash
python automate.py
```

**Features:**
- ✅ Real-time invoice processing
- ✅ Automatic compliance monitoring
- ✅ Smart auto-approval for low-risk actions
- ✅ Hourly overdue checks

**Example:**
```
[09:15:23] 📄 New file detected: invoice_001.jpg
  🤖 Starting automated workflow...
  ✅ Invoice processed successfully!
     Transaction ID: 42
     Vendor: ABC Corp
     Amount: ₹25,000.00
     Strategy: standard_process
  📤 Message sent automatically
```

---

### 2. Scheduled Tasks (`scheduler.py`)

**What it does:**
- Hourly: Check for newly overdue transactions
- Daily 9 AM: Compliance report
- Monday 9 AM: Customer analysis
- 1st of month: Monthly summary

**Usage:**
```bash
python scheduler.py
```

**Schedule:**
```
✅ Scheduled tasks configured:
   • Hourly: Overdue check
   • Daily 9 AM: Compliance report
   • Monday 9 AM: Customer analysis
   • 1st of month: Monthly summary
```

**Sample Output:**
```
============================================================
📊 DAILY COMPLIANCE REPORT - 2024-01-15 09:00
============================================================

📈 SUMMARY:
   Total Transactions: 156
   Pending: 45
   Overdue: 12
   Total Receivables: ₹2,450,000.00
   Overdue Amount: ₹380,000.00
   Interest Accrued: ₹15,200.00

⚠️  CRITICAL ALERTS (3):
   • XYZ Ltd: ₹150,000.00 (52 days overdue)
   • ABC Corp: ₹95,000.00 (48 days overdue)
   • DEF Industries: ₹85,000.00 (46 days overdue)

📧 PENDING APPROVALS: 5 messages
============================================================
```

---

### 3. Batch Processor (`batch_processor.py`)

**What it does:**
- Process multiple invoices in parallel
- Bulk upload from folder
- Generate summary report
- Save results to JSON

**Usage:**
```bash
# Process all invoices in a folder
python batch_processor.py ./invoices

# Process recursively with custom workers
python batch_processor.py ./invoices --recursive --workers 10
```

**Arguments:**
- `directory`: Folder containing invoice files
- `--recursive` or `-r`: Process subdirectories
- `--workers` or `-w`: Max concurrent workers (default: 5)

**Example:**
```
============================================================
📦 BATCH PROCESSING - 25 files
============================================================

  📄 Processing: invoice_001.jpg
  ✅ Success: ABC Corp - ₹25,000.00
  📄 Processing: invoice_002.jpg
  ✅ Success: XYZ Ltd - ₹50,000.00
  ...

============================================================
📊 BATCH SUMMARY
============================================================
Total Files: 25
✅ Successful: 23
❌ Failed: 2
⏱️  Duration: 45.32s
📈 Throughput: 0.55 files/sec
============================================================

💾 Results saved to: invoices/batch_results_20240115_143022.json
```

---

### 4. Webhook Server (`webhook_server.py`)

**What it does:**
- REST API for external integrations
- Receive invoices from email, ERP, or other systems
- Manual entry endpoint
- Query transactions and compliance reports

**Usage:**
```bash
python webhook_server.py
```

**Endpoints:**

#### Health Check
```bash
GET /health
```

#### Upload Invoice
```bash
POST /api/v1/invoice/upload
Content-Type: application/json

{
  "file_data": "base64_encoded_image",
  "file_type": "image",
  "filename": "invoice.jpg",
  "metadata": {
    "source": "email",
    "sender": "vendor@example.com"
  }
}
```

#### Manual Entry
```bash
POST /api/v1/invoice/manual
Content-Type: application/json

{
  "vendor_name": "ABC Corp",
  "gstin": "29ABCDE1234F1Z5",
  "amount": 50000.00,
  "invoice_number": "INV-001",
  "invoice_date": "2024-01-15",
  "payment_terms": "45 days"
}
```

#### Get Transactions
```bash
GET /api/v1/transactions?status=overdue&limit=50
```

#### Compliance Report
```bash
GET /api/v1/compliance/report
```

**Example Integration:**
```python
import requests
import base64

# Upload invoice via API
with open('invoice.jpg', 'rb') as f:
    file_data = base64.b64encode(f.read()).decode()

response = requests.post('http://localhost:5000/api/v1/invoice/upload', json={
    'file_data': file_data,
    'file_type': 'image',
    'filename': 'invoice.jpg'
})

print(response.json())
# {'status': 'success', 'transaction_id': 42, ...}
```

---

## 🔧 Configuration

### Auto-Approval Rules

Edit `automate.py` to customize auto-approval logic:

```python
# Auto-approve friendly reminders for low-value transactions
if comm.message_type == 'friendly_reminder' and txn.amount < 10000:
    # Auto-approve
```

**Current Rules:**
- ✅ Friendly reminders < ₹10,000: Auto-approved
- ⏳ Formal notices: Require HITL
- ⏳ Legal notices: Always require HITL
- ⏳ High-value (> ₹50,000): Require HITL

### Schedule Customization

Edit `scheduler.py` to change schedule:

```python
# Hourly tasks
schedule.every().hour.do(lambda: self.run_async_task(self.hourly_overdue_check()))

# Daily tasks
schedule.every().day.at("09:00").do(lambda: self.run_async_task(self.daily_compliance_report()))

# Weekly tasks
schedule.every().monday.at("09:00").do(lambda: self.run_async_task(self.weekly_customer_analysis()))
```

---

## 🎯 Use Cases

### Use Case 1: Email Integration
**Setup:**
1. Configure email forwarding to webhook
2. Email server sends invoice attachments to API
3. System auto-processes and sends recovery messages

**Flow:**
```
Email → Webhook API → Agent System → WhatsApp Message
```

### Use Case 2: ERP Integration
**Setup:**
1. ERP exports invoices to shared folder
2. File watcher detects new files
3. Auto-processes and updates ERP via API

**Flow:**
```
ERP Export → File Watcher → Agent System → ERP Update
```

### Use Case 3: Bulk Migration
**Setup:**
1. Export historical invoices to folder
2. Run batch processor
3. Review results and approve messages

**Flow:**
```
Historical Data → Batch Processor → Review → Approve
```

### Use Case 4: Daily Operations
**Setup:**
1. Start file watcher for real-time processing
2. Start scheduler for daily reports
3. Review dashboard for pending approvals

**Flow:**
```
New Invoices → Auto-Process → Daily Report → HITL Review
```

---

## 📊 Monitoring

### Real-Time Logs

All automation scripts print real-time logs:

```
[09:15:23] 📄 New file detected: invoice_001.jpg
[09:15:25] ✅ Invoice processed successfully!
[09:15:26] 📧 FRIENDLY_REMINDER message generated
[09:15:27] ✅ Auto-approving friendly reminder (₹8,500.00)
```

### Dashboard Integration

Use Streamlit dashboard alongside automation:

```bash
# Terminal 1: Automation
python automate.py

# Terminal 2: Dashboard
streamlit run streamlit_app.py
```

### API Monitoring

Check webhook server health:

```bash
curl http://localhost:5000/health
```

---

## 🛡️ Safety Features

### Human-in-the-Loop Gates

**Always require approval:**
- Legal notices
- High-value transactions (> ₹50,000)
- Valuable customers (relationship score > 70)
- Formal notices to established customers

**Auto-approved:**
- Friendly reminders < ₹10,000
- Standard process for low-risk customers

### Error Handling

All automation scripts include:
- ✅ Exception handling
- ✅ Retry logic
- ✅ Error logging
- ✅ Graceful degradation

### Audit Trail

All actions logged to database:
- Transaction processing
- Message generation
- Approval decisions
- API calls

---

## 🚀 Production Deployment

### Option 1: Windows Service

Use NSSM to run as Windows service:

```bash
# Install NSSM
choco install nssm

# Create service
nssm install BharatBizAgent python automate.py
nssm start BharatBizAgent
```

### Option 2: Docker

```dockerfile
FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install -r backend/requirements.txt

# Run all automation
CMD python automate.py & python scheduler.py & python webhook_server.py
```

### Option 3: Cloud Deployment

Deploy to Google Cloud Run or AWS Lambda for serverless automation.

---

## 📝 Troubleshooting

### File Watcher Not Detecting Files

**Issue:** New files not processed
**Solution:** Check `temp/` folder exists and has write permissions

### Scheduler Not Running

**Issue:** Tasks not executing
**Solution:** Verify system time is correct, check schedule syntax

### Webhook Server Connection Refused

**Issue:** Cannot connect to API
**Solution:** Check port 5000 is not in use, verify firewall settings

### Auto-Approval Not Working

**Issue:** Messages stuck in pending
**Solution:** Check auto-approval rules in `automate.py`, verify transaction amounts

---

## 🎉 Summary

You now have a fully automated agent system with:

✅ **Real-time processing** - File watcher for instant invoice handling
✅ **Scheduled reports** - Daily, weekly, monthly compliance summaries
✅ **Bulk processing** - Parallel processing for large batches
✅ **API integration** - REST endpoints for external systems
✅ **Smart automation** - Auto-approval for low-risk actions
✅ **HITL safety** - Human oversight for critical decisions

**Start automating:**
```bash
run_automation.bat
```

Choose your mode and let the agents handle the rest!
