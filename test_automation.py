"""
Test Automation System
Quick test to verify all automation components work.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import time

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def test_orchestrator():
    """Test basic orchestrator initialization."""
    print("1️⃣  Testing Orchestrator...")
    try:
        from core.orchestrator import Orchestrator
        orch = Orchestrator()
        print("   ✅ Orchestrator initialized")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_database():
    """Test database connection."""
    print("\n2️⃣  Testing Database...")
    try:
        from core.orchestrator import Orchestrator
        from memory.relational_db import Transaction, Customer
        
        orch = Orchestrator()
        db_session = orch.db.get_session()
        
        # Count records
        txn_count = db_session.query(Transaction).count()
        customer_count = db_session.query(Customer).count()
        
        print(f"   ✅ Database connected")
        print(f"   📊 Transactions: {txn_count}")
        print(f"   👥 Customers: {customer_count}")
        
        db_session.close()
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_agents():
    """Test all agents."""
    print("\n3️⃣  Testing Agents...")
    try:
        from core.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        agents = [
            ("Janitor", orch.janitor),
            ("Compliance", orch.compliance),
            ("Collector", orch.collector),
            ("Arbitrator", orch.arbitrator)
        ]
        
        for name, agent in agents:
            print(f"   ✅ {name} Agent: {agent.name}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_compliance_calculation():
    """Test compliance calculations."""
    print("\n4️⃣  Testing Compliance Calculations...")
    try:
        from core.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        # Test compliance check
        result = asyncio.run(orch.compliance.run(
            task="check_transaction",
            context={
                'invoice_date': '2024-01-01',
                'due_date': '2024-02-15',
                'amount': 50000.0,
                'payment_date': None
            }
        ))
        
        print(f"   ✅ Compliance check completed")
        print(f"   📊 Status: {result['status']}")
        print(f"   📅 Days overdue: {result['days_overdue']}")
        print(f"   💰 Interest: ₹{result['interest_amount']:,.2f}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_message_generation():
    """Test message generation."""
    print("\n5️⃣  Testing Message Generation...")
    try:
        from core.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        # Test message generation
        result = asyncio.run(orch.collector.run(
            task="generate_message",
            context={
                'tier': 'friendly_reminder',
                'transaction': {
                    'id': 1,
                    'vendor_name': 'Test Vendor',
                    'amount': 25000.0,
                    'invoice_number': 'TEST-001'
                },
                'compliance_status': {
                    'days_until_due': 5,
                    'days_overdue': 0,
                    'interest_amount': 0
                },
                'customer': {'phone_number': '+919876543210'}
            }
        ))
        
        print(f"   ✅ Message generated")
        print(f"   📧 Tier: {result['tier']}")
        print(f"   🔒 Requires HITL: {result['requires_hitl_approval']}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_arbitrator_scoring():
    """Test arbitrator customer scoring."""
    print("\n6️⃣  Testing Arbitrator Scoring...")
    try:
        from core.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        # Test customer scoring
        scores = orch.arbitrator.calculate_customer_scores(
            customer={
                'total_value': 500000.0,
                'total_transactions': 25,
                'avg_payment_delay_days': 5.0
            },
            transaction={
                'amount': 50000.0,
                'days_overdue': 10,
                'legal_flag': False
            }
        )
        
        print(f"   ✅ Scoring completed")
        print(f"   🏆 Relationship Score: {scores['relationship_score']}/100")
        print(f"   ⚠️  Transaction Risk: {scores['transaction_risk_score']}/100")
        print(f"   🎖️  Customer Tier: {scores['customer_value_tier'].upper()}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_file_watcher_setup():
    """Test file watcher directory setup."""
    print("\n7️⃣  Testing File Watcher Setup...")
    try:
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        print(f"   ✅ Watch directory created: {temp_dir.absolute()}")
        print(f"   📁 Drop invoice files here for auto-processing")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_webhook_imports():
    """Test webhook server dependencies."""
    print("\n8️⃣  Testing Webhook Dependencies...")
    try:
        from flask import Flask, request, jsonify
        print(f"   ✅ Flask imported successfully")
        
        import schedule
        print(f"   ✅ Schedule imported successfully")
        
        from watchdog.observers import Observer
        print(f"   ✅ Watchdog imported successfully")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("🧪 AUTOMATION SYSTEM TEST SUITE")
    print("="*60)
    print()
    
    tests = [
        test_orchestrator,
        test_database,
        test_agents,
        test_compliance_calculation,
        test_message_generation,
        test_arbitrator_scoring,
        test_file_watcher_setup,
        test_webhook_imports
    ]
    
    results = []
    for test in tests:
        results.append(test())
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Automation system ready.")
        print("\n🚀 Next steps:")
        print("   1. Run: python automate.py (File watcher)")
        print("   2. Run: python scheduler.py (Scheduled tasks)")
        print("   3. Run: python webhook_server.py (API server)")
        print("   4. Or use: run_automation.bat (All-in-one)")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("="*60)

if __name__ == "__main__":
    main()
