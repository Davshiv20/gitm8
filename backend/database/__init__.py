"""Database package for GitM8."""

from database.db import get_db, init_db
from database.base import Base

# Portfolio models are optional (not deployed to production yet)
try:
    from database.models import (
        Portfolio,
        PortfolioTheme,
        PortfolioCustomization,
        PortfolioAnalytics,
        PortfolioSnapshot,
    )
    __all__ = [
        "get_db",
        "init_db",
        "Base",
        "Portfolio",
        "PortfolioTheme",
        "PortfolioCustomization",
        "PortfolioAnalytics",
        "PortfolioSnapshot",
    ]
except ImportError:
    # Portfolio models not available
    __all__ = [
        "get_db",
        "init_db",
        "Base",
    ]


