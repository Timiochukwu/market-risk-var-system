# Day 001: Environment Setup & Data Collection

**Duration**: 1.5 - 2 hours
**Difficulty**: Beginner
**Prerequisites**: Basic Python knowledge, Python 3.8+ installed

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Set up your project structure
- Install necessary Python packages
- Create a data collector that fetches stock market data from Yahoo Finance
- Understand how financial data is structured
- Test your data collector with real stock data (Apple - AAPL)

---

## 🎯 Learning Objectives

### Financial Concepts:
- **Stock Prices**: Understand OHLC (Open, High, Low, Close) data
- **Trading Volume**: Number of shares traded
- **Market Data Sources**: Yahoo Finance API

### Programming Concepts:
- Python project structure
- Virtual environments
- External API integration
- Pandas DataFrames
- Error handling and logging

---

## 📦 Step 1: Project Setup (15 minutes)

### 1.1 Create Project Directory Structure

```bash
# Navigate to your project root
cd /home/user/market-risk-var-system

# Create directory structure
mkdir -p src/data
mkdir -p src/models
mkdir -p src/utils
mkdir -p src/api
mkdir -p tests
mkdir -p guide

# Create __init__.py files (makes directories Python packages)
touch src/__init__.py
touch src/data/__init__.py
touch src/models/__init__.py
touch src/utils/__init__.py
touch src/api/__init__.py
```

**What you just did:**
- Created a professional Python project structure
- `src/` = Source code directory
- Each subdirectory is a module (data, models, utils, api)
- `__init__.py` files tell Python these are packages

### 1.2 Create Virtual Environment (Optional but Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows

# Your prompt should now show (venv)
```

**Why virtual environments?**
- Isolates project dependencies
- Prevents conflicts with other Python projects
- Makes it easy to reproduce your setup

---

## 📦 Step 2: Install Dependencies (10 minutes)

### 2.1 Create requirements.txt

Create a file called `requirements_day001.txt` in the project root:

```bash
# Day 001 Dependencies - Data Collection
pandas==2.0.0
numpy==1.24.0
yfinance==0.2.28
requests==2.31.0
python-dateutil==2.8.2
```

### 2.2 Install Packages

```bash
pip install pandas==2.0.0 numpy==1.24.0 yfinance==0.2.28 requests==2.31.0 python-dateutil==2.8.2
```

**What each package does:**
- `pandas` - Data manipulation and analysis (think Excel for Python)
- `numpy` - Numerical computing (fast math operations)
- `yfinance` - Downloads stock market data from Yahoo Finance
- `requests` - Makes HTTP requests (downloads data from web)
- `python-dateutil` - Date/time manipulation

**Installation time**: 2-3 minutes

---

## 💻 Step 3: Build the Data Collector (45 minutes)

### 3.1 Understanding What We're Building

We're creating a `DataCollector` class that:
1. Fetches historical stock prices from Yahoo Finance
2. Handles different time periods (1 month, 1 year, 5 years, etc.)
3. Handles errors gracefully (what if the stock ticker is wrong?)
4. Returns data in a clean Pandas DataFrame

### 3.2 Create `src/data/data_collector.py`

Open your editor and create this file:

```python
"""
Data Collector Module for Market Risk VaR System
Fetches stock market data from Yahoo Finance
"""

import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional

