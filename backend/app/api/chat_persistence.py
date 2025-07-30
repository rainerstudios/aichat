"""
Chat persistence API routes
Replaces Assistant-UI Cloud with local PostgreSQL storage
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import uuid

from ..services.chat_persistence import get_chat_service, ChatPersistenceService
from ..models.chat import (
    ThreadResponse, MessageResponse, FeedbackResponse,
    CreateThreadRequest, CreateMessageRequest, CreateFeedbackRequest
)
from ..middleware.auth import get_current_user
from ..services.user_manager import UserSession

router = APIRouter(prefix="/api/chat", tags=["chat-persistence"])

@router.post("/threads", response_model=ThreadResponse)
async def create_thread(
    request: CreateThreadRequest,
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Create a new chat thread"""
    try:
        # Ensure user exists in database
        await chat_service.get_or_create_user(
            user_id=user.user_id,
            display_name=user.user_id,
            pterodactyl_user_id=user.pterodactyl_user_id
        )
        
        # Create thread
        thread = await chat_service.create_thread(user.user_id, request)
        return thread
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")

@router.get("/threads", response_model=List[ThreadResponse])
async def get_threads(
    status: str = Query("active", description="Thread status filter"),
    limit: int = Query(50, le=100, description="Maximum number of threads"),
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Get user's chat threads"""
    try:
        threads = await chat_service.get_threads(
            user_id=user.user_id,
            status=status,
            limit=limit
        )
        return threads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get threads: {str(e)}")

@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Get a specific thread"""
    try:
        thread = await chat_service.get_thread(thread_id, user.user_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        return thread
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")

@router.patch("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    title: Optional[str] = None,
    status: Optional[str] = None,
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Update thread properties"""
    try:
        # Verify user owns the thread
        existing_thread = await chat_service.get_thread(thread_id, user.user_id)
        if not existing_thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        thread = await chat_service.update_thread(
            thread_id=thread_id,
            title=title,
            status=status
        )
        return thread
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update thread: {str(e)}")

@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def add_message(
    thread_id: str,
    request: CreateMessageRequest,
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Add a message to a thread"""
    try:
        # Verify user owns the thread
        thread = await chat_service.get_thread(thread_id, user.user_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        message = await chat_service.add_message(thread_id, request)
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")

@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    thread_id: str,
    limit: int = Query(100, le=500, description="Maximum number of messages"),
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Get messages for a thread"""
    try:
        # Verify user owns the thread
        thread = await chat_service.get_thread(thread_id, user.user_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        messages = await chat_service.get_messages(thread_id, limit)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@router.patch("/messages/{message_id}/status")
async def update_message_status(
    message_id: str,
    status: str,
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Update message status"""
    try:
        message = await chat_service.update_message_status(message_id, status)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")

@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse)
async def add_message_feedback(
    message_id: str,
    request: CreateFeedbackRequest,
    user: UserSession = Depends(get_current_user),
    chat_service: ChatPersistenceService = Depends(get_chat_service)
):
    """Add feedback for a message"""
    try:
        feedback = await chat_service.add_feedback(message_id, user.user_id, request)
        return feedback
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for chat persistence service"""
    try:
        chat_service = get_chat_service()
        # Simple connectivity test - could be expanded
        return {"status": "healthy", "service": "chat_persistence"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")