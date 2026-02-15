"""
One-Click Production Deployment
Interactive deployment wizard for production.
"""
import os
import sys
import subprocess
from pathlib import Path
import time

class DeploymentWizard:
    """Interactive deployment wizard."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / 'backend'
    
    def print_banner(self):
        """Print deployment banner."""
        print("\n" + "="*60)
        print("🚀 BHARAT BIZ-AGENT - PRODUCTION DEPLOYMENT WIZARD")
        print("="*60 + "\n")
    
    def check_prerequisites(self):
        """Check if system is ready for deployment."""
        print("📋 Checking prerequisites...\n")
        
        checks = []
        
        # Check Python
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
            checks.append(True)
        else:
            print(f"❌ Python {version.major}.{version.minor} (need 3.10+)")
            checks.append(False)
        
        # Check .env
        env_file = self.backend_dir / '.env'
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
            if 'your_' not in content and 'your-' not in content:
                print("✅ Environment configured")
                checks.append(True)
            else:
                print("⚠️  Environment needs API keys")
                checks.append(False)
        else:
            print("❌ .env file missing")
            checks.append(False)
        
        # Check directories
        if (self.root_dir / 'data').exists() and (self.root_dir / 'temp').exists():
            print("✅ Directories created")
            checks.append(True)
        else:
            print("⚠️  Creating directories...")
            (self.root_dir / 'data').mkdir(exist_ok=True)
            (self.root_dir / 'temp').mkdir(exist_ok=True)
            (self.root_dir / 'backups').mkdir(exist_ok=True)
            checks.append(True)
        
        print()
        return all(checks)
    
    def select_deployment_method(self):
        """Let user select deployment method."""
        print("🎯 Select Deployment Method:\n")
        print("1. Docker Compose (Recommended)")
        print("   - All services in containers")
        print("   - Easy management")
        print("   - Production-ready")
        print()
        print("2. Windows Service")
        print("   - Native Windows services")
        print("   - Auto-start on boot")
        print("   - System integration")
        print()
        print("3. Manual Start")
        print("   - Start services manually")
        print("   - Full control")
        print("   - Development/testing")
        print()
        print("4. Cloud Deployment")
        print("   - Deploy to GCP/AWS/Azure")
        print("   - Scalable")
        print("   - Managed infrastructure")
        print()
        
        while True:
            choice = input("Enter choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            print("Invalid choice. Please enter 1-4.")
    
    def deploy_docker(self):
        """Deploy using Docker Compose."""
        print("\n🐳 Docker Compose Deployment\n")
        
        # Check if Docker is installed
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            print(f"✅ {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Docker not installed")
            print("\nInstall Docker Desktop:")
            print("https://www.docker.com/products/docker-desktop")
            return False
        
        # Check docker-compose
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True)
            print(f"✅ {result.stdout.strip()}")
        except FileNotFoundError:
            print("❌ Docker Compose not installed")
            return False
        
        print("\n📦 Building and starting services...\n")
        
        # Build and start
        try:
            subprocess.run(['docker-compose', 'up', '-d', '--build'], 
                         check=True)
            
            print("\n✅ Services started successfully!\n")
            
            # Show status
            time.sleep(3)
            subprocess.run(['docker-compose', 'ps'])
            
            print("\n🌐 Access Points:")
            print("   Dashboard: http://localhost:8501")
            print("   API: http://localhost:5000")
            print("   Health: http://localhost:5000/health")
            
            print("\n📊 Monitor:")
            print("   docker-compose logs -f")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Deployment failed: {e}")
            return False
    
    def deploy_windows_service(self):
        """Deploy as Windows Service."""
        print("\n🪟 Windows Service Deployment\n")
        
        # Check if NSSM is installed
        try:
            result = subprocess.run(['nssm', 'version'], 
                                  capture_output=True, text=True)
            print(f"✅ NSSM installed")
        except FileNotFoundError:
            print("❌ NSSM not installed")
            print("\nInstall NSSM:")
            print("   choco install nssm")
            print("\nOr download from: https://nssm.cc/download")
            return False
        
        print("\n📝 Service Installation Commands:\n")
        
        python_path = sys.executable
        work_dir = str(self.root_dir)
        
        services = [
            ('BharatBizAgent-Automation', 'automate.py', 'File Watcher'),
            ('BharatBizAgent-Scheduler', 'scheduler.py', 'Scheduler'),
            ('BharatBizAgent-Webhook', 'webhook_server.py', 'API Server')
        ]
        
        print("Run these commands as Administrator:\n")
        
        for service_name, script, description in services:
            print(f"# {description}")
            print(f'nssm install {service_name} "{python_path}" "{work_dir}\\{script}"')
            print(f'nssm set {service_name} AppDirectory "{work_dir}"')
            print(f'nssm set {service_name} DisplayName "{description}"')
            print(f'nssm set {service_name} Start SERVICE_AUTO_START')
            print(f'nssm start {service_name}')
            print()
        
        print("Or run the automated script:")
        print("   install_services.bat")
        
        # Create install script
        self.create_service_install_script(python_path, work_dir, services)
        
        return True
    
    def create_service_install_script(self, python_path, work_dir, services):
        """Create automated service installation script."""
        script_path = self.root_dir / 'install_services.bat'
        
        content = f"""@echo off
