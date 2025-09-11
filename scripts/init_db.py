#!/usr/bin/env python3
"""
Database initialization script.
Creates the necessary tables for the FFStudios Chat Bot.
"""

import sys
import logging
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.database.db import init_database, get_engine
from src.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables."""
    try:
        # Initialize database connection
        init_database()
        engine = get_engine()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_tables()