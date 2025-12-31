# Day 008: GARCH Model - Part 1 (Volatility Basics)

**Duration**: 2 hours
**Difficulty**: Intermediate-Advanced
**Prerequisites**: Completed Day 001-007

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Understand volatility clustering in financial markets
- Learn what GARCH models are and why they matter
- Implement GARCH(1,1) - the most common specification
- Fit GARCH models to return data
- Extract conditional volatility (time-varying risk)
- Compare constant vs time-varying volatility

---

## 🎯 Learning Objectives

### Financial Concepts:
- **Volatility Clustering**: High volatility follows high volatility
- **Conditional Volatility**: Risk that changes over time
- **Heteroskedasticity**: Non-constant variance
- **Leverage Effect**: Bad news increases volatility more than good news

### Statistical Concepts:
- **ARCH**: AutoRegressive Conditional Heteroskedasticity
- **GARCH**: Generalized ARCH
- **Volatility Persistence**: How long volatility shocks last
- **Unconditional vs Conditional Variance**

---

## 💡 Understanding Volatility Clustering (20 minutes)

### What is Volatility Clustering?

**Observation**: In financial markets, large price movements tend to be followed by large movements (of either sign), and small movements tend to be followed by small movements.

**Visual Example:**

```
Daily Returns Over Time:

 5% |     *                    *
 3% |   *   *              *     *
 1% | *       *          *         *
-1% |           *    *               *
-3% |             **                   *
-5% |                                    *
    |____________________________________________
     ↑           ↑                    ↑
     Calm      Volatile              Volatile
     Period    Period                Period
```

**Key Insight**:
- Volatility is **not constant** over time
- High volatility periods cluster together
- Low volatility periods cluster together

---

### Why Standard Models Fail

**Problem with Constant Volatility:**

```python
# Standard assumption:
σ = 0.02  # 2% volatility (constant)

# Reality:
σ_day1 = 0.01  # Calm day
σ_day2 = 0.01  # Still calm
σ_day3 = 0.04  # Sudden spike!
σ_day4 = 0.05  # Still volatile
σ_day5 = 0.03  # Calming down
```

**GARCH Solution**: Model volatility as a **time-varying process**.

---

## 📊 GARCH Model Explained

### GARCH(p,q) Formula

```
Returns equation:
r_t = μ + ε_t

where ε_t = σ_t × z_t  (z_t ~ N(0,1))

Variance equation (GARCH):
σ²_t = ω + Σ(α_i ε²_{t-i}) + Σ(β_j σ²_{t-j})
       ↑         ↑                  ↑
     Constant  ARCH terms       GARCH terms
               (past shocks)     (past variance)
```

### GARCH(1,1) - Most Common Specification

```
σ²_t = ω + α × ε²_{t-1} + β × σ²_{t-1}

Components:
- ω (omega): Base level of volatility
- α (alpha): Weight on yesterday's shock (ARCH term)
- β (beta): Weight on yesterday's volatility (GARCH term)
```

### Interpretation:

**Today's volatility depends on:**
1. **ω**: Long-run average volatility (constant)
2. **α × ε²_{t-1}**: How big was yesterday's return? (shock)
3. **β × σ²_{t-1}**: How volatile was yesterday? (persistence)

**Example:**
```
ω = 0.000005
α = 0.10
β = 0.85

Yesterday:
- Return: -3% (large shock!)
- Volatility: 2%

Today's volatility:
σ²_t = 0.000005 + 0.10 × (0.03)² + 0.85 × (0.02)²
     = 0.000005 + 0.00009 + 0.00034
     = 0.00044
σ_t = √0.00044 = 2.1%

→ Volatility increased from 2% to 2.1% due to yesterday's shock
```

---

## 🔍 Key GARCH Properties

### 1. Persistence

**Persistence = α + β**

- If α + β ≈ 1: High persistence (shocks last a long time)
- If α + β < 1: Low persistence (shocks die out quickly)
- Typical values: α + β = 0.95 to 0.99

**Example:**
```
α = 0.10, β = 0.85
Persistence = 0.95

A volatility shock today will have:
- 95% impact tomorrow
- 90% impact in 2 days
- 86% impact in 3 days
(Decays slowly!)
```

### 2. Mean Reversion

**Long-run volatility:**
```
σ̄² = ω / (1 - α - β)

Example:
ω = 0.00001, α = 0.10, β = 0.85
σ̄² = 0.00001 / (1 - 0.95) = 0.0002
σ̄ = 1.41%
```

