# 🏗️ System Architecture

Complete architecture overview of the automated agent system.

---

## 🎯 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  📧 Email  │  📁 File Drop  │  🌐 Webhook API  │  📱 Manual UI  │
└──────┬──────────────┬────────────────┬──────────────────┬────────┘
       │              │                │                  │
       └──────────────┴────────────────┴──────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  AUTOMATION LAYER  │
                    ├───────────────────┤
                    │ • File Watcher    │
                    │ • Scheduler       │
                    │ • Batch Processor │
                    │ • Webhook Server  │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │   ORCHESTRATOR    │
                    │  (Google ADK)     │
                    └─────────┬─────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
┌──────▼──────┐    ┌─────────▼────────┐    ┌───────▼──────┐
│   JANITOR   │    │   COMPLIANCE     │    │  ARBITRATOR  │
│   AGENT     │───▶│     AGENT        │───▶│    AGENT     │
│             │    │                  │    │              │
│ • OCR       │    │ • MSMED Act      │    │ • Scoring    │
│ • Voice     │    │ • Interest       │    │ • Strategy   │
│ • GSTIN     │    │ • Alerts         │    │ • HITL       │
└─────────────┘    └──────────────────┘    └───────┬──────┘
                                                    │
                                           ┌────────▼────────┐
                                           │   COLLECTOR     │
                                           │     AGENT       │
                                           │                 │
                                           │ • Messages      │
                                           │ • WhatsApp      │
                                           │ • Tiered        │
                                           └────────┬────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────┐
                    │                               │               │
            ┌───────▼────────┐            ┌────────▼────────┐     │
            │  VECTOR MEMORY │            │ RELATIONAL DB   │     │
            │   (ChromaDB)   │            │   (SQLite)      │     │
            │                │            │                 │     │
            │ • Semantic     │            │ • Transactions  │     │
            │ • Context      │            │ • Customers     │     │
            │ • History      │            │ • Messages      │     │
            └────────────────┘            └─────────────────┘     │
                                                                   │
                                                    ┌──────────────▼──┐
                                                    │  OUTPUT LAYER   │
                                                    ├─────────────────┤
                                                    │ • WhatsApp      │
                                                    │ • Dashboard     │
                                                    │ • Reports       │
                                                    │ • API Response  │
                                                    └─────────────────┘
```

---

## 🤖 Agent Workflow

### Full Processing Pipeline

```
1. INGESTION
   ├─ Invoice Image/PDF → Janitor Agent
   │  ├─ Gemini Vision OCR
   │  ├─ HuggingFace Qwen2.5-VL
   │  └─ GSTIN Validation
   │
   └─ Extracted Data
      ├─ Vendor Name
      ├─ Amount
      ├─ Invoice Number
      ├─ Dates
      └─ GSTIN

2. COMPLIANCE CHECK
   ├─ Compliance Agent
   │  ├─ Calculate days overdue
   │  ├─ Calculate interest (3x Bank Rate)
   │  ├─ Check MSMED Act Section 16
   │  └─ Flag Section 43B(h) violations
   │
   └─ Compliance Status
      ├─ Status: pending/overdue/paid
      ├─ Days overdue
      ├─ Interest amount
      └─ Legal flag

3. STRATEGY EVALUATION
   ├─ Arbitrator Agent
   │  ├─ Calculate relationship score (0-100)
   │  ├─ Calculate transaction risk (0-100)
   │  ├─ Apply decision matrix
   │  └─ Determine HITL requirement
   │
   └─ Strategy Recommendation
      ├─ grant_grace_period
      ├─ diplomatic_escalation
      ├─ aggressive_recovery
      └─ standard_process

4. MESSAGE GENERATION
   ├─ Collector Agent
   │  ├─ Determine tier (friendly/formal/legal)
   │  ├─ Generate message text
   │  └─ Check auto-approval eligibility
   │
   └─ Message Output
      ├─ Message text
      ├─ Tier
      └─ HITL approval flag

