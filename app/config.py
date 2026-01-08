"""
Configuration Management
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, Union


class Settings(BaseSettings):
    """Application Settings"""
    
    # API
    API_TITLE: str = "PostgreSQL Chat API"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Security
    API_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: Union[int, str] = Field(default=5432, description="PostgreSQL port")
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    POSTGRESQL_URL: Optional[str] = None  # Alternative: full connection string
    POSTGRESQL_DATABASE: Optional[str] = None  # Alternative database name
    
    @field_validator('DB_PORT', mode='before')
    @classmethod
    def parse_db_port(cls, v: Union[int, str, None]) -> int:
        """Parse DB_PORT from string or int, defaulting to 5432 if empty"""
        if v is None or v == '':
            return 5432
        if isinstance(v, str):
            return int(v) if v.strip() else 5432
        return int(v)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    
    # LLM
    OPENAI_API_KEY: Optional[str] = None
    API_KEY_OPENAI: Optional[str] = None  # Alternative name
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 1000
    
    # Gemini (for question refinement)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_TOKENS: int = 500
    
    # Security & Privacy
    SHOW_SQL_TO_USER: bool = Field(True, description="Show SQL query in response (set False in production)")
    
    # RAG
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    VECTOR_DIMENSION: int = 1536
    RAG_TOP_K: int = 5
    
    # SQL Safety
    SQL_TIMEOUT_SECONDS: int = 30
    SQL_MAX_ROWS: int = 1000
    SQL_ALLOWED_OPERATIONS: list[str] = ["SELECT"]
    
    # Observability
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    ENABLE_METRICS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
