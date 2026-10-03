import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base

logger = logging.getLogger("queryguard.database")

def get_engine():
    db_url = settings.DATABASE_URL
    try:
        # Test if PostgreSQL is reachable or if using SQLite
        if db_url.startswith("postgresql"):
            engine = create_engine(db_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            # Try a quick test connection
            with engine.connect() as conn:
                logger.info("Connected successfully to PostgreSQL database.")
                return engine
        else:
            return create_engine(db_url, connect_args={"check_same_thread": False})
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection to {db_url} failed ({e}). Falling back to local SQLite: {settings.SQLITE_FALLBACK}"
        )
        return create_engine(settings.SQLITE_FALLBACK, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
