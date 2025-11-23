from typing import TypeVar, Type, Optional, List, cast, Any, Callable
from uuid import UUID

from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .filters import Filter
from .manager import db_manager
from ..base import BaseDBModel
from ..base.app import AppObject
from ..exceptions import DatabaseError
from ..logging import get_logger
from ..utils import get_current_utc_datetime

T = TypeVar("T", bound=BaseDBModel)

logger = get_logger(__name__)


class Repository[T](AppObject):
    """
    Base class for repositories in the application.

    This class serves as a blueprint for all repository classes,
    ensuring they inherit common functionality and structure.
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        self._session = session
        self._model = model

    @property
    def session(self) -> AsyncSession:
        """
        Returns the current database session.
        """
        return self._session

    @property
    def model(self) -> Type[T]:
        """
        Returns the model class associated with this repository.
        """
        return self._model

    def _apply_filter(self, query: Any, field_name: str, value: Any) -> Any:
        """
        Applies a filter condition to a query.

        :param query: The SQLAlchemy query object.
        :param field_name: The name of the field to filter on.
        :param value: The filter value (can be a Filter instance or a plain value for equality).
        :return: The query with the filter applied.
        """
        if not hasattr(self.model, field_name):
            raise ValueError(f"Invalid filter attribute: {field_name}")

        field = getattr(self.model, field_name)

        return query.where(
            value.apply(field) if isinstance(value, Filter) else field == value
        )

    def _apply_filters(self, query: Any, **filters) -> Any:
        """
        Applies multiple filters to a query.

        :param query: The SQLAlchemy query object.
        :param filters: Filter criteria as keyword arguments.
                     Values can be Filter instances (from filters module) or plain values for equality.
        :return: The query with all filters applied.
        """
        for field_name, value in filters.items():
            query = self._apply_filter(query, field_name, value)
        return query

    async def get(self, id: UUID) -> Optional[T]:
        """
        Retrieves an entity by its ID.

        :param id: The UUID of the entity to retrieve.
        :return: The entity instance if found, else None.
        """

        try:
            query = select(self.model).where(self.model.id == id)
            result = await self.session.exec(query)
            return result.first()
        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving {self.model.__name__} with id {id}: {str(e)}"
            )
            raise DatabaseError(
                f"Error retrieving {self.model.__name__} with id {id}"
            ) from e

    async def get_or_raise(self, id: UUID) -> T:
        """
        Retrieves an entity by its ID or raises an error if not found.

        :param id: The UUID of the entity to retrieve.
        :return: The entity instance.
        :raises DatabaseError: If the entity is not found.
        """

        entity = await self.get(id)

        if entity is None:
            raise DatabaseError(f"{self.model.__name__} with id {id} not found")

        return entity

    async def get_first(self, **filters) -> Optional[T]:
        """
        Retrieves the first entity matching the provided filters.

        :param filters: Additional filtering criteria as keyword arguments.
             Use filter utility functions from authentication.core.base.filters:
             - gt(value): greater than
             - gte(value): greater than or equal
             - lt(value): less than
             - lte(value): less than or equal
             - ne(value): not equal
             - like(pattern): SQL LIKE (case-sensitive)
             - ilike(pattern): case-insensitive LIKE
             - in_(values): IN clause
             - not_in(values): NOT IN clause
             - is_null(): IS NULL
             - is_not_null(): IS NOT NULL
             - plain value: equality (default)

             Example:
                 from authentication.core.base.filters import gt, ilike, in_
                 await repo.all(expires_at=gt(datetime.now()), token=ilike("%abc%"))
        :return: A list of entity instances.
        """

        try:
            query = select(self.model)

            query = self._apply_filters(query, **filters)

            result = await self.session.exec(query)
            return cast(Optional[T], result.first())
        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving first {self.model.__name__} entity: {str(e)}"
            )
            raise DatabaseError(
                f"Error retrieving first {self.model.__name__} entity"
            ) from e

    async def all(
        self, skip: Optional[int] = None, limit: Optional[int] = None, **filters
    ) -> List[T]:
        """
        Retrieves all entities, optionally filtered by provided criteria.

        :param skip: Number of records to skip for pagination.
        :param limit: Maximum number of records to return.
        :param filters: Additional filtering criteria as keyword arguments.
                     Use filter utility functions from authentication.core.base.filters:
                     - gt(value): greater than
                     - gte(value): greater than or equal
                     - lt(value): less than
                     - lte(value): less than or equal
                     - ne(value): not equal
                     - like(pattern): SQL LIKE (case-sensitive)
                     - ilike(pattern): case-insensitive LIKE
                     - in_(values): IN clause
                     - not_in(values): NOT IN clause
                     - is_null(): IS NULL
                     - is_not_null(): IS NOT NULL
                     - plain value: equality (default)

                     Example:
                         from authentication.core.base.filters import gt, ilike, in_
                         await repo.all(expires_at=gt(datetime.now()), token=ilike("%abc%"))
        :return: A list of entity instances.
        """

        try:
            query = select(self.model)

            query = self._apply_filters(query, **filters)

            if skip is not None:
                query = query.offset(skip)

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.exec(query)
            return cast(List[T], result.all())
        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving all {self.model.__name__} entities: {str(e)}"
            )
            raise DatabaseError(
                f"Error retrieving all {self.model.__name__} entities"
            ) from e

    async def create(self, entity: T) -> T:
        """
        Creates a new entity in the database.

        :param entity: The entity instance to create.
        :return: The created entity instance.
        """

        try:
            self.session.add(entity)
            await self.session.commit()
            await self.session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            await self.session.rollback()
            raise DatabaseError(f"Error creating {self.model.__name__}") from e

    async def update(self, id: UUID, **updates) -> T:
        """
        Updates an existing entity in the database.

        :param id: The UUID of the entity to update.
        :param updates: The fields to update as keyword arguments.
        :return: The updated entity instance.
        """

        entity = await self.get_or_raise(id)

        for attr, value in updates.items():
            if not hasattr(entity, attr):
                raise ValueError(f"Invalid update attribute: {attr}")

            setattr(entity, attr, value)

        try:
            self.session.add(entity)
            await self.session.commit()
            await self.session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__} with id {id}: {str(e)}")
            await self.session.rollback()
            raise DatabaseError(
                f"Error updating {self.model.__name__} with id {id}"
            ) from e

    async def delete(self, id: UUID) -> None:
        """
        Deletes an entity from the database.

        :param id: The UUID of the entity to delete.
        """

        entity = await self.get_or_raise(id)

        try:
            await self.session.delete(entity)
            await self.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {str(e)}")
            await self.session.rollback()
            raise DatabaseError(
                f"Error deleting {self.model.__name__} with id {id}"
            ) from e

    async def soft_delete(self, id: UUID) -> T:
        """
        Soft deletes an entity from the database by setting its 'is_deleted' flag to True.

        :param id: The UUID of the entity to soft delete.
        :return: The soft deleted entity instance.
        """
        entity: BaseDBModel = await self.get_or_raise(id)

        if entity.is_deleted:
            raise DatabaseError(
                f"{self.model.__name__} with id {id} is already soft deleted"
            )

        return await self.update(id, deleted_at=get_current_utc_datetime())

    async def restore(self, id: UUID) -> T:
        """
        Restores a soft deleted entity by setting its 'is_deleted' flag to False.

        :param id: The UUID of the entity to restore.
        :return: The restored entity instance.
        """
        entity: BaseDBModel = await self.get_or_raise(id)

        if not entity.is_deleted:
            raise DatabaseError(
                f"{self.model.__name__} with id {id} is not soft deleted"
            )

        return await self.update(id, deleted_at=None)

    async def count(self, **filters) -> int:
        """
        Counts the number of entities in the database, optionally filtered by provided criteria.

        :param filters: Additional filtering criteria as keyword arguments.
                     Use filter utility functions from authentication.core.base.filters.
                     See all() method documentation for available filters.
        :return: The count of entity instances.
        """

        try:
            result = await self.all(**filters)
            return len(result)
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__} entities: {str(e)}")
            raise DatabaseError(f"Error counting {self.model.__name__} entities") from e

    async def exists(self, **filters) -> bool:
        """
        Checks if any entity exists in the database matching the provided criteria.

        :param filters: Filtering criteria as keyword arguments.
                     Use filter utility functions from authentication.core.base.filters:
                     - gt(value): greater than
                     - gte(value): greater than or equal
                     - lt(value): less than
                     - lte(value): less than or equal
                     - ne(value): not equal
                     - like(pattern): SQL LIKE (case-sensitive)
                     - ilike(pattern): case-insensitive LIKE
                     - in_(values): IN clause
                     - not_in(values): NOT IN clause
                     - is_null(): IS NULL
                     - is_not_null(): IS NOT NULL
                     - plain value: equality (default)

                     Example:
                         from authentication.core.base.filters import gt, is_not_null
                         await repo.exists(expires_at=gt(datetime.now()), ip_address=is_not_null())
        :return: True if at least one entity matches the criteria, else False.
        """

        try:
            query = select(self.model)
            query = self._apply_filters(query, **filters)
            result = await self.session.exec(query)
            return result.first() is not None
        except SQLAlchemyError as e:
            logger.error(
                f"Error checking existence of {self.model.__name__} entities: {str(e)}"
            )
            raise DatabaseError(
                f"Error checking existence of {self.model.__name__} entities"
            ) from e


def get_repository(model: Type[T]) -> Callable[[AsyncSession], Repository[T]]:
    """
    Dependency injection function to get a repository instance for a given model.

    :param model: The SQLModel class for which to create the repository.
    :return: An instance of Repository for the specified model.
    """

    def init_repository(
        session: AsyncSession = Depends(db_manager.session_dependency),
    ) -> Repository[T]:
        return Repository[T](session=session, model=model)

    return init_repository
