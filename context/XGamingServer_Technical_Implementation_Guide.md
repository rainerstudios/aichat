# XGamingServer AI Bot - Technical Implementation Guide

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Frontend UI   │    │   FastAPI App    │    │   Pterodactyl API   │
│  (assistant-ui) │◄──►│  (LangGraph)     │◄──►│   (Game Servers)    │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Game Knowledge │
                       │     Modules      │
                       └──────────────────┘
```

---

## 🚀 Step 1: Project Setup & Foundation

### **1.1 Clone and Setup Base Template**

```bash
# Clone the template
git clone https://github.com/Yonom/assistant-ui-langgraph-fastapi.git xgaming-ai-bot
cd xgaming-ai-bot

# Install dependencies
pip install -r requirements.txt
npm install  # For frontend

# Add additional dependencies for our use case
pip install httpx aiofiles pydantic-settings python-multipart
```

### **1.2 Environment Configuration**

```python
# .env file
OPENAI_API_KEY=your_openai_key
PTERODACTYL_API_URL=https://panel.xgamingserver.com/api
PTERODACTYL_API_KEY=your_pterodactyl_key
DATABASE_URL=sqlite:///./bot_data.db
LOG_LEVEL=INFO
```

### **1.3 Enhanced Settings**

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    pterodactyl_api_url: str
    pterodactyl_api_key: str
    database_url: str = "sqlite:///./bot_data.db"
    
    # Game knowledge settings
    knowledge_base_path: str = "./knowledge"
    supported_games_config: str = "./config/games.yaml"
    
    # Security settings
    max_api_calls_per_minute: int = 60
    require_confirmation_for: list = ["restart", "stop", "delete", "reinstall"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🧠 Step 2: Core State Management with LangGraph

### **2.1 Enhanced State Schema**

```python
# app/models/state.py
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

class ServerBotState(TypedDict):
    # User context
    user_id: str
    session_id: str
    authenticated: bool
    user_permissions: List[str]
    
    # Server context
    server_id: Optional[str]
    server_info: Optional[Dict[str, Any]]
    game_type: Optional[str]
    game_version: Optional[str]
    
    # Conversation context
    current_intent: Optional[str]
    pending_action: Optional[Dict[str, Any]]
    confirmation_required: bool
    confirmation_details: Optional[Dict[str, Any]]
    
    # System context
    last_api_call: Optional[datetime]
    error_count: int
    conversation_history: List[Dict[str, Any]]
    
    # Results and responses
    last_response: Optional[str]
    api_results: Optional[Dict[str, Any]]
```

### **2.2 LangGraph Workflow Definition**

```python
# app/workflows/server_bot.py
from langgraph.graph import StateGraph, END
from app.models.state import ServerBotState
from app.nodes import *

