"""
VaR calculation schemas.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

from .common import VaRMethod, Distribution


class VaRRequest(BaseModel):
    """Request schema for VaR calculation."""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    confidence_level: float = Field(0.95, ge=0.5, le=0.99, description="Confidence level", example=0.95)
    position_value: float = Field(1000000, gt=0, description="Position value in USD", example=1000000)
    method: VaRMethod = Field(VaRMethod.HISTORICAL, description="VaR calculation method")
    window: Optional[int] = Field(252, gt=0, description="Historical window size", example=252)
    distribution: Optional[Distribution] = Field(Distribution.NORMAL, description="Distribution assumption")
    simulations: Optional[int] = Field(10000, gt=0, description="Monte Carlo simulations", example=10000)
    horizon: Optional[int] = Field(1, gt=0, description="Forecast horizon in days", example=1)

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class VaRResponse(BaseModel):
    """Response schema for VaR calculation."""
    ticker: str
    method: str
    confidence_level: float
    position_value: float
    var_amount: float = Field(..., description="VaR in USD")
    var_percentage: float = Field(..., description="VaR as percentage")
    expected_shortfall: Optional[float] = Field(None, description="Expected Shortfall (CVaR)")
    calculation_date: datetime
    additional_info: Optional[Dict] = None


class MultiVaRRequest(BaseModel):
    """Request schema for multiple VaR methods comparison."""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    confidence_level: float = Field(0.95, ge=0.5, le=0.99, description="Confidence level")
    position_value: float = Field(1000000, gt=0, description="Position value in USD")
    include_garch: bool = Field(True, description="Include GARCH-based VaR")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class MultiVaRResponse(BaseModel):
    """Response schema for multiple VaR methods."""
    ticker: str
    confidence_level: float
    position_value: float
    var_estimates: List[VaRResponse]
    calculation_date: datetime
    summary: Dict
