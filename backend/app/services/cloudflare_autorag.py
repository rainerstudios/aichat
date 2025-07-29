import httpx
import json
import os
from typing import Dict, List, Any, Optional

class CloudflareAutoRAGService:
    """
    Service for interacting with Cloudflare AutoRAG
    """
    
    def __init__(self, 
                 account_id: str = None, 
                 api_token: str = None,
                 autorag_instance_id: str = None):
        self.account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN") 
        self.autorag_instance_id = autorag_instance_id or os.getenv("CLOUDFLARE_AUTORAG_INSTANCE_ID")
        
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
    
    async def query(self, 
                   question: str, 
                   max_results: int = 5,
                   filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query the AutoRAG system with a question
        
        Args:
            question: The user's question
            max_results: Maximum number of results to return
            filters: Optional metadata filters for retrieval
            
        Returns:
            Dict containing the answer and source documents
        """
        try:
            query_data = {
                "query": question
            }
            
            # Use the ai-search endpoint as shown in your curl example
            response = await self.session.post(f"{self.base_url}/ai-search", json=query_data)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the answer and sources from Cloudflare's response format
            if result.get("success"):
                result_data = result.get("result", {})
                return {
                    "answer": result_data.get("response", "No answer found"),
                    "sources": result_data.get("sources", []),
                    "query": question,
                    "search_query": result_data.get("search_query", question),
                    "confidence": 1.0 if result_data.get("response") else 0.0
                }
            else:
                errors = result.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else "AutoRAG query failed"
                return {
                    "answer": f"Error: {error_msg}",
                    "sources": [],
                    "query": question,
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
def create_autorag_service() -> CloudflareAutoRAGService:
    """Create AutoRAG service instance"""
    return CloudflareAutoRAGService()

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