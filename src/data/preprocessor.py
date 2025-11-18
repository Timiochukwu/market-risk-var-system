"""
Data Preprocessor Module for Market Risk VaR System
Calculates returns, cleans data, and prepares for modeling
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocess market data for risk analysis"""

    def __init__(self, data_dir: str = "data/processed"):
        """
        Initialize data preprocessor

        Args:
            data_dir: Directory to store processed data
        """
        self.data_dir = data_dir

    def calculate_returns(
        self,
        data: pd.DataFrame,
        price_column: str = 'Close',
        method: str = 'log'
    ) -> pd.Series:
        """
        Calculate returns from price data

        Args:
            data: DataFrame with price data
            price_column: Column name for prices
            method: 'log' for log returns or 'simple' for simple returns

        Returns:
            Series with calculated returns
        """
        prices = data[price_column]

        if method == 'log':
            returns = np.log(prices / prices.shift(1))
            logger.info("Calculated log returns")
        elif method == 'simple':
            returns = prices.pct_change()
            logger.info("Calculated simple returns")
        else:
            raise ValueError(f"Unknown method: {method}. Use 'log' or 'simple'")

        return returns

    def clean_data(
        self,
        data: pd.DataFrame,
        remove_na: bool = True,
        remove_outliers: bool = False,
        outlier_std: float = 5.0
    ) -> pd.DataFrame:
        """
        Clean data by removing NaN values and outliers

        Args:
            data: DataFrame to clean
            remove_na: Whether to remove NaN values
            remove_outliers: Whether to remove outliers
            outlier_std: Number of standard deviations for outlier detection

        Returns:
            Cleaned DataFrame
        """
        cleaned_data = data.copy()
        initial_len = len(cleaned_data)

        if remove_na:
            cleaned_data = cleaned_data.dropna()
            logger.info(f"Removed {initial_len - len(cleaned_data)} NaN values")

        if remove_outliers:
            # Remove outliers based on z-score
            numeric_cols = cleaned_data.select_dtypes(include=[np.number]).columns

            for col in numeric_cols:
                mean = cleaned_data[col].mean()
                std = cleaned_data[col].std()
                z_scores = np.abs((cleaned_data[col] - mean) / std)
                cleaned_data = cleaned_data[z_scores < outlier_std]

            logger.info(f"Removed {initial_len - len(cleaned_data)} outliers")

        return cleaned_data

    def prepare_returns_data(
        self,
        data: pd.DataFrame,
        price_column: str = 'Close',
        return_method: str = 'log',
        clean: bool = True
    ) -> pd.DataFrame:
        """
        Prepare returns data for modeling

        Args:
            data: Raw price DataFrame
            price_column: Column name for prices
            return_method: Method for calculating returns
            clean: Whether to clean the data

        Returns:
            DataFrame with returns and metadata
        """
        # Calculate returns
        returns = self.calculate_returns(data, price_column, return_method)

        # Create result DataFrame
        result = pd.DataFrame({
            'Price': data[price_column],
            'Returns': returns
        })

        # Add additional useful columns
        if 'Volume' in data.columns:
            result['Volume'] = data['Volume']

        # Clean data
        if clean:
            result = self.clean_data(result)

        logger.info(f"Prepared returns data with {len(result)} observations")
        return result

    def calculate_rolling_statistics(
        self,
        returns: pd.Series,
        window: int = 30
    ) -> pd.DataFrame:
        """
        Calculate rolling statistics for returns

        Args:
            returns: Series of returns
            window: Rolling window size

        Returns:
            DataFrame with rolling statistics
        """
        stats = pd.DataFrame(index=returns.index)

        stats['Rolling_Mean'] = returns.rolling(window=window).mean()
        stats['Rolling_Std'] = returns.rolling(window=window).std()
        stats['Rolling_Min'] = returns.rolling(window=window).min()
        stats['Rolling_Max'] = returns.rolling(window=window).max()
        stats['Rolling_Skew'] = returns.rolling(window=window).skew()
        stats['Rolling_Kurt'] = returns.rolling(window=window).kurt()

        logger.info(f"Calculated rolling statistics with window={window}")
        return stats

    def detect_regime_changes(
        self,
        returns: pd.Series,
        threshold: float = 2.0
    ) -> pd.Series:
        """
        Detect market regime changes based on volatility

        Args:
            returns: Series of returns
            threshold: Threshold for regime change (in std devs)

        Returns:
            Series with regime labels (0=normal, 1=high volatility)
        """
        # Calculate rolling volatility
        rolling_vol = returns.rolling(window=30).std()

        # Calculate volatility of volatility
        vol_mean = rolling_vol.mean()
        vol_std = rolling_vol.std()

        # Identify high volatility regimes
        regimes = (rolling_vol > (vol_mean + threshold * vol_std)).astype(int)

        logger.info(f"Detected {regimes.sum()} high volatility periods")
        return regimes

    def split_train_test(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.8
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into training and testing sets

        Args:
            data: DataFrame to split
            train_ratio: Ratio of data for training

        Returns:
            Tuple of (train_data, test_data)
        """
        split_idx = int(len(data) * train_ratio)

        train_data = data.iloc[:split_idx]
        test_data = data.iloc[split_idx:]

        logger.info(f"Split data: Train={len(train_data)}, Test={len(test_data)}")
        return train_data, test_data

    def normalize_data(
        self,
        data: pd.DataFrame,
        method: str = 'standardize'
    ) -> Tuple[pd.DataFrame, dict]:
        """
        Normalize data

        Args:
            data: DataFrame to normalize
            method: 'standardize' or 'minmax'

        Returns:
            Tuple of (normalized_data, scaling_params)
        """
        normalized = data.copy()
        params = {}

        numeric_cols = data.select_dtypes(include=[np.number]).columns

        if method == 'standardize':
            for col in numeric_cols:
                mean = data[col].mean()
                std = data[col].std()
                normalized[col] = (data[col] - mean) / std
                params[col] = {'mean': mean, 'std': std}

        elif method == 'minmax':
            for col in numeric_cols:
                min_val = data[col].min()
                max_val = data[col].max()
                normalized[col] = (data[col] - min_val) / (max_val - min_val)
                params[col] = {'min': min_val, 'max': max_val}

        else:
            raise ValueError(f"Unknown method: {method}")

        logger.info(f"Normalized data using {method} method")
        return normalized, params

    def get_summary_statistics(self, returns: pd.Series) -> dict:
        """
        Get summary statistics for returns

        Args:
            returns: Series of returns

        Returns:
            Dictionary with summary statistics
        """
        from scipy import stats

        clean_returns = returns.dropna()

        summary = {
            'count': len(clean_returns),
            'mean': clean_returns.mean(),
            'std': clean_returns.std(),
            'min': clean_returns.min(),
            'max': clean_returns.max(),
            'skewness': stats.skew(clean_returns),
            'kurtosis': stats.kurtosis(clean_returns),
            'q25': clean_returns.quantile(0.25),
            'median': clean_returns.median(),
            'q75': clean_returns.quantile(0.75),
            'var_95': clean_returns.quantile(0.05),
            'var_99': clean_returns.quantile(0.01)
        }

        return summary

    def save_processed_data(self, data: pd.DataFrame, filename: str) -> None:
        """
        Save processed data to CSV

        Args:
            data: DataFrame to save
            filename: Output filename
        """
        import os

        os.makedirs(self.data_dir, exist_ok=True)
        filepath = os.path.join(self.data_dir, filename)

        data.to_csv(filepath)
        logger.info(f"Processed data saved to {filepath}")

    def load_processed_data(self, filename: str) -> pd.DataFrame:
        """
        Load processed data from CSV

        Args:
            filename: Input filename

        Returns:
            DataFrame with loaded data
        """
        import os

        filepath = os.path.join(self.data_dir, filename)

        if os.path.exists(filepath):
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            logger.info(f"Processed data loaded from {filepath}")
            return data
        else:
            logger.warning(f"File not found: {filepath}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Example usage
    from data_collector import DataCollector

    # Collect data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="1y")

    # Preprocess data
    preprocessor = DataPreprocessor()

    # Prepare returns
    returns_data = preprocessor.prepare_returns_data(data)
    print("\nReturns Data:")
    print(returns_data.head())

    # Get summary statistics
    summary = preprocessor.get_summary_statistics(returns_data['Returns'])
    print("\nSummary Statistics:")
    for key, value in summary.items():
        print(f"{key}: {value:.6f}")

    # Calculate rolling statistics
    rolling_stats = preprocessor.calculate_rolling_statistics(
        returns_data['Returns'], window=30
    )
    print("\nRolling Statistics:")
    print(rolling_stats.tail())
