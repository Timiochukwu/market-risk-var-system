# Day 007: ARIMA Model - Part 2 (Forecasting)

**Duration**: 2 hours
**Difficulty**: Intermediate
**Prerequisites**: Completed Day 001-006

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Fit ARIMA models to return data
- Automatically optimize (p, d, q) parameters
- Generate multi-step ahead forecasts
- Calculate forecast confidence intervals
- Evaluate forecast accuracy
- Perform residual diagnostics
- Save and load fitted models

---

## 🎯 Learning Objectives

### Financial Concepts:
- **Return Forecasting**: Predicting future returns
- **Forecast Horizon**: How far ahead to predict
- **Confidence Intervals**: Uncertainty bounds
- **In-Sample vs Out-of-Sample**: Training vs testing

### Statistical Concepts:
- **Model Fitting**: Estimating AR and MA parameters
- **AIC/BIC**: Information criteria for model selection
- **Residual Diagnostics**: Checking model adequacy
- **Log-Likelihood**: Measure of model fit

---

## 💡 Understanding ARIMA Components (15 minutes)

### ARIMA(p, d, q) Explained

**ARIMA = AR + I + MA**

#### AR(p) - AutoRegressive
```
Current value depends on past p values

Example: AR(1)
y_t = c + φ₁ y_{t-1} + ε_t

If φ₁ > 0: Positive autocorrelation (momentum)
If φ₁ < 0: Negative autocorrelation (mean reversion)
```

#### I(d) - Integrated (Differencing)
```
d = 0: Use original series (if stationary)
d = 1: Use first difference (for prices → returns)
d = 2: Second difference (rarely needed)
```

#### MA(q) - Moving Average
```
Current value depends on past q forecast errors

Example: MA(1)
y_t = μ + ε_t + θ₁ ε_{t-1}

Uses past errors to improve forecast
```

### Common ARIMA Models for Returns:

| Model | Description | When to Use |
|-------|-------------|-------------|
| **ARIMA(0,0,0)** | White noise | Returns are random |
| **ARIMA(1,0,0)** | AR(1) | Returns have momentum |
| **ARIMA(0,0,1)** | MA(1) | Returns have short memory |
| **ARIMA(1,0,1)** | ARMA(1,1) | **Most common for returns** |
| **ARIMA(2,0,2)** | ARMA(2,2) | Complex patterns |

---

## 💻 Step 1: Implement ARIMA Fitting and Forecasting (60 minutes)

### 1.1 Add to `src/models/arima_model.py`

Add these methods to your `ARIMAForecaster` class:

