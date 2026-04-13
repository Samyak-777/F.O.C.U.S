"""
Database engine and session factory.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from src.db.models import Base

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables from ORM models."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency: yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
