from enum import Enum
from typing import Optional, List, Sequence, Type, Union, Dict, Any, Callable, Tuple

from fastapi import params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute, APIRouter
from fastapi.utils import generate_unique_id
from semver import Version
from starlette.responses import JSONResponse
from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Scope, Receive, Send, Lifespan

from ..dto import VersionMetadata
from ..utils import VersionRegistry
from ...constants import Constants
from ...exceptions import VersionNotSupportedError
from ...response import Response


# TODO: Add support for version ranges (e.g., ">=1.0.0,<2.0.0")
# TODO: Add support for method decorators (e.g., @router.get, @router.post) with versioning


class VersionedRoute(APIRoute):
    """
    Custom APIRoute that supports versioning via a 'version' parameter in the route decorator.
    """

    @property
    def version_metadata(self) -> Optional[VersionMetadata]:
        endpoint = self.endpoint
        return getattr(endpoint, Constants.VERSION_METADATA_ATTR, None)

    @property
    def version(self) -> Optional[Version]:
        version_metadata = self.version_metadata

        if version_metadata:
            return version_metadata.version

        registry = VersionRegistry.get_instance()

        return registry.default_version

    def is_requested_version_matches(self, scope: Scope) -> bool:
        requested_version = scope.get(Constants.REQUESTED_VERSION_SCOPE_KEY)
        method = scope.get("method")

        if not requested_version:  # should not happen when used with VersionMiddleware
            return False

        return requested_version == self.version and method in self.methods

    def matches(self, scope: Scope) -> Tuple[Match, Scope]:
        match, updated_scope = super().matches(scope)

        if match is not Match.FULL:
            return match, updated_scope

        if not self.is_requested_version_matches(scope):
            return Match.PARTIAL, updated_scope

        return Match.FULL, updated_scope

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.is_requested_version_matches(scope):
            raise VersionNotSupportedError("Invalid API version for this endpoint")

        await super().handle(scope, receive, send)


class VersionedRouter(APIRouter):
    """
    Custom APIRouter that uses VersionedRoute for its routes.
    """

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
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id
        ),
    ) -> None:
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
            generate_unique_id_function=generate_unique_id_function,
        )
