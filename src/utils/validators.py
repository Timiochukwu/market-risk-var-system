"""
Input validation utilities for Market Risk VaR System.
"""
import pandas as pd
import numpy as np
from typing import Union


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_returns(returns: pd.Series, min_observations: int = 30) -> pd.Series:
    """
    Validate returns series.

    Args:
        returns: Returns series to validate
        min_observations: Minimum required observations

    Returns:
        Cleaned returns series

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(returns, pd.Series):
        raise ValidationError(f"Returns must be a pandas Series, got {type(returns)}")

    # Remove NaN
    clean_returns = returns.dropna()

    if len(clean_returns) < min_observations:
        raise ValidationError(
            f"Insufficient data: {len(clean_returns)} observations, "
            f"minimum {min_observations} required"
        )

    # Check for infinite values
    if np.isinf(clean_returns).any():
        raise ValidationError("Returns contain infinite values")

    # Check variance
    if clean_returns.std() == 0:
        raise ValidationError("Returns have zero variance (constant values)")

    return clean_returns


def validate_position_value(position_value: float) -> float:
    """
    Validate position value.

    Args:
        position_value: Position value to validate

    Returns:
        Validated position value

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(position_value, (int, float)):
        raise ValidationError(
            f"position_value must be numeric, got {type(position_value)}"
        )

    if position_value <= 0:
        raise ValidationError(
            f"position_value must be positive, got {position_value}"
        )

    if position_value > 1e12:  # 1 trillion
        raise ValidationError(
            f"position_value seems unreasonably large: ${position_value:,.0f}"
        )

    return float(position_value)


def validate_confidence_level(confidence_level: float) -> float:
    """
    Validate confidence level.

    Args:
        confidence_level: Confidence level to validate

    Returns:
        Validated confidence level

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(confidence_level, (int, float)):
        raise ValidationError(
            f"confidence_level must be numeric, got {type(confidence_level)}"
        )

    if not 0 < confidence_level < 1:
        raise ValidationError(
            f"confidence_level must be between 0 and 1, got {confidence_level}"
        )

    return float(confidence_level)


def validate_simulations(simulations: int, min_sims: int = 1000) -> int:
    """
    Validate number of Monte Carlo simulations.

    Args:
        simulations: Number of simulations
        min_sims: Minimum recommended simulations

    Returns:
        Validated number of simulations

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(simulations, int):
        raise ValidationError(
            f"simulations must be an integer, got {type(simulations)}"
        )

    if simulations < 100:
        raise ValidationError(
            f"simulations must be at least 100, got {simulations}"
        )

    if simulations < min_sims:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Low number of simulations ({simulations}). "
            f"Recommended minimum: {min_sims}"
        )

    return simulations


def validate_ticker(ticker: str) -> str:
    """
    Validate ticker symbol.

    Args:
        ticker: Ticker symbol to validate

    Returns:
        Validated ticker (uppercase)

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(ticker, str):
        raise ValidationError(f"ticker must be a string, got {type(ticker)}")

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValidationError("ticker cannot be empty")

    if len(ticker) > 10:
        raise ValidationError(
            f"ticker seems too long ({len(ticker)} chars): {ticker}"
        )

    # Check for valid characters (alphanumeric + some symbols)
    if not all(c.isalnum() or c in ['.', '-', '^'] for c in ticker):
        raise ValidationError(
            f"ticker contains invalid characters: {ticker}"
        )

    return ticker
