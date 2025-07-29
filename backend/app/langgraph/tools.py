from langchain_core.tools import tool
from typing import Dict, List, Optional, Any
import asyncio
from ..services.pterodactyl_client import PterodactylClient, PterodactylAPIError
from ..services.pterodactyl_admin_client import PterodactylAdminClient, create_pterodactyl_admin_client
from ..services.user_manager import user_manager
from ..services.cloudflare_autorag import create_autorag_service, format_autorag_response
from ..services.cache_service import get_cache
from ..services.request_deduplicator import get_deduplicator
from ..services.local_docs_fallback import get_local_docs_fallback
import json

# Game detection patterns based on Pterodactyl's gameImageMapping.ts
def detect_game_type(egg_name: str = "", docker_image: str = "", variables: list = None) -> str:
    """Enhanced game detection using Pterodactyl's pattern matching system"""
    import re
    
    # Search texts - include variables
    search_texts = [egg_name.lower(), docker_image.lower()]
    
    # Add variable names and values to search
    if variables:
        for var in variables:
            if isinstance(var, dict) and 'attributes' in var:
                attrs = var['attributes']
                var_name = attrs.get('name', '').lower()
                var_desc = attrs.get('description', '').lower()
                env_var = attrs.get('env_variable', '').lower()
                
                search_texts.extend([var_name, var_desc, env_var])
                
                # Special handling for Minecraft version variables
                if 'minecraft' in var_name or 'minecraft' in var_desc or 'minecraft' in env_var:
                    return "Minecraft"
    
    # Game definitions with patterns (ordered by priority)
    game_patterns = [
        # Minecraft variants (highest priority)
        {
            "name": "Minecraft",
            "patterns": [
                r'\b(minecraft|mc)\b',
                r'\b(paper|spigot|bukkit|forge|fabric|vanilla|purpur|quilt)\b',
                r'\b(craftbukkit|mohist|magma|arclight)\b'
            ],
            "priority": 10
        },
        {
            "name": "Arma Reforger",
            "patterns": [r'\barma\s+reforger\b', r'reforger'],
            "priority": 9
        },
        # Other popular games
        {
            "name": "Counter-Strike",
            "patterns": [
                r'\b(counter[-\s]?strike|cs2?|csgo)\b',
                r'\b(source|global\s+offensive)\b'
            ],
            "priority": 8
        },
        {
            "name": "Rust",
            "patterns": [r'\brust\b'],
            "priority": 8
        },
        {
            "name": "ARK: Survival Evolved",
            "patterns": [
                r'\bark(\s+(survival(\s+evolved)?)?)?',
                r'\bsurvival\s+evolved\b'
            ],
            "priority": 7
        },
        {
            "name": "Valheim",
            "patterns": [r'\bvalheim\b'],
            "priority": 7
        },
        {
            "name": "Palworld",
            "patterns": [r'\bpalworld\b'],
            "priority": 7
        },
        {
            "name": "DayZ",
            "patterns": [r'\bdayz?\b'],
            "priority": 7
        },
        {
            "name": "Garry's Mod",
            "patterns": [
                r'\b(gmod|garry\'?s?\s+mod)\b',
                r'\bgarrysmod\b'
            ],
            "priority": 6
        },
        {
            "name": "Terraria",
            "patterns": [
                r'\bterraria\b',
                r'\btshock\b'
            ],
            "priority": 6
        },
        {
            "name": "FiveM",
            "patterns": [
                r'\bfive\s*m\b',
                r'\bfivem\b',
                r'\bgta\s*(5|v|rp)\b'
            ],
            "priority": 6
        },
        # Generic patterns
        {
            "name": "Discord Bot",
            "patterns": [
                r'\bdiscord\b.*\bbot\b',
                r'\bbot\b.*\bdiscord\b'
            ],
            "priority": 3
        },
        {
            "name": "Node.js Application",
            "patterns": [
                r'\bnode(\.?js)?\b',
                r'\bjavascript\b',
                r'\bnpm\b'
            ],
            "priority": 2
        },
        {
            "name": "Python Application",
            "patterns": [r'\bpython\b'],
            "priority": 2
        }
    ]
    
    best_match = None
    highest_priority = -1
    
    # Check each game definition
    for game in game_patterns:
        for search_text in search_texts:
            if not search_text:
                continue
                
            # Check if any pattern matches
            for pattern in game["patterns"]:
                if re.search(pattern, search_text, re.IGNORECASE):
                    if game["priority"] > highest_priority:
                        best_match = game["name"]
                        highest_priority = game["priority"]
                        break
    
    # For Minecraft, add variant info
    if best_match == "Minecraft":
        for search_text in search_texts:
            if "paper" in search_text:
                return "Minecraft (Paper)"
            elif "spigot" in search_text:
                return "Minecraft (Spigot)"
            elif "forge" in search_text:
                return "Minecraft (Forge)"
            elif "fabric" in search_text:
                return "Minecraft (Fabric)"
            elif "vanilla" in search_text:
                return "Minecraft (Vanilla)"
            elif "bukkit" in search_text:
                return "Minecraft (Bukkit)"
            elif "purpur" in search_text:
                return "Minecraft (Purpur)"
            elif "quilt" in search_text:
                return "Minecraft (Quilt)"
    
    return best_match or "Unknown"

