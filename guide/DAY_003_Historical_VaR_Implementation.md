# Day 003: Historical VaR Implementation

**Duration**: 2 hours
**Difficulty**: Intermediate
**Prerequisites**: Completed Day 001-002

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Understand what Value at Risk (VaR) is and why it's important
- Learn the Historical VaR method (non-parametric approach)
- Implement a VaR calculator class
- Calculate VaR at different confidence levels (90%, 95%, 99%)
- Compute Expected Shortfall (CVaR) - the average loss beyond VaR
- Apply VaR to real portfolio values

---

## 🎯 Learning Objectives

### Financial Concepts:
- **Value at Risk (VaR)**: Maximum expected loss over a time period
- **Confidence Level**: How certain we are about the VaR estimate
- **Quantiles**: Statistical percentiles for VaR calculation
- **Expected Shortfall (CVaR)**: Tail risk beyond VaR
- **Position Value**: Dollar amount invested

### Programming Concepts:
- Object-oriented programming (classes)
- Quantile calculations with pandas
- Type hints for better code documentation
- Logging for debugging

---

## 💡 Understanding Value at Risk (20 minutes)

### What is VaR?

**Value at Risk (VaR) answers this question:**

> "What is the maximum amount I could lose on my investment over the next day, with 95% confidence?"

### Real-World Example:

Imagine you have **$1,000,000 invested in Apple stock**.

**95% VaR of $16,000 means:**
- On 95 out of 100 days, you won't lose more than $16,000
- On 5 out of 100 days (about once per month), you could lose more than $16,000
- **It's not the worst-case scenario** - it's the "normal worst case"

### Why Do We Need VaR?

**For Banks & Financial Institutions:**
- Regulatory requirement (Basel III)
- Risk management and position sizing
- Capital allocation
- Limit setting for traders

**For Individual Investors:**
- Understand downside risk
- Portfolio diversification decisions
- Stress testing your portfolio

### VaR Formula (Conceptual)

```
VaR = Position Value × Quantile of Returns Distribution

Example:
Position Value = $1,000,000
95% Confidence → Use 5th percentile of returns
5th percentile return = -1.62%

VaR = $1,000,000 × 0.0162 = $16,200

Interpretation: "We are 95% confident we won't lose more than $16,200 tomorrow"
```

---

## 📊 Historical VaR Method

### How It Works:

1. **Collect Historical Returns** (e.g., 1 year = 252 trading days)
2. **Sort Returns** from worst to best
3. **Find the Percentile** (5th percentile for 95% confidence)
4. **Scale by Position Value**

### Example:

You have 100 days of returns, sorted:
```
Worst day:  -5.2%
Day 2:      -4.8%
Day 3:      -3.9%
Day 4:      -3.1%
Day 5:      -2.8%  ← 5th percentile (95% confidence)
Day 6:      -2.3%
...
Best day:   +8.1%
```

**95% VaR = $1,000,000 × 2.8% = $28,000**

### Advantages of Historical VaR:
✅ No assumptions about distribution (non-parametric)
✅ Easy to understand and calculate
✅ Captures fat tails and skewness
✅ Works for any asset class

### Disadvantages:
❌ Assumes future will be like the past
❌ Requires lots of historical data
❌ Can't predict unprecedented events
❌ Doesn't extrapolate beyond historical range

---

## 💻 Step 1: Build the VaR Calculator (60 minutes)

### 1.1 Create `src/models/var_calculator.py`

