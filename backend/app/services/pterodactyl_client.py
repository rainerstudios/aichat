import httpx
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

class PterodactylAPIError(Exception):
    """Custom exception for Pterodactyl API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class PterodactylClient:
    """
    Async client for Pterodactyl Panel API
    Handles both client and application API endpoints with proper error handling
    """
    
    def __init__(self, api_key: str, base_url: str = None):
        """
        Initialize the Pterodactyl API client
        
        Args:
            api_key: User's API key (client API key, not application)
            base_url: Base URL of your Pterodactyl panel (e.g., https://panel.xgaming.pro)
        """
        import os
        self.api_key = api_key
        self.base_url = (base_url or os.getenv("PTERODACTYL_PANEL_URL", "https://panel.xgaming.pro")).rstrip('/')
        self.client_api_url = f"{self.base_url}/api/client"
        
        # Configure HTTP client with proper timeouts and retries
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0), 
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "XGamingServer-AI-Assistant/1.0"
            },
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make authenticated request to Pterodactyl API with error handling and retries
        """
        url = f"{self.client_api_url}/{endpoint.lstrip('/')}"
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = await self.session.request(method, url, **kwargs)
                
                # Handle different response types
                if response.status_code == 204:  # No content
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
                    f"API request failed: {error_message}",
                    status_code=response.status_code,
                    response_data=data
                )
                
            except httpx.TimeoutException:
                if attempt == max_retries - 1:
                    raise PterodactylAPIError("Request timed out after retries")
                await asyncio.sleep(retry_delay * (attempt + 1))
                
            except httpx.NetworkError as e:
                if attempt == max_retries - 1:
                    raise PterodactylAPIError(f"Network error: {str(e)}")
                await asyncio.sleep(retry_delay * (attempt + 1))
    
    # SERVER MANAGEMENT METHODS
    
    async def get_servers(self) -> List[Dict[str, Any]]:
        """Get list of all servers user has access to"""
        response = await self._make_request("GET", "/")
        return response.get("data", [])
    
    async def get_server_details(self, server_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific server"""
        response = await self._make_request("GET", f"/servers/{server_id}")
        return response.get("attributes", {})
    
    async def get_server_resources(self, server_id: str) -> Dict[str, Any]:
        """Get server resource usage (CPU, RAM, disk, network)"""
        response = await self._make_request("GET", f"/servers/{server_id}/resources")
        return response.get("attributes", {})
    
    async def send_power_action(self, server_id: str, action: str) -> Dict[str, Any]:
        """
        Send power signal to server
        Actions: start, stop, restart, kill
        """
        valid_actions = ["start", "stop", "restart", "kill"]
        if action not in valid_actions:
            raise ValueError(f"Invalid action '{action}'. Must be one of: {valid_actions}")
        
        return await self._make_request("POST", f"/servers/{server_id}/power", 
                                      json={"signal": action})
    
    async def send_console_command(self, server_id: str, command: str) -> Dict[str, Any]:
        """Send command to server console"""
        return await self._make_request("POST", f"/servers/{server_id}/command",
                                      json={"command": command})
    
    # FILE MANAGEMENT METHODS
    
    async def list_files(self, server_id: str, directory: str = "/") -> List[Dict[str, Any]]:
        """List files and directories in specified path"""
        response = await self._make_request("GET", f"/servers/{server_id}/files/list",
                                          params={"directory": directory})
        return response.get("data", [])
    
    async def get_file_contents(self, server_id: str, file_path: str) -> str:
        """Get contents of a text file"""
        response = await self._make_request("GET", f"/servers/{server_id}/files/contents",
                                          params={"file": file_path})
        return response.get("content", "")
    
    async def write_file(self, server_id: str, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        return await self._make_request("POST", f"/servers/{server_id}/files/write",
                                      params={"file": file_path},
                                      content=content,
                                      headers={"Content-Type": "text/plain"})
    
    async def create_folder(self, server_id: str, folder_name: str, path: str = "/") -> Dict[str, Any]:
        """Create a new folder"""
        return await self._make_request("POST", f"/servers/{server_id}/files/create-folder",
                                      json={"name": folder_name, "path": path})
    
    async def delete_files(self, server_id: str, files: List[str]) -> Dict[str, Any]:
        """Delete multiple files/folders"""
        return await self._make_request("POST", f"/servers/{server_id}/files/delete",
                                      json={"root": "/", "files": files})
    
    # BACKUP MANAGEMENT METHODS
    
    async def list_backups(self, server_id: str) -> List[Dict[str, Any]]:
        """Get list of server backups"""
        response = await self._make_request("GET", f"/servers/{server_id}/backups")
        return response.get("data", [])
    
    async def create_backup(self, server_id: str, name: str = None, ignored_files: List[str] = None) -> Dict[str, Any]:
        """Create a new server backup"""
        payload = {}
        if name:
            payload["name"] = name
        if ignored_files:
            payload["ignored"] = "\n".join(ignored_files)
        
        response = await self._make_request("POST", f"/servers/{server_id}/backups", json=payload)
        return response.get("attributes", {})
    
    async def delete_backup(self, server_id: str, backup_id: str) -> Dict[str, Any]:
        """Delete a backup"""
        return await self._make_request("DELETE", f"/servers/{server_id}/backups/{backup_id}")
    
    async def restore_backup(self, server_id: str, backup_id: str, truncate: bool = False) -> Dict[str, Any]:
        """Restore from backup"""
        return await self._make_request("POST", f"/servers/{server_id}/backups/{backup_id}/restore",
                                      json={"truncate": truncate})
    
    # DATABASE MANAGEMENT METHODS
    
    async def list_databases(self, server_id: str) -> List[Dict[str, Any]]:
        """Get list of server databases"""
        response = await self._make_request("GET", f"/servers/{server_id}/databases")
        return response.get("data", [])
    
    async def create_database(self, server_id: str, database_name: str, remote: str = "%") -> Dict[str, Any]:
        """Create a new database"""
        return await self._make_request("POST", f"/servers/{server_id}/databases",
                                      json={"database": database_name, "remote": remote})
    
    async def delete_database(self, server_id: str, database_id: str) -> Dict[str, Any]:
        """Delete a database"""
        return await self._make_request("DELETE", f"/servers/{server_id}/databases/{database_id}")
    
    async def rotate_database_password(self, server_id: str, database_id: str) -> Dict[str, Any]:
        """Generate new password for database"""
        return await self._make_request("POST", f"/servers/{server_id}/databases/{database_id}/rotate-password")
    
    # USER MANAGEMENT METHODS
    
    async def list_subusers(self, server_id: str) -> List[Dict[str, Any]]:
        """Get list of server subusers"""
        response = await self._make_request("GET", f"/servers/{server_id}/users")
        return response.get("data", [])
    
    async def create_subuser(self, server_id: str, email: str, permissions: List[str]) -> Dict[str, Any]:
        """Create a new subuser"""
        return await self._make_request("POST", f"/servers/{server_id}/users",
                                      json={"email": email, "permissions": permissions})
    
    # STARTUP VARIABLES METHODS
    
    async def get_startup_variables(self, server_id: str) -> Dict[str, Any]:
        """Get server startup configuration"""
        response = await self._make_request("GET", f"/servers/{server_id}/startup")
        return response.get("data", [])
    
    async def update_startup_variable(self, server_id: str, key: str, value: str) -> Dict[str, Any]:
        """Update a startup variable"""
        return await self._make_request("PUT", f"/servers/{server_id}/startup/variable",
                                      json={"key": key, "value": value})
    
    # NETWORK MANAGEMENT METHODS
    
    async def get_network_allocations(self, server_id: str) -> List[Dict[str, Any]]:
        """Get server network allocations (ports)"""
        response = await self._make_request("GET", f"/servers/{server_id}/network/allocations")
        return response.get("data", [])
    
    async def create_allocation(self, server_id: str, notes: str = None) -> Dict[str, Any]:
        """Create a new network allocation"""
        payload = {}
        if notes:
            payload["notes"] = notes
        return await self._make_request("POST", f"/servers/{server_id}/network/allocations", 
                                      json=payload)
    
    async def set_primary_allocation(self, server_id: str, allocation_id: str) -> Dict[str, Any]:
        """Set primary allocation (main port)"""
        return await self._make_request("POST", f"/servers/{server_id}/network/allocations/{allocation_id}/primary")
    
    # UTILITY METHODS
    
    async def get_websocket_credentials(self, server_id: str) -> Dict[str, Any]:
        """Get websocket credentials for real-time console access"""
        response = await self._make_request("GET", f"/servers/{server_id}/websocket")
        return response.get("data", {})
    
    async def test_connection(self) -> bool:
        """Test if API connection and authentication work"""
        try:
            await self._make_request("GET", "/")
            return True
        except PterodactylAPIError:
            return False

# Factory function for creating clients
def create_pterodactyl_client(api_key: str, base_url: str = None) -> PterodactylClient:
    """Factory function to create a Pterodactyl client"""
    return PterodactylClient(api_key, base_url)