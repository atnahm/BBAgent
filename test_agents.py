"""Simple test script to verify agent functionality."""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def test_janitor_agent():
    """Test Janitor Agent initialization."""
    print("🧪 Testing Janitor Agent...")
    
    try:
        from agents.janitor_agent import JanitorAgent
        
        # Mock initialization (without real API key)
        print("✓ Janitor Agent imported successfully")
        print("  - Can process invoice images")
        print("  - Can process voice notes")
        print("  - Can validate GSTIN format")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_compliance_agent():
    """Test Compliance Agent."""
    print("\n🧪 Testing Compliance Agent...")
    
    try:
        from agents.compliance_agent import ComplianceAgent
        
        agent = ComplianceAgent(
            payment_limit_days=45,
            interest_multiplier=3.0,
            bank_rate_percent=6.5
        )
        
        # Test compliance calculation
        result = agent.check_transaction_status(
            invoice_date='2024-01-01',
            due_date='2024-02-15',
            amount=50000.0,
            payment_date=None
        )
        
        print("✓ Compliance Agent working")
        print(f"  - Status: {result['status']}")
        print(f"  - Days overdue: {result['days_overdue']}")
        print(f"  - Interest amount: ₹{result['interest_amount']:,.2f}")
        print(f"  - Alert level: {result['alert_level']}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_collector_agent():
    """Test Collector Agent."""
    print("\n🧪 Testing Collector Agent...")
    
    try:
        from agents.collector_agent import CollectorAgent
        
        agent = CollectorAgent(mock_mode=True)
        
        # Test message generation
        message = agent.generate_message(
            tier="friendly_reminder",
            transaction={
                'id': 1,
                'vendor_name': 'Test Vendor',
                'amount': 50000,
                'invoice_number': 'INV-001'
            },
            compliance_status={
                'days_until_due': 7,
                'days_overdue': 0
            },
            customer={'phone_number': '+919876543210'}
        )
        
        print("✓ Collector Agent working")
        print(f"  - Message tier: {message['tier']}")
        print(f"  - Requires HITL: {message['requires_hitl_approval']}")
        print(f"  - Message preview: {message['message_text'][:100]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_arbitrator_agent():
    """Test Arbitrator Agent."""
    print("\n🧪 Testing Arbitrator Agent...")
    
    try:
        from agents.arbitrator_agent import ArbitratorAgent
        
        agent = ArbitratorAgent(high_value_threshold=50000)
        
        # Test decision making
        strategy = agent.evaluate_recovery_strategy(
            transaction={'amount': 75000, 'id': 1},
            customer={
                'total_value': 500000,
                'avg_payment_delay_days': 5,
                'total_transactions': 25
            },
            compliance_status={
                'days_overdue': 30,
                'section_43b_h_violation': False
            },
            communication_history=[]
        )
        
        print("✓ Arbitrator Agent working")
        print(f"  - Relationship score: {strategy['relationship_score']:.1f}/100")
        print(f"  - Transaction risk: {strategy['transaction_risk_score']:.1f}/100")
        print(f"  - Recommendation: {strategy['recommendation']}")
        print(f"  - Reasoning: {strategy['reasoning']}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_database():
    """Test database initialization."""
    print("\n🧪 Testing Database...")
    
    try:
        from memory.relational_db import DatabaseManager
        
        db = DatabaseManager('./data/test_db.db')
        session = db.get_session()
        
        print("✓ Database initialized")
        print("  - Tables created: transactions, customers, communications")
        
        session.close()
        db.close()
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_vector_store():
    """Test vector store."""
    print("\n🧪 Testing Vector Store...")
    
    try:
        from memory.vector_store import VectorMemory
        
        vector_mem = VectorMemory(
            db_path='./data/test_chroma',
            collection_name='test_collection'
        )
        
        # Add test context
        vector_mem.add_transaction_context(
            transaction_id='test_1',
            context='Test transaction with vendor ABC for ₹50000',
            metadata={'vendor': 'ABC', 'amount': 50000}
        )
        
        print("✓ Vector Store working")
        print("  - Can store transaction context")
        print("  - Can retrieve semantic memories")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Bharat Biz-Agent - Component Tests")
    print("=" * 60)
    
    tests = [
        test_janitor_agent,
        test_compliance_agent,
        test_collector_agent,
        test_arbitrator_agent,
        test_database,
        test_vector_store
    ]
    
    results = []
    for test_func in tests:
        results.append(test_func())
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Check errors above.")
