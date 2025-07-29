# 📋 Phase 1: Core Integration Implementation
*Timeline: Week 1-2 | Build the foundation for full Pterodactyl integration*

## Overview
Phase 1 establishes the core infrastructure needed for deep Pterodactyl panel integration, including API client, user authentication, and safety mechanisms.

---

## 🎯 Phase 1 Goals
- ✅ Real Pterodactyl API integration (replace mock data)
- ✅ User authentication and session management  
- ✅ Server context detection and management
- ✅ Safety mechanisms for destructive operations
- ✅ Error handling and retry logic
- ✅ Basic security and permission validation

---

## 📦 Week 1: Core Infrastructure

### ✅ Task 1.1: Pterodactyl API Client Implementation (Day 1-2)

#### Step 1: Create API Client Service
- [ ] **File**: `backend/app/services/__init__.py` 
- [ ] **Action**: Create services directory

```python
# CREATE NEW FILE
# This marks the services directory as a Python package
```

- [ ] **File**: `backend/app/services/pterodactyl_client.py`
- [ ] **Action**: Create comprehensive API client

```python
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
            base_url: Base URL of your Pterodactyl panel (e.g., https://panel.xgamingserver.com)
        """
        self.api_key = api_key
        self.base_url = (base_url or "https://panel.xgamingserver.com").rstrip('/')
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
        response = await self._make_request("GET", "/servers")
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
```

#### Step 2: Add Environment Configuration
- [ ] **File**: `backend/.env` 
- [ ] **Action**: Add Pterodactyl configuration

```bash
# ADD THESE TO YOUR EXISTING .env FILE

# Pterodactyl Panel Configuration
PTERODACTYL_PANEL_URL=https://panel.xgamingserver.com
PTERODACTYL_DEFAULT_API_KEY=your_admin_api_key_here

# Security Settings
API_RATE_LIMIT_PER_MINUTE=60
REQUIRE_USER_AUTHENTICATION=true
ALLOW_DANGEROUS_OPERATIONS=false
```

#### Step 3: Update Requirements
- [ ] **File**: `backend/requirements.txt`
- [ ] **Action**: Add new dependencies

```txt
# ADD THESE LINES TO YOUR EXISTING requirements.txt
httpx>=0.24.0
python-multipart>=0.0.6
pydantic-settings>=2.0.0
```

- [ ] **Action**: Install new dependencies
```bash
cd /var/www/aichat/backend
pip install httpx python-multipart pydantic-settings
```

#### Step 4: Test API Client
- [ ] **File**: `backend/test_api_client.py` (temporary test file)
- [ ] **Action**: Create test script

```python
# CREATE TEMPORARY TEST FILE - DELETE AFTER TESTING
import asyncio
from app.services.pterodactyl_client import PterodactylClient

async def test_client():
    # Replace with a real user API key for testing
    client = PterodactylClient("your_test_api_key_here")
    
    try:
        # Test connection
        connected = await client.test_connection()
        print(f"Connection test: {'✅ Success' if connected else '❌ Failed'}")
        
        # Test getting servers
        servers = await client.get_servers()
        print(f"Found {len(servers)} servers")
        
        if servers:
            server_id = servers[0]["attributes"]["identifier"]
            print(f"Testing with server: {server_id}")
            
            # Test server details
            details = await client.get_server_details(server_id)
            print(f"Server name: {details.get('name', 'Unknown')}")
            
            # Test resources
            resources = await client.get_server_resources(server_id)
            print(f"CPU usage: {resources.get('cpu_absolute', 0)}%")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await client.session.aclose()

if __name__ == "__main__":
    asyncio.run(test_client())
```

- [ ] **Action**: Run test
```bash
cd /var/www/aichat/backend
python test_api_client.py
```

- [ ] **Expected Result**: Should connect and list servers
- [ ] **Action**: Delete test file after successful test

### ✅ Task 1.2: User Authentication System (Day 3-4)

#### Step 1: Create User Management Service
- [ ] **File**: `backend/app/services/user_manager.py`
- [ ] **Action**: Create user session management

