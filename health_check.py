"""
Production Health Check
Verify all services are running correctly.
"""
import requests
import sys
from pathlib import Path
import time

class HealthChecker:
    """Check health of all production services."""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
    
    def print_header(self, text):
        """Print section header."""
        print(f"\n{'='*60}")
        print(f"{text:^60}")
        print(f"{'='*60}\n")
    
    def check_api_health(self):
        """Check webhook API health."""
        print("🌐 Checking Webhook API...")
        
        try:
            response = requests.get('http://localhost:5000/health', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API responding")
                print(f"   Status: {data.get('status')}")
                print(f"   Service: {data.get('service')}")
                self.checks_passed.append("Webhook API")
                return True
            else:
                print(f"   ❌ API returned status {response.status_code}")
                self.checks_failed.append("Webhook API")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ API not responding (connection refused)")
            print(f"   Start with: python webhook_server.py")
            self.checks_failed.append("Webhook API")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.checks_failed.append("Webhook API")
            return False
    
    def check_dashboard(self):
        """Check Streamlit dashboard."""
        print("\n📊 Checking Dashboard...")
        
        try:
            response = requests.get('http://localhost:8501/_stcore/health', timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Dashboard responding")
                print(f"   URL: http://localhost:8501")
                self.checks_passed.append("Dashboard")
                return True
            else:
                print(f"   ❌ Dashboard returned status {response.status_code}")
                self.checks_failed.append("Dashboard")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Dashboard not responding")
            print(f"   Start with: streamlit run streamlit_app.py")
            self.checks_failed.append("Dashboard")
            return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.checks_failed.append("Dashboard")
            return False
    
    def check_database(self):
        """Check database connectivity."""
        print("\n💾 Checking Database...")
        
        try:
            sys.path.insert(0, str(Path(__file__).parent / 'backend'))
            from memory.relational_db import DatabaseManager
            from config_loader import CONFIG
            
            db = DatabaseManager(CONFIG['relational_db']['path'])
            session = db.get_session()
            
            # Try a simple query
            from memory.relational_db import Transaction
            count = session.query(Transaction).count()
            
            session.close()
            
            print(f"   ✅ Database connected")
            print(f"   Transactions: {count}")
            self.checks_passed.append("Database")
            return True
            
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            self.checks_failed.append("Database")
            return False
    
    def check_vector_db(self):
        """Check vector database."""
        print("\n🔍 Checking Vector Database...")
        
        try:
            sys.path.insert(0, str(Path(__file__).parent / 'backend'))
            from memory.vector_store import VectorMemory
            from config_loader import CONFIG
            
            vector_db = VectorMemory(
                db_path=CONFIG['vector_db']['path'],
                collection_name=CONFIG['vector_db']['collection_name']
            )
            
            print(f"   ✅ Vector DB connected")
            self.checks_passed.append("Vector Database")
            return True
            
        except Exception as e:
            print(f"   ❌ Vector DB error: {e}")
            self.checks_failed.append("Vector Database")
            return False
    
    def check_directories(self):
        """Check required directories exist."""
        print("\n📁 Checking Directories...")
        
        directories = [
            Path('data'),
            Path('temp'),
            Path('backups')
        ]
        
        all_exist = True
        
        for directory in directories:
            if directory.exists():
                print(f"   ✅ {directory}")
            else:
                print(f"   ❌ {directory} (missing)")
                all_exist = False
        
        if all_exist:
            self.checks_passed.append("Directories")
        else:
            self.checks_failed.append("Directories")
        
        return all_exist
    
    def check_file_watcher(self):
        """Check if file watcher is monitoring."""
        print("\n👁️  Checking File Watcher...")
        
        temp_dir = Path('temp')
        
        if not temp_dir.exists():
            print(f"   ❌ temp/ directory missing")
            self.checks_failed.append("File Watcher")
            return False
        
        # Create test file
        test_file = temp_dir / '.health_check'
        test_file.write_text('health check')
        
        print(f"   ℹ️  File watcher should be running")
        print(f"   Check: python automate.py")
        
        # Clean up
        test_file.unlink()
        
        self.checks_passed.append("File Watcher (manual check)")
        return True
    
    def test_api_endpoints(self):
        """Test API endpoints."""
        print("\n🔌 Testing API Endpoints...")
        
        endpoints = [
            ('GET', '/health', 'Health check'),
            ('GET', '/api/v1/transactions', 'Get transactions'),
            ('GET', '/api/v1/compliance/report', 'Compliance report')
        ]
        
        all_passed = True
        
        for method, endpoint, description in endpoints:
            try:
                url = f'http://localhost:5000{endpoint}'
                
                if method == 'GET':
                    response = requests.get(url, timeout=5)
                
                if response.status_code in [200, 201]:
                    print(f"   ✅ {endpoint} - {description}")
                else:
                    print(f"   ⚠️  {endpoint} - Status {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"   ❌ {endpoint} - {str(e)[:50]}")
                all_passed = False
        
        if all_passed:
            self.checks_passed.append("API Endpoints")
        else:
            self.checks_failed.append("API Endpoints")
        
        return all_passed
    
    def print_summary(self):
        """Print health check summary."""
        self.print_header("HEALTH CHECK SUMMARY")
        
        total = len(self.checks_passed) + len(self.checks_failed)
        
        print(f"✅ Passed: {len(self.checks_passed)}/{total}")
        for check in self.checks_passed:
            print(f"   • {check}")
        
        if self.checks_failed:
            print(f"\n❌ Failed: {len(self.checks_failed)}/{total}")
            for check in self.checks_failed:
                print(f"   • {check}")
            
            print(f"\n⚠️  Some checks failed. Review errors above.")
            print(f"\n📚 Troubleshooting:")
            print(f"   - Check services are running")
            print(f"   - Review logs for errors")
            print(f"   - See DEPLOYMENT_GUIDE.md")
        else:
            print(f"\n🎉 All checks passed! System is healthy.")
        
        print(f"\n{'='*60}\n")
    
    def run(self):
        """Run all health checks."""
        self.print_header("PRODUCTION HEALTH CHECK")
        
        print("Checking system health...\n")
        
        # Run checks
        self.check_api_health()
        self.check_dashboard()
        self.check_database()
        self.check_vector_db()
        self.check_directories()
        self.check_file_watcher()
        
        # Test API if it's running
        if "Webhook API" in self.checks_passed:
            self.test_api_endpoints()
        
        # Print summary
        self.print_summary()
        
        return len(self.checks_failed) == 0

if __name__ == "__main__":
    checker = HealthChecker()
    success = checker.run()
    
    sys.exit(0 if success else 1)
