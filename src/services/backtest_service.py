"""
Backtesting Module for Market Risk VaR System
Tests VaR model accuracy and performs validation
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VaRBacktester:
    """Backtest VaR models"""

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize backtester

        Args:
            confidence_level: VaR confidence level
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

    def calculate_exceptions(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        position_value: float = 1000000
    ) -> pd.DataFrame:
        """
        Calculate VaR exceptions (breaches)

        Args:
            returns: Actual returns
            var_estimates: VaR estimates
            position_value: Portfolio value

        Returns:
            DataFrame with exception analysis
        """
        # Align series
        common_index = returns.index.intersection(var_estimates.index)
        returns_aligned = returns.loc[common_index]
        var_aligned = var_estimates.loc[common_index]

        # Calculate actual losses
        actual_losses = -returns_aligned * position_value

        # Identify exceptions (actual loss > VaR)
        exceptions = actual_losses > var_aligned

        # Create results DataFrame
        results = pd.DataFrame({
            'Returns': returns_aligned,
            'Actual_Loss': actual_losses,
            'VaR_Estimate': var_aligned,
            'Exception': exceptions,
            'Excess_Loss': np.where(exceptions, actual_losses - var_aligned, 0)
        })

        num_exceptions = exceptions.sum()
        exception_rate = num_exceptions / len(exceptions)
        expected_rate = self.alpha

        logger.info(f"Total observations: {len(exceptions)}")
        logger.info(f"Number of exceptions: {num_exceptions}")
        logger.info(f"Exception rate: {exception_rate:.2%}")
        logger.info(f"Expected rate: {expected_rate:.2%}")

        return results

    def kupiec_test(
        self,
        num_exceptions: int,
        num_observations: int
    ) -> Dict[str, float]:
        """
        Kupiec POF (Proportion of Failures) test

        Tests if exception rate is significantly different from expected rate

        Args:
            num_exceptions: Number of VaR exceptions
            num_observations: Total number of observations

        Returns:
            Dictionary with test results
        """
        expected_rate = self.alpha
        observed_rate = num_exceptions / num_observations

        # Likelihood ratio test statistic
        if num_exceptions == 0:
            lr_statistic = -2 * np.log((1 - expected_rate) ** num_observations)
        elif num_exceptions == num_observations:
            lr_statistic = -2 * np.log(expected_rate ** num_observations)
        else:
            lr_statistic = -2 * (
                num_observations * np.log(1 - expected_rate) +
                num_exceptions * np.log(expected_rate / observed_rate) +
                (num_observations - num_exceptions) * np.log(
                    (1 - expected_rate) / (1 - observed_rate)
                )
            )

        # Chi-square distribution with 1 degree of freedom
        p_value = 1 - stats.chi2.cdf(lr_statistic, df=1)

        # Test result (reject null hypothesis if p-value < 0.05)
        reject_null = p_value < 0.05

        results = {
            'LR_Statistic': lr_statistic,
            'P_Value': p_value,
            'Reject_Null': reject_null,
            'Observed_Rate': observed_rate,
            'Expected_Rate': expected_rate,
            'Test': 'Kupiec POF'
        }

        logger.info(f"Kupiec Test - LR Statistic: {lr_statistic:.4f}")
        logger.info(f"Kupiec Test - P-value: {p_value:.4f}")
        logger.info(f"Kupiec Test - Model {'REJECTED' if reject_null else 'ACCEPTED'}")

        return results

    def christoffersen_test(
        self,
        exceptions: pd.Series
    ) -> Dict[str, float]:
        """
        Christoffersen Independence test

        Tests if exceptions are independent (no clustering)

        Args:
            exceptions: Boolean series of VaR exceptions

        Returns:
            Dictionary with test results
        """
        # Count transitions
        n00 = 0  # No exception followed by no exception
        n01 = 0  # No exception followed by exception
        n10 = 0  # Exception followed by no exception
        n11 = 0  # Exception followed by exception

        for i in range(len(exceptions) - 1):
            if not exceptions.iloc[i] and not exceptions.iloc[i + 1]:
                n00 += 1
            elif not exceptions.iloc[i] and exceptions.iloc[i + 1]:
                n01 += 1
            elif exceptions.iloc[i] and not exceptions.iloc[i + 1]:
                n10 += 1
            elif exceptions.iloc[i] and exceptions.iloc[i + 1]:
                n11 += 1

        # Calculate probabilities
        if n00 + n01 > 0:
            pi_0 = n01 / (n00 + n01)
        else:
            pi_0 = 0

        if n10 + n11 > 0:
            pi_1 = n11 / (n10 + n11)
        else:
            pi_1 = 0

        pi = (n01 + n11) / (n00 + n01 + n10 + n11)

        # Likelihood ratio test statistic
        if pi_0 == 0 or pi_1 == 0 or pi == 0:
            lr_statistic = 0
        else:
            lr_statistic = -2 * (
                n00 * np.log(1 - pi) + n01 * np.log(pi) +
                n10 * np.log(1 - pi) + n11 * np.log(pi) -
                n00 * np.log(1 - pi_0) - n01 * np.log(pi_0) -
                n10 * np.log(1 - pi_1) - n11 * np.log(pi_1)
            )

        # Chi-square distribution with 1 degree of freedom
        p_value = 1 - stats.chi2.cdf(lr_statistic, df=1)
        reject_null = p_value < 0.05

        results = {
            'LR_Statistic': lr_statistic,
            'P_Value': p_value,
            'Reject_Null': reject_null,
            'Pi_0': pi_0,
            'Pi_1': pi_1,
            'Test': 'Christoffersen Independence'
        }

        logger.info(f"Christoffersen Test - LR Statistic: {lr_statistic:.4f}")
        logger.info(f"Christoffersen Test - P-value: {p_value:.4f}")
        logger.info(f"Christoffersen Test - Model {'REJECTED' if reject_null else 'ACCEPTED'}")

        return results

    def combined_test(
        self,
        exceptions: pd.Series,
        num_observations: int
    ) -> Dict[str, float]:
        """
        Combined Kupiec and Christoffersen test

        Args:
            exceptions: Boolean series of VaR exceptions
            num_observations: Total number of observations

        Returns:
            Dictionary with combined test results
        """
        num_exceptions = exceptions.sum()

        # Kupiec test
        kupiec_results = self.kupiec_test(num_exceptions, num_observations)

        # Christoffersen test
        christ_results = self.christoffersen_test(exceptions)

        # Combined test statistic
        combined_lr = kupiec_results['LR_Statistic'] + christ_results['LR_Statistic']
        combined_p_value = 1 - stats.chi2.cdf(combined_lr, df=2)
        reject_null = combined_p_value < 0.05

        results = {
            'Combined_LR_Statistic': combined_lr,
            'Combined_P_Value': combined_p_value,
            'Reject_Null': reject_null,
            'Kupiec_LR': kupiec_results['LR_Statistic'],
            'Christoffersen_LR': christ_results['LR_Statistic'],
            'Test': 'Combined (Kupiec + Christoffersen)'
        }

        logger.info(f"Combined Test - LR Statistic: {combined_lr:.4f}")
        logger.info(f"Combined Test - P-value: {combined_p_value:.4f}")
        logger.info(f"Combined Test - Model {'REJECTED' if reject_null else 'ACCEPTED'}")

        return results

    def traffic_light_test(
        self,
        num_exceptions: int,
        num_observations: int
    ) -> Dict[str, any]:
        """
        Basel Traffic Light test

        Classifies VaR model into green, yellow, or red zone

        Args:
            num_exceptions: Number of VaR exceptions
            num_observations: Total number of observations

        Returns:
            Dictionary with traffic light zone
        """
        expected_exceptions = self.alpha * num_observations

        # Basel zones (for 95% VaR with 250 observations)
        # Adjust for different sample sizes
        scale_factor = num_observations / 250

        green_threshold = 4 * scale_factor
        red_threshold = 10 * scale_factor

        if num_exceptions <= green_threshold:
            zone = 'Green'
            status = 'ACCEPTABLE'
        elif num_exceptions < red_threshold:
            zone = 'Yellow'
            status = 'WARNING'
        else:
            zone = 'Red'
            status = 'UNACCEPTABLE'

        results = {
            'Zone': zone,
            'Status': status,
            'Num_Exceptions': num_exceptions,
            'Expected_Exceptions': expected_exceptions,
            'Green_Threshold': green_threshold,
            'Red_Threshold': red_threshold,
            'Test': 'Traffic Light'
        }

        logger.info(f"Traffic Light Test - Zone: {zone} ({status})")
        logger.info(f"Exceptions: {num_exceptions:.0f} | Expected: {expected_exceptions:.2f}")

        return results

    def backtest_var_model(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        position_value: float = 1000000
    ) -> Dict[str, any]:
        """
        Comprehensive VaR model backtest

        Args:
            returns: Actual returns
            var_estimates: VaR estimates
            position_value: Portfolio value

        Returns:
            Dictionary with all backtest results
        """
        logger.info("="*60)
        logger.info("COMPREHENSIVE VAR BACKTEST")
        logger.info("="*60)

        # Calculate exceptions
        exception_results = self.calculate_exceptions(returns, var_estimates, position_value)

        num_exceptions = exception_results['Exception'].sum()
        num_observations = len(exception_results)

        logger.info("\n" + "="*60)
        logger.info("STATISTICAL TESTS")
        logger.info("="*60)

        # Kupiec test
        kupiec_results = self.kupiec_test(num_exceptions, num_observations)

        # Christoffersen test
        christ_results = self.christoffersen_test(exception_results['Exception'])

        # Combined test
        combined_results = self.combined_test(exception_results['Exception'], num_observations)

        # Traffic light test
        traffic_results = self.traffic_light_test(num_exceptions, num_observations)

        # Calculate additional metrics
        mean_excess_loss = exception_results[exception_results['Exception']]['Excess_Loss'].mean()
        max_excess_loss = exception_results['Excess_Loss'].max()

        # Summary
        summary = {
            'num_observations': num_observations,
            'num_exceptions': num_exceptions,
            'exception_rate': num_exceptions / num_observations,
            'expected_rate': self.alpha,
            'mean_excess_loss': mean_excess_loss,
            'max_excess_loss': max_excess_loss,
            'kupiec_test': kupiec_results,
            'christoffersen_test': christ_results,
            'combined_test': combined_results,
            'traffic_light_test': traffic_results,
            'exception_details': exception_results
        }

        return summary

    def rolling_backtest(
        self,
        returns: pd.Series,
        var_calculator,
        window: int = 252,
        position_value: float = 1000000
    ) -> pd.DataFrame:
        """
        Perform rolling window backtest

        Args:
            returns: Historical returns
            var_calculator: VaRCalculator instance
            window: Rolling window size
            position_value: Portfolio value

        Returns:
            DataFrame with rolling backtest results
        """
        results = []

        for i in range(window, len(returns)):
            # Training window
            train_returns = returns.iloc[i-window:i]

            # Calculate VaR
            var_result = var_calculator.historical_var(train_returns, position_value)

            # Actual return for next period
            actual_return = returns.iloc[i]
            actual_loss = -actual_return * position_value

            # Check for exception
            exception = actual_loss > var_result['VaR']

            results.append({
                'Date': returns.index[i],
                'VaR': var_result['VaR'],
                'Actual_Loss': actual_loss,
                'Exception': exception
            })

        results_df = pd.DataFrame(results)
        results_df.set_index('Date', inplace=True)

        # Calculate cumulative exception rate
        results_df['Cumulative_Exceptions'] = results_df['Exception'].cumsum()
        results_df['Cumulative_Rate'] = (
            results_df['Cumulative_Exceptions'] /
            range(1, len(results_df) + 1)
        )

        return results_df


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor
    from models.var_calculator import VaRCalculator

    # Collect and prepare data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()

    # Split into train and test
    train_size = int(len(returns) * 0.7)
    train_returns = returns.iloc[:train_size]
    test_returns = returns.iloc[train_size:]

    # Calculate VaR on training set
    var_calc = VaRCalculator(confidence_level=0.95)
    var_result = var_calc.historical_var(train_returns, position_value=1000000)

    # Create constant VaR estimates for test period
    var_estimates = pd.Series(
        var_result['VaR'],
        index=test_returns.index
    )

    # Backtest
    backtester = VaRBacktester(confidence_level=0.95)
    backtest_results = backtester.backtest_var_model(
        test_returns,
        var_estimates,
        position_value=1000000
    )

    # Display summary
    print("\n" + "="*60)
    print("BACKTEST SUMMARY")
    print("="*60)
    print(f"Number of exceptions: {backtest_results['num_exceptions']}")
    print(f"Exception rate: {backtest_results['exception_rate']:.2%}")
    print(f"Expected rate: {backtest_results['expected_rate']:.2%}")
    print(f"Traffic Light Zone: {backtest_results['traffic_light_test']['Zone']}")
    print(f"Kupiec Test P-value: {backtest_results['kupiec_test']['P_Value']:.4f}")
    print(f"Combined Test P-value: {backtest_results['combined_test']['Combined_P_Value']:.4f}")
