from contextlib import asynccontextmanager
from typing import Any

import arrow
from fastapi import FastAPI

from .core import settings
from .core.database import db_manager
from .core.exceptions import setup_exception_handlers
from .core.logging import logger
from .core.middlewares import (
    setup_rate_limiting,
    setup_logging_middleware,
    setup_version_middleware,
)
from .core.response import AppResponse
from .core.routing import Extractor, RouterMetadata, AppRouter, FileRouter


class AppRouteExtractor(Extractor):
    def extract(self, module: Any) -> list[RouterMetadata]:
        routers = []

        if not hasattr(module, "router"):
            logger.warn("Module %s has no 'router' attribute", module.__name__)
            return routers

        router = getattr(module, "router")

        if not isinstance(router, AppRouter):
            logger.warn(
                "Attribute 'router' in module %s is not an instance of AppRouter",
                module.__name__,
            )
            return routers

        http_router = router.http_router

        routers.append(RouterMetadata(router=http_router))

        return routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up the application")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"Debug mode: {'enabled' if settings.debug else 'disabled'}")

    db_manager.initialize()

    start_time = arrow.utcnow()
    app.state.start_time = start_time

    yield

    logger.info("Shutting down the application")
    await db_manager.dispose()

    # Shutdown actions


def create_app():
    should_add_docs = settings.is_development and settings.enable_api_docs

    app = FastAPI(
        title=settings.app.name,
        description=settings.app.description,
        version=settings.app.version,
        debug=settings.debug,
        default_response_class=AppResponse,
        docs_url=settings.docs_url if should_add_docs else None,
        redoc_url=settings.redoc_url if should_add_docs else None,
        lifespan=lifespan,
    )

    @app.get("/")
    async def root():
        return {"message": "Authentication Service is running"}

    extractor = AppRouteExtractor()
    file_router = FileRouter(base_path="./api", extractor=extractor)

    app.include_router(file_router)

    # Middlewares
    setup_rate_limiting(app)
    setup_logging_middleware(app)
    setup_exception_handlers(app)
    setup_version_middleware(app, vendor_prefix="authentication")

    return app
