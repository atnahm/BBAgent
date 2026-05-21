"""Compliance Agent - MSMED Act Monitoring (Google ADK)."""
from google.adk.agents import BaseAgent
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class ComplianceAgent(BaseAgent):
    """
    ADK-powered Compliance Agent for MSMED Act monitoring.
    Calculates interest and generates compliance alerts.
    """
    
    def __init__(
        self,
        payment_limit_days: int = 45,
        interest_multiplier: float = 3.0,
        bank_rate_percent: float = 8.0,
        section_43b_h: bool = True
    ):
        """Initialize Compliance Agent with ADK BaseAgent."""
        super().__init__(
            name="ComplianceAgent",
            description="MSMED Act compliance monitoring specialist"
        )
        
        # Store configuration as private attributes to avoid Pydantic validation
        object.__setattr__(self, '_payment_limit_days', payment_limit_days)
        object.__setattr__(self, '_interest_multiplier', interest_multiplier)
        object.__setattr__(self, '_bank_rate_percent', bank_rate_percent)
        object.__setattr__(self, '_section_43b_h_enabled', section_43b_h)
        
        # Initialize AI client for risk analysis
        try:
            import os
            from backend.utils import AIModelClient
            from backend.config_loader import CONFIG
            
            api_key = os.getenv('HUGGINGFACE_API_KEY')
            ai_config = CONFIG.get('ai_models', {}).get('huggingface', {})
            model_name = ai_config.get('models', {}).get('compliance_llm', 'meta-llama/Llama-3.2-3B-Instruct')
            
            if api_key and api_key != 'your_huggingface_api_key_here':
                object.__setattr__(self, '_ai_client', AIModelClient(
                    api_key=api_key,
                    model_name=model_name,
                    timeout=ai_config.get('timeout', 30),
                    max_retries=ai_config.get('max_retries', 3)
                ))
                object.__setattr__(self, '_ai_enabled', True)
                print(f"✅ ComplianceAgent AI enabled with {model_name}")
            else:
                object.__setattr__(self, '_ai_client', None)
                object.__setattr__(self, '_ai_enabled', False)
                print("⚠️ ComplianceAgent AI disabled (no API key)")
        except Exception as e:
            print(f"⚠️ Failed to initialize AI for ComplianceAgent: {e}")
            object.__setattr__(self, '_ai_client', None)
            object.__setattr__(self, '_ai_enabled', False)
    
    async def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ADK-standard run method for compliance checks.
        
        Args:
            task: Compliance task type
            context: Transaction details
        
        Returns:
            Compliance status and recommendations
        """
        if task == "check_transaction":
            return self.check_transaction_status(
                invoice_date=context['invoice_date'],
                due_date=context['due_date'],
                amount=context['amount'],
                payment_date=context.get('payment_date'),
                country_code=context.get('country_code', 'US')
            )
        elif task == "generate_alert":
            return self.generate_compliance_alert(
                transaction=context['transaction'],
                compliance_status=context['compliance_status']
            )
        elif task == "annual_summary":
            return self.calculate_financial_year_compliance(
                transactions=context['transactions']
            )
        elif task == "analyze_risk":
            # NEW: AI-powered risk analysis
            return await self.analyze_compliance_risk(
                transaction=context['transaction'],
                customer_history=context.get('customer_history', {})
            )
        elif task == "generate_summary":
            # NEW: AI-generated compliance summary
            return await self.generate_compliance_summary(
                compliance_status=context['compliance_status'],
                transaction=context['transaction']
            )
        else:
            return {"error": f"Unknown task: {task}"}
    
    def check_transaction_status(
        self,
        invoice_date: str,
        due_date: str,
        amount: float,
        payment_date: Optional[str] = None,
        country_code: str = 'US'
    ) -> Dict[str, Any]:
        """Check compliance status of a transaction based on generalized country rules."""
        def parse_date(date_str):
            if not date_str: return None
            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    pass
            # Last ditch attempt: return None or raise
            raise ValueError(f"Unknown date format: {date_str}")

        invoice_dt = parse_date(invoice_date)
        due_dt = parse_date(due_date)
        payment_dt = parse_date(payment_date)
        
        today = datetime.utcnow()
        
        # Calculate days overdue
        if payment_dt:
            days_overdue = max(0, (payment_dt - due_dt).days)
            status = "paid_late" if days_overdue > 0 else "paid_on_time"
        else:
            days_overdue = max(0, (today - due_dt).days)
            status = "overdue" if days_overdue > 0 else "pending"
        
        # RAG / generalized logic variables
        interest_amount = 0.0
        legal_flag = False
        interest_rate = 0.0
        
        # Fallback simplistic mock generalized rules for numeric calculation
        if country_code == 'IN':
            limit_days = 45
            interest_rate = 19.5 # 3 * 6.5
        elif country_code == 'UK':
            limit_days = 60
            interest_rate = 8.0
        else: # US / Default
            limit_days = 30
            interest_rate = 18.0

        if days_overdue > 0:
            interest_amount = amount * (interest_rate / 100) * (days_overdue / 365)
        
        if days_overdue > limit_days:
            legal_flag = True
        
        # Determine alert level
        alert_level = self._get_alert_level(days_overdue, due_dt, today, limit_days)
        
        return {
            "status": status,
            "days_overdue": days_overdue,
            "interest_amount": round(interest_amount, 2),
            "interest_rate_annual": interest_rate,
            "alert_level": alert_level,
            "days_until_due": (due_dt - today).days if payment_dt is None else 0,
            "legal_flag": legal_flag,
            "country_code": country_code,
            "agent": self.name
        }
    
    def generate_compliance_alert(
        self,
        transaction: Dict[str, Any],
        compliance_status: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate alert if compliance action needed."""
        alert_level = compliance_status['alert_level']
        
        if alert_level == "none":
            return None
        
        currency = transaction.get('currency', 'USD')

        alerts = {
            "warning": {
                "severity": "low",
                "title": "Payment Due Soon",
                "message": f"Payment of {currency} {transaction['amount']:,.2f} to {transaction['vendor_name']} is due in {compliance_status['days_until_due']} days.",
                "action": "Send friendly reminder"
            },
            "critical": {
                "severity": "medium",
                "title": "Payment Overdue - Compliance Violation",
                "message": f"Payment of {currency} {transaction['amount']:,.2f} is {compliance_status['days_overdue']} days overdue. Interest accrued: {currency} {compliance_status['interest_amount']:,.2f}",
                "action": "Send formal notice"
            },
            "severe": {
                "severity": "high",
                "title": "Severe Legal / Tax Risk",
                "message": f"Payment overdue by {compliance_status['days_overdue']} days. Legal/Tax risks apply. Interest: {currency} {compliance_status['interest_amount']:,.2f}",
                "action": "Send legal notice (requires HITL approval)"
            }
        }
        
        alert = alerts.get(alert_level)
        if alert:
            alert['transaction_id'] = transaction.get('id')
            alert['compliance_status'] = compliance_status
            alert['agent'] = self.name
            
        return alert
    
    def _get_alert_level(self, days_overdue: int, due_date: datetime, today: datetime, limit_days: int) -> str:
        """Determine alert severity level."""
        days_until_due = (due_date - today).days
        
        if days_until_due > 0 and days_until_due <= 7:
            return "warning"
        
        if days_overdue > 0 and days_overdue <= limit_days:
            return "critical"
        elif days_overdue > limit_days:
            return "severe"
        
        return "none"
    
    def calculate_financial_year_compliance(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate compliance summary for financial year."""
        total_transactions = len(transactions)
        overdue_count = 0
        total_interest = 0.0
        section_43b_h_violations = 0
        
        for txn in transactions:
            if txn.get('days_overdue', 0) > 0:
                overdue_count += 1
                total_interest += txn.get('interest_amount', 0.0)
                
                if txn.get('days_overdue', 0) > self._payment_limit_days:
                    section_43b_h_violations += 1
        
        compliance_rate = ((total_transactions - overdue_count) / total_transactions * 100) if total_transactions > 0 else 0
        
        return {
            "total_transactions": total_transactions,
            "on_time_payments": total_transactions - overdue_count,
            "overdue_payments": overdue_count,
            "compliance_rate": round(compliance_rate, 2),
            "total_interest_accrued": round(total_interest, 2),
            "section_43b_h_violations": section_43b_h_violations,
            "tax_risk_transactions": section_43b_h_violations,
            "agent": self.name
        }
    
    # ========================================================================
    # AI-Powered Methods
    # ========================================================================
    
    async def analyze_compliance_risk(
        self,
        transaction: Dict[str, Any],
        customer_history: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        AI-powered risk analysis for compliance scenarios.
        Falls back to rule-based analysis if AI unavailable.
        """
        if not self._ai_enabled or not self._ai_client:
            return {
                "status": "fallback",
                "risk_level": "unknown",
                "message": "AI analysis unavailable, using rule-based logic",
                "agent": self.name
            }
        
        # Prepare context
        customer_history = customer_history or {}
        avg_delay = customer_history.get('avg_payment_delay_days', 0)
        total_txns = customer_history.get('total_transactions', 0)
        
        # Construct prompt
        prompt = f"""Analyze this MSME payment compliance scenario and provide risk assessment:

Transaction Details:
- Vendor: {transaction.get('vendor_name', 'Unknown')}
- Amount: ₹{transaction.get('amount', 0):,.2f}
- Days Overdue: {transaction.get('days_overdue', 0)}
- Interest Accrued: ₹{transaction.get('interest_amount', 0):,.2f}
- Legal Flag: {transaction.get('legal_flag', False)}

Customer Payment History:
- Average Delay: {avg_delay} days
- Total Transactions: {total_txns}

MSMED Act Context:
- Payment limit: {self._payment_limit_days} days
- Interest rate: {self._interest_multiplier * self._bank_rate_percent}% p.a.
- Section 43B(h) applies: {self._section_43b_h_enabled}

Provide a structured analysis with:
1. Risk Level (Low/Medium/High/Critical)
2. Key Risk Factors (2-3 bullet points)
3. Recommended Action
4. Predicted Payment Timeline"""

        system_prompt = "You are an MSME compliance expert analyzing payment risk scenarios under Indian MSMED Act 2006."
        
        # Call AI
        result = await self._ai_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=400,
            temperature=0.5
        )
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "ai_analysis": result['text'],
                "model": result.get('model'),
                "agent": self.name
            }
        else:
            return {
                "status": "error",
                "error": result.get('error'),
                "agent": self.name
            }
    
    async def generate_compliance_summary(
        self,
        compliance_status: Dict[str, Any],
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate human-readable compliance summary using AI.
        """
        if not self._ai_enabled or not self._ai_client:
            # Fallback to simple template
            return {
                "status": "fallback",
                "summary": f"Transaction of ₹{transaction.get('amount', 0):,.2f} is {compliance_status.get('status')}. "
                          f"Days overdue: {compliance_status.get('days_overdue', 0)}. "
                          f"Interest: ₹{compliance_status.get('interest_amount', 0):,.2f}.",
                "agent": self.name
            }
        
        prompt = f"""Generate a concise compliance summary for this MSME payment:

Status: {compliance_status.get('status')}
Amount: ₹{transaction.get('amount', 0):,.2f}
Vendor: {transaction.get('vendor_name')}
Days Overdue: {compliance_status.get('days_overdue', 0)}
Interest Accrued: ₹{compliance_status.get('interest_amount', 0):,.2f}
Alert Level: {compliance_status.get('alert_level')}
Section 43B(h) Violation: {compliance_status.get('section_43b_h_violation', False)}

Create a 2-3 sentence professional summary suitable for management review."""

        result = await self._ai_client.generate_text(
            prompt=prompt,
            max_tokens=150,
            temperature=0.6
        )
        
        if result['status'] == 'success':
            return {
                "status": "success",
                "summary": result['text'],
                "model": result.get('model'),
                "agent": self.name
            }
        else:
            return {
                "status": "error",
                "error": result.get('error'),
                "agent": self.name
            }

