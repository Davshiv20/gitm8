"""Portfolio service for managing portfolios, themes, and analytics."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from database.models import (
    Portfolio,
    PortfolioTheme,
    PortfolioCustomization,
    PortfolioAnalytics,
    PortfolioSnapshot,
)
from services.cache_service import get_cache_service
from services.github_graphql_service import get_complete_user_profile_graphql

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service for portfolio business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = get_cache_service()
    
    async def create_portfolio(
        self,
        username: str,
        theme_id: int = 1,
        is_public: bool = True
    ) -> Portfolio:
        """Create a new portfolio."""
        # Check if portfolio already exists
        existing = await self.get_portfolio_by_username(username)
        if existing:
            raise HTTPException(status_code=400, detail=f"Portfolio for {username} already exists")
        
        # Verify theme exists
        theme = await self.get_theme(theme_id)
        if not theme:
            raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")
        
        # Create portfolio
        portfolio = Portfolio(
            username=username,
            theme_id=theme_id,
            is_public=is_public,
        )
        self.db.add(portfolio)
        await self.db.flush()
        
        # Create default customization
        customization = PortfolioCustomization(
            portfolio_id=portfolio.id,
            section_order=None,  # Default order
            hidden_sections=None,  # No hidden sections by default
        )
        self.db.add(customization)
        await self.db.commit()
        await self.db.refresh(portfolio)
        
        logger.info(f"Created portfolio for {username}")
        return portfolio
    
    async def get_portfolio_by_username(self, username: str) -> Optional[Portfolio]:
        """Get portfolio by username."""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.theme))
            .options(selectinload(Portfolio.customization))
            .where(Portfolio.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_portfolio_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID."""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.theme))
            .options(selectinload(Portfolio.customization))
            .where(Portfolio.id == portfolio_id)
        )
        return result.scalar_one_or_none()
    
    async def get_public_portfolio(self, username: str) -> Optional[Portfolio]:
        """Get public portfolio by username."""
        portfolio = await self.get_portfolio_by_username(username)
        if not portfolio or not portfolio.is_public:
            return None
        return portfolio
    
    async def update_portfolio(
        self,
        username: str,
        theme_id: Optional[int] = None,
        is_public: Optional[bool] = None,
        custom_domain: Optional[str] = None
    ) -> Portfolio:
        """Update portfolio settings."""
        portfolio = await self.get_portfolio_by_username(username)
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio for {username} not found")
        
        if theme_id is not None:
            theme = await self.get_theme(theme_id)
            if not theme:
                raise HTTPException(status_code=404, detail=f"Theme {theme_id} not found")
            portfolio.theme_id = theme_id
            # Clear theme cache
            await self.cache.set_theme_config(theme_id, theme.config_json)
        
        if is_public is not None:
            portfolio.is_public = is_public
        
        if custom_domain is not None:
            # Check if domain is already taken
            if custom_domain:
                existing = await self.db.execute(
                    select(Portfolio).where(
                        Portfolio.custom_domain == custom_domain,
                        Portfolio.id != portfolio.id
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(status_code=400, detail="Custom domain already in use")
            portfolio.custom_domain = custom_domain
        
        portfolio.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(portfolio)
        
        # Clear cache
        await self.cache.clear_user_cache(username)
        
        logger.info(f"Updated portfolio for {username}")
        return portfolio
    
    async def delete_portfolio(self, username: str) -> bool:
        """Delete portfolio."""
        portfolio = await self.get_portfolio_by_username(username)
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"Portfolio for {username} not found")
        
        await self.db.delete(portfolio)
        await self.db.commit()
        
        # Clear cache
        await self.cache.clear_user_cache(username)
        
        logger.info(f"Deleted portfolio for {username}")
        return True
    
    async def get_github_data(self, username: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get GitHub user data (from cache or fetch fresh)."""
        # Check cache first
        if not force_refresh:
            cached_data = await self.cache.get_github_user_data(username)
            if cached_data:
                logger.info(f"Using cached GitHub data for {username}")
                return cached_data
        
        # Fetch from GitHub
        try:
            logger.info(f"Fetching fresh GitHub data for {username}")
            github_data = await get_complete_user_profile_graphql(username)
            
            # Cache the data
            await self.cache.set_github_user_data(username, github_data)
            
            # Also save snapshot to database
            portfolio = await self.get_portfolio_by_username(username)
            if portfolio:
                await self.save_snapshot(portfolio.id, github_data)
            
            return github_data
        except Exception as e:
            logger.error(f"Error fetching GitHub data for {username}: {str(e)}")
            # Try to get from database snapshot as fallback
            if portfolio:
                snapshot = await self.get_latest_snapshot(portfolio.id)
                if snapshot:
                    logger.info(f"Using database snapshot for {username}")
                    return snapshot.data_json
            raise HTTPException(status_code=500, detail=f"Failed to fetch GitHub data: {str(e)}")
    
    async def save_snapshot(self, portfolio_id: int, data: Dict[str, Any]) -> PortfolioSnapshot:
        """Save GitHub data snapshot to database."""
        expires_at = datetime.utcnow() + timedelta(hours=24)  # Snapshots expire after 24 hours
        
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            data_json=data,
            expires_at=expires_at,
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        
        return snapshot
    
    async def get_latest_snapshot(self, portfolio_id: int) -> Optional[PortfolioSnapshot]:
        """Get latest valid snapshot for portfolio."""
        result = await self.db.execute(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.portfolio_id == portfolio_id,
                PortfolioSnapshot.expires_at > datetime.utcnow()
            )
            .order_by(PortfolioSnapshot.cached_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def track_view(
        self,
        portfolio_id: int,
        viewer_ip: Optional[str] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PortfolioAnalytics:
        """Track a portfolio view."""
        analytics = PortfolioAnalytics(
            portfolio_id=portfolio_id,
            viewer_ip=viewer_ip,
            referrer=referrer,
            user_agent=user_agent,
        )
        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)
        return analytics
    
    async def get_analytics(
        self,
        portfolio_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics data for portfolio."""
        query = select(PortfolioAnalytics).where(
            PortfolioAnalytics.portfolio_id == portfolio_id
        )
        
        if start_date:
            query = query.where(PortfolioAnalytics.viewed_at >= start_date)
        if end_date:
            query = query.where(PortfolioAnalytics.viewed_at <= end_date)
        
        result = await self.db.execute(query)
        views = result.scalars().all()
        
        # Calculate statistics
        total_views = len(views)
        
        # Group by date
        views_by_date: Dict[str, int] = {}
        for view in views:
            date_str = view.viewed_at.date().isoformat()
            views_by_date[date_str] = views_by_date.get(date_str, 0) + 1
        
        # Top referrers
        referrers: Dict[str, int] = {}
        for view in views:
            if view.referrer:
                # Extract domain from referrer
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(view.referrer).netloc
                    referrers[domain] = referrers.get(domain, 0) + 1
                except:
                    pass
        
        return {
            "total_views": total_views,
            "views_by_date": views_by_date,
            "top_referrers": dict(sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10]),
            "recent_views": [
                {
                    "viewed_at": view.viewed_at.isoformat(),
                    "viewer_ip": view.viewer_ip,
                    "referrer": view.referrer,
                }
                for view in views[-50:]  # Last 50 views
            ]
        }
    
    async def update_customization(
        self,
        portfolio_id: int,
        section_order: Optional[List[str]] = None,
        hidden_sections: Optional[List[str]] = None,
        custom_css: Optional[str] = None
    ) -> PortfolioCustomization:
        """Update portfolio customization."""
        result = await self.db.execute(
            select(PortfolioCustomization).where(
                PortfolioCustomization.portfolio_id == portfolio_id
            )
        )
        customization = result.scalar_one_or_none()
        
        if not customization:
            customization = PortfolioCustomization(portfolio_id=portfolio_id)
            self.db.add(customization)
        
        if section_order is not None:
            customization.section_order = section_order
        if hidden_sections is not None:
            customization.hidden_sections = hidden_sections
        if custom_css is not None:
            customization.custom_css = custom_css
        
        customization.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(customization)
        
        # Clear cache
        portfolio = await self.get_portfolio_by_id(portfolio_id)
        if portfolio:
            await self.cache.delete_portfolio_render(portfolio.username)
        
        return customization
    
    # Theme management
    async def get_theme(self, theme_id: int) -> Optional[PortfolioTheme]:
        """Get theme by ID."""
        # Check cache first
        cached_config = await self.cache.get_theme_config(theme_id)
        if cached_config:
            # Still need to get from DB for full object, but use cached config
            result = await self.db.execute(
                select(PortfolioTheme).where(PortfolioTheme.id == theme_id)
            )
            theme = result.scalar_one_or_none()
            if theme:
                theme.config_json = cached_config
            return theme
        
        result = await self.db.execute(
            select(PortfolioTheme).where(PortfolioTheme.id == theme_id)
        )
        theme = result.scalar_one_or_none()
        
        if theme:
            # Cache the config
            await self.cache.set_theme_config(theme_id, theme.config_json)
        
        return theme
    
    async def get_all_themes(self) -> List[PortfolioTheme]:
        """Get all available themes."""
        result = await self.db.execute(select(PortfolioTheme))
        return list(result.scalars().all())
    
    async def create_theme(
        self,
        name: str,
        description: Optional[str],
        config_json: Dict[str, Any]
    ) -> PortfolioTheme:
        """Create a new theme."""
        # Check if theme with same name exists
        existing = await self.db.execute(
            select(PortfolioTheme).where(PortfolioTheme.name == name)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Theme '{name}' already exists")
        
        theme = PortfolioTheme(
            name=name,
            description=description,
            config_json=config_json,
        )
        self.db.add(theme)
        await self.db.commit()
        await self.db.refresh(theme)
        
        # Cache the config
        await self.cache.set_theme_config(theme.id, config_json)
        
        return theme