```python
def fit(
    self,
    series: pd.Series,
    optimize: bool = False,
    seasonal: bool = False
) -> None:
    """
    Fit ARIMA model to time series

    Args:
        series: Time series data (should be stationary)
        optimize: If True, automatically find best (p,d,q) using AIC
        seasonal: If True, include seasonal components (not implemented yet)

    Example:
        >>> arima = ARIMAForecaster(order=(1, 0, 1))
        >>> arima.fit(returns)
        >>> # Or auto-optimize:
        >>> arima.fit(returns, optimize=True)
    """

    series_clean = series.dropna()

    if len(series_clean) < 50:
        raise ValueError("Need at least 50 observations to fit ARIMA")

    logger.info(f"Fitting ARIMA{self.order} model to {len(series_clean)} observations...")

    if optimize:
        logger.info("Auto-optimizing ARIMA order...")
        self.order = self._auto_select_order(series_clean)
        self.p, self.d, self.q = self.order
        logger.info(f"Selected order: ARIMA{self.order}")

    try:
        # Fit ARIMA model
        self.model = ARIMA(series_clean, order=self.order)
        self.fitted_model = self.model.fit()

        # Store results
        self.results = {
            'aic': self.fitted_model.aic,
            'bic': self.fitted_model.bic,
            'hqic': self.fitted_model.hqic,
            'loglikelihood': self.fitted_model.llf,
            'num_params': len(self.fitted_model.params),
            'order': self.order
        }

        logger.info(f"Model fitted successfully")
        logger.info(f"AIC: {self.fitted_model.aic:.2f}")
        logger.info(f"BIC: {self.fitted_model.bic:.2f}")
        logger.info(f"Log-Likelihood: {self.fitted_model.llf:.2f}")

    except Exception as e:
        logger.error(f"Error fitting model: {str(e)}")
        raise

def _auto_select_order(
    self,
    series: pd.Series,
    max_p: int = 3,
    max_d: int = 1,
    max_q: int = 3
) -> Tuple[int, int, int]:
    """
    Automatically select best ARIMA order using AIC

    Args:
        series: Time series
        max_p: Maximum AR order to test
        max_d: Maximum differencing order
        max_q: Maximum MA order to test

    Returns:
        Optimal (p, d, q) tuple

    Example (internal use):
        >>> order = self._auto_select_order(returns)
        >>> # Returns: (1, 0, 1)
    """

    logger.info(f"Testing orders: p=[0,{max_p}], d=[0,{max_d}], q=[0,{max_q}]")

    best_aic = np.inf
    best_order = None
    results_list = []

    for p in range(max_p + 1):
        for d in range(max_d + 1):
            for q in range(max_q + 1):
                try:
                    model = ARIMA(series, order=(p, d, q))
                    fitted = model.fit()

                    aic = fitted.aic
                    results_list.append({
                        'p': p,
                        'd': d,
                        'q': q,
                        'aic': aic,
                        'bic': fitted.bic
                    })

                    if aic < best_aic:
                        best_aic = aic
                        best_order = (p, d, q)

                    logger.debug(f"  ARIMA({p},{d},{q}): AIC={aic:.2f}")

                except:
                    continue

    logger.info(f"Best order: ARIMA{best_order} with AIC={best_aic:.2f}")

    return best_order

def forecast(
    self,
    steps: int = 10,
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Generate forecasts with confidence intervals

    Args:
        steps: Number of steps ahead to forecast
        alpha: Significance level for confidence intervals (default: 0.05 for 95% CI)

    Returns:
        DataFrame with forecasts and confidence intervals

    Example:
        >>> arima.fit(returns)
        >>> forecast = arima.forecast(steps=30)
        >>> print(forecast)
        #   Step   Forecast  Lower_CI  Upper_CI
        #      1   0.000812  -0.03894  0.040564
        #      2   0.000756  -0.04125  0.042762
    """

    if self.fitted_model is None:
        raise ValueError("Model must be fitted before forecasting")

    logger.info(f"Forecasting {steps} steps ahead...")

    # Generate forecast
    forecast_result = self.fitted_model.get_forecast(steps=steps)

    # Get forecast values and confidence intervals
    forecast_mean = forecast_result.predicted_mean
    forecast_ci = forecast_result.conf_int(alpha=alpha)

    # Create DataFrame
    forecast_df = pd.DataFrame({
        'Step': range(1, steps + 1),
        'Forecast': forecast_mean.values,
        'Lower_CI': forecast_ci.iloc[:, 0].values,
        'Upper_CI': forecast_ci.iloc[:, 1].values
    })

    # Calculate confidence interval width
    forecast_df['CI_Width'] = forecast_df['Upper_CI'] - forecast_df['Lower_CI']

    logger.info(f"Forecast completed")
    logger.info(f"Mean forecast (step 1): {forecast_mean.iloc[0]:.6f}")
    logger.info(f"95% CI: [{forecast_ci.iloc[0, 0]:.6f}, {forecast_ci.iloc[0, 1]:.6f}]")

    return forecast_df

def get_in_sample_predictions(self) -> pd.Series:
    """
    Get in-sample (fitted) predictions

    Returns:
        Series of in-sample predictions

    Example:
        >>> predictions = arima.get_in_sample_predictions()
        >>> errors = returns - predictions
        >>> mae = abs(errors).mean()
    """

    if self.fitted_model is None:
        raise ValueError("Model must be fitted first")

    return self.fitted_model.fittedvalues

def get_residuals(self) -> pd.Series:
    """
    Get model residuals (forecast errors)

    Residuals = Actual - Predicted

    Returns:
        Series of residuals

    Example:
        >>> residuals = arima.get_residuals()
        >>> print(f"Mean residual: {residuals.mean():.6f}")  # Should be ~0
    """

    if self.fitted_model is None:
        raise ValueError("Model must be fitted first")

    return self.fitted_model.resid

def diagnose_residuals(self) -> Dict[str, any]:
    """
    Perform residual diagnostics

    Good residuals should be:
    - Mean ≈ 0
    - Constant variance (homoskedastic)
    - No autocorrelation (white noise)
    - Approximately normally distributed

    Returns:
        Dictionary with diagnostic statistics

    Example:
        >>> diagnostics = arima.diagnose_residuals()
        >>> print(f"Residuals pass tests: {diagnostics['all_good']}")
    """

    if self.fitted_model is None:
        raise ValueError("Model must be fitted first")

    residuals = self.get_residuals()

    # Basic statistics
    mean = residuals.mean()
    std = residuals.std()
    skewness = residuals.skew()
    kurtosis = residuals.kurtosis()

    # Test for autocorrelation
    # Ljung-Box test: H0 = no autocorrelation
    from statsmodels.stats.diagnostic import acorr_ljungbox
    lb_test = acorr_ljungbox(residuals, lags=[10], return_df=True)
    lb_pvalue = lb_test['lb_pvalue'].iloc[0]

    # Test for normality
    # Jarque-Bera test: H0 = normal distribution
    from scipy.stats import jarque_bera
    jb_stat, jb_pvalue = jarque_bera(residuals)

    diagnostics = {
        'mean': mean,
        'std': std,
        'skewness': skewness,
        'kurtosis': kurtosis,
        'ljung_box_pvalue': lb_pvalue,
        'jarque_bera_pvalue': jb_pvalue,
        'autocorrelation_ok': lb_pvalue > 0.05,
        'normality_ok': jb_pvalue > 0.05,
        'mean_ok': abs(mean) < 0.001,
        'all_good': (lb_pvalue > 0.05 and abs(mean) < 0.001)
    }

    return diagnostics

def print_diagnostics(self):
    """
    Print comprehensive model diagnostics

    Example:
        >>> arima.fit(returns)
        >>> arima.print_diagnostics()
    """

    if self.fitted_model is None:
        raise ValueError("Model must be fitted first")

    print("\n" + "="*70)
    print(f"ARIMA{self.order} MODEL DIAGNOSTICS")
    print("="*70)

    # Model parameters
    print(f"\n📊 Model Information:")
    print(f"  Order (p,d,q):   {self.order}")
    print(f"  Parameters:      {self.results['num_params']}")
    print(f"  Observations:    {self.fitted_model.nobs}")
    print(f"  AIC:             {self.results['aic']:.2f}")
    print(f"  BIC:             {self.results['bic']:.2f}")
    print(f"  Log-Likelihood:  {self.results['loglikelihood']:.2f}")

    # Coefficients
    print(f"\n📈 Estimated Coefficients:")
    for name, value in self.fitted_model.params.items():
        print(f"  {name:15s}: {value:>10.6f}")

    # Residual diagnostics
    print(f"\n🔍 Residual Diagnostics:")
    diagnostics = self.diagnose_residuals()

    print(f"  Mean:            {diagnostics['mean']:.6f} {'✅' if diagnostics['mean_ok'] else '❌'}")
    print(f"  Std Dev:         {diagnostics['std']:.6f}")
    print(f"  Skewness:        {diagnostics['skewness']:.4f}")
    print(f"  Kurtosis:        {diagnostics['kurtosis']:.4f}")

    print(f"\n📊 Statistical Tests:")
    print(f"  Ljung-Box (p={diagnostics['ljung_box_pvalue']:.4f}): ", end='')
    if diagnostics['autocorrelation_ok']:
        print("✅ No autocorrelation (good)")
    else:
        print("❌ Autocorrelation present (bad)")

    print(f"  Jarque-Bera (p={diagnostics['jarque_bera_pvalue']:.4f}): ", end='')
    if diagnostics['normality_ok']:
        print("✅ Normally distributed (good)")
    else:
        print("⚠️  Not normal (acceptable for returns)")

    print(f"\n📖 Overall Assessment:")
    if diagnostics['all_good']:
        print("  ✅ Model passes diagnostic checks")
        print("  ✅ Residuals are well-behaved")
    else:
        print("  ⚠️  Model may need improvement")
        if not diagnostics['autocorrelation_ok']:
            print("  → Consider higher order ARIMA")
        if not diagnostics['mean_ok']:
            print("  → Check model specification")

    print("="*70 + "\n")

def save_model(self, filepath: str):
    """
    Save fitted model to file

    Args:
        filepath: Path to save model

    Example:
        >>> arima.fit(returns)
        >>> arima.save_model('arima_model.pkl')
    """

    if self.fitted_model is None:
        raise ValueError("Model must be fitted before saving")

    import pickle

    model_data = {
        'fitted_model': self.fitted_model,
        'order': self.order,
        'results': self.results
    }

    with open(filepath, 'wb') as f:
        pickle.dump(model_data, f)

    logger.info(f"Model saved to: {filepath}")

def load_model(self, filepath: str):
    """
    Load fitted model from file

    Args:
        filepath: Path to load model from

    Example:
        >>> arima = ARIMAForecaster()
        >>> arima.load_model('arima_model.pkl')
        >>> forecast = arima.forecast(steps=10)
    """

    import pickle

    with open(filepath, 'rb') as f:
        model_data = pickle.load(f)

    self.fitted_model = model_data['fitted_model']
    self.order = model_data['order']
    self.p, self.d, self.q = self.order
    self.results = model_data['results']

    logger.info(f"Model loaded from: {filepath}")
    logger.info(f"Order: ARIMA{self.order}")
```

