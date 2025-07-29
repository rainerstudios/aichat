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