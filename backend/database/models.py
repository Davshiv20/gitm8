"""SQLAlchemy models for portfolio feature."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import relationship
from database.base import Base


class Portfolio(Base):
    """Portfolio metadata model."""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    theme_id = Column(Integer, ForeignKey("portfolio_themes.id"), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)           
    custom_domain = Column(String(255), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    theme = relationship("PortfolioTheme", back_populates="portfolios")
    customization = relationship("PortfolioCustomization", back_populates="portfolio", uselist=False)
    analytics = relationship("PortfolioAnalytics", back_populates="portfolio")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio")

    __table_args__ = (
        Index("idx_portfolio_username", "username"),
        Index("idx_portfolio_public", "is_public"),
    )


class PortfolioTheme(Base):
    """Predefined theme configurations."""
    __tablename__ = "portfolio_themes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    config_json = Column(JSON, nullable=False)  # Theme configuration (colors, typography, etc.)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    portfolios = relationship("Portfolio", back_populates="theme")


class PortfolioCustomization(Base):
    """User customizations for their portfolio."""
    __tablename__ = "portfolio_customizations"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), unique=True, nullable=False)
    section_order = Column(JSON, nullable=True)  # Array of section names in order
    hidden_sections = Column(JSON, nullable=True)  # Array of hidden section names
    custom_css = Column(Text, nullable=True)  # Custom CSS overrides
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="customization")


class PortfolioAnalytics(Base):
    """View tracking for portfolios."""
    __tablename__ = "portfolio_analytics"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    viewer_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    referrer = Column(String(500), nullable=True)  # HTTP referrer
    user_agent = Column(String(500), nullable=True)  # User agent string

    # Relationships
    portfolio = relationship("Portfolio", back_populates="analytics")

    __table_args__ = (
        Index("idx_analytics_portfolio_date", "portfolio_id", "viewed_at"),
        Index("idx_analytics_date", "viewed_at"),
    )


class PortfolioSnapshot(Base):
    """Cached GitHub data snapshots."""
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    data_json = Column(JSON, nullable=False)  # Cached GitHub profile data
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # When this snapshot expires

    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")

    __table_args__ = (
        Index("idx_snapshot_portfolio_expires", "portfolio_id", "expires_at"),
    )


