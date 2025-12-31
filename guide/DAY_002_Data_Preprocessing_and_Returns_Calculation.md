# Day 002: Data Preprocessing & Returns Calculation

**Duration**: 1.5 - 2 hours
**Difficulty**: Beginner-Intermediate
**Prerequisites**: Completed Day 001

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Understand what "returns" are and why they matter for risk analysis
- Learn the difference between simple returns and log returns
- Build a `DataPreprocessor` class to clean and transform data
- Detect and handle outliers in financial data
- Calculate summary statistics (mean, standard deviation, skewness, kurtosis)

---

## 🎯 Learning Objectives

### Financial Concepts:
- **Returns**: Percentage change in stock price
- **Simple Returns vs Log Returns**: Two ways to measure price changes
- **Volatility**: How much prices fluctuate (measured by standard deviation)
- **Outliers**: Unusual price movements (crashes, spikes)

### Programming Concepts:
- Data transformation with pandas
- Statistical calculations
- Z-score outlier detection
- Handling missing data (NaN values)

---

## 💡 Understanding Returns (15 minutes)

### Why We Use Returns Instead of Prices

**Question**: If Apple stock went from $150 to $155, is that good?

**Answer**: It depends!
- For a $10,000 portfolio: You gained $333 (3.3% return)
- For a $1,000 portfolio: You gained $33 (3.3% return)

**Returns are percentage changes** - they let us compare:
- Different stocks (Apple vs Microsoft)
- Different time periods (2020 vs 2023)
- Different portfolio sizes

### Two Types of Returns

#### 1. Simple Returns (Arithmetic Returns)
```
Simple Return = (Price_today - Price_yesterday) / Price_yesterday

Example:
Yesterday: $150
Today: $155
Simple Return = (155 - 150) / 150 = 0.0333 = 3.33%
```

#### 2. Log Returns (Continuously Compounded Returns)
```
Log Return = ln(Price_today / Price_yesterday)

Example:
Yesterday: $150
Today: $155
Log Return = ln(155/150) = 0.0328 = 3.28%
```

### Which One to Use?

**For VaR Analysis, we use Log Returns because:**
- ✅ They are time-additive (daily returns sum to weekly returns)
- ✅ They are symmetric (a +10% gain and -10% loss are equal magnitude)
- ✅ They are approximately normally distributed (needed for statistical models)
- ✅ Better for GARCH and ARIMA models

---

## 📦 Step 1: Install New Dependencies (5 minutes)

```bash
pip install scipy==1.11.0
```

**What scipy does**:
- Advanced statistical functions
- Distribution fitting
- Hypothesis testing
- Outlier detection

---

## 💻 Step 2: Build the Data Preprocessor (60 minutes)

### 2.1 Create `src/data/preprocessor.py`

