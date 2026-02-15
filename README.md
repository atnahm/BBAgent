# Bharat Biz-Agent

> AI-powered invoice processing and compliance automation for Indian MSMEs

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

Bharat Biz-Agent is a production-ready multi-agent system that automates invoice processing, compliance monitoring, and payment recovery for Indian MSMEs. Built with Google ADK, it addresses the ₹30 Lakh Crore credit gap through intelligent automation.

### Key Features

- **Multimodal Data Ingestion**: Extract data from images, PDFs, and voice notes (Hinglish support)
- **MSMED Act Compliance**: Automatic 45-day payment limit tracking with interest calculation
- **Smart Automation**: 60% auto-approval rate with human-in-the-loop for critical decisions
- **Real-time Processing**: File watcher for instant invoice processing
- **Scheduled Reports**: Daily, weekly, and monthly compliance reports
- **REST API**: Webhook endpoints for external system integration
- **Production Ready**: Docker deployment, monitoring, and automated backups

## Quick Start

### Prerequisites

- Python 3.10+
- 4GB RAM (8GB recommended)
- API key from [HuggingFace](https://huggingface.co/settings/tokens) or [Google Gemini](https://makersuite.google.com/app/apikey)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd BBAgent

# Install dependencies
pip install -r backend/requirements.txt
pip install schedule watchdog flask psutil

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Verify setup
python quick_test.py
```

### Running the System

**Option 1: Quick Start (Development)**
```bash
# Start all services
start_production.bat  # Windows
./start_production.sh # Linux/Mac
```

**Option 2: Docker (Production)**
```bash
docker-compose up -d
```

**Option 3: Individual Services**
```bash
# Terminal 1: File watcher
python automate.py

# Terminal 2: Scheduler
python scheduler.py

# Terminal 3: API server
python webhook_server.py

# Terminal 4: Dashboard
streamlit run streamlit_app.py
```

### Verify Deployment

```bash
# Run health check
python health_check.py

# Access services
# Dashboard: http://localhost:8501
# API: http://localhost:5000
# Health: http://localhost:5000/health
```

## Architecture

### Multi-Agent System

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  JANITOR    │───▶│  COMPLIANCE  │───▶│ ARBITRATOR  │───▶│  COLLECTOR   │
│             │    │              │    │             │    │              │
│ • OCR       │    │ • MSMED Act  │    │ • Scoring   │    │ • Messages   │
│ • Voice     │    │ • Interest   │    │ • Strategy  │    │ • WhatsApp   │
│ • GSTIN     │    │ • Alerts     │    │ • HITL      │    │ • Tiered     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

### Automation Modes

1. **File Watcher** (`automate.py`) - Real-time invoice processing
2. **Scheduler** (`scheduler.py`) - Automated reports (hourly/daily/weekly)
3. **Batch Processor** (`batch_processor.py`) - Bulk processing with parallel workers
4. **Webhook API** (`webhook_server.py`) - REST endpoints for integrations
5. **Email Integration** (`email_integration.py`) - Auto-fetch from email
6. **Monitoring** (`monitoring_dashboard.py`) - Real-time system health

### Technology Stack

- **Framework**: Google ADK (Agent Development Kit)
- **LLM**: Gemini 1.5 Flash / HuggingFace Qwen2.5-VL
- **Vector DB**: ChromaDB (local)
- **Database**: SQLite with SQLAlchemy
- **UI**: Streamlit
- **API**: Flask
- **Automation**: Python Schedule, Watchdog

## Usage

### Processing Invoices

**Automatic (File Watcher)**
```bash
# Drop invoice in temp/ folder
# System processes automatically
# Low-risk: Auto-approved
# High-risk: Queued for HITL
```

**Manual (Dashboard)**
1. Open http://localhost:8501
2. Go to "Upload Invoice"
3. Upload image/PDF
4. Review extracted data
5. Approve messages if needed

**Bulk Processing**
```bash
python batch_processor.py ./invoices --workers 10
```

**API Integration**
```bash
curl -X POST http://localhost:5000/api/v1/invoice/upload \
  -H "Content-Type: application/json" \
  -d '{"file_data": "base64_encoded_image", "file_type": "image"}'
```

### Monitoring

```bash
# Real-time monitoring
python monitoring_dashboard.py --interval 30

# Export metrics
python monitoring_dashboard.py --export
```

### Backup & Restore

```bash
# Create backup
python backup_script.py backup

# List backups
python backup_script.py list

# Restore backup
python backup_script.py restore --timestamp 20240115_143022
```

## Configuration

### Environment Variables

Edit `backend/.env`:

```bash
# LLM Provider (choose one)
LLM_PROVIDER=huggingface  # or gemini

# API Keys
HUGGINGFACE_API_KEY=your_token_here
GEMINI_API_KEY=your_key_here

# Database
DATABASE_PATH=./data/biz_agent.db
CHROMA_DB_PATH=./data/chroma_db

# WhatsApp (optional)
WHATSAPP_MOCK_MODE=true
WHATSAPP_API_KEY=your_token

# GSTIN Validation (optional)
GSTIN_MOCK_MODE=true
GST_API_KEY=your_key
```

### Auto-Approval Rules

Edit `automate.py` (line 150):

```python
# Default: Auto-approve friendly reminders < ₹10,000
if comm.message_type == 'friendly_reminder' and txn.amount < 10000:
    # Auto-approve
```

### Schedule Times

Edit `scheduler.py` (line 180):

```python
# Default: Daily report at 9 AM
schedule.every().day.at("09:00").do(...)
```

## API Reference

### Endpoints

**Health Check**
```
GET /health
```

**Upload Invoice**
```
POST /api/v1/invoice/upload
Content-Type: application/json

{
  "file_data": "base64_encoded_file",
  "file_type": "image",
  "filename": "invoice.jpg"
}
```

**Manual Entry**
```
POST /api/v1/invoice/manual
Content-Type: application/json

{
  "vendor_name": "ABC Corp",
  "amount": 50000,
  "invoice_number": "INV-001",
  "invoice_date": "2024-01-15",
  "payment_terms": "45 days"
}
```

**Get Transactions**
```
GET /api/v1/transactions?status=overdue&limit=50
```

**Compliance Report**
```
GET /api/v1/compliance/report
```

## Production Deployment

### Docker Compose (Recommended)

```bash
# Configure
cp backend/.env.example backend/.env
# Edit backend/.env

# Deploy
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f
```

### Windows Service

```bash
# Install NSSM
choco install nssm

# Run installer
install_services.bat  # As Administrator
```

### Cloud Deployment

See [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for:
- Google Cloud Platform (Cloud Run, Vertex AI)
- AWS (ECS Fargate, Lambda)
- Azure (Container Instances)
- Kubernetes

## Testing

```bash
# Quick verification
python quick_test.py

# Full test suite
python test_automation.py

# Performance testing
python performance_test.py

# Health check
python health_check.py
```

## Performance

- **Invoice Processing**: 3-5 seconds
- **File Detection**: <1 second
- **API Response**: <2 seconds
- **Batch Throughput**: 0.5 files/sec (scalable to 20 workers)
- **Auto-Approval Rate**: ~60%
- **Uptime**: 24/7 operation

## Project Structure

```
BBAgent/
├── backend/
│   ├── agents/              # Google ADK agents
│   ├── core/                # Orchestrator
│   ├── memory/              # Database layer
│   ├── config.yaml          # Configuration
│   └── requirements.txt     # Dependencies
├── docs/                    # Documentation
├── data/                    # Databases (gitignored)
├── temp/                    # Watch folder (gitignored)
├── backups/                 # Backups (gitignored)
├── automate.py              # File watcher
├── scheduler.py             # Scheduled tasks
├── batch_processor.py       # Bulk processing
├── webhook_server.py        # REST API
├── streamlit_app.py         # Dashboard
├── monitoring_dashboard.py  # Monitoring
├── backup_script.py         # Backup/restore
├── docker-compose.yml       # Docker deployment
└── README.md                # This file
```

## Documentation

- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Production deployment
- **[AUTOMATION_GUIDE.md](docs/AUTOMATION_GUIDE.md)** - Automation reference
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture
- **[PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md)** - Pre-deployment checklist
- **[ADK_ENHANCEMENT.md](docs/ADK_ENHANCEMENT.md)** - Google ADK integration

## Troubleshooting

### Common Issues

**Services won't start**
```bash
# Check ports
netstat -an | findstr "5000 8501"

# Kill processes
taskkill /F /IM python.exe

# Restart
start_production.bat
```

**High memory usage**
```bash
# Check monitoring
python monitoring_dashboard.py

# Reduce workers
# Edit batch_processor.py: max_workers=5
```

**Processing errors**
```bash
# Check logs
docker-compose logs automation

# Verify API keys
cat backend/.env

# Test connection
python quick_test.py
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Google ADK for agent framework
- MSMED Act 2006 compliance logic
- Indian MSME sector research
- Gemini API for multimodal processing
- HuggingFace for open-source models

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/BBAgent/issues)
- **Documentation**: [docs/](docs/)
- **Email**: support@example.com

---

**Built with ❤️ for Indian MSMEs**
