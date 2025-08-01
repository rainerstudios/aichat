"""
Chat persistence service using PostgreSQL
Replaces Assistant-UI Cloud functionality
"""

import asyncio
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete, desc, func
from datetime import datetime, timedelta
import os
import uuid

from ..models.chat import (
    Base, User, ChatThread, ChatMessage, MessageFeedback,
    UserResponse, ThreadResponse, MessageResponse, FeedbackResponse,
    CreateThreadRequest, CreateMessageRequest, CreateFeedbackRequest
)
from .thread_naming import ThreadNamingService

class ChatPersistenceService:
    """Service for managing chat persistence in PostgreSQL"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Convert psycopg2 URL to asyncpg for async support
        if "postgresql+psycopg2://" in self.database_url:
            self.database_url = self.database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        elif "postgresql://" in self.database_url and "+asyncpg" not in self.database_url:
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # Handle SSL configuration for NeonDB/asyncpg
        if "sslmode=require" in self.database_url:
            self.database_url = self.database_url.replace("sslmode=require", "ssl=require")
        
        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,  # 30 minutes
            pool_pre_ping=True,  # Verify connections before use
            pool_timeout=30,
            connect_args={
                "server_settings": {
                    "jit": "off"  # Disable JIT for better NeonDB compatibility
                }
            }
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_database(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_or_create_user(self, user_id: str, email: str = None, 
                                display_name: str = None, 
                                pterodactyl_user_id: int = None) -> UserResponse:
        """Get existing user or create new one"""
        async with self.async_session() as session:
            # Try to get existing user
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Create new user
                user = User(
                    user_id=user_id,
                    email=email,
                    display_name=display_name,
                    pterodactyl_user_id=pterodactyl_user_id
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            else:
                # Update last active
                user.last_active = datetime.utcnow()
                if email and user.email != email:
                    user.email = email
                if display_name and user.display_name != display_name:
                    user.display_name = display_name
                if pterodactyl_user_id and user.pterodactyl_user_id != pterodactyl_user_id:
                    user.pterodactyl_user_id = pterodactyl_user_id
                await session.commit()
                await session.refresh(user)
            
            return UserResponse(
                id=str(user.id),
                user_id=user.user_id,
                email=user.email,
                display_name=user.display_name,
                pterodactyl_user_id=user.pterodactyl_user_id,
                created_at=user.created_at,
                last_active=user.last_active
            )
    
    async def create_thread(self, user_id: str, request: CreateThreadRequest) -> ThreadResponse:
        """Create a new chat thread"""
        async with self.async_session() as session:
            # Get user
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Create thread
            thread = ChatThread(
                thread_id=str(uuid.uuid4()),
                user_id=user.id,
                title=request.title,
                server_id=request.server_id,
                server_name=request.server_name,
                thread_metadata=request.thread_metadata
            )
            session.add(thread)
            await session.commit()
            await session.refresh(thread)
            
            return ThreadResponse(
                id=str(thread.id),
                thread_id=thread.thread_id,
                user_id=str(thread.user_id),
                title=thread.title,
                status=thread.status,
                server_id=thread.server_id,
                server_name=thread.server_name,
                thread_metadata=thread.thread_metadata or {},
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                message_count=thread.message_count
            )
    
    async def get_threads(self, user_id: str, status: str = "active", 
                         limit: int = 50) -> List[ThreadResponse]:
        """Get user's chat threads"""
        async with self.async_session() as session:
            # Get user
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                return []
            
            # Get threads
            result = await session.execute(
                select(ChatThread)
                .where(ChatThread.user_id == user.id)
                .where(ChatThread.status == status)
                .order_by(desc(ChatThread.updated_at))
                .limit(limit)
            )
            threads = result.scalars().all()
            
            return [ThreadResponse(
                id=str(thread.id),
                thread_id=thread.thread_id,
                user_id=str(thread.user_id),
                title=thread.title,
                status=thread.status,
                server_id=thread.server_id,
                server_name=thread.server_name,
                thread_metadata=thread.thread_metadata or {},
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                message_count=thread.message_count
            ) for thread in threads]
    
    async def get_thread(self, thread_id: str, user_id: str = None) -> Optional[ThreadResponse]:
        """Get a specific thread"""
        async with self.async_session() as session:
            query = select(ChatThread).where(ChatThread.thread_id == thread_id)
            
            if user_id:
                user_result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    query = query.where(ChatThread.user_id == user.id)
            
            result = await session.execute(query)
            thread = result.scalar_one_or_none()
            
            return ThreadResponse(
                id=str(thread.id),
                thread_id=thread.thread_id,
                user_id=str(thread.user_id),
                title=thread.title,
                status=thread.status,
                server_id=thread.server_id,
                server_name=thread.server_name,
                thread_metadata=thread.thread_metadata or {},
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                message_count=thread.message_count
            ) if thread else None
    
    async def update_thread(self, thread_id: str, title: str = None, 
                           status: str = None, metadata: Dict[str, Any] = None) -> Optional[ThreadResponse]:
        """Update thread properties"""
        async with self.async_session() as session:
            result = await session.execute(
                select(ChatThread).where(ChatThread.thread_id == thread_id)
            )
            thread = result.scalar_one_or_none()
            
            if not thread:
                return None
            
            if title:
                thread.title = title
            if status:
                thread.status = status
            if metadata is not None:
                thread.thread_metadata = metadata
            
            await session.commit()
            await session.refresh(thread)
            
            return ThreadResponse(
                id=str(thread.id),
                thread_id=thread.thread_id,
                user_id=str(thread.user_id),
                title=thread.title,
                status=thread.status,
                server_id=thread.server_id,
                server_name=thread.server_name,
                thread_metadata=thread.thread_metadata or {},
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                message_count=thread.message_count
            )
    
    async def add_message(self, thread_id: str, request: CreateMessageRequest) -> MessageResponse:
        """Add a message to a thread"""
        async with self.async_session() as session:
            # Get thread
            thread_result = await session.execute(
                select(ChatThread).where(ChatThread.thread_id == thread_id)
            )
            thread = thread_result.scalar_one_or_none()
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")
            
            # Get next sequence number
            seq_result = await session.execute(
                select(func.coalesce(func.max(ChatMessage.sequence_number), 0) + 1)
                .where(ChatMessage.thread_id == thread.id)
            )
            sequence_number = seq_result.scalar()
            
            # Create message
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                thread_id=thread.id,
                role=request.role,
                content=request.content,
                tool_calls=request.tool_calls,
                msg_metadata=request.thread_metadata,
                sequence_number=sequence_number
            )
            session.add(message)
            
            # Auto-generate thread title from the first exchange
            if (
                request.role == "assistant"
                and sequence_number == 2
                and thread.title == "New Chat"
            ):
                # Fetch the first user message
                first_message_result = await session.execute(
                    select(ChatMessage)
                    .where(ChatMessage.thread_id == thread.id)
                    .where(ChatMessage.role == "user")
                    .order_by(ChatMessage.sequence_number)
                    .limit(1)
                )
                first_user_message = first_message_result.scalar_one_or_none()

                if first_user_message:
                    # Define a background task to generate and update the title
                    async def generate_and_set_title():
                        try:
                            new_title = await ThreadNamingService.generate_title_from_exchange(
                                first_user_message.content, request.content
                            )
                            if new_title and new_title != "New Chat":
                                async with self.async_session() as task_session:
                                    await task_session.execute(
                                        update(ChatThread)
                                        .where(ChatThread.id == thread.id)
                                        .values(title=new_title)
                                    )
                                    await task_session.commit()
                        except Exception as e:
                            # Log the error, but don't let it crash the main process
                            print(f"Error generating thread title: {e}")
                    
                    # Run the title generation in the background
                    asyncio.create_task(generate_and_set_title())
            
            await session.commit()
            await session.refresh(message)
            
            return MessageResponse(
                id=str(message.id),
                message_id=message.message_id,
                thread_id=str(message.thread_id),
                role=message.role,
                content=message.content,
                status=message.status,
                tool_calls=message.tool_calls or [],
                thread_metadata=message.msg_metadata or {},
                created_at=message.created_at,
                sequence_number=message.sequence_number
            )
    
    async def get_messages(self, thread_id: str, limit: int = 100) -> List[MessageResponse]:
        """Get messages for a thread"""
        async with self.async_session() as session:
            # Get thread
            thread_result = await session.execute(
                select(ChatThread).where(ChatThread.thread_id == thread_id)
            )
            thread = thread_result.scalar_one_or_none()
            if not thread:
                return []
            
            # Get messages
            result = await session.execute(
                select(ChatMessage)
                .where(ChatMessage.thread_id == thread.id)
                .order_by(ChatMessage.sequence_number)
                .limit(limit)
            )
            messages = result.scalars().all()
            
            return [MessageResponse(
                id=str(message.id),
                message_id=message.message_id,
                thread_id=str(message.thread_id),
                role=message.role,
                content=message.content,
                status=message.status,
                tool_calls=message.tool_calls or [],
                thread_metadata=message.msg_metadata or {},
                created_at=message.created_at,
                sequence_number=message.sequence_number
            ) for message in messages]
    
    async def update_message_status(self, message_id: str, status: str) -> Optional[MessageResponse]:
        """Update message status (e.g., from 'running' to 'complete')"""
        async with self.async_session() as session:
            result = await session.execute(
                select(ChatMessage).where(ChatMessage.message_id == message_id)
            )
            message = result.scalar_one_or_none()
            
            if not message:
                return None
            
            message.status = status
            await session.commit()
            await session.refresh(message)
            
            return MessageResponse(
                id=str(message.id),
                message_id=message.message_id,
                thread_id=str(message.thread_id),
                role=message.role,
                content=message.content,
                status=message.status,
                tool_calls=message.tool_calls or [],
                thread_metadata=message.msg_metadata or {},
                created_at=message.created_at,
                sequence_number=message.sequence_number
            )
    
    async def add_feedback(self, message_id: str, user_id: str, 
                          request: CreateFeedbackRequest) -> FeedbackResponse:
        """Add feedback for a message"""
        async with self.async_session() as session:
            # Get message and user
            message_result = await session.execute(
                select(ChatMessage).where(ChatMessage.message_id == message_id)
            )
            message = message_result.scalar_one_or_none()
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Check if feedback already exists
            existing_result = await session.execute(
                select(MessageFeedback)
                .where(MessageFeedback.message_id == message.id)
                .where(MessageFeedback.user_id == user.id)
            )
            existing_feedback = existing_result.scalar_one_or_none()
            
            if existing_feedback:
                # Update existing feedback
                existing_feedback.rating = request.rating
                existing_feedback.comment = request.comment
                await session.commit()
                await session.refresh(existing_feedback)
                return FeedbackResponse(
                    id=str(existing_feedback.id),
                    message_id=str(existing_feedback.message_id),
                    user_id=str(existing_feedback.user_id),
                    rating=existing_feedback.rating,
                    comment=existing_feedback.comment,
                    created_at=existing_feedback.created_at
                )
            else:
                # Create new feedback
                feedback = MessageFeedback(
                    message_id=message.id,
                    user_id=user.id,
                    rating=request.rating,
                    comment=request.comment
                )
                session.add(feedback)
                await session.commit()
                await session.refresh(feedback)
                return FeedbackResponse(
                    id=str(feedback.id),
                    message_id=str(feedback.message_id),
                    user_id=str(feedback.user_id),
                    rating=feedback.rating,
                    comment=feedback.comment,
                    created_at=feedback.created_at
                )
    
    async def cleanup_old_threads(self, days: int = 90):
        """Clean up old inactive threads"""
        async with self.async_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            await session.execute(
                update(ChatThread)
                .where(ChatThread.updated_at < cutoff_date)
                .where(ChatThread.status == "active")
                .values(status="archived")
            )
            await session.commit()

# Global service instance
_chat_service: Optional[ChatPersistenceService] = None

def get_chat_service() -> ChatPersistenceService:
    """Get the global chat persistence service instance"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatPersistenceService()
    return _chat_service

async def init_chat_database():
    """Initialize the chat database"""
    service = get_chat_service()
    await service.init_database()