5. DELIVERY
   ├─ Auto-Approve (if eligible)
   │  └─ Send WhatsApp message
   │
   └─ HITL Queue (if required)
      └─ Wait for human approval
```

---

## 🔄 Automation Workflows

### 1. File Watcher Workflow

```
New File Detected
       │
       ▼
Check File Type
       │
       ├─ Image/PDF → process_invoice()
       └─ Audio → process_voice()
       │
       ▼
Full Agent Pipeline
       │
       ├─ Success → Log result
       └─ Error → Log error
       │
       ▼
Auto-Approval Check
       │
       ├─ Low-risk → Send immediately
       └─ High-risk → Queue for HITL
```

### 2. Scheduler Workflow

```
Hourly:
  └─ Check overdue transactions
     └─ Update status
     └─ Generate messages

Daily 9 AM:
  └─ Compliance report
     ├─ Total receivables
     ├─ Overdue count
     ├─ Interest accrued
     └─ Critical alerts

Monday 9 AM:
  └─ Customer analysis
     ├─ Top 10 by value
     ├─ Relationship scores
     └─ Payment patterns

1st of Month:
  └─ Monthly summary
     ├─ Compliance rate
     ├─ MSMED violations
     └─ Financial metrics
```

### 3. Batch Processing Workflow

```
Directory Scan
       │
       ▼
Find Invoice Files
       │
       ▼
Parallel Processing (N workers)
       │
       ├─ Worker 1 → Invoice A
       ├─ Worker 2 → Invoice B
       ├─ Worker 3 → Invoice C
       └─ Worker N → Invoice N
       │
       ▼
Collect Results
       │
       ▼
Generate Summary
       │
       └─ Save to JSON
```

### 4. Webhook API Workflow

```
HTTP Request
       │
       ▼
Validate Payload
       │
       ▼
Decode/Parse Data
       │
       ▼
Process Invoice
       │
       ▼
Return JSON Response
       │
       ├─ Success: transaction_id, status
       └─ Error: error message
```

---

## 💾 Data Flow

### Transaction Lifecycle

```
1. CREATION
   ├─ Source: Image/Voice/API/Manual
   ├─ Status: pending
   └─ Store in SQLite

2. COMPLIANCE CHECK
   ├─ Calculate overdue days
   ├─ Calculate interest
   └─ Update status: overdue (if applicable)

3. STRATEGY EVALUATION
   ├─ Score customer relationship
   ├─ Assess transaction risk
   └─ Recommend action

4. MESSAGE GENERATION
   ├─ Determine tier
   ├─ Generate text
   └─ Store in Communications table

5. APPROVAL
   ├─ Auto-approve (if eligible)
   └─ HITL queue (if required)

6. DELIVERY
   ├─ Send WhatsApp message
   └─ Update delivery_status: sent

7. PAYMENT
   ├─ Manual update
   └─ Status: paid
```

### Memory Architecture

```
┌─────────────────────────────────────┐
│         HYBRID MEMORY               │
├─────────────────────────────────────┤
│                                     │
│  VECTOR MEMORY (ChromaDB)           │
│  ├─ Semantic search                 │
│  ├─ Transaction context             │
│  ├─ Communication history           │
│  └─ Relationship patterns           │
│                                     │
│  RELATIONAL DB (SQLite)             │
│  ├─ Structured facts                │
│  ├─ Transactions table              │
│  ├─ Customers table                 │
│  └─ Communications table            │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔐 Security & Safety

### HITL Gates

```
Decision Point → Check Criteria → Route

Criteria:
├─ Message Type
│  ├─ Legal notice → Always HITL
│  ├─ Formal notice → HITL if valuable customer
│  └─ Friendly reminder → Auto-approve if < ₹10k
│
├─ Transaction Amount
│  ├─ > ₹50,000 → HITL
│  └─ < ₹50,000 → Check other criteria
│
└─ Customer Value
   ├─ Relationship score > 70 → HITL
   └─ Relationship score < 70 → Auto-approve
```

