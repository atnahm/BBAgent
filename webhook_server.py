"""
Webhook Server for External Integrations
Receives invoice data from external systems via HTTP API.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import base64
import tempfile

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator

app = Flask(__name__)
orchestrator = Orchestrator()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Bharat Biz-Agent',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/invoice/upload', methods=['POST'])
def upload_invoice():
    """
    Upload invoice for processing.
    
    Request body:
    {
        "file_data": "base64_encoded_file",
        "file_type": "image" or "voice",
        "filename": "invoice.jpg",
        "metadata": {
            "source": "email",
            "sender": "vendor@example.com"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'file_data' not in data:
            return jsonify({'error': 'Missing file_data'}), 400
        
        # Decode file
        file_data = base64.b64decode(data['file_data'])
        file_type = data.get('file_type', 'image')
        filename = data.get('filename', 'invoice.jpg')
        
        # Save to temp file
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(file_data)
            tmp_path = tmp_file.name
        
        # Process invoice
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            orchestrator.process_invoice(tmp_path, file_type)
        )
        
        loop.close()
        
        # Clean up
        Path(tmp_path).unlink()
        
        if result['status'] == 'success':
            return jsonify({
                'status': 'success',
                'transaction_id': result['transaction_id'],
                'vendor_name': result['ingestion']['extraction']['vendor_name'],
                'amount': result['ingestion']['extraction']['amount'],
                'compliance_status': result['compliance']['compliance']['status'],
                'message': 'Invoice processed successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'error': result.get('error')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/invoice/manual', methods=['POST'])
def manual_entry():
    """
    Manual invoice entry.
    
    Request body:
    {
        "vendor_name": "ABC Corp",
        "gstin": "29ABCDE1234F1Z5",
        "amount": 50000.00,
        "invoice_number": "INV-001",
        "invoice_date": "2024-01-15",
        "payment_terms": "45 days"
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['vendor_name', 'amount', 'invoice_number', 'invoice_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        from memory.relational_db import Customer, Transaction
        from datetime import timedelta
        
        db_session = orchestrator.db.get_session()
        
        try:
            # Find or create customer
            customer = db_session.query(Customer).filter_by(
                name=data['vendor_name']
            ).first()
            
            if not customer:
                customer = Customer(
                    name=data['vendor_name'],
                    gstin=data.get('gstin'),
                    total_transactions=0,
                    total_value=0.0
                )
                db_session.add(customer)
                db_session.commit()
            
            # Parse dates
            from datetime import datetime
            invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d')
            
            # Calculate due date
            payment_days = int(data.get('payment_terms', '45').split()[0])
            due_date = invoice_date + timedelta(days=payment_days)
            
            # Create transaction
            transaction = Transaction(
                vendor_name=data['vendor_name'],
                gstin=data.get('gstin'),
                amount=float(data['amount']),
                invoice_number=data['invoice_number'],
                invoice_date=invoice_date,
                due_date=due_date,
                source_type='api',
                customer_id=customer.id,
                status='pending'
            )
            db_session.add(transaction)
            
            # Update customer
            customer.total_transactions += 1
            customer.total_value += float(data['amount'])
            
            db_session.commit()
            
            return jsonify({
                'status': 'success',
                'transaction_id': transaction.id,
                'message': 'Transaction created successfully'
            }), 201
            
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filters."""
    try:
        from memory.relational_db import Transaction
        
        db_session = orchestrator.db.get_session()
        
        try:
            # Get query parameters
            status = request.args.get('status')
            limit = int(request.args.get('limit', 100))
            
            query = db_session.query(Transaction)
            
            if status:
                query = query.filter_by(status=status)
            
            transactions = query.limit(limit).all()
            
            result = [{
                'id': t.id,
                'vendor_name': t.vendor_name,
                'amount': t.amount,
                'invoice_number': t.invoice_number,
                'status': t.status,
                'days_overdue': t.days_overdue,
                'invoice_date': t.invoice_date.isoformat() if t.invoice_date else None,
                'due_date': t.due_date.isoformat() if t.due_date else None
            } for t in transactions]
            
            return jsonify({
                'status': 'success',
                'count': len(result),
                'transactions': result
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/compliance/report', methods=['GET'])
def compliance_report():
    """Get compliance summary report."""
    try:
        from memory.relational_db import Transaction
        
        db_session = orchestrator.db.get_session()
        
        try:
            all_txns = db_session.query(Transaction).all()
            
            total = len(all_txns)
            overdue = len([t for t in all_txns if t.status == 'overdue'])
            pending = len([t for t in all_txns if t.status == 'pending'])
            paid = len([t for t in all_txns if t.status == 'paid'])
            
            total_receivables = sum(t.amount for t in all_txns if t.status != 'paid')
            total_interest = sum(t.interest_amount or 0 for t in all_txns)
            
            return jsonify({
                'status': 'success',
                'report': {
                    'total_transactions': total,
                    'pending': pending,
                    'overdue': overdue,
                    'paid': paid,
                    'total_receivables': total_receivables,
                    'total_interest_accrued': total_interest,
                    'compliance_rate': ((total - overdue) / total * 100) if total > 0 else 100
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 200
            
        finally:
            db_session.close()
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🌐 Starting Webhook Server...")
    print("📡 Endpoints:")
    print("   GET  /health")
    print("   POST /api/v1/invoice/upload")
    print("   POST /api/v1/invoice/manual")
    print("   GET  /api/v1/transactions")
    print("   GET  /api/v1/compliance/report")
    print("\n🚀 Server running on http://localhost:5000\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
