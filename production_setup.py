"""
Production Setup Script
Automated setup and verification for production deployment.
"""
import os
import sys
from pathlib import Path
import subprocess
import shutil

class ProductionSetup:
    """Setup system for production deployment."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / 'backend'
        self.data_dir = self.root_dir / 'data'
        self.temp_dir = self.root_dir / 'temp'
        self.backup_dir = self.root_dir / 'backups'
        self.checks_passed = []
        self.checks_failed = []
    
    def print_header(self, text):
        """Print section header."""
        print(f"\n{'='*60}")
        print(f"{text:^60}")
        print(f"{'='*60}\n")
    
    def check_python_version(self):
        """Check Python version."""
        print("🐍 Checking Python version...")
        version = sys.version_info
        
        if version.major == 3 and version.minor >= 10:
            print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
            self.checks_passed.append("Python version")
            return True
        else:
            print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.10+)")
            self.checks_failed.append("Python version")
            return False
    
    def check_dependencies(self):
        """Check if all dependencies are installed."""
        print("\n📦 Checking dependencies...")
        
        required_packages = [
            'google-generativeai',
            'chromadb',
            'sqlalchemy',
            'streamlit',
            'flask',
            'schedule',
            'watchdog',
            'psutil'
        ]
        
        missing = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} (missing)")
                missing.append(package)
        
        if missing:
            print(f"\n   Install missing packages:")
            print(f"   pip install {' '.join(missing)}")
            self.checks_failed.append("Dependencies")
            return False
        else:
            self.checks_passed.append("Dependencies")
            return True
    
    def create_directories(self):
        """Create necessary directories."""
        print("\n📁 Creating directories...")
        
        directories = [
            self.data_dir,
            self.temp_dir,
            self.backup_dir,
            self.data_dir / 'chroma_db'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {directory}")
        
        self.checks_passed.append("Directories")
        return True
    
    def check_env_file(self):
        """Check if .env file exists and is configured."""
        print("\n⚙️  Checking environment configuration...")
        
        env_file = self.backend_dir / '.env'
        env_example = self.backend_dir / '.env.example'
        
        if not env_file.exists():
            if env_example.exists():
                print(f"   ⚠️  .env not found, copying from .env.example")
                shutil.copy(env_example, env_file)
                print(f"   ⚠️  Please edit backend/.env with your API keys")
                self.checks_failed.append("Environment config (needs API keys)")
                return False
            else:
                print(f"   ❌ .env.example not found")
                self.checks_failed.append("Environment config")
                return False
        
        # Check if API keys are set
        with open(env_file) as f:
            content = f.read()
        
        if 'your_' in content or 'your-' in content:
            print(f"   ⚠️  .env contains placeholder values")
            print(f"   ⚠️  Please set your actual API keys in backend/.env")
            self.checks_failed.append("API keys not configured")
            return False
        
        print(f"   ✅ .env configured")
        self.checks_passed.append("Environment config")
        return True
    
    def test_database_connection(self):
        """Test database initialization."""
        print("\n💾 Testing database connection...")
        
        try:
            sys.path.insert(0, str(self.backend_dir))
            from memory.relational_db import DatabaseManager
            from config_loader import CONFIG
            
            db = DatabaseManager(CONFIG['relational_db']['path'])
            session = db.get_session()
            session.close()
            
            print(f"   ✅ SQLite database initialized")
            self.checks_passed.append("Database")
            return True
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            self.checks_failed.append("Database")
            return False
    
    def test_vector_db(self):
        """Test vector database initialization."""
        print("\n🔍 Testing vector database...")
        
        try:
            sys.path.insert(0, str(self.backend_dir))
            from memory.vector_store import VectorMemory
            from config_loader import CONFIG
            
            vector_db = VectorMemory(
                db_path=CONFIG['vector_db']['path'],
                collection_name=CONFIG['vector_db']['collection_name']
            )
            
            print(f"   ✅ ChromaDB initialized")
            self.checks_passed.append("Vector database")
            return True
        except Exception as e:
            print(f"   ❌ Vector DB error: {e}")
            self.checks_failed.append("Vector database")
            return False
    
    def check_ports(self):
        """Check if required ports are available."""
        print("\n🔌 Checking port availability...")
        
        import socket
        
        ports = {
            5000: 'Webhook API',
            8501: 'Streamlit Dashboard'
        }
        
        all_available = True
        
        for port, service in ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"   ⚠️  Port {port} ({service}) is in use")
                all_available = False
            else:
                print(f"   ✅ Port {port} ({service}) available")
        
        if all_available:
            self.checks_passed.append("Ports")
        else:
            self.checks_failed.append("Ports (some in use)")
        
        return all_available
    
    def create_production_config(self):
        """Create production-specific configuration."""
        print("\n⚙️  Creating production configuration...")
        
        prod_config = self.root_dir / 'production.env'
        
        config_content = """# Production Configuration
