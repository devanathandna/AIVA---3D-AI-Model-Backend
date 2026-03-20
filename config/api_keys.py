"""
API Key Manager with circular rotation for multiple providers
"""
import os
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class KeyPool:
    """Pool of API keys for a specific service"""
    service_name: str
    keys: List[str]
    current_index: int = 0
    _lock: threading.Lock = None
    
    def __post_init__(self):
        self._lock = threading.Lock()
        if not self.keys:
            raise ValueError(f"No API keys found for service: {self.service_name}")
    
    def get_next_key(self) -> str:
        """Get next API key using circular rotation (thread-safe)"""
        with self._lock:
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            return key
    
    def get_current_index(self) -> int:
        """Get current rotation index"""
        with self._lock:
            return self.current_index
    
    def reset_rotation(self):
        """Reset rotation to start from first key"""
        with self._lock:
            self.current_index = 0

class APIKeyManager:
    """Manages API keys with circular rotation for multiple services"""
    
    def __init__(self):
        self.key_pools: Dict[str, KeyPool] = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from environment variables"""
        # Load STT keys (Groq)
        stt_keys = self._load_keys_for_service("GROQ_STT", 5)
        if stt_keys:
            self.key_pools["groq_stt"] = KeyPool("groq_stt", stt_keys)
        
        # Load TTS keys (Gemini)
        tts_keys = self._load_keys_for_service("GEMINI_TTS", 5) 
        if tts_keys:
            self.key_pools["gemini_tts"] = KeyPool("gemini_tts", tts_keys)
        
        # Load General AI keys (Gemini)
        ai_keys = self._load_keys_for_service("GEMINI_AI", 5)
        if ai_keys:
            self.key_pools["gemini_ai"] = KeyPool("gemini_ai", ai_keys)
    
    def _load_keys_for_service(self, prefix: str, expected_count: int) -> List[str]:
        """Load keys for a specific service from environment"""
        keys = []
        
        for i in range(1, expected_count + 1):
            key = os.getenv(f"{prefix}_API_KEY_{i}")
            if key and key.strip():
                keys.append(key.strip())
        
        # Fallback to single key if numbered keys not found
        if not keys:
            single_key = os.getenv(f"{prefix}_API_KEY")
            if single_key and single_key.strip():
                keys.append(single_key.strip())
        
        if keys:
            print(f"[API_KEY_MANAGER] Loaded {len(keys)} keys for {prefix}")
        else:
            print(f"[API_KEY_MANAGER] ⚠️  No keys found for {prefix}")
        
        return keys
    
    def get_key(self, service: str) -> Optional[str]:
        """Get next API key for specified service"""
        if service not in self.key_pools:
            print(f"[API_KEY_MANAGER] ❌ Service '{service}' not found")
            return None
        
        key = self.key_pools[service].get_next_key()
        current_idx = self.key_pools[service].get_current_index()
        total_keys = len(self.key_pools[service].keys)
        
        print(f"[API_KEY_MANAGER] 🔑 Using {service} key {current_idx}/{total_keys}")
        return key
    
    def get_groq_stt_key(self) -> Optional[str]:
        """Get Groq STT API key"""
        return self.get_key("groq_stt")
    
    def get_gemini_tts_key(self) -> Optional[str]:
        """Get Gemini TTS API key"""
        return self.get_key("gemini_tts")
    
    def get_gemini_ai_key(self) -> Optional[str]:
        """Get Gemini AI API key"""
        return self.get_key("gemini_ai")
    
    def get_service_status(self) -> Dict[str, Dict]:
        """Get status of all key pools"""
        status = {}
        for service, pool in self.key_pools.items():
            status[service] = {
                "total_keys": len(pool.keys),
                "current_index": pool.get_current_index(),
                "next_key_suffix": pool.keys[pool.get_current_index()][-4:] if pool.keys else "N/A"
            }
        return status
    
    def reset_all_rotations(self):
        """Reset all key rotations to start position"""
        for pool in self.key_pools.values():
            pool.reset_rotation()
        print("[API_KEY_MANAGER] 🔄 All key rotations reset")
    
    def validate_keys(self) -> Dict[str, bool]:
        """Basic validation of key availability"""
        validation = {}
        required_services = ["groq_stt", "gemini_tts", "gemini_ai"]
        
        for service in required_services:
            validation[service] = service in self.key_pools and len(self.key_pools[service].keys) > 0
            
        return validation

# Global API key manager instance
_api_key_manager = None

def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager

# Convenience functions
def get_groq_stt_key() -> Optional[str]:
    """Get next Groq STT API key"""
    return get_api_key_manager().get_groq_stt_key()

def get_gemini_tts_key() -> Optional[str]:
    """Get next Gemini TTS API key"""
    return get_api_key_manager().get_gemini_tts_key()

def get_gemini_ai_key() -> Optional[str]:
    """Get next Gemini AI API key"""
    return get_api_key_manager().get_gemini_ai_key()

def get_deepgram_key() -> Optional[str]:
    """Get Deepgram API key"""
    key = os.getenv("DEEPGRAM_API_KEY")
    if key and key.strip():
        return key.strip()
    return None