"""
Standardized API error messages and handlers.
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ErrorMessages:
    """Centralized error messages."""

    # Data errors
    TICKER_NOT_FOUND = "No data found for ticker: {ticker}"
    INSUFFICIENT_DATA = "Insufficient data for calculation: {count} observations, minimum {required} required"
    DATA_FETCH_FAILED = "Failed to fetch market data: {reason}"

    # Validation errors
    INVALID_CONFIDENCE = "Confidence level must be between 0.50 and 0.99, got {value}"
    INVALID_POSITION = "Position value must be positive, got {value}"
    INVALID_TICKER = "Invalid ticker symbol: {ticker}"
    INVALID_METHOD = "Invalid VaR method: {method}. Allowed: {allowed}"
    INVALID_SIMULATIONS = "Number of simulations must be at least 100, got {value}"

    # Calculation errors
    CALCULATION_FAILED = "VaR calculation failed: {reason}"
    GARCH_FIT_FAILED = "GARCH model fitting failed: {reason}"
    ARIMA_FIT_FAILED = "ARIMA model fitting failed: {reason}"

    # System errors
    INTERNAL_ERROR = "An internal error occurred. Please try again later."
    RATE_LIMIT_EXCEEDED = "Rate limit exceeded. Please try again in {retry_after} seconds."
    REQUEST_TOO_LARGE = "Request body too large. Maximum size: {max_size} bytes."

    # Authentication errors (for future use)
    UNAUTHORIZED = "Authentication required"
    INVALID_TOKEN = "Invalid or expired token"
    FORBIDDEN = "You don't have permission to access this resource"


def create_error_response(
    status_code: int,
    message: str,
    details: dict = None
) -> HTTPException:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional error details

    Returns:
        HTTPException with standardized format
    """
    error_response = {
        "error": True,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code
    }

    if details:
        error_response["details"] = details

    return HTTPException(status_code=status_code, detail=error_response)


# Exception handlers
async def validation_exception_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": True,
            "message": str(exc),
            "timestamp": datetime.now().isoformat(),
            "status_code": 400,
            "path": str(request.url)
        }
    )


async def type_exception_handler(request: Request, exc: TypeError):
    """Handle type errors."""
    logger.warning(f"Type error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": True,
            "message": f"Invalid input type: {str(exc)}",
            "timestamp": datetime.now().isoformat(),
            "status_code": 400,
            "path": str(request.url)
        }
    )


async def api_exception_handler(request: Request, exc: APIError):
    """Handle custom API errors."""
    logger.error(f"API error: {exc.message}", extra=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now().isoformat(),
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    # Don't expose internal error details in production
    from config.settings import settings

    if settings.DEBUG:
        message = f"Internal error: {str(exc)}"
    else:
        message = ErrorMessages.INTERNAL_ERROR

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status_code": 500,
            "path": str(request.url)
        }
    )