```python
"""
Data Preprocessor Module for Market Risk VaR System
Calculates returns, cleans data, handles outliers
"""

import pandas as pd
import numpy as np
from scipy import stats
import logging
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Preprocesses financial data for VaR analysis

    Handles:
    - Returns calculation (simple and log returns)
    - Outlier detection and removal
    - Missing data handling
    - Summary statistics
    """

    def __init__(self):
        """Initialize Data Preprocessor"""
        logger.info("DataPreprocessor initialized")

    def calculate_simple_returns(self, prices: pd.Series) -> pd.Series:
        """
        Calculate simple (arithmetic) returns

        Formula: R_t = (P_t - P_{t-1}) / P_{t-1}

        Args:
            prices: Series of prices

        Returns:
            Series of simple returns

        Example:
            >>> prices = pd.Series([100, 105, 103, 108])
            >>> returns = preprocessor.calculate_simple_returns(prices)
            >>> # Returns: [NaN, 0.05, -0.019, 0.0485]
        """

        returns = prices.pct_change()
        logger.info(f"Calculated simple returns: {len(returns)} values")

        return returns

    def calculate_log_returns(self, prices: pd.Series) -> pd.Series:
        """
        Calculate logarithmic (continuously compounded) returns

        Formula: r_t = ln(P_t / P_{t-1})

        Args:
            prices: Series of prices

        Returns:
            Series of log returns

        Example:
            >>> prices = pd.Series([100, 105, 103, 108])
            >>> returns = preprocessor.calculate_log_returns(prices)
        """

        log_returns = np.log(prices / prices.shift(1))
        logger.info(f"Calculated log returns: {len(log_returns)} values")

        return log_returns

    def prepare_returns_data(
        self,
        data: pd.DataFrame,
        price_column: str = 'Close',
        return_type: str = 'log'
    ) -> pd.DataFrame:
        """
        Prepare a complete returns dataset from price data

        Args:
            data: DataFrame with price data (from DataCollector)
            price_column: Column name to use for returns ('Close', 'Adj Close', etc.)
            return_type: 'log' or 'simple'

        Returns:
            DataFrame with prices and returns

        Example:
            >>> from src.data.data_collector import DataCollector
            >>> collector = DataCollector()
            >>> data = collector.fetch_stock_data("AAPL", period="1y")
            >>> preprocessor = DataPreprocessor()
            >>> returns_data = preprocessor.prepare_returns_data(data)
        """

        logger.info(f"Preparing returns data from '{price_column}' column...")

        # Create output DataFrame
        result = pd.DataFrame()

        # Add price column
        result['Price'] = data[price_column]

        # Calculate returns
        if return_type == 'log':
            result['Returns'] = self.calculate_log_returns(data[price_column])
        elif return_type == 'simple':
            result['Returns'] = self.calculate_simple_returns(data[price_column])
        else:
            raise ValueError(f"Invalid return_type: {return_type}. Use 'log' or 'simple'")

        # Add volume if available
        if 'Volume' in data.columns:
            result['Volume'] = data['Volume']

        # Remove first row (NaN return)
        result = result.dropna(subset=['Returns'])

        logger.info(f"Prepared {len(result)} returns observations")
        logger.info(f"Date range: {result.index[0]} to {result.index[-1]}")

        return result

    def detect_outliers(
        self,
        returns: pd.Series,
        z_threshold: float = 3.0
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Detect outliers using Z-score method

        An outlier is defined as a return more than z_threshold standard
        deviations away from the mean.

        Args:
            returns: Series of returns
            z_threshold: Number of standard deviations (default: 3.0)

        Returns:
            Tuple of (outlier_mask, z_scores)
            - outlier_mask: Boolean series (True = outlier)
            - z_scores: Z-score for each return

        Example:
            >>> outliers, z_scores = preprocessor.detect_outliers(returns, z_threshold=3.0)
            >>> print(f"Found {outliers.sum()} outliers")
        """

        # Calculate Z-scores
        mean = returns.mean()
        std = returns.std()
        z_scores = (returns - mean) / std

        # Identify outliers
        outlier_mask = np.abs(z_scores) > z_threshold

        num_outliers = outlier_mask.sum()
        pct_outliers = (num_outliers / len(returns)) * 100

        logger.info(f"Detected {num_outliers} outliers ({pct_outliers:.2f}%)")
        logger.info(f"Z-threshold: {z_threshold}")

        return outlier_mask, z_scores

    def remove_outliers(
        self,
        data: pd.DataFrame,
        returns_column: str = 'Returns',
        z_threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        Remove outliers from dataset

        Args:
            data: DataFrame with returns
            returns_column: Name of returns column
            z_threshold: Z-score threshold

        Returns:
            DataFrame with outliers removed

        Example:
            >>> clean_data = preprocessor.remove_outliers(returns_data, z_threshold=3.5)
        """

        returns = data[returns_column]
        outlier_mask, z_scores = self.detect_outliers(returns, z_threshold)

        # Keep only non-outliers
        clean_data = data[~outlier_mask].copy()

        removed = len(data) - len(clean_data)
        logger.info(f"Removed {removed} outliers")
        logger.info(f"Remaining observations: {len(clean_data)}")

        return clean_data

    def handle_missing_data(
        self,
        data: pd.DataFrame,
        method: str = 'drop'
    ) -> pd.DataFrame:
        """
        Handle missing (NaN) values in dataset

        Args:
            data: DataFrame with potential missing values
            method: How to handle missing data
                   - 'drop': Remove rows with NaN
                   - 'ffill': Forward fill (use previous value)
                   - 'interpolate': Linear interpolation

        Returns:
            DataFrame with missing data handled

        Example:
            >>> clean_data = preprocessor.handle_missing_data(data, method='drop')
        """

        initial_rows = len(data)

        if method == 'drop':
            clean_data = data.dropna()
        elif method == 'ffill':
            clean_data = data.fillna(method='ffill')
        elif method == 'interpolate':
            clean_data = data.interpolate(method='linear')
        else:
            raise ValueError(f"Invalid method: {method}")

        removed = initial_rows - len(clean_data)

        if removed > 0:
            logger.info(f"Handled {removed} missing values using '{method}' method")

        return clean_data

    def get_summary_statistics(self, returns: pd.Series) -> dict:
        """
        Calculate comprehensive summary statistics for returns

        Args:
            returns: Series of returns

        Returns:
            Dictionary with statistical measures

        Example:
            >>> stats = preprocessor.get_summary_statistics(returns_data['Returns'])
            >>> print(f"Mean: {stats['mean']:.6f}")
            >>> print(f"Volatility: {stats['std']:.6f}")
        """

        stats_dict = {
            'count': len(returns),
            'mean': returns.mean(),
            'std': returns.std(),  # Volatility
            'min': returns.min(),
            'max': returns.max(),
            'median': returns.median(),
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis(),
            'percentile_1': returns.quantile(0.01),
            'percentile_5': returns.quantile(0.05),
            'percentile_95': returns.quantile(0.95),
            'percentile_99': returns.quantile(0.99)
        }

        return stats_dict

    def print_summary_statistics(self, returns: pd.Series, ticker: str = ""):
        """
        Print formatted summary statistics

        Args:
            returns: Series of returns
            ticker: Optional ticker symbol for display

        Example:
            >>> preprocessor.print_summary_statistics(returns_data['Returns'], ticker="AAPL")
        """

        stats = self.get_summary_statistics(returns)

        print("\n" + "="*60)
        print(f"SUMMARY STATISTICS{' - ' + ticker if ticker else ''}")
        print("="*60)
        print(f"Observations:        {stats['count']}")
        print(f"Mean (daily):        {stats['mean']:.6f} ({stats['mean']*100:.4f}%)")
        print(f"Std Dev (volatility):{stats['std']:.6f} ({stats['std']*100:.4f}%)")
        print(f"Min:                 {stats['min']:.6f} ({stats['min']*100:.4f}%)")
        print(f"Max:                 {stats['max']:.6f} ({stats['max']*100:.4f}%)")
        print(f"Median:              {stats['median']:.6f}")
        print(f"Skewness:            {stats['skewness']:.4f}")
        print(f"Kurtosis:            {stats['kurtosis']:.4f}")
        print(f"\nPercentiles:")
        print(f"  1%:                {stats['percentile_1']:.6f} ({stats['percentile_1']*100:.4f}%)")
        print(f"  5%:                {stats['percentile_5']:.6f} ({stats['percentile_5']*100:.4f}%)")
        print(f"  95%:               {stats['percentile_95']:.6f} ({stats['percentile_95']*100:.4f}%)")
        print(f"  99%:               {stats['percentile_99']:.6f} ({stats['percentile_99']*100:.4f}%)")
        print("="*60)

        # Interpret skewness
        if stats['skewness'] < -0.5:
            print("⚠️  Negative skewness: More extreme losses than gains")
        elif stats['skewness'] > 0.5:
            print("📈 Positive skewness: More extreme gains than losses")
        else:
            print("✅ Approximately symmetric distribution")

        # Interpret kurtosis
        if stats['kurtosis'] > 3:
            print("⚠️  High kurtosis: Fat tails (more extreme events)")
        elif stats['kurtosis'] < 0:
            print("📊 Low kurtosis: Thin tails (fewer extreme events)")
        else:
            print("✅ Normal kurtosis")

        print("="*60 + "\n")

    def annualize_statistics(self, daily_mean: float, daily_std: float, trading_days: int = 252) -> dict:
        """
        Convert daily statistics to annualized values

        Args:
            daily_mean: Daily mean return
            daily_std: Daily standard deviation (volatility)
            trading_days: Trading days per year (default: 252)

        Returns:
            Dictionary with annualized statistics

        Example:
            >>> annual = preprocessor.annualize_statistics(0.001, 0.02)
            >>> print(f"Annual return: {annual['annual_return']*100:.2f}%")
        """

        annual_return = daily_mean * trading_days
        annual_volatility = daily_std * np.sqrt(trading_days)

        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'annual_return_pct': annual_return * 100,
            'annual_volatility_pct': annual_volatility * 100
        }


# Test the preprocessor
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector

    print("="*60)
    print("Testing DataPreprocessor")
    print("="*60)

    # Fetch data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    # Initialize preprocessor
    preprocessor = DataPreprocessor()

    # Test 1: Prepare returns data
    print("\n📊 Test 1: Preparing returns data...")
    returns_data = preprocessor.prepare_returns_data(data)
    print(f"Shape: {returns_data.shape}")
    print(f"\nFirst 5 rows:")
    print(returns_data.head())

    # Test 2: Summary statistics
    print("\n📈 Test 2: Summary statistics...")
    preprocessor.print_summary_statistics(returns_data['Returns'], ticker="AAPL")

    # Test 3: Outlier detection
    print("\n🔍 Test 3: Detecting outliers...")
    outliers, z_scores = preprocessor.detect_outliers(returns_data['Returns'], z_threshold=3.0)
    print(f"Number of outliers: {outliers.sum()}")
    if outliers.sum() > 0:
        print(f"Outlier dates:")
        print(returns_data[outliers][['Price', 'Returns']])

    # Test 4: Remove outliers
    print("\n🧹 Test 4: Removing outliers...")
    clean_data = preprocessor.remove_outliers(returns_data, z_threshold=3.0)
    print(f"Original rows: {len(returns_data)}")
    print(f"Clean rows: {len(clean_data)}")

    # Test 5: Annualized statistics
    print("\n📅 Test 5: Annualized statistics...")
    daily_stats = preprocessor.get_summary_statistics(returns_data['Returns'])
    annual_stats = preprocessor.annualize_statistics(
        daily_stats['mean'],
        daily_stats['std']
    )
    print(f"Daily mean return: {daily_stats['mean']*100:.4f}%")
    print(f"Annual return: {annual_stats['annual_return_pct']:.2f}%")
    print(f"Daily volatility: {daily_stats['std']*100:.4f}%")
    print(f"Annual volatility: {annual_stats['annual_volatility_pct']:.2f}%")

    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)
```

