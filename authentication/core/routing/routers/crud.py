from enum import Enum
from typing import (
    Optional,
    List,
    Any,
    Dict,
    Type,
    Union,
    Sequence,
    Callable,
    TypeVar,
    Annotated,
    Awaitable,
)
from uuid import UUID

from fastapi import params
from fastapi.datastructures import Default
from fastapi.params import Depends
from fastapi.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from .app import AppRouter
from .version import VersionedRoute
from ...base import BaseDBModel, BaseModel
from ...database import Repository
from ...database.repository import get_repository
from ...exceptions import NotFoundError, ValidationError
from ...response import Response as AppResponse
from ...utils import pluralize
from ....schemas import (
    PaginationParams,
    PaginatedResponse,
    PaginationInfo,
)  # TODO: Move to core.schemas.common

T = TypeVar("T", bound=BaseDBModel)


# TODO: Create a generic CRUD controller that can be used with the router


class AppCRUDRouter[T](AppRouter):
    def __init__(
        self,
        *,
        prefix: str = "",
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        routes: Optional[List[BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        dependency_overrides_provider: Optional[Any] = None,
        route_class: Type[VersionedRoute] = VersionedRoute,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        lifespan: Optional[Lifespan[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        model: Type[T],
        create_schema: Optional[Type[BaseModel]] = None,
        update_schema: Optional[Type[BaseModel]] = None,
        include_update: bool = True,
        include_create: bool = True,
        include_delete: bool = True,
        exists_callback: Optional[
            Callable[[Any, Repository[T]], Awaitable[bool]]
        ] = None,
        **kwargs,
    ):
        super().__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            **kwargs,
        )
        self.model = model
        self.model_name = model.__name__.lower()
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.include_update = include_update
        self.include_create = include_create
        self.include_delete = include_delete
        self.exist_callback = exists_callback

        if include_create and not create_schema:
            raise ValueError("create_schema must be provided if include_create is True")

        if include_update and not update_schema:
            raise ValueError("update_schema must be provided if include_update is True")

        self.add_crud_routes()

    def add_crud_routes(self):
        self.http_router.add_api_route(
            "",
            self.get_all,
            methods=["GET"],
            name=f"get_all_{pluralize(self.model_name)}",
        )

        self.http_router.add_api_route(
            "/{id}",
            self.get_one,
            methods=["GET"],
            name=f"get_{self.model_name}",
        )

        if self.include_create:
            self.http_router.add_api_route(
                "",
                self.create,
                methods=["POST"],
                name=f"create_{self.model_name}",
            )

        if self.include_update:
            self.http_router.add_api_route(
                "/{id}",
                self.update,
                methods=["PATCH"],
                name=f"update_{self.model_name}",
            )

        if self.include_delete:
            self.http_router.add_api_route(
                "/{id}",
                self.soft_delete,
                methods=["DELETE"],
                name=f"soft_delete_{self.model_name}",
            )

            self.http_router.add_api_route(
                "/{id}/restore",
                self.restore,
                methods=["PATCH"],
                name=f"restore_{self.model_name}",
            )

            self.http_router.add_api_route(
                "/{id}/force",
                self.delete,
                methods=["DELETE"],
                name=f"delete_{self.model_name}",
            )

    @property
    def get_all(self):
        model = self.model

        async def route(
            repository: Annotated[Repository[T], Depends(get_repository(model))],
            pagination: PaginationParams = params.Depends(),
        ):
            # TODO: Support filtering, sorting, etc.
            roles = await repository.all(skip=pagination.offset, limit=pagination.limit)
            total = await repository.count()
            page_count = (total + pagination.limit - 1) // pagination.limit
            has_next = pagination.page < page_count
            has_previous = pagination.page > 1

            prefix = self.http_router.prefix
            prefix = (
                prefix
                if prefix != "/" or prefix != f"{pluralize(self.model_name)}"
                else ""
            )
            base_url = f"{prefix}/{pluralize(self.model_name)}"

            pagination = PaginationInfo(
                total_items=total,
                total_pages=page_count,
                current_page=pagination.page,
                items_per_page=pagination.limit,
                has_next=has_next,
                has_previous=has_previous,
                next_page_url=f"{base_url}?page={pagination.page + 1}&limit={pagination.limit}"
                if has_next
                else None,
                previous_page_url=f"{base_url}?page={pagination.page - 1}&limit={pagination.limit}"
                if has_previous
                else None,
            )

            return AppResponse.ok(
                message=f"{pluralize(self.model_name.capitalize())} retrieved successfully",
                data=PaginatedResponse(
                    pagination=pagination,
                    items=roles,
                ),
            )

        return route

    @property
    def get_one(self):
        model = self.model

        async def route(
            id: UUID,
            repository: Annotated[Repository[T], Depends(get_repository(model))],
        ):
            item = await repository.get(id)

            if not item:
                raise NotFoundError(message=f"{self.model_name.capitalize()} not found")

            return AppResponse.ok(
                message=f"{self.model_name.capitalize()} retrieved successfully",
                data=item,
            )

        return route

    @property
    def create(self):
        create_schema = self.create_schema
        model = self.model

        async def route(
            data: create_schema,
            repository: Annotated[Repository[T], Depends(get_repository(model))],
        ):
            new_entity = model.model_validate(data)

            exists = False

            if self.exist_callback:
                exists = await self.exist_callback(new_entity, repository)

            if exists:
                raise ValidationError(
                    message=f"{self.model_name.capitalize()} with given details already exists"
                )

            created = await repository.create(new_entity)

            return AppResponse.created(
                message=f"{self.model_name.capitalize()} created successfully",
                data=created,
            )

        return route

    @property
    def update(self):
        update_schema = self.update_schema
        model = self.model

        async def route(
            id: UUID,
            data: update_schema,
            repository: Annotated[Repository[T], Depends(get_repository(model))],
        ):
            exists = await repository.exists(id=id)

            if self.exist_callback:
                cb_result = await self.exist_callback(data, repository)

                if cb_result:
                    raise ValidationError(
                        message=f"{self.model_name.capitalize()} with given details already exists"
                    )

            if not exists:
                raise NotFoundError(message=f"{self.model_name.capitalize()} not found")

            updated = await repository.update(id, **data.model_dump())

            return AppResponse.ok(
                message=f"{self.model_name.capitalize()} updated successfully",
                data=updated,
            )

        return route

    @property
    def delete(self):
        model = self.model

        async def route(
            id: UUID,
            repository: Annotated[Repository[T], Depends(get_repository(model))],
        ):
            exists = await repository.exists(id=id)

            if not exists:
                raise NotFoundError(message=f"{self.model_name.capitalize()} not found")

            await repository.delete(id)

            return AppResponse.ok(
                message=f"{self.model_name.capitalize()} deleted successfully",
            )

        return route

    @property
    def soft_delete(self):
        model = self.model

        async def route(
            id: UUID,
            repository: Annotated[Repository[T], Depends(get_repository(model))],
        ):
            exists: BaseDBModel = await repository.get(id)

            if exists.is_deleted:
                raise ValidationError(
                    message=f"{self.model_name.capitalize()} is already soft deleted"
                )

            if not exists:
                raise NotFoundError(message=f"{self.model_name.capitalize()} not found")

            deleted = await repository.soft_delete(id)

            return AppResponse.ok(
                message=f"{self.model_name.capitalize()} soft deleted successfully",
                data=deleted,
            )

        return route

    @property
    def restore(self):
        model = self.model

        async def route(
            id: UUID,
            repository: Annotated[Repository[T], Depends(get_repository(model))],
        ):
            exists: BaseDBModel = await repository.get(id)

            if not exists:
                raise NotFoundError(message=f"{self.model_name.capitalize()} not found")

            if not exists.is_deleted:
                raise ValidationError(
                    message=f"{self.model_name.capitalize()} is not deleted"
                )

            restored = await repository.restore(id)

            return AppResponse.ok(
                message=f"{self.model_name.capitalize()} restored successfully",
                data=restored,
            )

        return route
