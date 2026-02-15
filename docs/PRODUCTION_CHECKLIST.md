# 🚀 Production Deployment Checklist

Complete checklist for taking your system to production.

---

## ✅ Pre-Deployment Checklist

### 1. Environment Configuration

- [ ] Copy `.env.example` to `.env`
- [ ] Set production API keys
  - [ ] `GEMINI_API_KEY` or `HUGGINGFACE_API_KEY`
  - [ ] `WHATSAPP_API_KEY` (if using real WhatsApp)
  - [ ] `GST_API_KEY` (if using real GSTIN validation)
- [ ] Set `WHATSAPP_MOCK_MODE=false` for production
- [ ] Set `GSTIN_MOCK_MODE=false` for production
- [ ] Configure database paths
- [ ] Set secure passwords/tokens

### 2. System Requirements

- [ ] Python 3.10+ installed
- [ ] 4GB RAM minimum (8GB recommended)
- [ ] 20GB disk space
- [ ] Stable internet connection
- [ ] Backup storage configured

### 3. Dependencies

- [ ] Install all requirements: `pip install -r backend/requirements.txt`
- [ ] Install automation packages: `pip install schedule watchdog flask psutil`
- [ ] Test imports: `python quick_test.py`

### 4. Database Setup

- [ ] Create `data/` directory
- [ ] Initialize SQLite database
- [ ] Initialize ChromaDB
- [ ] Test database connections
- [ ] Set up backup schedule

### 5. Security

- [ ] API keys stored securely (not in code)
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS enabled for webhook API
- [ ] Rate limiting configured
- [ ] Authentication implemented (if needed)
- [ ] Firewall rules configured

---

## 🐳 Docker Deployment (Recommended)

### Prerequisites
- [ ] Docker Desktop installed
- [ ] Docker Compose installed
- [ ] 4GB RAM allocated to Docker

### Steps

1. **Configure Environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with production values
   ```

2. **Build Images**
   ```bash
   docker-compose build
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Verify Services**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

5. **Test Endpoints**
   ```bash
   curl http://localhost:5000/health
   curl http://localhost:8501
   ```

### Post-Deployment

- [ ] Services running: `docker-compose ps`
- [ ] Logs clean: `docker-compose logs`
- [ ] Dashboard accessible: http://localhost:8501
- [ ] API accessible: http://localhost:5000
- [ ] Health check passing: http://localhost:5000/health

---

## 🪟 Windows Service Deployment

### Prerequisites
- [ ] NSSM installed: `choco install nssm`
- [ ] Python in system PATH
- [ ] Administrator privileges

### Steps

1. **Install Services**
   ```bash
   # File Watcher
   nssm install BharatBizAgent-Automation ^
     "C:\Python310\python.exe" ^
     "E:\BBAgent\automate.py"
   
   nssm set BharatBizAgent-Automation AppDirectory "E:\BBAgent"
   nssm set BharatBizAgent-Automation Start SERVICE_AUTO_START
   
   # Scheduler
   nssm install BharatBizAgent-Scheduler ^
     "C:\Python310\python.exe" ^
     "E:\BBAgent\scheduler.py"
   
   nssm set BharatBizAgent-Scheduler AppDirectory "E:\BBAgent"
   nssm set BharatBizAgent-Scheduler Start SERVICE_AUTO_START
   
   # Webhook API
   nssm install BharatBizAgent-Webhook ^
     "C:\Python310\python.exe" ^
     "E:\BBAgent\webhook_server.py"
   
   nssm set BharatBizAgent-Webhook AppDirectory "E:\BBAgent"
   nssm set BharatBizAgent-Webhook Start SERVICE_AUTO_START
   ```

2. **Start Services**
   ```bash
   nssm start BharatBizAgent-Automation
   nssm start BharatBizAgent-Scheduler
   nssm start BharatBizAgent-Webhook
   ```

3. **Verify Services**
   ```bash
   nssm status BharatBizAgent-Automation
   nssm status BharatBizAgent-Scheduler
   nssm status BharatBizAgent-Webhook
   ```

