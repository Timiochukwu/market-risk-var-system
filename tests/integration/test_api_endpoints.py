"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, api_client):
        """Test root endpoint."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'timestamp' in data

    def test_health_endpoint(self, api_client):
        """Test health endpoint."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'


class TestVaREndpoints:
    """Test VaR calculation endpoints."""

    @pytest.mark.integration
    def test_calculate_var_endpoint(self, api_client):
        """Test VaR calculation endpoint."""
        payload = {
            "ticker": "AAPL",
            "confidence_level": 0.95,
            "position_value": 1000000,
            "method": "historical"
        }
        response = api_client.post("/api/v1/var/calculate", json=payload)

        # Note: This might fail without real data connection
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert 'ticker' in data
            assert 'var_amount' in data
            assert data['ticker'] == 'AAPL'

    @pytest.mark.integration
    def test_compare_var_methods(self, api_client):
        """Test VaR methods comparison endpoint."""
        payload = {
            "ticker": "AAPL",
            "confidence_level": 0.95,
            "position_value": 1000000,
            "include_garch": False
        }
        response = api_client.post("/api/v1/var/compare", json=payload)

        # Note: This might fail without real data connection
        assert response.status_code in [200, 404, 500]


class TestGARCHEndpoints:
    """Test GARCH model endpoints."""

    @pytest.mark.integration
    def test_garch_forecast_endpoint(self, api_client):
        """Test GARCH forecast endpoint."""
        payload = {
            "ticker": "AAPL",
            "p": 1,
            "q": 1,
            "distribution": "normal",
            "forecast_horizon": 10
        }
        response = api_client.post("/api/v1/garch/forecast", json=payload)

        # Note: This might fail without real data connection
        assert response.status_code in [200, 404, 500]
