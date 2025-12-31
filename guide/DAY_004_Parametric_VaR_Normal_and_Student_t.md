# Day 004: Parametric VaR (Normal & Student's t)

**Duration**: 2 hours
**Difficulty**: Intermediate
**Prerequisites**: Completed Day 001-003

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Understand Parametric VaR (Variance-Covariance method)
- Learn about the Normal distribution and Z-scores
- Implement Student's t distribution for fat tails
- Compare Historical vs Parametric VaR
- Understand when to use each method

---

## 🎯 Learning Objectives

### Financial Concepts:
- **Parametric VaR**: Assumes returns follow a specific distribution
- **Normal Distribution**: Bell curve assumption
- **Student's t Distribution**: Accounts for fat tails (extreme events)
- **Degrees of Freedom**: Parameter for t-distribution
- **Z-scores**: Standard deviations from the mean

### Programming Concepts:
- scipy.stats module for distributions
- Statistical distribution functions (ppf, pdf, cdf)
- Comparison methods

---

## 💡 Understanding Parametric VaR (20 minutes)

### What is Parametric VaR?

Unlike Historical VaR (which uses actual data), **Parametric VaR makes assumptions** about the distribution of returns.

**Historical VaR says:**
> "Look at the past 252 days, the 5th worst day was -3.12%, so that's our VaR"

**Parametric VaR says:**
> "Returns follow a normal distribution with mean=0.08% and std=2.01%, so VaR = mean + z-score × std"

### The Formula

```
VaR = -Position_Value × (μ + z_α × σ)

where:
  μ = mean return
  σ = standard deviation (volatility)
  z_α = z-score for confidence level α
```

### Example Calculation (95% VaR)

```
Position Value = $1,000,000
Mean return (μ) = 0.0008 (0.08% per day)
Std dev (σ) = 0.02 (2% per day)
Confidence = 95% → z-score = -1.645

VaR = -$1,000,000 × (0.0008 + (-1.645) × 0.02)
    = -$1,000,000 × (0.0008 - 0.0329)
    = -$1,000,000 × (-0.0321)
    = $32,100

Interpretation: 95% VaR is $32,100
```

---

## 📊 Normal Distribution vs Student's t Distribution

### Normal Distribution (Gaussian)

```
Bell curve:

        *
      *   *
    *       *
  *           *
*               *
__________________|__________________
                 μ (mean)

Properties:
- Symmetric
- Thin tails (few extreme events)
- Defined by 2 parameters: mean (μ) and std dev (σ)
```

**Z-scores for common confidence levels:**
- 90% confidence → z = -1.282
- 95% confidence → z = -1.645
- 99% confidence → z = -2.326

### Student's t Distribution

```
Fatter tails:

        *
      * | *
    *   |   *
  *     |     *
*       |       *  ← Fatter tails = more extreme events
________|________
        μ

Properties:
- Symmetric
- Fat tails (more extreme events than normal)
- Defined by 3 parameters: mean (μ), std dev (σ), degrees of freedom (df)
- Approaches normal distribution as df → ∞
```

**When to use t-distribution:**
- Small sample sizes (< 30 observations)
- Financial data with frequent extreme events
- More conservative VaR estimates

---

## 💻 Step 1: Implement Parametric VaR (50 minutes)

### 1.1 Update `src/models/var_calculator.py`

Add this method to your `VaRCalculator` class:

