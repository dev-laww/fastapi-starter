from contextlib import asynccontextmanager
from functools import wraps
from typing import Optional, Any, AsyncGenerator, TypeVar, Callable, Coroutine

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession, create_async_engine

from .base import AppObject
from .config import settings
from .exceptions import DatabaseError
from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class DatabaseManager(AppObject):
    """
    Manages the database connection and sessions using SQLAlchemy's asynchronous capabilities.
    Provides methods to initialize the database engine, create sessions, and dispose of resources.
    """

    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def initialize(self):
        """
        Initializes the database engine and session factory.
        """
        logger.info("Initializing DatabaseManager")

        if self._engine is not None:
            raise RuntimeError("DatabaseManager is already initialized.")

        try:
            self._engine = create_async_engine(
                settings.database_url,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=settings.database_pool_timeout,
            )

            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        """
        Provides an asynchronous context manager for database sessions.
        """

        if self._session_factory is None:
            raise RuntimeError("DatabaseManager is not initialized.")

        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()

                if isinstance(e, SQLAlchemyError):
                    raise DatabaseError(f"Database operation error: {str(e)}")

                raise
            finally:
                await session.close()

    async def session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Dependency injection method for FastAPI routes to get a database session.
        """

        async with self.get_session() as session:
            logger.debug("Database session created")
            try:
                yield session
            except Exception as e:
                logger.error(f"Error during database session usage: {str(e)}")
                raise
            finally:
                logger.debug("Database session closed")

    def with_session(self, func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        """
        Decorator that injects a session into an async function.
        Example:
            @db_manager.with_session
            async def do_something(db: AsyncSession):
                ...
        """

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async with self.get_session() as session:
                logger.debug("Database session created for decorated function")
                return await func(*args, db=session, **kwargs)

        return wrapper

    async def dispose(self):
        """
        Disposes the database engine and session factory.
        """
        logger.info("Disposing DatabaseManager")

        if self._engine is None:
            raise RuntimeError("DatabaseManager is not initialized.")

        await self._engine.dispose()

        self._engine = None
        self._session_factory = None

    @property
    def engine(self) -> AsyncEngine:
        """
        Returns the database engine.
        """

        if self._engine is None:
            raise RuntimeError("DatabaseManager is not initialized.")

        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Returns the session factory.
        """

        if self._session_factory is None:
            raise RuntimeError("DatabaseManager is not initialized.")

        return self._session_factory


db_manager = DatabaseManager()