# Set up logging (helps us debug issues)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collects financial market data from Yahoo Finance

    This class provides methods to fetch stock prices, forex rates,
    and cryptocurrency data for risk analysis.
    """

    def __init__(self):
        """Initialize the Data Collector"""
        logger.info("DataCollector initialized")

    def fetch_stock_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "1y"
    ) -> pd.DataFrame:
        """
        Fetch stock price data from Yahoo Finance

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
            start_date: Start date in 'YYYY-MM-DD' format (optional)
            end_date: End date in 'YYYY-MM-DD' format (optional)
            period: Time period if dates not specified
                    Options: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Adj Close

        Examples:
            >>> collector = DataCollector()
            >>> # Get 1 year of Apple stock data
            >>> data = collector.fetch_stock_data("AAPL", period="1y")
            >>> # Get data for specific date range
            >>> data = collector.fetch_stock_data("MSFT", start_date="2020-01-01", end_date="2023-12-31")
        """

        logger.info(f"Fetching data for {ticker}...")

        try:
            # Create a Ticker object
            stock = yf.Ticker(ticker)

            # Fetch historical data
            if start_date and end_date:
                # Use specific date range
                data = stock.history(start=start_date, end=end_date)
                logger.info(f"Fetched data from {start_date} to {end_date}")
            else:
                # Use period (e.g., "1y" for 1 year)
                data = stock.history(period=period)
                logger.info(f"Fetched data for period: {period}")

            # Check if data is empty
            if data.empty:
                logger.warning(f"No data found for ticker: {ticker}")
                return pd.DataFrame()

            # Log success
            logger.info(f"Successfully fetched {len(data)} records for {ticker}")
            logger.info(f"Date range: {data.index[0]} to {data.index[-1]}")

            return data

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return pd.DataFrame()

    def fetch_multiple_tickers(
        self,
        tickers: list,
        period: str = "1y"
    ) -> dict:
        """
        Fetch data for multiple tickers

        Args:
            tickers: List of ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOGL'])
            period: Time period for all tickers

        Returns:
            Dictionary with ticker as key and DataFrame as value

        Example:
            >>> collector = DataCollector()
            >>> data = collector.fetch_multiple_tickers(['AAPL', 'MSFT'], period='6mo')
            >>> aapl_data = data['AAPL']
        """

        logger.info(f"Fetching data for {len(tickers)} tickers...")

        results = {}

        for ticker in tickers:
            data = self.fetch_stock_data(ticker, period=period)
            if not data.empty:
                results[ticker] = data

        logger.info(f"Successfully fetched data for {len(results)}/{len(tickers)} tickers")

        return results

    def get_latest_price(self, ticker: str) -> float:
        """
        Get the most recent closing price for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Latest closing price as float

        Example:
            >>> collector = DataCollector()
            >>> price = collector.get_latest_price('AAPL')
            >>> print(f"Apple stock price: ${price:.2f}")
        """

        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")

            if data.empty:
                logger.warning(f"No price data found for {ticker}")
                return 0.0

            latest_price = data['Close'].iloc[-1]
            logger.info(f"{ticker} latest price: ${latest_price:.2f}")

            return float(latest_price)

        except Exception as e:
            logger.error(f"Error getting latest price for {ticker}: {str(e)}")
            return 0.0

    def get_stock_info(self, ticker: str) -> dict:
        """
        Get detailed information about a stock

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with stock information (name, sector, market cap, etc.)

        Example:
            >>> collector = DataCollector()
            >>> info = collector.get_stock_info('AAPL')
            >>> print(f"Company: {info.get('longName', 'N/A')}")
        """

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            logger.info(f"Retrieved info for {ticker}: {info.get('longName', 'N/A')}")

            return info

        except Exception as e:
            logger.error(f"Error getting info for {ticker}: {str(e)}")
            return {}


# Example usage (run this file directly to test)
if __name__ == "__main__":
    print("="*60)
    print("Testing DataCollector")
    print("="*60)

    # Create a DataCollector instance
    collector = DataCollector()

    # Test 1: Fetch Apple stock data for 1 year
    print("\n📊 Test 1: Fetching AAPL data (1 year)...")
    aapl_data = collector.fetch_stock_data("AAPL", period="1y")
    print(f"\nData shape: {aapl_data.shape}")
    print(f"\nFirst 5 rows:")
    print(aapl_data.head())
    print(f"\nLast 5 rows:")
    print(aapl_data.tail())

    # Test 2: Get latest price
    print("\n💰 Test 2: Getting latest price...")
    latest_price = collector.get_latest_price("AAPL")
    print(f"AAPL latest price: ${latest_price:.2f}")

    # Test 3: Get stock info
    print("\n📋 Test 3: Getting stock info...")
    info = collector.get_stock_info("AAPL")
    print(f"Company Name: {info.get('longName', 'N/A')}")
    print(f"Sector: {info.get('sector', 'N/A')}")
    print(f"Industry: {info.get('industry', 'N/A')}")
    print(f"Market Cap: ${info.get('marketCap', 0):,}")

    # Test 4: Fetch multiple tickers
    print("\n📊 Test 4: Fetching multiple tickers...")
    multi_data = collector.fetch_multiple_tickers(['AAPL', 'MSFT', 'GOOGL'], period='6mo')
    print(f"Successfully fetched data for: {list(multi_data.keys())}")

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
```

---

## 🧪 Step 4: Test Your Data Collector (20 minutes)

### 4.1 Run the Test

```bash
cd /home/user/market-risk-var-system
python src/data/data_collector.py
```

### 4.2 Expected Output

You should see something like:

```
============================================================
Testing DataCollector
============================================================
INFO:__main__:DataCollector initialized

📊 Test 1: Fetching AAPL data (1 year)...
INFO:__main__:Fetching data for AAPL...
INFO:__main__:Fetched data for period: 1y
INFO:__main__:Successfully fetched 252 records for AAPL
INFO:__main__:Date range: 2023-01-03 to 2024-01-02

Data shape: (252, 7)

First 5 rows:
                  Open        High         Low       Close   Volume  Dividends  Stock Splits
Date
2023-01-03  130.28  130.90  124.17  125.07  112117500        0.0           0.0
2023-01-04  126.89  128.66  125.08  126.36   89113600        0.0           0.0
...

💰 Test 2: Getting latest price...
AAPL latest price: $185.92

📋 Test 3: Getting stock info...
Company Name: Apple Inc.
Sector: Technology
Industry: Consumer Electronics
Market Cap: 2,917,123,456,789

✅ All tests completed!
```

### 4.3 Understanding the Output

**Data Shape**: `(252, 7)` means:
- 252 rows = 252 trading days (approximately 1 year)
- 7 columns = Open, High, Low, Close, Volume, Dividends, Stock Splits

**Columns Explained**:
- `Open`: Price at market open (9:30 AM EST)
- `High`: Highest price during the day
- `Low`: Lowest price during the day
- `Close`: Price at market close (4:00 PM EST)
- `Volume`: Number of shares traded
- `Dividends`: Dividend payments (if any)
- `Stock Splits`: Stock split events

---

## 🔍 Step 5: Experiment and Explore (15 minutes)

Try these experiments to understand how the data collector works:

### Experiment 1: Different Time Periods

```python
from src.data.data_collector import DataCollector

collector = DataCollector()

# Get 5 years of data
data_5y = collector.fetch_stock_data("AAPL", period="5y")
print(f"5 years: {len(data_5y)} trading days")

# Get 1 month of data
data_1mo = collector.fetch_stock_data("AAPL", period="1mo")
print(f"1 month: {len(data_1mo)} trading days")

# Get maximum available data
data_max = collector.fetch_stock_data("AAPL", period="max")
print(f"Maximum: {len(data_max)} trading days")
```

### Experiment 2: Different Stocks

```python
# Tech stocks
msft_data = collector.fetch_stock_data("MSFT", period="1y")  # Microsoft
googl_data = collector.fetch_stock_data("GOOGL", period="1y")  # Google

# Other sectors
jpm_data = collector.fetch_stock_data("JPM", period="1y")  # JPMorgan (Finance)
xom_data = collector.fetch_stock_data("XOM", period="1y")  # ExxonMobil (Energy)
```

### Experiment 3: Specific Date Ranges

```python
# Get data for a specific year
data_2023 = collector.fetch_stock_data(
    "AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
print(f"2023 data: {len(data_2023)} days")
```

### Experiment 4: Invalid Ticker (Error Handling)

```python
# This should fail gracefully
bad_data = collector.fetch_stock_data("INVALIDTICKER")
print(f"Bad ticker returned: {bad_data.empty}")  # Should be True
```

---

## 📊 Step 6: Understanding Financial Data (10 minutes)

### What is OHLC Data?

Imagine you're tracking a stock throughout a single day:

```
9:30 AM (Market Open):  Stock price = $150 (OPEN)
10:00 AM:               Stock price = $155
11:00 AM:               Stock price = $148 (This becomes the LOW)
2:00 PM:                Stock price = $158 (This becomes the HIGH)
4:00 PM (Market Close): Stock price = $156 (CLOSE)
```

At the end of the day, you have:
- **Open**: $150
- **High**: $158
- **Low**: $148
- **Close**: $156
- **Volume**: Total shares traded (e.g., 50 million)

### Why Do We Need Historical Data?

For **Value at Risk (VaR)** calculations, we need to:
1. Calculate daily returns (how much the stock goes up/down each day)
2. Analyze patterns in volatility (how "jumpy" the stock is)
3. Predict future risk based on historical patterns

**More data = Better risk predictions**

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Set up a professional Python project structure
✅ Installed financial data analysis packages
✅ Created a `DataCollector` class that fetches real market data
✅ Tested your code with Apple stock (AAPL)
✅ Learned about OHLC (Open, High, Low, Close) data
✅ Understood why we need historical data for risk analysis

---

## 🐛 Troubleshooting

### Issue 1: "No module named 'yfinance'"

**Solution**: Make sure you installed the packages:
```bash
pip install yfinance
```

### Issue 2: "No data found for ticker"

**Possible causes**:
- Invalid ticker symbol (check spelling)
- Yahoo Finance is down (try again later)
- No internet connection

### Issue 3: Data is empty

**Solution**: Try a different time period:
```python
data = collector.fetch_stock_data("AAPL", period="5y")  # Use 5 years instead
```

### Issue 4: SSL Certificate Error

**Solution**:
```bash
pip install --upgrade certifi
```

---

## 📚 Additional Learning Resources

### Understanding Stock Market Data:
- [Investopedia - OHLC Charts](https://www.investopedia.com/terms/o/ohlcchart.asp)
- [What is Trading Volume?](https://www.investopedia.com/terms/v/volume.asp)

### Python & Pandas:
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Working with Time Series Data](https://pandas.pydata.org/docs/user_guide/timeseries.html)

---

## 🎯 Homework / Practice

Before moving to Day 002, try these exercises:

### Exercise 1: Fetch Your Favorite Stock
```python
# Replace with any stock you're interested in
my_stock = "TSLA"  # Tesla, or try NFLX (Netflix), NVDA (Nvidia)
data = collector.fetch_stock_data(my_stock, period="2y")
print(data.describe())  # Shows statistical summary
```

### Exercise 2: Compare Two Stocks
```python
aapl = collector.fetch_stock_data("AAPL", period="1y")
msft = collector.fetch_stock_data("MSFT", period="1y")

print(f"AAPL average close: ${aapl['Close'].mean():.2f}")
print(f"MSFT average close: ${msft['Close'].mean():.2f}")
```

### Exercise 3: Find the Biggest Price Move
```python
data = collector.fetch_stock_data("AAPL", period="1y")
data['Daily_Range'] = data['High'] - data['Low']
biggest_move = data['Daily_Range'].max()
biggest_move_date = data['Daily_Range'].idxmax()

print(f"Biggest daily price range: ${biggest_move:.2f}")
print(f"Date: {biggest_move_date}")
```

---

## 🔜 Coming Up in Day 002

Tomorrow you'll learn:
- How to calculate **returns** (daily price changes)
- Clean the data (handle missing values, outliers)
- Calculate summary statistics (mean, standard deviation)
- Understand **log returns** vs **simple returns**

**File you'll create**: `src/data/preprocessor.py`

---

## 💾 Save Your Work

Make sure to save all your files:
```bash
git add src/data/data_collector.py
git commit -m "Day 001: Add data collector module"
```

---

**Great job completing Day 001! See you tomorrow! 🚀**
