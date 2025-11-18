"""
API Schemas Module for Market Risk VaR System
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class VaRMethod(str, Enum):
    """VaR calculation methods"""
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    GARCH = "garch"


class Distribution(str, Enum):
    """Statistical distributions"""
    NORMAL = "normal"
    T = "t"
    SKEWT = "skewt"


class DataRequest(BaseModel):
    """Request schema for fetching market data"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)", example="2022-01-01")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)", example="2024-01-01")
    period: Optional[str] = Field("2y", description="Period to fetch", example="2y")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class VaRRequest(BaseModel):
    """Request schema for VaR calculation"""
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
    """Response schema for VaR calculation"""
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
    """Request schema for multiple VaR methods comparison"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    confidence_level: float = Field(0.95, ge=0.5, le=0.99, description="Confidence level")
    position_value: float = Field(1000000, gt=0, description="Position value in USD")
    include_garch: bool = Field(True, description="Include GARCH-based VaR")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class MultiVaRResponse(BaseModel):
    """Response schema for multiple VaR methods"""
    ticker: str
    confidence_level: float
    position_value: float
    var_estimates: List[VaRResponse]
    calculation_date: datetime
    summary: Dict


class GARCHRequest(BaseModel):
    """Request schema for GARCH model"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    p: int = Field(1, ge=1, le=5, description="GARCH lag order")
    q: int = Field(1, ge=1, le=5, description="ARCH lag order")
    distribution: Distribution = Field(Distribution.NORMAL, description="Error distribution")
    forecast_horizon: int = Field(10, gt=0, le=100, description="Forecast horizon")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class GARCHResponse(BaseModel):
    """Response schema for GARCH model"""
    ticker: str
    model_order: str
    distribution: str
    aic: float
    bic: float
    forecast: List[Dict[str, float]]
    calculation_date: datetime


class ARIMARequest(BaseModel):
    """Request schema for ARIMA model"""
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
    """Response schema for ARIMA model"""
    ticker: str
    model_order: str
    aic: float
    bic: float
    forecast: List[Dict[str, float]]
    calculation_date: datetime


class BacktestRequest(BaseModel):
    """Request schema for VaR backtesting"""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    confidence_level: float = Field(0.95, ge=0.5, le=0.99, description="Confidence level")
    position_value: float = Field(1000000, gt=0, description="Position value in USD")
    method: VaRMethod = Field(VaRMethod.HISTORICAL, description="VaR method to backtest")
    train_ratio: float = Field(0.7, gt=0, lt=1, description="Training data ratio")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()


class BacktestResponse(BaseModel):
    """Response schema for backtesting results"""
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


class PortfolioVaRRequest(BaseModel):
    """Request schema for portfolio VaR"""
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
    """Response schema for portfolio VaR"""
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


class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: str
    timestamp: datetime


# Import numpy for validation
import numpy as np
