"""
Batch Invoice Processor
Process multiple invoices in bulk with parallel execution.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator

class BatchProcessor:
    """Process multiple invoices in parallel."""
    
    def __init__(self, max_workers=5):
        print(f"🚀 Initializing Batch Processor (max workers: {max_workers})...")
        self.orchestrator = Orchestrator()
        self.max_workers = max_workers
        self.results = []
    
    async def process_single_invoice(self, file_path, source_type='image'):
        """Process a single invoice."""
        try:
            print(f"  📄 Processing: {Path(file_path).name}")
            
            result = await self.orchestrator.process_invoice(file_path, source_type)
            
            if result['status'] == 'success':
                print(f"  ✅ Success: {result['ingestion']['extraction']['vendor_name']} - ₹{result['ingestion']['extraction']['amount']:,.2f}")
            else:
                print(f"  ❌ Failed: {result.get('error')}")
            
            return {
                'file': str(file_path),
                'status': result['status'],
                'result': result
            }
            
        except Exception as e:
            print(f"  ❌ Error processing {Path(file_path).name}: {str(e)}")
            return {
                'file': str(file_path),
                'status': 'error',
                'error': str(e)
            }
    
    async def process_batch(self, file_paths, source_type='image'):
        """Process multiple invoices concurrently."""
        print(f"\n{'='*60}")
        print(f"📦 BATCH PROCESSING - {len(file_paths)} files")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        
        # Process concurrently
        tasks = [self.process_single_invoice(fp, source_type) for fp in file_paths]
        results = await asyncio.gather(*tasks)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Summary
        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len(results) - success_count
        
        print(f"\n{'='*60}")
        print(f"📊 BATCH SUMMARY")
        print(f"{'='*60}")
        print(f"Total Files: {len(file_paths)}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"📈 Throughput: {len(file_paths)/duration:.2f} files/sec")
        print(f"{'='*60}\n")
        
        return results
    
    def process_directory(self, directory_path, recursive=False):
        """Process all invoices in a directory."""
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            print(f"❌ Directory not found: {directory_path}")
            return
        
        # Find all invoice files
        patterns = ['*.jpg', '*.jpeg', '*.png', '*.pdf']
        files = []
        
        for pattern in patterns:
            if recursive:
                files.extend(dir_path.rglob(pattern))
            else:
                files.extend(dir_path.glob(pattern))
        
        if not files:
            print(f"⚠️  No invoice files found in {directory_path}")
            return
        
        print(f"📁 Found {len(files)} invoice files")
        
        # Process batch
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(self.process_batch(files))
            
            # Save results
            self._save_results(results, dir_path)
            
        finally:
            loop.close()
    
    def _save_results(self, results, output_dir):
        """Save batch processing results to JSON."""
        output_file = output_dir / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {output_file}")

def main():
    """CLI interface for batch processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch Invoice Processor')
    parser.add_argument('directory', help='Directory containing invoice files')
    parser.add_argument('--recursive', '-r', action='store_true', help='Process subdirectories')
    parser.add_argument('--workers', '-w', type=int, default=5, help='Max concurrent workers')
    
    args = parser.parse_args()
    
    processor = BatchProcessor(max_workers=args.workers)
    processor.process_directory(args.directory, recursive=args.recursive)

if __name__ == "__main__":
    main()
