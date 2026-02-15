"""Quick test script to verify ADK agents initialization."""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

print("=" * 50)
print("Testing ADK Agent Initialization")
print("=" * 50)

# Test 1: Import orchestrator
print("\n1. Importing orchestrator...")
try:
    from core.orchestrator import Orchestrator
    print("   ✅ Import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialize orchestrator
print("\n2. Initializing orchestrator...")
try:
    orch = Orchestrator()
    print("   ✅ Orchestrator initialized")
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check agents
print("\n3. Checking agents...")
try:
    print(f"   - Janitor: {orch.janitor.name}")
    print(f"   - Compliance: {orch.compliance.name}")
    print(f"   - Collector: {orch.collector.name}")
    print(f"   - Arbitrator: {orch.arbitrator.name}")
    print("   ✅ All 4 agents present")
except Exception as e:
    print(f"   ❌ Agent check failed: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("🎉 ALL TESTS PASSED!")
print("=" * 50)
print("\nYour ADK system is ready to run!")
print("Start with: streamlit run streamlit_app.py")