---

## 🧪 Step 2: Test ARIMA Forecasting (25 minutes)

### 2.1 Create Test Script `test_arima_forecasting.py`

```python
"""
Test ARIMA Forecasting
"""

import sys
sys.path.append('src')

from data.data_collector import DataCollector
from data.preprocessor import DataPreprocessor
from models.arima_model import ARIMAForecaster
import pandas as pd
import numpy as np

print("="*70)
print("Testing ARIMA Forecasting")
print("="*70)

# Fetch data
print("\n📥 Fetching data...")
collector = DataCollector()
data = collector.fetch_stock_data("AAPL", period="2y")

preprocessor = DataPreprocessor()
returns_data = preprocessor.prepare_returns_data(data)
returns = returns_data['Returns'].dropna()

print(f"Total observations: {len(returns)}")

# Test 1: Fit ARIMA(1,0,1)
print("\n" + "="*70)
print("TEST 1: Fit ARIMA(1,0,1) Model")
print("="*70)

arima = ARIMAForecaster(order=(1, 0, 1))
arima.fit(returns)

# Print diagnostics
arima.print_diagnostics()

# Test 2: Generate forecasts
print("\n" + "="*70)
print("TEST 2: Generate 30-Day Forecast")
print("="*70)

forecast = arima.forecast(steps=30)

print("\n" + forecast.head(10).to_string(index=False))
print(f"\n... ({len(forecast)} total forecasts)")

# Test 3: Auto-optimize order
print("\n" + "="*70)
print("TEST 3: Auto-Optimize ARIMA Order")
print("="*70)

arima_auto = ARIMAForecaster()
arima_auto.fit(returns, optimize=True)

print(f"\nOptimal order found: ARIMA{arima_auto.order}")
print(f"AIC: {arima_auto.results['aic']:.2f}")
print(f"BIC: {arima_auto.results['bic']:.2f}")

# Test 4: Compare different orders
print("\n" + "="*70)
print("TEST 4: Compare Different ARIMA Orders")
print("="*70)

orders_to_test = [(0,0,0), (1,0,0), (0,0,1), (1,0,1), (2,0,2)]
comparison = []

for order in orders_to_test:
    try:
        model = ARIMAForecaster(order=order)
        model.fit(returns)

        comparison.append({
            'Order': f"ARIMA{order}",
            'AIC': model.results['aic'],
            'BIC': model.results['bic'],
            'Params': model.results['num_params']
        })
    except:
        pass

comparison_df = pd.DataFrame(comparison).sort_values('AIC')
print("\n" + comparison_df.to_string(index=False))
print(f"\n✅ Best model: {comparison_df.iloc[0]['Order']}")

# Test 5: In-sample vs Out-of-sample
print("\n" + "="*70)
print("TEST 5: In-Sample vs Out-of-Sample Forecast")
print("="*70)

# Split data
train_size = int(len(returns) * 0.8)
train = returns.iloc[:train_size]
test = returns.iloc[train_size:]

print(f"Training set: {len(train)} observations")
print(f"Test set:     {len(test)} observations")

# Fit on training data
arima_train = ARIMAForecaster(order=(1, 0, 1))
arima_train.fit(train)

# Forecast
forecast_test = arima_train.forecast(steps=len(test))

# Calculate errors
actual = test.values
predicted = forecast_test['Forecast'].values[:len(actual)]

mae = np.mean(np.abs(actual - predicted))
rmse = np.sqrt(np.mean((actual - predicted) ** 2))

print(f"\nForecast Accuracy:")
print(f"  MAE (Mean Absolute Error):  {mae:.6f}")
print(f"  RMSE (Root Mean Squared):   {rmse:.6f}")
print(f"  Actual volatility (std):    {test.std():.6f}")

# Test 6: Save and load model
print("\n" + "="*70)
print("TEST 6: Save and Load Model")
print("="*70)

arima.save_model('arima_model.pkl')
print("✅ Model saved")

# Load model
arima_loaded = ARIMAForecaster()
arima_loaded.load_model('arima_model.pkl')
print("✅ Model loaded")

# Test that loaded model works
forecast_loaded = arima_loaded.forecast(steps=5)
print(f"\nForecast from loaded model:")
print(forecast_loaded.to_string(index=False))

print("\n" + "="*70)
print("✅ All tests completed!")
print("="*70)
```

