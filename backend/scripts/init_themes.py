"""Script to initialize default themes in the database."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.db import init_db, get_db
from database.models import PortfolioTheme
from sqlalchemy import select


# Default theme configurations
THEMES = [
    {
        "name": "modern",
        "description": "Clean and modern design with vibrant colors",
        "config": {
            "colors": {
                "primary": "#5BC0BE",
                "secondary": "#6FFFE9",
                "background": "#FFFFFF",
                "surface": "#F7F7F7",
                "text": "#1A1A1A",
                "textSecondary": "#666666",
                "accent": "#FF6B6B",
            },
            "typography": {
                "fontFamily": "Inter, system-ui, sans-serif",
                "headingFont": "Inter, system-ui, sans-serif",
                "fontSize": "16px",
                "headingSize": "2.5rem",
            },
            "spacing": {
                "small": "0.5rem",
                "medium": "1rem",
                "large": "2rem",
            },
            "borderRadius": "8px",
        }
    },
    {
        "name": "minimal",
        "description": "Minimalist design with clean lines",
        "config": {
            "colors": {
                "primary": "#000000",
                "secondary": "#333333",
                "background": "#FFFFFF",
                "surface": "#FAFAFA",
                "text": "#1A1A1A",
                "textSecondary": "#888888",
                "accent": "#000000",
            },
            "typography": {
                "fontFamily": "Georgia, serif",
                "headingFont": "Georgia, serif",
                "fontSize": "18px",
                "headingSize": "3rem",
            },
            "spacing": {
                "small": "0.5rem",
                "medium": "1.5rem",
                "large": "3rem",
            },
            "borderRadius": "0px",
        }
    },
    {
        "name": "dark",
        "description": "Dark theme with neon accents",
        "config": {
            "colors": {
                "primary": "#00D9FF",
                "secondary": "#00FF88",
                "background": "#0A0A0A",
                "surface": "#1A1A1A",
                "text": "#FFFFFF",
                "textSecondary": "#CCCCCC",
                "accent": "#FF00FF",
            },
            "typography": {
                "fontFamily": "JetBrains Mono, monospace",
                "headingFont": "JetBrains Mono, monospace",
                "fontSize": "16px",
                "headingSize": "2.5rem",
            },
            "spacing": {
                "small": "0.5rem",
                "medium": "1rem",
                "large": "2rem",
            },
            "borderRadius": "12px",
        }
    },
    {
        "name": "colorful",
        "description": "Vibrant and colorful design",
        "config": {
            "colors": {
                "primary": "#FF6B6B",
                "secondary": "#4ECDC4",
                "background": "#FFF9E7",
                "surface": "#FFFFFF",
                "text": "#2C3E50",
                "textSecondary": "#7F8C8D",
                "accent": "#FFE66D",
            },
            "typography": {
                "fontFamily": "Poppins, sans-serif",
                "headingFont": "Poppins, sans-serif",
                "fontSize": "16px",
                "headingSize": "3rem",
            },
            "spacing": {
                "small": "0.5rem",
                "medium": "1rem",
                "large": "2rem",
            },
            "borderRadius": "16px",
        }
    },
    {
        "name": "professional",
        "description": "Professional and corporate design",
        "config": {
            "colors": {
                "primary": "#2C3E50",
                "secondary": "#34495E",
                "background": "#FFFFFF",
                "surface": "#ECF0F1",
                "text": "#2C3E50",
                "textSecondary": "#7F8C8D",
                "accent": "#3498DB",
            },
            "typography": {
                "fontFamily": "Roboto, sans-serif",
                "headingFont": "Roboto, sans-serif",
                "fontSize": "16px",
                "headingSize": "2.25rem",
            },
            "spacing": {
                "small": "0.5rem",
                "medium": "1rem",
                "large": "2rem",
            },
            "borderRadius": "4px",
        }
    },
]


async def init_themes():
    """Initialize themes in the database."""
    init_db()
    
    async for db in get_db():
        # Check if themes already exist
        result = await db.execute(select(PortfolioTheme))
        existing_themes = result.scalars().all()
        
        if existing_themes:
            print(f"Found {len(existing_themes)} existing themes. Skipping initialization.")
            return
        
        # Create themes
        for theme_data in THEMES:
            theme = PortfolioTheme(
                name=theme_data["name"],
                description=theme_data["description"],
                config_json=theme_data["config"],
            )
            db.add(theme)
        
        await db.commit()
        print(f"✅ Initialized {len(THEMES)} themes in the database")
        break


if __name__ == "__main__":
    asyncio.run(init_themes())

