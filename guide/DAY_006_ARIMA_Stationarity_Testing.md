# Day 006: ARIMA Model - Part 1 (Stationarity Testing)

**Duration**: 2 hours
**Difficulty**: Intermediate
**Prerequisites**: Completed Day 001-005

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Understand what time series stationarity means
- Learn why stationarity is important for forecasting
- Implement the Augmented Dickey-Fuller (ADF) test
- Understand differencing for making series stationary
- Interpret ACF and PACF plots
- Begin building an ARIMA forecasting module

---

## 🎯 Learning Objectives

### Financial Concepts:
- **Time Series**: Sequential data points indexed by time
- **Stationarity**: Statistical properties don't change over time
- **Random Walk**: Non-stationary process common in stock prices
- **Differencing**: Transform non-stationary → stationary
- **Mean Reversion**: Tendency to return to average value

### Statistical Concepts:
- **Augmented Dickey-Fuller (ADF) Test**: Test for unit root
- **ACF (Autocorrelation Function)**: Correlation with lagged values
- **PACF (Partial Autocorrelation Function)**: Direct correlation with specific lag
- **p-value**: Statistical significance threshold

---

## 💡 Understanding Stationarity (20 minutes)

### What is Stationarity?

**Stationary Series**: Statistical properties (mean, variance) remain constant over time

**Example of Stationary Data:**
```
Daily returns: [-0.5%, +0.8%, -0.3%, +1.2%, -0.7%, ...]

Mean: ~0% (constant)
Variance: ~2% (constant)
No long-term trend
```

**Example of Non-Stationary Data:**
```
Stock prices: [$100, $102, $105, $103, $108, $112, ...]

Mean: Changes over time (upward trend)
Variance: May increase over time
Clear trend present
```

### Visual Comparison

```
Stationary (Returns):
  2%  |     *     *
  1%  |  *     *     *
  0%  |___*___*___*___*___
 -1%  |     *     *
 -2%  |  *     *
      Time →

Non-Stationary (Prices):
$150 |                    *
$140 |                *
$130 |            *
$120 |        *
$110 |    *
$100 |*
      Time →
```

---

## 🔍 Why Stationarity Matters

### For ARIMA Models:

**ARIMA assumes stationarity** to make reliable forecasts.

**Problem with Non-Stationary Data:**
- Spurious correlations
- Unreliable forecasts
- Model parameters don't make sense
- Statistical tests fail

**Solution:**
1. Test for stationarity (ADF test)
2. If non-stationary → Apply differencing
3. If stationary → Proceed with modeling

---

## 📊 The Augmented Dickey-Fuller (ADF) Test

### What Does It Test?

**Null Hypothesis (H₀)**: Series has a unit root (non-stationary)
**Alternative (H₁)**: Series is stationary

### Interpretation:

| p-value | Conclusion | Action |
|---------|------------|--------|
| **< 0.05** | Reject H₀ → **Stationary** ✅ | Proceed with modeling |
| **≥ 0.05** | Fail to reject H₀ → **Non-stationary** ❌ | Apply differencing |

### Example:

```python
# Stock prices
ADF statistic: -1.234
p-value: 0.65 (> 0.05)
→ Non-stationary (as expected!)

# Stock returns
ADF statistic: -12.456
p-value: 0.000001 (< 0.05)
→ Stationary ✓
```

---

## 💻 Step 1: Install statsmodels (5 minutes)

```bash
pip install statsmodels==0.14.0
```

**What statsmodels does:**
- Time series analysis (ARIMA, SARIMAX, VAR)
- Statistical tests (ADF, KPSS, etc.)
- ACF/PACF calculations
- Forecasting tools

---

## 💻 Step 2: Build Stationarity Testing Module (50 minutes)

### 2.1 Create `src/models/arima_model.py`

