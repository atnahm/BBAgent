"""Janitor Agent - Multimodal Data Ingestion (Google ADK)."""
from google.adk.agents import BaseAgent
from typing import Dict, Any, Optional
import google.generativeai as genai
from datetime import datetime, timedelta
import re
from PIL import Image
from pathlib import Path

class JanitorAgent(BaseAgent):
    """
    ADK-powered Janitor Agent for invoice extraction.
    Handles image OCR, voice transcription, and GSTIN validation.
    """
    
    def __init__(
        self,
        huggingface_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize Janitor Agent with HuggingFace OCR only."""
        super().__init__(
            name="JanitorAgent",
            description="Extracts structured data from invoices using Vision OCR"
        )
        object.__setattr__(self, '_model_name', "huggingface-vision")
        object.__setattr__(self, '_model', None)
        
        # Initialize HuggingFace Vision OCR (ONLY provider)
        if huggingface_config and huggingface_config.get('api_key'):
            from huggingface_hub import InferenceClient
            api_key = huggingface_config.get('api_key')
            model_name = huggingface_config.get('model', 'Qwen/Qwen2.5-VL-7B-Instruct')
            
            object.__setattr__(self, '_hf_api_key', api_key)
            object.__setattr__(self, '_hf_model_name', model_name)
            
            try:
                object.__setattr__(self, '_hf_client', InferenceClient(
                    model=model_name,
                    token=api_key
                ))
                print(f"✅ HuggingFace Vision OCR initialized: {model_name}")
            except Exception as e:
                print(f"❌ Failed to initialize HuggingFace: {e}")
                object.__setattr__(self, '_hf_client', None)
        else:
            print("⚠️ HuggingFace not configured. OCR will not work.")
            object.__setattr__(self, '_hf_client', None)
    
    async def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute agent task asynchronously.
        Supported tasks: extract_invoice, process_voice
        """
        if task == "extract_invoice":
            return await self.process_invoice_image(
                context.get('image_path'),
                provider=context.get('provider')
            )
        elif task == "process_voice":
            return await self.process_voice_note(context.get('audio_path'))
        elif task == "validate_gstin":
            return self.validate_gstin(
                context.get('gstin'),
                context.get('mock_mode', True)
            )
        else:
            return {"error": f"Unknown task: {task}"}
    
    async def process_invoice_image(self, image_path: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """Extract invoice data from image using HuggingFace Vision OCR."""
        if not self._hf_client:
            return {
                "status": "error",
                "error": "HuggingFace Vision OCR not configured. Please set HUGGINGFACE_API_KEY in .env"
            }
        
        result = await self._process_with_huggingface(image_path)
        return self._post_process_result(result)
    
    def _post_process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process and validate extraction result."""
        if result.get('status') == 'success' and result.get('data'):
            try:
                result['data'] = self._validate_extracted_data(result['data'])
            except Exception as e:
                print(f"Validation warning: {e}")
        return result
    
    async def _process_with_gemini(self, image_path: str) -> Dict[str, Any]:
        """Extract invoice data using Gemini Vision."""
        try:
            import google.generativeai as genai
            
            # Upload image
            uploaded_file = genai.upload_file(image_path)
            
            # Prompt for structured extraction
            prompt = """Extract the following information from this Indian invoice/bill image:

1. Vendor Name
2. GSTIN (15-character tax ID)
3. Total Amount (in ₹)
4. Invoice Number
5. Invoice Date (DD/MM/YYYY or any format)
6. Due Date (if mentioned, otherwise calculate 45 days from invoice date)

Return ONLY a JSON object with these exact keys:
{
  "vendor_name": "...",
  "gstin": "...",
  "amount": 0.0,
  "invoice_number": "...",
  "invoice_date": "DD/MM/YYYY",
  "due_date": "DD/MM/YYYY"
}

If any field is not found, use null. Be precise with numbers."""

            # Generate response
            response = self._gemini_model.generate_content([uploaded_file, prompt])
            
            # Parse JSON (clean response)
            import json
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            return {
                "status": "success",
                "data": data,
                "raw_text": response.text,
                "agent": self.name,
                "provider": "gemini"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "provider": "gemini"
            }
    
    async def _process_with_huggingface(self, image_path: str) -> Dict[str, Any]:
        """Extract invoice data using HuggingFace VLM (Qwen2.5-VL)."""
        # Explicitly block PDFs to prevent server 500 errors
        if str(image_path).lower().endswith('.pdf'):
            return {
                "status": "error",
                "error": "PDFs currently require Gemini mode. Please upload an image (JPG/PNG) for HuggingFace."
            }

        try:
            import base64
            import json
            from PIL import Image
            import io
            
            # Load image with PIL to ensure proper format
            img = Image.open(image_path)
            
            # Convert to RGB (standardize channels)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 1024px dimension) to ensure API stability
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to bytes buffer as standard JPEG
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=95)
            buffer.seek(0)
            
            # Encode to base64 (ensure single line)
            image_data = base64.b64encode(buffer.read()).decode('utf-8').replace('\n', '')
            
            # Prompt for structured extraction (same as Gemini)
            prompt = """Extract the following information from this Indian invoice/bill image:

1. Vendor Name
2. GSTIN (15-character tax ID)
3. Total Amount (in ₹)
4. Invoice Number
5. Invoice Date (DD/MM/YYYY or any format)
6. Due Date (if mentioned, otherwise calculate 45 days from invoice date)

Return ONLY a JSON object with these exact keys:
{
  "vendor_name": "...",
  "gstin": "...",
  "amount": 0.0,
  "invoice_number": "...",
  "invoice_date": "DD/MM/YYYY",
  "due_date": "DD/MM/YYYY"
}

If any field is not found, use null. Be precise with numbers."""

            # Call HuggingFace Inference API
            response = self._hf_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url", 
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }],
                max_tokens=2048
            )
            
            # Parse response
            text = response.choices[0].message.content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            return {
                "status": "success",
                "data": data,
                "raw_text": text,
                "agent": self.name,
                "provider": "huggingface",
                "model": self._hf_model_name
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name,
                "provider": "huggingface"
            }
    
    async def process_voice_note(self, audio_path: str) -> Dict[str, Any]:
        """Extract invoice details from voice note (Hinglish)."""
        try:
            # Upload audio file
            audio_file = genai.upload_file(audio_path)
            
            prompt = """You are listening to a voice note from an Indian MSME owner about a transaction.

The person might be speaking in Hinglish (mix of Hindi and English). Extract:
{
  "vendor_name": "Name of vendor/party",
  "amount": "Amount mentioned (as number)",
  "transaction_date": "Date mentioned in YYYY-MM-DD format (if not mentioned, use null)",
  "payment_due_date": "Due date if mentioned (YYYY-MM-DD)",
  "description": "Brief description of the transaction",
  "context": "Any additional context like payment promises, relationship notes",
  "confidence": 0.0-1.0
}

IMPORTANT:
- Handle code-mixed Hindi-English speech
- Extract numbers from Indian number system (lakh, crore)
- Parse dates in various formats (e.g., "kal", "next week", "15 tarikh ko")
- Capture relationship context (e.g., "old customer", "promised to pay after harvest")
"""
            
            if not self._gemini_model:
                return {"status": "error", "error": "Gemini not configured for voice processing"}
                
            response = self._gemini_model.generate_content([prompt, audio_file])
            
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                import json
                extracted_data = json.loads(json_match.group())
                extracted_data['source_type'] = 'voice'
                extracted_data['raw_data_path'] = str(audio_path)
                extracted_data['agent'] = self.name
                
                # Run validation/normalization
                try:
                    extracted_data = self._validate_extracted_data(extracted_data)
                except Exception as e:
                    print(f"Voice validation warning: {e}")

                return {
                    "status": "success",
                    "data": extracted_data
                }
            else:
                return {
                    "status": "error",
                    "error": "Failed to extract data from voice note"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    
    def validate_gstin(self, gstin: Optional[str], mock_mode: bool = True) -> Dict[str, Any]:
        """Validate GSTIN format and optionally check with API."""
        from utils import validate_gstin_checksum, get_state_from_gstin
        
        if not gstin:
            return {"valid": False, "reason": "GSTIN not provided"}
        
        # Basic validation + Checksum
        if not validate_gstin_checksum(gstin):
             return {"valid": False, "reason": "Invalid GSTIN format or checksum"}
        
        if mock_mode:
            # Mock validation for POC
            return {
                "valid": True,
                "gstin": gstin,
                "business_name": f"Mock Business for {gstin[:2]}",
                "state": get_state_from_gstin(gstin),
                "status": "Active",
                "mock": True,
                "agent": self.name
            }
        else:
            # Real GSTIN API Integration (Generic Structure)
            try:
                import requests
                # Using a generic placeholder structure. 
                # User should replace this with their specific GSTIN provider (e.g., Masters India, ClearTax, etc.)
                
                # Check for API key in config/env
                # For now, we'll assume a generic header-based auth
                gst_api_key = os.getenv('GST_API_KEY')
                if not gst_api_key:
                     return {
                        "valid": False, 
                        "reason": "GST_API_KEY not configured",
                        "mock": False
                    }

                # Example Endpoint (Replace with actual provider)
                url = f"https://api.gst-provider.com/v1/taxpayer/{gstin}"
                headers = {"Authorization": f"Bearer {gst_api_key}"}
                
                # Uncomment to activate when provider is selected
                # response = requests.get(url, headers=headers)
                # if response.status_code == 200:
                #     data = response.json()
                #     return {
                #         "valid": True,
                #         "gstin": gstin,
                #         "business_name": data.get('legal_name'),
                #         "status": data.get('status'),
                #         "mock": False
                #     }
                
                # Fallback for now since no provider is actually selected
                return {
                    "valid": True, 
                    "gstin": gstin, 
                    "mock": False, 
                    "note": "Real API configured but endpoint commented out (Select Provider)"
                }
                    
            except Exception as e:
                return {
                    "valid": False, 
                    "reason": f"API Error: {str(e)}",
                    "mock": False
                }
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate extracted data."""
        from utils import parse_date
        
        if data.get('invoice_date'):
            invoice_date = parse_date(data['invoice_date'])
            
            if invoice_date and data.get('payment_terms'):
                # Extract days from payment terms
                days_match = re.search(r'(\d+)\s*days?', data['payment_terms'].lower())
                if days_match:
                    days = int(days_match.group(1))
                    data['due_date'] = (invoice_date + timedelta(days=days)).strftime('%Y-%m-%d')
                else:
                    # Default to 45 days as per MSMED Act
                    data['due_date'] = (invoice_date + timedelta(days=45)).strftime('%Y-%m-%d')
            
            # Normalize invoice_date format if needed
            if invoice_date:
                data['invoice_date'] = invoice_date.strftime('%Y-%m-%d')
        
        # Clean GSTIN
        if data.get('gstin'):
            data['gstin'] = data['gstin'].upper().replace(' ', '')
        
        return data

    def _get_state_from_gstin(self, gstin: str) -> str:
        """Deprecated: Use utils.get_state_from_gstin instead."""
        from utils import get_state_from_gstin
        return get_state_from_gstin(gstin)

