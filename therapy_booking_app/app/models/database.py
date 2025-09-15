from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add the parent directory to the path to find config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config.settings import config

def get_database_url():
    """Get database URL from configuration"""
    return config.DATABASE_URL

# Database engine
engine = create_engine(
    config.DATABASE_URL,
    echo=config.DEBUG,  # Log SQL queries in debug mode
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