---

## 🧪 Step 3: Test Your Preprocessor (20 minutes)

### 3.1 Run the Test

```bash
cd /home/user/market-risk-var-system
python src/data/preprocessor.py
```

### 3.2 Expected Output

```
============================================================
Testing DataPreprocessor
============================================================

📊 Test 1: Preparing returns data...
INFO:__main__:Preparing returns data from 'Close' column...
INFO:__main__:Calculated log returns: 504 values
INFO:__main__:Prepared 503 returns observations
Shape: (503, 3)

First 5 rows:
                Price   Returns     Volume
Date
2022-01-04  182.01   -0.0033   99310400
2022-01-05  179.58   -0.0134   94537600
2022-01-06  172.00   -0.0426   96904000
...

📈 Test 2: Summary statistics...
============================================================
SUMMARY STATISTICS - AAPL
============================================================
Observations:        503
Mean (daily):        0.000812 (0.0812%)
Std Dev (volatility):0.020145 (2.0145%)
Min:                 -0.052899 (-5.2899%)
Max:                 0.088038 (8.8038%)
Skewness:            0.2341
Kurtosis:            3.8912
⚠️  High kurtosis: Fat tails (more extreme events)
============================================================

🔍 Test 3: Detecting outliers...
INFO:__main__:Detected 7 outliers (1.39%)

📅 Test 5: Annualized statistics...
Daily mean return: 0.0812%
Annual return: 20.46%
Daily volatility: 2.0145%
Annual volatility: 31.97%
```

