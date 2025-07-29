import asyncio
import hashlib
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field

@dataclass
class PendingRequest:
    """Represents a pending request with its future"""
    future: asyncio.Future = field(default_factory=asyncio.Future)
    waiters: Set[asyncio.Future] = field(default_factory=set)

class RequestDeduplicator:
    """
    Deduplicates identical requests to prevent multiple API calls for the same query
    """
    
    def __init__(self):
        self.pending_requests: Dict[str, PendingRequest] = {}
        self._lock = asyncio.Lock()
    
    def _generate_key(self, query: str, game_type: str = None) -> str:
        """Generate deduplication key from query and game type"""
        normalized_query = query.lower().strip()
        key_input = f"{normalized_query}|{game_type or 'generic'}"
        return hashlib.md5(key_input.encode()).hexdigest()
    
    async def deduplicate(self, query: str, game_type: str, query_func, *args, **kwargs):
        """
        Deduplicate identical requests - if same query is already being processed,
        wait for that result instead of making a new request
        """
        key = self._generate_key(query, game_type)
        
        async with self._lock:
            if key in self.pending_requests:
                # Request already in progress, wait for its result
                pending = self.pending_requests[key]
                waiter = asyncio.Future()
                pending.waiters.add(waiter)
                
                # Release lock before waiting
                async with asyncio.timeout(30):  # 30 second timeout
                    try:
                        return await waiter
                    except asyncio.CancelledError:
                        pending.waiters.discard(waiter)
                        raise
            else:
                # New request, create pending entry
                pending = PendingRequest()
                self.pending_requests[key] = pending
        
        try:
            # Execute the actual query function
            result = await query_func(*args, **kwargs)
            
            # Notify all waiters
            async with self._lock:
                if key in self.pending_requests:
                    pending = self.pending_requests[key]
                    
                    # Set result for the main future
                    if not pending.future.done():
                        pending.future.set_result(result)
                    
                    # Notify all waiters
                    for waiter in pending.waiters:
                        if not waiter.done():
                            waiter.set_result(result)
                    
                    # Clean up
                    del self.pending_requests[key]
            
            return result
            
        except Exception as e:
            # Notify all waiters of the error
            async with self._lock:
                if key in self.pending_requests:
                    pending = self.pending_requests[key]
                    
                    # Set exception for the main future
                    if not pending.future.done():
                        pending.future.set_exception(e)
                    
                    # Notify all waiters of the exception
                    for waiter in pending.waiters:
                        if not waiter.done():
                            waiter.set_exception(e)
                    
                    # Clean up
                    del self.pending_requests[key]
            
            raise
    
    async def clear_pending(self):
        """Clear all pending requests (useful for cleanup)"""
        async with self._lock:
            for pending in self.pending_requests.values():
                if not pending.future.done():
                    pending.future.cancel()
                for waiter in pending.waiters:
                    if not waiter.done():
                        waiter.cancel()
            self.pending_requests.clear()
    
    async def stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        async with self._lock:
            return {
                "pending_requests": len(self.pending_requests),
                "total_waiters": sum(len(p.waiters) for p in self.pending_requests.values())
            }

# Global deduplicator instance
_deduplicator_instance = None

def get_deduplicator() -> RequestDeduplicator:
    """Get or create global deduplicator instance"""
    global _deduplicator_instance
    if _deduplicator_instance is None:
        _deduplicator_instance = RequestDeduplicator()
    return _deduplicator_instance