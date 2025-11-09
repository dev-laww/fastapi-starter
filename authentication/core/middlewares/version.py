import re
from typing import Union, cast

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    Scope,
    WebSocketScope,
)
from fastapi import FastAPI

from ..constants import Constants
from ..routing.utils import parse_version


# TODO: Add support for default api version, latest version, and version negotiation strategies e.g., "latest", "stable", etc.

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
            re.IGNORECASE
        )

    async def __call__(self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable):
        if not scope["type"] in ("http", "websocket"):
            return await self.app(scope, receive, send)

        scope = cast(Union[HTTPScope, WebSocketScope], scope)
        headers = dict(scope.get("headers", []))

        if b"accept" in headers:
            accept_header = headers[b"accept"].decode("latin1")
            # Use search() instead of match() to find the pattern anywhere in the header
            # This handles cases where Accept header has multiple values (comma-separated)
            match = self.accept_header_regex.search(accept_header)

            if match:
                version_str = match.group("version")
                scope[Constants.REQUESTED_VERSION_SCOPE_KEY] = parse_version(version_str)

        return await self.app(scope, receive, send)


def setup_version_middleware(app: FastAPI, vendor_prefix: str) -> None:
    """Sets up the version middleware for the ASGI application."""
    app.add_middleware(VersionMiddleware, vendor_prefix=vendor_prefix)
