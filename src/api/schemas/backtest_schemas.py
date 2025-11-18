"""
Backtesting schemas.
"""
from pydantic import BaseModel, Field, validator
from typing import Dict
from datetime import datetime

from .common import VaRMethod


class BacktestRequest(BaseModel):
    """Request schema for VaR backtesting."""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    confidence_level: float = Field(0.95, ge=0.5, le=0.99, description="Confidence level")
    position_value: float = Field(1000000, gt=0, description="Position value in USD")
    method: VaRMethod = Field(VaRMethod.HISTORICAL, description="VaR method to backtest")
    train_ratio: float = Field(0.7, gt=0, lt=1, description="Training data ratio")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class BacktestResponse(BaseModel):
    """Response schema for backtesting results."""
    ticker: str
    method: str
    confidence_level: float
    num_observations: int
    num_exceptions: int
    exception_rate: float
    expected_rate: float
    kupiec_test: Dict
    christoffersen_test: Dict
    traffic_light_zone: str
    mean_excess_loss: float
    max_excess_loss: float
    calculation_date: datetime