Volatility **reverts** to this long-run average.

---

## 💻 Step 1: Install ARCH Package (5 minutes)

```bash
pip install arch==6.2.0
```

**What arch package provides:**
- GARCH, EGARCH, GJR-GARCH models
- Multiple distributions (Normal, Student's t, Skewed-t)
- Volatility forecasting
- Model diagnostics

---

## 💻 Step 2: Build GARCH Model (50 minutes)

### 2.1 Create `src/models/garch_model.py`

```python
"""
GARCH Model Module for Market Risk VaR System
Implements GARCH for volatility forecasting
"""

import pandas as pd
import numpy as np
from arch import arch_model
import warnings
import logging
from typing import Dict, Optional, Tuple
import pickle

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GARCHForecaster:
    """
    GARCH (Generalized AutoRegressive Conditional Heteroskedasticity) model

    GARCH models time-varying volatility, capturing:
    - Volatility clustering
    - Leverage effects (with EGARCH)
    - Fat tails in return distribution
    """

    def __init__(
        self,
        p: int = 1,
        q: int = 1,
        mean: str = 'Zero',
        dist: str = 'normal'
    ):
        """
        Initialize GARCH forecaster

        Args:
            p: GARCH lag order (usually 1)
            q: ARCH lag order (usually 1)
            mean: Mean model ('Zero', 'Constant', 'AR')
            dist: Error distribution ('normal', 't', 'skewt')

        Example:
            >>> garch = GARCHForecaster(p=1, q=1)  # GARCH(1,1) - most common
            >>> garch = GARCHForecaster(p=1, q=1, dist='t')  # with Student's t
        """
        self.p = p
        self.q = q
        self.mean = mean
        self.dist = dist
        self.model = None
        self.fitted_model = None
        self.results = None

        logger.info(f"GARCH({p},{q}) forecaster initialized")
        logger.info(f"Mean model: {mean}, Distribution: {dist}")

    def fit(self, returns: pd.Series, rescale: bool = True) -> None:
        """
        Fit GARCH model to returns

        Args:
            returns: Return series (should be stationary)
            rescale: Whether to rescale to percentage (default: True)
                    ARCH package works better with rescaled data

        Example:
            >>> garch = GARCHForecaster(p=1, q=1)
            >>> garch.fit(returns)
        """

        # Clean data
        returns_clean = returns.dropna()

        if len(returns_clean) < 100:
            raise ValueError("Need at least 100 observations for GARCH")

        # Rescale to percentage if needed (helps numerical stability)
        if rescale:
            returns_clean = returns_clean * 100
            logger.info("Returns rescaled to percentage")

        logger.info(f"Fitting GARCH({self.p},{self.q}) to {len(returns_clean)} observations...")

        try:
            # Create GARCH model
            self.model = arch_model(
                returns_clean,
                mean=self.mean,
                vol='Garch',
                p=self.p,
                q=self.q,
                dist=self.dist
            )

            # Fit model
            self.fitted_model = self.model.fit(disp='off')

            logger.info("✅ Model fitted successfully")

            # Store results
            self.results = {
                'aic': self.fitted_model.aic,
                'bic': self.fitted_model.bic,
                'loglikelihood': self.fitted_model.loglikelihood,
                'num_params': self.fitted_model.num_params,
                'p': self.p,
                'q': self.q,
                'mean': self.mean,
                'dist': self.dist
            }

            # Extract parameters
            params = self.fitted_model.params
            if 'omega' in params:
                self.results['omega'] = params['omega']
            if 'alpha[1]' in params:
                self.results['alpha'] = params['alpha[1]']
            if 'beta[1]' in params:
                self.results['beta'] = params['beta[1]']

            # Calculate persistence
            if 'alpha' in self.results and 'beta' in self.results:
                self.results['persistence'] = self.results['alpha'] + self.results['beta']

            logger.info(f"AIC: {self.fitted_model.aic:.2f}")
            logger.info(f"BIC: {self.fitted_model.bic:.2f}")

            if 'omega' in self.results:
                logger.info(f"ω (omega):    {self.results['omega']:.8f}")
            if 'alpha' in self.results:
                logger.info(f"α (alpha):    {self.results['alpha']:.6f}")
            if 'beta' in self.results:
                logger.info(f"β (beta):     {self.results['beta']:.6f}")
            if 'persistence' in self.results:
                logger.info(f"Persistence (α+β): {self.results['persistence']:.6f}")

        except Exception as e:
            logger.error(f"❌ Error fitting model: {str(e)}")
            raise

    def get_conditional_volatility(self) -> pd.Series:
        """
        Get conditional volatility (fitted values)

        This is the time-varying volatility estimated by GARCH

        Returns:
            Series with conditional volatility (in percentage if rescaled)

        Example:
            >>> garch.fit(returns)
            >>> vol = garch.get_conditional_volatility()
            >>> print(f"Current volatility: {vol.iloc[-1]:.2f}%")
        """

        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        cond_vol = self.fitted_model.conditional_volatility

        logger.info(f"Conditional volatility extracted: {len(cond_vol)} values")
        logger.info(f"Mean volatility: {cond_vol.mean():.4f}%")
        logger.info(f"Min volatility:  {cond_vol.min():.4f}%")
        logger.info(f"Max volatility:  {cond_vol.max():.4f}%")

        return cond_vol

    def get_standardized_residuals(self) -> pd.Series:
        """
        Get standardized residuals

        These should be approximately N(0,1) if model is correctly specified

        Returns:
            Series of standardized residuals

        Example:
            >>> residuals = garch.get_standardized_residuals()
            >>> print(f"Mean: {residuals.mean():.4f}")  # Should be ~0
            >>> print(f"Std: {residuals.std():.4f}")   # Should be ~1
        """

        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        return self.fitted_model.std_resid

    def get_model_summary(self) -> str:
        """
        Get detailed model summary

        Returns:
            String with full model output

        Example:
            >>> print(garch.get_model_summary())
        """

        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        return str(self.fitted_model.summary())

    def get_parameters(self) -> pd.Series:
        """
        Get model parameters

        Returns:
            Series with parameter estimates

        Example:
            >>> params = garch.get_parameters()
            >>> print(f"omega: {params['omega']}")
            >>> print(f"alpha: {params['alpha[1]']}")
            >>> print(f"beta: {params['beta[1]']}")
        """

        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        return self.fitted_model.params

    def print_diagnostics(self):
        """
        Print comprehensive diagnostics

        Example:
            >>> garch.fit(returns)
            >>> garch.print_diagnostics()
        """

        if self.fitted_model is None:
            raise ValueError("Model must be fitted first")

        print("\n" + "="*70)
        print(f"GARCH({self.p},{self.q}) MODEL DIAGNOSTICS")
        print("="*70)

        # Model information
        print(f"\n📊 Model Specification:")
        print(f"  GARCH Order:     ({self.p}, {self.q})")
        print(f"  Mean Model:      {self.mean}")
        print(f"  Distribution:    {self.dist}")
        print(f"  Observations:    {self.fitted_model.nobs}")

        # Information criteria
        print(f"\n📈 Model Fit:")
        print(f"  Log-Likelihood:  {self.results['loglikelihood']:.2f}")
        print(f"  AIC:             {self.results['aic']:.2f}")
        print(f"  BIC:             {self.results['bic']:.2f}")

        # Parameters
        print(f"\n🔧 Estimated Parameters:")
        params = self.get_parameters()
        for name, value in params.items():
            print(f"  {name:15s}: {value:>10.8f}")

        # GARCH-specific metrics
        if 'persistence' in self.results:
            print(f"\n📊 GARCH Metrics:")
            print(f"  Persistence (α+β): {self.results['persistence']:.6f}")

            if self.results['persistence'] >= 1:
                print(f"  ⚠️  WARNING: Persistence >= 1 (non-stationary!)")
            elif self.results['persistence'] > 0.95:
                print(f"  ⚠️  High persistence: Shocks last a long time")
            else:
                print(f"  ✅ Moderate persistence")

            # Long-run volatility
            if self.results['persistence'] < 1 and 'omega' in self.results:
                long_run_var = self.results['omega'] / (1 - self.results['persistence'])
                long_run_vol = np.sqrt(long_run_var)
                print(f"  Long-run volatility: {long_run_vol:.4f}%")

        # Conditional volatility stats
        cond_vol = self.get_conditional_volatility()
        print(f"\n📉 Conditional Volatility:")
        print(f"  Mean:    {cond_vol.mean():.4f}%")
        print(f"  Std Dev: {cond_vol.std():.4f}%")
        print(f"  Min:     {cond_vol.min():.4f}%")
        print(f"  Max:     {cond_vol.max():.4f}%")
        print(f"  Current: {cond_vol.iloc[-1]:.4f}%")

        # Standardized residuals
        std_resid = self.get_standardized_residuals()
        print(f"\n🔍 Standardized Residuals:")
        print(f"  Mean:     {std_resid.mean():.4f} (should be ~0)")
        print(f"  Std Dev:  {std_resid.std():.4f} (should be ~1)")
        print(f"  Skewness: {std_resid.skew():.4f}")
        print(f"  Kurtosis: {std_resid.kurtosis():.4f}")

        if abs(std_resid.mean()) > 0.1:
            print(f"  ⚠️  Mean far from 0")
        else:
            print(f"  ✅ Mean close to 0")

        if abs(std_resid.std() - 1) > 0.2:
            print(f"  ⚠️  Std dev far from 1")
        else:
            print(f"  ✅ Std dev close to 1")

        print("="*70 + "\n")


# Test the module
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor

    print("="*70)
    print("Testing GARCH Forecaster - Volatility Modeling")
    print("="*70)

    # Fetch data
    print("\n📥 Fetching data...")
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()

    print(f"Observations: {len(returns)}")

    # Test 1: Fit GARCH(1,1)
    print("\n" + "="*70)
    print("TEST 1: Fit GARCH(1,1) Model")
    print("="*70)

    garch = GARCHForecaster(p=1, q=1)
    garch.fit(returns)

    # Print diagnostics
    garch.print_diagnostics()

    # Test 2: Extract conditional volatility
    print("\n" + "="*70)
    print("TEST 2: Conditional Volatility Time Series")
    print("="*70)

    cond_vol = garch.get_conditional_volatility()

    print(f"\nVolatility Statistics:")
    print(f"  Mean:    {cond_vol.mean():.4f}%")
    print(f"  Std:     {cond_vol.std():.4f}%")
    print(f"  Min:     {cond_vol.min():.4f}%")
    print(f"  Max:     {cond_vol.max():.4f}%")

    print(f"\nFirst 5 volatility values:")
    print(cond_vol.head())

    print(f"\nLast 5 volatility values:")
    print(cond_vol.tail())

    # Test 3: Compare distributions
    print("\n" + "="*70)
    print("TEST 3: Compare Normal vs Student's t Distribution")
    print("="*70)

    garch_normal = GARCHForecaster(p=1, q=1, dist='normal')
    garch_t = GARCHForecaster(p=1, q=1, dist='t')

    garch_normal.fit(returns)
    garch_t.fit(returns)

    print(f"\nNormal distribution:")
    print(f"  AIC: {garch_normal.results['aic']:.2f}")
    print(f"  BIC: {garch_normal.results['bic']:.2f}")

    print(f"\nStudent's t distribution:")
    print(f"  AIC: {garch_t.results['aic']:.2f}")
    print(f"  BIC: {garch_t.results['bic']:.2f}")

    if garch_t.results['aic'] < garch_normal.results['aic']:
        print(f"\n✅ Student's t fits better (lower AIC)")
    else:
        print(f"\n✅ Normal distribution fits better (lower AIC)")

    # Test 4: Volatility clustering visualization
    print("\n" + "="*70)
    print("TEST 4: Detect Volatility Clustering")
    print("="*70)

    # Check autocorrelation in squared returns
    from statsmodels.tsa.stattools import acf

    returns_squared = returns ** 2
    acf_sq = acf(returns_squared, nlags=10, fft=False)

    print(f"\nACF of Squared Returns (tests for volatility clustering):")
    print(f"  Lag 1: {acf_sq[1]:.4f}")
    print(f"  Lag 5: {acf_sq[5]:.4f}")
    print(f"  Lag 10: {acf_sq[10]:.4f}")

    if acf_sq[1] > 0.05:
        print(f"\n✅ Significant autocorrelation → Volatility clustering present!")
        print(f"   → GARCH is appropriate")
    else:
        print(f"\n❌ No volatility clustering")

    print("\n" + "="*70)
    print("✅ All tests completed!")
    print("="*70)
```

---

## 🧪 Step 3: Test GARCH Model (20 minutes)

### 3.1 Run the Test

```bash
cd /home/user/market-risk-var-system
python src/models/garch_model.py
```

### 3.2 Expected Output

```
======================================================================
Testing GARCH Forecaster - Volatility Modeling
======================================================================

======================================================================
TEST 1: Fit GARCH(1,1) Model
======================================================================

======================================================================
GARCH(1, 1) MODEL DIAGNOSTICS
======================================================================

📊 Model Specification:
  GARCH Order:     (1, 1)
  Mean Model:      Zero
  Distribution:    normal
  Observations:    503

📈 Model Fit:
  Log-Likelihood:  1425.84
  AIC:             -2845.67
  BIC:             -2832.45

🔧 Estimated Parameters:
  omega          : 0.00000543
  alpha[1]       : 0.09876543
  beta[1]        : 0.87654321

📊 GARCH Metrics:
  Persistence (α+β): 0.975309
  ⚠️  High persistence: Shocks last a long time
  Long-run volatility: 2.0145%

📉 Conditional Volatility:
  Mean:    2.0234%
  Std Dev: 0.4567%
  Min:     1.2345%
  Max:     4.5678%
  Current: 1.9876%

🔍 Standardized Residuals:
  Mean:     -0.0012 (should be ~0)
  Std Dev:  0.9987 (should be ~1)
  ✅ Mean close to 0
  ✅ Std dev close to 1
======================================================================

TEST 4: Detect Volatility Clustering
======================================================================

ACF of Squared Returns (tests for volatility clustering):
  Lag 1: 0.1234
  Lag 5: 0.0567
  Lag 10: 0.0234

✅ Significant autocorrelation → Volatility clustering present!
   → GARCH is appropriate
```

---

## 📊 Step 4: Understanding Results (15 minutes)

### Interpreting GARCH Parameters

```python
ω = 0.00000543
α = 0.098765
β = 0.876543
```

**What this means:**

1. **α = 0.10**: 10% weight on yesterday's shock
   - If yesterday had a big move → today's volatility ↑

2. **β = 0.88**: 88% weight on yesterday's volatility
   - Yesterday's volatility carries forward strongly

3. **α + β = 0.98**: Very high persistence!
   - Volatility shocks die out very slowly
   - Takes weeks for volatility to return to normal

4. **Long-run volatility**:
   ```
   σ̄ = √(ω / (1 - α - β))
      = √(0.00000543 / 0.025)
      = 1.47%
   ```

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Understood volatility clustering
✅ Learned GARCH model theory
✅ Implemented GARCH(1,1) - the workhorse model
✅ Fitted GARCH to real return data
✅ Extracted conditional (time-varying) volatility
✅ Compared Normal vs Student's t distributions
✅ Diagnosed model fit quality
✅ Understood persistence and mean reversion

---

## 🐛 Troubleshooting

### Issue 1: "Convergence not achieved"

**Solutions**:
- Use more data (at least 250 observations)
- Remove extreme outliers
- Try different starting values

### Issue 2: Persistence > 1

**This means**:
- Model is non-stationary
- Infinite unconditional variance
- Consider IGARCH or check data quality

### Issue 3: Very high/low volatility estimates

**Check**:
- Are returns in decimal or percentage? (rescale if needed)
- Remove data errors or extreme events

---

## 🎯 Homework / Practice

### Exercise 1: Compare GARCH Across Stocks

```python
# Fit GARCH(1,1) to different stocks
# Compare persistence (α + β)
# Which stocks have highest persistence?
```

### Exercise 2: Plot Conditional Volatility

```python
import matplotlib.pyplot as plt

# Plot returns and volatility together
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(returns.index, returns, label='Returns')
ax1.set_title('Daily Returns')

ax2.plot(cond_vol.index, cond_vol, label='GARCH Volatility', color='red')
ax2.set_title('Conditional Volatility')

plt.tight_layout()
plt.show()
```

### Exercise 3: Volatility During Crisis

```python
# Fit GARCH to COVID period (March 2020)
# Compare volatility to normal periods
```

---

## 🔜 Coming Up in Day 009

Tomorrow you'll learn:
- **GARCH Forecasting**: Multi-day volatility forecasts
- **VaR from GARCH**: Using forecasted volatility
- **EGARCH**: Asymmetric volatility (leverage effect)
- **Model Selection**: Choosing best GARCH specification

**File you'll update**: `src/models/garch_model.py` (Part 2)

---

**Amazing work! You've mastered GARCH basics! 📊**