```python
"""
ARIMA Model Module for Market Risk VaR System
Time series forecasting using ARIMA
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt
import logging
from typing import Tuple, Dict, Optional
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ARIMAForecaster:
    """
    ARIMA (AutoRegressive Integrated Moving Average) forecaster

    ARIMA is used to forecast future returns based on historical patterns.

    Components:
    - AR (AutoRegressive): Uses past values
    - I (Integrated): Differencing to achieve stationarity
    - MA (Moving Average): Uses past forecast errors
    """

    def __init__(self, order: Tuple[int, int, int] = (1, 0, 1)):
        """
        Initialize ARIMA forecaster

        Args:
            order: (p, d, q) tuple
                p = AR order (number of lagged observations)
                d = Degree of differencing
                q = MA order (size of moving average window)

        Examples:
            >>> arima = ARIMAForecaster(order=(1, 0, 1))  # ARIMA(1,0,1)
            >>> arima = ARIMAForecaster(order=(2, 1, 2))  # ARIMA(2,1,2)
        """
        self.order = order
        self.p, self.d, self.q = order
        self.model = None
        self.fitted_model = None
        self.results = None

        logger.info(f"ARIMA Forecaster initialized with order {order}")

    def test_stationarity(
        self,
        series: pd.Series,
        significance_level: float = 0.05
    ) -> Dict[str, any]:
        """
        Test if a time series is stationary using Augmented Dickey-Fuller test

        Args:
            series: Time series to test
            significance_level: Threshold for p-value (default: 0.05)

        Returns:
            Dictionary with test results and interpretation

        Example:
            >>> result = arima.test_stationarity(returns)
            >>> print(f"Is stationary: {result['is_stationary']}")
            >>> print(f"p-value: {result['p_value']:.6f}")
        """

        logger.info("Running Augmented Dickey-Fuller (ADF) test...")

        # Run ADF test
        adf_result = adfuller(series.dropna(), autolag='AIC')

        # Extract results
        adf_statistic = adf_result[0]
        p_value = adf_result[1]
        n_lags = adf_result[2]
        n_obs = adf_result[3]
        critical_values = adf_result[4]

        # Determine if stationary
        is_stationary = p_value < significance_level

        result = {
            'adf_statistic': adf_statistic,
            'p_value': p_value,
            'n_lags_used': n_lags,
            'n_observations': n_obs,
            'critical_values': critical_values,
            'is_stationary': is_stationary,
            'significance_level': significance_level
        }

        # Log results
        logger.info(f"ADF Statistic: {adf_statistic:.6f}")
        logger.info(f"p-value: {p_value:.6f}")
        logger.info(f"Critical Values:")
        for key, value in critical_values.items():
            logger.info(f"  {key}: {value:.4f}")

        if is_stationary:
            logger.info(f"✅ Series IS stationary (p-value < {significance_level})")
        else:
            logger.info(f"❌ Series is NOT stationary (p-value >= {significance_level})")
            logger.info("   → Consider differencing or transformation")

        return result

    def difference_series(
        self,
        series: pd.Series,
        order: int = 1
    ) -> pd.Series:
        """
        Apply differencing to make series stationary

        Differencing: X'(t) = X(t) - X(t-1)

        Args:
            series: Original time series
            order: Order of differencing (1 = first difference, 2 = second difference)

        Returns:
            Differenced series

        Example:
            >>> # Original: [100, 102, 105, 103]
            >>> diff = arima.difference_series(prices, order=1)
            >>> # Result: [2, 3, -2]
        """

        logger.info(f"Applying differencing of order {order}...")

        differenced = series.copy()

        for i in range(order):
            differenced = differenced.diff().dropna()
            logger.info(f"  After {i+1} differencing: {len(differenced)} observations")

        return differenced

    def calculate_acf_pacf(
        self,
        series: pd.Series,
        nlags: int = 40
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate ACF and PACF

        ACF (Autocorrelation Function):
        - Measures correlation between series and its lagged values
        - Helps identify MA (q) order

        PACF (Partial Autocorrelation Function):
        - Measures direct correlation with specific lag
        - Helps identify AR (p) order

        Args:
            series: Time series
            nlags: Number of lags to calculate

        Returns:
            Tuple of (acf_values, pacf_values)

        Example:
            >>> acf_vals, pacf_vals = arima.calculate_acf_pacf(returns, nlags=20)
            >>> print(f"ACF at lag 1: {acf_vals[1]:.4f}")
        """

        logger.info(f"Calculating ACF and PACF for {nlags} lags...")

        series_clean = series.dropna()

        # Calculate ACF
        acf_values = acf(series_clean, nlags=nlags, fft=False)

        # Calculate PACF
        pacf_values = pacf(series_clean, nlags=nlags, method='ywm')

        logger.info(f"ACF values calculated: {len(acf_values)} lags")
        logger.info(f"PACF values calculated: {len(pacf_values)} lags")

        return acf_values, pacf_values

    def plot_acf_pacf(
        self,
        series: pd.Series,
        nlags: int = 40,
        save_path: Optional[str] = None
    ):
        """
        Plot ACF and PACF for visual inspection

        Args:
            series: Time series
            nlags: Number of lags to plot
            save_path: Optional path to save figure

        Example:
            >>> arima.plot_acf_pacf(returns, nlags=20, save_path='acf_pacf.png')
        """

        logger.info("Plotting ACF and PACF...")

        series_clean = series.dropna()

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Plot ACF
        plot_acf(series_clean, lags=nlags, ax=axes[0])
        axes[0].set_title('Autocorrelation Function (ACF)', fontsize=14)
        axes[0].set_xlabel('Lag')
        axes[0].set_ylabel('ACF')
        axes[0].grid(True, alpha=0.3)

        # Plot PACF
        plot_pacf(series_clean, lags=nlags, ax=axes[1], method='ywm')
        axes[1].set_title('Partial Autocorrelation Function (PACF)', fontsize=14)
        axes[1].set_xlabel('Lag')
        axes[1].set_ylabel('PACF')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plot saved to: {save_path}")
        else:
            plt.show()

        plt.close()

    def print_stationarity_report(
        self,
        series: pd.Series,
        series_name: str = "Series"
    ):
        """
        Print comprehensive stationarity report

        Args:
            series: Time series to analyze
            series_name: Name for display

        Example:
            >>> arima.print_stationarity_report(returns, series_name="AAPL Returns")
        """

        print("\n" + "="*70)
        print(f"STATIONARITY REPORT: {series_name}")
        print("="*70)

        # Basic statistics
        print(f"\n📊 Basic Statistics:")
        print(f"  Observations: {len(series)}")
        print(f"  Mean:         {series.mean():.6f}")
        print(f"  Std Dev:      {series.std():.6f}")
        print(f"  Min:          {series.min():.6f}")
        print(f"  Max:          {series.max():.6f}")

        # ADF test
        print(f"\n🔍 Augmented Dickey-Fuller Test:")
        adf_result = self.test_stationarity(series)

        print(f"  ADF Statistic:  {adf_result['adf_statistic']:.6f}")
        print(f"  p-value:        {adf_result['p_value']:.6f}")
        print(f"  Lags Used:      {adf_result['n_lags_used']}")
        print(f"\n  Critical Values:")
        for key, value in adf_result['critical_values'].items():
            print(f"    {key:>4s}: {value:.4f}")

        # Interpretation
        print(f"\n📖 Interpretation:")
        if adf_result['is_stationary']:
            print(f"  ✅ Series IS stationary")
            print(f"  ✅ p-value ({adf_result['p_value']:.6f}) < 0.05")
            print(f"  ✅ Can proceed with ARIMA modeling")
        else:
            print(f"  ❌ Series is NOT stationary")
            print(f"  ❌ p-value ({adf_result['p_value']:.6f}) >= 0.05")
            print(f"  ⚠️  Recommendation: Apply differencing (d=1) or transformation")

        # ACF/PACF summary
        print(f"\n📈 Autocorrelation Analysis:")
        acf_vals, pacf_vals = self.calculate_acf_pacf(series, nlags=10)

        print(f"  ACF at lag 1:  {acf_vals[1]:.4f}")
        print(f"  ACF at lag 5:  {acf_vals[5]:.4f}")
        print(f"  PACF at lag 1: {pacf_vals[1]:.4f}")
        print(f"  PACF at lag 5: {pacf_vals[5]:.4f}")

        print("="*70 + "\n")


# Test the module
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor

    print("="*70)
    print("Testing ARIMA Forecaster - Stationarity Testing")
    print("="*70)

    # Fetch data
    print("\n📥 Fetching Apple (AAPL) data...")
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()
    prices = returns_data['Price']

    # Initialize ARIMA forecaster
    arima = ARIMAForecaster()

    # Test 1: Stationarity of prices (should be non-stationary)
    print("\n" + "="*70)
    print("TEST 1: Stationarity of Stock Prices")
    print("="*70)
    arima.print_stationarity_report(prices, series_name="AAPL Prices")

    # Test 2: Stationarity of returns (should be stationary)
    print("\n" + "="*70)
    print("TEST 2: Stationarity of Returns")
    print("="*70)
    arima.print_stationarity_report(returns, series_name="AAPL Returns")

    # Test 3: Differencing prices to make them stationary
    print("\n" + "="*70)
    print("TEST 3: Differencing Prices")
    print("="*70)

    diff_prices = arima.difference_series(prices, order=1)
    print(f"\nOriginal prices: {len(prices)} observations")
    print(f"Differenced:     {len(diff_prices)} observations")

    arima.print_stationarity_report(diff_prices, series_name="Differenced Prices")

    # Test 4: ACF and PACF visualization
    print("\n" + "="*70)
    print("TEST 4: ACF/PACF Plots")
    print("="*70)

    print("\nGenerating ACF/PACF plots for returns...")
    arima.plot_acf_pacf(returns, nlags=30, save_path='arima_acf_pacf.png')

    # Test 5: Compare different stocks
    print("\n" + "="*70)
    print("TEST 5: Compare Stationarity Across Stocks")
    print("="*70)

    tickers = ['AAPL', 'MSFT', 'TSLA']
    results = []

    for ticker in tickers:
        data = collector.fetch_stock_data(ticker, period="1y")
        returns = preprocessor.prepare_returns_data(data)['Returns']
        adf_result = arima.test_stationarity(returns)

        results.append({
            'Ticker': ticker,
            'ADF_Statistic': adf_result['adf_statistic'],
            'p_value': adf_result['p_value'],
            'Is_Stationary': '✅' if adf_result['is_stationary'] else '❌'
        })

    print("\n" + pd.DataFrame(results).to_string(index=False))

    print("\n" + "="*70)
    print("✅ All tests completed!")
    print("="*70)
```