### 2.2 Run the Test

```bash
python test_arima_forecasting.py
```

### 2.3 Expected Output

```
======================================================================
TEST 1: Fit ARIMA(1,0,1) Model
======================================================================

======================================================================
ARIMA(1, 0, 1) MODEL DIAGNOSTICS
======================================================================

📊 Model Information:
  Order (p,d,q):   (1, 0, 1)
  Parameters:      3
  Observations:    503
  AIC:             -2845.67
  BIC:             -2832.45
  Log-Likelihood:  1425.84

📈 Estimated Coefficients:
  const          :   0.000823
  ar.L1          :   0.234567
  ma.L1          :  -0.123456

🔍 Residual Diagnostics:
  Mean:            -0.000002 ✅
  Std Dev:         0.019876
  Skewness:        0.2145
  Kurtosis:        3.8901

📊 Statistical Tests:
  Ljung-Box (p=0.8765): ✅ No autocorrelation (good)
  Jarque-Bera (p=0.0234): ⚠️  Not normal (acceptable for returns)

📖 Overall Assessment:
  ✅ Model passes diagnostic checks
  ✅ Residuals are well-behaved

======================================================================
TEST 4: Compare Different ARIMA Orders
======================================================================

         Order      AIC      BIC  Params
   ARIMA(1, 0, 1)  -2845.67  -2832.45       3
   ARIMA(2, 0, 2)  -2843.12  -2824.56       5
   ARIMA(1, 0, 0)  -2838.90  -2829.34       2
   ARIMA(0, 0, 1)  -2837.45  -2827.89       2
   ARIMA(0, 0, 0)  -2802.34  -2796.12       1

✅ Best model: ARIMA(1, 0, 1)

======================================================================
TEST 5: In-Sample vs Out-of-Sample Forecast
======================================================================

Training set: 402 observations
Test set:     101 observations

Forecast Accuracy:
  MAE (Mean Absolute Error):  0.015234
  RMSE (Root Mean Squared):   0.019876
  Actual volatility (std):    0.020145
```

