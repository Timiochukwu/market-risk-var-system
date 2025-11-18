"""
Pytest configuration and shared fixtures.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_returns():
    """Generate sample returns data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    returns = pd.Series(
        np.random.normal(0.0005, 0.02, len(dates)),
        index=dates,
        name='Returns'
    )
    return returns


@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    prices = 100 * np.exp(np.random.normal(0.0005, 0.02, len(dates)).cumsum())
    df = pd.DataFrame({
        'Close': prices,
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)
    return df


@pytest.fixture
def sample_var_params():
    """Sample VaR calculation parameters."""
    return {
        'confidence_level': 0.95,
        'position_value': 1000000,
        'window': 252
    }


@pytest.fixture
def api_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from src.api.main import app

    return TestClient(app)
