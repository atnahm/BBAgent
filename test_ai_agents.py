"""
Test suite for AI-enhanced agents.
Tests AI integration for Compliance, Collector, and Arbitrator agents.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from agents.compliance_agent import ComplianceAgent
from agents.collector_agent import CollectorAgent
from agents.arbitrator_agent import ArbitratorAgent

# Test data
test_transaction = {
    'id': 1,
    'vendor_name': 'ABC Enterprises',
    'amount': 75000,
    'invoice_number': 'INV-2024-001',
    'days_overdue': 50,
    'interest_amount': 1500,
    'legal_flag': True
}

test_customer = {
    'name': 'ABC Enterprises',
    'total_value': 500000,
    'total_transactions': 25,
    'avg_payment_delay_days': 10,
    'relationship_score': 65,
    'phone_number': '+919876543210'
}

test_compliance_status = {
    'status': 'overdue',
    'days_overdue': 50,
    'days_until_due': -5,
    'interest_amount': 1500,
    'interest_rate_annual': 18.0,
    'alert_level': 'severe',
    'legal_flag': True,
    'section_43b_h_violation': True
}

async def test_compliance_agent():
    """Test ComplianceAgent AI capabilities."""
    print("\n" + "="*60)
    print("🧪 Testing ComplianceAgent AI Integration")
    print("="*60)
    
    agent = ComplianceAgent()
    
    # Test 1: AI Risk Analysis
    print("\n📊 Test 1: AI-Powered Risk Analysis")
    print("-" * 60)
    
    result = await agent.run(
        task="analyze_risk",
        context={
            'transaction': test_transaction,
            'customer_history': {
                'avg_payment_delay_days': 10,
                'total_transactions': 25
            }
        }
    )
    
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"Model: {result.get('model')}")
        print(f"\nAI Analysis:\n{result.get('ai_analysis')}")
    else:
        print(f"Message: {result.get('message', result.get('error'))}")
    
    # Test 2: AI Compliance Summary
    print("\n📝 Test 2: AI-Generated Compliance Summary")
    print("-" * 60)
    
    result = await agent.run(
        task="generate_summary",
        context={
            'compliance_status': test_compliance_status,
            'transaction': test_transaction
        }
    )
    
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"Model: {result.get('model')}")
        print(f"\nSummary:\n{result.get('summary')}")
    else:
        print(f"Summary: {result.get('summary')}")

async def test_collector_agent():
    """Test CollectorAgent AI capabilities."""
    print("\n" + "="*60)
    print("💬 Testing CollectorAgent AI Integration")
    print("="*60)
    
    agent = CollectorAgent()
    
    # Test different message tiers
    tiers = ["friendly_reminder", "formal_notice", "legal_notice"]
    
    for tier in tiers:
        print(f"\n📱 Test: AI Message Generation - {tier}")
        print("-" * 60)
        
        result = await agent.run(
            task="generate_ai_message",
            context={
                'tier': tier,
                'transaction': test_transaction,
                'compliance_status': test_compliance_status,
                'customer': test_customer
            }
        )
        
        print(f"Status: {result.get('status')}")
        print(f"Tier: {result.get('tier')}")
        print(f"AI Generated: {result.get('ai_generated', False)}")
        if result.get('model'):
            print(f"Model: {result.get('model')}")
        print(f"Requires HITL: {result.get('requires_hitl_approval')}")
        print(f"\nMessage:\n{result.get('message_text')}")

async def test_arbitrator_agent():
    """Test ArbitratorAgent AI capabilities."""
    print("\n" + "="*60)
    print("⚖️  Testing ArbitratorAgent AI Integration")
    print("="*60)
    
    agent = ArbitratorAgent()
    
    # Test AI Strategy Evaluation
    print("\n🎯 Test: AI-Powered Strategic Recommendation")
    print("-" * 60)
    
    result = await agent.run(
        task="evaluate_ai_strategy",
        context={
            'transaction': test_transaction,
            'customer': test_customer,
            'compliance_status': test_compliance_status,
            'communication_history': []
        }
    )
    
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"Model: {result.get('model')}")
        print(f"Relationship Score: {result.get('relationship_score')}/100")
        print(f"Transaction Risk: {result.get('transaction_risk_score')}/100")
        print(f"Customer Tier: {result.get('customer_tier')}")
        print(f"Risk Level: {result.get('risk_level')}")
        print(f"Requires HITL: {result.get('requires_hitl_approval')}")
        print(f"\nAI Recommendation:\n{result.get('ai_recommendation')}")
    else:
        print(f"Recommendation: {result.get('recommendation')}")
        print(f"Reasoning: {result.get('reasoning')}")

async def main():
    """Run all AI agent tests."""
    print("\n" + "="*60)
    print("🚀 AI-Enhanced Agents Test Suite")
    print("="*60)
    print("\nThis test suite validates AI integration across all agents.")
    print("If HuggingFace API key is not configured, agents will")
    print("gracefully fallback to rule-based logic.\n")
    
    try:
        await test_compliance_agent()
        await test_collector_agent()
        await test_arbitrator_agent()
        
        print("\n" + "="*60)
        print("✅ All AI Agent Tests Completed")
        print("="*60)
        print("\nNote: Check output above for AI vs fallback behavior.")
        print("AI features require valid HUGGINGFACE_API_KEY in .env\n")
        
    except Exception as e:
        print(f"\n❌ Test Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
