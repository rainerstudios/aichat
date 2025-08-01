import asyncio
import hashlib
import time
import re
import mmh3
from typing import Dict, Any, Optional, Tuple, Set, List
from dataclasses import dataclass
from collections import defaultdict
import json

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    response: str
    timestamp: float
    query_hash: str
    game_type: str
    hit_count: int = 0

class MinHashLSH:
    """MinHash + LSH implementation for semantic similarity detection"""
    
    def __init__(self, num_perm: int = 64, threshold: float = 0.6):
        self.num_perm = num_perm
        self.threshold = threshold
        self.bands = int(num_perm / 4)  # 16 bands with 4 rows each
        self.rows = int(num_perm / self.bands)
        
        # LSH buckets: band_id -> bucket_hash -> set of query_hashes
        self.lsh_buckets: Dict[int, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
    def _get_shingles(self, text: str, k: int = 2) -> Set[str]:
        """Generate k-shingles from text"""
        # Normalize text
        text = re.sub(r'\s+', ' ', text.lower().strip())
        words = text.split()
        
        # Create word shingles
        shingles = set()
        for i in range(len(words) - k + 1):
            shingle = ' '.join(words[i:i + k])
            shingles.add(shingle)
            
        # Add single words for short queries
        if len(words) < k or len(shingles) < 3:
            shingles.update(words)
            
        return shingles
    
    def _compute_minhash(self, shingles: Set[str]) -> List[int]:
        """Compute MinHash signature"""
        if not shingles:
            return [0] * self.num_perm
            
        signature = []
        for i in range(self.num_perm):
            min_hash = float('inf')
            for shingle in shingles:
                # Use different hash seeds for each permutation
                hash_val = mmh3.hash(shingle, seed=i, signed=False)
                min_hash = min(min_hash, hash_val)
            signature.append(int(min_hash))
        return signature
    
    def _add_to_lsh(self, query_hash: str, signature: List[int]):
        """Add signature to LSH buckets"""
        for band in range(self.bands):
            start = band * self.rows
            end = start + self.rows
            band_values = tuple(signature[start:end])
            bucket_hash = hashlib.md5(str(band_values).encode()).hexdigest()
            self.lsh_buckets[band][bucket_hash].add(query_hash)
    
    def _get_candidates(self, signature: List[int]) -> Set[str]:
        """Get candidate similar queries from LSH buckets"""
        candidates = set()
        for band in range(self.bands):
            start = band * self.rows
            end = start + self.rows
            band_values = tuple(signature[start:end])
            bucket_hash = hashlib.md5(str(band_values).encode()).hexdigest()
            candidates.update(self.lsh_buckets[band].get(bucket_hash, set()))
        return candidates
    
    def add_query(self, query: str, query_hash: str):
        """Add a query to the LSH index"""
        shingles = self._get_shingles(query)
        signature = self._compute_minhash(shingles)
        self._add_to_lsh(query_hash, signature)
    
    def find_similar(self, query: str, stored_queries: Dict[str, str]) -> List[Tuple[str, float]]:
        """Find similar queries with similarity scores"""
        shingles = self._get_shingles(query)
        signature = self._compute_minhash(shingles)
        
        candidates = self._get_candidates(signature)
        similar_queries = []
        
        for candidate_hash in candidates:
            if candidate_hash in stored_queries:
                candidate_query = stored_queries[candidate_hash]
                candidate_shingles = self._get_shingles(candidate_query)
                candidate_signature = self._compute_minhash(candidate_shingles)
                
                # Calculate Jaccard similarity from MinHash signatures
                matches = sum(1 for a, b in zip(signature, candidate_signature) if a == b)
                similarity = matches / self.num_perm
                
                if similarity >= self.threshold:
                    similar_queries.append((candidate_hash, similarity))
        
        # Sort by similarity descending
        return sorted(similar_queries, key=lambda x: x[1], reverse=True)

class SimilarityCache:
    """
    Advanced similarity-based cache using MinHash + LSH for semantic query matching
    Implements Cloudflare AutoRAG-style similarity caching with configurable thresholds
    """
    
    # Similarity thresholds matching AutoRAG's behavior
    THRESHOLDS = {
        'exact': 0.95,    # Near-identical matches only
        'strong': 0.75,   # High semantic similarity (default)
        'broad': 0.6,     # Moderate matching
        'loose': 0.4      # Maximum reuse
    }
    
    def __init__(self, 
                 ttl_seconds: int = 1800,  # 30 minutes (AutoRAG uses 30 days, but we'll be more conservative)
                 max_size: int = 1000,
                 threshold: str = 'strong'):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.threshold_name = threshold
        self.threshold_value = self.THRESHOLDS.get(threshold, 0.75)
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}  # query_hash -> CacheEntry
        self.query_index: Dict[str, str] = {}   # query_hash -> original_query
        
        # MinHash LSH for similarity detection
        self.lsh = MinHashLSH(num_perm=64, threshold=self.threshold_value)
        
        # Async lock for thread safety
        self._lock = asyncio.Lock()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_queries': 0
        }
    
    def _generate_query_hash(self, query: str, game_type: str = None) -> str:
        """Generate hash for query + game_type"""
        # Normalize query for consistent hashing
        normalized_query = re.sub(r'\s+', ' ', query.lower().strip())
        cache_input = f"{normalized_query}|{game_type or 'generic'}"
        return hashlib.sha256(cache_input.encode()).hexdigest()
    
    def _cleanup_expired(self):
        """Remove expired entries (synchronous helper)"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry.timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            if key in self.cache:
                del self.cache[key]
            if key in self.query_index:
                del self.query_index[key]
        
        return len(expired_keys)
    
    def _evict_lru(self):
        """Evict least recently used entries"""
        if len(self.cache) < self.max_size:
            return 0
            
        # Sort by hit_count (ascending) then timestamp (ascending) for LRU
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: (x[1].hit_count, x[1].timestamp)
        )
        
        # Remove oldest 20% to avoid frequent evictions
        evict_count = max(1, len(sorted_entries) // 5)
        evicted = 0
        
        for key, _ in sorted_entries[:evict_count]:
            if key in self.cache:
                del self.cache[key]
                evicted += 1
            if key in self.query_index:
                del self.query_index[key]
        
        self.stats['evictions'] += evicted
        return evicted
    
    async def get(self, query: str, game_type: str = None) -> Optional[str]:
        """Get cached response for query or similar queries"""
        async with self._lock:
            self.stats['total_queries'] += 1
            
            # Clean up expired entries
            expired_count = self._cleanup_expired()
            
            # First try exact match
            query_hash = self._generate_query_hash(query, game_type)
            if query_hash in self.cache:
                entry = self.cache[query_hash]
                entry.hit_count += 1
                self.stats['hits'] += 1
                return entry.response
            
            # Then try similarity matching using LSH
            similar_queries = self.lsh.find_similar(query, self.query_index)
            
            for similar_hash, similarity in similar_queries:
                if similar_hash in self.cache:
                    # Check game_type compatibility
                    entry = self.cache[similar_hash]
                    if game_type is None or entry.game_type == game_type or entry.game_type == 'generic':
                        entry.hit_count += 1
                        self.stats['hits'] += 1
                        
                        # Add note about cache hit
                        cache_note = f"\n\n*[Similar query found in cache - {similarity:.1%} match]*"
                        return entry.response + cache_note
            
            self.stats['misses'] += 1
            return None
    
    async def set(self, query: str, response: str, game_type: str = None):
        """Cache a response with similarity indexing"""
        async with self._lock:
            query_hash = self._generate_query_hash(query, game_type)
            
            # Evict if necessary
            self._evict_lru()
            
            # Store the entry
            entry = CacheEntry(
                response=response,
                timestamp=time.time(),
                query_hash=query_hash,
                game_type=game_type or 'generic',
                hit_count=0
            )
            
            self.cache[query_hash] = entry
            self.query_index[query_hash] = query
            
            # Add to LSH index for similarity matching
            self.lsh.add_query(query, query_hash)
    
    async def clear(self):
        """Clear all cached responses"""
        async with self._lock:
            self.cache.clear()
            self.query_index.clear()
            self.lsh = MinHashLSH(num_perm=64, threshold=self.threshold_value)
            
            # Reset stats
            self.stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'total_queries': 0
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        async with self._lock:
            current_time = time.time()
            valid_entries = sum(
                1 for entry in self.cache.values()
                if current_time - entry.timestamp < self.ttl_seconds
            )
            
            hit_rate = (self.stats['hits'] / max(1, self.stats['total_queries'])) * 100
            
            return {
                "cache_status": "enabled",
                "similarity_threshold": f"{self.threshold_name} ({self.threshold_value:.2f})",
                "total_entries": len(self.cache),
                "valid_entries": valid_entries,
                "expired_entries": len(self.cache) - valid_entries,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hit_rate": f"{hit_rate:.1f}%",
                "total_hits": self.stats['hits'],
                "total_misses": self.stats['misses'],
                "total_queries": self.stats['total_queries'],
                "evictions": self.stats['evictions'],
                "memory_usage": len(str(self.cache).encode('utf-8')),
                "lsh_buckets": sum(len(buckets) for buckets in self.lsh.lsh_buckets.values())
            }
    
    async def set_threshold(self, threshold: str):
        """Change similarity threshold dynamically"""
        if threshold in self.THRESHOLDS:
            async with self._lock:
                self.threshold_name = threshold
                self.threshold_value = self.THRESHOLDS[threshold]
                # Rebuild LSH index with new threshold
                self.lsh = MinHashLSH(num_perm=64, threshold=self.threshold_value)
                for query_hash, query in self.query_index.items():
                    self.lsh.add_query(query, query_hash)

# Global similarity cache instance
_similarity_cache_instance = None

def get_similarity_cache(threshold: str = 'strong') -> SimilarityCache:
    """Get or create global similarity cache instance"""
    global _similarity_cache_instance
    if _similarity_cache_instance is None:
        _similarity_cache_instance = SimilarityCache(
            ttl_seconds=1800,  # 30 minutes
            max_size=1000,     # 1000 entries
            threshold=threshold
        )
    return _similarity_cache_instance

# Backwards compatibility with existing cache interface
class ResponseCache:
    """Legacy cache interface - wraps SimilarityCache"""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self.similarity_cache = SimilarityCache(
            ttl_seconds=ttl_seconds,
            max_size=max_size,
            threshold='strong'
        )
    
    async def get(self, query: str, game_type: str = None) -> Optional[str]:
        return await self.similarity_cache.get(query, game_type)
    
    async def set(self, query: str, response: str, game_type: str = None):
        await self.similarity_cache.set(query, response, game_type)
    
    async def clear(self):
        await self.similarity_cache.clear()
    
    async def stats(self) -> Dict[str, Any]:
        return await self.similarity_cache.get_stats()