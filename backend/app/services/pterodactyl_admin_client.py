import httpx
import json
from typing import Dict, List, Optional, Any, Union
import asyncio
import os
from .pterodactyl_client import PterodactylAPIError

class PterodactylAdminClient:
    """
    Admin client using Pterodactyl Application API for centralized server management
    This uses a single admin API key and implements strict user-server validation
    """
    
    def __init__(self, admin_api_key: str = None, base_url: str = None):
        """
        Initialize the Pterodactyl Application API client
        
        Args:
            admin_api_key: Application API key with limited permissions
            base_url: Base URL of your Pterodactyl panel
        """
        self.admin_api_key = admin_api_key or os.getenv("PTERODACTYL_ADMIN_API_KEY")
        self.base_url = (base_url or os.getenv("PTERODACTYL_PANEL_URL", "https://panel.xgaming.pro")).rstrip('/')
        self.app_api_url = f"{self.base_url}/api/application"
        
        if not self.admin_api_key:
            raise ValueError("PTERODACTYL_ADMIN_API_KEY environment variable is required")
        
        # Configure HTTP client
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0), 
            headers={
                "Authorization": f"Bearer {self.admin_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "XGamingServer-AI-Assistant-Admin/1.0"
            },
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Pterodactyl Application API"""
        url = f"{self.app_api_url}/{endpoint.lstrip('/')}"
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = await self.session.request(method, url, **kwargs)
                
                if response.status_code == 204:
                    return {"success": True}
                
                if response.headers.get("content-type", "").startswith("application/json"):
                    data = response.json()
                else:
                    data = {"content": response.text}
                
                if response.is_success:
                    return data
                
                # Handle API errors
                error_message = "Unknown API error"
                if isinstance(data, dict):
                    if "errors" in data:
                        error_message = "; ".join([
                            f"{err.get('code', 'ERROR')}: {err.get('detail', 'Unknown error')}" 
                            for err in data["errors"]
                        ])
                    elif "message" in data:
                        error_message = data["message"]
                
                raise PterodactylAPIError(
                    f"Admin API request failed: {error_message}",
                    status_code=response.status_code,
                    response_data=data
                )
                
            except httpx.TimeoutException:
                if attempt == max_retries - 1:
                    raise PterodactylAPIError("Admin API request timed out after retries")
                await asyncio.sleep(retry_delay * (attempt + 1))
                
            except httpx.NetworkError as e:
                if attempt == max_retries - 1:
                    raise PterodactylAPIError(f"Admin API network error: {str(e)}")
                await asyncio.sleep(retry_delay * (attempt + 1))
    
    # USER AND SERVER RELATIONSHIP METHODS
    
    async def get_user_servers(self, pterodactyl_user_id: int) -> List[Dict[str, Any]]:
        """
        Get all servers owned by a specific Pterodactyl user
        CRITICAL: This is used for server ownership verification
        """
        try:
            # Get user with their servers included
            response = await self._make_request("GET", f"/users/{pterodactyl_user_id}", 
                                              params={"include": "servers"})
            
            user_data = response.get("attributes", {})
            relationships = user_data.get("relationships", {})
            servers_data = relationships.get("servers", {}).get("data", [])
            
            # Extract server UUIDs for ownership verification
            return [server.get("attributes", {}) for server in servers_data]
            
        except PterodactylAPIError as e:
            if e.status_code == 404:
                return []  # User not found
            raise
    
    async def verify_user_owns_server(self, pterodactyl_user_id: int, server_uuid: str) -> bool:
        """
        CRITICAL SECURITY METHOD: Verify a user owns a specific server
        Must be called before any server operations
        """
        try:
            user_servers = await self.get_user_servers(pterodactyl_user_id)
            
            # Check if server_uuid exists in user's servers
            for server in user_servers:
                if server.get("uuid") == server_uuid or server.get("identifier") == server_uuid:
                    return True
            
            return False
            
        except Exception as e:
            # On any error, deny access for security
            print(f"Server ownership verification failed: {e}")
            return False
    
    # SERVER MANAGEMENT METHODS (with ownership verification)
    
    async def get_server_details(self, server_uuid: str, pterodactyl_user_id: int = None) -> Dict[str, Any]:
        """Get server details (with optional ownership verification)"""
        # Optional: Verify ownership if user_id provided
        if pterodactyl_user_id:
            if not await self.verify_user_owns_server(pterodactyl_user_id, server_uuid):
                raise PterodactylAPIError(f"User {pterodactyl_user_id} does not own server {server_uuid}", 403)
        
        response = await self._make_request("GET", f"/servers/{server_uuid}")
        return response.get("attributes", {})
    
    async def send_power_action(self, server_uuid: str, action: str, pterodactyl_user_id: int) -> Dict[str, Any]:
        """
        Send power action to server with mandatory ownership verification
        """
        # CRITICAL: Always verify ownership for power actions
        if not await self.verify_user_owns_server(pterodactyl_user_id, server_uuid):
            raise PterodactylAPIError(f"Access denied: User {pterodactyl_user_id} does not own server {server_uuid}", 403)
        
        valid_actions = ["start", "stop", "restart", "kill"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action '{action}'. Must be one of: {valid_actions}")
        
        return await self._make_request("POST", f"/servers/{server_uuid}/power", 
                                      json={"signal": action})
    
    async def send_console_command(self, server_uuid: str, command: str, pterodactyl_user_id: int) -> Dict[str, Any]:
        """Send console command with ownership verification"""
        # CRITICAL: Always verify ownership for console commands
        if not await self.verify_user_owns_server(pterodactyl_user_id, server_uuid):
            raise PterodactylAPIError(f"Access denied: User {pterodactyl_user_id} does not own server {server_uuid}", 403)
        
        return await self._make_request("POST", f"/servers/{server_uuid}/command",
                                      json={"command": command})
    
    # Additional server management methods with ownership verification...
    
    async def test_connection(self) -> bool:
        """Test admin API connection"""
        try:
            await self._make_request("GET", "/users", params={"per_page": 1})
            return True
        except PterodactylAPIError:
            return False

# Factory function
def create_pterodactyl_admin_client() -> PterodactylAdminClient:
    """Factory function to create admin client"""
    return PterodactylAdminClient()