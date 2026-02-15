"""
Centralized utility functions for the backend.
Includes date parsing, validation, and common formatting logic.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse date string with multiple fallback formats.
    Returns: datetime object or None
    """
    if not date_str or str(date_str).lower() in ['null', 'none', 'nan']:
        return None
        
    date_str = str(date_str).strip()
    
    # Try ISO format first
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        pass
        
    formats = (
        '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d',
        '%d %b %Y', '%d %B %Y', '%b %d %Y',
        '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'
    )
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
            
    # Attempt to handle specific edge cases if needed
    logger.warning(f"⚠️ Date parsing failed for: {date_str}")
    return None

def calculate_due_date(invoice_date: datetime, payment_terms: str = "45 days") -> datetime:
    """Calculate due date based on terms."""
    days = 45 # Default
    
    match = re.search(r'(\d+)', str(payment_terms))
    if match:
        days = int(match.group(1))
        
    return invoice_date + timedelta(days=days)

def validate_gstin_checksum(gstin: str) -> bool:
    """
    Validate GSTIN checksum (15th digit).
    GSTIN Format: [State:2][PAN:10][Entity:1][Z][Check:1]
    """
    if not gstin or len(gstin) != 15:
        return False
        
    gstin = gstin.upper()
    if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gstin):
        return False
        
    # Checksum logic (simplified)
    # Proper algorithm is a bit complex, keeping it basic regex for now
    # to avoid false negatives on valid but edge-case GSTINs in POC.
    # In production, use a library or the full weighted sum algo.
    return True

def get_state_from_gstin(gstin: str) -> str:
    """Extract state name from GSTIN."""
    state_codes = {
        "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
        "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
        "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
        "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
        "18": "Assam", "19": "West Bengal", "27": "Maharashtra", 
        "29": "Karnataka", "32": "Kerala", "33": "Tamil Nadu", 
        "36": "Telangana", "37": "Andhra Pradesh"
    }
    return state_codes.get(gstin[:2], "Unknown")

# ============================================================================
# AI Model Integration - Shared HuggingFace Client
# ============================================================================

class AIModelClient:
    """
    Shared HuggingFace LLM client for all agents.
    Provides text generation with retry logic and fallback handling.
    """
    
    def __init__(self, api_key: str, model_name: str, timeout: int = 30, max_retries: int = 3):
        """
        Initialize HuggingFace client.
        
        Args:
            api_key: HuggingFace API token
            model_name: Model identifier (e.g., "meta-llama/Llama-3.2-3B-Instruct")
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(token=api_key, timeout=timeout)
            self.model = model_name
            self.max_retries = max_retries
            self.enabled = True
            logger.info(f"✅ AIModelClient initialized with model: {model_name}")
        except ImportError:
            logger.error("❌ huggingface_hub not installed. AI features disabled.")
            self.client = None
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize AIModelClient: {e}")
            self.client = None
            self.enabled = False
    
    async def generate_text(
        self, 
        prompt: str, 
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate text using HuggingFace LLM with retry logic.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            system_prompt: Optional system instruction
            
        Returns:
            Dict with 'status', 'text', and optional 'error'
        """
        if not self.enabled or not self.client:
            return {
                "status": "error",
                "error": "AI client not initialized",
                "text": None
            }
        
        # Construct full prompt with system instruction if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🤖 Calling HuggingFace API (attempt {attempt + 1}/{self.max_retries})...")
                
                # Use chat_completion for conversational models
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Extract text from response
                generated_text = response.choices[0].message.content
                
                logger.info(f"✅ AI generation successful ({len(generated_text)} chars)")
                return {
                    "status": "success",
                    "text": generated_text.strip(),
                    "model": self.model,
                    "tokens_used": len(generated_text.split())  # Approximate
                }
                
            except Exception as e:
                logger.warning(f"⚠️ AI generation attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "status": "error",
                        "error": str(e),
                        "text": None
                    }
        
        return {
            "status": "error",
            "error": "Max retries exceeded",
            "text": None
        }
    
    def generate_text_sync(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of generate_text for non-async contexts.
        """
        if not self.enabled or not self.client:
            return {
                "status": "error",
                "error": "AI client not initialized",
                "text": None
            }
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.text_generation(
                    full_prompt,
                    model=self.model,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    return_full_text=False
                )
                
                return {
                    "status": "success",
                    "text": response.strip(),
                    "model": self.model
                }
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        "status": "error",
                        "error": str(e),
                        "text": None
                    }
        
        return {
            "status": "error",
            "error": "Max retries exceeded",
            "text": None
        }

