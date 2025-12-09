"""Database connection and session management for GCP Cloud SQL."""

import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from config.settings import get_settings
from database.base import Base

logger = logging.getLogger(__name__)

# Global engine and session factory (lazy initialization)
_engine: Optional[create_async_engine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_database_url() -> str:
    """Get database URL from settings."""
    settings = get_settings()
    database_url = settings.database_url
    
    if not database_url:
        # Default to local PostgreSQL for development
        database_url = "postgresql://postgres:postgres@localhost:5432/gitm8_portfolio"
        logger.warning(
            "DATABASE_URL not set, using default local PostgreSQL: "
            "postgresql://postgres:postgres@localhost:5432/gitm8_portfolio"
        )
    if "?sslmode=" in database_url:
        database_url= database_url.split("?")[0]
    
    # Convert postgresql:// to postgresql+asyncpg:// for async driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif not database_url.startswith("postgresql+asyncpg://"):
        raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
    
    return database_url

def init_db() -> None:
    """Initialize database connection (lazy initialization)."""
    global _engine, _session_factory
    
    if _engine is not None:
        logger.info("Database already initialized")
        return
    
    try:
        database_url = get_database_url()
        
        # Create async engine with connection pooling
        # Use NullPool for serverless (Vercel), regular pool for local development
        from config.settings import get_settings
        settings = get_settings()
        is_local = "localhost" in database_url or "127.0.0.1" in database_url
        
        _engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
        poolclass=NullPool,  # best practice for async setups
        connect_args={
            "server_settings": {"application_name": "gitm8_backend"}
        }
        )
        # Create session factory
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        logger.info("✅ Database connection initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (dependency for FastAPI routes)."""
    global _session_factory
    
    # Lazy initialization on first request
    if _session_factory is None:
        init_db()
    
    if _session_factory is None:
        raise RuntimeError("Database session factory not initialized")
    
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables (for migrations)."""
    global _engine
    
    if _engine is None:
        init_db()
    
    if _engine is None:
        raise RuntimeError("Database engine not initialized")
    
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Database tables created")


async def drop_tables() -> None:
    """Drop all database tables (use with caution!)."""
    global _engine
    
    if _engine is None:
        init_db()
    
    if _engine is None:
        raise RuntimeError("Database engine not initialized")
    
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.info("⚠️  Database tables dropped")

def get_engine():
    global _engine
    if _engine is None:
        init_db()
    return _engine