```python
"""
VaR Calculator Module for Market Risk VaR System
Implements Historical VaR method
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VaRCalculator:
    """
    Calculate Value at Risk using Historical method

    VaR represents the maximum expected loss over a given time period
    at a specified confidence level.
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize VaR calculator

        Args:
            confidence_level: Confidence level for VaR (e.g., 0.95 for 95%, 0.99 for 99%)

        Example:
            >>> var_calc = VaRCalculator(confidence_level=0.95)  # 95% VaR
            >>> var_calc = VaRCalculator(confidence_level=0.99)  # 99% VaR
        """
        if not 0 < confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")

        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level  # Significance level

        logger.info(f"VaR Calculator initialized with {confidence_level*100}% confidence level")

    def historical_var(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        window: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate Historical VaR using quantile method

        Args:
            returns: Historical returns (daily log returns)
            position_value: Portfolio value in currency (e.g., $1,000,000)
            window: Rolling window size (None = use all data)

        Returns:
            Dictionary containing:
                - VaR: Value at Risk in dollars
                - ES: Expected Shortfall in dollars
                - VaR_Percentage: VaR as percentage of position
                - ES_Percentage: ES as percentage of position
                - Method: "Historical"

        Example:
            >>> var_calc = VaRCalculator(confidence_level=0.95)
            >>> result = var_calc.historical_var(returns, position_value=1000000)
            >>> print(f"95% VaR: ${result['VaR']:,.2f}")
        """

        # Clean data (remove NaN values)
        returns_clean = returns.dropna()

        # Use only recent data if window is specified
        if window is not None:
            returns_clean = returns_clean.tail(window)
            logger.info(f"Using last {window} observations")

        if len(returns_clean) == 0:
            raise ValueError("No valid returns data provided")

        # Calculate VaR as the alpha-quantile of the loss distribution
        # Note: We use alpha (not 1-alpha) because we're looking at losses
        var_percentile = returns_clean.quantile(self.alpha)

        # Convert to positive dollar amount (loss)
        var = -var_percentile * position_value

        # Calculate Expected Shortfall (CVaR)
        # ES = Average of all returns worse than VaR
        es_returns = returns_clean[returns_clean <= var_percentile]

        if len(es_returns) > 0:
            es = -es_returns.mean() * position_value
            es_percentage = -es_returns.mean() * 100
        else:
            es = var
            es_percentage = -var_percentile * 100

        logger.info(f"Historical VaR ({self.confidence_level*100}%): ${var:,.2f}")
        logger.info(f"Expected Shortfall: ${es:,.2f}")
        logger.info(f"Based on {len(returns_clean)} observations")

        return {
            'VaR': var,
            'ES': es,
            'VaR_Percentage': -var_percentile * 100,
            'ES_Percentage': es_percentage,
            'Method': 'Historical',
            'Observations': len(returns_clean),
            'Worst_Return': returns_clean.min(),
            'Best_Return': returns_clean.max()
        }

    def compare_confidence_levels(
        self,
        returns: pd.Series,
        position_value: float = 1000000,
        confidence_levels: list = [0.90, 0.95, 0.99]
    ) -> pd.DataFrame:
        """
        Compare VaR at different confidence levels

        Args:
            returns: Historical returns
            position_value: Portfolio value
            confidence_levels: List of confidence levels to compare

        Returns:
            DataFrame with VaR at each confidence level

        Example:
            >>> var_calc = VaRCalculator()
            >>> comparison = var_calc.compare_confidence_levels(returns)
            >>> print(comparison)
        """

        results = []

        for cl in confidence_levels:
            # Create temporary VaR calculator with this confidence level
            temp_calc = VaRCalculator(confidence_level=cl)
            var_result = temp_calc.historical_var(returns, position_value)

            results.append({
                'Confidence_Level': f"{cl*100}%",
                'VaR_Amount': var_result['VaR'],
                'VaR_Percentage': var_result['VaR_Percentage'],
                'ES_Amount': var_result['ES'],
                'ES_Percentage': var_result['ES_Percentage']
            })

        df = pd.DataFrame(results)
        logger.info(f"Compared VaR across {len(confidence_levels)} confidence levels")

        return df

    def rolling_var(
        self,
        returns: pd.Series,
        window: int = 252,
        position_value: float = 1000000
    ) -> pd.Series:
        """
        Calculate rolling VaR over time

        Args:
            returns: Historical returns
            window: Rolling window size (e.g., 252 = 1 year)
            position_value: Portfolio value

        Returns:
            Series with rolling VaR values

        Example:
            >>> var_calc = VaRCalculator(confidence_level=0.95)
            >>> rolling = var_calc.rolling_var(returns, window=252)
            >>> rolling.plot(title="Rolling 1-Year VaR")
        """

        logger.info(f"Calculating rolling VaR with {window}-day window...")

        rolling_var_values = []
        rolling_dates = []

        for i in range(window, len(returns)):
            # Get window of returns
            window_returns = returns.iloc[i-window:i]

            # Calculate VaR for this window
            var_result = self.historical_var(window_returns, position_value, window=None)

            rolling_var_values.append(var_result['VaR'])
            rolling_dates.append(returns.index[i])

        rolling_var_series = pd.Series(rolling_var_values, index=rolling_dates)

        logger.info(f"Calculated {len(rolling_var_series)} rolling VaR values")

        return rolling_var_series


# Test the VaR calculator
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor

    print("="*70)
    print("Testing VaR Calculator - Historical Method")
    print("="*70)

    # Step 1: Fetch data
    print("\n📥 Step 1: Fetching Apple (AAPL) data...")
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    # Step 2: Prepare returns
    print("\n📊 Step 2: Preparing returns...")
    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()

    print(f"Total observations: {len(returns)}")
    print(f"Date range: {returns.index[0].date()} to {returns.index[-1].date()}")

    # Step 3: Calculate VaR at 95% confidence
    print("\n💰 Step 3: Calculating 95% VaR for $1,000,000 position...")
    var_calc = VaRCalculator(confidence_level=0.95)
    var_result = var_calc.historical_var(returns, position_value=1000000)

    print("\n" + "="*70)
    print("VaR RESULTS (95% Confidence)")
    print("="*70)
    print(f"Position Value:           ${1000000:,.2f}")
    print(f"VaR (95%):                ${var_result['VaR']:,.2f}")
    print(f"VaR Percentage:           {var_result['VaR_Percentage']:.2f}%")
    print(f"Expected Shortfall:       ${var_result['ES']:,.2f}")
    print(f"ES Percentage:            {var_result['ES_Percentage']:.2f}%")
    print(f"Observations Used:        {var_result['Observations']}")
    print("="*70)

    print("\n📖 Interpretation:")
    print(f"• We are 95% confident that losses won't exceed ${var_result['VaR']:,.2f} tomorrow")
    print(f"• On average, when VaR is breached, we expect to lose ${var_result['ES']:,.2f}")
    print(f"• This represents {var_result['VaR_Percentage']:.2f}% of the portfolio value")
    print(f"• Expected to breach VaR ~{252 * 0.05:.0f} days per year (5% of 252 trading days)")

    # Step 4: Compare confidence levels
    print("\n📊 Step 4: Comparing different confidence levels...")
    comparison = var_calc.compare_confidence_levels(
        returns,
        position_value=1000000,
        confidence_levels=[0.90, 0.95, 0.99]
    )

    print("\n" + "="*70)
    print("VaR COMPARISON ACROSS CONFIDENCE LEVELS")
    print("="*70)
    print(comparison.to_string(index=False))
    print("="*70)

    print("\n📖 Interpretation:")
    print(f"• 90% VaR: Lower confidence, smaller loss estimate")
    print(f"• 95% VaR: Standard confidence level (Basel II requirement)")
    print(f"• 99% VaR: Higher confidence, larger loss estimate (Basel III)")
    print(f"• As confidence ↑, VaR ↑ (we want to be more certain)")

    # Step 5: Different position sizes
    print("\n💵 Step 5: VaR for different position sizes...")
    print("\n" + "="*70)
    print("VaR FOR DIFFERENT PORTFOLIO SIZES (95% Confidence)")
    print("="*70)

    positions = [100000, 500000, 1000000, 5000000, 10000000]

    for pos in positions:
        result = var_calc.historical_var(returns, position_value=pos)
        print(f"Position: ${pos:>12,} → VaR: ${result['VaR']:>12,.2f} ({result['VaR_Percentage']:.2f}%)")

    print("="*70)

    # Step 6: Rolling VaR
    print("\n📈 Step 6: Calculating rolling 1-year VaR...")
    rolling = var_calc.rolling_var(returns, window=252, position_value=1000000)

    print(f"\nRolling VaR statistics:")
    print(f"  Minimum VaR: ${rolling.min():,.2f}")
    print(f"  Maximum VaR: ${rolling.max():,.2f}")
    print(f"  Mean VaR:    ${rolling.mean():,.2f}")
    print(f"  Current VaR: ${rolling.iloc[-1]:,.2f}")

    print("\n" + "="*70)
    print("✅ All tests completed successfully!")
    print("="*70)

    # Extra: Show worst days
    print("\n📉 BONUS: 5 Worst Trading Days in Dataset")
    print("="*70)
    worst_days = returns.nsmallest(5)
    for date, ret in worst_days.items():
        loss_1m = -ret * 1000000
        print(f"{date.date()}: {ret*100:>7.2f}% return → ${loss_1m:>10,.2f} loss on $1M position")
    print("="*70)
```

