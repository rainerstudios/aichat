from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.errors import NodeInterrupt
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from .tools import tools, detect_game_type
from .state import AgentState
from ..services.pterodactyl_admin_client import create_pterodactyl_admin_client

model = ChatOpenAI()
query_rewrite_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # Fast, deterministic model for query rewriting

def format_chat_history(messages, max_messages=5):
    """Format recent chat history for query rewriting context"""
    if not messages:
        return "No previous context"
    
    # Get last few messages for context
    recent_messages = messages[-max_messages:]
    formatted = []
    
    for msg in recent_messages:
        if hasattr(msg, 'content') and msg.content:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted) if formatted else "No previous context"

async def query_rewrite_node(state: AgentState, config) -> AgentState:
    """
    LLM-powered query rewriting node for enhanced document retrieval
    Transforms conversational queries into technical, keyword-rich search queries
    """
    # Skip rewriting if disabled or no human message
    if not state.get("query_rewrite_enabled", True):
        return state
    
    messages = state["messages"]
    if not messages or not isinstance(messages[-1], HumanMessage):
        return state
    
    original_query = messages[-1].content
    if not original_query or len(original_query.strip()) < 5:
        return state
    
    # Get chat history and game context
    chat_history = format_chat_history(messages[:-1])
    game_type = state.get("game_type", "Unknown")
    
    # Build context-aware rewriting prompt
    rewrite_prompt = f"""You are a search query optimizer for technical gaming server documentation.

Transform the user's conversational query into a technical, keyword-rich search query optimized for vector database retrieval.

CONTEXT:
- Game Type: {game_type}
- Chat History: {chat_history}

GUIDELINES:
1. Extract core technical concepts and problems
2. Add relevant technical keywords and synonyms
3. Include error codes, technical terms, and troubleshooting keywords
4. Keep it focused and under 50 words
5. Remove conversational filler words

EXAMPLES:
User: "how do i make this work when my api call keeps failing?"
Rewritten: "API call failure troubleshooting authentication headers rate limiting network timeout 500 error"

User: "my minecraft server won't start"
Rewritten: "minecraft server startup failure boot error configuration troubleshooting launch issues"

User: "players can't connect to my server"
Rewritten: "server connection issues player connectivity firewall port forwarding network troubleshooting"

Original Query: {original_query}

Rewritten Query:"""

    try:
        # Use fast model for query rewriting
        response = await query_rewrite_model.ainvoke([
            SystemMessage(content=rewrite_prompt)
        ])
        
        rewritten_query = response.content.strip()
        
        # Validate the rewritten query
        if (rewritten_query and 
            len(rewritten_query) > 5 and 
            len(rewritten_query) < 300 and
            rewritten_query.lower() != original_query.lower()):
            
            state["rewritten_query"] = rewritten_query
            print(f"Query rewritten: '{original_query}' -> '{rewritten_query}'")
        else:
            print(f"Query rewriting failed or unnecessary for: '{original_query}'")
            
    except Exception as e:
        print(f"Query rewriting error: {e}")
        # Continue without rewriting on error
    
    return state

def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "tools"


class AnyArgsSchema(BaseModel):
    class Config:
        extra = "allow"


class FrontendTool(BaseTool):
    def __init__(self, name: str):
        super().__init__(name=name, description="", args_schema=AnyArgsSchema)

    def _run(self, *args, **kwargs):
        raise NodeInterrupt("This is a frontend tool call")

    async def _arun(self, *args, **kwargs) -> str:
        raise NodeInterrupt("This is a frontend tool call")


def get_tool_defs(config):
    frontend_tools = [
        {"type": "function", "function": tool}
        for tool in config["configurable"]["frontend_tools"]
    ]
    return tools + frontend_tools


def get_tools(config):
    frontend_tools = [
        FrontendTool(tool.name) for tool in config["configurable"]["frontend_tools"]
    ]
    return tools + frontend_tools


async def call_model(state: AgentState, config):
    """Enhanced model call with user context and safety checks"""
    
    # --- Extract iframe context ---
    pterodactyl_user_id = state.get("pterodactyl_user_id") or config["configurable"].get("pterodactyl_user_id")
    current_server_id = state.get("current_server_id") or config["configurable"].get("current_server_id")
    
    # Store in state for tools to access
    if pterodactyl_user_id:
        state["pterodactyl_user_id"] = pterodactyl_user_id
    if current_server_id:
        state["current_server_id"] = current_server_id
    
    # --- Game Type Detection ---
    game_type = state.get("game_type")
    if not game_type and current_server_id and pterodactyl_user_id:
        try:
            async with create_pterodactyl_admin_client() as admin_client:
                server_details = await admin_client.get_server_details(current_server_id, int(pterodactyl_user_id))
                game_type = detect_game_type(
                    egg_name=server_details.get('egg', {}).get('name', ''),
                    docker_image=server_details.get('docker_image', ''),
                    variables=server_details.get('relationships', {}).get('variables', {}).get('data', [])
                )
                state["game_type"] = game_type
        except Exception as e:
            print(f"Could not detect game type: {e}")
            state["game_type"] = "Generic"

    # Extract user context from config
    system_prompt = config["configurable"].get("system", "")
    
    # Add user context to system prompt
    enhanced_system = f"""{system_prompt}

CURRENT CONTEXT:
- Pterodactyl User ID: {pterodactyl_user_id or 'unknown'}
- Current Server ID: {current_server_id or 'unknown'} 
- Detected Game Type: {state.get('game_type', 'Unknown')}

TOOL USAGE GUIDELINES:
- **PRIORITY 1: Use `query_documentation` for ANY knowledge questions** including:
  * Server setup, configuration, and troubleshooting
  * Game-specific guides, mods, and settings  
  * Best practices and tutorials
  * Pterodactyl panel usage
  * Comparisons between different server types (Paper vs Spigot, etc.)
- **IMPORTANT**: The tool name is `query_documentation`, NOT `get_knowledge_base_info`
- For server actions (restart, stop, etc.), use the server action tools which automatically verify ownership.
- All server operations use the admin API with proper ownership verification.
- Server ID "auto-detect" will use the current server or the user's first server.
- Always explain what operations will do before executing potentially disruptive actions.
- The documentation tool has comprehensive knowledge from multiple sources - use it liberally!
"""
    
    messages = [SystemMessage(content=enhanced_system)] + state["messages"]
    model_with_tools = model.bind_tools(get_tool_defs(config))
    response = await model_with_tools.ainvoke(messages)
    
    return {"messages": [response]}


async def run_tools(input, config, **kwargs):
    tool_node = ToolNode(get_tools(config))
    return await tool_node.ainvoke(input, config, **kwargs)


# Define a new graph with query rewriting
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("query_rewrite", query_rewrite_node)  # NEW: Query rewriting node
workflow.add_node("agent", call_model)
workflow.add_node("tools", run_tools)

# Set entry point to query rewriting
workflow.set_entry_point("query_rewrite")

# Flow: query_rewrite -> agent -> tools/END
workflow.add_edge("query_rewrite", "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    ["tools", END],
)
workflow.add_edge("tools", "agent")

assistant_ui_graph = workflow.compile()
