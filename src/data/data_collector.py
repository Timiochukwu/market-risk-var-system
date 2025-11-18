"""
Data Collector Module for Market Risk VaR System
Fetches stock and FX market data from various sources
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """Collect market data for risk analysis"""

    def __init__(self, data_dir: str = "data/raw"):
        """
        Initialize data collector

        Args:
            data_dir: Directory to store raw data
        """
        self.data_dir = data_dir

    def fetch_stock_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y"
    ) -> pd.DataFrame:
        """
        Fetch stock price data from Yahoo Finance

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            period: Period to fetch if dates not specified (default: 2 years)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"Fetching data for {ticker}...")

            if start_date and end_date:
                data = yf.download(ticker, start=start_date, end=end_date, progress=False)
            else:
                data = yf.download(ticker, period=period, progress=False)

            if data.empty:
                logger.warning(f"No data retrieved for {ticker}")
                return pd.DataFrame()

            # Add ticker column
            data['Ticker'] = ticker

            logger.info(f"Successfully fetched {len(data)} records for {ticker}")
            return data

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            raise

    def fetch_multiple_tickers(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y"
    ) -> pd.DataFrame:
        """
        Fetch data for multiple tickers

        Args:
            tickers: List of ticker symbols
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            period: Period to fetch if dates not specified

        Returns:
            DataFrame with combined data for all tickers
        """
        all_data = []

        for ticker in tickers:
            try:
                data = self.fetch_stock_data(ticker, start_date, end_date, period)
                if not data.empty:
                    all_data.append(data)
            except Exception as e:
                logger.error(f"Skipping {ticker} due to error: {str(e)}")
                continue

        if all_data:
            combined_data = pd.concat(all_data)
            logger.info(f"Successfully fetched data for {len(all_data)} tickers")
            return combined_data
        else:
            logger.warning("No data retrieved for any ticker")
            return pd.DataFrame()

    def fetch_fx_data(
        self,
        currency_pair: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y"
    ) -> pd.DataFrame:
        """
        Fetch foreign exchange data

        Args:
            currency_pair: Currency pair (e.g., 'EURUSD=X', 'GBPUSD=X')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            period: Period to fetch if dates not specified

        Returns:
            DataFrame with FX data
        """
        # Ensure proper FX ticker format
        if not currency_pair.endswith('=X'):
            currency_pair = f"{currency_pair}=X"

        return self.fetch_stock_data(currency_pair, start_date, end_date, period)

    def get_latest_price(self, ticker: str) -> float:
        """
        Get the latest price for a ticker

        Args:
            ticker: Ticker symbol

        Returns:
            Latest closing price
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.history(period="1d")
            if not info.empty:
                return info['Close'].iloc[-1]
            else:
                logger.warning(f"No recent data available for {ticker}")
                return 0.0
        except Exception as e:
            logger.error(f"Error getting latest price for {ticker}: {str(e)}")
            return 0.0

    def save_data(self, data: pd.DataFrame, filename: str) -> None:
        """
        Save data to CSV file

        Args:
            data: DataFrame to save
            filename: Output filename
        """
        import os

        os.makedirs(self.data_dir, exist_ok=True)
        filepath = os.path.join(self.data_dir, filename)

        data.to_csv(filepath)
        logger.info(f"Data saved to {filepath}")

    def load_data(self, filename: str) -> pd.DataFrame:
        """
        Load data from CSV file

        Args:
            filename: Input filename

        Returns:
            DataFrame with loaded data
        """
        import os

        filepath = os.path.join(self.data_dir, filename)

        if os.path.exists(filepath):
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            logger.info(f"Data loaded from {filepath}")
            return data
        else:
            logger.warning(f"File not found: {filepath}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Example usage
    collector = DataCollector()

    # Fetch single stock
    aapl_data = collector.fetch_stock_data("AAPL", period="1y")
    print(f"\nAAPL Data Shape: {aapl_data.shape}")
    print(aapl_data.head())

    # Fetch multiple stocks
    tickers = ["AAPL", "MSFT", "GOOGL"]
    multi_data = collector.fetch_multiple_tickers(tickers, period="6mo")
    print(f"\nMultiple Tickers Data Shape: {multi_data.shape}")

    # Fetch FX data
    fx_data = collector.fetch_fx_data("EURUSD", period="1y")
    print(f"\nEURUSD Data Shape: {fx_data.shape}")
    print(fx_data.head())
