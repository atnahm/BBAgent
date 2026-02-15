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
                payment_date=context.get('payment_date')
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
        else:
            return {"error": f"Unknown task: {task}"}
    
    def check_transaction_status(
        self,
        invoice_date: str,
        due_date: str,
        amount: float,
        payment_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check compliance status of a transaction."""
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
        
        # Calculate interest (MSMED Act Section 16)
        interest_amount = 0.0
        if days_overdue > 0:
            annual_interest_rate = self._interest_multiplier * self._bank_rate_percent
            interest_amount = amount * (annual_interest_rate / 100) * (days_overdue / 365)
        
        # Check Section 43B(h) compliance
        section_43b_h_violation = False
        tax_disallowance_risk = False
        
        if self._section_43b_h_enabled and days_overdue > self._payment_limit_days:
            section_43b_h_violation = True
            tax_disallowance_risk = True
        
        # Determine alert level
        alert_level = self._get_alert_level(days_overdue, due_dt, today)
        
        return {
            "status": status,
            "days_overdue": days_overdue,
            "interest_amount": round(interest_amount, 2),
            "interest_rate_annual": self._interest_multiplier * self._bank_rate_percent,
            "section_43b_h_violation": section_43b_h_violation,
            "tax_disallowance_risk": tax_disallowance_risk,
            "alert_level": alert_level,
            "days_until_due": (due_dt - today).days if payment_dt is None else 0,
            "legal_flag": days_overdue > self._payment_limit_days,
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
        
        alerts = {
            "warning": {
                "severity": "low",
                "title": "Payment Due Soon",
                "message": f"Payment of ₹{transaction['amount']:,.2f} to {transaction['vendor_name']} is due in {compliance_status['days_until_due']} days.",
                "action": "Send friendly reminder"
            },
            "critical": {
                "severity": "medium",
                "title": "Payment Overdue - MSMED Act Violation",
                "message": f"Payment of ₹{transaction['amount']:,.2f} is {compliance_status['days_overdue']} days overdue. Interest accrued: ₹{compliance_status['interest_amount']:,.2f}",
                "action": "Send formal notice"
            },
            "severe": {
                "severity": "high",
                "title": "Section 43B(h) Tax Disallowance Risk",
                "message": f"Payment overdue by {compliance_status['days_overdue']} days. Buyer risks tax deduction disallowance. Interest: ₹{compliance_status['interest_amount']:,.2f}",
                "action": "Send legal notice (requires HITL approval)"
            }
        }
        
        alert = alerts.get(alert_level)
        if alert:
            alert['transaction_id'] = transaction.get('id')
            alert['compliance_status'] = compliance_status
            alert['agent'] = self.name
            
        return alert
    
    def _get_alert_level(self, days_overdue: int, due_date: datetime, today: datetime) -> str:
        """Determine alert severity level."""
        days_until_due = (due_date - today).days
        
        if days_until_due > 0 and days_until_due <= 7:
            return "warning"
        
        if days_overdue > 0 and days_overdue <= self._payment_limit_days:
            return "critical"
        elif days_overdue > self._payment_limit_days:
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