### Audit Trail

```
Every Action Logged:
├─ Transaction creation
├─ Compliance checks
├─ Strategy decisions
├─ Message generation
├─ Approval decisions
└─ Delivery status

Stored in:
├─ Database timestamps
├─ Agent attribution
└─ Status history
```

---

## 🚀 Scalability

### Current Capacity

```
Single Instance:
├─ File Watcher: Real-time processing
├─ Scheduler: Hourly/Daily/Weekly tasks
├─ Batch Processor: ~0.5 files/sec (5 workers)
└─ Webhook API: ~10 req/sec
```

### Scaling Options

```
Horizontal Scaling:
├─ Multiple file watchers (different folders)
├─ Load-balanced webhook servers
└─ Distributed batch processing

Vertical Scaling:
├─ Increase batch workers (10-20)
├─ Faster LLM provider
└─ Database optimization

Cloud Deployment:
├─ Google Cloud Run (serverless)
├─ Vertex AI (agent hosting)
└─ Cloud SQL (managed database)
```

---

## 🔌 Integration Points

### Input Integrations

```
1. Email
   └─ Forward to webhook → Auto-process

2. ERP Systems
   └─ Export to watched folder → Auto-process

3. Accounting Software
   └─ API push to webhook → Auto-process

4. Mobile App
   └─ Upload via API → Auto-process
```

### Output Integrations

```
1. WhatsApp Business API
   └─ Send recovery messages

2. Dashboard
   └─ Real-time monitoring

3. Reporting Tools
   └─ Export compliance data

4. ERP Systems
   └─ Update payment status
```

---

## 📊 Performance Metrics

### Key Metrics

```
Processing:
├─ Invoice processing time: ~3-5s
├─ Batch throughput: 0.5 files/sec
└─ API response time: <2s

Automation:
├─ File detection latency: <1s
├─ Compliance check frequency: Hourly
└─ Auto-approval rate: ~60%

Accuracy:
├─ OCR accuracy: ~95%
├─ GSTIN validation: 100% (format)
└─ Compliance calculation: 100%
```

---

## 🛠️ Technology Stack

```
┌─────────────────────────────────────┐
│         APPLICATION LAYER           │
├─────────────────────────────────────┤
│ • Streamlit (Dashboard)             │
│ • Flask (Webhook API)               │
│ • Python Schedule (Scheduler)       │
│ • Watchdog (File Watcher)           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│           AGENT LAYER               │
├─────────────────────────────────────┤
│ • Google ADK (Framework)            │
│ • Async/Await (Concurrency)         │
│ • BaseAgent (Interface)             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│            AI LAYER                 │
├─────────────────────────────────────┤
│ • Gemini 1.5 Flash (Vision)         │
│ • HuggingFace Qwen2.5-VL (Vision)   │
│ • ChromaDB (Vector Embeddings)      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          STORAGE LAYER              │
├─────────────────────────────────────┤
│ • SQLite (Relational)               │
│ • ChromaDB (Vector)                 │
│ • File System (Raw data)            │
└─────────────────────────────────────┘
```

---

## 📈 Future Enhancements

### Planned Features

```
1. Advanced Analytics
   ├─ Predictive payment modeling
   ├─ Customer churn prediction
   └─ Cash flow forecasting

2. Multi-Channel Communication
   ├─ Email integration
   ├─ SMS fallback
   └─ Voice calls

3. Enhanced Automation
   ├─ ML-based auto-approval
   ├─ Dynamic threshold adjustment
   └─ Anomaly detection

4. Enterprise Features
   ├─ Multi-tenant support
   ├─ Role-based access control
   └─ Advanced reporting
```

---

This architecture supports:
✅ Real-time processing
✅ Scheduled automation
✅ Bulk operations
✅ External integrations
✅ Human oversight
✅ Audit compliance