```python
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import jwt
import hashlib
from pydantic import BaseModel

class UserSession(BaseModel):
    user_id: str
    session_id: str
    api_key: str
    permissions: List[str]
    servers: List[str]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime

class UserManager:
    """
    Manages user sessions and API key validation
    """
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.active_sessions: Dict[str, UserSession] = {}
        self.session_timeout = timedelta(hours=2)  # 2 hour timeout
    
    def create_session(self, user_id: str, api_key: str, 
                      permissions: List[str] = None, 
                      servers: List[str] = None) -> str:
        """
        Create a new user session
        """
        session_id = self._generate_session_id(user_id, api_key)
        now = datetime.utcnow()
        
        session = UserSession(
            user_id=user_id,
            session_id=session_id,
            api_key=api_key,
            permissions=permissions or [],
            servers=servers or [],
            created_at=now,
            expires_at=now + self.session_timeout,
            last_activity=now
        )
        
        self.active_sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Get active session and update last activity
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Check if session expired
        if datetime.utcnow() > session.expires_at:
            del self.active_sessions[session_id]
            return None
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        return session
    
    def validate_server_access(self, session_id: str, server_id: str) -> bool:
        """
        Check if user has access to specific server
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        # If no servers specified, allow all (admin mode)
        if not session.servers:
            return True
        
        return server_id in session.servers
    
    def has_permission(self, session_id: str, permission: str) -> bool:
        """
        Check if user has specific permission
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        return permission in session.permissions
    
    def cleanup_expired_sessions(self):
        """
        Remove expired sessions
        """
        now = datetime.utcnow()
        expired_sessions = [
            sid for sid, session in self.active_sessions.items()
            if now > session.expires_at
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
    
    def _generate_session_id(self, user_id: str, api_key: str) -> str:
        """
        Generate unique session ID
        """
        data = f"{user_id}:{api_key}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

# Global user manager instance
user_manager = UserManager("your-secret-key-change-this")
```

#### Step 2: Add Authentication Middleware
- [ ] **File**: `backend/app/middleware/__init__.py`
- [ ] **Action**: Create middleware directory

```python
# CREATE NEW FILE
# This marks the middleware directory as a Python package
```

- [ ] **File**: `backend/app/middleware/auth.py`
- [ ] **Action**: Create authentication middleware

```python
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from ..services.user_manager import user_manager, UserSession
from ..services.pterodactyl_client import PterodactylClient

security = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserSession:
    """
    Get current authenticated user session
    """
    # For development/testing - allow bypass with header
    if request.headers.get("X-Dev-Mode") == "true":
        return create_dev_session()
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide valid API key."
        )
    
    # Extract session ID from token
    session_id = credentials.credentials
    session = user_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please authenticate again."
        )
    
    return session

async def authenticate_user_api_key(api_key: str) -> UserSession:
    """
    Authenticate user with Pterodactyl API key and create session
    """
    try:
        # Test API key by attempting to connect
        async with PterodactylClient(api_key) as client:
            connected = await client.test_connection()
            if not connected:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key. Cannot connect to Pterodactyl panel."
                )
            
            # Get user's servers
            servers = await client.get_servers()
            server_ids = [s["attributes"]["identifier"] for s in servers]
            
            # Create session
            user_id = f"user_{api_key[:8]}"  # Simple user ID based on API key
            session_id = user_manager.create_session(
                user_id=user_id,
                api_key=api_key,
                permissions=["server.control", "server.files", "server.config"],
                servers=server_ids
            )
            
            return user_manager.get_session(session_id)
            
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

def create_dev_session() -> UserSession:
    """
    Create development session for testing (REMOVE IN PRODUCTION)
    """
    from datetime import datetime, timedelta
    
    return UserSession(
        user_id="dev_user",
        session_id="dev_session",
        api_key="dev_api_key",
        permissions=["server.control", "server.files", "server.config"],
        servers=["dev_server"],
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        last_activity=datetime.utcnow()
    )

async def require_server_access(server_id: str, user: UserSession = Depends(get_current_user)):
    """
    Ensure user has access to specific server
    """
    if not user_manager.validate_server_access(user.session_id, server_id):
        raise HTTPException(
            status_code=403,
            detail=f"You don't have access to server {server_id}"
        )
    
    return user

async def require_permission(permission: str, user: UserSession = Depends(get_current_user)):
    """
    Ensure user has specific permission
    """
    if not user_manager.has_permission(user.session_id, permission):
        raise HTTPException(
            status_code=403,
            detail=f"You don't have permission: {permission}"
        )
    
    return user
```

#### Step 3: Update LangGraph State with User Context
- [ ] **File**: `backend/app/langgraph/state.py`
- [ ] **Action**: Add user context to state

