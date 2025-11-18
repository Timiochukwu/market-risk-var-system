"""
FastAPI Main Application for Market Risk VaR System.
"""
from fastapi import FastAPI

from config.logging_config import logger
from src.api.middleware import setup_middleware
from src.api.routers import (
    health_router,
    data_router,
    var_router,
    garch_router,
    arima_router,
    backtest_router,
    portfolio_router,
)

# Initialize FastAPI app
app = FastAPI(
    title="Market Risk VaR API",
    description="REST API for Value at Risk calculations using ARIMA and GARCH models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(health_router)
app.include_router(data_router)
app.include_router(var_router)
app.include_router(garch_router)
app.include_router(arima_router)
app.include_router(backtest_router)
app.include_router(portfolio_router)

logger.info("Market Risk VaR API initialized successfully")


def start_server():
    """Start the API server (for CLI entry point)."""
    import uvicorn
    from config.settings import settings

    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    start_server()
