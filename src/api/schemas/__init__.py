"""
API Schemas - Pydantic models for request/response validation.
"""
from .common import VaRMethod, Distribution, HealthResponse, ErrorResponse
from .data import DataRequest
from .var_schemas import VaRRequest, VaRResponse, MultiVaRRequest, MultiVaRResponse
from .garch_schemas import GARCHRequest, GARCHResponse
from .arima_schemas import ARIMARequest, ARIMAResponse
from .backtest_schemas import BacktestRequest, BacktestResponse
from .portfolio_schemas import PortfolioVaRRequest, PortfolioVaRResponse

__all__ = [
    # Common
    "VaRMethod",
    "Distribution",
    "HealthResponse",
    "ErrorResponse",
    # Data
    "DataRequest",
    # VaR
    "VaRRequest",
    "VaRResponse",
    "MultiVaRRequest",
    "MultiVaRResponse",
    # GARCH
    "GARCHRequest",
    "GARCHResponse",
    # ARIMA
    "ARIMARequest",
    "ARIMAResponse",
    # Backtest
    "BacktestRequest",
    "BacktestResponse",
    # Portfolio
    "PortfolioVaRRequest",
    "PortfolioVaRResponse",
]
