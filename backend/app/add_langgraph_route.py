from assistant_stream import create_run, RunController
from assistant_stream.serialization import DataStreamResponse
from langchain_core.messages import (
    HumanMessage,
    AIMessageChunk,
    AIMessage,
    ToolMessage,
    SystemMessage,
    BaseMessage,
)
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Literal, Union, Optional, Any
from langgraph.errors import NodeInterrupt
from .middleware.auth import get_current_user
from .services.user_manager import UserSession
from .services.chat_persistence import get_chat_service
from .models.chat import CreateThreadRequest, CreateMessageRequest


class LanguageModelTextPart(BaseModel):
    type: Literal["text"]
    text: str
    providerMetadata: Optional[Any] = None


class LanguageModelImagePart(BaseModel):
    type: Literal["image"]
    image: str  # Will handle URL or base64 string
    mimeType: Optional[str] = None
    providerMetadata: Optional[Any] = None


class LanguageModelFilePart(BaseModel):
    type: Literal["file"]
    data: str  # URL or base64 string
    mimeType: str
    providerMetadata: Optional[Any] = None


class LanguageModelToolCallPart(BaseModel):
    type: Literal["tool-call"]
    toolCallId: str
    toolName: str
    args: Any
    providerMetadata: Optional[Any] = None


class LanguageModelToolResultContentPart(BaseModel):
    type: Literal["text", "image"]
    text: Optional[str] = None
    data: Optional[str] = None
    mimeType: Optional[str] = None


class LanguageModelToolResultPart(BaseModel):
    type: Literal["tool-result"]
    toolCallId: str
    toolName: str
    result: Any
    isError: Optional[bool] = None
    content: Optional[List[LanguageModelToolResultContentPart]] = None
    providerMetadata: Optional[Any] = None


class LanguageModelSystemMessage(BaseModel):
    role: Literal["system"]
    content: str


class LanguageModelUserMessage(BaseModel):
    role: Literal["user"]
    content: List[
        Union[LanguageModelTextPart, LanguageModelImagePart, LanguageModelFilePart]
    ]


class LanguageModelAssistantMessage(BaseModel):
    role: Literal["assistant"]
    content: List[Union[LanguageModelTextPart, LanguageModelToolCallPart]]


class LanguageModelToolMessage(BaseModel):
    role: Literal["tool"]
    content: List[LanguageModelToolResultPart]


LanguageModelV1Message = Union[
    LanguageModelSystemMessage,
    LanguageModelUserMessage,
    LanguageModelAssistantMessage,
    LanguageModelToolMessage,
]


def convert_to_langchain_messages(
    messages: List[LanguageModelV1Message],
) -> List[BaseMessage]:
    result = []

    for msg in messages:
        if msg.role == "system":
            result.append(SystemMessage(content=msg.content))

        elif msg.role == "user":
            content = []
            for p in msg.content:
                if isinstance(p, LanguageModelTextPart):
                    content.append({"type": "text", "text": p.text})
                elif isinstance(p, LanguageModelImagePart):
                    content.append({"type": "image_url", "image_url": p.image})
            result.append(HumanMessage(content=content))

        elif msg.role == "assistant":
            # Handle both text and tool calls
            text_parts = [
                p for p in msg.content if isinstance(p, LanguageModelTextPart)
            ]
            text_content = " ".join(p.text for p in text_parts)
            tool_calls = [
                {
                    "id": p.toolCallId,
                    "name": p.toolName,
                    "args": p.args,
                }
                for p in msg.content
                if isinstance(p, LanguageModelToolCallPart)
            ]
            result.append(AIMessage(content=text_content, tool_calls=tool_calls))

        elif msg.role == "tool":
            for tool_result in msg.content:
                result.append(
                    ToolMessage(
                        content=str(tool_result.result),
                        tool_call_id=tool_result.toolCallId,
                    )
                )

    return result


