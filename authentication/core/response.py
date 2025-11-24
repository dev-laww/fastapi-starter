import traceback
from http import HTTPStatus
from typing import Mapping, Any, Optional, List

from pydantic import ValidationError
from starlette.background import BackgroundTask
from starlette.responses import JSONResponse

from .base import BaseModel


class ErrorDetail(BaseModel):
    """Error detail model for error responses."""

    type: str
    code: str
    message: str
    details: Optional[Any] = None
    stack_trace: Optional[List[str]] = None


class Response(BaseModel):
    """Uniform API response model."""

    status: int
    success: bool
    message: str
    data: Optional[Any] = None
    code: Optional[str] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def ok(
        cls,
        message: str = "Success",
        data: Any = None,
        status: int = HTTPStatus.OK,
        code: str = "SUCCESS",
    ) -> "Response":
        """Create a successful response."""
        return cls(status=status, success=True, message=message, code=code, data=data)

    @classmethod
    def created(
        cls,
        message: str = "Resource created successfully",
        data: Any = None,
        code: str = "CREATED",
    ) -> "Response":
        """Create a 201 Created response."""
        return cls.ok(message=message, data=data, status=HTTPStatus.CREATED, code=code)

    @classmethod
    def no_content(
        cls, message: str = "No content", code: str = "NO_CONTENT"
    ) -> "Response":
        """Create a 204 No Content response."""
        return cls.ok(message=message, status=HTTPStatus.NO_CONTENT, code=code)

    @classmethod
    def failure(
        cls,
        status: int,
        message: str = "Request failed",
        code: str = "FAILURE",
        exception: Optional[Exception] = None,
        details: Optional[Any] = None,
        include_stack_trace: bool = False,
    ) -> "Response":
        """Create a failure response."""
        error_detail = None

        if exception:
            stack_trace: Optional[List[str]] = None
            if include_stack_trace:
                stack_trace = traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )

            error_detail = ErrorDetail(
                type=type(exception).__name__,
                code=getattr(exception, "code", code),
                message=str(exception),
                details=getattr(exception, "details", details),
                stack_trace=stack_trace,
            )
        elif details:
            # Create error detail even without exception if details provided
            error_detail = ErrorDetail(
                type="ValidationError", code=code, message=message, details=details
            )

        return cls(
            status=status, success=False, message=message, code=code, error=error_detail
        )

    @classmethod
    def bad_request(
        cls,
        message: str = "Bad request",
        code: str = "BAD_REQUEST",
        data: Optional[Any] = None,
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 400 Bad Request response."""
        return cls.failure(
            status=HTTPStatus.BAD_REQUEST,
            message=message,
            code=code,
            details=data,
            exception=exception,
        )

    @classmethod
    def unauthorized(
        cls,
        message: str = "Authentication required",
        code: str = "UNAUTHORIZED",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 401 Unauthorized response."""
        return cls.failure(
            status=HTTPStatus.UNAUTHORIZED,
            message=message,
            code=code,
            exception=exception,
        )

    @classmethod
    def forbidden(
        cls,
        message: str = "Access denied",
        code: str = "FORBIDDEN",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 403 Forbidden response."""
        return cls.failure(
            status=HTTPStatus.FORBIDDEN, message=message, code=code, exception=exception
        )

    @classmethod
    def not_found(
        cls,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 404 Not Found response."""
        return cls.failure(
            status=HTTPStatus.NOT_FOUND, message=message, code=code, exception=exception
        )

    @classmethod
    def conflict(
        cls,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 409 Conflict response."""
        return cls.failure(
            status=HTTPStatus.CONFLICT, message=message, code=code, exception=exception
        )

    @classmethod
    def too_many_requests(
        cls,
        message: str = "Too many requests",
        code: str = "RATE_LIMIT_EXCEEDED",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 429 Too Many Requests response."""
        return cls.failure(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            message=message,
            code=code,
            exception=exception,
        )

    @classmethod
    def internal_error(
        cls,
        message: str = "Internal server error",
        code: str = "INTERNAL_SERVER_ERROR",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 500 Internal Server Error response."""
        return cls.failure(
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            message=message,
            code=code,
            exception=exception,
            include_stack_trace=True,
        )

    @classmethod
    def bad_gateway(
        cls,
        message: str = "Bad gateway",
        code: str = "BAD_GATEWAY",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 502 Bad Gateway response."""
        return cls.failure(
            status=HTTPStatus.BAD_GATEWAY,
            message=message,
            code=code,
            exception=exception,
        )

    @classmethod
    def service_unavailable(
        cls,
        message: str = "Service unavailable",
        code: str = "SERVICE_UNAVAILABLE",
        exception: Optional[Exception] = None,
    ) -> "Response":
        """Create a 503 Service Unavailable response."""
        return cls.failure(
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            message=message,
            code=code,
            exception=exception,
        )


class AppResponse(JSONResponse):
    """Custom JSON response for the application."""

    def __init__(
        self,
        content: Any,
        status_code: int = HTTPStatus.OK,
        headers: Optional[Mapping[str, str]] = None,
        media_type: Optional[str] = None,
        background: Optional[BackgroundTask] = None,
    ) -> None:
        """Initialize the response with sanitized content."""
        # If content is already a dict, validate it through Response model
        if isinstance(content, Response):
            sanitized = content
        else:
            # Wrap raw content in a success response
            try:
                sanitized = Response.model_validate(content)
            except ValidationError:
                sanitized = Response.ok(data=content)

        super().__init__(
            content=sanitized.model_dump(exclude_none=True),
            status_code=sanitized.status,
            headers=headers,
            media_type=media_type,
            background=background,
        )


__all__ = [
    "Response",
    "ErrorDetail",
    "AppResponse",
]