---

## 🧪 Step 2: Test Your VaR Calculator (20 minutes)

### 2.1 Run the Test

```bash
cd /home/user/market-risk-var-system
python src/models/var_calculator.py
```

### 2.2 Expected Output

```
======================================================================
Testing VaR Calculator - Historical Method
======================================================================

📥 Step 1: Fetching Apple (AAPL) data...
📊 Step 2: Preparing returns...
Total observations: 503
Date range: 2022-01-04 to 2024-01-03

💰 Step 3: Calculating 95% VaR for $1,000,000 position...

======================================================================
VaR RESULTS (95% Confidence)
======================================================================
Position Value:           $1,000,000.00
VaR (95%):                $31,234.56
VaR Percentage:           3.12%
Expected Shortfall:       $38,456.78
ES Percentage:            3.85%
Observations Used:        503
======================================================================

📖 Interpretation:
• We are 95% confident that losses won't exceed $31,234.56 tomorrow
• On average, when VaR is breached, we expect to lose $38,456.78
• This represents 3.12% of the portfolio value
• Expected to breach VaR ~13 days per year (5% of 252 trading days)

======================================================================
VaR COMPARISON ACROSS CONFIDENCE LEVELS
======================================================================
Confidence_Level  VaR_Amount  VaR_Percentage  ES_Amount  ES_Percentage
            90%    $23,456.78           2.35   $32,123.45           3.21
            95%    $31,234.56           3.12   $38,456.78           3.85
            99%    $48,567.89           4.86   $52,345.67           5.23
======================================================================
```

