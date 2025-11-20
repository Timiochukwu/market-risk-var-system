"""
Rate limiting for API endpoints.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter.

    For production, use Redis-based rate limiting (e.g., slowapi, fastapi-limiter).
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 60  # Cleanup old entries every 60 seconds
        self.last_cleanup = time.time()

    def _cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory growth."""
        current_time = time.time()

        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff_time = current_time - 60  # Keep last 60 seconds

            for ip in list(self.requests.keys()):
                self.requests[ip] = [
                    ts for ts in self.requests[ip] if ts > cutoff_time
                ]

                # Remove IP if no recent requests
                if not self.requests[ip]:
                    del self.requests[ip]

            self.last_cleanup = current_time

    def is_allowed(self, identifier: str) -> Tuple[bool, int]:
        """
        Check if request is allowed.

        Args:
            identifier: Client identifier (IP address)

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        self._cleanup_old_requests()

        current_time = time.time()
        cutoff_time = current_time - 60  # Last minute

        # Get requests in last minute
        recent_requests = [
            ts for ts in self.requests[identifier] if ts > cutoff_time
        ]

        self.requests[identifier] = recent_requests

        if len(recent_requests) >= self.requests_per_minute:
            # Calculate retry after
            oldest_request = min(recent_requests)
            retry_after = int(60 - (current_time - oldest_request)) + 1
            return False, retry_after

        # Add current request
        self.requests[identifier].append(current_time)
        return True, 0

    def get_usage(self, identifier: str) -> Dict:
        """
        Get rate limit usage for an identifier.

        Args:
            identifier: Client identifier

        Returns:
            Dictionary with usage stats
        """
        current_time = time.time()
        cutoff_time = current_time - 60

        recent_requests = [
            ts for ts in self.requests.get(identifier, [])
            if ts > cutoff_time
        ]

        return {
            "requests_used": len(recent_requests),
            "requests_limit": self.requests_per_minute,
            "requests_remaining": self.requests_per_minute - len(recent_requests),
            "reset_in_seconds": 60
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        is_allowed, retry_after = self.rate_limiter.is_allowed(client_ip)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": True,
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                    "timestamp": datetime.now().isoformat()
                },
                headers={"Retry-After": str(retry_after)}
            )

        # Add rate limit headers to response
        response = await call_next(request)

        usage = self.rate_limiter.get_usage(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(usage["requests_remaining"])
        response.headers["X-RateLimit-Reset"] = str(usage["reset_in_seconds"])

        return response


# For use with decorators on specific endpoints
from functools import wraps

def rate_limit(requests_per_minute: int = 10):
    """
    Decorator for rate limiting specific endpoints.

    Usage:
        @router.post("/expensive-operation")
        @rate_limit(requests_per_minute=5)
        async def expensive_operation():
            ...
    """
    rate_limiter = RateLimiter(requests_per_minute)

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host if request.client else "unknown"
            is_allowed, retry_after = rate_limiter.is_allowed(client_ip)

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "retry_after": retry_after
                    },
                    headers={"Retry-After": str(retry_after)}
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


from fastapi.responses import JSONResponse
