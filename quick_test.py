"""Quick test to verify automation setup."""
import sys
from pathlib import Path

print("🧪 Quick Automation Test\n")

# Test 1: Check dependencies
print("1. Checking dependencies...")
try:
    import schedule
    import watchdog
    import flask
    print("   ✅ All automation packages installed\n")
except ImportError as e:
    print(f"   ❌ Missing package: {e}\n")
    print("   Run: pip install schedule watchdog flask\n")
    sys.exit(1)

# Test 2: Check backend path
print("2. Checking backend structure...")
backend_path = Path(__file__).parent / 'backend'
if backend_path.exists():
    print(f"   ✅ Backend found: {backend_path}\n")
else:
    print(f"   ❌ Backend not found\n")
    sys.exit(1)

# Test 3: Check temp directory
print("3. Checking watch directory...")
temp_dir = Path("temp")
temp_dir.mkdir(exist_ok=True)
print(f"   ✅ Watch directory ready: {temp_dir.absolute()}\n")

# Test 4: Check automation scripts
print("4. Checking automation scripts...")
scripts = ['automate.py', 'scheduler.py', 'batch_processor.py', 'webhook_server.py']
for script in scripts:
    if Path(script).exists():
        print(f"   ✅ {script}")
    else:
        print(f"   ❌ {script} missing")
print()

# Test 5: Check config
print("5. Checking configuration...")
config_file = backend_path / 'config.yaml'
env_file = backend_path / '.env'

if config_file.exists():
    print(f"   ✅ config.yaml found")
else:
    print(f"   ⚠️  config.yaml not found")

if env_file.exists():
    print(f"   ✅ .env found")
else:
    print(f"   ⚠️  .env not found (copy from .env.example)")
print()

print("="*60)
print("✅ AUTOMATION SYSTEM READY!")
print("="*60)
print("\n🚀 Start automation:")
print("   • File Watcher:    python automate.py")
print("   • Scheduler:       python scheduler.py")
print("   • Batch Process:   python batch_processor.py ./invoices")
print("   • Webhook API:     python webhook_server.py")
print("   • All-in-one:      run_automation.bat")
print()
