"""
Configuration management for BrandAI application.
Loads environment variables and provides configuration settings.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")
    
    @property
    def GOOGLE_APPLICATION_CREDENTIALS(self) -> str:
        """Get GCP credentials path."""
        env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if env_path:
            return env_path
        
        # Default based on environment
        if self._is_docker:
            return "/app/config/gcp/service-account.json"
        else:
            return str(self.base_dir / "config" / "gcp" / "service-account.json")
    
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Vertex AI
    VERTEX_AI_ENABLED: bool = os.getenv("VERTEX_AI_ENABLED", "true").lower() == "true"
    
    # Application
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    @property
    def _is_docker(self) -> bool:
        """Check if running in Docker container."""
        # Check if /app exists (Docker path) or if we're in a container
        return Path("/app").exists() or os.path.exists("/.dockerenv")
    
    @property
    def base_dir(self) -> Path:
        """Get base directory of the application."""
        if self._is_docker:
            # In Docker, base is /app
            return Path("/app")
        else:
            # Local development, go up to project root from backend/app/
            return Path(__file__).parent.parent.parent
    
    @property
    def storage_dir(self) -> Path:
        """Get storage directory path."""
        # Check if explicitly set in env
        env_storage = os.getenv("STORAGE_PATH")
        if env_storage:
            env_path = Path(env_storage)
            # If env path is Docker path but we're not in Docker, ignore it
            if str(env_path).startswith("/app/") and not self._is_docker:
                # Use local path instead
                return self.base_dir / "data" / "storage"
            return env_path
        
        # Default paths based on environment
        if self._is_docker:
            return Path("/app/data/storage")
        else:
            return self.base_dir / "data" / "storage"
    
    @property
    def rag_dir(self) -> Path:
        """Get RAG directory path."""
        # Check if explicitly set in env
        env_rag = os.getenv("RAG_PATH")
        if env_rag:
            env_path = Path(env_rag)
            # If env path is Docker path but we're not in Docker, ignore it
            if str(env_path).startswith("/app/") and not self._is_docker:
                # Use local path instead
                return self.base_dir / "data" / "rag"
            return env_path
        
        # Default paths based on environment
        if self._is_docker:
            return Path("/app/data/rag")
        else:
            return self.base_dir / "data" / "rag"
    
    def validate(self) -> bool:
        """Validate that required settings are present."""
        # Only validate in production, allow missing in development
        if self.APP_ENV == "production":
            required_settings = [
                ("GCP_PROJECT_ID", self.GCP_PROJECT_ID),
                ("GEMINI_API_KEY", self.GEMINI_API_KEY),
            ]
            
            missing = [name for name, value in required_settings if not value]
            
            if missing:
                raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True


# Global settings instance
settings = Settings()
