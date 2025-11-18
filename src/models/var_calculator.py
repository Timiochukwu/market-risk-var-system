"""
VaR Calculator Module for Market Risk VaR System
Implements three VaR calculation methods: Historical, Parametric, Monte Carlo
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VaRCalculator:
    """Calculate Value at Risk using multiple methods"""

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize VaR calculator

        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%, 0.99 for 99%)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    def historical_var(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        window: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate Historical VaR

        Args:
            returns: Historical returns
            position_value: Portfolio value in currency
            window: Rolling window size (None for full history)

        Returns:
            Dictionary with VaR and ES (Expected Shortfall)
        """
        returns_clean = returns.dropna()

        if window is not None:
            returns_clean = returns_clean.tail(window)

        # Calculate VaR as the quantile of losses
        var_percentile = returns_clean.quantile(self.alpha)
        var = -var_percentile * position_value

        # Calculate Expected Shortfall (CVaR)
        es_returns = returns_clean[returns_clean <= var_percentile]
        es = -es_returns.mean() * position_value if len(es_returns) > 0 else var

        logger.info(f"Historical VaR ({self.confidence_level*100}%): ${var:,.2f}")
        logger.info(f"Expected Shortfall: ${es:,.2f}")

        return {
            'VaR': var,
            'ES': es,
            'VaR_Percentage': -var_percentile * 100,
            'ES_Percentage': -es_returns.mean() * 100 if len(es_returns) > 0 else -var_percentile * 100,
            'Method': 'Historical'
        }

    def parametric_var(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        window: Optional[int] = None,
        distribution: str = 'normal'
    ) -> Dict[str, float]:
        """
        Calculate Parametric VaR (Variance-Covariance method)

        Args:
            returns: Historical returns
            position_value: Portfolio value in currency
            window: Rolling window size
            distribution: 'normal' or 't' (Student's t)

        Returns:
            Dictionary with VaR and ES
        """
        returns_clean = returns.dropna()

        if window is not None:
            returns_clean = returns_clean.tail(window)

        # Calculate statistics
        mean = returns_clean.mean()
        std = returns_clean.std()

        if distribution == 'normal':
            # Normal distribution
            z_score = stats.norm.ppf(self.alpha)
            var_percentile = mean + z_score * std

        elif distribution == 't':
            # Student's t distribution
            df = len(returns_clean) - 1
            t_score = stats.t.ppf(self.alpha, df)
            var_percentile = mean + t_score * std

        else:
            raise ValueError(f"Unknown distribution: {distribution}")

        var = -var_percentile * position_value

        # Expected Shortfall for normal distribution
        if distribution == 'normal':
            z_score = stats.norm.ppf(self.alpha)
            es_percentile = mean - std * stats.norm.pdf(z_score) / self.alpha
        else:
            # For t-distribution, use numerical approximation
            es_percentile = var_percentile

        es = -es_percentile * position_value

        logger.info(f"Parametric VaR ({self.confidence_level*100}%, {distribution}): ${var:,.2f}")
        logger.info(f"Expected Shortfall: ${es:,.2f}")

        return {
            'VaR': var,
            'ES': es,
            'VaR_Percentage': -var_percentile * 100,
            'ES_Percentage': -es_percentile * 100,
            'Mean': mean,
            'Std': std,
            'Distribution': distribution,
            'Method': 'Parametric'
        }

    def monte_carlo_var(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        simulations: int = 10000,
        horizon: int = 1,
        method: str = 'bootstrap',
        distribution: str = 'normal'
    ) -> Dict[str, float]:
        """
        Calculate Monte Carlo VaR

        Args:
            returns: Historical returns
            position_value: Portfolio value in currency
            simulations: Number of Monte Carlo simulations
            horizon: Forecast horizon in days
            method: 'bootstrap' or 'parametric'
            distribution: Distribution for parametric method

        Returns:
            Dictionary with VaR and ES
        """
        returns_clean = returns.dropna()

        if method == 'bootstrap':
            # Bootstrap resampling
            simulated_returns = np.random.choice(
                returns_clean,
                size=(simulations, horizon),
                replace=True
            )
            # Calculate cumulative returns
            portfolio_returns = np.sum(simulated_returns, axis=1)

        elif method == 'parametric':
            # Parametric simulation
            mean = returns_clean.mean()
            std = returns_clean.std()

            if distribution == 'normal':
                simulated_returns = np.random.normal(
                    mean * horizon,
                    std * np.sqrt(horizon),
                    simulations
                )
            elif distribution == 't':
                df = len(returns_clean) - 1
                simulated_returns = stats.t.rvs(
                    df,
                    loc=mean * horizon,
                    scale=std * np.sqrt(horizon),
                    size=simulations
                )
            else:
                raise ValueError(f"Unknown distribution: {distribution}")

            portfolio_returns = simulated_returns

        else:
            raise ValueError(f"Unknown method: {method}")

        # Calculate VaR and ES
        var_percentile = np.quantile(portfolio_returns, self.alpha)
        var = -var_percentile * position_value

        # Expected Shortfall
        es_returns = portfolio_returns[portfolio_returns <= var_percentile]
        es = -np.mean(es_returns) * position_value if len(es_returns) > 0 else var

        logger.info(f"Monte Carlo VaR ({self.confidence_level*100}%, {method}): ${var:,.2f}")
        logger.info(f"Expected Shortfall: ${es:,.2f}")
        logger.info(f"Simulations: {simulations}, Horizon: {horizon} day(s)")

        return {
            'VaR': var,
            'ES': es,
            'VaR_Percentage': -var_percentile * 100,
            'ES_Percentage': -np.mean(es_returns) * 100 if len(es_returns) > 0 else -var_percentile * 100,
            'Simulations': simulations,
            'Horizon': horizon,
            'Method': f'Monte Carlo ({method})',
            'Simulated_Returns': portfolio_returns
        }

    def garch_var(
        self,
        garch_forecast: pd.Series,
        position_value: float = 1000000,
        distribution: str = 'normal'
    ) -> Dict[str, float]:
        """
        Calculate VaR using GARCH volatility forecast

        Args:
            garch_forecast: Forecasted volatility from GARCH model
            position_value: Portfolio value in currency
            distribution: Distribution assumption

        Returns:
            Dictionary with VaR
        """
        # Get next period volatility forecast
        next_vol = garch_forecast.iloc[0] if isinstance(garch_forecast, pd.Series) else garch_forecast

        if distribution == 'normal':
            z_score = stats.norm.ppf(self.alpha)
        elif distribution == 't':
            df = 10  # Typical assumption
            z_score = stats.t.ppf(self.alpha, df)
        else:
            raise ValueError(f"Unknown distribution: {distribution}")

        # VaR = z_score * volatility * position_value
        # Note: volatility is in percentage, divide by 100
        var = -z_score * (next_vol / 100) * position_value

        logger.info(f"GARCH VaR ({self.confidence_level*100}%): ${var:,.2f}")

        return {
            'VaR': var,
            'Volatility': next_vol,
            'Distribution': distribution,
            'Method': 'GARCH'
        }

    def calculate_all_methods(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        garch_forecast: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Calculate VaR using all methods

        Args:
            returns: Historical returns
            position_value: Portfolio value
            garch_forecast: Optional GARCH volatility forecast

        Returns:
            DataFrame with VaR from all methods
        """
        logger.info(f"\nCalculating VaR for position value: ${position_value:,.2f}")
        logger.info(f"Confidence level: {self.confidence_level*100}%\n")

        results = []

        # Historical VaR
        hist_var = self.historical_var(returns, position_value)
        results.append(hist_var)

        # Parametric VaR (Normal)
        param_var_normal = self.parametric_var(returns, position_value, distribution='normal')
        results.append(param_var_normal)

        # Parametric VaR (Student's t)
        param_var_t = self.parametric_var(returns, position_value, distribution='t')
        results.append(param_var_t)

        # Monte Carlo VaR (Bootstrap)
        mc_var_bootstrap = self.monte_carlo_var(
            returns, position_value, simulations=10000, method='bootstrap'
        )
        results.append(mc_var_bootstrap)

        # Monte Carlo VaR (Parametric)
        mc_var_param = self.monte_carlo_var(
            returns, position_value, simulations=10000, method='parametric'
        )
        results.append(mc_var_param)

        # GARCH VaR if forecast provided
        if garch_forecast is not None:
            garch_var = self.garch_var(garch_forecast, position_value)
            results.append(garch_var)

        # Create summary DataFrame
        summary_df = pd.DataFrame(results)

        # Select key columns for display
        display_cols = ['Method', 'VaR', 'ES', 'VaR_Percentage']
        display_cols = [col for col in display_cols if col in summary_df.columns]

        return summary_df[display_cols] if display_cols else summary_df

    def rolling_var(
        self,
        returns: pd.Series,
        window: int = 252,
        position_value: float = 1000000,
        method: str = 'historical'
    ) -> pd.Series:
        """
        Calculate rolling VaR

        Args:
            returns: Historical returns
            window: Rolling window size
            position_value: Portfolio value
            method: VaR calculation method

        Returns:
            Series with rolling VaR
        """
        rolling_var = []

        for i in range(window, len(returns)):
            window_returns = returns.iloc[i-window:i]

            if method == 'historical':
                var_result = self.historical_var(window_returns, position_value)
            elif method == 'parametric':
                var_result = self.parametric_var(window_returns, position_value)
            else:
                raise ValueError(f"Unknown method: {method}")

            rolling_var.append(var_result['VaR'])

        rolling_var_series = pd.Series(
            rolling_var,
            index=returns.index[window:]
        )

        return rolling_var_series

    def compare_confidence_levels(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        confidence_levels: list = [0.90, 0.95, 0.99],
        method: str = 'historical'
    ) -> pd.DataFrame:
        """
        Compare VaR at different confidence levels

        Args:
            returns: Historical returns
            position_value: Portfolio value
            confidence_levels: List of confidence levels
            method: VaR calculation method

        Returns:
            DataFrame with VaR at different confidence levels
        """
        results = []

        for cl in confidence_levels:
            var_calc = VaRCalculator(confidence_level=cl)

            if method == 'historical':
                var_result = var_calc.historical_var(returns, position_value)
            elif method == 'parametric':
                var_result = var_calc.parametric_var(returns, position_value)
            elif method == 'monte_carlo':
                var_result = var_calc.monte_carlo_var(returns, position_value)
            else:
                raise ValueError(f"Unknown method: {method}")

            results.append({
                'Confidence_Level': f"{cl*100}%",
                'VaR': var_result['VaR'],
                'ES': var_result.get('ES', np.nan),
                'VaR_Percentage': var_result['VaR_Percentage']
            })

        return pd.DataFrame(results)


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor
    from models.garch_model import GARCHForecaster

    # Collect and prepare data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()

    # Calculate VaR using all methods
    var_calc = VaRCalculator(confidence_level=0.95)

    # Fit GARCH model for GARCH-based VaR
    garch = GARCHForecaster(p=1, q=1)
    garch.fit(returns)
    garch_forecast = garch.forecast(horizon=1)

    # Calculate VaR using all methods
    var_results = var_calc.calculate_all_methods(
        returns,
        position_value=1000000,
        garch_forecast=garch_forecast['Volatility']
    )

    print("\nVaR Comparison (All Methods):")
    print(var_results.to_string(index=False))

    # Compare confidence levels
    print("\n" + "="*60)
    comparison = var_calc.compare_confidence_levels(
        returns,
        position_value=1000000,
        confidence_levels=[0.90, 0.95, 0.99],
        method='historical'
    )
    print("\nVaR at Different Confidence Levels (Historical Method):")
    print(comparison.to_string(index=False))