---

## 📊 Step 4: Understanding the Statistics (15 minutes)

### What Do These Numbers Mean?

#### Mean (Average Return)
- **Daily**: 0.0812% per day
- **Annual**: 20.46% per year
- **Interpretation**: On average, AAPL goes up 0.08% per day

#### Standard Deviation (Volatility)
- **Daily**: 2.01% per day
- **Annual**: 32% per year
- **Interpretation**: Typical daily price movement is ±2%

#### Skewness (0.2341)
- **Positive** = More extreme gains than losses
- **Negative** = More extreme losses than gains
- **Zero** = Symmetric distribution
- **AAPL**: Slightly positive (small asymmetry)

#### Kurtosis (3.89)
- **Normal distribution**: Kurtosis = 3
- **High kurtosis (>3)**: "Fat tails" - more extreme events
- **AAPL**: 3.89 means more crashes/spikes than normal distribution predicts

#### Percentiles
- **1st percentile**: -4.36% (worst 1% of days)
- **99th percentile**: +4.50% (best 1% of days)

---

## 🔍 Step 5: Experiments (15 minutes)

### Experiment 1: Compare Simple vs Log Returns

```python
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor

collector = DataCollector()
data = collector.fetch_stock_data("AAPL", period="1y")

preprocessor = DataPreprocessor()

# Simple returns
simple_returns = preprocessor.prepare_returns_data(data, return_type='simple')
simple_stats = preprocessor.get_summary_statistics(simple_returns['Returns'])

# Log returns
log_returns = preprocessor.prepare_returns_data(data, return_type='log')
log_stats = preprocessor.get_summary_statistics(log_returns['Returns'])

print(f"Simple returns mean: {simple_stats['mean']:.6f}")
print(f"Log returns mean:    {log_stats['mean']:.6f}")
print(f"Difference:          {abs(simple_stats['mean'] - log_stats['mean']):.6f}")
```

