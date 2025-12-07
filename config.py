"""Configuration management for the crawler application."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):

    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Groq Configuration
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "meta-llama/llama-4-maverick-17b-128e-instruct")
    use_groq_fallback: bool = os.getenv("USE_GROQ_FALLBACK", "true").lower() == "true"
    
    # PostgreSQL Configuration
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    postgres_database: str = os.getenv("POSTGRES_DATABASE", "crawler_db")
    postgres_url: Optional[str] = os.getenv("POSTGRES_URL", None)  # Full PostgreSQL URL
    
    # Qdrant Configuration
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_url: Optional[str] = os.getenv("QDRANT_URL", None)  # Cloud Qdrant URL
    qdrant_api_key: Optional[str] = os.getenv("QDRANT_API_KEY", None)  # Cloud Qdrant API Key
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "crawler_vectors")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Crawler Configuration
    crawler_user_agent: str = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    crawler_timeout: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
    crawler_max_retries: int = int(os.getenv("CRAWLER_MAX_RETRIES", "3"))
    
    # LLM Configuration
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    llm_provider: str = os.getenv("LLM_PROVIDER", "auto")  # auto, openai, groq
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

