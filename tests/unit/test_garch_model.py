"""
Unit tests for GARCH Model.
"""
import pytest
import pandas as pd

from src.models.garch_model import GARCHForecaster


class TestGARCHForecaster:
    """Test suite for GARCH Forecaster."""

    def test_initialization(self):
        """Test GARCH model initialization."""
        garch = GARCHForecaster(p=1, q=1, dist='normal')
        assert garch.p == 1
        assert garch.q == 1
        assert garch.dist == 'normal'

    def test_fit(self, sample_returns):
        """Test GARCH model fitting."""
        garch = GARCHForecaster(p=1, q=1)
        garch.fit(sample_returns)

        assert garch.fitted is True
        assert garch.results is not None
        assert 'aic' in garch.results
        assert 'bic' in garch.results

    def test_forecast(self, sample_returns):
        """Test GARCH volatility forecasting."""
        garch = GARCHForecaster(p=1, q=1)
        garch.fit(sample_returns)
        forecast = garch.forecast(horizon=10)

        assert isinstance(forecast, pd.DataFrame)
        assert len(forecast) == 10
        assert 'Variance' in forecast.columns
        assert 'Volatility' in forecast.columns
        assert (forecast['Volatility'] > 0).all()

    def test_forecast_without_fit(self, sample_returns):
        """Test that forecasting without fitting raises error."""
        garch = GARCHForecaster(p=1, q=1)

        with pytest.raises((ValueError, AttributeError)):
            garch.forecast(horizon=10)
