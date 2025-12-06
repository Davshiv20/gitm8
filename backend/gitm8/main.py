import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.routing import APIRouter
from routes import routes
# from routes.portfolio_routes import router as portfolio_router
from fastapi.middleware.cors import CORSMiddleware
from config.settings import validate_settings, get_settings
from database.db import init_db, get_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # ============================================================
    # STARTUP
    # ============================================================
    logger.info("🚀 Starting GitM8 backend server...")
    
    try:
        # Validate settings and environment variables
        settings = validate_settings()
        logger.info("✅ Settings validation completed successfully")
        
        # Store settings in app state for access in routes
        app.state.settings = settings
        
        # Initialize and test database connection
        logger.info("🔌 Initializing database connection...")
        init_db()
        
        # Test database connection
        try:
            from sqlalchemy import text
            engine = get_engine()

            if engine is None:
                logger.error("❌ Database engine not initialized")
                raise RuntimeError("Database engine not initialized")

            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.scalar()
                logger.info("✅ Database connection successful")
        except Exception as db_error:
            logger.error(f"❌ Database connection failed: {str(db_error)}")
            logger.error("   Please check your DATABASE_URL and ensure PostgreSQL is running")
            raise
        
        # Initialize HTTP client session for external API calls
        logger.info("🌐 Initializing HTTP client session...")
        from services.github_graphql_service import GitHubGraphQLService
        
        # Pre-create the session (optional - it will be created on first request anyway)
        # This ensures session is ready and validates GitHub token early
        try:
            await GitHubGraphQLService.get_session()
            logger.info("✅ HTTP client session initialized successfully")
        except Exception as session_error:
            logger.warning(f"⚠️  HTTP session initialization warning: {str(session_error)}")
            logger.warning("   Session will be created on first request")
        
        logger.info("✅ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        raise
    
    # ============================================================
    # APPLICATION RUNS HERE
    # ============================================================
    yield
    
    # ============================================================
    # SHUTDOWN
    # ============================================================
    logger.info("🛑 Shutting down GitM8 backend server...")
    
    # Close HTTP client sessions
    logger.info("🔌 Closing HTTP client sessions...")
    try:
        from services.github_graphql_service import GitHubGraphQLService
        from services.llm_service import cleanup_llm_client
        await GitHubGraphQLService.release_session()
        await cleanup_llm_client()
        logger.info("✅ HTTP client sessions closed successfully")
    except Exception as e:
        logger.error(f"⚠️  Error closing HTTP sessions: {str(e)}")
    
    # Close database connections
    logger.info("🔌 Closing database connections...")
    try:
        engine = get_engine()
        if engine:
            await engine.dispose()
            logger.info("✅ Database connections closed successfully")
    except Exception as e:
        logger.error(f"⚠️  Error closing database: {str(e)}")
    
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="GitM8 Backend",
    description="GitHub collaboration analysis API",
    version="1.0.0",
    lifespan=lifespan
)

# Get settings for CORS configuration
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include manual routes
app.include_router(routes.router)
app.include_router(portfolio_router)

# ============================================================
# AUTO-GENERATED ROUTES FROM DECORATORS
# ============================================================
from services.endpoint_registry import generate_routes
from services.github_graphql_service import GitHubGraphQLService

# Initialize services (this triggers decorator registration)
# Note: Don't need to create instance here if using class methods
# But we do it to trigger the @register_wrapper decorators
github_service = GitHubGraphQLService()

# Generate routes from registry
auto_router = generate_routes(
    prefix="/api/github",  # More specific prefix for GitHub endpoints
    service_instances={"GitHubGraphQLService": github_service}
)
app.include_router(auto_router)

@app.get("/")
async def root():
    return {
        "message": "I AM THE BACKEND",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database
        engine = get_engine()
        db_status = "connected" if engine else "disconnected"
        
        # Check HTTP session
        from services.github_graphql_service import GitHubGraphQLService
        session_status = "active" if GitHubGraphQLService._shared_session else "not_initialized"
        
        return {
            "status": "healthy",
            "database": db_status,
            "http_session": session_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Set to False in production
        log_level="info"
    )