**You'll notice**: They're very similar! Log returns are slightly smaller.

### Experiment 2: Effect of Outlier Removal

```python
# With outliers
stats_with_outliers = preprocessor.get_summary_statistics(returns_data['Returns'])

# Without outliers
clean_data = preprocessor.remove_outliers(returns_data, z_threshold=3.0)
stats_without_outliers = preprocessor.get_summary_statistics(clean_data['Returns'])

print("With outliers:")
print(f"  Std Dev: {stats_with_outliers['std']:.6f}")
print(f"  Min: {stats_with_outliers['min']:.6f}")
print(f"  Max: {stats_with_outliers['max']:.6f}")

print("\nWithout outliers:")
print(f"  Std Dev: {stats_without_outliers['std']:.6f}")
print(f"  Min: {stats_without_outliers['min']:.6f}")
print(f"  Max: {stats_without_outliers['max']:.6f}")
```

**You'll notice**: Volatility (std dev) decreases when you remove outliers.

### Experiment 3: Compare Different Stocks

```python
tickers = ['AAPL', 'MSFT', 'TSLA']  # Tech stocks

for ticker in tickers:
    data = collector.fetch_stock_data(ticker, period="1y")
    returns_data = preprocessor.prepare_returns_data(data)
    preprocessor.print_summary_statistics(returns_data['Returns'], ticker=ticker)
```

