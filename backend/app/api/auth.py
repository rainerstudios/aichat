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