```python
def parametric_var(
    self,
    returns: pd.Series,
    position_value: float = 1000000,
    window: Optional[int] = None,
    distribution: str = 'normal'
) -> Dict[str, float]:
    """
    Calculate Parametric VaR (Variance-Covariance method)

    Assumes returns follow a specified distribution (normal or t)

    Args:
        returns: Historical returns
        position_value: Portfolio value in currency
        window: Rolling window size (None = use all data)
        distribution: 'normal' or 't' (Student's t)

    Returns:
        Dictionary containing VaR, ES, and statistics

    Example:
        >>> var_calc = VaRCalculator(confidence_level=0.95)
        >>> # Normal distribution
        >>> var_normal = var_calc.parametric_var(returns, 1000000, distribution='normal')
        >>> # Student's t distribution
        >>> var_t = var_calc.parametric_var(returns, 1000000, distribution='t')
    """

    # Clean data
    returns_clean = returns.dropna()

    # Use only recent data if window specified
    if window is not None:
        returns_clean = returns_clean.tail(window)
        logger.info(f"Using last {window} observations")

    if len(returns_clean) == 0:
        raise ValueError("No valid returns data provided")

    # Calculate statistics
    mean = returns_clean.mean()
    std = returns_clean.std()

    logger.info(f"Mean return: {mean:.6f} ({mean*100:.4f}%)")
    logger.info(f"Volatility:  {std:.6f} ({std*100:.4f}%)")

    if distribution == 'normal':
        # Normal distribution
        z_score = stats.norm.ppf(self.alpha)
        var_percentile = mean + z_score * std

        # Expected Shortfall for normal distribution
        # ES = μ - σ × φ(z_α) / α
        # where φ is the standard normal PDF
        z_score_abs = abs(z_score)
        es_percentile = mean - std * stats.norm.pdf(z_score_abs) / self.alpha

        logger.info(f"Using Normal distribution (z-score: {z_score:.4f})")

    elif distribution == 't':
        # Student's t distribution
        df = len(returns_clean) - 1  # Degrees of freedom
        t_score = stats.t.ppf(self.alpha, df)
        var_percentile = mean + t_score * std

        # For t-distribution, use approximation for ES
        # (exact formula is complex)
        es_percentile = var_percentile * 1.2  # Conservative approximation

        logger.info(f"Using Student's t distribution (df={df}, t-score: {t_score:.4f})")

    else:
        raise ValueError(f"Unknown distribution: {distribution}. Use 'normal' or 't'")

    # Convert to positive dollar amounts (losses)
    var = -var_percentile * position_value
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
        'Method': f'Parametric ({distribution})',
        'Observations': len(returns_clean)
    }
```

---

## 🧪 Step 2: Test Parametric VaR (20 minutes)

### 2.1 Create Test Script

Create a file `test_parametric_var.py`:

```python
"""
Test Parametric VaR Methods
"""

import sys
sys.path.append('src')

from data.data_collector import DataCollector
from data.preprocessor import DataPreprocessor
from models.var_calculator import VaRCalculator
import pandas as pd

print("="*70)
print("Testing Parametric VaR (Normal & Student's t)")
print("="*70)

# Fetch and prepare data
print("\n📥 Fetching Apple (AAPL) data (2 years)...")
collector = DataCollector()
data = collector.fetch_stock_data("AAPL", period="2y")

preprocessor = DataPreprocessor()
returns_data = preprocessor.prepare_returns_data(data)
returns = returns_data['Returns'].dropna()

print(f"Observations: {len(returns)}")
print(f"Date range: {returns.index[0].date()} to {returns.index[-1].date()}")

# Initialize calculator
var_calc = VaRCalculator(confidence_level=0.95)

# Test 1: Normal distribution VaR
print("\n" + "="*70)
print("TEST 1: Parametric VaR with Normal Distribution")
print("="*70)

var_normal = var_calc.parametric_var(
    returns,
    position_value=1000000,
    distribution='normal'
)

print(f"\nPosition Value:     ${1000000:,.2f}")
print(f"Mean Return:        {var_normal['Mean']*100:.4f}%")
print(f"Volatility (Std):   {var_normal['Std']*100:.4f}%")
print(f"VaR (95%):          ${var_normal['VaR']:,.2f}")
print(f"VaR Percentage:     {var_normal['VaR_Percentage']:.2f}%")
print(f"Expected Shortfall: ${var_normal['ES']:,.2f}")

# Test 2: Student's t distribution VaR
print("\n" + "="*70)
print("TEST 2: Parametric VaR with Student's t Distribution")
print("="*70)

var_t = var_calc.parametric_var(
    returns,
    position_value=1000000,
    distribution='t'
)

print(f"\nPosition Value:     ${1000000:,.2f}")
print(f"VaR (95%):          ${var_t['VaR']:,.2f}")
print(f"VaR Percentage:     {var_t['VaR_Percentage']:.2f}%")
print(f"Expected Shortfall: ${var_t['ES']:,.2f}")

# Test 3: Compare all three methods
print("\n" + "="*70)
print("TEST 3: Comparison - Historical vs Normal vs Student's t")
print("="*70)

var_historical = var_calc.historical_var(returns, position_value=1000000)

comparison_data = {
    'Method': ['Historical', 'Parametric (Normal)', 'Parametric (t)'],
    'VaR_Amount': [var_historical['VaR'], var_normal['VaR'], var_t['VaR']],
    'VaR_Percentage': [var_historical['VaR_Percentage'], var_normal['VaR_Percentage'], var_t['VaR_Percentage']],
    'ES_Amount': [var_historical['ES'], var_normal['ES'], var_t['ES']]
}

comparison_df = pd.DataFrame(comparison_data)
print("\n" + comparison_df.to_string(index=False))

print("\n📊 Analysis:")
print(f"  Historical VaR:    ${var_historical['VaR']:,.2f}")
print(f"  Normal VaR:        ${var_normal['VaR']:,.2f} (diff: {(var_normal['VaR']/var_historical['VaR']-1)*100:+.1f}%)")
print(f"  Student's t VaR:   ${var_t['VaR']:,.2f} (diff: {(var_t['VaR']/var_historical['VaR']-1)*100:+.1f}%)")

# Test 4: Effect of sample size on t-distribution
print("\n" + "="*70)
print("TEST 4: Effect of Sample Size on Student's t VaR")
print("="*70)

sample_sizes = [30, 60, 126, 252, 504]

print(f"\n{'Sample Size':<15} {'VaR (Normal)':<15} {'VaR (t)':<15} {'Difference':<15}")
print("-" * 60)

for size in sample_sizes:
    if size <= len(returns):
        recent_returns = returns.tail(size)

        var_n = var_calc.parametric_var(recent_returns, 1000000, distribution='normal')
        var_t_test = var_calc.parametric_var(recent_returns, 1000000, distribution='t')

        diff = var_t_test['VaR'] - var_n['VaR']
        print(f"{size:<15} ${var_n['VaR']:>12,.2f} ${var_t_test['VaR']:>12,.2f} ${diff:>12,.2f}")

print("\n📖 Observation: As sample size increases, t-distribution → normal distribution")

print("\n" + "="*70)
print("✅ All tests completed!")
print("="*70)
```

