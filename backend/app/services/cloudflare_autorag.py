import httpx
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class AutoRAGConfig:
    """Configuration for AutoRAG optimization features"""
    enable_query_rewriting: bool = True
    enable_similarity_cache: bool = True
    chunk_size: int = 256  # Optimized for speed
    chunk_overlap: float = 0.15  # 15% overlap
    max_results: int = 5
    match_threshold: float = 0.3
    similarity_cache_threshold: str = 'strong'  # exact, strong, broad, loose

class CloudflareAutoRAGService:
    """
    Service for interacting with Cloudflare AutoRAG
    """
    
    def __init__(self, 
                 account_id: str = None, 
                 api_token: str = None,
                 autorag_instance_id: str = None,
                 config: AutoRAGConfig = None):
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN") 
        self.autorag_instance_id = autorag_instance_id or os.getenv("CLOUDFLARE_AUTORAG_INSTANCE_ID")
        self.config = config or AutoRAGConfig()
        
        if not all([self.account_id, self.api_token, self.autorag_instance_id]):
            raise ValueError("Missing required Cloudflare credentials: CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, CLOUDFLARE_AUTORAG_INSTANCE_ID")
        
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/autorag/rags/{self.autorag_instance_id}"
        
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=5.0),  # More reasonable timeout - 20s total, 5s connect
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            },
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)  # Connection pooling
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    def _rewrite_query(self, question: str, game_type: str = None) -> str:
        """
        Rewrite user query for better vector search performance
        Transforms conversational queries into keyword-rich search terms
        """
        if not self.config.enable_query_rewriting:
            return question
            
        # Basic query enhancement patterns
        query = question.lower().strip()
        
        # Extract key terms and add synonyms
        enhanced_terms = []
        
        # Game-specific enhancements
        if game_type:
            if "minecraft" in game_type.lower():
                enhanced_terms.extend(["minecraft", "server", "configuration", "setup"])
            elif "pterodactyl" in query or "panel" in query:
                enhanced_terms.extend(["pterodactyl", "panel", "server management", "configuration"])
        
        # Problem-solving keywords
        if any(word in query for word in ["error", "issue", "problem", "not working", "broken"]):
            enhanced_terms.extend(["troubleshooting", "fix", "solution", "debugging"])
        
        # Setup/configuration keywords
        if any(word in query for word in ["setup", "install", "configure", "settings"]):
            enhanced_terms.extend(["installation", "configuration", "guide", "tutorial"])
        
        # Performance keywords
        if any(word in query for word in ["slow", "lag", "performance", "optimize"]):
            enhanced_terms.extend(["performance", "optimization", "tuning", "resources"])
        
        # Combine original query with enhanced terms
        all_terms = [question] + enhanced_terms
        enhanced_query = " ".join(set(all_terms))  # Remove duplicates
        
        # Limit length to prevent issues
        if len(enhanced_query) > 200:
            enhanced_query = enhanced_query[:200]
        
        return enhanced_query
    
    def _build_metadata_filters(self, game_type: str = None, doc_types: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Build metadata filters for scoped retrieval
        Reduces search space and improves relevance
        """
        filters = []
        
        # Game-type based filtering
        if game_type and game_type != "Unknown":
            # Create a compound filter for game-type folders
            game_filter = {
                "type": "or",
                "filters": [
                    {"type": "eq", "key": "folder", "value": f"{game_type.lower()}/"},
                    {"type": "eq", "key": "folder", "value": "general/"},
                    {"type": "eq", "key": "folder", "value": "pterodactyl/"}
                ]
            }
            filters.append(game_filter)
        
        # Document type filtering (if specified)
        if doc_types:
            doc_type_filter = {
                "type": "or",
                "filters": [
                    {"type": "eq", "key": "folder", "value": f"{doc_type}/"}
                    for doc_type in doc_types
                ]
            }
            filters.append(doc_type_filter)
        
        # Recent documents preference (last 6 months)
        import time
        six_months_ago = int((time.time() - 15552000) * 1000)  # 6 months in milliseconds
        filters.append({
            "type": "gte",
            "key": "timestamp",
            "value": str(six_months_ago)
        })
        
        if len(filters) == 1:
            return filters[0]
        elif len(filters) > 1:
            return {
                "type": "and",
                "filters": filters
            }
        
        return None

    async def query(self, 
                   question: str, 
                   max_results: int = None,
                   filters: Optional[Dict[str, Any]] = None,
                   game_type: str = None) -> Dict[str, Any]:
        """
        Query the AutoRAG system with enhanced features
        
        Args:
            question: The user's question
            max_results: Maximum number of results to return (uses config default if None)
            filters: Optional metadata filters for retrieval (merged with auto-generated filters)
            game_type: Game type for context-aware filtering and query rewriting
            
        Returns:
            Dict containing the answer and source documents
        """
        try:
            # Use config defaults if not specified
            max_results = max_results or self.config.max_results
            
            # Apply query rewriting for better retrieval
            enhanced_query = self._rewrite_query(question, game_type)
            
            # Build metadata filters for scoped retrieval
            auto_filters = self._build_metadata_filters(game_type)
            
            # Merge user filters with auto-generated filters
            final_filters = filters
            if auto_filters:
                if filters:
                    final_filters = {
                        "type": "and",
                        "filters": [filters, auto_filters]
                    }
                else:
                    final_filters = auto_filters
            
            # Build request payload with optimization parameters
            query_data = {
                "query": enhanced_query,
                "rewrite_query": self.config.enable_query_rewriting,
                "max_num_results": max_results,
                "ranking_options": {
                    "score_threshold": self.config.match_threshold
                }
            }
            
            # Add filters if present
            if final_filters:
                query_data["filters"] = final_filters
            
            # Use the ai-search endpoint with optimized parameters
            response = await self.session.post(f"{self.base_url}/ai-search", json=query_data)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the answer and sources from Cloudflare's response format
            if result.get("success"):
                result_data = result.get("result", {})
                return {
                    "answer": result_data.get("response", "No answer found"),
                    "sources": result_data.get("data", []),  # Updated to match AutoRAG format
                    "query": question,
                    "search_query": result_data.get("search_query", enhanced_query),
                    "enhanced_query": enhanced_query,
                    "filters_applied": final_filters is not None,
                    "confidence": 1.0 if result_data.get("response") else 0.0
                }
            else:
                errors = result.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else "AutoRAG query failed"
                return {
                    "answer": f"Error: {error_msg}",
                    "sources": [],
                    "query": question,
                    "enhanced_query": enhanced_query,
                    "confidence": 0.0
                }
            
        except httpx.TimeoutException as e:
            # Return a timeout-specific response instead of crashing
            return {
                "answer": "The documentation search timed out. This might be due to high server load. Please try a simpler question or try again in a moment.",
                "sources": [],
                "query": question,
                "confidence": 0.0
            }
        except httpx.HTTPError as e:
            # Handle HTTP errors gracefully
            return {
                "answer": f"Documentation service is temporarily unavailable (HTTP {e.response.status_code if hasattr(e, 'response') else 'error'}). Please try again later.",
                "sources": [],
                "query": question,
                "confidence": 0.0
            }
        except Exception as e:
            # Handle any other errors gracefully
            return {
                "answer": "I encountered an issue searching the documentation. Let me try to answer from my general knowledge instead.",
                "sources": [],
                "query": question,
                "confidence": 0.0
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get AutoRAG instance status
        """
        try:
            response = await self.session.get(f"{self.base_url}/status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get AutoRAG status: {e}")

# Factory function
def create_autorag_service(config: AutoRAGConfig = None) -> CloudflareAutoRAGService:
    """Create AutoRAG service instance with optimized configuration"""
    if config is None:
        config = AutoRAGConfig(
            enable_query_rewriting=True,
            enable_similarity_cache=True,
            chunk_size=256,  # Optimized for speed
            chunk_overlap=0.15,
            max_results=5,
            match_threshold=0.3,
            similarity_cache_threshold='strong'
        )
    return CloudflareAutoRAGService(config=config)

# Helper function to format AutoRAG response for LangGraph tools
def format_autorag_response(response: Dict[str, Any]) -> str:
    """
    Format AutoRAG response into a readable string for the LLM
    """
    answer = response.get("answer", "No answer found")
    sources = response.get("sources", [])
    
    # Limit answer length to prevent streaming issues
    if len(answer) > 2000:
        answer = answer[:2000] + "...\n\n[Response truncated for readability]"
    
    # Clean answer text to remove potential problematic characters
    answer = answer.replace('\x00', '').strip()
    
    formatted_response = f"{answer}\n\n"
    
    # Only add sources if we have them and response isn't too long already
    if sources and len(formatted_response) < 1500:
        formatted_response += "**Sources:**\n"
        for i, source in enumerate(sources[:2], 1):  # Limit to top 2 sources
            title = source.get("title", "Unknown")[:50]  # Limit title length
            url = source.get("url", "")
            
            formatted_response += f"{i}. {title}"
            if url:
                formatted_response += f" - {url}"
            formatted_response += "\n"
            
            # Stop if response gets too long
            if len(formatted_response) > 1800:
                break
    
    return formatted_response[:2000]  # Hard limit on response length