---

## 📊 Step 3: Understanding the Results (15 minutes)

### VaR vs Expected Shortfall

```
Returns Distribution (Sorted from Worst to Best):

Worst 1%: [-5.2%, -4.8%, -4.5%, -4.2%, -4.0%]  ← ES region (99% confidence)
Worst 5%: [..., -3.5%, -3.2%, -3.1%]           ← VaR cutoff (95% confidence)
Middle:   [-1.2%, -0.5%, 0.0%, 0.5%, 1.2%, ...]
Best:     [6.0%, 7.2%, 8.1%]

VaR (95%) = 3.1% → "We're 95% sure we won't lose more than 3.1%"
ES (95%) = 3.8% → "When we DO breach VaR, average loss is 3.8%"
```

**Key Insight**: ES is always >= VaR because it's the average of the worst cases.

### Confidence Level Interpretation

| Confidence | Meaning | Breach Frequency | Use Case |
|------------|---------|------------------|----------|
| **90%** | Less conservative | ~25 days/year | Internal risk mgmt |
| **95%** | Standard | ~13 days/year | Basel II, standard reporting |
| **99%** | Very conservative | ~3 days/year | Basel III, stress testing |

---

## 🔍 Step 4: Experiments (20 minutes)

### Experiment 1: VaR During COVID Crash (2020)

```python
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator

collector = DataCollector()
preprocessor = DataPreprocessor()

# Get S&P 500 data including COVID period
data = collector.fetch_stock_data("SPY", start_date="2019-01-01", end_date="2020-12-31")
returns_data = preprocessor.prepare_returns_data(data)
returns = returns_data['Returns']

# Calculate VaR before COVID (2019)
returns_2019 = returns['2019']
var_calc_95 = VaRCalculator(confidence_level=0.95)
var_2019 = var_calc_95.historical_var(returns_2019, position_value=1000000)

# Calculate VaR during COVID (2020)
returns_2020 = returns['2020']
var_2020 = var_calc_95.historical_var(returns_2020, position_value=1000000)

print(f"2019 (pre-COVID) VaR: ${var_2019['VaR']:,.2f}")
print(f"2020 (COVID) VaR:     ${var_2020['VaR']:,.2f}")
print(f"Increase:             {(var_2020['VaR'] / var_2019['VaR'] - 1) * 100:.1f}%")
```