**You'll notice**: Tesla (TSLA) has much higher volatility than Apple or Microsoft!

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Learned the difference between simple and log returns
✅ Built a complete data preprocessing pipeline
✅ Calculated returns from price data
✅ Detected and removed outliers using Z-scores
✅ Computed comprehensive summary statistics
✅ Understood volatility, skewness, and kurtosis
✅ Annualized daily statistics to yearly values

---

## 🐛 Troubleshooting

### Issue 1: "Returns are all NaN"

**Solution**: Make sure you're using the 'Close' column:
```python
returns_data = preprocessor.prepare_returns_data(data, price_column='Close')
```

### Issue 2: "Skewness or Kurtosis is NaN"

**Cause**: Not enough data points

**Solution**: Fetch more data:
```python
data = collector.fetch_stock_data("AAPL", period="2y")  # Use 2 years
```

### Issue 3: "Too many outliers detected"

**Solution**: Increase z_threshold:
```python
outliers, z = preprocessor.detect_outliers(returns, z_threshold=4.0)  # More lenient
```

---

## 📚 Key Formulas Reference

### Simple Return
```
R_t = (P_t - P_{t-1}) / P_{t-1}
```

### Log Return
```
r_t = ln(P_t / P_{t-1})
```

### Z-Score (Outlier Detection)
```
Z = (x - μ) / σ
where:
  x = return value
  μ = mean return
  σ = standard deviation
```

### Annualization
```
Annual Return = Daily Return × 252
Annual Volatility = Daily Volatility × √252
```

---

## 🎯 Homework / Practice

### Exercise 1: Find the Most Volatile Stock

```python
tickers = ['AAPL', 'GOOGL', 'TSLA', 'NVDA', 'AMD']
volatilities = {}

for ticker in tickers:
    data = collector.fetch_stock_data(ticker, period="1y")
    returns_data = preprocessor.prepare_returns_data(data)
    stats = preprocessor.get_summary_statistics(returns_data['Returns'])
    volatilities[ticker] = stats['std']

# Find most volatile
most_volatile = max(volatilities, key=volatilities.get)
print(f"Most volatile stock: {most_volatile}")
print(f"Daily volatility: {volatilities[most_volatile]*100:.2f}%")
```

### Exercise 2: Detect Market Crash Days

```python
data = collector.fetch_stock_data("SPY", period="5y")  # S&P 500 ETF
returns_data = preprocessor.prepare_returns_data(data)

# Find days with returns < -3%
crash_days = returns_data[returns_data['Returns'] < -0.03]
print(f"Found {len(crash_days)} crash days (< -3%)")
print(crash_days[['Price', 'Returns']].sort_values('Returns'))
```

### Exercise 3: Calculate Sharpe Ratio (Preview of Day 015)

```python
stats = preprocessor.get_summary_statistics(returns_data['Returns'])
risk_free_rate = 0.02 / 252  # 2% annual risk-free rate

sharpe_ratio = (stats['mean'] - risk_free_rate) / stats['std']
print(f"Daily Sharpe Ratio: {sharpe_ratio:.4f}")
print(f"Annualized Sharpe Ratio: {sharpe_ratio * np.sqrt(252):.4f}")
```

---

## 🔜 Coming Up in Day 003

Tomorrow you'll learn:
- **Historical VaR**: Calculate Value at Risk using historical data
- **Quantiles**: Understanding percentiles for risk measurement
- **Confidence Levels**: 90%, 95%, 99% VaR
- **Expected Shortfall (CVaR)**: Average loss beyond VaR

**File you'll create**: `src/models/var_calculator.py` (Part 1)

---

**Great job! You've mastered data preprocessing! 🎉**
