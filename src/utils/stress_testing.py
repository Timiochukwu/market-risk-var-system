"""
Stress Testing and Scenario Analysis Module

This module helps answer "What if?" questions:
- What if the market crashes 20%?
- What if volatility doubles?
- What if we have another 2008-style crisis?

Stress testing is crucial for risk management because:
1. Shows how portfolio performs in extreme scenarios
2. Identifies vulnerabilities before they cause losses
3. Required by regulators (Basel III, Dodd-Frank)
4. Helps in risk budgeting and capital allocation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StressTester:
    """
    Perform stress testing and scenario analysis on portfolios

    Stress testing involves applying extreme but plausible scenarios
    to see how a portfolio would perform. Think of it as "war gaming"
    your portfolio against various disaster scenarios.
    """

    def __init__(self):
        """Initialize stress tester"""
        self.scenarios = {}

    def market_crash_scenario(
        self,
        returns: pd.Series,
        crash_magnitude: float = -0.20,
        position_value: float = 1000000
    ) -> Dict[str, float]:
        """
        Simulate a market crash scenario

        This answers: "What if the market crashes X% tomorrow?"

        Example scenarios:
        - Flash crash: -10% (like 2010)
        - Major crash: -20% (like Black Monday 1987)
        - Extreme crash: -30% (like 1929)

        Args:
            returns: Historical returns series
            crash_magnitude: Size of crash (negative value, e.g., -0.20 for -20%)
            position_value: Current portfolio value

        Returns:
            Dictionary with crash impact metrics
        """
        # Calculate what happens to portfolio
        portfolio_loss = crash_magnitude * position_value
        new_portfolio_value = position_value * (1 + crash_magnitude)

        # Calculate how many standard deviations this crash represents
        # This shows how "extreme" the scenario is
        returns_std = returns.std()
        returns_mean = returns.mean()
        z_score = (crash_magnitude - returns_mean) / returns_std

        # Find if we've seen anything similar in history
        worse_days = returns[returns <= crash_magnitude]
        historical_probability = len(worse_days) / len(returns)

        logger.info(f"Market Crash Scenario: {crash_magnitude*100:.1f}%")
        logger.info(f"Portfolio Loss: ${abs(portfolio_loss):,.2f}")
        logger.info(f"New Portfolio Value: ${new_portfolio_value:,.2f}")

        return {
            'Scenario': 'Market Crash',
            'Crash_Magnitude': crash_magnitude * 100,
            'Portfolio_Loss': abs(portfolio_loss),
            'New_Portfolio_Value': new_portfolio_value,
            'Z_Score': z_score,
            'Sigma_Event': abs(z_score),  # How many standard deviations
            'Historical_Probability': historical_probability * 100,
            'Days_Seen_Worse': len(worse_days)
        }

    def volatility_spike_scenario(
        self,
        returns: pd.Series,
        current_position: float = 1000000,
        vol_multiplier: float = 2.0,
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Simulate a volatility spike scenario

        This answers: "What if volatility suddenly doubles or triples?"

        Volatility spikes happen during:
        - Market panics (VIX spikes)
        - Economic crises
        - Geopolitical events

        When volatility increases, VaR increases proportionally.

        Args:
            returns: Historical returns
            current_position: Portfolio value
            vol_multiplier: How much volatility increases (2.0 = doubles)
            confidence_level: VaR confidence level

        Returns:
            Dictionary with volatility spike impact
        """
        # Calculate current volatility and VaR
        current_vol = returns.std()
        current_var = -returns.quantile(1 - confidence_level) * current_position

        # Calculate stressed volatility and VaR
        stressed_vol = current_vol * vol_multiplier
        stressed_var = current_var * vol_multiplier

        # Calculate additional capital needed (VaR increase)
        additional_var = stressed_var - current_var

        logger.info(f"Volatility Spike: {vol_multiplier}x increase")
        logger.info(f"Current VaR: ${current_var:,.2f}")
        logger.info(f"Stressed VaR: ${stressed_var:,.2f}")

        return {
            'Scenario': 'Volatility Spike',
            'Volatility_Multiplier': vol_multiplier,
            'Current_Volatility': current_vol * 100,
            'Stressed_Volatility': stressed_vol * 100,
            'Current_VaR': current_var,
            'Stressed_VaR': stressed_var,
            'VaR_Increase': additional_var,
            'VaR_Increase_Percentage': (additional_var / current_var) * 100
        }

    def correlation_breakdown_scenario(
        self,
        returns_df: pd.DataFrame,
        weights: np.ndarray,
        correlation_target: float = 1.0
    ) -> Dict[str, float]:
        """
        Simulate correlation breakdown (when diversification fails)

        This answers: "What if all my assets move together in a crisis?"

        During market crashes, correlations often spike to 1.0:
        - Stocks, bonds, commodities all fall together
        - Diversification provides no protection
        - "The only thing that goes up is correlation!"

        This is one of the biggest risks in portfolio management.

        Args:
            returns_df: DataFrame with returns for each asset
            weights: Portfolio weights
            correlation_target: Target correlation (1.0 = perfect correlation)

        Returns:
            Dictionary with correlation breakdown impact
        """
        # Calculate current portfolio statistics
        current_returns = (returns_df * weights).sum(axis=1)
        current_vol = current_returns.std()

        # Create stressed correlation matrix (all correlations = target)
        num_assets = len(weights)
        stressed_corr = np.full((num_assets, num_assets), correlation_target)
        np.fill_diagonal(stressed_corr, 1.0)  # Diagonal is always 1

        # Calculate individual asset volatilities
        individual_vols = returns_df.std().values

        # Create stressed covariance matrix
        # Cov = Corr × Vol1 × Vol2
        stressed_cov = np.outer(individual_vols, individual_vols) * stressed_corr

        # Calculate stressed portfolio volatility
        stressed_variance = np.dot(weights, np.dot(stressed_cov, weights))
        stressed_vol = np.sqrt(stressed_variance)

        # Calculate increase in volatility
        vol_increase = stressed_vol - current_vol
        vol_increase_pct = (vol_increase / current_vol) * 100

        logger.info(f"Correlation Breakdown Scenario")
        logger.info(f"Current Portfolio Vol: {current_vol*100:.2f}%")
        logger.info(f"Stressed Portfolio Vol: {stressed_vol*100:.2f}%")

        return {
            'Scenario': 'Correlation Breakdown',
            'Target_Correlation': correlation_target,
            'Current_Volatility': current_vol * 100,
            'Stressed_Volatility': stressed_vol * 100,
            'Volatility_Increase': vol_increase * 100,
            'Volatility_Increase_Percentage': vol_increase_pct
        }

    def historical_scenario(
        self,
        returns: pd.Series,
        scenario_name: str,
        scenario_return: float,
        position_value: float = 1000000
    ) -> Dict[str, float]:
        """
        Apply a historical crisis scenario

        This replicates actual historical events:
        - Black Monday 1987: -22.6%
        - 2008 Financial Crisis: -38% (peak to trough)
        - COVID-19 Crash: -34% (Feb-Mar 2020)
        - Dot-com Crash: -49% (2000-2002)

        Learning from history helps prepare for the future.

        Args:
            returns: Historical returns
            scenario_name: Name of historical event
            scenario_return: Return during that event (negative)
            position_value: Portfolio value

        Returns:
            Dictionary with historical scenario impact
        """
        # Calculate portfolio impact
        portfolio_loss = scenario_return * position_value
        new_value = position_value * (1 + scenario_return)

        # Compare to historical distribution
        worse_days = returns[returns <= scenario_return]
        percentile = stats.percentileofscore(returns, scenario_return)

        logger.info(f"Historical Scenario: {scenario_name}")
        logger.info(f"Scenario Return: {scenario_return*100:.2f}%")
        logger.info(f"Portfolio Loss: ${abs(portfolio_loss):,.2f}")

        return {
            'Scenario': f'Historical - {scenario_name}',
            'Scenario_Return': scenario_return * 100,
            'Portfolio_Loss': abs(portfolio_loss),
            'New_Portfolio_Value': new_value,
            'Percentile': percentile,
            'Days_Worse_In_History': len(worse_days)
        }

    def custom_scenario(
        self,
        returns: pd.Series,
        scenario_name: str,
        shock: float,
        position_value: float = 1000000
    ) -> Dict[str, float]:
        """
        Create a custom stress scenario

        This allows you to test any specific scenario you're worried about:
        - Fed raises rates 2%
        - Oil price doubles
        - Currency devaluation
        - Competitor launches disruptive product

        Args:
            returns: Historical returns
            scenario_name: Name for your scenario
            shock: Expected return impact (e.g., -0.15 for -15%)
            position_value: Portfolio value

        Returns:
            Dictionary with scenario impact
        """
        portfolio_loss = shock * position_value
        new_value = position_value * (1 + shock)

        return {
            'Scenario': scenario_name,
            'Shock': shock * 100,
            'Portfolio_Loss': abs(portfolio_loss) if shock < 0 else 0,
            'Portfolio_Gain': shock * position_value if shock > 0 else 0,
            'New_Portfolio_Value': new_value,
            'Return': shock * 100
        }

    def run_comprehensive_stress_test(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Run a comprehensive set of stress scenarios

        This runs multiple scenarios at once to give you a full picture
        of potential risks. This is what risk managers present to executives.

        Scenarios included:
        1. Minor crash (-10%)
        2. Major crash (-20%)
        3. Extreme crash (-30%)
        4. Volatility doubles
        5. Volatility triples
        6. Historical events (2008, COVID, etc.)

        Args:
            returns: Historical returns
            position_value: Portfolio value
            confidence_level: VaR confidence level

        Returns:
            DataFrame with all stress test results
        """
        logger.info("Running comprehensive stress test...")

        results = []

        # Market crash scenarios
        for crash_pct in [-0.10, -0.20, -0.30]:
            result = self.market_crash_scenario(returns, crash_pct, position_value)
            results.append(result)

        # Volatility spike scenarios
        for vol_mult in [2.0, 3.0]:
            result = self.volatility_spike_scenario(returns, position_value, vol_mult, confidence_level)
            results.append(result)

        # Historical scenarios
        historical_scenarios = [
            ('Black Monday 1987', -0.226),
            ('2008 Financial Crisis', -0.38),
            ('COVID-19 Crash 2020', -0.34),
            ('Flash Crash 2010', -0.10)
        ]

        for name, ret in historical_scenarios:
            result = self.historical_scenario(returns, name, ret, position_value)
            results.append(result)

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        logger.info("Stress test completed")
        return results_df

    def reverse_stress_test(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        loss_threshold: float = 0.50
    ) -> Dict[str, float]:
        """
        Reverse stress test: "What scenario would wipe me out?"

        Instead of asking "What happens if X occurs?",
        this asks "What X would cause disaster?"

        Example: "What return would cause 50% portfolio loss?"

        This is required by many regulators and is very insightful
        for understanding your breaking point.

        Args:
            returns: Historical returns
            position_value: Portfolio value
            loss_threshold: Loss threshold (0.50 = 50% loss)

        Returns:
            Dictionary with reverse stress test results
        """
        # Calculate the return that would cause the threshold loss
        breaking_point_return = -loss_threshold

        # Calculate how many standard deviations this is
        returns_mean = returns.mean()
        returns_std = returns.std()
        z_score = (breaking_point_return - returns_mean) / returns_std

        # Check if we've ever seen this in history
        worse_days = returns[returns <= breaking_point_return]
        historical_occurrences = len(worse_days)

        # Calculate portfolio impact
        portfolio_loss = loss_threshold * position_value
        remaining_value = position_value * (1 - loss_threshold)

        logger.info(f"Reverse Stress Test: {loss_threshold*100:.0f}% loss threshold")
        logger.info(f"Breaking point return: {breaking_point_return*100:.2f}%")
        logger.info(f"Sigma event: {abs(z_score):.2f}σ")

        return {
            'Loss_Threshold': loss_threshold * 100,
            'Breaking_Point_Return': breaking_point_return * 100,
            'Portfolio_Loss': portfolio_loss,
            'Remaining_Value': remaining_value,
            'Sigma_Event': abs(z_score),
            'Historical_Occurrences': historical_occurrences,
            'Probability': (historical_occurrences / len(returns)) * 100
        }


# Predefined historical scenarios (ready to use!)
HISTORICAL_SCENARIOS = {
    'Black Monday 1987': -0.226,
    'Russian Crisis 1998': -0.165,
    'Dot-com Crash 2000-2002': -0.49,
    'September 11 2001': -0.117,
    '2008 Financial Crisis': -0.38,
    'Flash Crash 2010': -0.10,
    'COVID-19 Crash 2020': -0.34,
    'Russian Invasion 2022': -0.13
}


# Example usage
if __name__ == "__main__":
    import sys
    sys.path.append('../..')
    from src.data.data_collector import DataCollector
    from src.data.preprocessor import DataPreprocessor

    # Collect data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    # Prepare returns
    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()

    # Run stress tests
    stress_tester = StressTester()

    print("\n" + "="*80)
    print("COMPREHENSIVE STRESS TEST RESULTS")
    print("="*80)

    # Run all stress scenarios
    results = stress_tester.run_comprehensive_stress_test(
        returns,
        position_value=1000000
    )

    print(results.to_string(index=False))

    print("\n" + "="*80)
    print("REVERSE STRESS TEST")
    print("="*80)

    # Run reverse stress test
    reverse_result = stress_tester.reverse_stress_test(
        returns,
        position_value=1000000,
        loss_threshold=0.50
    )

    print(f"To lose 50% of portfolio:")
    print(f"Required return: {reverse_result['Breaking_Point_Return']:.2f}%")
    print(f"This is a {reverse_result['Sigma_Event']:.1f}-sigma event")
    print(f"Seen {reverse_result['Historical_Occurrences']} times in history")
    print("="*80)
