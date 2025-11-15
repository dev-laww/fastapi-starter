import re
from typing import Union, cast

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    Scope,
    WebSocketScope,
    ASGISendEvent,
)
from fastapi import FastAPI
from semver import Version

from .. import settings
from ..constants import Constants
from ..logging import get_logger
from ..routing import VersionedRoute
from ..routing.utils import parse_version, VersionRegistry

logger = get_logger(__name__)


class VersionMiddleware:
    """
    Use this middleware to parse the Accept Header if present and get an API version
    from the vendor tree. See https://www.rfc-editor.org/rfc/rfc6838#section-3.2

    If incoming http or websocket request contains an Accept header with the following
    value: `"accept/vnd.vendor_prefix.v42+json"`, the scope of the ASGI application
    will then contain an `api_version` of 42.

    If the http or websocket request does not contain an Accept header, or if the accept
    header value does not use a proper format, the scope of the ASGI application will
    then contain an `api_version` that defaults to the provided `latest_version`

    This also allows for version to be specified using the specified header key.
    """

    def __init__(self, app: ASGI3Application, vendor_prefix: str):
        self.app = app
        self.vendor_prefix = vendor_prefix
        self.version_regex = re.compile(Constants.SEMVER_REGEX, re.VERBOSE)
        # Accept header regex with semver pattern embedded
        # Use IGNORECASE flag for case-insensitive matching and search() instead of match()
        # Note: Using IGNORECASE only (no VERBOSE) for more reliable matching
        self.accept_header_regex = re.compile(
            Constants.ACCEPT_HEADER_VERSION_REGEX.format(
                vendor_prefix=re.escape(vendor_prefix)
            ),
            re.IGNORECASE,
        )

    async def __call__(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        scope = cast(Union[HTTPScope, WebSocketScope], scope)
        headers = dict(scope.get("headers", []))

        registry = VersionRegistry.get_instance()
        scope[Constants.REQUESTED_VERSION_SCOPE_KEY] = registry.default_version

        if b"accept" in headers:
            accept_header = headers[b"accept"].decode("latin1")
            # Use search() instead of match() to find the pattern anywhere in the header
            # This handles cases where Accept header has multiple values (comma-separated)
            match = self.accept_header_regex.search(accept_header)

            if match:
                version_str = match.group("version")
                scope[Constants.REQUESTED_VERSION_SCOPE_KEY] = parse_version(
                    version_str
                )

        async def send_wrapper(evt: ASGISendEvent):
            if evt["type"] != "http.response.start":
                await send(evt)
                return

            event_headers = evt.setdefault("headers", [])
            version = scope.get(Constants.REQUESTED_VERSION_SCOPE_KEY)
            event_headers.append(
                (b"x-api-latest-version", str(registry.latest_version).encode("latin1"))
            )
            event_headers.append(
                (
                    b"x-api-available-versions",
                    ",".join(str(v) for v in sorted(registry.all_versions)).encode(
                        "latin1"
                    ),
                )
            )

            if not version:
                await send(evt)
                return

            version_header_value = str(version).encode("latin1")
            event_headers.append((b"x-api-version", version_header_value))

            await send(evt)

        return await self.app(scope, receive, send_wrapper)


def setup_version_middleware(app: FastAPI, vendor_prefix: str) -> None:
    """Sets up the version middleware for the ASGI application."""
    app.add_middleware(VersionMiddleware, vendor_prefix=vendor_prefix)  # type: ignore

    registry = VersionRegistry()
    registry.add_version(Version(1))

    # Register all versions from the app's routes
    for route in app.routes:
        if not isinstance(route, VersionedRoute):
            continue

        if registry.has_version(route.version):
            continue

        registry.add_version(route.version)

    registry.default_version = (
        registry.latest_version
        if settings.default_api_version == "latest"
        else parse_version(settings.default_api_version)
    )

    logger.info("API Versioning Middleware configured")
    logger.info(f"Default API version: {registry.default_version}")
    logger.info(f"Latest API version: {registry.latest_version}")
    logger.info(
        f"Available API versions: {", ".join(str(v) for v in registry.all_versions)}"
    )