# Helper function to get admin client (centralized)
def get_admin_client() -> PterodactylAdminClient:
    """Get Pterodactyl admin client for centralized management"""
    return create_pterodactyl_admin_client()

# Helper function to extract user context from iframe/state
def get_user_context_from_state(state: dict) -> tuple[int, str]:
    """Extract pterodactyl_user_id and current_server_id from agent state"""
    pterodactyl_user_id = state.get("pterodactyl_user_id")
    current_server_id = state.get("current_server_id")
    
    if not pterodactyl_user_id:
        raise ValueError("No Pterodactyl user ID found in context - iframe integration issue")
    
    return int(pterodactyl_user_id), current_server_id

# Helper function to detect server from context
async def detect_server_id(pterodactyl_user_id: int, server_hint: str = None) -> str:
    """Auto-detect server ID from user context using admin API"""
    admin_client = get_admin_client()
    
    # If user specified a server, verify they own it
    if server_hint and server_hint != "auto-detect":
        if await admin_client.verify_user_owns_server(pterodactyl_user_id, server_hint):
            return server_hint
        else:
            raise ValueError(f"You don't have access to server '{server_hint}' or it doesn't exist")
    
    # Auto-detect: use first available server
    async with admin_client:
        user_servers = await admin_client.get_user_servers(pterodactyl_user_id)
        if user_servers:
            return user_servers[0].get("uuid", user_servers[0].get("identifier", ""))
    
    raise ValueError("No servers found for your account")

