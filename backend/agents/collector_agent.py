"""Collector Agent - Recovery Communication (Google ADK)."""
from google.adk.agents import BaseAgent
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime

class CollectorAgent(BaseAgent):
    """
    ADK-powered Collector Agent for payment recovery.
    Generates tiered WhatsApp messages with HITL approval.
    """
    
    def __init__(self, mock_mode: bool = True, model_name: str = "gemini-1.5-flash"):
        """Initialize Collector Agent with ADK BaseAgent."""
        super().__init__(
            name="CollectorAgent",
            description="Generates recovery messages and manages WhatsApp automation"
        )
        
        # Store configuration as private attributes to avoid Pydantic validation
        object.__setattr__(self, '_mock_mode', mock_mode)
        
        # Only initialize Gemini if we have an API key from environment
        try:
            import os
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                object.__setattr__(self, '_model', genai.GenerativeModel(model_name))
            else:
                object.__setattr__(self, '_model', None)
        except:
            object.__setattr__(self, '_model', None)
    
    async def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ADK-standard run method for recovery operations.
        
        Args:
            task: Recovery task type
            context: Transaction and customer details
        
        Returns:
            Message generation and sending results
        """
        if task == "generate_message":
            return self.generate_message(
                tier=context['tier'],
                transaction=context['transaction'],
                compliance_status=context['compliance_status'],
                customer=context['customer']
            )
        elif task == "send_message":
            return await self.send_whatsapp_message(
                phone_number=context['phone_number'],
                message=context['message'],
                message_id=context.get('message_id')
            )
        elif task == "determine_tier":
            return self.determine_message_tier(
                compliance_status=context['compliance_status'],
                communication_history=context.get('communication_history', [])
            )
        else:
            return {"error": f"Unknown task: {task}"}
    
    def generate_message(
        self,
        tier: str,
        transaction: Dict[str, Any],
        compliance_status: Dict[str, Any],
        customer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate WhatsApp message based on tier."""
        
        vendor_name = transaction.get('vendor_name', 'Customer')
        amount = transaction.get('amount', 0)
        invoice_num = transaction.get('invoice_number', 'N/A')
        
        if tier == "friendly_reminder":
            message_text = f"""🙏 Namaste {vendor_name} ji,

Aapka payment reminder hai:
📄 Invoice: {invoice_num}
💰 Amount: ₹{amount:,.2f}
📅 Due Date: {compliance_status.get('days_until_due', 'N/A')} days me

Dhanyavaad! 🙏"""
            requires_hitl = False
            
        elif tier == "formal_notice":
            message_text = f"""📢 PAYMENT OVERDUE NOTICE

Dear {vendor_name},

Re: Invoice No. {invoice_num}

Payment of ₹{amount:,.2f} is overdue by {compliance_status.get('days_overdue', 0)} days.

As per MSMED Act 2006, interest accrued: ₹{compliance_status.get('interest_amount', 0):,.2f} @ {compliance_status.get('interest_rate_annual', 0)}% p.a.

Kindly clear the outstanding amount at the earliest.

Regards,
Accounts Team"""
            requires_hitl = True
            
        elif tier == "legal_notice":
            message_text = f"""⚠️ LEGAL NOTICE - MSMED ACT 2006 ⚠️

To: {vendor_name}
Invoice: {invoice_num}
Amount Due: ₹{amount:,.2f}

Payment is overdue by {compliance_status.get('days_overdue', 0)} days, violating MSMED Act 2006.

SECTION 43B(h) INCOME TAX WARNING:
Buyer may face TAX DEDUCTION DISALLOWANCE for delayed MSME payments.

Interest Accrued: ₹{compliance_status.get('interest_amount', 0):,.2f}

IMMEDIATE ACTION REQUIRED within 7 days to avoid:
1. Legal proceedings under MSMED Act
2. Reporting to MSME Samadhaan Portal
3. Credit rating impact

Contact immediately: [Contact Details]

This is a system-generated legal notice."""
            requires_hitl = True
            
        else:
            return {"error": f"Invalid tier: {tier}"}
        
        return {
            "status": "success",
            "tier": tier,
            "message_text": message_text,
            "requires_hitl_approval": requires_hitl,
            "phone_number": customer.get('phone_number'),
            "transaction_id": transaction.get('id'),
            "generated_at": datetime.utcnow().isoformat(),
            "agent": self.name
        }
    
    async def send_whatsapp_message(
        self,
        phone_number: str,
        message: str,
        message_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send WhatsApp message (mock or real)."""
        
        if self._mock_mode:
            # Mock sending for POC
            return {
                "status": "success",
                "delivery_status": "sent (mock)",
                "phone_number": phone_number,
                "message_id": message_id,
                "sent_at": datetime.utcnow().isoformat(),
                "mock": True,
                "agent": self.name
            }
        else:
            # TODO: Integrate real WhatsApp Business API
            # For production, use wwebjs or official API
            return {
                "status": "error",
                "error": "Real WhatsApp integration not implemented"
            }
    
    def determine_message_tier(
        self,
        compliance_status: Dict[str, Any],
        communication_history: list = []
    ) -> str:
        """Determine appropriate message tier based on compliance status."""
        
        days_until_due = compliance_status.get('days_until_due', 0)
        days_overdue = compliance_status.get('days_overdue', 0)
        legal_flag = compliance_status.get('legal_flag', False)
        
        # Count previous communications
        reminder_count = len([c for c in communication_history if c.get('message_type') == 'friendly_reminder'])
        formal_count = len([c for c in communication_history if c.get('message_type') == 'formal_notice'])
        
        # Tier logic
        if legal_flag or days_overdue > 45:
            return "legal_notice"
        elif days_overdue > 0 or (days_until_due <= 3 and formal_count > 0):
            return "formal_notice"
        elif days_until_due <= 7:
            return "friendly_reminder"
        else:
            return "none"
    
    def requires_hitl_approval(
        self,
        tier: str,
        transaction_amount: float,
        customer_value: float
    ) -> bool:
        """Determine if message requires HITL approval."""
        
        # Legal notices always require approval
        if tier == "legal_notice":
            return True
        
        # High-value transactions require approval
        if transaction_amount > 50000:
            return True
        
        # Valuable customers require approval
        if customer_value > 500000:
            return True
        
        # Formal notices require approval
        if tier == "formal_notice":
            return True
        
        return False
