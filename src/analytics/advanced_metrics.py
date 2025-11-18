"""
Advanced Risk Metrics Module for Market Risk VaR System

This module provides additional risk metrics beyond basic VaR:
- CVaR (Conditional Value at Risk / Expected Shortfall)
- Maximum Drawdown (largest peak-to-trough decline)
- Sharpe Ratio (risk-adjusted return)
- Sortino Ratio (downside risk-adjusted return)
- Calmar Ratio (return vs max drawdown)
- Value at Risk decomposition

These metrics help risk managers get a complete picture of portfolio risk.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from scipy import stats
import logging

# Set up logging to track what the code is doing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedRiskMetrics:
    """
    Calculate advanced risk metrics for portfolio analysis

    This class provides methods to calculate various risk metrics that complement
    traditional VaR analysis. These metrics are used by risk managers, portfolio
    managers, and regulators to assess investment risk.
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize the advanced risk metrics calculator

        Args:
            risk_free_rate: Annual risk-free rate (e.g., 0.02 for 2%)
                           This is typically the Treasury bill rate
        """
        self.risk_free_rate = risk_free_rate

    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95,
        position_value: float = 1000000
    ) -> Dict[str, float]:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall

        CVaR answers: "If losses exceed VaR, what's the expected loss?"
        It's more informative than VaR because it considers tail risk.

        Example:
            If 95% VaR is $10,000, CVaR might be $15,000
            This means: In the worst 5% of cases, average loss is $15,000

        Args:
            returns: Series of historical returns (e.g., daily returns)
            confidence_level: Confidence level (0.95 = 95%)
            position_value: Portfolio value in dollars

        Returns:
            Dictionary with CVaR and related statistics
        """
        # Remove any missing values
        returns_clean = returns.dropna()

        # Calculate the VaR threshold (the percentile below which we consider "bad outcomes")
        alpha = 1 - confidence_level
        var_threshold = returns_clean.quantile(alpha)

        # CVaR is the average of all returns below the VaR threshold
        # These are the "really bad" scenarios
        tail_losses = returns_clean[returns_clean <= var_threshold]
        cvar_percentage = -tail_losses.mean() if len(tail_losses) > 0 else -var_threshold

        # Convert percentage to dollar amount
        cvar_amount = cvar_percentage * position_value
        var_amount = -var_threshold * position_value

        # Calculate how much worse CVaR is than VaR
        # This shows the "tail risk" - how bad things can get beyond VaR
        tail_risk = cvar_amount - var_amount

        logger.info(f"CVaR ({confidence_level*100}%): ${cvar_amount:,.2f}")
        logger.info(f"VaR: ${var_amount:,.2f}")
        logger.info(f"Tail Risk: ${tail_risk:,.2f}")

        return {
            'CVaR': cvar_amount,
            'CVaR_Percentage': cvar_percentage * 100,
            'VaR': var_amount,
            'VaR_Percentage': -var_threshold * 100,
            'Tail_Risk': tail_risk,
            'Num_Tail_Events': len(tail_losses),
            'Worst_Loss': -returns_clean.min() * position_value
        }

    def calculate_maximum_drawdown(
        self,
        prices: pd.Series
    ) -> Dict[str, any]:
        """
        Calculate Maximum Drawdown (MDD)

        Maximum Drawdown is the largest peak-to-trough decline in portfolio value.
        It shows the biggest loss an investor would have experienced.

        Example:
            Portfolio goes from $100k → $120k → $80k → $110k
            MDD = ($120k - $80k) / $120k = 33.3%

        This is important because:
        - Shows worst historical loss
        - Indicates how much pain investors endured
        - Used in Calmar Ratio calculation

        Args:
            prices: Series of portfolio prices or cumulative returns

        Returns:
            Dictionary with MDD statistics
        """
        # Calculate cumulative maximum (the highest point reached so far)
        # This is the "peak" at each point in time
        cumulative_max = prices.cummax()

        # Calculate drawdown at each point
        # Drawdown = (current price - peak price) / peak price
        drawdown = (prices - cumulative_max) / cumulative_max

        # Find the maximum drawdown (most negative value)
        max_drawdown = drawdown.min()

        # Find when the maximum drawdown occurred
        max_dd_date = drawdown.idxmin()

        # Find the peak before the drawdown
        peak_date = prices[:max_dd_date].idxmax()
        peak_value = prices[peak_date]

        # Find the trough (lowest point)
        trough_value = prices[max_dd_date]

        # Calculate recovery time (how long to get back to peak)
        # Find the first date after trough where price exceeds peak
        recovery_dates = prices[max_dd_date:][prices[max_dd_date:] >= peak_value]
        recovery_date = recovery_dates.index[0] if len(recovery_dates) > 0 else None

        # Calculate how many days it took to recover
        if recovery_date:
            recovery_days = (recovery_date - max_dd_date).days
        else:
            recovery_days = None  # Still in drawdown

        logger.info(f"Maximum Drawdown: {max_drawdown*100:.2f}%")
        logger.info(f"Peak Date: {peak_date.date()}")
        logger.info(f"Trough Date: {max_dd_date.date()}")

        return {
            'Max_Drawdown': max_drawdown,
            'Max_Drawdown_Percentage': max_drawdown * 100,
            'Peak_Date': peak_date,
            'Trough_Date': max_dd_date,
            'Peak_Value': peak_value,
            'Trough_Value': trough_value,
            'Recovery_Date': recovery_date,
            'Recovery_Days': recovery_days,
            'Current_Drawdown': drawdown.iloc[-1]
        }

    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted return metric)

        Sharpe Ratio = (Return - Risk-Free Rate) / Volatility

        It measures how much extra return you get per unit of risk.
        Higher is better!

        Example:
            Strategy A: 10% return, 5% volatility → Sharpe = 1.6
            Strategy B: 12% return, 10% volatility → Sharpe = 1.0
            Strategy A is better (more return per unit of risk)

        Interpretation:
            < 1.0: Poor risk-adjusted returns
            1.0-2.0: Good
            2.0-3.0: Very good
            > 3.0: Excellent

        Args:
            returns: Series of returns (e.g., daily)
            periods_per_year: Trading periods per year (252 for daily, 12 for monthly)

        Returns:
            Annualized Sharpe Ratio
        """
        # Calculate excess returns (returns above risk-free rate)
        # Convert annual risk-free rate to period rate
        period_rf_rate = self.risk_free_rate / periods_per_year
        excess_returns = returns - period_rf_rate

        # Calculate annualized mean and std
        mean_excess = excess_returns.mean() * periods_per_year
        std_excess = excess_returns.std() * np.sqrt(periods_per_year)

        # Sharpe Ratio = Mean Excess Return / Volatility
        sharpe_ratio = mean_excess / std_excess if std_excess != 0 else 0

        logger.info(f"Sharpe Ratio: {sharpe_ratio:.4f}")

        return sharpe_ratio

    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sortino Ratio (like Sharpe, but only considers downside risk)

        Sortino Ratio = (Return - Risk-Free Rate) / Downside Deviation

        Unlike Sharpe Ratio, Sortino only penalizes downside volatility.
        Upside volatility is good (we like big gains!), so it's not penalized.

        This is more investor-friendly because:
        - We don't care if returns are volatile on the upside
        - We only care about downside risk

        Args:
            returns: Series of returns
            periods_per_year: Trading periods per year

        Returns:
            Annualized Sortino Ratio
        """
        # Calculate excess returns
        period_rf_rate = self.risk_free_rate / periods_per_year
        excess_returns = returns - period_rf_rate

        # Calculate downside deviation (only negative returns matter)
        # Square all negative excess returns, average them, then take square root
        downside_returns = excess_returns[excess_returns < 0]
        downside_deviation = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(periods_per_year)

        # Sortino Ratio
        mean_excess = excess_returns.mean() * periods_per_year
        sortino_ratio = mean_excess / downside_deviation if downside_deviation != 0 else 0

        logger.info(f"Sortino Ratio: {sortino_ratio:.4f}")

        return sortino_ratio

    def calculate_calmar_ratio(
        self,
        returns: pd.Series,
        prices: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Calmar Ratio (return vs maximum drawdown)

        Calmar Ratio = Annualized Return / Maximum Drawdown

        This measures return relative to the worst loss experienced.
        Higher is better - means you get good returns without big drawdowns.

        Example:
            10% annual return, 20% max drawdown → Calmar = 0.5
            10% annual return, 10% max drawdown → Calmar = 1.0 (better!)

        Args:
            returns: Series of returns
            prices: Series of prices (to calculate drawdown)
            periods_per_year: Trading periods per year

        Returns:
            Calmar Ratio
        """
        # Calculate annualized return
        annualized_return = returns.mean() * periods_per_year

        # Calculate maximum drawdown
        mdd_result = self.calculate_maximum_drawdown(prices)
        max_drawdown = abs(mdd_result['Max_Drawdown'])

        # Calmar Ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown != 0 else 0

        logger.info(f"Calmar Ratio: {calmar_ratio:.4f}")

        return calmar_ratio

    def calculate_var_decomposition(
        self,
        returns_df: pd.DataFrame,
        weights: np.ndarray,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Decompose portfolio VaR into individual asset contributions

        This shows how much each asset contributes to total portfolio risk.
        Useful for:
        - Identifying main risk drivers
        - Rebalancing decisions
        - Risk budgeting

        Example:
            Portfolio VaR = $100k
            - Stock A contributes 60% → $60k
            - Stock B contributes 40% → $40k

        Args:
            returns_df: DataFrame with returns for each asset (columns = assets)
            weights: Array of portfolio weights (must sum to 1)
            confidence_level: VaR confidence level

        Returns:
            DataFrame with VaR contributions by asset
        """
        # Calculate portfolio returns
        portfolio_returns = (returns_df * weights).sum(axis=1)

        # Calculate portfolio VaR
        alpha = 1 - confidence_level
        portfolio_var = -portfolio_returns.quantile(alpha)

        # Calculate covariance matrix (shows how assets move together)
        cov_matrix = returns_df.cov()

        # Calculate portfolio volatility
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_vol = np.sqrt(portfolio_variance)

        # Calculate marginal VaR (how VaR changes if we add more of an asset)
        marginal_var = np.dot(cov_matrix, weights) / portfolio_vol

        # Calculate component VaR (actual contribution of each asset)
        component_var = weights * marginal_var * portfolio_var / portfolio_vol

        # Calculate percentage contribution
        percent_contribution = (component_var / portfolio_var) * 100

        # Create results DataFrame
        decomposition = pd.DataFrame({
            'Asset': returns_df.columns,
            'Weight': weights * 100,
            'Component_VaR': component_var,
            'Percent_Contribution': percent_contribution,
            'Marginal_VaR': marginal_var
        })

        logger.info(f"Portfolio VaR: {portfolio_var:.6f}")
        logger.info("VaR Decomposition:")
        logger.info(f"\n{decomposition.to_string()}")

        return decomposition

    def calculate_all_metrics(
        self,
        returns: pd.Series,
        prices: pd.Series,
        position_value: float = 1000000,
        confidence_level: float = 0.95
    ) -> Dict[str, any]:
        """
        Calculate all advanced risk metrics in one call

        This is a convenience method that calculates everything at once.
        Perfect for generating comprehensive risk reports.

        Args:
            returns: Series of returns
            prices: Series of prices
            position_value: Portfolio value
            confidence_level: VaR confidence level

        Returns:
            Dictionary with all risk metrics
        """
        logger.info("Calculating all advanced risk metrics...")

        # Calculate each metric
        cvar = self.calculate_cvar(returns, confidence_level, position_value)
        mdd = self.calculate_maximum_drawdown(prices)
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        calmar = self.calculate_calmar_ratio(returns, prices)

        # Combine into single dictionary
        all_metrics = {
            'CVaR': cvar,
            'Maximum_Drawdown': mdd,
            'Sharpe_Ratio': sharpe,
            'Sortino_Ratio': sortino,
            'Calmar_Ratio': calmar
        }

        return all_metrics

    def get_risk_summary(
        self,
        returns: pd.Series,
        prices: pd.Series,
        position_value: float = 1000000
    ) -> pd.DataFrame:
        """
        Create a summary table of all risk metrics

        This creates a nice formatted table perfect for reports.

        Args:
            returns: Series of returns
            prices: Series of prices
            position_value: Portfolio value

        Returns:
            DataFrame with formatted risk metrics summary
        """
        metrics = self.calculate_all_metrics(returns, prices, position_value)

        # Create summary rows
        summary_data = [
            ['CVaR (95%)', f"${metrics['CVaR']['CVaR']:,.2f}", 'Expected loss in worst 5% scenarios'],
            ['Max Drawdown', f"{metrics['Maximum_Drawdown']['Max_Drawdown_Percentage']:.2f}%", 'Largest peak-to-trough decline'],
            ['Sharpe Ratio', f"{metrics['Sharpe_Ratio']:.4f}", 'Risk-adjusted return (higher is better)'],
            ['Sortino Ratio', f"{metrics['Sortino_Ratio']:.4f}", 'Downside risk-adjusted return'],
            ['Calmar Ratio', f"{metrics['Calmar_Ratio']:.4f}", 'Return vs max drawdown']
        ]

        summary_df = pd.DataFrame(
            summary_data,
            columns=['Metric', 'Value', 'Description']
        )

        return summary_df


# Example usage - only runs when you execute this file directly
if __name__ == "__main__":
    # Import required modules
    import sys
    sys.path.append('../..')
    from src.data.data_collector import DataCollector
    from src.data.preprocessor import DataPreprocessor

    # Collect sample data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    # Prepare returns
    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)

    # Calculate advanced metrics
    advanced_metrics = AdvancedRiskMetrics(risk_free_rate=0.02)

    # Get comprehensive risk summary
    summary = advanced_metrics.get_risk_summary(
        returns=returns_data['Returns'].dropna(),
        prices=returns_data['Price'],
        position_value=1000000
    )

    print("\n" + "="*80)
    print("ADVANCED RISK METRICS SUMMARY")
    print("="*80)
    print(summary.to_string(index=False))
    print("="*80)