---

## 🧪 Step 3: Test Stationarity Module (20 minutes)

### 3.1 Run the Test

```bash
cd /home/user/market-risk-var-system
python src/models/arima_model.py
```

### 3.2 Expected Output

```
======================================================================
Testing ARIMA Forecaster - Stationarity Testing
======================================================================

======================================================================
TEST 1: Stationarity of Stock Prices
======================================================================

📊 Basic Statistics:
  Observations: 504
  Mean:         162.345678
  Std Dev:      24.567890
  Min:          125.010000
  Max:          196.450000

🔍 Augmented Dickey-Fuller Test:
  ADF Statistic:  -1.234567
  p-value:        0.654321
  Lags Used:      14

  Critical Values:
     1%: -3.4432
     5%: -2.8671
    10%: -2.5698

📖 Interpretation:
  ❌ Series is NOT stationary
  ❌ p-value (0.654321) >= 0.05
  ⚠️  Recommendation: Apply differencing (d=1) or transformation

======================================================================
TEST 2: Stationarity of Returns
======================================================================

📊 Basic Statistics:
  Observations: 503
  Mean:         0.000812
  Std Dev:      0.020145
  Min:          -0.052899
  Max:          0.088038

🔍 Augmented Dickey-Fuller Test:
  ADF Statistic:  -18.234567
  p-value:        0.000000
  Lags Used:      0

📖 Interpretation:
  ✅ Series IS stationary
  ✅ p-value (0.000000) < 0.05
  ✅ Can proceed with ARIMA modeling

======================================================================
TEST 5: Compare Stationarity Across Stocks
======================================================================

Ticker  ADF_Statistic   p_value  Is_Stationary
  AAPL      -18.234567  0.000000             ✅
  MSFT      -17.891234  0.000000             ✅
  TSLA      -16.543210  0.000000             ✅
```

