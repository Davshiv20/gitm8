"""
Centralized configuration management for GitM8 backend.
Supports environment-specific configuration files (.env.development, .env.stag, .env.production).

Features:
- LRU cache for performance (settings loaded once and cached)
- Environment-specific configuration loading
- Type-safe validation with Pydantic
- Automatic reload disable for production environments
- Special handling for CORS wildcard origins
- Required environment variables validation with startup logging
"""

import os
import logging
from typing import List, Optional
from functools import lru_cache
from pydantic import BaseSettings, Field, field_validator, ValidationInfo, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings with environment-specific loading."""

    # Environment Configuration
    env: str = Field(default="development", description="Environment (development, stag, production)")

    # CORS Configuration
    allowed_origins_str: str = Field(
        default="http://localhost:5173,http://localhost:8000",
        alias="ALLOWED_ORIGINS",
        description="Allowed CORS origins as comma-separated string"
    )

    # GitHub Configuration
    github_token: str = Field(description="GitHub API token for authentication")
    
    # Google Gemini Configuration (optional, for fallback)
    google_api_key: Optional[str] = Field(default=None, description="Google API key for Gemini")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8180, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload (development only)")
    debug: bool = Field(default=False, description="Debug mode")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **data):
        # Determine which env file to load based on ENV variable at runtime
        env = os.getenv('ENV', 'development')
        env_file = f".env.{env}"

        # Update model config with the correct env file
        self.__class__.model_config = SettingsConfigDict(
            env_file=env_file,
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

        super().__init__(**data)

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Validate environment value."""
        valid_envs = ["development", "stag", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {', '.join(valid_envs)}")
        return v

    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, v: str) -> str:
        """Validate GitHub token is provided."""
        if not v:
            raise ValueError("GitHub token is required")
        return v

    @field_validator("allowed_origins_str", mode="before")
    @classmethod
    def validate_allowed_origins_str(cls, v) -> str:
        """Validate allowed origins string with fallback."""
        if v is None:
            return "http://localhost:5173,http://localhost:8000"
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator("reload")
    @classmethod
    def validate_reload(cls, v: bool, info: ValidationInfo) -> bool:
        """Disable reload for production environments."""
        env = info.data.get("env", "development")
        if env in ["stag", "production"]:
            return False
        return v

    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v: bool, info: ValidationInfo) -> bool:
        """Enable debug for development environment."""
        env = info.data.get("env", "development")
        if env == "development":
            return True
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env == "development"

    @property
    def is_stag(self) -> bool:
        """Check if running in stag environment."""
        return self.env == "stag"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    @property
    def allowed_origins(self) -> List[str]:
        """Convert comma-separated string to list of origins with special handling for wildcard."""
        origins_str = self.allowed_origins_str.strip()

        # Handle wildcard case
        if origins_str == "*":
            return ["*"]

        # Split by comma and clean up whitespace for multiple origins
        origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

        # Remove duplicates while preserving order
        seen = set()
        unique_origins = []
        for origin in origins:
            if origin not in seen:
                seen.add(origin)
                unique_origins.append(origin)

        return unique_origins

    def validate_required_env_vars(self) -> None:
        """Validate all required environment variables and log missing ones."""
        logger = logging.getLogger(__name__)
        
        missing_vars = []
        
        # Check required variables
        if not self.github_token:
            missing_vars.append("GITHUB_TOKEN")
        
        if missing_vars:
            logger.error("❌ Missing required environment variables:")
            for var in missing_vars:
                logger.error(f"   - {var}")
            logger.error("Please set these environment variables before starting the server.")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Log successful validation
        logger.info("✅ All required environment variables are set")
        logger.info(f"   - Environment: {self.env}")
        logger.info(f"   - Server: {self.host}:{self.port}")
        logger.info(f"   - Debug mode: {self.debug}")
        logger.info(f"   - CORS origins: {', '.join(self.allowed_origins)}")
        
        if self.google_api_key:
            logger.info("   - Google API key: ✅ Set")
        else:
            logger.warning("   - Google API key: ⚠️  Not set (Gemini fallback disabled)")


@lru_cache(maxsize=10)
def get_settings() -> Settings:
    """Get cached settings instance with LRU cache for performance."""
    return Settings()


def validate_settings() -> Settings:
    """Validate settings and return them, logging any issues."""
    try:
        settings = get_settings()
        settings.validate_required_env_vars()
        return settings
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Settings validation failed: {str(e)}")
        raise


# Create global settings instance with caching
settings = get_settings()

# Export commonly used settings
ENV = settings.env
DEBUG = settings.debug
GITHUB_TOKEN = settings.github_token
GOOGLE_API_KEY = settings.google_api_key