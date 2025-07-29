import asyncio
import hashlib
import time
from typing import Dict, Any, Optional, Tuple
import json

class ResponseCache:
    """
    In-memory cache for AutoRAG responses to improve performance
    """
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self.ttl_seconds = ttl_seconds  # 5 minutes default
        self.max_size = max_size
        self.cache: Dict[str, Tuple[Any, float]] = {}  # key: (response, timestamp)
        self._lock = asyncio.Lock()
    
    def _generate_key(self, query: str, game_type: str = None) -> str:
        """Generate cache key from query and game type"""
        # Normalize query for better cache hits
        normalized_query = query.lower().strip()
        cache_input = f"{normalized_query}|{game_type or 'generic'}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    async def get(self, query: str, game_type: str = None) -> Optional[str]:
        """Get cached response if available and not expired"""
        async with self._lock:
            key = self._generate_key(query, game_type)
            
            if key in self.cache:
                response, timestamp = self.cache[key]
                
                # Check if not expired
                if time.time() - timestamp < self.ttl_seconds:
                    return response
                else:
                    # Remove expired entry
                    del self.cache[key]
            
            return None
    
    async def set(self, query: str, response: str, game_type: str = None):
        """Cache a response"""
        async with self._lock:
            key = self._generate_key(query, game_type)
            
            # Implement simple LRU by removing oldest if at max size
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (response, time.time())
    
    async def clear(self):
        """Clear all cached responses"""
        async with self._lock:
            self.cache.clear()
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            current_time = time.time()
            valid_entries = sum(1 for _, (_, timestamp) in self.cache.items() 
                              if current_time - timestamp < self.ttl_seconds)
            
            return {
                "total_entries": len(self.cache),
                "valid_entries": valid_entries,
                "expired_entries": len(self.cache) - valid_entries,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds
            }

# Global cache instance
_cache_instance = None

def get_cache() -> ResponseCache:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache(ttl_seconds=300, max_size=100)  # 5 min TTL, 100 entries max
    return _cache_instance