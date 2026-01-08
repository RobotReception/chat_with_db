"""
Database Connection Management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory"""
        # Support POSTGRESQL_URL if provided, otherwise build from components
        if settings.POSTGRESQL_URL:
            database_url = settings.POSTGRESQL_URL
        else:
            database_url = (
                f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
        
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.DEBUG,
        )
        
        # Set statement timeout
        @event.listens_for(self.engine, "connect")
        def set_timeout(dbapi_conn, connection_record):
            with dbapi_conn.cursor() as cursor:
                cursor.execute(
                    f"SET statement_timeout = {settings.SQL_TIMEOUT_SECONDS * 1000}"
                )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(
            "Database connection pool initialized",
            extra={
                "database_url": database_url.split("@")[-1] if "@" in database_url else database_url,
                "database_name": database_url.split("/")[-1] if "/" in database_url else "unknown"
            }
        )
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session with automatic cleanup
        Usage:
            with db_manager.get_session() as session:
                result = session.execute(query)
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def get_connection_string(self) -> str:
        """Get raw connection string for LangChain SQLDatabase"""
        if settings.POSTGRESQL_URL:
            return settings.POSTGRESQL_URL
        return (
            f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )


# Global database manager instance
db_manager = DatabaseManager()
