"""
Common schemas and enums shared across the API.
"""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class VaRMethod(str, Enum):
    """VaR calculation methods."""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    GARCH = "garch"


class Distribution(str, Enum):
    """Statistical distributions."""
    NORMAL = "normal"
    T = "t"
    SKEWT = "skewt"


class HealthResponse(BaseModel):
    """API health check response."""
    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: str
    timestamp: datetime
