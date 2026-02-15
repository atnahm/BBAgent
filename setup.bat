@echo off
echo ========================================
echo Bharat Biz-Agent POC - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version

echo.
echo [2/4] Installing dependencies...
pip install -r backend\requirements.txt

echo.
echo [3/4] Creating directories...
if not exist "data" mkdir data
if not exist "temp" mkdir temp

echo.
echo [4/4] Checking configuration...
if not exist "backend\.env" (
    echo Creating .env file from template...
    copy backend\.env.example backend\.env
    echo.
    echo ⚠️  IMPORTANT: Edit backend\.env and add your Gemini API key!
    echo Get free API key from: https://makersuite.google.com/app/apikey
    echo.
) else (
    echo ✓ .env file already exists
)

echo.
echo ========================================
echo ✅ Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit backend\.env and add your GEMINI_API_KEY
echo 2. Run: streamlit run streamlit_app.py
echo.
pause