# Copy this to backend/.env and fill in your values

# LLM Provider (gemini or huggingface)
LLM_PROVIDER=gemini

# API Keys (REQUIRED)
GEMINI_API_KEY=your_production_gemini_key
HUGGINGFACE_API_KEY=your_production_huggingface_key

# Database Paths
DATABASE_PATH=./data/biz_agent.db
CHROMA_DB_PATH=./data/chroma_db

# WhatsApp Configuration (PRODUCTION)
WHATSAPP_MOCK_MODE=false
WHATSAPP_API_KEY=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_TEST_NUMBER=+919876543210

# GSTIN Validation (PRODUCTION)
GSTIN_MOCK_MODE=false
GST_API_KEY=your_gst_provider_api_key

# Email Integration (OPTIONAL)
EMAIL_ADDRESS=your_email@example.com
EMAIL_PASSWORD=your_app_password
"""
        
        with open(prod_config, 'w') as f:
            f.write(config_content)
        
        print(f"   ✅ Production config template created: {prod_config}")
        print(f"   ⚠️  Copy to backend/.env and configure for production")
        
        return True
    
    def generate_startup_script(self):
        """Generate production startup script."""
        print("\n🚀 Generating startup scripts...")
        
        # Windows batch script
        windows_script = self.root_dir / 'start_production.bat'
        
        windows_content = """@echo off
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
"""
        
        with open(windows_script, 'w') as f:
            f.write(windows_content)
        
        print(f"   ✅ Windows startup script: {windows_script}")
        
        # Linux/Mac script
        linux_script = self.root_dir / 'start_production.sh'
        
        linux_content = """#!/bin/bash
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
"""
        
        with open(linux_script, 'w') as f:
            f.write(linux_content)
        
        # Make executable
        try:
            os.chmod(linux_script, 0o755)
        except:
            pass
        
        print(f"   ✅ Linux/Mac startup script: {linux_script}")
        
        return True
    
    def print_summary(self):
        """Print setup summary."""
        self.print_header("PRODUCTION SETUP SUMMARY")
        
        print(f"✅ Checks Passed: {len(self.checks_passed)}")
        for check in self.checks_passed:
            print(f"   • {check}")
        
        if self.checks_failed:
            print(f"\n❌ Checks Failed: {len(self.checks_failed)}")
            for check in self.checks_failed:
                print(f"   • {check}")
            
            print(f"\n⚠️  Please fix the failed checks before deploying to production")
        else:
            print(f"\n🎉 All checks passed! System ready for production.")
        
        print(f"\n{'='*60}")
        print(f"NEXT STEPS")
        print(f"{'='*60}")
        
        if self.checks_failed:
            print(f"\n1. Fix failed checks above")
            print(f"2. Configure backend/.env with production API keys")
            print(f"3. Run this script again")
        else:
            print(f"\n1. Review PRODUCTION_CHECKLIST.md")
            print(f"2. Choose deployment method:")
            print(f"   • Docker: docker-compose up -d")
            print(f"   • Windows: start_production.bat")
            print(f"   • Linux/Mac: ./start_production.sh")
            print(f"   • Service: See DEPLOYMENT_GUIDE.md")
            print(f"\n3. Monitor: python monitoring_dashboard.py")
            print(f"4. Backup: python backup_script.py backup")
        
        print(f"\n{'='*60}\n")
    
    def run(self):
        """Run complete production setup."""
        self.print_header("PRODUCTION SETUP")
        
        print("This script will prepare your system for production deployment.\n")
        
        # Run all checks
        self.check_python_version()
        self.check_dependencies()
        self.create_directories()
        self.check_env_file()
        self.test_database_connection()
        self.test_vector_db()
        self.check_ports()
        self.create_production_config()
        self.generate_startup_script()
        
        # Print summary
        self.print_summary()
        
        return len(self.checks_failed) == 0

if __name__ == "__main__":
    setup = ProductionSetup()
    success = setup.run()
    
    sys.exit(0 if success else 1)