```python
# REPLACE YOUR EXISTING state.py WITH THIS ENHANCED VERSION

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # Core conversation state
    messages: Annotated[list[BaseMessage], add_messages]
    
    # User context (NEW)
    user_id: str
    session_id: str  
    api_key: str
    user_permissions: List[str]
    accessible_servers: List[str]
    
    # Server context (NEW)
    current_server_id: Optional[str]
    server_info: Optional[Dict[str, Any]]
    game_type: Optional[str]
    
    # Operation context (NEW)
    pending_confirmation: Optional[Dict[str, Any]]
    last_operation_result: Optional[Dict[str, Any]]
    safety_warnings: List[str]
    
    # System context
    system_prompt: str
    frontend_tools: List[Dict[str, Any]]
```

### ✅ Task 1.3: Enhanced Tool System with Real API Integration (Day 5-6)

#### Step 1: Update Tools with Real API Calls
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Replace with enhanced tool system

```python
# REPLACE YOUR EXISTING tools.py WITH THIS ENHANCED VERSION

from langchain_core.tools import tool
from typing import Dict, List, Optional, Any
import asyncio
from ..services.pterodactyl_client import PterodactylClient, PterodactylAPIError
from ..services.user_manager import user_manager
import json

# Helper function to get client for user
def get_user_client(session_id: str) -> PterodactylClient:
    """Get Pterodactyl client for authenticated user"""
    session = user_manager.get_session(session_id)
    if not session:
        raise ValueError("Invalid session - please authenticate")
    
    return PterodactylClient(session.api_key)

# Helper function to detect server from context
async def detect_server_id(session_id: str, server_hint: str = None) -> str:
    """Auto-detect server ID from user context"""
    session = user_manager.get_session(session_id)
    if not session:
        raise ValueError("Invalid session")
    
    # If user specified a server
    if server_hint and server_hint != "auto-detect":
        if server_hint in session.servers:
            return server_hint
        else:
            raise ValueError(f"You don't have access to server '{server_hint}'")
    
    # Auto-detect: use first available server
    if session.servers:
        return session.servers[0]
    
    # Last resort: get from API
    async with get_user_client(session_id) as client:
        servers = await client.get_servers()
        if servers:
            return servers[0]["attributes"]["identifier"]
    
    raise ValueError("No servers found for your account")

@tool
async def get_server_status(server_id: str = "auto-detect", session_id: str = "dev_session") -> str:
    """Get current server status, player count, and resource usage"""
    try:
        # Detect actual server ID
        actual_server_id = await detect_server_id(session_id, server_id)
        
        async with get_user_client(session_id) as client:
            # Get server details and resources in parallel
            server_details, resources = await asyncio.gather(
                client.get_server_details(actual_server_id),
                client.get_server_resources(actual_server_id)
            )
            
            # Format response
            status_map = {
                "running": "🟢 ONLINE",
                "starting": "🟡 STARTING", 
                "stopping": "🟡 STOPPING",
                "offline": "🔴 OFFLINE"
            }
            
            status = status_map.get(server_details.get("current_state", "unknown"), "❓ UNKNOWN")
            
            # Format resource usage
            cpu_usage = f"{resources.get('cpu_absolute', 0):.1f}%"
            memory_bytes = resources.get('memory_bytes', 0)
            memory_limit = server_details.get('limits', {}).get('memory', 1024) * 1024 * 1024  # MB to bytes
            memory_usage = f"{memory_bytes / (1024**3):.1f}GB / {memory_limit / (1024**3):.1f}GB"
            
            disk_bytes = resources.get('disk_bytes', 0) 
            disk_limit = server_details.get('limits', {}).get('disk', 10240) * 1024 * 1024  # MB to bytes
            disk_usage = f"{disk_bytes / (1024**3):.1f}GB / {disk_limit / (1024**3):.1f}GB"
            
            network_rx = resources.get('network_rx_bytes', 0) / (1024**2)  # MB
            network_tx = resources.get('network_tx_bytes', 0) / (1024**2)  # MB
            
            return f"""
🖥️ **{server_details.get('name', 'Unknown Server')}**
**Status**: {status}
**Server ID**: `{actual_server_id}`

📊 **Resource Usage**
⚡ **CPU**: {cpu_usage}
💾 **Memory**: {memory_usage} ({memory_bytes / memory_limit * 100:.1f}%)
💽 **Disk**: {disk_usage} ({disk_bytes / disk_limit * 100:.1f}%)
🌐 **Network**: ↓{network_rx:.1f}MB ↑{network_tx:.1f}MB

🎮 **Game Info**
**Type**: {server_details.get('egg', {}).get('name', 'Unknown')}
**Node**: {server_details.get('node', 'Unknown')}

⏱️ **Uptime**: {resources.get('uptime', 0) // 1000 // 60} minutes
"""
            
    except PterodactylAPIError as e:
        return f"❌ **API Error**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool
async def restart_server(server_id: str = "auto-detect", confirm: bool = False, session_id: str = "dev_session") -> str:
    """Restart a game server (REQUIRES CONFIRMATION - will disconnect players)"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        if not confirm:
            # Get server details to show impact
            async with get_user_client(session_id) as client:
                details = await client.get_server_details(actual_server_id)
                resources = await client.get_server_resources(actual_server_id)
            
            return f"""
⚠️  **CONFIRMATION REQUIRED** ⚠️

**Server**: {details.get('name', 'Unknown')}
**Current Status**: {details.get('current_state', 'unknown').upper()}

**Restart will:**
- 🔄 Stop the server gracefully
- 💾 Save current world state
- ⏳ Server offline for 30-60 seconds
- 🚀 Restart with fresh resources

**⚠️ Players will be disconnected temporarily**

To proceed, say: **"restart server with confirmation"**
"""
        
        # Execute restart
        async with get_user_client(session_id) as client:
            await client.send_power_action(actual_server_id, "restart")
            
        return f"""
✅ **Server Restart Initiated** 

🔄 **Status**: Restart signal sent successfully
⏳ **ETA**: Server will be back online in 30-60 seconds
📊 **Monitor**: Use "get server status" to check progress

**Next Steps:**
1. Wait 30-60 seconds for full restart
2. Check status to confirm server is online
3. Players can reconnect once status shows "ONLINE"
"""
        
    except PterodactylAPIError as e:
        return f"❌ **Restart Failed**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool
async def stop_server(server_id: str = "auto-detect", confirm: bool = False, session_id: str = "dev_session") -> str:
    """Stop a game server (REQUIRES CONFIRMATION - will disconnect all players)"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        if not confirm:
            async with get_user_client(session_id) as client:
                details = await client.get_server_details(actual_server_id)
                
            return f"""
🛑 **CONFIRMATION REQUIRED** 🛑

**Server**: {details.get('name', 'Unknown')}
**Current Status**: {details.get('current_state', 'unknown').upper()}

**Stop will:**
- ⏹️ Shut down server completely  
- 💾 Save all data and disconnect players
- 🔴 Server will remain OFFLINE until manually started

**⚠️ All players will be disconnected immediately**

To proceed, say: **"stop server with confirmation"**
"""
        
        # Execute stop
        async with get_user_client(session_id) as client:
            await client.send_power_action(actual_server_id, "stop")
            
        return f"""
🛑 **Server Stop Initiated**

✅ **Status**: Stop signal sent successfully
🔴 **Result**: Server is shutting down
⏹️ **Note**: Server will remain offline until started

**To start again**: Say "start server" when ready
"""
        
    except PterodactylAPIError as e:
        return f"❌ **Stop Failed**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool
async def start_server(server_id: str = "auto-detect", session_id: str = "dev_session") -> str:
    """Start a stopped game server"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        async with get_user_client(session_id) as client:
            await client.send_power_action(actual_server_id, "start")
            
        return f"""
🚀 **Server Start Initiated**

✅ **Status**: Start signal sent successfully
⚡ **Progress**: Server is booting up...
⏳ **ETA**: Online in 30-60 seconds

**Monitor Progress**: Use "get server status" to check when ready
**Players**: Can connect once status shows "ONLINE"
"""
        
    except PterodactylAPIError as e:
        return f"❌ **Start Failed**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool
async def send_server_command(command: str, server_id: str = "auto-detect", session_id: str = "dev_session") -> str:
    """Send a command to the game server console"""
    try:
        actual_server_id = await detect_server_id(session_id, server_id)
        
        # Safety checks for dangerous commands
        dangerous_patterns = [
            'stop', 'shutdown', 'kill', 'halt',
            'rm ', 'delete', 'format', 'wipe',
            'ban ', 'kick ', 'whitelist remove'
        ]
        
        if any(pattern in command.lower() for pattern in dangerous_patterns):
            return f"""
⚠️  **POTENTIALLY DANGEROUS COMMAND** ⚠️

Command: `{command}`

**This command could:**
- Disconnect players
- Delete data
- Cause server instability

**Safer alternatives:**
- For player management: Ask me "help with player management"
- For server control: Use "restart/stop/start server" commands
- For configuration: Ask me "help with server settings"

What are you trying to accomplish? I can suggest a safer approach.
"""
        
        # Execute command
        async with get_user_client(session_id) as client:
            await client.send_console_command(actual_server_id, command)
            
        return f"""
📟 **Console Command Executed**

**Command**: `{command}`
**Status**: ✅ Sent to server console
**Server ID**: `{actual_server_id}`

⏳ **Command is processing...**
📊 **Check Results**: Monitor server console or use "get server status"
🎮 **Player Impact**: Players may see changes immediately
"""
        
    except PterodactylAPIError as e:
        return f"❌ **Command Failed**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool  
async def list_user_servers(session_id: str = "dev_session") -> str:
    """List all servers the user has access to"""
    try:
        async with get_user_client(session_id) as client:
            servers = await client.get_servers()
            
        if not servers:
            return "❌ **No servers found** - Your account doesn't have access to any servers."
        
        server_list = []
        for server_data in servers:
            attrs = server_data.get("attributes", {})
            server_list.append(f"""
🖥️ **{attrs.get('name', 'Unknown')}**
   📋 ID: `{attrs.get('identifier', 'unknown')}`
   🎮 Game: {attrs.get('egg', {}).get('name', 'Unknown')}
   🟢 Status: {attrs.get('current_state', 'unknown').upper()}
   🌐 Node: {attrs.get('node', 'Unknown')}
""")
        
        return f"""
📋 **Your Servers** ({len(servers)} total)
{''.join(server_list)}

**Usage**: Specify server ID in commands or use "auto-detect" for first server
**Example**: "get server status server123" or just "get server status"
"""
        
    except PterodactylAPIError as e:
        return f"❌ **API Error**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

# Export tools list
tools = [
    get_server_status,
    restart_server,
    stop_server,
    start_server,
    send_server_command,
    list_user_servers,
]
```