### Post-Deployment

- [ ] Services running in Services.msc
- [ ] Logs in Event Viewer
- [ ] Auto-start on boot configured
- [ ] Test file processing
- [ ] Test API endpoints

---

## ☁️ Cloud Deployment

### Google Cloud Platform

1. **Build and Push Image**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/bharat-biz-agent
   ```

2. **Deploy Services**
   ```bash
   # Webhook API
   gcloud run deploy bharat-biz-webhook \
     --image gcr.io/PROJECT_ID/bharat-biz-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY=your_key
   
   # Dashboard
   gcloud run deploy bharat-biz-dashboard \
     --image gcr.io/PROJECT_ID/bharat-biz-agent \
     --platform managed \
     --region us-central1 \
     --command streamlit \
     --args "run,streamlit_app.py,--server.address=0.0.0.0"
   ```

3. **Setup Cloud Scheduler**
   ```bash
   gcloud scheduler jobs create http daily-compliance \
     --schedule="0 9 * * *" \
     --uri="https://YOUR-WEBHOOK-URL/api/v1/compliance/report"
   ```

### Post-Deployment

- [ ] Services deployed
- [ ] URLs accessible
- [ ] Environment variables set
- [ ] Scheduler configured
- [ ] Monitoring enabled

---

## 📊 Monitoring Setup

### 1. Real-Time Monitoring

```bash
# Start monitoring dashboard
python monitoring_dashboard.py --interval 30
```

- [ ] Monitoring dashboard running
- [ ] Metrics being collected
- [ ] Alerts configured

### 2. Log Monitoring

**Docker:**
```bash
docker-compose logs -f --tail=100
```

**Windows Service:**
- Check Event Viewer → Application Logs

**Cloud:**
- GCP: Cloud Logging
- AWS: CloudWatch
- Azure: Application Insights

### 3. Health Checks

- [ ] API health check: `curl http://localhost:5000/health`
- [ ] Dashboard health: `curl http://localhost:8501/_stcore/health`
- [ ] Database accessible
- [ ] File watcher detecting files

---

## 💾 Backup Configuration

### 1. Automated Backups

**Create Backup Script Schedule:**

**Windows Task Scheduler:**
```bash
schtasks /create /tn "BharatBizBackup" ^
  /tr "python E:\BBAgent\backup_script.py backup" ^
  /sc daily /st 02:00
```

**Linux Cron:**
```bash
0 2 * * * cd /path/to/BBAgent && python backup_script.py backup
```

### 2. Backup Verification

- [ ] Backup script tested: `python backup_script.py backup`
- [ ] Backups created in `backups/` folder
- [ ] Restore tested: `python backup_script.py restore --timestamp XXXXXX`
- [ ] Backup schedule configured
- [ ] Off-site backup configured (optional)

---

## 🔒 Security Hardening

### 1. API Security

- [ ] HTTPS enabled (use reverse proxy like nginx)
- [ ] Rate limiting implemented
- [ ] API authentication added (if needed)
- [ ] CORS configured properly
- [ ] Input validation enabled

### 2. Database Security

- [ ] Database file permissions restricted
- [ ] Regular backups enabled
- [ ] Sensitive data encrypted (if needed)
- [ ] Access logs enabled

### 3. Network Security

- [ ] Firewall configured
- [ ] Only necessary ports open (5000, 8501)
- [ ] VPN/private network (if needed)
- [ ] DDoS protection (if cloud)

---

## 🧪 Testing in Production

### 1. Smoke Tests

```bash
# Quick test
python quick_test.py

# Full test
python test_automation.py

# Performance test
python performance_test.py
```

- [ ] All tests passing
- [ ] No errors in logs
- [ ] Services responding

### 2. End-to-End Test

1. **Upload Test Invoice**
   - [ ] Drop file in `temp/` folder
   - [ ] File detected within 1 second
   - [ ] Processing completes in 3-5 seconds
   - [ ] Data saved to database
   - [ ] Dashboard updated

