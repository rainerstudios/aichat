from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from langgraph.errors import NodeInterrupt
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from .tools import tools, detect_game_type
from .state import AgentState
from ..services.pterodactyl_admin_client import create_pterodactyl_admin_client

model = ChatOpenAI()


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


# Define a new graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", run_tools)

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    ["tools", END],
)

workflow.add_edge("tools", "agent")

assistant_ui_graph = workflow.compile()
