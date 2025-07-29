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
    game_type: Optional[str]
