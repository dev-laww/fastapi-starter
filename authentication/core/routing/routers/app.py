"""
Universal AppRouter with class-based dependency injection support.
This module provides the AppRouter class, in combination with decorators like `@route`, to facilitate
class-based routing in FastAPI applications. It allows defining shared dependencies as class attributes,
which are automatically injected into route handler methods.

Example usage patterns:
    from typing import Annotated
    from fastapi import Depends
    from sqlalchemy.orm import Session

    def get_db() -> Session:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    class ItemRouter(AppRouter):
        # When using Annotated with empty Depends(), the type is used as the dependency
        db: Annotated[Session, Depends()]

        def __init__(self):
            super().__init__(prefix="/items", tags=["items"])

        @route(path="/", methods=["GET"])
        async def list_items(self, skip: int = 0, limit: int = 100):
            return self.db.query(Item).offset(skip).limit(limit).all()


    # Pattern 2: Using Annotated with explicit dependency function
    class ItemRouter(AppRouter):
        db: Annotated[Session, Depends(get_db)]

        def __init__(self):
            super().__init__(prefix="/items", tags=["items"])

        @route(path="/{item_id}", methods=["GET"])
        async def get_item(self, item_id: int):
            item = self.db.query(Item).filter(Item.id == item_id).first()
            if not item:
                raise HTTPException(404, "Item not found")
            return item


    # Pattern 3: Traditional pattern (without Annotated)
    class LegacyRouter(AppRouter):
        db: Session = Depends(get_db)

        def __init__(self):
            super().__init__(prefix="/legacy", tags=["legacy"])

        @route(path="/users", methods=["GET"])
        def get_users(self):
            return self.db.query(User).all()


    # Pattern 4: Multiple dependencies
    class UserRouter(AppRouter):
        db: Annotated[Session, Depends(get_db)]
        current_user: Annotated[User, Depends(get_current_active_user)]
        settings: Annotated[Settings, Depends(get_settings)]

        def __init__(self):
            super().__init__(prefix="/users", tags=["users"])

        @route(path="/me", methods=["GET"])
        async def get_current_user_info(self):
            # All dependencies available via self
            user_data = self.db.query(UserData).filter_by(
                user_id=self.current_user.id
            ).first()

            return {
                "user": self.current_user,
                "data": user_data,
                "api_version": self.settings.API_VERSION
            }

        @route(path="/me/items", methods=["GET"])
        async def get_my_items(self, limit: int = 50):
            return self.db.query(Item).filter_by(
                owner_id=self.current_user.id
            ).limit(limit).all()


    # Pattern 5: Dependency classes with Annotated
    class HealthController:
        def __init__(self, db: Session = Depends(get_db)):
            self.db = db

        async def check_health(self):
            # Check database connection
            try:
                self.db.execute("SELECT 1")
                return {"status": "healthy", "database": "connected"}
            except Exception as e:
                return {"status": "unhealthy", "database": str(e)}

    class HealthRouter(AppRouter):
        # Empty Depends() will automatically use HealthController as the dependency
        controller: Annotated[HealthController, Depends()]

        def __init__(self):
            super().__init__(prefix="/health", tags=["health"])

        @route(path="/", methods=["GET"])
        async def get_health(self):
            return await self.controller.check_health()
"""

import dataclasses
import functools
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
    get_type_hints,
)

from fastapi import params
from fastapi.datastructures import Default
from starlette.responses import JSONResponse
from starlette.responses import Response
from starlette.routing import BaseRoute
from starlette.types import ASGIApp, Lifespan

from .version import VersionedRoute, VersionedRouter

try:
    from typing_inspect import is_classvar
except ImportError:
    # Fallback for environments without typing_inspect
    from typing import ClassVar as _ClassVar

    def is_classvar(tp):
        return hasattr(tp, "__origin__") and tp.__origin__ is _ClassVar


from ..dto import RouteMetadata
from ...base import AppObject
from ...constants import Constants

import inspect