### Experiment 2: Effect of Sample Size

```python
# Test VaR with different amounts of historical data
windows = [60, 126, 252, 504]  # 3mo, 6mo, 1yr, 2yr

for window in windows:
    recent_returns = returns.tail(window)
    var_result = var_calc_95.historical_var(recent_returns, position_value=1000000)
    print(f"{window:3d} days: VaR = ${var_result['VaR']:>10,.2f} ({var_result['VaR_Percentage']:.2f}%)")
```

**You'll notice**: More data generally gives more stable VaR estimates.

### Experiment 3: Compare Different Stocks

```python
tickers = ['AAPL', 'TSLA', 'JNJ', 'XLE']  # Tech, volatile, defensive, energy

for ticker in tickers:
    data = collector.fetch_stock_data(ticker, period="1y")
    returns_data = preprocessor.prepare_returns_data(data)
    var_result = var_calc_95.historical_var(returns_data['Returns'], position_value=1000000)

    print(f"{ticker:4s}: VaR = ${var_result['VaR']:>10,.2f} ({var_result['VaR_Percentage']:>5.2f}%)")
```

**You'll notice**: Tesla (TSLA) has much higher VaR than Johnson & Johnson (JNJ)!

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Understood what Value at Risk (VaR) means
✅ Learned the Historical VaR method
✅ Implemented a complete VaR calculator
✅ Calculated VaR at multiple confidence levels (90%, 95%, 99%)
✅ Computed Expected Shortfall (CVaR)
✅ Interpreted VaR results in real-world terms
✅ Applied VaR to different portfolio sizes
✅ Calculated rolling VaR over time

---

## 🐛 Troubleshooting

### Issue 1: VaR is negative

**Cause**: Your returns are mostly positive (bull market)

**Solution**: This is actually correct! It means the 5th percentile is a positive return. Interpret as "virtually no downside risk in this period."

### Issue 2: VaR seems too high/low

**Check**:
- Are you using log returns? ✓
- Is position_value correct? ✓
- Is confidence_level between 0 and 1? ✓

### Issue 3: "Not enough data"

**Solution**: Use at least 100 observations:
```python
data = collector.fetch_stock_data("AAPL", period="1y")  # ~252 days
```

---

## 📚 Key Formulas Reference

### Historical VaR
```
VaR_α = -Position_Value × Quantile_α(Returns)

where:
  α = significance level (0.05 for 95% confidence)
  Quantile_α = α-th percentile of returns
```

### Expected Shortfall (CVaR)
```
ES_α = -Position_Value × E[Returns | Returns ≤ Quantile_α]

In words: Average of all returns worse than VaR
```

---

## 🎯 Homework / Practice

### Exercise 1: Create a VaR Report Function

```python
def generate_var_report(ticker, position_value=1000000):
    """Generate comprehensive VaR report for a ticker"""
    # Your code here
    pass
```

### Exercise 2: Find Stocks with VaR < $20,000

```python
tickers = ['AAPL', 'MSFT', 'JNJ', 'PG', 'KO']  # Mix of stocks

low_var_stocks = []
for ticker in tickers:
    # Calculate VaR for each
    # Keep only stocks with VaR < $20,000
    pass
```

### Exercise 3: Historical VaR Accuracy

```python
# Calculate VaR on first 80% of data
# Test on last 20%
# Count how many days VaR was breached
# Should be ~5% for 95% VaR
```

---

## 🔜 Coming Up in Day 004

Tomorrow you'll learn:
- **Parametric VaR**: Assume normal distribution
- **Z-scores**: Using statistical distributions
- **Student's t distribution**: Accounting for fat tails
- **Compare**: Historical vs Parametric VaR

**File you'll update**: `src/models/var_calculator.py` (Part 2)

---

**Excellent work! You've mastered Historical VaR! 📊**
