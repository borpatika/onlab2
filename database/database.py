import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .models import Base


DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://mlsz_user:mlsz_password@postgres:5432/mlsz_db'  # Docker URL
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def drop_db():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped!")

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_session():
    """Get a new database session (manual management)"""
    return SessionLocal()