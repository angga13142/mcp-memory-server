"""Authentication middleware for HTTP transport."""

import os
from typing import Any, Callable

from src.utils.logger import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Authentication failed."""

    pass


def get_api_key() -> str | None:
    """Get API key from environment variable."""
    return os.getenv("MCP_API_KEY")


def verify_bearer_token(authorization: str | None) -> bool:
    """Verify bearer token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        True if authenticated, False otherwise
    """
    if not authorization:
        return False

    api_key = get_api_key()
    if not api_key:
        # If no API key configured, allow all requests
        return True

    if not authorization.startswith("Bearer "):
        return False

    token = authorization[7:]  # Remove "Bearer " prefix
    return token == api_key


async def http_auth_middleware(
    request: Any,
    call_next: Callable,
) -> Any:
    """Middleware to authenticate HTTP requests.

    Args:
        request: HTTP request
        call_next: Next middleware/handler

    Returns:
        Response or 401 error
    """
    # Check if API key is configured
    api_key = get_api_key()

    if api_key:
        # Authentication required
        auth_header = request.headers.get("authorization")

        if not verify_bearer_token(auth_header):
            logger.warning(f"Unauthorized access attempt from {request.client.host}")
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "Valid bearer token required",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Proceed to next handler
    return await call_next(request)