---

## 📊 Step 3: Understanding Forecast Results (15 minutes)

### Interpreting Forecasts

```python
forecast = arima.forecast(steps=30)

#    Step   Forecast  Lower_CI  Upper_CI  CI_Width
# 0     1   0.000812  -0.03894  0.040564  0.079504
# 1     2   0.000756  -0.04125  0.042762  0.084012
# ...
```

**What This Means:**

- **Step 1 (tomorrow)**: Expected return = 0.0812%
- **95% Confidence**: We're 95% sure tomorrow's return will be between -3.894% and +4.056%
- **CI Width increases**: Further out = more uncertainty

### Why Forecasts Revert to Mean

ARIMA forecasts typically converge to the mean:

```
Step  1: Forecast = 0.000812 (uses recent data)
Step  5: Forecast = 0.000798
Step 10: Forecast = 0.000785
Step 30: Forecast = 0.000772 (→ long-run mean)
```

**This is expected!** Returns have weak autocorrelation.

---

## 🔍 Step 4: Experiments (15 minutes)

### Experiment 1: Forecast Horizon Effect

```python
horizons = [1, 5, 10, 30, 60]

for h in horizons:
    forecast = arima.forecast(steps=h)
    ci_width_mean = forecast['CI_Width'].mean()
    print(f"{h:2d}-step forecast: Avg CI width = {ci_width_mean:.6f}")
```