---

## 📊 Step 4: Understanding ACF and PACF (15 minutes)

### What Do ACF and PACF Tell Us?

**ACF (Autocorrelation Function):**
- Measures correlation with ALL previous lags
- Helps determine **q** (MA order)

**PACF (Partial Autocorrelation Function):**
- Measures DIRECT correlation with specific lag
- Helps determine **p** (AR order)

### Reading ACF/PACF Plots:

```
ACF Plot:
 1.0 |█
 0.8 |█
 0.6 |█
 0.4 |▌
 0.2 |▌ ▌ ▌
 0.0 |__|__|__|__|__  ← If drops quickly: use low q (MA order)
    0  1  2  3  4  Lag

PACF Plot:
 1.0 |█
 0.8 |▌
 0.6 |
 0.4 |
 0.2 |  ▌
 0.0 |__|__|__|__|__  ← If drops after lag 1: use p=1 (AR order)
    0  1  2  3  4  Lag
```

### Rule of Thumb:

| Pattern | Suggested Order |
|---------|----------------|
| **ACF cuts off after lag q** | MA(q) model |
| **PACF cuts off after lag p** | AR(p) model |
| **Both decay slowly** | ARIMA(p,d,q) needed |
| **Returns (stationary)** | Usually ARIMA(1,0,1) or ARIMA(2,0,2) |

---

## 🔍 Step 5: Experiments (15 minutes)

### Experiment 1: Test Different Differencing Orders

