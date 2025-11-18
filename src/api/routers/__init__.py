"""
API Routers - Endpoint organization.
"""
from .health import router as health_router
from .data import router as data_router
from .var import router as var_router
from .garch import router as garch_router
from .arima import router as arima_router
from .backtest import router as backtest_router
from .portfolio import router as portfolio_router

__all__ = [
    "health_router",
    "data_router",
    "var_router",
    "garch_router",
    "arima_router",
    "backtest_router",
    "portfolio_router",
]
