# 🚀 Quick Wins Implementation Checklist
*Start here for immediate results within 1-2 hours*

## Overview
This checklist gives you basic server management functionality immediately by enhancing your existing system with minimal changes.

---

## ✅ Quick Win #1: Basic Server Status Tool (30 minutes)

### Step 1: Add Server Status Tool
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add new tool function

```python
# ADD THIS TO YOUR EXISTING tools.py file
from langchain_core.tools import tool
import httpx
import os

@tool
async def get_server_status(server_id: str = "auto-detect") -> str:
    """Get current server status, player count, and resource usage for XGaming Server panel"""
    
    # For quick testing - replace with real API call later
    mock_data = {
        "server_name": "MyMinecraftServer", 
        "status": "running",
        "players": "3/20",
        "cpu_usage": "45%",
        "memory_usage": "2.1GB/4GB", 
        "uptime": "2d 14h 32m",
        "game_type": "Minecraft Java Edition"
    }
    
    # TODO: Replace this with real Pterodactyl API call
    # api_key = get_user_api_key()  # Implement user context
    # response = await pterodactyl_client.get_server_details(server_id)
    
    return f"""
**Server Status Report**
🖥️ **Server**: {mock_data['server_name']}
🟢 **Status**: {mock_data['status'].upper()}
👥 **Players**: {mock_data['players']}
⚡ **CPU**: {mock_data['cpu_usage']}
💾 **Memory**: {mock_data['memory_usage']} 
⏱️ **Uptime**: {mock_data['uptime']}
🎮 **Game**: {mock_data['game_type']}
"""

# ADD to your existing tools list
tools = [
    get_server_status,  # ADD THIS LINE
    # ... your existing tools
]
```

### Step 2: Test the Tool
- [ ] **Action**: Restart your FastAPI backend
```bash
cd /var/www/aichat/backend
python -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

- [ ] **Action**: Test via frontend at https://chat.xgaming.pro
- [ ] **Test Query**: "What's my server status?"
- [ ] **Expected Result**: Should return formatted server status information

---

## ✅ Quick Win #2: Server Control Tools (45 minutes)

### Step 1: Add Power Management Tools
- [ ] **File**: `backend/app/langgraph/tools.py`  
- [ ] **Action**: Add server control functions

```python
# ADD THESE TO YOUR EXISTING tools.py file

@tool
async def restart_server(server_id: str = "auto-detect", confirm: bool = False) -> str:
    """Restart a game server (REQUIRES CONFIRMATION - this will disconnect players)"""
    
    if not confirm:
        return """
⚠️  **CONFIRMATION REQUIRED** ⚠️

Restarting the server will:
- Disconnect all current players
- Take the server offline for 30-60 seconds  
- Apply any pending configuration changes

**Current players will lose unsaved progress.**

To proceed, ask me: "restart server with confirmation"
"""
    
    # TODO: Replace with real API call
    # result = await pterodactyl_client.send_power_action(server_id, "restart")
    
    return """
✅ **Server Restart Initiated**

🔄 Stopping server gracefully...
⏳ Server will be back online in 30-60 seconds
🎮 Players can reconnect once status shows "running"

Use "get server status" to check progress.
"""

@tool  
async def stop_server(server_id: str = "auto-detect", confirm: bool = False) -> str:
    """Stop a game server (REQUIRES CONFIRMATION - this will disconnect players)"""
    
    if not confirm:
        return """
🛑 **CONFIRMATION REQUIRED** 🛑

Stopping the server will:
- Disconnect all current players immediately
- Take the server completely offline
- Require manual start to bring back online

**Players will lose unsaved progress.**

To proceed, ask me: "stop server with confirmation"
"""
    
    # TODO: Replace with real API call  
    # result = await pterodactyl_client.send_power_action(server_id, "stop")
    
    return """
🛑 **Server Stop Initiated**

Server is shutting down gracefully...
⏹️ Server is now OFFLINE
🔧 Use "start server" when ready to bring back online
"""

@tool
async def start_server(server_id: str = "auto-detect") -> str:
    """Start a stopped game server"""
    
    # TODO: Replace with real API call
    # result = await pterodactyl_client.send_power_action(server_id, "start")
    
    return """
🚀 **Server Start Initiated**

⚡ Starting server processes...
📡 Allocating resources...
🎮 Server will be online in 30-60 seconds

Use "get server status" to check progress.
"""