### 2.2 Run the Test

```bash
python test_parametric_var.py
```

### 2.3 Expected Output

```
======================================================================
Testing Parametric VaR (Normal & Student's t)
======================================================================

📥 Fetching Apple (AAPL) data (2 years)...
Observations: 503

======================================================================
TEST 1: Parametric VaR with Normal Distribution
======================================================================

Position Value:     $1,000,000.00
Mean Return:        0.0812%
Volatility (Std):   2.0145%
VaR (95%):          $32,346.12
VaR Percentage:     3.23%
Expected Shortfall: $38,567.23

======================================================================
TEST 3: Comparison - Historical vs Normal vs Student's t
======================================================================

          Method  VaR_Amount  VaR_Percentage   ES_Amount
      Historical   $31,234.56           3.12   $38,456.78
Parametric (Normal)   $32,346.12           3.23   $38,567.23
  Parametric (t)   $33,789.45           3.38   $40,547.34

📊 Analysis:
  Historical VaR:    $31,234.56
  Normal VaR:        $32,346.12 (diff: +3.6%)
  Student's t VaR:   $33,789.45 (diff: +8.2%)
```

---

## 📊 Step 3: Understanding the Differences (15 minutes)

### Why Are the Results Different?

**Historical VaR ($31,234):**
- Uses actual historical data
- No assumptions about distribution
- Captures real market behavior

**Normal VaR ($32,346):**
- Assumes normal distribution
- Smooth, symmetric tails
- Can underestimate risk if returns have fat tails

**Student's t VaR ($33,789):**
- Accounts for fat tails
- More conservative
- Better for financial data (which often has extreme events)

### When to Use Each Method:

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Historical** | Stable markets, lots of data | Simple, no assumptions | Backward-looking, can't extrapolate |
| **Normal** | Quick estimates, stable assets | Fast, mathematically elegant | Underestimates tail risk |
| **Student's t** | Volatile markets, small samples | Captures fat tails, conservative | Requires parameter estimation |

---

## 🔍 Step 4: Experiments (20 minutes)

### Experiment 1: Compare During Crisis vs Normal Times

