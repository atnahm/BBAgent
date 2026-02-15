@echo off
REM Production Startup Script

echo ========================================
echo Starting Bharat Biz-Agent (Production)
echo ========================================
echo.

REM Start services in separate windows
start "Automation" cmd /k python automate.py
timeout /t 2 /nobreak >nul

start "Scheduler" cmd /k python scheduler.py
timeout /t 2 /nobreak >nul

start "Webhook API" cmd /k python webhook_server.py
timeout /t 2 /nobreak >nul

start "Dashboard" cmd /k streamlit run streamlit_app.py
timeout /t 2 /nobreak >nul

start "Monitoring" cmd /k python monitoring_dashboard.py --interval 30

echo.
echo All services started!
echo.
echo Services:
echo   - Automation (File Watcher)
echo   - Scheduler (Reports)
echo   - Webhook API (http://localhost:5000)
echo   - Dashboard (http://localhost:8501)
echo   - Monitoring
echo.
pause
