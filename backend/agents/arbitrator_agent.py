"""Enhanced Arbitrator Agent using Google ADK framework."""
from google.adk.agents import BaseAgent
from typing import Dict, Any, List, Optional

class ArbitratorAgent(BaseAgent):
    """
    ADK-powered Arbitrator Agent for governance and relationship management.
    Balances recovery vs relationship preservation using dual-manager logic.
    """
    
    def __init__(self, high_value_threshold: float = 50000):
        """Initialize Arbitrator Agent with ADK BaseAgent."""
        super().__init__(
            name="ArbitratorAgent",
            description="Governance and relationship preservation specialist"
        )
        
        # Store configuration as private attribute to avoid Pydantic validation
        object.__setattr__(self, '_high_value_threshold', high_value_threshold)
        
        # Initialize AI client for strategic decisions
        try:
            import os
            from backend.utils import AIModelClient
            from backend.config_loader import CONFIG
            
            llm_config = CONFIG.get('llm', {})
            provider = llm_config.get('provider', 'huggingface')
            
            if provider == "local":
                local_config = llm_config.get("local", {})
                object.__setattr__(self, '_ai_client', AIModelClient(
                    api_key="none",
                    model_name=local_config.get("model", "llama3"),
                    endpoint_url=local_config.get("endpoint_url", "http://localhost:11434/api/generate")
                ))
                object.__setattr__(self, '_ai_enabled', True)
                print(f"✅ ArbitratorAgent AI enabled with LOCAL {local_config.get('model')}")
            else:
                api_key = os.getenv('HUGGINGFACE_API_KEY')
                ai_config = CONFIG.get('ai_models', {}).get('huggingface', {})
                model_name = ai_config.get('models', {}).get('arbitrator_llm', 'mistralai/Mistral-7B-Instruct-v0.3')

                if api_key and api_key != 'your_huggingface_api_key_here':
                    object.__setattr__(self, '_ai_client', AIModelClient(
                        api_key=api_key,
                        model_name=model_name,
                        timeout=ai_config.get('timeout', 30),
                        max_retries=ai_config.get('max_retries', 3)
                    ))
                    object.__setattr__(self, '_ai_enabled', True)
                    print(f"✅ ArbitratorAgent AI enabled with {model_name}")
                else:
                    object.__setattr__(self, '_ai_client', None)
                    object.__setattr__(self, '_ai_enabled', False)
                    print("⚠️ ArbitratorAgent AI disabled (no API key)")
        except Exception as e:
            print(f"⚠️ Failed to initialize AI for ArbitratorAgent: {e}")
            object.__setattr__(self, '_ai_client', None)
            object.__setattr__(self, '_ai_enabled', False)
    
    async def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ADK-standard run method for governance decisions.
        
        Args:
            task: Governance task type
            context: Transaction, customer, and compliance details
        
        Returns:
            Strategic recommendations and approval decisions
        """
        if task == "evaluate_strategy":
            if self._ai_enabled and self._ai_client:
                # Dynamically use AI if configured
                result = await self.evaluate_ai_strategy(
                    transaction=context['transaction'],
                    customer=context['customer'],
                    compliance_status=context['compliance_status'],
                    communication_history=context.get('communication_history', [])
                )
            else:
                result = self.evaluate_recovery_strategy(
                    transaction=context['transaction'],
                    customer=context['customer'],
                    compliance_status=context['compliance_status'],
                    communication_history=context.get('communication_history', [])
                )

            # Advanced Integration: Auto-Escalation Check
            if result.get("transaction_risk_score", 0) > 80:
                result["trigger_escalation"] = True

            return result
        elif task == "evaluate_ai_strategy":
            # Direct AI call backward compatibility
            return await self.evaluate_ai_strategy(
                transaction=context['transaction'],
                customer=context['customer'],
                compliance_status=context['compliance_status'],
                communication_history=context.get('communication_history', [])
            )
        elif task == "approve_action":
            return self.evaluate_hitl_approval(
                action_type=context['action_type'],
                transaction=context['transaction'],
                customer=context['customer'],
                message_details=context.get('message_details')
            )
        elif task == "score_customer":
            return self.calculate_customer_scores(
                customer=context['customer'],
                transaction=context.get('transaction')
            )
        else:
            return {"error": f"Unknown task: {task}"}
    
    def evaluate_recovery_strategy(
        self,
        transaction: Dict[str, Any],
        customer: Dict[str, Any],
        compliance_status: Dict[str, Any],
        communication_history: List[Dict[str, Any]] = []
    ) -> Dict[str, Any]:
        """Evaluate and recommend recovery strategy."""
        
        # Calculate scores
        scores = self.calculate_customer_scores(customer, transaction)
        relationship_score = scores['relationship_score']
        transaction_risk = scores['transaction_risk_score']
        
        # Decision matrix
        if relationship_score >= 70 and transaction_risk < 50:
            recommendation = "grant_grace_period"
            reasoning = "High-value customer with low transaction risk. Preserve relationship."
            action = "Extend grace period by 7 days. Send diplomatic reminder."
            
        elif relationship_score >= 70 and transaction_risk >= 50:
            recommendation = "diplomatic_escalation"
            reasoning = "Valuable customer but significant risk. Balance required."
            action = "Send formal notice with relationship consideration."
            
        elif relationship_score < 40 and transaction_risk >= 60:
            recommendation = "aggressive_recovery"
            reasoning = "Low customer value, high risk. Prioritize recovery."
            action = "Proceed with legal notice and recovery process."
            
        else:
            recommendation = "standard_process"
            reasoning = "Standard case. Follow normal compliance workflow."
            action = "Apply standard recovery protocol based on days overdue."
        
        # Determine HITL requirement
        requires_hitl = self._requires_hitl_approval(
            recommendation, 
            transaction.get('amount', 0),
            relationship_score
        )
        
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "suggested_action": action,
            "relationship_score": relationship_score,
            "transaction_risk_score": transaction_risk,
            "requires_hitl_approval": requires_hitl,
            "customer_tier": self._get_customer_tier(relationship_score),
            "priority_level": self._get_priority_level(transaction_risk),
            "agent": self.name
        }
    
    def calculate_customer_scores(
        self,
        customer: Dict[str, Any],
        transaction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate relationship and risk scores."""
        
        # Relationship Score (0-100)
        relationship_score = 0
        
        # Business value (0-30 points)
        total_value = customer.get('total_value', 0)
        if total_value > 1000000:
            relationship_score += 30
        elif total_value > 500000:
            relationship_score += 20
        elif total_value > 100000:
            relationship_score += 10
        
        # Payment history (0-30 points)
        avg_delay = customer.get('avg_payment_delay_days', 0)
        if avg_delay == 0:
            relationship_score += 30
        elif avg_delay <= 5:
            relationship_score += 25
        elif avg_delay <= 10:
            relationship_score += 15
        elif avg_delay <= 20:
            relationship_score += 5
        
        # Transaction count (0-20 points)
        txn_count = customer.get('total_transactions', 0)
        if txn_count > 50:
            relationship_score += 20
        elif txn_count > 20:
            relationship_score += 15
        elif txn_count > 10:
            relationship_score += 10
        elif txn_count > 5:
            relationship_score += 5
        
        # Transaction Risk Score (0-100)
        transaction_risk = 0
        
        if transaction:
            # Amount urgency (0-40 points)
            amount = transaction.get('amount', 0)
            if amount > 100000:
                transaction_risk += 40
            elif amount > 50000:
                transaction_risk += 30
            elif amount > 25000:
                transaction_risk += 20
            elif amount > 10000:
                transaction_risk += 10
            
            # Overdue severity (0-40 points)
            days_overdue = transaction.get('days_overdue', 0)
            if days_overdue > 60:
                transaction_risk += 40
            elif days_overdue > 45:
                transaction_risk += 35
            elif days_overdue > 30:
                transaction_risk += 25
            elif days_overdue > 15:
                transaction_risk += 15
            elif days_overdue > 0:
                transaction_risk += 5
            
            # Legal risk (0-20 points)
            if transaction.get('legal_flag'):
                transaction_risk += 20
        
        return {
            "relationship_score": min(100, relationship_score),
            "transaction_risk_score": min(100, transaction_risk),
            "customer_value_tier": self._get_customer_tier(relationship_score),
            "risk_level": self._get_priority_level(transaction_risk)
        }
    
    def evaluate_hitl_approval(
        self,
        action_type: str,
        transaction: Dict[str, Any],
        customer: Dict[str, Any],
        message_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate whether action requires HITL approval."""
        
        scores = self.calculate_customer_scores(customer, transaction)
        
        # Approval logic
        requires_approval = False
        approval_reason = []
        
        # Legal actions always require approval
        if action_type == "legal_notice":
            requires_approval = True
            approval_reason.append("Legal action requires human oversight")
        
        # High-value transactions
        if transaction.get('amount', 0) > self._high_value_threshold:
            requires_approval = True
            approval_reason.append(f"Transaction exceeds threshold (₹{self._high_value_threshold:,.0f})")
        
        # High-value customers
        if scores['relationship_score'] >= 70:
            requires_approval = True
            approval_reason.append("High-value customer relationship at stake")
        
        # Formal notices to good customers
        if action_type == "formal_notice" and scores['relationship_score'] >= 50:
            requires_approval = True
            approval_reason.append("Formal notice to established customer")
        
        return {
            "requires_approval": requires_approval,
            "approval_reasons": approval_reason,
            "auto_approve": not requires_approval,
            "relationship_score": scores['relationship_score'],
            "transaction_risk": scores['transaction_risk_score'],
            "recommendation": "proceed" if not requires_approval else "seek_approval",
            "agent": self.name
        }
    
    def _requires_hitl_approval(
        self,
        recommendation: str,
        amount: float,
        relationship_score: float
    ) -> bool:
        """Determine if recommendation requires HITL."""
        
        if recommendation == "aggressive_recovery":
            return True
        
        if amount > self._high_value_threshold:
            return True
        
        if relationship_score >= 70:
            return True
        
        return False
    
    def _get_customer_tier(self, relationship_score: float) -> str:
        """Categorize customer based on relationship score."""
        if relationship_score >= 70:
            return "platinum"
        elif relationship_score >= 50:
            return "gold"
        elif relationship_score >= 30:
            return "silver"
        else:
            return "bronze"
    
    def _get_priority_level(self, risk_score: float) -> str:
        """Categorize priority based on risk score."""
        if risk_score >= 70:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 30:
            return "medium"
        else:
            return "low"
    
    # ========================================================================
    # AI-Powered Methods
    # ========================================================================
    
    async def evaluate_ai_strategy(
        self,
        transaction: Dict[str, Any],
        customer: Dict[str, Any],
        compliance_status: Dict[str, Any],
        communication_history: List[Dict[str, Any]] = []
    ) -> Dict[str, Any]:
        """
        AI-powered strategic evaluation for recovery vs relationship balance.
        Falls back to rule-based evaluation if AI unavailable.
        """
        if not self._ai_enabled or not self._ai_client:
            # Fallback to rule-based strategy
            return self.evaluate_recovery_strategy(
                transaction, customer, compliance_status, communication_history
            )
        
        # Calculate scores for context
        scores = self.calculate_customer_scores(customer, transaction)
        relationship_score = scores['relationship_score']
        transaction_risk = scores['transaction_risk_score']
        
        # Construct prompt
        prompt = f"""As a business relationship arbitrator, analyze this MSME payment recovery scenario:

Customer Profile:
- Name: {customer.get('name', 'Unknown')}
- Total Business Value: ₹{customer.get('total_value', 0):,.0f}
- Transaction Count: {customer.get('total_transactions', 0)}
- Average Payment Delay: {customer.get('avg_payment_delay_days', 0)} days
- Relationship Score: {relationship_score}/100
- Customer Tier: {scores.get('customer_value_tier')}

Current Situation:
- Invoice Amount: ₹{transaction.get('amount', 0):,.0f}
- Days Overdue: {compliance_status.get('days_overdue', 0)}
- Interest Accrued: ₹{compliance_status.get('interest_amount', 0):,.0f}
- Legal Flag: {compliance_status.get('legal_flag', False)}
- Transaction Risk Score: {transaction_risk}/100

Communication History:
- Previous Messages: {len(communication_history)}

Provide strategic recommendation:
1. Strategy (grant_grace_period/diplomatic_escalation/aggressive_recovery/standard_process)
2. Detailed reasoning (2-3 sentences)
3. Specific action steps
4. Risk assessment for chosen strategy
5. Relationship preservation tactics"""

        system_prompt = "You are an expert business arbitrator specializing in MSME payment recovery. Balance aggressive recovery with long-term relationship preservation. Consider Indian business culture and MSMED Act compliance."
        
        # Call AI
        result = await self._ai_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=500,
            temperature=0.6
        )
        
        if result['status'] == 'success':
            # Determine HITL requirement based on scores
            requires_hitl = self._requires_hitl_approval(
                "ai_recommendation",
                transaction.get('amount', 0),
                relationship_score
            )
            
            return {
                "status": "success",
                "ai_recommendation": result['text'],
                "relationship_score": relationship_score,
                "transaction_risk_score": transaction_risk,
                "requires_hitl_approval": requires_hitl,
                "customer_tier": scores.get('customer_value_tier'),
                "risk_level": scores.get('risk_level'),
                "model": result.get('model'),
                "agent": self.name
            }
        else:
            # Fallback to rule-based on AI failure
            print(f"⚠️ AI strategy evaluation failed: {result.get('error')}. Using rule-based logic.")
            return self.evaluate_recovery_strategy(
                transaction, customer, compliance_status, communication_history
            )
