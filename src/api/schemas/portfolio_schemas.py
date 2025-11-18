"""
Portfolio VaR schemas.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime
import numpy as np

from .common import VaRMethod


class PortfolioVaRRequest(BaseModel):
    """Request schema for portfolio VaR."""
    tickers: List[str] = Field(..., description="List of ticker symbols", example=["AAPL", "MSFT", "GOOGL"])
    weights: List[float] = Field(..., description="Portfolio weights", example=[0.4, 0.3, 0.3])
    confidence_level: float = Field(0.95, ge=0.5, le=0.99, description="Confidence level")
    position_value: float = Field(1000000, gt=0, description="Total portfolio value in USD")
    method: VaRMethod = Field(VaRMethod.HISTORICAL, description="VaR calculation method")

    @validator('tickers')
    def tickers_must_be_uppercase(cls, v):
        return [ticker.upper() for ticker in v]

    @validator('weights')
    def weights_must_sum_to_one(cls, v):
        if not np.isclose(sum(v), 1.0, atol=0.01):
            raise ValueError("Weights must sum to 1.0")
        return v

    @validator('weights')
    def check_lengths(cls, v, values):
        if 'tickers' in values and len(v) != len(values['tickers']):
            raise ValueError("Number of weights must match number of tickers")
        return v


class PortfolioVaRResponse(BaseModel):
    """Response schema for portfolio VaR."""
    tickers: List[str]
    weights: List[float]
    confidence_level: float
    position_value: float
    portfolio_var: float
    portfolio_es: float
    diversification_benefit: float
    individual_vars: List[Dict]
    correlation_matrix: Optional[List[List[float]]] = None
    calculation_date: datetime
