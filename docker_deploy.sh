#!/bin/bash
# Docker Deployment Script

echo "========================================"
echo "Docker Deployment - Bharat Biz-Agent"
echo "========================================"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "[1/5] Checking Docker..."
docker --version
docker-compose --version
echo

echo "[2/5] Checking configuration..."
if [ ! -f "backend/.env" ]; then
    echo "WARNING: backend/.env not found!"
    if [ -f "backend/.env.example" ]; then
        echo "Copying .env.example to .env..."
        cp backend/.env.example backend/.env
        echo
        echo "IMPORTANT: Edit backend/.env with your API keys!"
        echo "Press Enter after editing..."
        read
    else
        echo "ERROR: backend/.env.example not found!"
        exit 1
    fi
fi
echo "Configuration found: backend/.env"
echo

echo "[3/5] Creating directories..."
mkdir -p data temp backups
echo "Directories created."
echo

echo "[4/5] Building Docker images..."
docker-compose build
if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed!"
    exit 1
fi
echo "Build complete."
echo

echo "[5/5] Starting services..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start services!"
    exit 1
fi
echo

echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo
echo "Services running:"
docker-compose ps
echo
echo "Access points:"
echo "  Dashboard: http://localhost:8501"
echo "  API:       http://localhost:5000"
echo "  Health:    http://localhost:5000/health"
echo
echo "Useful commands:"
echo "  View logs:    docker-compose logs -f"
echo "  Stop:         docker-compose down"
echo "  Restart:      docker-compose restart"
echo "  Status:       docker-compose ps"
echo