#### Step 2: Update Agent with User Context
- [ ] **File**: `backend/app/langgraph/agent.py`
- [ ] **Action**: Add user context handling

```python
# REPLACE YOUR EXISTING call_model function with this enhanced version

async def call_model(state, config):
    """Enhanced model call with user context and safety checks"""
    
    # Extract user context from config
    system_prompt = config["configurable"].get("system", "")
    frontend_tools = config["configurable"].get("frontend_tools", [])
    user_session = config["configurable"].get("user_session", {})
    
    # Add user context to system prompt
    enhanced_system = f"""{system_prompt}

CURRENT USER CONTEXT:
- User ID: {user_session.get('user_id', 'unknown')}
- Available Servers: {len(user_session.get('accessible_servers', []))} servers
- Permissions: {', '.join(user_session.get('user_permissions', []))}

TOOL USAGE GUIDELINES:
- Always use session_id parameter: "{user_session.get('session_id', 'dev_session')}"
- For server operations, you can use "auto-detect" to use user's first server
- Always explain what operations will do before executing
- Ask for confirmation for potentially disruptive operations

SAFETY RULES:
- Server restarts/stops require explicit user confirmation
- Explain impact on players before executing commands
- Use server status checks to verify operations completed
- Guide users through troubleshooting step-by-step
"""
    
    messages = [SystemMessage(content=enhanced_system)] + state["messages"]
    model_with_tools = model.bind_tools(get_tool_defs(config))
    response = await model_with_tools.ainvoke(messages)
    
    return {"messages": [response]}
```