```python
# Test how many times we need to difference prices
for d in [0, 1, 2]:
    if d == 0:
        series = prices
    else:
        series = arima.difference_series(prices, order=d)

    result = arima.test_stationarity(series)
    print(f"d={d}: p-value = {result['p_value']:.6f}, Stationary: {result['is_stationary']}")
```

**Expected:**
- d=0: Not stationary (prices)
- d=1: Stationary (returns)
- d=2: Still stationary (over-differenced)

### Experiment 2: ACF of Different Assets

```python
assets = [
    ('AAPL', 'Tech Stock'),
    ('JNJ', 'Defensive Stock'),
    ('GLD', 'Gold ETF'),
    ('SPY', 'S&P 500 ETF')
]

for ticker, description in assets:
    data = collector.fetch_stock_data(ticker, period="1y")
    returns = preprocessor.prepare_returns_data(data)['Returns']

    acf_vals, _ = arima.calculate_acf_pacf(returns, nlags=5)
    print(f"{ticker:4s} ({description:15s}): ACF[1]={acf_vals[1]:.4f}")
```

### Experiment 3: Volatility Clustering Detection

```python
# Check if squared returns show autocorrelation (= volatility clustering)
returns_squared = returns ** 2

print("Original Returns:")
arima.print_stationarity_report(returns, "Returns")

print("\nSquared Returns:")
arima.print_stationarity_report(returns_squared, "Squared Returns")

acf_sq, _ = arima.calculate_acf_pacf(returns_squared, nlags=10)
if acf_sq[1] > 0.1:
    print("⚠️ High ACF in squared returns → Volatility clustering present")
    print("   → Consider GARCH model (coming in Day 008)")
```

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Understood time series stationarity
✅ Implemented the Augmented Dickey-Fuller (ADF) test
✅ Learned to interpret p-values for stationarity
✅ Applied differencing to make series stationary
✅ Calculated ACF and PACF
✅ Generated ACF/PACF plots
✅ Understood how to select ARIMA orders (p, d, q)
✅ Built the foundation for ARIMA forecasting

---

## 🐛 Troubleshooting

### Issue 1: "ValueError: x is constant"

**Cause**: Your series has no variation

**Solution**: Check that you're using returns, not a constant value

### Issue 2: ACF/PACF plots don't show

**Cause**: matplotlib backend issue

**Solution**:
```python
import matplotlib
matplotlib.use('Agg')  # Use file backend
arima.plot_acf_pacf(returns, save_path='plot.png')
```

### Issue 3: ADF test says returns are non-stationary

**Possible causes:**
- Very small sample size
- Extreme outliers
- Structural breaks

**Solution**: Remove outliers or use longer time period

---

## 📚 Key Formulas Reference

### ADF Test Statistic
```
Δy_t = α + βt + γy_{t-1} + δ₁Δy_{t-1} + ... + δₚΔy_{t-p} + ε_t

Test: Is γ = 0? (unit root)

If γ = 0 → Non-stationary
If γ < 0 → Stationary
```

### First Difference
```
Δy_t = y_t - y_{t-1}

Example:
Prices: [100, 102, 105, 103]
First diff: [2, 3, -2]  (these are simple returns!)
```

### ACF at Lag k
```
ρ_k = Corr(y_t, y_{t-k})

Measures correlation k periods apart
```

---

## 🎯 Homework / Practice

### Exercise 1: Test Your Own Stock

```python
# Pick a stock you're interested in
# Test stationarity of:
# 1. Prices
# 2. Returns
# 3. Log returns
# 4. Absolute returns
# Which are stationary?
```

### Exercise 2: Find Optimal Differencing Order

```python
def find_optimal_differencing(series, max_d=3):
    """
    Find minimum differencing order to achieve stationarity
    """
    # Your code here
    pass
```

### Exercise 3: Seasonal Stationarity

```python
# For daily data, test if there's weekly seasonality
# Hint: Check ACF at lag 5 (weekly)
# If significant → might need seasonal ARIMA
```

---

## 🔜 Coming Up in Day 007

Tomorrow you'll learn:
- **ARIMA Model Fitting**: Estimate (p, d, q) parameters
- **Order Selection**: Auto-optimization using AIC/BIC
- **Forecasting**: Multi-step ahead forecasts
- **Confidence Intervals**: Uncertainty in predictions
- **Model Diagnostics**: Residual analysis

**File you'll update**: `src/models/arima_model.py` (Part 2)

---

**Great work! You've mastered stationarity testing! 📈**
