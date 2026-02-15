# 🚀 Production Deployment Guide

Complete guide for deploying the automated agent system to production.

---

## 📋 Deployment Options

### Option 1: Docker Compose (Recommended)
### Option 2: Windows Service
### Option 3: Cloud Deployment (GCP/AWS/Azure)
### Option 4: Kubernetes

---

## 🐳 Option 1: Docker Compose Deployment

### Prerequisites
- Docker Desktop installed
- Docker Compose installed
- 4GB RAM minimum
- 10GB disk space

### Quick Start

1. **Configure Environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

2. **Build and Start**
   ```bash
   docker-compose up -d
   ```

3. **Verify Services**
   ```bash
   docker-compose ps
   ```

### Services Running

```
Service         Port    Purpose
-----------------------------------------
automation      -       File watcher
scheduler       -       Scheduled tasks
webhook         5000    REST API
dashboard       8501    Streamlit UI
monitoring      -       System monitoring
```

### Access Points

- **Dashboard:** http://localhost:8501
- **API:** http://localhost:5000
- **Health Check:** http://localhost:5000/health

### Management Commands

```bash
# View logs
docker-compose logs -f automation
docker-compose logs -f scheduler
docker-compose logs -f webhook

# Restart services
docker-compose restart automation
docker-compose restart scheduler

# Stop all services
docker-compose down

# Update and restart
docker-compose down
docker-compose build
docker-compose up -d

# Scale webhook service
docker-compose up -d --scale webhook=3
```

### Volume Management

```bash
# Backup data
docker run --rm -v bharat-biz-agent_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/data-backup.tar.gz /data

# Restore data
docker run --rm -v bharat-biz-agent_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/data-backup.tar.gz -C /
```

---

## 🪟 Option 2: Windows Service Deployment

### Prerequisites
- NSSM (Non-Sucking Service Manager)
- Python 3.10+ installed
- Administrator privileges

### Installation

1. **Install NSSM**
   ```bash
   choco install nssm
   ```

2. **Create Services**

   **File Watcher Service:**
   ```bash
   nssm install BharatBizAgent-Automation ^
     "C:\Python310\python.exe" ^
     "E:\BBAgent\automate.py"
   
   nssm set BharatBizAgent-Automation AppDirectory "E:\BBAgent"
   nssm set BharatBizAgent-Automation DisplayName "Bharat Biz-Agent Automation"
   nssm set BharatBizAgent-Automation Description "Invoice processing automation"
   nssm set BharatBizAgent-Automation Start SERVICE_AUTO_START
   ```

   **Scheduler Service:**
   ```bash
   nssm install BharatBizAgent-Scheduler ^
     "C:\Python310\python.exe" ^
     "E:\BBAgent\scheduler.py"
   
   nssm set BharatBizAgent-Scheduler AppDirectory "E:\BBAgent"
   nssm set BharatBizAgent-Scheduler DisplayName "Bharat Biz-Agent Scheduler"
   nssm set BharatBizAgent-Scheduler Start SERVICE_AUTO_START
   ```

   **Webhook Service:**
   ```bash
   nssm install BharatBizAgent-Webhook ^
     "C:\Python310\python.exe" ^
     "E:\BBAgent\webhook_server.py"
   
   nssm set BharatBizAgent-Webhook AppDirectory "E:\BBAgent"
   nssm set BharatBizAgent-Webhook DisplayName "Bharat Biz-Agent API"
   nssm set BharatBizAgent-Webhook Start SERVICE_AUTO_START
   ```

3. **Start Services**
   ```bash
   nssm start BharatBizAgent-Automation
   nssm start BharatBizAgent-Scheduler
   nssm start BharatBizAgent-Webhook
   ```

### Management

```bash
# Check status
nssm status BharatBizAgent-Automation

# Stop service
nssm stop BharatBizAgent-Automation

# Restart service
nssm restart BharatBizAgent-Automation

# Remove service
nssm remove BharatBizAgent-Automation confirm
```

### Logs

Services log to Windows Event Viewer:
- Application Logs → BharatBizAgent-*

---

## ☁️ Option 3: Cloud Deployment

### Google Cloud Platform (GCP)

#### Cloud Run Deployment

1. **Build Container**
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
     --command python \
     --args webhook_server.py
   
   # Dashboard
   gcloud run deploy bharat-biz-dashboard \
     --image gcr.io/PROJECT_ID/bharat-biz-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --command streamlit \
     --args "run,streamlit_app.py,--server.address=0.0.0.0"
   ```

3. **Setup Cloud Scheduler**
   ```bash
   # Daily compliance report
   gcloud scheduler jobs create http daily-compliance \
     --schedule="0 9 * * *" \
     --uri="https://YOUR-WEBHOOK-URL/api/v1/compliance/report" \
     --http-method=GET
   ```

#### Vertex AI Agent Deployment

```bash
# Deploy agents to Vertex AI
adk deploy --agent janitor --cloud vertex-ai --project PROJECT_ID
adk deploy --agent compliance --cloud vertex-ai --project PROJECT_ID
adk deploy --agent collector --cloud vertex-ai --project PROJECT_ID
adk deploy --agent arbitrator --cloud vertex-ai --project PROJECT_ID
```

### AWS Deployment

#### ECS Fargate

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name bharat-biz-agent
   ```