### ✅ Task 1.4: Update FastAPI Route with Authentication (Day 7)

#### Step 1: Create Authentication Endpoint
- [ ] **File**: `backend/app/api/__init__.py`
- [ ] **Action**: Create API directory

```python
# CREATE NEW FILE
# This marks the API directory as a Python package
```

- [ ] **File**: `backend/app/api/auth.py`
- [ ] **Action**: Create authentication endpoints

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from ..middleware.auth import authenticate_user_api_key
from ..services.user_manager import user_manager

router = APIRouter()

class AuthRequest(BaseModel):
    api_key: str

class AuthResponse(BaseModel):
    session_id: str
    user_id: str
    servers_count: int
    permissions: list
    expires_in: int  # seconds

@router.post("/authenticate", response_model=AuthResponse)
async def authenticate(request: AuthRequest):
    """Authenticate user with Pterodactyl API key"""
    try:
        session = await authenticate_user_api_key(request.api_key)
        
        return AuthResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            servers_count=len(session.servers),
            permissions=session.permissions,
            expires_in=7200  # 2 hours
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout(session_id: str):
    """Logout user and invalidate session"""
    if session_id in user_manager.active_sessions:
        del user_manager.active_sessions[session_id]
    
    return {"message": "Logged out successfully"}

@router.get("/session")
async def get_session_info(session_id: str):
    """Get current session information"""
    session = user_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return {
        "user_id": session.user_id,
        "permissions": session.permissions,
        "servers": session.servers,
        "expires_at": session.expires_at.isoformat(),
        "last_activity": session.last_activity.isoformat()
    }
