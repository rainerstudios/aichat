"""
Chat persistence models for PostgreSQL storage
Replaces Assistant-UI Cloud with local database
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255))
    display_name = Column(String(255))
    pterodactyl_user_id = Column(Integer, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    threads = relationship("ChatThread", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("MessageFeedback", back_populates="user", cascade="all, delete-orphan")

class ChatThread(Base):
    __tablename__ = "chat_threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False, default="New Chat")
    status = Column(String(50), default="active", index=True)  # active, archived, deleted
    server_id = Column(String(255))  # Pterodactyl server context
    server_name = Column(String(255))
    thread_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    message_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="threads")
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("chat_threads.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system, tool
    content = Column(JSONB, nullable=False)  # Assistant-UI format
    status = Column(String(50), default="complete")  # running, complete, error
    tool_calls = Column(JSONB, default=[])
    msg_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    sequence_number = Column(Integer, nullable=False)
    
    # Relationships
    thread = relationship("ChatThread", back_populates="messages")
    feedback = relationship("MessageFeedback", back_populates="message", cascade="all, delete-orphan")
    
    # Composite index for thread ordering
    __table_args__ = (
        Index('ix_messages_thread_sequence', 'thread_id', 'sequence_number'),
    )

class MessageFeedback(Base):
    __tablename__ = "message_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(String(20), nullable=False)  # thumbs_up, thumbs_down
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("ChatMessage", back_populates="feedback")
    user = relationship("User", back_populates="feedback")
    
    # Unique constraint: one feedback per user per message
    __table_args__ = (
        Index('ix_feedback_unique', 'message_id', 'user_id', unique=True),
    )

# Pydantic models for API responses
class UserResponse(BaseModel):
    id: str
    user_id: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    pterodactyl_user_id: Optional[int] = None
    created_at: datetime
    last_active: datetime
    
    class Config:
        from_attributes = True

class ThreadResponse(BaseModel):
    id: str
    thread_id: str
    user_id: str
    title: str
    status: str
    server_id: Optional[str] = None
    server_name: Optional[str] = None
    thread_metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    message_count: int
    
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: str
    message_id: str
    thread_id: str
    role: str
    content: List[Dict[str, Any]]
    status: str
    tool_calls: List[Dict[str, Any]] = []
    thread_metadata: Dict[str, Any] = {}
    created_at: datetime
    sequence_number: int
    
    class Config:
        from_attributes = True

class FeedbackResponse(BaseModel):
    id: str
    message_id: str
    user_id: str
    rating: str
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Request models
class CreateThreadRequest(BaseModel):
    title: str = "New Chat"
    server_id: Optional[str] = None
    server_name: Optional[str] = None
    thread_metadata: Dict[str, Any] = {}

class CreateMessageRequest(BaseModel):
    role: str
    content: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]] = []
    thread_metadata: Dict[str, Any] = {}

class CreateFeedbackRequest(BaseModel):
    rating: str  # thumbs_up, thumbs_down
    comment: Optional[str] = None