@tool
async def query_documentation(query: str, game_type: str = None, **kwargs) -> str:
    """
    Query documentation for server management, game-specific guides, and troubleshooting information.
    This searches through comprehensive documentation from Pterodactyl, game guides, and server management resources.
    Use this tool for ANY questions about:
    - Server setup and configuration
    - Game-specific settings and mods
    - Troubleshooting server issues
    - Best practices and guides
    """
    try:
        # Validate input
        if not query or len(query.strip()) == 0:
            return "Please provide a specific question to search the documentation."
        
        # Limit query length to prevent issues
        if len(query) > 500:
            query = query[:500] + "..."
        
        # Check cache first for performance improvement
        cache = get_cache()
        cached_response = await cache.get(query, game_type)
        if cached_response:
            return f"{cached_response}\n\n*[Cached response for faster performance]*"
        
        # Use deduplicator to prevent multiple identical queries
        deduplicator = get_deduplicator()
        
        async def _execute_query():
            async with create_autorag_service() as autorag:
                # Build enhanced query with context (but keep it concise)
                enhanced_query = query.strip()
                
                # Add game type context if provided
                if game_type and game_type != "Unknown":
                    enhanced_query = f"Game: {game_type}\n\nQuestion: {enhanced_query}"
                
                response = await autorag.query(
                    question=enhanced_query,
                    max_results=3  # Reduced to prevent large responses
                )
                
                formatted_response = format_autorag_response(response)
                
                # Ensure response isn't empty
                if not formatted_response or formatted_response.strip() == "No answer found":
                    return "I couldn't find specific information about that in the documentation. Could you rephrase your question or be more specific?"
                
                # Cache the successful response
                await cache.set(query, formatted_response, game_type)
                
                return formatted_response
        
        # Execute with deduplication
        return await deduplicator.deduplicate(query, game_type or "generic", _execute_query)
            
    except Exception as e:
        error_msg = str(e)
        print(f"Documentation query error: {error_msg}")  # Log for debugging
        
        # Try local docs fallback when AutoRAG fails
        try:
            local_fallback = get_local_docs_fallback()
            fallback_result = await local_fallback.search_local_docs(query, game_type)
            
            if fallback_result:
                # Cache the fallback result too
                cache = get_cache()
                await cache.set(query, fallback_result, game_type)
                return fallback_result
        except Exception as fallback_error:
            print(f"Local docs fallback also failed: {fallback_error}")
        
        # Final fallback to general error messages
        if "timeout" in error_msg.lower():
            return "The documentation search timed out. Please try a simpler question or try again."
        elif "404" in error_msg or "not found" in error_msg.lower():
            return "Documentation service is currently unavailable. I can try to answer from my general knowledge."
        elif "autorag" in error_msg.lower():
            return "The documentation service is experiencing issues. I'll answer based on my general knowledge about server management."
        else:
            return "I encountered an issue searching the documentation. Let me try to answer from my general knowledge instead."

@tool
async def get_server_status(server_id: str = "auto-detect", session_id: str = "admin_session") -> str:
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
            
            status = status_map.get(resources.get("current_state", "unknown"), "❓ UNKNOWN")
            
            # Extract resources from the nested structure
            resource_data = resources.get('resources', {})
            
            # Format resource usage
            cpu_usage = f"{resource_data.get('cpu_absolute', 0):.1f}%"
            
            # Memory usage
            memory_bytes = resource_data.get('memory_bytes', 0)
            memory_limit_mb = server_details.get('limits', {}).get('memory', 0)
            memory_gb = memory_bytes / (1024**3)
            if memory_limit_mb == 0:
                memory_usage = f"{memory_gb:.1f}GB / Unlimited"
            else:
                memory_limit_gb = memory_limit_mb / 1024  # MB to GB
                memory_usage = f"{memory_gb:.1f}GB / {memory_limit_gb:.1f}GB"
            
            # Disk usage
            disk_bytes = resource_data.get('disk_bytes', 0) 
            disk_limit_mb = server_details.get('limits', {}).get('disk', 0)
            disk_gb = disk_bytes / (1024**3)
            if disk_limit_mb == 0:
                disk_usage = f"{disk_gb:.1f}GB / Unlimited"
            else:
                disk_limit_gb = disk_limit_mb / 1024  # MB to GB
                disk_usage = f"{disk_gb:.1f}GB / {disk_limit_gb:.1f}GB"
            
            network_rx = resource_data.get('network_rx_bytes', 0) / (1024**2)  # MB
            network_tx = resource_data.get('network_tx_bytes', 0) / (1024**2)  # MB
            
            # Fix uptime calculation (convert milliseconds to minutes)
            uptime_ms = resource_data.get('uptime', 0)
            uptime_minutes = uptime_ms // 1000 // 60
            
            return f"""
🖥️ **{server_details.get('name', 'Unknown Server')}**
**Status**: {status}
**Server ID**: `{actual_server_id}`

📊 **Resource Usage**
⚡ **CPU**: {cpu_usage}
💾 **Memory**: {memory_usage}
💽 **Disk**: {disk_usage}
🌐 **Network**: ↓{network_rx:.1f}MB ↑{network_tx:.1f}MB

🎮 **Game Info**
**Type**: {detect_game_type(server_details.get('egg', {}).get('name', ''), server_details.get('docker_image', ''), server_details.get('relationships', {}).get('variables', {}).get('data', []))}
**Node**: {server_details.get('node', 'Unknown')}

⏱️ **Uptime**: {uptime_minutes} minutes
"""
            
    except PterodactylAPIError as e:
        return f"❌ **API Error**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool
async def restart_server(server_id: str = "auto-detect", confirmation_data: str = None, session_id: str = "admin_session") -> str:
    """Restart a game server - requires confirmation due to player impact"""
    try:
        # Check if confirmation data was provided
        if confirmation_data:
            try:
                confirmation = json.loads(confirmation_data)
                if confirmation.get("confirmed"):
                    # Execute restart with the confirmed server_id
                    actual_server_id = confirmation.get("server_id")
                    if not actual_server_id:
                        return "❌ **Error**: No server ID provided in confirmation"
                    
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
                elif confirmation.get("cancelled"):
                    return "❌ **Restart Cancelled**: Operation cancelled by user"
            except json.JSONDecodeError:
                pass
        
        # No confirmation provided, show confirmation dialog
        actual_server_id = await detect_server_id(pterodactyl_user_id, server_id)
        
        # Get server details for confirmation UI
        async with get_admin_client() as admin_client:
            details = await admin_client.get_server_details(actual_server_id, pterodactyl_user_id)
        
        # Return JSON with server details for the UI to handle confirmation
        return json.dumps({
            "action": "restart",
            "server_id": actual_server_id,
            "server_name": details.get('name', 'Unknown'),
            "current_status": details.get('current_state', 'unknown').upper(),
            "requires_confirmation": True,
            "warning": "Players will be disconnected temporarily",
            "impact": [
                "🔄 Stop the server gracefully",
                "💾 Save current world state", 
                "⏳ Server offline for 30-60 seconds",
                "🚀 Restart with fresh resources"
            ]
        })
        
    except PterodactylAPIError as e:
        return f"❌ **Restart Failed**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool
async def stop_server(server_id: str = "auto-detect", confirmation_data: str = None, session_id: str = "admin_session") -> str:
    """Stop a game server - requires confirmation due to player impact"""
    try:
        # Check if confirmation data was provided
        if confirmation_data:
            try:
                confirmation = json.loads(confirmation_data)
                if confirmation.get("confirmed"):
                    # Execute stop with the confirmed server_id
                    actual_server_id = confirmation.get("server_id")
                    if not actual_server_id:
                        return "❌ **Error**: No server ID provided in confirmation"
                    
                    async with get_user_client(session_id) as client:
                        await client.send_power_action(actual_server_id, "stop")
                        
                    return f"""
🛑 **Server Stop Initiated**

✅ **Status**: Stop signal sent successfully
🔴 **Result**: Server is shutting down
⏹️ **Note**: Server will remain offline until started

**To start again**: Say "start server" when ready
"""
                elif confirmation.get("cancelled"):
                    return "❌ **Stop Cancelled**: Operation cancelled by user"
            except json.JSONDecodeError:
                pass
        
        # No confirmation provided, show confirmation dialog
        actual_server_id = await detect_server_id(pterodactyl_user_id, server_id)
        
        # Get server details for confirmation UI
        async with get_admin_client() as admin_client:
            details = await admin_client.get_server_details(actual_server_id, pterodactyl_user_id)
        
        # Return JSON with server details for the UI to handle confirmation
        return json.dumps({
            "action": "stop",
            "server_id": actual_server_id,
            "server_name": details.get('name', 'Unknown'),
            "current_status": details.get('current_state', 'unknown').upper(),
            "requires_confirmation": True,
            "warning": "All players will be disconnected immediately",
            "impact": [
                "⏹️ Shut down server completely",
                "💾 Save all data and disconnect players", 
                "🔴 Server will remain OFFLINE until manually started"
            ]
        })
        
    except PterodactylAPIError as e:
        return f"❌ **Stop Failed**: {e.message}"
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

@tool
async def start_server(server_id: str = "auto-detect", session_id: str = "admin_session") -> str:
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
async def send_server_command(command: str, server_id: str = "auto-detect", session_id: str = "admin_session") -> str:
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
async def list_user_servers(session_id: str = "admin_session") -> str:
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
    query_documentation,
]