REM Automated Service Installation
REM Run as Administrator

echo Installing Bharat Biz-Agent Services...
echo.

"""
        
        for service_name, script, description in services:
            content += f"""echo Installing {description}...
nssm install {service_name} "{python_path}" "{work_dir}\\{script}"
nssm set {service_name} AppDirectory "{work_dir}"
nssm set {service_name} DisplayName "{description}"
nssm set {service_name} Start SERVICE_AUTO_START
echo.

"""
        
        content += """echo Starting services...
"""
        
        for service_name, _, _ in services:
            content += f"nssm start {service_name}\n"
        
        content += """
echo.
echo ========================================
echo Services installed and started!
echo ========================================
echo.
echo Check status in Services.msc
echo.
pause
"""
        
        with open(script_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Created: {script_path}")
        print("   Run as Administrator to install services")
    
    def deploy_manual(self):
        """Deploy with manual start."""
        print("\n🔧 Manual Deployment\n")
        
        print("Services will start in separate windows.\n")
        
        if sys.platform == 'win32':
            # Use start_production.bat
            script = self.root_dir / 'start_production.bat'
            if script.exists():
                print(f"Starting services using {script}...\n")
                subprocess.Popen(['cmd', '/c', str(script)])
                print("✅ Services started in separate windows")
            else:
                print("❌ start_production.bat not found")
                return False
        else:
            # Linux/Mac
            script = self.root_dir / 'start_production.sh'
            if script.exists():
                print(f"Starting services using {script}...\n")
                subprocess.Popen(['bash', str(script)])
                print("✅ Services started")
            else:
                print("❌ start_production.sh not found")
                return False
        
        print("\n🌐 Access Points:")
        print("   Dashboard: http://localhost:8501")
        print("   API: http://localhost:5000")
        
        print("\n📊 Monitor:")
        print("   Check console windows for logs")
        
        return True
    
    def deploy_cloud(self):
        """Show cloud deployment instructions."""
        print("\n☁️  Cloud Deployment\n")
        
        print("Select cloud provider:\n")
        print("1. Google Cloud Platform (GCP)")
        print("2. Amazon Web Services (AWS)")
        print("3. Microsoft Azure")
        print()
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            self.show_gcp_instructions()
        elif choice == '2':
            self.show_aws_instructions()
        elif choice == '3':
            self.show_azure_instructions()
        else:
            print("Invalid choice")
            return False
        
        return True
    
    def show_gcp_instructions(self):
        """Show GCP deployment instructions."""
        print("\n🌐 Google Cloud Platform Deployment\n")
        
        print("1. Build and push image:")
        print("   gcloud builds submit --tag gcr.io/PROJECT_ID/bharat-biz-agent")
        print()
        
        print("2. Deploy to Cloud Run:")
        print("   gcloud run deploy bharat-biz-webhook \\")
        print("     --image gcr.io/PROJECT_ID/bharat-biz-agent \\")
        print("     --platform managed \\")
        print("     --region us-central1 \\")
        print("     --allow-unauthenticated")
        print()
        
        print("3. Setup Cloud Scheduler:")
        print("   gcloud scheduler jobs create http daily-compliance \\")
        print("     --schedule='0 9 * * *' \\")
        print("     --uri='https://YOUR-URL/api/v1/compliance/report'")
        print()
        
        print("📚 Full guide: DEPLOYMENT_GUIDE.md")
    
    def show_aws_instructions(self):
        """Show AWS deployment instructions."""
        print("\n🌐 Amazon Web Services Deployment\n")
        
        print("1. Create ECR repository:")
        print("   aws ecr create-repository --repository-name bharat-biz-agent")
        print()
        
        print("2. Build and push:")
        print("   docker build -t bharat-biz-agent .")
        print("   docker tag bharat-biz-agent:latest ACCOUNT.dkr.ecr.REGION.amazonaws.com/bharat-biz-agent:latest")
        print("   docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/bharat-biz-agent:latest")
        print()
        
        print("3. Deploy to ECS Fargate:")
        print("   aws ecs create-service \\")
        print("     --cluster bharat-biz-cluster \\")
        print("     --service-name automation \\")
        print("     --task-definition bharat-biz-agent")
        print()
        
        print("📚 Full guide: DEPLOYMENT_GUIDE.md")
    
    def show_azure_instructions(self):
        """Show Azure deployment instructions."""
        print("\n🌐 Microsoft Azure Deployment\n")
        
        print("1. Create resource group:")
        print("   az group create --name bharat-biz-rg --location eastus")
        print()
        
        print("2. Deploy container:")
        print("   az container create \\")
        print("     --resource-group bharat-biz-rg \\")
        print("     --name bharat-biz-automation \\")
        print("     --image YOUR_REGISTRY/bharat-biz-agent:latest \\")
        print("     --cpu 1 --memory 2")
        print()
        
        print("📚 Full guide: DEPLOYMENT_GUIDE.md")
    
    def show_post_deployment(self):
        """Show post-deployment steps."""
        print("\n" + "="*60)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*60 + "\n")
        
        print("📋 Next Steps:\n")
        print("1. Verify services are running")
        print("2. Test with sample invoice")
        print("3. Check dashboard: http://localhost:8501")
        print("4. Monitor logs")
        print("5. Setup automated backups")
        print()
        
        print("📊 Monitoring:")
        print("   python monitoring_dashboard.py")
        print()
        
        print("💾 Backup:")
        print("   python backup_script.py backup")
        print()
        
        print("📚 Documentation:")
        print("   - GO_PRODUCTION.md")
        print("   - PRODUCTION_CHECKLIST.md")
        print("   - DEPLOYMENT_GUIDE.md")
        print()
    
    def run(self):
        """Run deployment wizard."""
        self.print_banner()
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met.")
            print("\nRun: python production_setup.py")
            print("Then configure backend/.env with your API keys")
            return False
        
        print("✅ System ready for deployment!\n")
        
        # Select method
        method = self.select_deployment_method()
        
        # Deploy
        success = False
        if method == 1:
            success = self.deploy_docker()
        elif method == 2:
            success = self.deploy_windows_service()
        elif method == 3:
            success = self.deploy_manual()
        elif method == 4:
            success = self.deploy_cloud()
        
        if success:
            self.show_post_deployment()
        
        return success

if __name__ == "__main__":
    wizard = DeploymentWizard()
    success = wizard.run()
    
    sys.exit(0 if success else 1)
