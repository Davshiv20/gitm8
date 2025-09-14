import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.routing import APIRouter
from routes import routes
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
    # Startup
    logger.info("🚀 Starting GitM8 backend server...")
    
    try:
        # Validate settings and environment variables
        settings = validate_settings()
        logger.info("✅ Settings validation completed successfully")
        
        # Store settings in app state for access in routes
        app.state.settings = settings
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down GitM8 backend server...")


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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
