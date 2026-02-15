#!/bin/bash
# Production Startup Script

echo "========================================"
echo "Starting Bharat Biz-Agent (Production)"
echo "========================================"
echo

# Start services in background
python automate.py &
sleep 2

python scheduler.py &
sleep 2

python webhook_server.py &
sleep 2

streamlit run streamlit_app.py &
sleep 2

python monitoring_dashboard.py --interval 30 &

echo
echo "All services started!"
echo
echo "Services:"
echo "  - Automation (File Watcher)"
echo "  - Scheduler (Reports)"
echo "  - Webhook API (http://localhost:5000)"
echo "  - Dashboard (http://localhost:8501)"
echo "  - Monitoring"
echo
