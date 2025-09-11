"""
Database connection and session management using SQLAlchemy.
"""
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = None
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def init_database() -> None:
    """
    Initialize the database engine and session factory.
    Reads PostgreSQL configuration from environment variables.
    """
    global DATABASE_URL, engine, SessionLocal
    
    if engine is not None:
        return  # Already initialized
    
    # Get database configuration from environment
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    database = os.getenv("PGDATABASE")
    
    if not all([user, password, database]):
        raise ValueError(
            "Missing database configuration. Please set PGUSER, PGPASSWORD, and PGDATABASE in your .env file"
        )
    
    # Construct database URL
    DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    
    # Create engine with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before use
        echo=False  # Set to True for SQL debugging
    )
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def close_database() -> None:
    """Close all database connections."""
    global engine
    if engine:
        engine.dispose()
        engine = None


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager that provides a database session.
    Automatically handles commit/rollback and session cleanup.
    
    Usage:
        with get_db_session() as session:
            # Use session here
            session.add(item)
            session.commit()
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_engine() -> Engine:
    """Get the database engine."""
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return engine


def test_connection() -> bool:
    """
    Test the database connection.
    Returns True if connection is successful, False otherwise.
    """
    try:
        with get_db_session() as session:
            # SQLAlchemy 2.x requires text() for textual SQL
            session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False