2. **Build and Push**
   ```bash
   docker build -t bharat-biz-agent .
   docker tag bharat-biz-agent:latest \
     ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/bharat-biz-agent:latest
   docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/bharat-biz-agent:latest
   ```

3. **Create Task Definition**
   ```json
   {
     "family": "bharat-biz-agent",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "containerDefinitions": [
       {
         "name": "automation",
         "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/bharat-biz-agent:latest",
         "command": ["python", "automate.py"],
         "essential": true
       }
     ]
   }
   ```

4. **Create Service**
   ```bash
   aws ecs create-service \
     --cluster bharat-biz-cluster \
     --service-name automation \
     --task-definition bharat-biz-agent \
     --desired-count 1 \
     --launch-type FARGATE
   ```

### Azure Deployment

#### Container Instances

```bash
# Create resource group
az group create --name bharat-biz-rg --location eastus

# Deploy container
az container create \
  --resource-group bharat-biz-rg \
  --name bharat-biz-automation \
  --image YOUR_REGISTRY/bharat-biz-agent:latest \
  --cpu 1 \
  --memory 2 \
  --restart-policy Always \
  --command-line "python automate.py"
```

---

## ☸️ Option 4: Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured
- Helm (optional)

### Deployment Files

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bharat-biz-automation
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bharat-biz-automation
  template:
    metadata:
      labels:
        app: bharat-biz-automation
    spec:
      containers:
      - name: automation
        image: bharat-biz-agent:latest
        command: ["python", "automate.py"]
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: temp
          mountPath: /app/temp
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: bharat-biz-data
      - name: temp
        emptyDir: {}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bharat-biz-webhook
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bharat-biz-webhook
  template:
    metadata:
      labels:
        app: bharat-biz-webhook
    spec:
      containers:
      - name: webhook
        image: bharat-biz-agent:latest
        command: ["python", "webhook_server.py"]
        ports:
        - containerPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: bharat-biz-webhook
spec:
  selector:
    app: bharat-biz-webhook
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

### Deploy

```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get services
```

---

## 🔒 Security Considerations

### API Keys
- Store in environment variables
- Use secrets management (AWS Secrets Manager, GCP Secret Manager)
- Rotate keys regularly

### Network Security
- Use HTTPS for webhook API
- Implement rate limiting
- Add authentication middleware

### Database Security
- Regular backups
- Encrypt sensitive data
- Restrict access

### Monitoring
- Set up alerts for failures
- Monitor resource usage
- Track API usage

---

## 📊 Monitoring & Logging

### Application Monitoring

```bash
# Real-time monitoring
python monitoring_dashboard.py --interval 10

# Export metrics
python monitoring_dashboard.py --export
```

### Log Aggregation

**Docker:**
```bash
docker-compose logs -f --tail=100
```

**Cloud:**
- GCP: Cloud Logging
- AWS: CloudWatch Logs
- Azure: Application Insights

### Metrics to Track

- Invoice processing rate
- API response times
- Error rates
- Auto-approval rate
- Compliance violations
- System resource usage

---

## 🔄 Backup & Recovery

### Database Backup

```bash
# Backup SQLite
cp data/biz_agent.db backups/biz_agent_$(date +%Y%m%d).db

# Backup ChromaDB
tar -czf backups/chroma_$(date +%Y%m%d).tar.gz data/chroma_db/
```

### Automated Backups

**Cron job (Linux):**
```bash
0 2 * * * /path/to/backup_script.sh
```

**Task Scheduler (Windows):**
```bash
schtasks /create /tn "BharatBizBackup" /tr "backup_script.bat" /sc daily /st 02:00
```

### Recovery

```bash
# Restore SQLite
cp backups/biz_agent_20240115.db data/biz_agent.db

# Restore ChromaDB
tar -xzf backups/chroma_20240115.tar.gz -C data/
```

---

## 🚦 Health Checks

### Webhook API
```bash
curl http://localhost:5000/health
```

### Dashboard
```bash
curl http://localhost:8501/_stcore/health
```

### Automation Status
```bash
# Check if processing
ls -lt temp/
```

---

## 📈 Scaling

### Horizontal Scaling

**Docker Compose:**
```bash
docker-compose up -d --scale webhook=5
```

**Kubernetes:**
```bash
kubectl scale deployment bharat-biz-webhook --replicas=5
```

### Vertical Scaling

Increase resources in:
- Docker: `docker-compose.yml` (cpu/memory limits)
- Kubernetes: `deployment.yaml` (resources)
- Cloud: Instance size

---

## 🆘 Troubleshooting

### Common Issues

**Service won't start:**
- Check logs
- Verify environment variables
- Check port availability

**High memory usage:**
- Reduce batch workers
- Implement pagination
- Clear old data

**Slow processing:**
- Check LLM API limits
- Increase workers
- Optimize database queries

---

## ✅ Production Checklist

- [ ] Environment variables configured
- [ ] API keys secured
- [ ] Database backed up
- [ ] Monitoring enabled
- [ ] Logs configured
- [ ] Health checks working
- [ ] Auto-restart enabled
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team trained

---

## 📞 Support

For deployment issues:
1. Check logs first
2. Review this guide
3. Check AUTOMATION_GUIDE.md
4. Verify configuration

---

**🎉 Your system is production-ready!**

Choose your deployment option and follow the steps above.
