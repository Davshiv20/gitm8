"""Cache service using Upstash Redis REST API for serverless compatibility."""

import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from upstash_redis import Redis
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Global Redis client (lazy initialization)
_redis_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    """Get or create Redis client (lazy initialization). Returns None if not configured."""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    settings = get_settings()
    
    if not settings.upstash_redis_rest_url or not settings.upstash_redis_rest_token:
        logger.warning(
            "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN not set. "
            "Caching will be disabled. Set these for production."
        )
        return None
    
    try:
        _redis_client = Redis(
            url=settings.upstash_redis_rest_url,
            token=settings.upstash_redis_rest_token,
        )
        logger.info("✅ Redis client initialized")
        return _redis_client
    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis client: {str(e)}")
        logger.warning("Continuing without cache...")
        return None


class CacheService:
    """Cache service for GitHub data, portfolio renders, and theme configs."""
    
    # Cache key prefixes
    GITHUB_DATA_PREFIX = "github:user:"
    PORTFOLIO_RENDER_PREFIX = "portfolio:render:"
    THEME_CONFIG_PREFIX = "theme:config:"
    
    # TTL constants (in seconds)
    GITHUB_DATA_TTL = 3600  # 1 hour
    PORTFOLIO_RENDER_TTL = 1800  # 30 minutes
    THEME_CONFIG_TTL = 86400  # 24 hours (themes don't change often)
    
    def __init__(self):
        self.redis = get_redis_client()
    
    def _is_available(self) -> bool:
        """Check if Redis is available."""
        return self.redis is not None
    
    async def get_github_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get cached GitHub user data."""
        if not self._is_available():
            return None
        try:
            key = f"{self.GITHUB_DATA_PREFIX}{username}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached GitHub data for {username}: {str(e)}")
            return None
    
    async def set_github_user_data(self, username: str, data: Dict[str, Any]) -> bool:
        """Cache GitHub user data."""
        if not self._is_available():
            return False
        try:
            key = f"{self.GITHUB_DATA_PREFIX}{username}"
            value = json.dumps(data)
            await self.redis.setex(key, self.GITHUB_DATA_TTL, value)
            return True
        except Exception as e:
            logger.error(f"Error caching GitHub data for {username}: {str(e)}")
            return False
    
    async def get_portfolio_render(self, username: str) -> Optional[str]:
        """Get cached portfolio HTML render."""
        if not self._is_available():
            return None
        try:
            key = f"{self.PORTFOLIO_RENDER_PREFIX}{username}"
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Error getting cached portfolio render for {username}: {str(e)}")
            return None
    
    async def set_portfolio_render(self, username: str, html: str) -> bool:
        """Cache portfolio HTML render."""
        if not self._is_available():
            return False
        try:
            key = f"{self.PORTFOLIO_RENDER_PREFIX}{username}"
            await self.redis.setex(key, self.PORTFOLIO_RENDER_TTL, html)
            return True
        except Exception as e:
            logger.error(f"Error caching portfolio render for {username}: {str(e)}")
            return False
    
    async def get_theme_config(self, theme_id: int) -> Optional[Dict[str, Any]]:
        """Get cached theme configuration."""
        if not self._is_available():
            return None
        try:
            key = f"{self.THEME_CONFIG_PREFIX}{theme_id}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached theme config for theme {theme_id}: {str(e)}")
            return None
    
    async def set_theme_config(self, theme_id: int, config: Dict[str, Any]) -> bool:
        """Cache theme configuration."""
        if not self._is_available():
            return False
        try:
            key = f"{self.THEME_CONFIG_PREFIX}{theme_id}"
            value = json.dumps(config)
            await self.redis.setex(key, self.THEME_CONFIG_TTL, value)
            return True
        except Exception as e:
            logger.error(f"Error caching theme config for theme {theme_id}: {str(e)}")
            return False
    
    async def delete_github_user_data(self, username: str) -> bool:
        """Delete cached GitHub user data."""
        if not self._is_available():
            return False
        try:
            key = f"{self.GITHUB_DATA_PREFIX}{username}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cached GitHub data for {username}: {str(e)}")
            return False
    
    async def delete_portfolio_render(self, username: str) -> bool:
        """Delete cached portfolio render."""
        if not self._is_available():
            return False
        try:
            key = f"{self.PORTFOLIO_RENDER_PREFIX}{username}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cached portfolio render for {username}: {str(e)}")
            return False
    
    async def clear_user_cache(self, username: str) -> bool:
        """Clear all cache entries for a user."""
        if not self._is_available():
            return False
        try:
            github_key = f"{self.GITHUB_DATA_PREFIX}{username}"
            render_key = f"{self.PORTFOLIO_RENDER_PREFIX}{username}"
            await self.redis.delete(github_key, render_key)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache for {username}: {str(e)}")
            return False


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

