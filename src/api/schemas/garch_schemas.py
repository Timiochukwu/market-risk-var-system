"""
GARCH model schemas.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict
from datetime import datetime

from .common import Distribution


class GARCHRequest(BaseModel):
    """Request schema for GARCH model."""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    p: int = Field(1, ge=1, le=5, description="GARCH lag order")
    q: int = Field(1, ge=1, le=5, description="ARCH lag order")
    distribution: Distribution = Field(Distribution.NORMAL, description="Error distribution")
    forecast_horizon: int = Field(10, gt=0, le=100, description="Forecast horizon")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class GARCHResponse(BaseModel):
    """Response schema for GARCH model."""
    ticker: str
    model_order: str
    distribution: str
    aic: float
    bic: float
    forecast: List[Dict[str, float]]
    calculation_date: datetime
