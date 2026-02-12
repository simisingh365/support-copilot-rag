"""
Database session management for the RAG Customer Support System.

Provides:
- SQLAlchemy engine configuration
- Session factory for database sessions
- Dependency injection for FastAPI
- Database initialization function
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base

# Load environment variables
load_dotenv()


def get_database_url() -> str:
    """
    Get the database URL from environment variables.
    
    Returns:
        str: The database connection URL.
    """
    return os.getenv("DATABASE_URL", "sqlite:///./rag_system.db")


def get_engine():
    """
    Create and configure the SQLAlchemy engine.
    
    Handles SQLite-specific connection arguments for thread safety.
    
    Returns:
        Engine: Configured SQLAlchemy engine.
    """
    database_url = get_database_url()
    
    # SQLite-specific configuration for thread safety
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    
    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=False,  # Set to True for SQL query logging
    )
    
    return engine


# Create engine
engine = get_engine()

# Create SessionLocal factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI database sessions.
    
    Provides a database session for each request and ensures proper cleanup.
    
    Yields:
        Session: SQLAlchemy database session.
    
    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function creates all tables defined in the models if they don't exist.
    It uses SQLAlchemy's create_all which is idempotent.
    
    Raises:
        Exception: If database initialization fails.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data. Use only for testing/development.
    
    Raises:
        Exception: If database drop fails.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        print("All database tables dropped.")
    except Exception as e:
        print(f"Error dropping database tables: {e}")
        raise


def reset_db() -> None:
    """
    Reset the database by dropping and recreating all tables.
    
    WARNING: This will delete all data. Use only for testing/development.
    
    Raises:
        Exception: If database reset fails.
    """
    try:
        drop_db()
        init_db()
        print("Database reset successfully.")
    except Exception as e:
        print(f"Error resetting database: {e}")
        raise