```

#### Step 2: Update Chat Route with Authentication
- [ ] **File**: `backend/app/add_langgraph_route.py`
- [ ] **Action**: Add authentication to chat route

```python
# ADD THESE IMPORTS TO THE TOP OF YOUR EXISTING FILE
from .middleware.auth import get_current_user
from .services.user_manager import UserSession
from fastapi import Depends

# REPLACE YOUR EXISTING add_langgraph_route function with this enhanced version
def add_langgraph_route(app: FastAPI, graph, path: str):
    async def chat_completions(
        request: ChatRequest,
        user: UserSession = Depends(get_current_user)  # ADD THIS PARAMETER
    ):
        inputs = convert_to_langchain_messages(request.messages)

        async def run(controller: RunController):
            tool_calls = {}
            tool_calls_by_idx = {}
            try:
                async for msg, metadata in graph.astream(
                    {"messages": inputs},
                    {
                        "configurable": {
                            "system": request.system,
                            "frontend_tools": request.tools,
                            "user_session": {  # ADD USER CONTEXT
                                "user_id": user.user_id,
                                "session_id": user.session_id,
                                "accessible_servers": user.servers,
                                "user_permissions": user.permissions
                            }
                        }
                    },
                    stream_mode="messages",
                ):
                    # ... rest of your existing streaming logic remains the same
                    if isinstance(msg, ToolMessage):
                        tool_controller = tool_calls[msg.tool_call_id]
                        tool_controller.set_result(msg.content)

                    if isinstance(msg, AIMessageChunk) or isinstance(msg, AIMessage):
                        if msg.content:
                            controller.append_text(msg.content)

                        for chunk in msg.tool_call_chunks:
                            if not chunk["index"] in tool_calls_by_idx:
                                tool_controller = await controller.add_tool_call(
                                    chunk["name"], chunk["id"]
                                )
                                tool_calls_by_idx[chunk["index"]] = tool_controller
                                tool_calls[chunk["id"]] = tool_controller
                            else:
                                tool_controller = tool_calls_by_idx[chunk["index"]]

                            tool_controller.append_args_text(chunk["args"])
            except NodeInterrupt as e:
                if e.values and "messages" in e.values:
                    msg: AIMessage = e.values["messages"][-1]
                    for tool_call in msg.tool_calls:
                        tool_controller = await controller.add_tool_call(
                            tool_call["name"], tool_call["id"]
                        )
                        tool_controller.set_args(tool_call["args"])

        return DataStreamResponse(create_run(run))

    # Add the route
    app.add_api_route(path, chat_completions, methods=["POST"])
    
    # Also add authentication routes
    from .api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
```

#### Step 3: Update Server Setup
- [ ] **File**: `backend/app/server.py`
- [ ] **Action**: Add session cleanup and error handling

```python
# ADD THESE IMPORTS TO YOUR EXISTING server.py
from contextlib import asynccontextmanager
import asyncio
from .services.user_manager import user_manager

# ADD THIS LIFESPAN MANAGER BEFORE YOUR app = FastAPI() LINE
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting XGaming Server AI Assistant...")
    
    # Start session cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    cleanup_task.cancel()
    print("👋 Shutting down gracefully...")

