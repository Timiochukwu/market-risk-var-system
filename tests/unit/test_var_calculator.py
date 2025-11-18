"""
Unit tests for VaR Calculator.
"""
import pytest
import pandas as pd
import numpy as np

from src.models.var_calculator import VaRCalculator


class TestVaRCalculator:
    """Test suite for VaR Calculator."""

    def test_initialization(self):
        """Test VaR calculator initialization."""
        var_calc = VaRCalculator(confidence_level=0.95)
        assert var_calc.confidence_level == 0.95
        assert var_calc.alpha == 0.05

    def test_historical_var(self, sample_returns, sample_var_params):
        """Test historical VaR calculation."""
        var_calc = VaRCalculator(confidence_level=sample_var_params['confidence_level'])
        result = var_calc.historical_var(
            sample_returns,
            position_value=sample_var_params['position_value']
        )

        assert 'VaR' in result
        assert 'ES' in result
        assert 'Method' in result
        assert result['Method'] == 'Historical VaR'
        assert result['VaR'] > 0
        assert result['ES'] >= result['VaR']

    def test_parametric_var_normal(self, sample_returns, sample_var_params):
        """Test parametric VaR with normal distribution."""
        var_calc = VaRCalculator(confidence_level=sample_var_params['confidence_level'])
        result = var_calc.parametric_var(
            sample_returns,
            position_value=sample_var_params['position_value'],
            distribution='normal'
        )

        assert 'VaR' in result
        assert 'ES' in result
        assert result['Method'] == 'Parametric VaR (Normal)'
        assert result['VaR'] > 0

    def test_monte_carlo_var(self, sample_returns, sample_var_params):
        """Test Monte Carlo VaR calculation."""
        var_calc = VaRCalculator(confidence_level=sample_var_params['confidence_level'])
        result = var_calc.monte_carlo_var(
            sample_returns,
            position_value=sample_var_params['position_value'],
            simulations=1000
        )

        assert 'VaR' in result
        assert 'Method' in result
        assert 'Monte Carlo' in result['Method']
        assert result['VaR'] > 0

    def test_confidence_level_validation(self):
        """Test confidence level validation."""
        with pytest.raises(ValueError):
            VaRCalculator(confidence_level=1.5)

        with pytest.raises(ValueError):
            VaRCalculator(confidence_level=-0.1)

    def test_compare_all_methods(self, sample_returns, sample_var_params):
        """Test comparison of all VaR methods."""
        var_calc = VaRCalculator(confidence_level=sample_var_params['confidence_level'])
        results = var_calc.calculate_all_methods(
            sample_returns,
            position_value=sample_var_params['position_value']
        )

        assert isinstance(results, pd.DataFrame)
        assert len(results) >= 3  # At least 3 methods
        assert 'Method' in results.columns
        assert 'VaR' in results.columns
