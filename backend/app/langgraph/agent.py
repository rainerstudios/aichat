from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage
from langgraph.errors import NodeInterrupt
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from .tools import tools
from .state import AgentState


model = ChatOpenAI()


def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "tools"


class AnyArgsSchema(BaseModel):
    # By not defining any fields and allowing extras,
    # this schema will accept any input passed in.
    class Config:
        extra = "allow"


class FrontendTool(BaseTool):
    def __init__(self, name: str):
        super().__init__(name=name, description="", args_schema=AnyArgsSchema)

    def _run(self, *args, **kwargs):
        # Since this is a frontend-only tool, it might not actually execute anything.
        # Raise an interrupt or handle accordingly.
        raise NodeInterrupt("This is a frontend tool call")

    async def _arun(self, *args, **kwargs) -> str:
        # Similarly handle async calls
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
