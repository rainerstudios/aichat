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
    Create development session using real API key from environment
    """
    from datetime import datetime, timedelta
    import os
    
    # Check if session already exists
    existing_session = user_manager.get_session("admin_session")
    if existing_session:
        return existing_session
    
    # Use the client API key from environment (client keys have server access)
    real_api_key = os.getenv("PTERODACTYL_CLIENT_API_KEY", os.getenv("PTERODACTYL_DEFAULT_API_KEY", "dev_api_key"))
    
    # Create session using user_manager to ensure it's properly stored
    session_id = user_manager.create_session(
        user_id="admin_user",
        api_key=real_api_key,
        permissions=["server.control", "server.files", "server.config", "server.admin"],
        servers=[]  # Empty means access to all servers
    )
    
    # Override the session_id to be predictable for dev mode
    session = user_manager.get_session(session_id)
    if session:
        # Remove the old session and create a new one with fixed ID
        del user_manager.active_sessions[session_id]
        session.session_id = "admin_session"
        user_manager.active_sessions["admin_session"] = session
    
    return user_manager.get_session("admin_session")

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