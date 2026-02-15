"""
Performance Testing Script
Test system throughput and response times.
"""
import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime
import statistics

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator

class PerformanceTester:
    """Test automation system performance."""
    
    def __init__(self):
        print("🧪 Initializing Performance Tester...")
        self.orchestrator = Orchestrator()
        self.results = []
    
    async def test_compliance_check_speed(self, iterations=100):
        """Test compliance check performance."""
        print(f"\n📊 Testing Compliance Check Speed ({iterations} iterations)...")
        
        times = []
        
        for i in range(iterations):
            start = time.time()
            
            await self.orchestrator.compliance.run(
                task="check_transaction",
                context={
                    'invoice_date': '2024-01-01',
                    'due_date': '2024-02-15',
                    'amount': 50000.0,
                    'payment_date': None
                }
            )
            
            elapsed = time.time() - start
            times.append(elapsed)
            
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i+1}/{iterations}")
        
        return {
            'test': 'compliance_check',
            'iterations': iterations,
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'median_time': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    async def test_message_generation_speed(self, iterations=50):
        """Test message generation performance."""
        print(f"\n📧 Testing Message Generation Speed ({iterations} iterations)...")
        
        times = []
        
        for i in range(iterations):
            start = time.time()
            
            await self.orchestrator.collector.run(
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
            )
            
            elapsed = time.time() - start
            times.append(elapsed)
            
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i+1}/{iterations}")
        
        return {
            'test': 'message_generation',
            'iterations': iterations,
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'median_time': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    async def test_arbitrator_scoring_speed(self, iterations=100):
        """Test arbitrator scoring performance."""
        print(f"\n⚖️  Testing Arbitrator Scoring Speed ({iterations} iterations)...")
        
        times = []
        
        for i in range(iterations):
            start = time.time()
            
            self.orchestrator.arbitrator.calculate_customer_scores(
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
            
            elapsed = time.time() - start
            times.append(elapsed)
            
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i+1}/{iterations}")
        
        return {
            'test': 'arbitrator_scoring',
            'iterations': iterations,
            'avg_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'median_time': statistics.median(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def test_database_operations(self, iterations=1000):
        """Test database read/write performance."""
        print(f"\n💾 Testing Database Operations ({iterations} iterations)...")
        
        from memory.relational_db import Transaction, Customer
        
        # Write test
        write_times = []
        db_session = self.orchestrator.db.get_session()
        
        try:
            for i in range(iterations):
                start = time.time()
                
                # Query operation
                db_session.query(Transaction).limit(10).all()
                
                elapsed = time.time() - start
                write_times.append(elapsed)
                
                if (i + 1) % 100 == 0:
                    print(f"   Progress: {i+1}/{iterations}")
        
        finally:
            db_session.close()
        
        return {
            'test': 'database_operations',
            'iterations': iterations,
            'avg_time': statistics.mean(write_times),
            'min_time': min(write_times),
            'max_time': max(write_times),
            'median_time': statistics.median(write_times),
            'std_dev': statistics.stdev(write_times) if len(write_times) > 1 else 0
        }
    
    def print_results(self, result):
        """Print test results."""
        print(f"\n{'='*60}")
        print(f"Test: {result['test'].upper()}")
        print(f"{'='*60}")
        print(f"Iterations:   {result['iterations']}")
        print(f"Avg Time:     {result['avg_time']*1000:.2f}ms")
        print(f"Min Time:     {result['min_time']*1000:.2f}ms")
        print(f"Max Time:     {result['max_time']*1000:.2f}ms")
        print(f"Median Time:  {result['median_time']*1000:.2f}ms")
        print(f"Std Dev:      {result['std_dev']*1000:.2f}ms")
        print(f"Throughput:   {result['iterations']/sum([result['avg_time']*result['iterations']]):.2f} ops/sec")
        print(f"{'='*60}")
    
    async def run_all_tests(self):
        """Run all performance tests."""
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUITE")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run tests
        results = []
        
        # Test 1: Compliance checks
        result = await self.test_compliance_check_speed(iterations=100)
        self.print_results(result)
        results.append(result)
        
        # Test 2: Message generation
        result = await self.test_message_generation_speed(iterations=50)
        self.print_results(result)
        results.append(result)
        
        # Test 3: Arbitrator scoring
        result = await self.test_arbitrator_scoring_speed(iterations=100)
        self.print_results(result)
        results.append(result)
        
        # Test 4: Database operations
        result = self.test_database_operations(iterations=1000)
        self.print_results(result)
        results.append(result)
        
        # Summary
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        
        for result in results:
            throughput = result['iterations'] / (result['avg_time'] * result['iterations'])
            print(f"{result['test']:30} {result['avg_time']*1000:8.2f}ms  {throughput:8.2f} ops/sec")
        
        print("="*60)
        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return results

if __name__ == "__main__":
    tester = PerformanceTester()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        results = loop.run_until_complete(tester.run_all_tests())
    finally:
        loop.close()