**Observation**: Confidence intervals widen with horizon.

### Experiment 2: Volatile vs Stable Stocks

```python
stocks = [
    ('JNJ', 'Johnson & Johnson (stable)'),
    ('TSLA', 'Tesla (volatile)')
]

for ticker, name in stocks:
    data = collector.fetch_stock_data(ticker, period="1y")
    returns = preprocessor.prepare_returns_data(data)['Returns']

    arima = ARIMAForecaster(order=(1,0,1))
    arima.fit(returns)

    forecast = arima.forecast(steps=10)
    ci_width = forecast.iloc[0]['CI_Width']

    print(f"{ticker}: {name}")
    print(f"  1-step CI width: {ci_width:.6f}\n")
```

**Observation**: Volatile stocks have wider confidence intervals.

### Experiment 3: Model Complexity vs Fit

```python
# Test if more complex models always better
for max_order in [1, 2, 3, 4, 5]:
    arima = ARIMAForecaster()
    arima.fit(returns, optimize=True)  # Will search up to max_order

    print(f"Max order {max_order}: Best = ARIMA{arima.order}, AIC = {arima.results['aic']:.2f}")
```

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Fitted ARIMA models to return data
✅ Automatically optimized (p, d, q) parameters using AIC
✅ Generated multi-step forecasts with confidence intervals
✅ Performed comprehensive residual diagnostics
✅ Evaluated in-sample vs out-of-sample accuracy
✅ Compared different ARIMA specifications
✅ Saved and loaded fitted models
✅ Built a complete ARIMA forecasting pipeline

---

## 🐛 Troubleshooting

### Issue 1: "Model did not converge"

**Solutions**:
- Reduce model complexity (lower p or q)
- Check for outliers in data
- Ensure series is stationary

### Issue 2: Poor forecast accuracy

**This is normal for returns!** Returns are hard to predict.
- MAE close to std dev = reasonable
- ARIMA captures some patterns but not all
- This is why we use GARCH for volatility (Day 008)

### Issue 3: Very wide confidence intervals

**This is expected** for financial returns:
- High volatility = wide intervals
- More uncertainty = wider intervals
- This is realistic, not a problem

---

## 📚 Key Formulas Reference

### AIC (Akaike Information Criterion)
```
AIC = -2 × log(L) + 2k

where:
  L = likelihood
  k = number of parameters

Lower AIC = Better model
```

### BIC (Bayesian Information Criterion)
```
BIC = -2 × log(L) + k × log(n)

where:
  n = number of observations

BIC penalizes complexity more than AIC
```

### ARMA(1,1) Model
```
y_t = c + φ₁ y_{t-1} + θ₁ ε_{t-1} + ε_t

where:
  φ₁ = AR coefficient
  θ₁ = MA coefficient
  ε_t = white noise error
```

---

## 🎯 Homework / Practice

### Exercise 1: Build a Forecast Comparison Function

```python
def compare_forecasts(ticker, orders_list):
    """
    Compare forecast accuracy of different ARIMA orders
    Returns DataFrame with RMSE for each
    """
    # Your code here
    pass
```

### Exercise 2: Rolling Window Forecasts

```python
# Implement rolling window forecasts:
# 1. Fit model on first 252 days
# 2. Forecast next day
# 3. Move window forward
# 4. Repeat
# 5. Compare forecasts to actual
```

### Exercise 3: Combine ARIMA with VaR

```python
# Use ARIMA forecast as input to VaR:
# 1. Forecast next 30 days of returns
# 2. Use forecasted returns for VaR
# 3. Compare to historical VaR
```

---

## 🔜 Coming Up in Day 008

Tomorrow you'll learn:
- **GARCH Models**: Volatility forecasting
- **Conditional Volatility**: Time-varying risk
- **GARCH(1,1)**: Standard specification
- **Volatility Clustering**: Why GARCH works
- **GARCH-VaR**: Combining volatility forecasts with VaR

**File you'll create**: `src/models/garch_model.py`

---

**Excellent work! You've mastered ARIMA forecasting! 🎯**
