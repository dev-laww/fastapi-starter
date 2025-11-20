from http import HTTPStatus
from typing import Any, Dict, Type, Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logging import logger
from .response import AppResponse, Response


class AppException(Exception):
    """Base exception for the application."""

    code: str = "APP_EXCEPTION"
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str = None, details: Any = None):
        self.message = message or "An application error occurred"
        self.details = details
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Exception raised for authentication errors."""

    code = "AUTHENTICATION_ERROR"
    status_code = HTTPStatus.UNAUTHORIZED

    def __init__(self, message: str = "Authentication failed", details: Any = None):
        super().__init__(message, details)


class AuthorizationError(AppException):
    """Exception raised for authorization errors."""

    code = "AUTHORIZATION_ERROR"
    status_code = HTTPStatus.FORBIDDEN

    def __init__(self, message: str = "Access denied", details: Any = None):
        super().__init__(message, details)


class ValidationError(AppException):
    """Exception raised for validation errors."""

    code = "VALIDATION_ERROR"
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str = "Validation failed", details: Any = None):
        super().__init__(message, details)


class NotFoundError(AppException):
    """Exception raised when a resource is not found."""

    code = "NOT_FOUND_ERROR"
    status_code = HTTPStatus.NOT_FOUND

    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(message, details)


class DatabaseError(AppException):
    """Exception raised for database-related errors."""

    code = "DATABASE_ERROR"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str = "Database error occurred", details: Any = None):
        super().__init__(message, details)


class ExternalServiceError(AppException):
    """Exception raised for errors from external services."""

    code = "EXTERNAL_SERVICE_ERROR"
    status_code = HTTPStatus.BAD_GATEWAY

    def __init__(self, message: str = "External service error", details: Any = None):
        super().__init__(message, details)


class ConflictError(AppException):
    """Exception raised for resource conflicts."""

    code = "CONFLICT_ERROR"
    status_code = HTTPStatus.CONFLICT

    def __init__(self, message: str = "Resource conflict", details: Any = None):
        super().__init__(message, details)


class RateLimitError(AppException):
    """Exception raised when rate limit is exceeded."""

    code = "RATE_LIMIT_ERROR"
    status_code = HTTPStatus.TOO_MANY_REQUESTS

    def __init__(self, message: str = "Rate limit exceeded", details: Any = None):
        super().__init__(message, details)


class VersionNotSupportedError(AppException):
    """Exception raised when API version is not supported."""

    code = "VERSION_NOT_SUPPORTED_ERROR"
    status_code = HTTPStatus.NOT_ACCEPTABLE

    def __init__(self, message: str = "API version not supported", details: Any = None):
        super().__init__(message, details)


def setup_exception_handlers(app: FastAPI):
    """Sets up custom exception handlers for the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle all custom application exceptions."""
        if exc.status_code >= 500:
            logger.error(
                f"{exc.code}: {exc.message}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "code": exc.code,
                    "details": exc.details,
                },
                exc_info=exc.status_code >= 500,
            )

        response_map: Dict[Type[Exception], Callable[[], Response]] = {
            AuthenticationError: lambda: Response.failure(
                status=401, message=exc.message, code="AUTH_ERROR"
            ),
            AuthorizationError: lambda: Response.failure(
                status=403, message=exc.message, code="AUTHZ_ERROR"
            ),
            NotFoundError: lambda: Response.failure(
                status=404, message=exc.message, code="NOT_FOUND"
            ),
            ValidationError: lambda: Response.failure(
                status=400, message=exc.message, code="VALIDATION_ERROR"
            ),
        }

        response_builder = response_map.get(
            type(exc),
            lambda: Response.failure(
                status=exc.status_code,
                message=getattr(exc, "message", str(exc)),
                code=exc.code,
            ),
        )

        content = response_builder()
        return AppResponse(content=content.model_dump(), status_code=exc.status_code)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        content = Response.failure(
            status=exc.status_code, message=exc.detail, code="HTTP_ERROR"
        )

        return AppResponse(content=content.model_dump(), status_code=exc.status_code)

    @app.exception_handler(HTTPStatus.NOT_FOUND)
    async def not_found_exception_handler(request: Request, exc):
        """Handle 404 Not Found errors."""

        content = Response.not_found(
            message="The requested resource was not found", code="NOT_FOUND"
        )

        return AppResponse(
            content=content.model_dump(), status_code=HTTPStatus.NOT_FOUND
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle request validation errors."""

        errors = exc.errors()
        logger.warning(
            f"Validation error: {len(errors)} error(s)",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": errors,
            },
        )

        error_details = [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            }
            for err in errors
        ]

        content = Response.bad_request(
            message="Validation failed",
            code="VALIDATION_ERROR",
            data={"errors": error_details},
        )
        return AppResponse(
            content=content.model_dump(), status_code=HTTPStatus.BAD_REQUEST
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""

        logger.exception(
            f"Unhandled exception: {type(exc).__name__}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
            },
        )

        content = Response.internal_error(
            message="An unexpected error occurred",
            exception=exc,
            code="INTERNAL_SERVER_ERROR",
        )

        return AppResponse(
            content=content.model_dump(), status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )


__all__ = [
    "AppException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "DatabaseError",
    "ExternalServiceError",
    "ConflictError",
    "RateLimitError",
    "VersionNotSupportedError",
    "setup_exception_handlers",
]
