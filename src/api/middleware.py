"""
Middleware configuration for FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config.settings import settings
from config.logging_config import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        # Remove server header
        response.headers.pop("Server", None)

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""

    def __init__(self, app, max_size: int = 1_000_000):  # 1MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_size:
                from src.api.errors import ErrorMessages, create_error_response
                raise create_error_response(
                    413,
                    ErrorMessages.REQUEST_TOO_LARGE.format(max_size=self.max_size)
                )

        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {response.status_code} - Completed in {process_time:.3f}s"
        )

        # Add custom header with processing time
        response.headers["X-Process-Time"] = str(process_time)

        return response


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all middleware for the application.

    Args:
        app: FastAPI application instance
    """
    # Trusted host middleware (prevent host header attacks)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure with actual domains in production
        )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers middleware (CRITICAL)
    app.add_middleware(SecurityHeadersMiddleware)

    # Request size limit middleware (CRITICAL)
    app.add_middleware(RequestSizeLimitMiddleware, max_size=1_000_000)  # 1MB

    # GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Rate limiting middleware
    from src.api.rate_limiter import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

    # Custom logging middleware
    if settings.DEBUG:
        app.add_middleware(LoggingMiddleware)

    logger.info("Middleware configured successfully with security enhancements")