class FrontendToolCall(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: dict[str, Any]


class ChatRequest(BaseModel):
    system: Optional[str] = ""
    tools: Optional[List[FrontendToolCall]] = []
    messages: List[LanguageModelV1Message]
    ptero_context: Optional[dict] = None
    thread_id: Optional[str] = None


def add_langgraph_route(app: FastAPI, graph, path: str):
    async def chat_completions(
        request: ChatRequest,
        user: UserSession = Depends(get_current_user)
    ):
        inputs = convert_to_langchain_messages(request.messages)
        chat_service = get_chat_service()

        # Extract iframe context from the Pterodactyl context
        current_server_id = None
        pterodactyl_user_id = None
        
        if request.ptero_context:
            current_server_id = request.ptero_context.get('serverId')
            pterodactyl_user_id = request.ptero_context.get('userId')  # From iframe postMessage
        
        # Handle chat persistence
        thread_id = request.thread_id
        current_thread = None
        
        # Ensure user exists in database
        await chat_service.get_or_create_user(
            user_id=user.user_id,
            display_name=user.user_id,
            pterodactyl_user_id=None  # Extract from ptero_context if needed
        )
        
        # Get or create thread
        if thread_id:
            current_thread = await chat_service.get_thread(thread_id, user.user_id)
        
        if not current_thread:
            # Create new thread
            thread_request = CreateThreadRequest(
                title="New Chat",
                server_id=current_server_id,
                server_name=None,  # Could be enhanced to get server name
                thread_metadata={"ptero_context": request.ptero_context or {}}
            )
            current_thread = await chat_service.create_thread(user.user_id, thread_request)
            thread_id = current_thread.thread_id
        
        # Persist user message (if this is a new message, not just a thread continuation)
        if request.messages and request.messages[-1].role == "user":
            user_message = request.messages[-1]
            await chat_service.add_message(
                thread_id=thread_id,
                request=CreateMessageRequest(
                    role="user",
                    content=[{"type": "text", "text": part.text} for part in user_message.content if hasattr(part, 'text')],
                    tool_calls=[],
                    thread_metadata={"ptero_context": request.ptero_context or {}}
                )
            )

        async def run(controller: RunController):
            tool_calls = {}
            tool_calls_by_idx = {}
            assistant_content = []  # Track assistant response for persistence
            assistant_tool_calls = []  # Track tool calls for persistence
            try:
                async for msg, metadata in graph.astream(
                    {
                        "messages": inputs,
                        "current_server_id": current_server_id,
                        "pterodactyl_user_id": pterodactyl_user_id,  # From iframe context
                    },
                    {
                        "configurable": {
                            "system": request.system,
                            "frontend_tools": request.tools,
                            "current_server_id": current_server_id,
                            "pterodactyl_user_id": pterodactyl_user_id,
                            "user_session": {
                                "user_id": user.user_id,
                                "session_id": user.session_id,
                                "accessible_servers": user.servers,
                                "user_permissions": user.permissions,
                            }
                        }
                    },
                    stream_mode="messages",
                ):
                    if isinstance(msg, ToolMessage):
                        if msg.tool_call_id in tool_calls:
                            tool_controller = tool_calls[msg.tool_call_id]
                            tool_controller.set_result(msg.content)

                    if isinstance(msg, AIMessageChunk) or isinstance(msg, AIMessage):
                        if msg.content:
                            controller.append_text(msg.content)
                            assistant_content.append({"type": "text", "text": msg.content})

                        for chunk in msg.tool_call_chunks:
                            if not chunk["index"] in tool_calls_by_idx:
                                tool_controller = await controller.add_tool_call(
                                    chunk["name"], chunk["id"]
                                )
                                tool_calls_by_idx[chunk["index"]] = tool_controller
                                tool_calls[chunk["id"]] = tool_controller
                                
                                # Track tool call for persistence
                                assistant_tool_calls.append({
                                    "id": chunk["id"],
                                    "name": chunk["name"],
                                    "args": chunk["args"]
                                })
                            else:
                                tool_controller = tool_calls_by_idx[chunk["index"]]

                            tool_controller.append_args_text(chunk["args"])
            except NodeInterrupt as e:
                if e.values and "messages" in e.values:
                    msg: AIMessage = e.values["messages"][-1]
                    for tool_call in msg.tool_calls:
                        tool_controller = await controller.add_tool_call(
                            tool_call["name"], tool_call["id"]
                        )
                        tool_controller.set_args(tool_call["args"])
            
            # Persist assistant response after streaming completes
            if assistant_content or assistant_tool_calls:
                await chat_service.add_message(
                    thread_id=thread_id,
                    request=CreateMessageRequest(
                        role="assistant",
                        content=assistant_content,
                        tool_calls=assistant_tool_calls,
                        thread_metadata={"ptero_context": request.ptero_context or {}}
                    )
                )

        # Return the streaming response with thread_id in headers
        response = DataStreamResponse(create_run(run))
        response.headers["X-Thread-ID"] = thread_id
        return response

    # Add the route
    app.add_api_route(path, chat_completions, methods=["POST"])
    
    # Also add authentication routes
    from .api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
