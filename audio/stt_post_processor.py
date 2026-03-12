"""
STT Post-Processor using Groq Llama-4 Scout
Corrects common abbreviations and transcription errors
"""

import os
import logging
from typing import Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)


class STTPostProcessor:
    """Post-process STT output to correct common abbreviations and errors"""
    
    def __init__(self):
        self._client = None
        self._correction_rules = self._load_correction_rules()
    
    def _get_client(self) -> Groq:
        """Get Groq client for STT post-processing"""
        if self._client is None:
            api_key = os.getenv("GROQ_STT_Processor")
            if not api_key:
                raise Exception("GROQ_STT_Processor API key not found")
            self._client = Groq(api_key=api_key)
        return self._client
    
    def _load_correction_rules(self) -> Dict[str, str]:
        """Load common correction rules for educational context"""
        return {
            # Department abbreviations
            "PC": "BC", "pc": "bc",
            "MBC": "MBC", "mbc": "MBC", 
            "SC": "SC", "sc": "SC",
            
            # Course codes
            "CIC": "CSE", "cic": "CSE",
            "CCE": "CCE", "cce": "CCE",
            "ECE": "ECE", "ece": "ECE", 
            "EEE": "EEE", "eee": "EEE",
            "MECH": "MECH", "mech": "MECH",
            "CIVIL": "CIVIL", "civil": "CIVIL",
            
            # Institution names
            "St EShwar": "Sri Eshwar", "st eshwar": "Sri Eshwar",
            "St. EShwar": "Sri Eshwar", "st. eshwar": "Sri Eshwar",
            "Sree Eshwar": "Sri Eshwar", "sree eshwar": "Sri Eshwar",
            
            # Common hostel/college terms
            "mess hall": "mess", "dining hall": "mess",
            "dormitory": "hostel", "dorm": "hostel",
            "canteen": "cafeteria",
            "principal sir": "principal", "principal madam": "principal",
            
            # Academic terms
            "semester exam": "semester examination",
            "internal exam": "internal assessment",
            "lab exam": "laboratory examination",
            "viva voce": "viva",
            
            # Time corrections
            "7 AM": "7:00 AM", "8 AM": "8:00 AM", "9 AM": "9:00 AM",
            "7 PM": "7:00 PM", "8 PM": "8:00 PM", "9 PM": "9:00 PM",
        }
    
    def apply_quick_corrections(self, text: str) -> str:
        """Apply quick rule-based corrections"""
        corrected = text
        
        # Apply correction rules
        for wrong, correct in self._correction_rules.items():
            # Word boundary replacement to avoid partial matches
            import re
            pattern = r'\b' + re.escape(wrong) + r'\b'
            corrected = re.sub(pattern, correct, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    async def process_stt_corrections(self, original_text: str, context: str = "college") -> Dict[str, Any]:
        """
        Use Groq Llama-4 Scout to intelligently correct STT output
        
        Args:
            original_text: Raw STT output
            context: Context hint (college, hostel, academic, etc.)
        
        Returns:
            Corrected text with confidence score
        """
        try:
            # First apply quick rule-based corrections
            quick_corrected = self.apply_quick_corrections(original_text)
            
            # If significant changes were made, use that
            if quick_corrected != original_text:
                logger.info(f"Quick corrections applied: '{original_text}' → '{quick_corrected}'")
                return {
                    "success": True,
                    "original_text": original_text,
                    "corrected_text": quick_corrected,
                    "correction_type": "rule_based",
                    "confidence": 0.95,
                    "corrections_applied": True
                }
            
            # For complex corrections, use Llama-4 Scout
            client = self._get_client()
            
            correction_prompt = f"""You are an STT correction specialist for an Sri Eshwar college context.

TASK: Correct transcription errors in the following text. Focus on:
1. Department abbreviations (PC→BC/MBC/SC, CIC→CSE/CCE , CSC -> CSE) Don't Abbreviate any acronyms
2. If anything sounds like "stee" or "sree", correct it to "Sri Eshwar"
3. Course codes and academic terms
4. Common college/hostel vocabulary
5. Only allowed courses are CSE,CCE,AIDS,MECH,ECE,EEE,AIML if any abbreviation appears somehow related,map to corresponding

CONTEXT: {context}
ORIGINAL TEXT: "{original_text}"

RULES:
- Only correct obvious transcription errors
- Preserve the original meaning and intent
- Use proper Indian English conventions
- Keep informal conversational tone

Return ONLY the corrected text, no explanations."""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Fastest Llama model for quick STT corrections
                messages=[{"role": "user", "content": correction_prompt}],
                temperature=0.1,  # Low temperature for consistent corrections
                max_tokens=150,   # Reduced for faster response
                top_p=0.9
            )
            
            corrected_text = response.choices[0].message.content.strip()
            
            # Remove quotes if Llama added them
            if corrected_text.startswith('"') and corrected_text.endswith('"'):
                corrected_text = corrected_text[1:-1]
            
            # Calculate confidence based on similarity
            corrections_made = corrected_text != original_text
            confidence = 0.90 if corrections_made else 0.95
            
            logger.info(f"Llama STT correction: '{original_text}' → '{corrected_text}'")
            
            return {
                "success": True,
                "original_text": original_text,
                "corrected_text": corrected_text,
                "correction_type": "llama_smart",
                "confidence": confidence,
                "corrections_applied": corrections_made
            }
            
        except Exception as e:
            logger.error(f"STT post-processing failed: {e}")
            return {
                "success": False,
                "original_text": original_text,
                "corrected_text": original_text,  # Fallback to original
                "correction_type": "none",
                "confidence": 0.85,
                "corrections_applied": False,
                "error": str(e)
            }
    
    def get_correction_examples(self) -> Dict[str, str]:
        """Get examples of corrections for testing"""
        return {
            "I'm in PC category": "I'm in BC category",
            "CIC department is good": "CSE department is good", 
            "St EShwar college hostel": "Sri Eshwar college hostel",
            "mess timing is 7 AM to 9 PM": "mess timing is 7:00 AM to 9:00 PM",
            "internal exam next week": "internal assessment next week"
        }


# Global instance
_stt_post_processor = None

def get_stt_post_processor() -> STTPostProcessor:
    """Get global STT post-processor instance"""
    global _stt_post_processor
    if _stt_post_processor is None:
        _stt_post_processor = STTPostProcessor()
    return _stt_post_processor