2. **Test API**
   ```bash
   curl -X POST http://localhost:5000/api/v1/invoice/manual \
     -H "Content-Type: application/json" \
     -d '{"vendor_name":"Test","amount":10000,"invoice_number":"TEST-001","invoice_date":"2024-01-15","payment_terms":"45 days"}'
   ```
   - [ ] API responds successfully
   - [ ] Transaction created
   - [ ] Dashboard shows new transaction

3. **Test Scheduler**
   - [ ] Wait for scheduled task
   - [ ] Report generated
   - [ ] No errors in logs

### 3. Load Testing

```bash
# Process multiple invoices
python batch_processor.py ./test_invoices --workers 10
```

- [ ] Batch processing works
- [ ] No memory leaks
- [ ] Performance acceptable

---

## 📈 Performance Optimization

### 1. Database Optimization

- [ ] Add indexes for frequent queries
- [ ] Vacuum database regularly
- [ ] Monitor query performance

### 2. Resource Optimization

- [ ] Adjust batch workers based on CPU
- [ ] Configure memory limits (Docker)
- [ ] Enable caching (if needed)

### 3. Monitoring Thresholds

- [ ] CPU alert: > 80%
- [ ] Memory alert: > 85%
- [ ] Disk alert: > 90%
- [ ] Error rate alert: > 5%

---

## 🚨 Incident Response Plan

### 1. Service Down

**Steps:**
1. Check service status
2. Review logs
3. Restart service
4. Verify recovery
5. Document incident

**Commands:**
```bash
# Docker
docker-compose restart automation

# Windows Service
nssm restart BharatBizAgent-Automation

# Check logs
docker-compose logs automation
```

### 2. Database Issues

**Steps:**
1. Stop all services
2. Backup current database
3. Restore from backup (if needed)
4. Restart services
5. Verify data integrity

### 3. High Error Rate

**Steps:**
1. Check logs for errors
2. Identify root cause
3. Apply fix
4. Monitor recovery
5. Update documentation

---

## 📞 Support & Maintenance

### Daily Tasks

- [ ] Check monitoring dashboard
- [ ] Review error logs
- [ ] Verify backups completed
- [ ] Check pending approvals

### Weekly Tasks

- [ ] Review performance metrics
- [ ] Check disk space
- [ ] Update dependencies (if needed)
- [ ] Review compliance reports

### Monthly Tasks

- [ ] Security audit
- [ ] Performance review
- [ ] Backup verification
- [ ] Documentation updates
- [ ] Team training (if needed)

---

## ✅ Production Go-Live Checklist

### Final Checks

- [ ] All environment variables configured
- [ ] All services running
- [ ] Monitoring enabled
- [ ] Backups configured
- [ ] Security hardened
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Team trained
- [ ] Support plan in place
- [ ] Rollback plan ready

### Go-Live Steps

1. **Pre-Launch**
   - [ ] Final backup
   - [ ] Final tests
   - [ ] Team briefing

2. **Launch**
   - [ ] Start all services
   - [ ] Verify health checks
   - [ ] Monitor closely

3. **Post-Launch**
   - [ ] Monitor for 24 hours
   - [ ] Address any issues
   - [ ] Document lessons learned

---

## 🎉 Production Ready!

Once all items are checked, your system is ready for production use.

### Quick Reference

**Start Services:**
```bash
# Docker
docker-compose up -d

# Windows Service
nssm start BharatBizAgent-Automation
nssm start BharatBizAgent-Scheduler
nssm start BharatBizAgent-Webhook

# Manual
python automate.py &
python scheduler.py &
python webhook_server.py &
```

**Monitor:**
```bash
python monitoring_dashboard.py
```

**Backup:**
```bash
python backup_script.py backup
```

**Support:**
- Check logs first
- Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- See [AUTOMATION_GUIDE.md](AUTOMATION_GUIDE.md)

---

**Good luck with your production deployment! 🚀**