# ADD to your existing tools list
tools = [
    get_server_status,
    restart_server,    # ADD THIS
    stop_server,       # ADD THIS  
    start_server,      # ADD THIS
    # ... your existing tools
]
```

### Step 2: Test Server Controls
- [ ] **Action**: Restart backend
- [ ] **Test Queries**:
  - [ ] "restart my server" → Should ask for confirmation
  - [ ] "restart server with confirmation" → Should show restart message
  - [ ] "stop my server" → Should ask for confirmation
  - [ ] "start my server" → Should show start message

---

## ✅ Quick Win #3: Enhanced System Prompt (5 minutes)

### Step 1: Update System Prompt Context
- [ ] **File**: `frontend-new/app/api/chat/route.ts`
- [ ] **Action**: Enhance existing system prompt

```typescript
// REPLACE the existing system prompt with this enhanced version
system: system || `You are XGaming Server's AI customer support assistant. You help customers manage their game servers on our hosting platform.

CURRENT CAPABILITIES:
- Check server status and resource usage
- Restart, stop, and start servers (with safety confirmations)
- Provide game server troubleshooting advice
- Help with XGaming Server panel navigation

SAFETY RULES:
- ALWAYS ask for confirmation before server restarts or stops
- Explain what each action will do to players
- Provide helpful context about server operations
- Guide users through step-by-step solutions

RESPONSE STYLE:
- Use emojis and formatting for clear status updates
- Be conversational but professional
- Provide specific, actionable advice
- Ask clarifying questions when needed

If users need help beyond your current capabilities, guide them to create a support ticket for human assistance.`,
```

### Step 2: Test Enhanced Responses
- [ ] **Test Queries**:
  - [ ] "Help me with my server" → Should show available capabilities
  - [ ] "My server is lagging" → Should provide troubleshooting steps
  - [ ] "How do I optimize performance?" → Should give specific advice

---

## ✅ Quick Win #4: Console Command Tool (30 minutes)

### Step 1: Add Console Command Capability
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add console command tool

```python
# ADD THIS TO YOUR EXISTING tools.py file

@tool
async def send_server_command(command: str, server_id: str = "auto-detect") -> str:
    """Send a command to the game server console (be careful - some commands are destructive)"""
    
    # Safety check for dangerous commands
    dangerous_commands = ['stop', 'kill', 'shutdown', 'rm', 'delete', 'ban', 'whitelist remove']
    if any(danger in command.lower() for danger in dangerous_commands):
        return f"""
⚠️  **DANGEROUS COMMAND DETECTED** ⚠️

Command: `{command}`

This command could be destructive. For safety:
- Use server control tools for start/stop/restart
- Ask me for help with player management
- Contact support for advanced operations

What are you trying to accomplish? I can suggest a safer approach.
"""
    
    # TODO: Replace with real console command
    # result = await pterodactyl_client.send_console_command(server_id, command)
    
    return f"""
📟 **Console Command Executed**

Command: `{command}`
Status: ✅ Sent to server console

⏳ Command is processing...
📊 Check server logs for command output
🎮 Players may see changes immediately

Use "get server status" to verify results.
"""

# ADD to your existing tools list  
tools = [
    get_server_status,
    restart_server,
    stop_server, 
    start_server,
    send_server_command,  # ADD THIS
    # ... your existing tools
]
```

### Step 2: Test Console Commands
- [ ] **Test Queries**:
  - [ ] "run command /time set day" → Should execute safely
  - [ ] "send stop command" → Should warn about dangerous command
  - [ ] "run /gamemode creative for Steve" → Should execute

---

## ✅ Quick Win #5: Basic Troubleshooting Tool (15 minutes)

### Step 1: Add Troubleshooting Helper
- [ ] **File**: `backend/app/langgraph/tools.py`
- [ ] **Action**: Add troubleshooting tool

```python
# ADD THIS TO YOUR EXISTING tools.py file

