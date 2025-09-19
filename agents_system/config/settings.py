"""Configuration settings for the Super Admin Agent system."""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_organization: Optional[str] = Field(None, env="OPENAI_ORGANIZATION")
    
    # Models Configuration
    text_model: str = Field("gpt-4o-mini", env="TEXT_MODEL")
    voice_model: str = Field("whisper-1", env="VOICE_MODEL")
    embedding_model: str = Field("text-embedding-3-small", env="EMBEDDING_MODEL")
    
    # Supabase Configuration
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    
    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379/1", env="REDIS_URL")
    
    # JWT Configuration
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    
    # Application Configuration
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8001, env="APP_PORT")
    debug: bool = Field(False, env="DEBUG")
    
    # CORS Configuration
    allowed_origins: str = Field(
        "http://localhost:3000,http://localhost:8000", 
        env="ALLOWED_ORIGINS"
    )
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return self.allowed_origins
    
    # File Upload Configuration
    max_file_size: int = Field(100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    upload_dir: str = Field("uploads", env="UPLOAD_DIR")
    supported_file_types: str = Field(
        "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation,text/csv,image/jpeg,image/png,image/gif,text/plain",
        env="SUPPORTED_FILE_TYPES"
    )
    
    @property
    def supported_file_types_list(self) -> List[str]:
        """Parse supported file types from comma-separated string."""
        if isinstance(self.supported_file_types, str):
            return [file_type.strip() for file_type in self.supported_file_types.split(",") if file_type.strip()]
        return self.supported_file_types
    
    # Vector Store Configuration
    vector_dimension: int = Field(1536, env="VECTOR_DIMENSION")  # text-embedding-3-small
    similarity_threshold: float = Field(0.8, env="SIMILARITY_THRESHOLD")
    max_results: int = Field(10, env="MAX_RESULTS")
    
    # Agent Configuration
    super_admin_system_prompt: str = Field(
        "You are a Super Admin Agent for an educational platform. You can create and manage course assistants, "
        "answer questions about the platform (institutions, students, teachers, admins, parents), and perform "
        "platform operations via natural language. When creating courses, gather requirements and create "
        "specialized course assistants with appropriate role instructions and constraints.",
        env="SUPER_ADMIN_SYSTEM_PROMPT"
    )
    
    default_course_assistant_prompt: str = Field(
        "You are a specialized course instructor assistant. Your primary role is to help students learn and "
        "understand the subject matter. Use uploaded course materials as your primary knowledge base and "
        "follow the specific role instructions and constraints provided by the Super Admin.",
        env="DEFAULT_COURSE_ASSISTANT_PROMPT"
    )
    
    # Session Configuration
    session_timeout: int = Field(3600, env="SESSION_TIMEOUT")  # 1 hour
    max_sessions_per_user: int = Field(50, env="MAX_SESSIONS_PER_USER")
    
    class Config:
        """Pydantic configuration."""
        env_file = "agents/.env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