def create_server_bot_workflow():
    # Initialize the state graph
    workflow = StateGraph(ServerBotState)
    
    # Core nodes
    workflow.add_node("authenticate_user", authenticate_user_node)
    workflow.add_node("detect_intent", detect_intent_node)
    workflow.add_node("load_server_context", load_server_context_node)
    workflow.add_node("load_game_knowledge", load_game_knowledge_node)
    
    # Action nodes
    workflow.add_node("server_control", server_control_node)
    workflow.add_node("file_operations", file_operations_node)
    workflow.add_node("configuration_management", config_management_node)
    workflow.add_node("backup_operations", backup_operations_node)
    workflow.add_node("user_management", user_management_node)
    
    # Safety and confirmation
    workflow.add_node("safety_check", safety_check_node)
    workflow.add_node("request_confirmation", confirmation_request_node)
    workflow.add_node("execute_action", action_execution_node)
    
    # Response generation
    workflow.add_node("generate_response", response_generation_node)
    workflow.add_node("escalate_to_support", support_escalation_node)
    
    # Define the flow
    workflow.set_entry_point("authenticate_user")
    
    # Authentication flow
    workflow.add_conditional_edges(
        "authenticate_user",
        lambda state: "detect_intent" if state.get("authenticated") else END
    )
    
    # Intent detection and routing
    workflow.add_conditional_edges(
        "detect_intent",
        route_by_intent,
        {
            "server_info": "load_server_context",
            "server_control": "safety_check",
            "file_ops": "file_operations",
            "config": "configuration_management",
            "backup": "backup_operations",
            "users": "user_management",
            "help": "generate_response",
            "escalate": "escalate_to_support"
        }
    )
    
    # Safety check routing
    workflow.add_conditional_edges(
        "safety_check",
        lambda state: "request_confirmation" if state.get("confirmation_required") else "execute_action"
    )
    
    # Confirmation flow
    workflow.add_edge("request_confirmation", "execute_action")
    workflow.add_edge("execute_action", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()
```

---

## 🔌 Step 3: Pterodactyl API Integration

### **3.1 API Client Implementation**

```python
# app/services/pterodactyl_client.py
import httpx
from typing import Dict, List, Optional, Any
from app.core.config import settings
from app.models.exceptions import PterodactylAPIError

class PterodactylClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.pterodactyl_api_key
        self.base_url = settings.pterodactyl_api_url
        self.session = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "Application/vnd.pterodactyl.v1+json"
            }
        )
    
    # Server Management
    async def get_server_details(self, server_id: str) -> Dict[str, Any]:
        """Get detailed server information"""
        try:
            response = await self.session.get(f"/client/servers/{server_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise PterodactylAPIError(f"Failed to get server details: {e}")
    
    async def get_server_resources(self, server_id: str) -> Dict[str, Any]:
        """Get server resource usage"""
        response = await self.session.get(f"/client/servers/{server_id}/resources")
        response.raise_for_status()
        return response.json()
    
    async def send_power_action(self, server_id: str, action: str) -> Dict[str, Any]:
        """Send power signal (start, stop, restart, kill)"""
        payload = {"signal": action}
        response = await self.session.post(
            f"/client/servers/{server_id}/power", 
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def send_console_command(self, server_id: str, command: str) -> Dict[str, Any]:
        """Send command to server console"""
        payload = {"command": command}
        response = await self.session.post(
            f"/client/servers/{server_id}/command",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # File Operations
    async def list_files(self, server_id: str, directory: str = "/") -> List[Dict]:
        """List files in directory"""
        params = {"directory": directory}
        response = await self.session.get(
            f"/client/servers/{server_id}/files/list",
            params=params
        )
        response.raise_for_status()
        return response.json()["data"]
    
    async def get_file_contents(self, server_id: str, file_path: str) -> str:
        """Get file contents"""
        params = {"file": file_path}
        response = await self.session.get(
            f"/client/servers/{server_id}/files/contents",
            params=params
        )
        response.raise_for_status()
        return response.text
    
    async def write_file(self, server_id: str, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to file"""
        params = {"file": file_path}
        response = await self.session.post(
            f"/client/servers/{server_id}/files/write",
            params=params,
            content=content,
            headers={"Content-Type": "text/plain"}
        )
        response.raise_for_status()
        return response.json()
    
    # Backup Operations
    async def create_backup(self, server_id: str, name: str = None) -> Dict[str, Any]:
        """Create server backup"""
        payload = {}
        if name:
            payload["name"] = name
        
        response = await self.session.post(
            f"/client/servers/{server_id}/backups",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def list_backups(self, server_id: str) -> List[Dict]:
        """List all backups"""
        response = await self.session.get(f"/client/servers/{server_id}/backups")
        response.raise_for_status()
        return response.json()["data"]
    
    # Database Operations
    async def list_databases(self, server_id: str) -> List[Dict]:
        """List server databases"""
        response = await self.session.get(f"/client/servers/{server_id}/databases")
        response.raise_for_status()
        return response.json()["data"]
    
    async def create_database(self, server_id: str, name: str, remote: str = "%") -> Dict[str, Any]:
        """Create new database"""
        payload = {
            "database": name,
            "remote": remote
        }
        response = await self.session.post(
            f"/client/servers/{server_id}/databases",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # Startup Variables
    async def get_startup_variables(self, server_id: str) -> Dict[str, Any]:
        """Get server startup variables"""
        response = await self.session.get(f"/client/servers/{server_id}/startup")
        response.raise_for_status()
        return response.json()
    
    async def update_startup_variable(self, server_id: str, key: str, value: str) -> Dict[str, Any]:
        """Update startup variable"""
        payload = {
            "key": key,
            "value": value
        }
        response = await self.session.put(
            f"/client/servers/{server_id}/startup/variable",
            json=payload
        )
        response.raise_for_status()
        return response.json()
```

---

## 🎮 Step 4: Game Knowledge System

### **4.1 Base Game Module**

```python
# app/game_modules/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class GameSetting(BaseModel):
    name: str
    type: str  # string, integer, boolean, enum
    description: str
    default_value: Any
    possible_values: Optional[List[Any]] = None
    requires_restart: bool = False

class GameModule(ABC):
    def __init__(self):
        self.name = ""
        self.settings = []
        self.common_issues = {}
        self.optimization_tips = []
    
    @abstractmethod
    async def detect_game_type(self, server_info: Dict) -> bool:
        """Detect if this module applies to the server"""
        pass
    
    @abstractmethod
    async def get_recommended_settings(self, scenario: str) -> Dict[str, Any]:
        """Get recommended settings for scenario (pvp, pve, creative, etc.)"""
        pass
    
    @abstractmethod
    async def validate_configuration(self, config: Dict) -> List[str]:
        """Validate configuration and return warnings/errors"""
        pass
    
    async def troubleshoot_issue(self, issue_description: str) -> str:
        """Provide troubleshooting guidance"""
        # Use AI to match issue with known solutions
        pass
    
    async def get_optimization_suggestions(self, server_resources: Dict) -> List[str]:
        """Get performance optimization suggestions"""
        pass
```

### **4.2 Minecraft Module Example**

```python
# app/game_modules/minecraft.py
from .base import GameModule, GameSetting
from typing import Dict, List, Any

class MinecraftModule(GameModule):
    def __init__(self):
        super().__init__()
        self.name = "Minecraft"
        self.settings = [
            GameSetting(
                name="server-name",
                type="string",
                description="Server name displayed in server list",
                default_value="A Minecraft Server"
            ),
            GameSetting(
                name="gamemode",
                type="enum",
                description="Default game mode for players",
                default_value="survival",
                possible_values=["survival", "creative", "adventure", "spectator"],
                requires_restart=True
            ),
            GameSetting(
                name="difficulty",
                type="enum",
                description="Game difficulty",
                default_value="easy",
                possible_values=["peaceful", "easy", "normal", "hard"]
            ),
            GameSetting(
                name="max-players",
                type="integer",
                description="Maximum number of players",
                default_value=20
            )
        ]
        
        self.common_issues = {
            "can't connect": "Check if server is online and ports are open",
            "lag": "Check TPS, reduce view distance, optimize plugins",
            "crash": "Check logs for errors, update plugins, increase RAM"
        }
    
    async def detect_game_type(self, server_info: Dict) -> bool:
        """Detect Minecraft server"""
        egg_name = server_info.get("egg", {}).get("name", "").lower()
        return any(keyword in egg_name for keyword in ["minecraft", "spigot", "paper", "forge"])
    
    async def get_recommended_settings(self, scenario: str) -> Dict[str, Any]:
        """Get scenario-based settings"""
        scenarios = {
            "pvp": {
                "pvp": "true",
                "difficulty": "hard",
                "spawn-protection": "0",
                "keep-inventory": "false"
            },
            "creative": {
                "gamemode": "creative",
                "spawn-monsters": "false",
                "pvp": "false",
                "difficulty": "peaceful"
            },
            "survival": {
                "gamemode": "survival",
                "difficulty": "normal",
                "pvp": "false",
                "keep-inventory": "false"
            }
        }
        return scenarios.get(scenario, {})
    
    async def validate_configuration(self, config: Dict) -> List[str]:
        """Validate Minecraft configuration"""
        warnings = []
        
        if config.get("max-players", 0) > 100:
            warnings.append("High player count may cause performance issues")
        
        if config.get("view-distance", 10) > 16:
            warnings.append("High view distance increases RAM usage significantly")
        
        return warnings
    
    # Minecraft-specific methods
    async def manage_whitelist(self, action: str, player: str = None) -> str:
        """Manage whitelist operations"""
        if action == "enable":
            return "whitelist on"
        elif action == "disable":
            return "whitelist off"
        elif action == "add" and player:
            return f"whitelist add {player}"
        elif action == "remove" and player:
            return f"whitelist remove {player}"
    
    async def manage_operators(self, action: str, player: str = None) -> str:
        """Manage operator permissions"""
        if action == "add" and player:
            return f"op {player}"
        elif action == "remove" and player:
            return f"deop {player}"
    
    async def ban_player(self, player: str, reason: str = None) -> str:
        """Ban a player"""
        command = f"ban {player}"
        if reason:
            command += f" {reason}"
        return command
```

### **4.3 Game Module Manager**

```python
# app/services/game_manager.py
from typing import Dict, Optional
from app.game_modules.base import GameModule
from app.game_modules.minecraft import MinecraftModule
from app.game_modules.rust import RustModule
from app.game_modules.generic import GenericModule

class GameModuleManager:
    def __init__(self):
        self.modules = {
            "minecraft": MinecraftModule(),
            "rust": RustModule(),
            # Add more game modules
        }
        self.generic_module = GenericModule()
    
    async def detect_game_module(self, server_info: Dict) -> GameModule:
        """Detect and return appropriate game module"""
        for module_name, module in self.modules.items():
            if await module.detect_game_type(server_info):
                return module
        
        # Return generic module if no specific match
        return self.generic_module
    
    async def get_module_by_name(self, game_name: str) -> Optional[GameModule]:
        """Get module by game name"""
        return self.modules.get(game_name.lower())
```

---

## 🔍 Step 5: LangGraph Node Implementation

### **5.1 Core Nodes**

```python
# app/nodes/core_nodes.py
from app.models.state import ServerBotState
from app.services.pterodactyl_client import PterodactylClient
from app.services.game_manager import GameModuleManager
from app.services.intent_detector import IntentDetector

async def authenticate_user_node(state: ServerBotState) -> ServerBotState:
    """Authenticate user and load permissions"""
    # Implementation for user authentication
    # This would integrate with your auth system
    state["authenticated"] = True
    state["user_permissions"] = ["server.control", "server.files", "server.config"]
    return state

async def detect_intent_node(state: ServerBotState) -> ServerBotState:
    """Detect user intent from message"""
    intent_detector = IntentDetector()
    last_message = state["conversation_history"][-1]["content"]
    
    intent = await intent_detector.detect_intent(last_message)
    state["current_intent"] = intent
    
    return state

async def load_server_context_node(state: ServerBotState) -> ServerBotState:
    """Load server information and context"""
    if not state.get("server_id"):
        # Extract server ID from conversation or user context
        pass
    
    client = PterodactylClient()
    server_info = await client.get_server_details(state["server_id"])
    
    state["server_info"] = server_info
    return state

async def load_game_knowledge_node(state: ServerBotState) -> ServerBotState:
    """Load appropriate game module"""
    game_manager = GameModuleManager()
    game_module = await game_manager.detect_game_module(state["server_info"])
    
    state["game_type"] = game_module.name
    # Store game module reference (in practice, you'd store identifier)
    
    return state

async def safety_check_node(state: ServerBotState) -> ServerBotState:
    """Check if action requires confirmation"""
    intent = state.get("current_intent")
    destructive_actions = ["restart", "stop", "delete", "reinstall", "file_delete"]
    
    if intent in destructive_actions:
        state["confirmation_required"] = True
        state["confirmation_details"] = {
            "action": intent,
            "warning": f"This will {intent} your server and may disconnect players."
        }
    else:
        state["confirmation_required"] = False
    
    return state
```

### **5.2 Action Nodes**

```python
# app/nodes/action_nodes.py
from app.models.state import ServerBotState
from app.services.pterodactyl_client import PterodactylClient

async def server_control_node(state: ServerBotState) -> ServerBotState:
    """Handle server power operations"""
    client = PterodactylClient()
    action = state["pending_action"]["type"]
    server_id = state["server_id"]
    
    try:
        if action == "restart":
            result = await client.send_power_action(server_id, "restart")
        elif action == "stop":
            result = await client.send_power_action(server_id, "stop")
        elif action == "start":
            result = await client.send_power_action(server_id, "start")
        
        state["api_results"] = result
        state["last_response"] = f"Server {action} initiated successfully."
        
    except Exception as e:
        state["last_response"] = f"Failed to {action} server: {str(e)}"
    
    return state

async def file_operations_node(state: ServerBotState) -> ServerBotState:
    """Handle file operations"""
    client = PterodactylClient()
    action = state["pending_action"]
    server_id = state["server_id"]
    
    try:
        if action["type"] == "list_files":
            files = await client.list_files(server_id, action.get("directory", "/"))
            state["api_results"] = files
            
        elif action["type"] == "read_file":
            content = await client.get_file_contents(server_id, action["file_path"])
            state["api_results"] = {"content": content}
            
        elif action["type"] == "write_file":
            await client.write_file(server_id, action["file_path"], action["content"])
            state["last_response"] = "File updated successfully."
            
    except Exception as e:
        state["last_response"] = f"File operation failed: {str(e)}"
    
    return state

async def configuration_management_node(state: ServerBotState) -> ServerBotState:
    """Handle configuration changes"""
    client = PterodactylClient()
    action = state["pending_action"]
    server_id = state["server_id"]
    
    try:
        if action["type"] == "update_startup_variable":
            result = await client.update_startup_variable(
                server_id, 
                action["key"], 
                action["value"]
            )
            state["api_results"] = result
            state["last_response"] = f"Updated {action['key']} to {action['value']}"
            
    except Exception as e:
        state["last_response"] = f"Configuration update failed: {str(e)}"
    
    return state
```

---

## 🤖 Step 6: AI Response Generation

### **6.1 Response Generation with Context**

```python
# app/services/response_generator.py
from openai import AsyncOpenAI
from app.models.state import ServerBotState
from app.core.config import settings

class ResponseGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_response(self, state: ServerBotState) -> str:
        """Generate contextual response based on state"""
        
        # Build context from state
        context = self._build_context(state)
        
        # Create system prompt
        system_prompt = self._create_system_prompt(state)
        
        # Generate response
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def _build_context(self, state: ServerBotState) -> str:
        """Build context string from state"""
        context_parts = []
        
        # Add server info
        if state.get("server_info"):
            server = state["server_info"]
            context_parts.append(f"Server: {server.get('name', 'Unknown')}")
            context_parts.append(f"Game: {state.get('game_type', 'Unknown')}")
            context_parts.append(f"Status: {server.get('status', 'Unknown')}")
        
        # Add recent conversation
        if state.get("conversation_history"):
            last_msg = state["conversation_history"][-1]
            context_parts.append(f"User Request: {last_msg['content']}")
        
        # Add API results if available
        if state.get("api_results"):
            context_parts.append(f"API Results: {state['api_results']}")
        
        # Add any errors or warnings
        if state.get("last_response"):
            context_parts.append(f"Last Response: {state['last_response']}")
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self, state: ServerBotState) -> str:
        """Create system prompt based on current context"""
        game_type = state.get("game_type", "Generic")
        
        prompt = f"""You are an expert AI assistant for XGamingServer, specializing in {game_type} server management.

Your capabilities:
- Server control (start/stop/restart)
- File management and configuration
- Game-specific optimization
- Troubleshooting and support
- User and permission management

Current context:
- User is authenticated with permissions: {state.get('user_permissions', [])}
- Current server game type: {game_type}
- Action requires confirmation: {state.get('confirmation_required', False)}

Guidelines:
1. Always be helpful and provide clear explanations
2. For destructive actions, ask for explicit confirmation
3. Provide game-specific advice when relevant
4. Escalate complex issues to human support when needed
5. Keep responses concise but informative

If you need to perform an action, explain what will happen before doing it.
"""
        return prompt
```

---

## 🔗 Step 7: FastAPI Integration

### **7.1 Enhanced API Routes**

```python
# app/api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from app.workflows.server_bot import create_server_bot_workflow
from app.models.state import ServerBotState
from app.services.auth import get_current_user

router = APIRouter()
workflow = create_server_bot_workflow()

@router.post("/chat")
async def chat_endpoint(
    message: str,
    session_id: str,
    user=Depends(get_current_user)
):
    """Main chat endpoint"""
    try:
        # Initialize or get existing state
        initial_state = ServerBotState(
            user_id=user.id,
            session_id=session_id,
            authenticated=True,
            user_permissions=user.permissions,
            conversation_history=[{"role": "user", "content": message}],
            error_count=0
        )
        
        # Run the workflow
        final_state = await workflow.ainvoke(initial_state)
        
        return {
            "response": final_state.get("last_response"),
            "requires_confirmation": final_state.get("confirmation_required", False),
            "confirmation_details": final_state.get("confirmation_details"),
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm-action")
async def confirm_action(
    session_id: str,
    confirmed: bool,
    user=Depends(get_current_user)
):
    """Handle action confirmation"""
    if confirmed:
        # Execute the pending action
        # This would resume the workflow from confirmation point
        pass
    else:
        # Cancel the action
        return {"response": "Action cancelled.", "session_id": session_id}

@router.get("/server/{server_id}/status")
async def get_server_status(
    server_id: str,
    user=Depends(get_current_user)
):
    """Get quick server status"""
    from app.services.pterodactyl_client import PterodactylClient
    
    client = PterodactylClient()
    try:
        server_info = await client.get_server_details(server_id)
        resources = await client.get_server_resources(server_id)
        
        return {
            "status": server_info.get("status"),
            "players": resources.get("players", 0),
            "cpu_usage": resources.get("cpu_absolute"),
            "memory_usage": resources.get("memory_bytes"),
            "disk_usage": resources.get("disk_bytes")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🎨 Step 8: Frontend Integration

### **8.1 Enhanced Chat Component**

```typescript
// frontend/src/components/ServerBotChat.tsx
import { useAssistant } from "@assistant-ui/react";
import { useState } from "react";

interface ServerBotChatProps {
  serverId?: string;
  userId: string;
}

export function ServerBotChat({ serverId, userId }: ServerBotChatProps) {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [pendingConfirmation, setPendingConfirmation] = useState<any>(null);
  
  const { messages, input, setInput, sendMessage } = useAssistant({
    api: "/api/chat",
    body: {
      session_id: sessionId,
      server_id: serverId
    }
  });

  const handleSendMessage = async () => {
    const response = await sendMessage();
    
    if (response.requires_confirmation) {
      setPendingConfirmation(response.confirmation_details);
    }
  };

  const handleConfirmAction = async (confirmed: boolean) => {
    const response = await fetch("/api/confirm-action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        confirmed
      })
    });
    
    const result = await response.json();
    setPendingConfirmation(null);
    
    // Add result to messages
    addMessage({ role: "assistant", content: result.response });
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            {message.content}
          </div>
        ))}
      </div>
      
      {pendingConfirmation && (
        <div className="confirmation-dialog">
          <h3>Confirm Action</h3>
          <p>{pendingConfirmation.warning}</p>
          <button onClick={() => handleConfirmAction(true)}>
            Confirm
          </button>
          <button onClick={() => handleConfirmAction(false)}>
            Cancel
          </button>
        </div>
      )}
      
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything about your server..."
          onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
        />
        <button onClick={handleSendMessage}>Send</button>
      </div>
    </div>
  );
}
```

---

## 🚀 Step 9: Deployment & Testing

### **9.1 Docker Configuration**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Install frontend dependencies and build
RUN npm install && npm run build

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **9.2 Docker Compose for Development**

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PTERODACTYL_API_URL=${PTERODACTYL_API_URL}
      - PTERODACTYL_API_KEY=${PTERODACTYL_API_KEY}
    volumes:
      - ./app:/app/app
      - ./knowledge:/app/knowledge
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: xgaming_bot
      POSTGRES_USER: bot_user
      POSTGRES_PASSWORD: bot_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

## 🧪 Step 10: Testing Strategy

### **10.1 Unit Tests**

```python
# tests/test_game_modules.py
import pytest
from app.game_modules.minecraft import MinecraftModule

@pytest.mark.asyncio
async def test_minecraft_detection():
    module = MinecraftModule()
    
    # Test positive detection
    server_info = {
        "egg": {"name": "Minecraft Java Server"}
    }
    assert await module.detect_game_type(server_info) == True
    
    # Test negative detection
    server_info = {
        "egg": {"name": "Rust Server"}
    }
    assert await module.detect_game_type(server_info) == False

@pytest.mark.asyncio
async def test_minecraft_recommendations():
    module = MinecraftModule()
    
    pvp_settings = await module.get_recommended_settings("pvp")
    assert pvp_settings["pvp"] == "true"
    assert pvp_settings["difficulty"] == "hard"
```

### **10.2 Integration Tests**

```python
# tests/test_workflows.py
import pytest
from app.workflows.server_bot import create_server_bot_workflow
from app.models.state import ServerBotState

@pytest.mark.asyncio
async def test_server_control_workflow():
    workflow = create_server_bot_workflow()
    
    initial_state = ServerBotState(
        user_id="test_user",
        session_id="test_session",
        authenticated=True,
        server_id="test_server",
        current_intent="restart",
        conversation_history=[{"role": "user", "content": "restart my server"}]
    )
    
    final_state = await workflow.ainvoke(initial_state)
    
    assert final_state["confirmation_required"] == True
    assert "restart" in final_state["confirmation_details"]["action"]
```

---

## 📈 Performance Optimization

### **11.1 Caching Strategy**

```python
# app/services/cache.py
import redis
import json
from typing import Any, Optional

class CacheService:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    async def get_server_cache(self, server_id: str) -> Optional[dict]:
        """Get cached server information"""
        cached = self.redis_client.get(f"server:{server_id}")
        return json.loads(cached) if cached else None
    
    async def set_server_cache(self, server_id: str, data: dict, ttl: int = 300):
        """Cache server information for 5 minutes"""
        self.redis_client.setex(
            f"server:{server_id}", 
            ttl, 
            json.dumps(data)
        )
    
    async def get_game_knowledge_cache(self, game_type: str) -> Optional[dict]:
        """Get cached game knowledge"""
        cached = self.redis_client.get(f"game:{game_type}")
        return json.loads(cached) if cached else None
```

---

## 🎯 Development Timeline

### **Week 1-2: Foundation**
1. ✅ Set up assistant-ui-langgraph-fastapi template
2. ✅ Basic Pterodactyl API integration
3. ✅ Simple server status and control
4. ✅ Basic conversation flow

### **Week 3-4: Core Features**
1. ✅ File operations integration
2. ✅ Safety confirmation workflows
3. ✅ Game detection system
4. ✅ Minecraft module implementation

### **Week 5-6: Expansion**
1. ✅ Add 5 more game modules
2. ✅ Backup and database operations
3. ✅ User management features
4. ✅ Enhanced error handling

### **Week 7-8: Polish & Testing**
1. ✅ Comprehensive testing
2. ✅ Performance optimization
3. ✅ Documentation
4. ✅ Deployment preparation

---

This implementation leverages the assistant-ui-langgraph-fastapi template to handle the complex conversation flows while providing deep integration with your Pterodactyl panel and game-specific knowledge. The modular design allows for easy expansion as you add more games and features.