@tool
async def diagnose_server_issue(problem_description: str) -> str:
    """Diagnose common server problems and provide solutions"""
    
    problem = problem_description.lower()
    
    if 'lag' in problem or 'slow' in problem or 'performance' in problem:
        return """
🐌 **Server Performance Issues**

**Common Causes & Solutions:**

🔧 **Quick Fixes:**
- Restart server to clear memory leaks
- Check if too many players online
- Reduce view distance in server settings

⚡ **Optimization Tips:**
- Allocate more RAM if available
- Remove unnecessary plugins/mods
- Limit chunk loading distance

📊 **Check These:**
- CPU Usage (should be <80%)
- Memory Usage (should be <90%) 
- Disk Space (needs 20%+ free)

Use "get server status" to check current resources.
"""
    
    elif 'crash' in problem or 'offline' in problem or 'down' in problem:
        return """
💥 **Server Crash/Offline Issues**

**Immediate Steps:**
1. Check server status first
2. Try starting the server if stopped  
3. Check server logs for error messages

🔍 **Common Crash Causes:**
- Out of memory (increase RAM allocation)
- Plugin conflicts (disable recent plugins)
- Corrupted world files (restore from backup)
- Version incompatibilities (check game version)

🛠️ **Recovery Steps:**
1. "start server" to attempt restart
2. If fails, try "restart server with confirmation"
3. Contact support if crashes persist

Use "get server status" to verify current state.
"""
    
    elif 'connect' in problem or 'join' in problem or 'access' in problem:
        return """
🔌 **Connection Issues**

**Player Can't Connect:**

🌐 **Network Checks:**
- Verify server is running and online
- Check if server IP/port are correct
- Ensure server isn't full (player limit)

🛡️ **Access Controls:**
- Check if whitelist is enabled
- Verify player isn't banned
- Confirm game version matches server

🔧 **Quick Fixes:**
- Restart server to refresh connections
- Check firewall/port settings
- Verify server visibility settings

Use "get server status" to check online status.
"""
    
    else:
        return f"""
🤔 **General Troubleshooting**

Issue: {problem_description}

**Standard Diagnostic Steps:**

1️⃣ **Check Status**: "get server status"
2️⃣ **Review Resources**: Look for high CPU/memory usage  
3️⃣ **Check Logs**: Look for error messages
4️⃣ **Try Restart**: Often resolves temporary issues

**Common Categories:**
- Performance/lag issues
- Server crashes or offline
- Player connection problems
- Configuration/setup issues

Can you describe the specific symptoms you're seeing?
"""

# ADD to your existing tools list
tools = [
    get_server_status,
    restart_server,
    stop_server,
    start_server, 
    send_server_command,
    diagnose_server_issue,  # ADD THIS
    # ... your existing tools
]
```

### Step 2: Test Troubleshooting
- [ ] **Test Queries**:
  - [ ] "My server is lagging" → Should provide performance tips
  - [ ] "Server crashed" → Should provide crash recovery steps
  - [ ] "Players can't connect" → Should provide connection troubleshooting

---

## 🧪 Testing Your Quick Wins

### Final Testing Checklist
- [ ] **Backend Status**: FastAPI running on port 8000
- [ ] **Frontend Status**: Next.js running on port 3000, accessible at https://chat.xgaming.pro
- [ ] **Tool Registration**: All 5 new tools added to `tools` list

### Test Conversation Flow
Copy/paste these test queries to verify everything works:

```
1. "What's my server status?"
2. "My server is running slow, help me diagnose the issue"  
3. "I want to restart my server"
4. "restart server with confirmation"
5. "Run the command /time set day"
6. "My server keeps crashing, what should I do?"
```

### Expected Results
- [ ] ✅ Server status shows formatted response with mock data
- [ ] ✅ Restart requires confirmation, then shows progress message
- [ ] ✅ Console commands execute with safety warnings
- [ ] ✅ Troubleshooting provides relevant advice based on problem type
- [ ] ✅ All responses use emojis and clear formatting

---

## 🎯 Next Steps After Quick Wins

Once these quick wins are working:

1. **Week 1**: Implement real Pterodactyl API calls (replace mock data)
2. **Week 2**: Add user authentication and server context
3. **Week 3**: Add file management and backup tools
4. **Week 4**: Implement game-specific knowledge and optimization

---

## 🚨 Troubleshooting Quick Wins

### Common Issues:

**Tools not working?**
- Check `tools` list includes new functions
- Restart FastAPI backend completely
- Verify no syntax errors in tools.py

**Frontend not calling tools?**
- Check browser console for errors
- Verify system prompt mentions available tools
- Test with simple queries first

**Tools returning errors?**
- Check function syntax and imports
- Verify all required parameters have defaults
- Test functions individually in Python

### Support:
If you encounter issues, the mock responses should work immediately. Real API integration comes in Phase 1 implementation.