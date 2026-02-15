"""ADK-Enhanced Multi-Agent Orchestrator."""
from google.adk import sessions
from google.adk.agents import Agent
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from agents.janitor_agent import JanitorAgent
from agents.compliance_agent import ComplianceAgent
from agents.collector_agent import CollectorAgent
from agents.arbitrator_agent import ArbitratorAgent
from memory.relational_db import DatabaseManager, Transaction, Customer, Communication
from memory.vector_store import VectorMemory
from config_loader import CONFIG

from utils import parse_date

class Orchestrator:
    """
    Google ADK-powered orchestrator for multi-agent coordination.
    Manages agent sessions and workflow state.
    """
    
    def __init__(self):
        """Initialize ADK orchestrator with all agents."""
        # Initialize Janitor with HuggingFace Vision OCR only
        self.janitor = JanitorAgent(
            huggingface_config=CONFIG['llm'].get('huggingface')
        )
        
        self.compliance = ComplianceAgent(
            payment_limit_days=CONFIG['compliance']['msmed_act']['payment_limit_days'],
            interest_multiplier=CONFIG['compliance']['msmed_act']['interest_multiplier'],
            bank_rate_percent=CONFIG['compliance']['msmed_act']['bank_rate_percent']
        )
        
        self.collector = CollectorAgent(
            mock_mode=CONFIG['whatsapp']['mock_mode']
        )
        
        self.arbitrator = ArbitratorAgent(
            high_value_threshold=50000  # ₹50,000
        )
        
        # Initialize memory systems
        self.db = DatabaseManager(CONFIG['relational_db']['path'])
        self.vector_memory = VectorMemory(
            db_path=CONFIG['vector_db']['path'],
            collection_name=CONFIG['vector_db']['collection_name']
        )
        
        # Initialize ADK session with required fields
        import uuid
        self.session = sessions.Session(
            id=str(uuid.uuid4()),
            appName="BharatBizAgent",
            userId="default_user"
        )
        
    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """Deprecated: Use utils.parse_date instead."""
        return parse_date(date_str)
    
    async def process_invoice(
        self,
        file_path: str,
        source_type: str = 'image',
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ADK-powered invoice processing pipeline.
        Uses async agent execution for better performance.
        """
        try:
            # Step 1: Janitor Agent extracts data
            if source_type == 'image':
                extraction_result = await self.janitor.run(
                    task="extract_invoice",
                    context={'image_path': file_path, 'provider': provider}
                )
            elif source_type == 'voice':
                extraction_result = await self.janitor.run(
                    task="process_voice",
                    context={'audio_path': file_path}
                )
            else:
                return {"error": "Invalid source type"}
            
            if extraction_result['status'] != 'success':
                return extraction_result
            
            data = extraction_result['data']
            
            # Ensure invoice_date is set (default to today if missing)
            if not data.get('invoice_date'):
                from datetime import datetime
                data['invoice_date'] = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Ensure due_date is set (default to 45 days from invoice_date if missing)
            if not data.get('due_date') and data.get('invoice_date'):
                from datetime import timedelta
                invoice_date = self._parse_date(data['invoice_date'])
                if invoice_date:
                    data['due_date'] = (invoice_date + timedelta(days=45)).strftime('%Y-%m-%d')
            
            # If still no due_date, use today + 45 days
            if not data.get('due_date'):
                from datetime import datetime, timedelta
                data['due_date'] = (datetime.utcnow() + timedelta(days=45)).strftime('%Y-%m-%d')
            
            # Step 2: Validate GSTIN (sync operation)
            gstin_validation = self.janitor.validate_gstin(
                data.get('gstin'),
                mock_mode=CONFIG['gstin']['mock_mode']
            )
            
            # Step 3: Save to database
            db_session = self.db.get_session()
            try:
                # Find or create customer
                customer = db_session.query(Customer).filter_by(
                    gstin=data.get('gstin')
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
                
                # Check if transaction exists
                existing_transaction = db_session.query(Transaction).filter_by(
                    invoice_number=data.get('invoice_number')
                ).first()

                if existing_transaction:
                    print(f"Transaction {data.get('invoice_number')} already exists. Updating...")
                    transaction = existing_transaction
                    transaction.vendor_name = data['vendor_name']
                    transaction.gstin = data.get('gstin')
                    transaction.amount = data['amount']
                    transaction.invoice_date = self._parse_date(data['invoice_date'])
                    transaction.due_date = self._parse_date(data['due_date'])
                    transaction.source_type = source_type
                    transaction.raw_data_path = file_path
                    transaction.customer_id = customer.id
                else:
                    transaction = Transaction(
                        vendor_name=data['vendor_name'],
                        gstin=data.get('gstin'),
                        amount=data['amount'],
                        invoice_number=data.get('invoice_number'),
                        invoice_date=self._parse_date(data['invoice_date']),
                        due_date=self._parse_date(data['due_date']),
                        source_type=source_type,
                        raw_data_path=file_path,
                        customer_id=customer.id,
                        status='pending'
                    )
                    db_session.add(transaction)
                
                db_session.commit()
                
                # Update customer stats
                customer.total_transactions += 1
                customer.total_value += data['amount']
                db_session.commit()
                
                transaction_id = transaction.id
                
                # Step 4: Run Compliance Check
                compliance_result = await self.compliance.run(
                    task="check_transaction",
                    context={
                        "invoice_date": data['invoice_date'],
                        "due_date": data['due_date'],
                        "amount": data['amount'],
                        "payment_date": None
                    }
                )
                
                # Step 4.5: AI Risk Analysis (if enabled)
                ai_risk_analysis = None
                try:
                    ai_risk_analysis = await self.compliance.run(
                        task="analyze_risk",
                        context={
                            "transaction": {
                                'vendor_name': data['vendor_name'],
                                'amount': data['amount'],
                                'days_overdue': compliance_result.get('days_overdue', 0),
                                'interest_amount': compliance_result.get('interest_amount', 0),
                                'legal_flag': compliance_result.get('legal_flag', False)
                            },
                            "customer_history": {
                                'avg_payment_delay_days': customer.avg_payment_delay_days,
                                'total_transactions': customer.total_transactions
                            }
                        }
                    )
                except Exception as e:
                    print(f"AI risk analysis failed: {e}")
                
                # Step 5: Run Strategy/Arbitrator Evaluation
                strategy_result = await self.arbitrator.run(
                    task="evaluate_ai_strategy",  # Use AI-enhanced method
                    context={
                        "transaction": {
                            "id": transaction_id,
                            "vendor_name": data['vendor_name'],
                            "amount": data['amount'],
                            "days_overdue": compliance_result.get('days_overdue', 0),
                            "legal_flag": compliance_result.get('legal_flag', False)
                        },
                        "customer": {
                            "name": customer.name,
                            "total_value": customer.total_value,
                            "avg_payment_delay_days": customer.avg_payment_delay_days,
                            "total_transactions": customer.total_transactions
                        },
                        "compliance_status": compliance_result,
                        "communication_history": []
                    }
                )

                # Step 6: Generate Message if needed
                message_result = None
                if strategy_result.get('recommendation') or strategy_result.get('ai_recommendation'):
                    # Determine message tier
                    recommendation = strategy_result.get('recommendation', 'standard_process')
                    message_tier = "friendly_reminder"  # Default
                    
                    if recommendation == 'diplomatic_escalation':
                        message_tier = "formal_notice"
                    elif recommendation == 'aggressive_recovery':
                        message_tier = "legal_notice"
                    
                    # Try AI message generation first
                    try:
                        message_result = await self.collector.run(
                            task="generate_ai_message",
                            context={
                                'tier': message_tier,
                                'transaction': {
                                    'id': transaction_id,
                                    'vendor_name': data['vendor_name'],
                                    'amount': data['amount'],
                                    'invoice_number': data.get('invoice_number', 'N/A')
                                },
                                'compliance_status': compliance_result,
                                'customer': {
                                    'name': customer.name,
                                    'phone_number': customer.phone_number,
                                    'relationship_score': 50  # Default
                                }
                            }
                        )
                    except Exception as e:
                        print(f"AI message generation failed: {e}")
                        # Fallback to simple message
                        message_result = {
                            "message_text": f"Generated {message_tier} for {data['vendor_name']}",
                            "requires_hitl_approval": strategy_result.get('requires_hitl_approval', False),
                            "tier": message_tier
                        }
                    
                    # Create communication record
                    comm = Communication(
                        transaction_id=transaction_id,
                        message_type=message_result.get('tier', message_tier),
                        message_text=message_result.get('message_text', ''),
                        delivery_status='pending_approval' if message_result.get('requires_hitl_approval') else 'approved'
                    )
                    db_session.add(comm)
                    db_session.commit()

                # Step 7: Store in vector memory
                context_text = f"""
                Transaction with {data['vendor_name']}
                Amount: ₹{data['amount']}
                Invoice: {data.get('invoice_number', 'N/A')}
                Compliance: {compliance_result.get('status')}
                Strategy: {strategy_result.get('recommendation')}
                """
                
                self.vector_memory.add_transaction_context(
                    transaction_id=str(transaction_id),
                    context=context_text,
                    metadata={
                        "vendor_name": str(data['vendor_name']),
                        "amount": float(data['amount'] or 0.0),
                        "status": "pending",
                        "customer_id": str(customer.id),
                        "agent": str(data.get('agent', 'Unknown'))
                    }
                )
                # ChromaDB v0.4+ auto-persists, no need to call persist()
                
                return {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "ingestion": {"extraction": data},
                    "compliance": {
                        "compliance": compliance_result,
                        "ai_risk_analysis": ai_risk_analysis  # NEW: AI insights
                    },
                    "strategy": strategy_result,
                    "message": message_result,
                    "gstin_validation": gstin_validation,
                    "message_text": "Invoice processed successfully with complete ADK workflow"
                }
                
            except Exception as e:
                db_session.rollback()
                return {"status": "error", "error": str(e)}
            finally:
                db_session.close()
                
        except Exception as e:
            return {"status": "error", "error": f"ADK processing error: {str(e)}"}
    
    async def check_compliance_adk(self, transaction_id: int) -> Dict[str, Any]:
        """ADK-powered compliance checking."""
        db_session = self.db.get_session()
        
        try:
            transaction = db_session.query(Transaction).get(transaction_id)
            if not transaction:
                return {"error": "Transaction not found"}
            
            # Run compliance agent
            compliance_result = await self.compliance.run(
                task="check_transaction",
                context={
                    'invoice_date': transaction.invoice_date.strftime('%Y-%m-%d'),
                    'due_date': transaction.due_date.strftime('%Y-%m-%d'),
                    'amount': transaction.amount,
                    'payment_date': transaction.payment_date.strftime('%Y-%m-%d') if transaction.payment_date else None
                }
            )
            
            # Update transaction with compliance data
            transaction.days_overdue = compliance_result['days_overdue']
            transaction.interest_amount = compliance_result['interest_amount']
            transaction.legal_flag = compliance_result['legal_flag']
            
            if compliance_result['status'] == 'overdue':
                transaction.status = 'overdue'
            
            db_session.commit()
            
            return {
                "status": "success",
                "compliance": compliance_result,
                "message": "Compliance check completed with ADK"
            }
            
        finally:
            db_session.close()
    
    def run_sync(self, coro):
        """Helper to run async functions synchronously."""
        return asyncio.run(coro)
    
    async def process_full_workflow_adk(
        self,
        file_path: str,
        source_type: str = 'image'
    ) -> Dict[str, Any]:
        """
        Complete end-to-end ADK workflow:
        Janitor → Compliance → Arbitrator → Collector
        """
        try:
            # Step 1: Ingest invoice
            ingest_result = await self.process_invoice_adk(file_path, source_type)
            if ingest_result['status'] != 'success':
                return ingest_result
            
            transaction_id = ingest_result['transaction_id']
            
            # Step 2: Check compliance
            compliance_result = await self.check_compliance_adk(transaction_id)
            if compliance_result['status'] != 'success':
                return compliance_result
            
            # Step 3: Get transaction and customer for decision making
            db_session = self.db.get_session()
            try:
                transaction = db_session.query(Transaction).get(transaction_id)
                customer = transaction.customer
                
                # Step 4: Arbitrator evaluates strategy
                strategy_result = await self.arbitrator.run(
                    task="evaluate_strategy",
                    context={
                        'transaction': {
                            'id': transaction.id,
                            'amount': transaction.amount,
                            'vendor_name': transaction.vendor_name,
                            'invoice_number': transaction.invoice_number,
                            'days_overdue': transaction.days_overdue
                        },
                        'customer': {
                            'id': customer.id,
                            'name': customer.name,
                            'total_value': customer.total_value,
                            'total_transactions': customer.total_transactions,
                            'avg_payment_delay_days': customer.avg_payment_delay_days
                        },
                        'compliance_status': compliance_result['compliance'],
                        'communication_history': []
                    }
                )
                
                # Step 5: Determine message tier
                tier_result = await self.collector.run(
                    task="determine_tier",
                    context={
                        'compliance_status': compliance_result['compliance'],
                        'communication_history': []
                    }
                )
                
                message_tier = tier_result if isinstance(tier_result, str) else tier_result.get('tier', 'none')
                
                # Step 6: Generate message if needed
                message_result = None
                if message_tier != "none":
                    message_result = await self.collector.run(
                        task="generate_message",
                        context={
                            'tier': message_tier,
                            'transaction': {
                                'id': transaction.id,
                                'vendor_name': transaction.vendor_name,
                                'amount': transaction.amount,
                                'invoice_number': transaction.invoice_number
                            },
                            'compliance_status': compliance_result['compliance'],
                            'customer': {'phone_number': customer.phone_number}
                        }
                    )
                    
                    # Save to database if requires HITL
                    if message_result.get('requires_hitl_approval'):
                        comm = Communication(
                            transaction_id=transaction_id,
                            message_type=message_tier,
                            message_text=message_result['message_text'],
                            requires_approval=True,
                            approval_status='pending'
                        )
                        db_session.add(comm)
                        db_session.commit()
                
                db_session.close()
                
                return {
                    "status": "success",
                    "workflow": "complete",
                    "transaction_id": transaction_id,
                    "ingestion": ingest_result,
                    "compliance": compliance_result,
                    "strategy": strategy_result,
                    "message_tier": message_tier,
                    "message": message_result,
                    "workflow_status": "ADK workflow completed successfully"
                }
                
            except Exception as e:
                db_session.rollback()
                db_session.close()
                return {"status": "error", "error": f"Workflow error: {str(e)}"}
                
        except Exception as e:
            return {"status": "error", "error": f"ADK workflow error: {str(e)}"}

