"""
Database configuration and session management.
Simplified and integrated with new configuration system.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import get_settings

# Get configuration
settings = get_settings()

def get_database_url():
    """Get database URL from configuration"""
    return settings.database_url

# Database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600   # Recycle connections every hour
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()
metadata = MetaData()

# Database dependency for FastAPI
def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables(db_engine=None):
    """Create all database tables"""
    if db_engine is None:
        db_engine = engine
    Base.metadata.create_all(bind=db_engine)