class AppRouter(AppObject):
    """
    Enhanced FastAPI router with class-based dependency injection support.

    Usage:
        class MyRouter(AppRouter):
            # Define shared dependencies as class attributes
            db: Session = Depends(get_db)
            current_user: User = Depends(get_current_user)

            def __init__(self):
                super().__init__(prefix="/api", tags=["my-api"])

            @route(path="/items", methods=["GET"])
            def get_items(self):
                # Access dependencies via self
                return self.db.query(Item).filter_by(owner=self.current_user.id).all()
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
        **kwargs,
    ):
        self.http_router = VersionedRouter(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            responses=responses,
            default_response_class=default_response_class,
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
        self._register_routes()

    def _get_class_dependencies(self) -> Dict[str, tuple]:
        """
        Extract class-level dependencies from type hints.

        Returns:
            Dict mapping dependency names to (type_hint, Depends instance) tuples.
        """
        from typing import get_args, get_origin

        cls = self.__class__
        dependencies = {}

        try:
            hints = get_type_hints(cls, include_extras=True)
        except Exception:  # noqa
            # Fallback if `get_type_hints` fails
            hints = {}

        for name, hint in hints.items():
            if is_classvar(hint):
                continue

            # Handle Annotated types
            actual_type = hint
            depends_instance = None

            if get_origin(hint) is not None:
                # For Annotated[Type, Depends()], get_args returns (Type, Depends(), ...)
                args = get_args(hint)
                if args:
                    actual_type = args[0]

                    for arg in args[1:]:
                        if isinstance(arg, params.Depends):
                            depends_instance = arg
                            break

            # Also check class attribute for Depends
            if depends_instance is None and hasattr(cls, name):
                value = getattr(cls, name)
                if isinstance(value, params.Depends):
                    depends_instance = value

            if depends_instance is not None:
                if depends_instance.dependency is None:
                    depends_instance = params.Depends(actual_type)

                dependencies[name] = (actual_type, depends_instance)

        return dependencies

    def _register_routes(self):
        """
        Register all methods decorated with route metadata.

        Wraps each route method to inject class-level dependencies.
        """
        dependencies = self._get_class_dependencies()

        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not hasattr(method, Constants.ROUTE_METADATA_ATTR):
                continue

            meta = getattr(method, Constants.ROUTE_METADATA_ATTR)

            if not isinstance(meta, RouteMetadata):
                continue

            wrapped_endpoint = self._wrap_endpoint(method, dependencies)

            route_kwargs = {
                field.name: getattr(meta, field.name)
                for field in dataclasses.fields(meta)
            }

            self.http_router.add_api_route(
                endpoint=wrapped_endpoint,
                **route_kwargs,
            )

    def _wrap_endpoint(
        self, method: Callable[..., Any], dependencies: Dict[str, tuple]
    ) -> Callable:
        """
        Wrap an endpoint method to handle dependency injection.

        This creates a new function that:
        1. Has a signature without 'self' but with dependency parameters
        2. Injects resolved dependencies as instance attributes
        3. Calls the original method with proper parameters

        Args:
            method: The original endpoint method
            dependencies: Dict of dependency name -> (type, Depends instance) tuples

        Returns:
            A wrapped function suitable for FastAPI routing
        """
        sig = inspect.signature(method)
        params_list = [p for p in sig.parameters.values() if p.name != "self"]

        dependency_params = []
        for dep_key, (dep_type, dep_depends) in dependencies.items():
            param = inspect.Parameter(
                name=dep_key,
                kind=inspect.Parameter.KEYWORD_ONLY,
                annotation=dep_type,
                default=dep_depends,
            )
            dependency_params.append(param)

        new_signature = sig.replace(parameters=params_list + dependency_params)
        is_async = inspect.iscoroutinefunction(method)

        def prepare_method_arguments(kwargs: Dict[str, Any]) -> Dict[str, Any]:
            """Inject dependencies into self and return cleaned-up method arguments."""
            injected: Dict[str, Any] = {}
            method_args: Dict[str, Any] = {}

            for key, val in kwargs.items():
                if key in dependencies:
                    injected[key] = val
                else:
                    method_args[key] = val

            for name, instance in injected.items():
                setattr(self, name, instance)

            return method_args

        if is_async:

            @functools.wraps(method)
            async def endpoint_wrapper(**kwargs):
                method_args = prepare_method_arguments(kwargs)
                return await method(**method_args)
        else:

            @functools.wraps(method)
            def endpoint_wrapper(**kwargs):
                method_args = prepare_method_arguments(kwargs)
                return method(**method_args)

        endpoint_wrapper.__signature__ = new_signature
        endpoint_wrapper.__wrapped__ = method

        return endpoint_wrapper

    def include_router(self, router: "AppRouter", **kwargs):
        """
        Include another AppRouter into this router.

        Args:
            router: The AppRouter instance to include.
            **kwargs: Additional keyword arguments for inclusion.
        """
        self.http_router.include_router(router.http_router, **kwargs)
