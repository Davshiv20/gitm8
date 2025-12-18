"""Portfolio API routes."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database.db import get_db
from services.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


# Request/Response models
class PortfolioCreateRequest(BaseModel):
    username: str
    theme_id: int = 1
    is_public: bool = True


class PortfolioUpdateRequest(BaseModel):
    theme_id: Optional[int] = None
    is_public: Optional[bool] = None
    custom_domain: Optional[str] = None


class CustomizationUpdateRequest(BaseModel):
    section_order: Optional[list[str]] = None
    hidden_sections: Optional[list[str]] = None
    custom_css: Optional[str] = None


@router.post("")
async def create_portfolio(
    request: PortfolioCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new portfolio."""
    try:
        service = PortfolioService(db)
        portfolio = await service.create_portfolio(
            username=request.username,
            theme_id=request.theme_id,
            is_public=request.is_public
        )
        return {
            "success": True,
            "portfolio": {
                "id": portfolio.id,
                "username": portfolio.username,
                "theme_id": portfolio.theme_id,
                "is_public": portfolio.is_public,
                "custom_domain": portfolio.custom_domain,
                "created_at": portfolio.created_at.isoformat(),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create portfolio: {str(e)}")


@router.get("/{username}")
async def get_portfolio(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio by username (includes customization)."""
    try:
        service = PortfolioService(db)
        portfolio = await service.get_portfolio_by_username(username)
        
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio for {username} not found")
        
        return {
            "success": True,
            "portfolio": {
                "id": portfolio.id,
                "username": portfolio.username,
                "theme_id": portfolio.theme_id,
                "is_public": portfolio.is_public,
                "custom_domain": portfolio.custom_domain,
                "created_at": portfolio.created_at.isoformat(),
                "updated_at": portfolio.updated_at.isoformat(),
                "theme": {
                    "id": portfolio.theme.id,
                    "name": portfolio.theme.name,
                    "description": portfolio.theme.description,
                    "config": portfolio.theme.config_json,
                } if portfolio.theme else None,
                "customization": {
                    "section_order": portfolio.customization.section_order if portfolio.customization else None,
                    "hidden_sections": portfolio.customization.hidden_sections if portfolio.customization else None,
                    "custom_css": portfolio.customization.custom_css if portfolio.customization else None,
                } if portfolio.customization else None,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {str(e)}")


@router.get("/{username}/public")
async def get_public_portfolio(
    username: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get public portfolio view (tracks analytics)."""
    try:
        service = PortfolioService(db)
        portfolio = await service.get_public_portfolio(username)
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found or not public")
        
        # Track view
        try:
            viewer_ip = request.client.host if request.client else None
            referrer = request.headers.get("referer")
            user_agent = request.headers.get("user-agent")
            await service.track_view(
                portfolio_id=portfolio.id,
                viewer_ip=viewer_ip,
                referrer=referrer,
                user_agent=user_agent
            )
        except Exception as e:
            logger.warning(f"Failed to track view: {str(e)}")
        
        # Get GitHub data
        github_data = await service.get_github_data(username)
        
        return {
            "success": True,
            "portfolio": {
                "id": portfolio.id,
                "username": portfolio.username,
                "theme_id": portfolio.theme_id,
                "custom_domain": portfolio.custom_domain,
                "theme": {
                    "id": portfolio.theme.id,
                    "name": portfolio.theme.name,
                    "description": portfolio.theme.description,
                    "config": portfolio.theme.config_json,
                } if portfolio.theme else None,
                "customization": {
                    "section_order": portfolio.customization.section_order if portfolio.customization else None,
                    "hidden_sections": portfolio.customization.hidden_sections if portfolio.customization else None,
                    "custom_css": portfolio.customization.custom_css if portfolio.customization else None,
                } if portfolio.customization else None,
            },
            "github_data": github_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting public portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get public portfolio: {str(e)}")


@router.put("/{username}")
async def update_portfolio(
    username: str,
    request: PortfolioUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update portfolio settings."""
    try:
        service = PortfolioService(db)
        portfolio = await service.update_portfolio(
            username=username,
            theme_id=request.theme_id,
            is_public=request.is_public,
            custom_domain=request.custom_domain
        )
        return {
            "success": True,
            "portfolio": {
                "id": portfolio.id,
                "username": portfolio.username,
                "theme_id": portfolio.theme_id,
                "is_public": portfolio.is_public,
                "custom_domain": portfolio.custom_domain,
                "updated_at": portfolio.updated_at.isoformat(),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update portfolio: {str(e)}")


@router.delete("/{username}")
async def delete_portfolio(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete portfolio."""
    try:
        service = PortfolioService(db)
        await service.delete_portfolio(username)
        return {"success": True, "message": f"Portfolio for {username} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete portfolio: {str(e)}")


@router.post("/{username}/refresh")
async def refresh_portfolio_data(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """Refresh GitHub data for portfolio."""
    try:
        service = PortfolioService(db)
        portfolio = await service.get_portfolio_by_username(username)
        
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio for {username} not found")
        
        # Force refresh
        github_data = await service.get_github_data(username, force_refresh=True)
        
        return {
            "success": True,
            "message": f"Portfolio data refreshed for {username}",
            "github_data": github_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing portfolio data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh portfolio data: {str(e)}")


@router.put("/{username}/customization")
async def update_customization(
    username: str,
    request: CustomizationUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update portfolio customization."""
    try:
        service = PortfolioService(db)
        portfolio = await service.get_portfolio_by_username(username)
        
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio for {username} not found")
        
        customization = await service.update_customization(
            portfolio_id=portfolio.id,
            section_order=request.section_order,
            hidden_sections=request.hidden_sections,
            custom_css=request.custom_css
        )
        
        return {
            "success": True,
            "customization": {
                "section_order": customization.section_order,
                "hidden_sections": customization.hidden_sections,
                "custom_css": customization.custom_css,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update customization: {str(e)}")


@router.get("/{username}/analytics")
async def get_analytics(
    username: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get analytics data for portfolio."""
    try:
        service = PortfolioService(db)
        portfolio = await service.get_portfolio_by_username(username)
        
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio for {username} not found")
        
        # Parse dates
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        analytics = await service.get_analytics(
            portfolio_id=portfolio.id,
            start_date=start,
            end_date=end
        )
        
        return {
            "success": True,
            "analytics": analytics,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# Theme routes
@router.get("/themes", tags=["themes"])
async def get_themes(db: AsyncSession = Depends(get_db)):
    """Get all available themes."""
    try:
        service = PortfolioService(db)
        themes = await service.get_all_themes()
        return {
            "success": True,
            "themes": [
                {
                    "id": theme.id,
                    "name": theme.name,
                    "description": theme.description,
                    "config": theme.config_json,
                }
                for theme in themes
            ]
        }
    except Exception as e:
        logger.error(f"Error getting themes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get themes: {str(e)}")


@router.get("/themes/{theme_id}", tags=["themes"])
async def get_theme(theme_id: int, db: AsyncSession = Depends(get_db)):
    """Get theme by ID."""
    try:
        service = PortfolioService(db)
        theme = await service.get_theme(theme_id)
        
        if not theme:
            raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")
        
        return {
            "success": True,
            "theme": {
                "id": theme.id,
                "name": theme.name,
                "description": theme.description,
                "config": theme.config_json,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting theme: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get theme: {str(e)}")



