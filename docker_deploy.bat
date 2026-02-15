@echo off
REM Docker Deployment Script

echo ========================================
echo Docker Deployment - Bharat Biz-Agent
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/5] Checking Docker...
docker --version
docker-compose --version
echo.

echo [2/5] Checking configuration...
if not exist "backend\.env" (
    echo WARNING: backend\.env not found!
    if exist "backend\.env.example" (
        echo Copying .env.example to .env...
        copy "backend\.env.example" "backend\.env"
        echo.
        echo IMPORTANT: Edit backend\.env with your API keys before continuing!
        echo Press any key to open .env file...
        pause >nul
        notepad "backend\.env"
        echo.
        echo After configuring, press any key to continue...
        pause >nul
    ) else (
        echo ERROR: backend\.env.example not found!
        pause
        exit /b 1
    )
)
echo Configuration found: backend\.env
echo.

echo [3/5] Creating directories...
if not exist "data" mkdir data
if not exist "temp" mkdir temp
if not exist "backups" mkdir backups
echo Directories created.
echo.

echo [4/5] Building Docker images...
docker-compose build
if errorlevel 1 (
    echo ERROR: Docker build failed!
    pause
    exit /b 1
)
echo Build complete.
echo.

echo [5/5] Starting services...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Failed to start services!
    pause
    exit /b 1
)
echo.

echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo Services running:
docker-compose ps
echo.
echo Access points:
echo   Dashboard: http://localhost:8501
echo   API:       http://localhost:5000
echo   Health:    http://localhost:5000/health
echo.
echo Useful commands:
echo   View logs:    docker-compose logs -f
echo   Stop:         docker-compose down
echo   Restart:      docker-compose restart
echo   Status:       docker-compose ps
echo.
echo Opening dashboard in browser...
timeout /t 3 /nobreak >nul
start http://localhost:8501
echo.
pause