async def periodic_cleanup():
    """Clean up expired sessions every 30 minutes"""
    while True:
        try:
            await asyncio.sleep(1800)  # 30 minutes
            user_manager.cleanup_expired_sessions()
            print(f"🧹 Cleaned up expired sessions. Active: {len(user_manager.active_sessions)}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"❌ Cleanup error: {e}")

# REPLACE YOUR app = FastAPI() line with:
app = FastAPI(lifespan=lifespan)

# ... rest of your existing server.py remains the same
```

---

## 📦 Week 2: Testing and Refinement

### ✅ Task 1.5: Integration Testing (Day 8-9)

#### Step 1: Create Test Suite
- [ ] **File**: `backend/tests/__init__.py`
- [ ] **Action**: Create tests directory

- [ ] **File**: `backend/tests/test_integration.py`
- [ ] **Action**: Create integration tests

```python
import pytest
import asyncio
from httpx import AsyncClient
from app.server import app
from app.services.user_manager import user_manager

@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def dev_session():
    """Create development session for testing"""
    return user_manager.create_session(
        user_id="test_user",
        api_key="test_api_key",
        permissions=["server.control", "server.files"],
        servers=["test_server_123"]
    )

class TestAuthentication:
    async def test_chat_requires_auth(self, test_client):
        """Test that chat endpoint requires authentication"""
        response = await test_client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "test"}]
        })
        assert response.status_code == 401

    async def test_dev_mode_bypass(self, test_client):
        """Test development mode authentication bypass"""
        response = await test_client.post("/api/chat", 
            headers={"X-Dev-Mode": "true"},
            json={
                "messages": [{"role": "user", "content": "get server status"}],
                "system": "You are a test assistant"
            }
        )
        assert response.status_code == 200

class TestTools:
    async def test_server_status_tool(self, test_client):
        """Test server status tool with mock data"""
        response = await test_client.post("/api/chat",
            headers={"X-Dev-Mode": "true"},
            json={
                "messages": [{"role": "user", "content": "What's my server status?"}],
                "system": "You are XGaming Server support assistant"
            }
        )
        
        assert response.status_code == 200
        # Response should be streaming, so we need to read the stream
        content = response.content.decode()
        assert "Server Status" in content or "server" in content.lower()

    async def test_server_restart_requires_confirmation(self, test_client):
        """Test that server restart asks for confirmation"""
        response = await test_client.post("/api/chat",
            headers={"X-Dev-Mode": "true"},
            json={
                "messages": [{"role": "user", "content": "restart my server"}],
                "system": "You are XGaming Server support assistant"
            }
        )
        
        assert response.status_code == 200
        content = response.content.decode()
        assert "confirmation" in content.lower() or "confirm" in content.lower()
```

#### Step 2: Manual Testing Checklist
- [ ] **Test Authentication**:
  - [ ] Try chat without authentication → Should get 401 error
  - [ ] Use X-Dev-Mode header → Should work with dev session
  - [ ] Test with invalid API key → Should get authentication error

- [ ] **Test Basic Tools**:
  - [ ] "What's my server status?" → Should return formatted status
  - [ ] "restart my server" → Should ask for confirmation  
  - [ ] "restart server with confirmation" → Should show restart message
  - [ ] "list my servers" → Should show available servers

#### Step 3: Load Testing
- [ ] **File**: `backend/load_test.py` (temporary)
- [ ] **Action**: Create simple load test

```python
# CREATE TEMPORARY LOAD TEST
import asyncio
import httpx
import time

async def test_concurrent_requests():
    """Test multiple concurrent chat requests"""
    async with httpx.AsyncClient() as client:
        tasks = []
        
        for i in range(10):  # 10 concurrent requests
            task = client.post(
                "http://localhost:8000/api/chat",
                headers={"X-Dev-Mode": "true"},
                json={
                    "messages": [{"role": "user", "content": f"test request {i}"}],
                    "system": "You are a test assistant"
                },
                timeout=30
            )
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        success_count = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        
        print(f"✅ {success_count}/10 requests successful")
        print(f"⏱️ Total time: {end_time - start_time:.2f}s")
        print(f"📊 Average time per request: {(end_time - start_time) / 10:.2f}s")

if __name__ == "__main__":
    asyncio.run(test_concurrent_requests())
