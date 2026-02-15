@echo off
REM Automation Launcher for Bharat Biz-Agent

echo ========================================
echo Bharat Biz-Agent - Automation System
echo ========================================
echo.

echo Select automation mode:
echo.
echo 1. File Watcher (Auto-process new invoices)
echo 2. Scheduled Tasks (Daily/Weekly reports)
echo 3. Batch Processor (Process folder of invoices)
echo 4. Webhook Server (API endpoint)
echo 5. Full System (All automation enabled)
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo Starting File Watcher...
    echo Drop invoice files in 'temp' folder to auto-process
    echo.
    python automate.py
) else if "%choice%"=="2" (
    echo.
    echo Starting Scheduled Tasks...
    echo Running daily compliance reports and weekly summaries
    echo.
    python scheduler.py
) else if "%choice%"=="3" (
    echo.
    set /p folder="Enter folder path: "
    echo.
    echo Processing all invoices in: %folder%
    echo.
    python batch_processor.py "%folder%"
) else if "%choice%"=="4" (
    echo.
    echo Starting Webhook Server on http://localhost:5000
    echo.
    python webhook_server.py
) else if "%choice%"=="5" (
    echo.
    echo Starting Full Automation System...
    echo.
    start "File Watcher" cmd /k python automate.py
    timeout /t 2 /nobreak >nul
    start "Scheduler" cmd /k python scheduler.py
    timeout /t 2 /nobreak >nul
    start "Webhook Server" cmd /k python webhook_server.py
    echo.
    echo All systems started in separate windows!
    echo.
) else (
    echo Invalid choice!
    pause
    exit /b
)

pause
