"""Collector Agent - Recovery Communication (Google ADK)."""
from google.adk.agents import BaseAgent
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime
from backend.config_loader import CONFIG

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
        
        # Store configuration as private attributes
        object.__setattr__(self, '_mock_mode', CONFIG['whatsapp']['mock_mode'])
        object.__setattr__(self, '_whatsapp_config', CONFIG['whatsapp'])
        
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
        
        # Initialize AI client for message generation
        try:
            from backend.utils import AIModelClient
            
            hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
            ai_config = CONFIG.get('ai_models', {}).get('huggingface', {})
            collector_model = ai_config.get('models', {}).get('collector_llm', 'meta-llama/Llama-3.2-3B-Instruct')
            
            if hf_api_key and hf_api_key != 'your_huggingface_api_key_here':
                object.__setattr__(self, '_ai_client', AIModelClient(
                    api_key=hf_api_key,
                    model_name=collector_model,
                    timeout=ai_config.get('timeout', 30),
                    max_retries=ai_config.get('max_retries', 3)
                ))
                object.__setattr__(self, '_ai_enabled', True)
                print(f"✅ CollectorAgent AI enabled with {collector_model}")
            else:
                object.__setattr__(self, '_ai_client', None)
                object.__setattr__(self, '_ai_enabled', False)
                print("⚠️ CollectorAgent AI disabled (no API key)")
        except Exception as e:
            print(f"⚠️ Failed to initialize AI for CollectorAgent: {e}")
            object.__setattr__(self, '_ai_client', None)
            object.__setattr__(self, '_ai_enabled', False)
    
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
        elif task == "generate_ai_message":
            # NEW: AI-powered message generation
            return await self.generate_ai_message(
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
            # Real WhatsApp Business API Integration
            try:
                import requests
                
                api_key = self._whatsapp_config['api_key']
                phone_id = self._whatsapp_config['phone_number_id']
                
                if not api_key or not phone_id or "Variable not set" in api_key:
                    return {
                        "status": "error",
                        "error": "WhatsApp API credentials not configured in .env"
                    }
                
                url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "text",
                    "text": {"body": message}
                }
                
                response = requests.post(url, headers=headers, json=payload)
                response_data = response.json()
                
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "delivery_status": "sent",
                        "phone_number": phone_number,
                        "message_id": response_data.get('messages', [{}])[0].get('id'),
                        "sent_at": datetime.utcnow().isoformat(),
                        "agent": self.name
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"WhatsApp API Error: {response.text}",
                        "agent": self.name
                    }
                    
            except ImportError:
                return {
                    "status": "error",
                    "error": "requests library not installed",
                    "agent": self.name
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "agent": self.name
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
    
    # ========================================================================
    # AI-Powered Methods
    # ========================================================================
    
    async def generate_ai_message(
        self,
        tier: str,
        transaction: Dict[str, Any],
        compliance_status: Dict[str, Any],
        customer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized WhatsApp message using AI.
        Falls back to template-based generation if AI unavailable.
        """
        if not self._ai_enabled or not self._ai_client:
            # Fallback to template-based generation
            return self.generate_message(tier, transaction, compliance_status, customer)
        
        vendor_name = transaction.get('vendor_name', 'Customer')
        amount = transaction.get('amount', 0)
        invoice_num = transaction.get('invoice_number', 'N/A')
        days_overdue = compliance_status.get('days_overdue', 0)
        days_until_due = compliance_status.get('days_until_due', 0)
        interest_amount = compliance_status.get('interest_amount', 0)
        relationship_score = customer.get('relationship_score', 50)
        
        # Determine tone and requirements based on tier
        if tier == "friendly_reminder":
            tone = "friendly and respectful"
            requirements = "Use Hindi-English mix (Hinglish), keep it warm and casual, under 200 characters"
            requires_hitl = False
        elif tier == "formal_notice":
            tone = "professional and firm"
            requirements = "Professional English, mention MSMED Act, include interest calculation, under 300 characters"
            requires_hitl = True
        elif tier == "legal_notice":
            tone = "formal and authoritative"
            requirements = "Legal English, cite MSMED Act 2006 and Section 43B(h), mention consequences, under 350 characters"
            requires_hitl = True
        else:
            return {"error": f"Invalid tier: {tier}"}
        
        # Construct prompt
        prompt = f"""Generate a WhatsApp payment reminder message:

Context:
- Customer: {vendor_name} (Relationship Score: {relationship_score}/100)
- Invoice: {invoice_num}
- Amount: ₹{amount:,.2f}
- Days Overdue: {days_overdue} (Due in: {days_until_due} days)
- Interest Accrued: ₹{interest_amount:,.2f}
- Message Tier: {tier}

Requirements:
- Tone: {tone}
- {requirements}
- Include emoji where appropriate
- Culturally appropriate for Indian MSME business
- Do NOT include sender signature or company name

Generate ONLY the message text:"""

        system_prompt = "You are an expert in Indian business communication, specializing in payment recovery messages for MSME transactions. Generate culturally appropriate, effective WhatsApp messages."
        
        # Call AI
        result = await self._ai_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=200,
            temperature=0.8
        )
        
        if result['status'] == 'success':
            message_text = result['text'].strip()
            
            return {
                "status": "success",
                "tier": tier,
                "message_text": message_text,
                "requires_hitl_approval": requires_hitl,
                "phone_number": customer.get('phone_number'),
                "transaction_id": transaction.get('id'),
                "generated_at": datetime.utcnow().isoformat(),
                "ai_generated": True,
                "model": result.get('model'),
                "agent": self.name
            }
        else:
            # Fallback to template on AI failure
            print(f"⚠️ AI message generation failed: {result.get('error')}. Using template.")
            return self.generate_message(tier, transaction, compliance_status, customer)
