import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes import routes
# from routes.portfolio_routes import router as portfolio_router
from fastapi.middleware.cors import CORSMiddleware
from config.settings import validate_settings, get_settings

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
        
        # Initialize HTTP client session for external API calls
        logger.info("🌐 Initializing HTTP client session...")
        from services.github_graphql_service import GitHubGraphQLService
        from services.llm_service import init_llm_client
        import aiohttp
        
        # Pre-create the GitHub session (optional - it will be created on first request anyway)
        # This ensures session is ready and validates GitHub token early
        try:
            await GitHubGraphQLService.get_session()
            logger.info("✅ GitHub HTTP client session initialized successfully")
        except Exception as session_error:
            logger.warning(f"⚠️  GitHub session initialization warning: {str(session_error)}")
            logger.warning("   Session will be created on first request")
        
        # Initialize LLM client with shared aiohttp session
        try:
            timeout = aiohttp.ClientTimeout(total=30, connect=5)
            llm_session = aiohttp.ClientSession(timeout=timeout)
            await init_llm_client(llm_session)
            # Store session in app state for cleanup
            app.state.llm_session = llm_session
        except Exception as llm_error:
            logger.error(f"❌ Failed to initialize LLM client: {str(llm_error)}")
            raise
        
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
        
        # Close GitHub session
        await GitHubGraphQLService.release_session()
        
        # Close LLM client and its session
        await cleanup_llm_client()
        if hasattr(app.state, 'llm_session') and app.state.llm_session:
            await app.state.llm_session.close()
            logger.info("✅ LLM session closed")
        
        logger.info("✅ HTTP client sessions closed successfully")
    except Exception as e:
        logger.error(f"⚠️  Error closing HTTP sessions: {str(e)}")
    
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
# app.include_router(portfolio_router)

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
        # Check HTTP sessions
        from services.github_graphql_service import GitHubGraphQLService
        github_session_status = "active" if GitHubGraphQLService._shared_session else "not_initialized"
        
        # Check LLM client
        llm_session_status = "active" if hasattr(app.state, 'llm_session') and app.state.llm_session else "not_initialized"
        
        return {
            "status": "healthy",
            "github_session": github_session_status,
            "llm_session": llm_session_status
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