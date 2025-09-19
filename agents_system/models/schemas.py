"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class AgentRole(str, Enum):
    """Agent role enumeration."""
    SUPER_ADMIN = "super_admin"
    COURSE_INSTRUCTOR = "course_instructor"


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FileType(str, Enum):
    """Supported file types."""
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    CSV = "text/csv"
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    TXT = "text/plain"


# Base Models
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# Message Models
class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str = Field(..., min_length=1, max_length=10000)
    role: MessageRole = MessageRole.USER
    session_id: str = Field(..., min_length=1)
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str
    content: str
    role: MessageRole
    session_id: str
    user_id: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Schema for chat requests."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    stream: bool = Field(default=False)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4000)
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Schema for chat responses."""
    message: MessageResponse
    session_id: str
    usage: Optional[Dict[str, Any]] = None


# Session Models
class SessionCreate(BaseModel):
    """Schema for creating a new chat session."""
    title: Optional[str] = Field(None, max_length=255)
    agent_type: AgentRole = AgentRole.SUPER_ADMIN
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    """Schema for updating a chat session."""
    title: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Schema for session response."""
    id: str
    title: str
    agent_type: AgentRole
    agent_id: Optional[str] = None
    user_id: str
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


# Course Assistant Models
class CourseAssistantCreate(BaseModel):
    """Schema for creating a course assistant."""
    name: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    role_instructions: str = Field(..., min_length=1, max_length=5000)
    constraints: Optional[str] = Field(None, max_length=2000)
    system_prompt: Optional[str] = Field(None, max_length=3000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4000)
    metadata: Optional[Dict[str, Any]] = None


class CourseAssistantUpdate(BaseModel):
    """Schema for updating a course assistant."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    role_instructions: Optional[str] = Field(None, min_length=1, max_length=5000)
    constraints: Optional[str] = Field(None, max_length=2000)
    system_prompt: Optional[str] = Field(None, max_length=3000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class CourseAssistantResponse(BaseModel):
    """Schema for course assistant response."""
    id: str
    name: str
    subject: str
    description: Optional[str] = None
    role_instructions: str
    constraints: Optional[str] = None
    system_prompt: str
    temperature: float
    max_tokens: Optional[int] = None
    is_active: bool = True
    openai_assistant_id: Optional[str] = None
    vector_store_id: Optional[str] = None
    file_count: int = 0
    session_count: int = 0
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


# File Models
class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    upload_path: str
    openai_file_id: Optional[str] = None
    processing_status: str = "pending"
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class FileResponse(BaseModel):
    """Schema for file response."""
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    upload_path: str
    openai_file_id: Optional[str] = None
    processing_status: str
    error_message: Optional[str] = None
    assistant_id: Optional[str] = None
    vector_store_id: Optional[str] = None
    chunk_count: int = 0
    uploaded_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class FileProcessRequest(BaseModel):
    """Schema for file processing request."""
    file_ids: List[str] = Field(..., min_items=1)
    assistant_id: str = Field(..., min_length=1)
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)


# Vector Store Models
class VectorSearchRequest(BaseModel):
    """Schema for vector similarity search."""
    query: str = Field(..., min_length=1, max_length=1000)
    assistant_id: Optional[str] = None
    vector_store_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata_filter: Optional[Dict[str, Any]] = None


class VectorSearchResult(BaseModel):
    """Schema for vector search result."""
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    file_id: Optional[str] = None
    chunk_id: Optional[str] = None


class VectorSearchResponse(BaseModel):
    """Schema for vector search response."""
    results: List[VectorSearchResult]
    query: str
    total_results: int
    search_time_ms: float


# Platform Models
class PlatformStats(BaseModel):
    """Schema for platform statistics."""
    total_users: int
    total_institutions: int
    total_courses: int
    total_course_assistants: int
    total_chat_sessions: int
    total_messages: int
    active_sessions_24h: int
    files_uploaded: int
    storage_used_mb: float


class PlatformOperationRequest(BaseModel):
    """Schema for platform operation requests."""
    operation: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class PlatformOperationResponse(BaseModel):
    """Schema for platform operation responses."""
    operation: str
    status: str
    result: Optional[Dict[str, Any]] = None
    message: str
    executed_at: datetime


# Error Models
class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""
    error: str = "Validation Error"
    detail: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Health Check Models
class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str]
    version: str = "1.0.0"


# Batch Operation Models
class BatchOperation(BaseModel):
    """Schema for batch operations."""
    operation_type: str
    items: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None


class BatchOperationResponse(BaseModel):
    """Schema for batch operation responses."""
    operation_type: str
    total_items: int
    successful_items: int
    failed_items: int
    results: List[Dict[str, Any]]
    errors: List[str]
    executed_at: datetime = Field(default_factory=datetime.utcnow)


# WebSocket Models
class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str
    data: Dict[str, Any]
    session_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketResponse(BaseModel):
    """Schema for WebSocket responses."""
    type: str
    data: Dict[str, Any]
    status: str = "success"
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