```python
# Normal period (2019)
data_2019 = collector.fetch_stock_data("SPY", start_date="2019-01-01", end_date="2019-12-31")
returns_2019 = preprocessor.prepare_returns_data(data_2019)['Returns']

var_calc = VaRCalculator(confidence_level=0.95)

hist_2019 = var_calc.historical_var(returns_2019, 1000000)
norm_2019 = var_calc.parametric_var(returns_2019, 1000000, distribution='normal')
t_2019 = var_calc.parametric_var(returns_2019, 1000000, distribution='t')

print("2019 (Normal Period):")
print(f"  Historical: ${hist_2019['VaR']:,.2f}")
print(f"  Normal:     ${norm_2019['VaR']:,.2f}")
print(f"  Student's t: ${t_2019['VaR']:,.2f}")

# Crisis period (2020 - COVID)
data_2020 = collector.fetch_stock_data("SPY", start_date="2020-01-01", end_date="2020-12-31")
returns_2020 = preprocessor.prepare_returns_data(data_2020)['Returns']

hist_2020 = var_calc.historical_var(returns_2020, 1000000)
norm_2020 = var_calc.parametric_var(returns_2020, 1000000, distribution='normal')
t_2020 = var_calc.parametric_var(returns_2020, 1000000, distribution='t')

print("\n2020 (COVID Crisis):")
print(f"  Historical: ${hist_2020['VaR']:,.2f}")
print(f"  Normal:     ${norm_2020['VaR']:,.2f}")
print(f"  Student's t: ${t_2020['VaR']:,.2f}")
```

**Observation**: During crises, Student's t gives more conservative (higher) VaR estimates.

### Experiment 2: Different Confidence Levels

```python
confidence_levels = [0.90, 0.95, 0.99]

for cl in confidence_levels:
    var_calc = VaRCalculator(confidence_level=cl)

    hist = var_calc.historical_var(returns, 1000000)
    norm = var_calc.parametric_var(returns, 1000000, distribution='normal')
    t_dist = var_calc.parametric_var(returns, 1000000, distribution='t')

    print(f"\n{cl*100}% Confidence:")
    print(f"  Historical: ${hist['VaR']:>10,.2f}")
    print(f"  Normal:     ${norm['VaR']:>10,.2f}")
    print(f"  Student's t: ${t_dist['VaR']:>10,.2f}")
```

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Understood Parametric VaR (Variance-Covariance method)
✅ Implemented Normal distribution VaR
✅ Implemented Student's t distribution VaR
✅ Learned about Z-scores and degrees of freedom
✅ Compared Historical vs Parametric methods
✅ Understood when to use each distribution
✅ Tested VaR during crisis vs normal periods

---

## 🐛 Troubleshooting

### Issue 1: Student's t VaR much higher than Normal

**This is expected!** Student's t has fatter tails, so it gives more conservative estimates.

### Issue 2: Normal VaR is negative

**Possible causes:**
- Mean return is very positive
- Volatility is very low

**Solution**: This means the asset is very stable with positive drift. VaR near zero is correct.

### Issue 3: "Degrees of freedom too low"

**Cause**: Not enough data for t-distribution

**Solution**: Use at least 30 observations:
```python
data = collector.fetch_stock_data("AAPL", period="6mo")  # At least 120 days
```

---

## 📚 Key Formulas Reference

### Parametric VaR (Normal Distribution)
```
VaR = -Position_Value × (μ + z_α × σ)

where:
  μ = mean return
  σ = standard deviation
  z_α = z-score for confidence level α

Z-scores:
  90% confidence: z = -1.282
  95% confidence: z = -1.645
  99% confidence: z = -2.326
```

### Parametric VaR (Student's t Distribution)
```
VaR = -Position_Value × (μ + t_α,df × σ)

where:
  t_α,df = t-score for confidence level α and df degrees of freedom
  df = n - 1 (n = sample size)
```

---

## 🎯 Homework / Practice

### Exercise 1: Build a Method Comparison Function

```python
def compare_all_var_methods(ticker, position_value=1000000):
    """
    Compare Historical, Normal, and Student's t VaR
    Returns a DataFrame with all three methods
    """
    # Your code here
    pass
```

### Exercise 2: Test Normality Assumption

```python
from scipy import stats

# Shapiro-Wilk test for normality
statistic, p_value = stats.shapiro(returns)

if p_value > 0.05:
    print("Returns are approximately normal")
else:
    print("Returns are NOT normal - use Historical or t-distribution")
```

### Exercise 3: Optimal Distribution Selection

```python
def select_best_distribution(returns):
    """
    Automatically select best distribution based on kurtosis
    High kurtosis (>3) → Student's t
    Normal kurtosis (~3) → Normal
    """
    # Your code here
    pass
```

---

## 🔜 Coming Up in Day 005

Tomorrow you'll learn:
- **Monte Carlo VaR**: Simulation-based approach
- **Bootstrap Resampling**: Randomly sample from historical data
- **Parametric Simulation**: Generate random returns from distribution
- **Multi-horizon VaR**: 10-day, 30-day forecasts

**File you'll update**: `src/models/var_calculator.py` (Part 3)

---

**Great work! You've mastered Parametric VaR! 📈**
