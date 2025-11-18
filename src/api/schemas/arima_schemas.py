"""
ARIMA model schemas.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict
from datetime import datetime


class ARIMARequest(BaseModel):
    """Request schema for ARIMA model."""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    p: int = Field(1, ge=0, le=5, description="AR order")
    d: int = Field(0, ge=0, le=2, description="Differencing order")
    q: int = Field(1, ge=0, le=5, description="MA order")
    forecast_steps: int = Field(10, gt=0, le=100, description="Forecast steps")
    optimize: bool = Field(False, description="Auto-optimize order")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class ARIMAResponse(BaseModel):
    """Response schema for ARIMA model."""
    ticker: str
    model_order: str
    aic: float
    bic: float
    forecast: List[Dict[str, float]]
    calculation_date: datetime