```

- [ ] **Action**: Run load test
```bash
cd /var/www/aichat/backend
python load_test.py
```

### ✅ Task 1.6: Error Handling and Monitoring (Day 10)

#### Step 1: Add Comprehensive Error Handling
- [ ] **File**: `backend/app/middleware/error_handler.py`
- [ ] **Action**: Create error handling middleware

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/www/aichat/backend/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("xgaming-ai-assistant")

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled error in {request.method} {request.url}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again or contact support.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Log request
        logger.info(f"[{request_id}] {request.method} {request.url} - START")
        
        try:
            response = await call_next(request)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"[{request_id}] {request.method} {request.url} - {response.status_code} ({duration:.3f}s)")
            
            return response
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"[{request_id}] {request.method} {request.url} - ERROR ({duration:.3f}s): {str(e)}")
            raise
```

#### Step 2: Add Monitoring Endpoints
- [ ] **File**: `backend/app/api/monitoring.py`
- [ ] **Action**: Create health check and monitoring endpoints

```python
from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import asyncio
from ..services.user_manager import user_manager
from ..services.pterodactyl_client import PterodactylClient

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics
        active_sessions = len(user_manager.active_sessions)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": disk.free / (1024**3)
            },
            "application": {
                "active_sessions": active_sessions,
                "uptime_seconds": (datetime.utcnow() - datetime.utcnow()).total_seconds()  # Placeholder
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""
    active_sessions = len(user_manager.active_sessions)
    
    metrics = f"""
# HELP xgaming_active_sessions Number of active user sessions
# TYPE xgaming_active_sessions gauge
xgaming_active_sessions {active_sessions}

# HELP xgaming_health_status Health status of the application (1=healthy, 0=unhealthy)
# TYPE xgaming_health_status gauge
xgaming_health_status 1
"""
    
    return metrics
```

#### Step 3: Update Server with Monitoring
- [ ] **File**: `backend/app/server.py`
- [ ] **Action**: Add monitoring and error handling

```python
# ADD THESE IMPORTS TO YOUR EXISTING server.py
from .middleware.error_handler import ErrorHandlingMiddleware, RequestLoggingMiddleware
from .api.monitoring import router as monitoring_router

# ADD THESE LINES AFTER app = FastAPI(lifespan=lifespan):
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# ADD MONITORING ROUTES BEFORE add_langgraph_route
app.include_router(monitoring_router, prefix="/health", tags=["monitoring"])

# ... rest of your existing server.py remains the same
```

---

## 🎯 Phase 1 Success Criteria

### Testing Checklist
- [ ] **Authentication System**:
  - [ ] Users can authenticate with Pterodactyl API keys
  - [ ] Sessions are created and managed properly
  - [ ] Invalid keys are rejected with clear error messages
  - [ ] Sessions expire and clean up automatically

- [ ] **Core Server Tools Work**:
  - [ ] Server status shows real data from Pterodactyl API
  - [ ] Server restart/stop/start work with confirmations
  - [ ] Console commands execute safely with warnings
  - [ ] User can list their accessible servers

- [ ] **Security & Safety**:
  - [ ] Destructive operations require confirmation
  - [ ] Users can only access their own servers
  - [ ] Dangerous commands are blocked with warnings
  - [ ] API errors are handled gracefully

- [ ] **System Reliability**:
  - [ ] Health checks work and show system status
  - [ ] Errors are logged properly
  - [ ] Sessions clean up expired entries
  - [ ] Concurrent requests handle properly

### Performance Targets
- [ ] **Response Times**:
  - [ ] Server status: < 2 seconds
  - [ ] Server control actions: < 3 seconds  
  - [ ] Authentication: < 5 seconds
  - [ ] Console commands: < 2 seconds

- [ ] **Concurrent Usage**:
  - [ ] 10 concurrent users without issues
  - [ ] Session management scales properly
  - [ ] API rate limits respected

### Documentation Updates
- [ ] **Update README**:
  - [ ] Add authentication instructions
  - [ ] Document available tools and commands
  - [ ] Include troubleshooting guide
  - [ ] Add development setup instructions

---

## 🚀 Ready for Phase 2

After Phase 1 completion, you'll have:
- ✅ Real Pterodactyl API integration
- ✅ User authentication and session management
- ✅ Basic server control tools with safety mechanisms
- ✅ Error handling and monitoring
- ✅ Secure, scalable foundation for advanced features

**Next**: Phase 2 will add game-specific intelligence, advanced file operations, and smart troubleshooting capabilities.