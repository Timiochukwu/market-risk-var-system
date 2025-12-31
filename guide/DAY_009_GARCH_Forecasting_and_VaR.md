# Day 009: GARCH Model - Part 2 (Forecasting & VaR)

**Duration**: 2 hours
**Difficulty**: Intermediate-Advanced
**Prerequisites**: Completed Day 001-008

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Generate multi-step GARCH volatility forecasts
- Calculate GARCH-based VaR
- Implement EGARCH for leverage effects
- Compare analytical vs simulation forecasts
- Integrate GARCH with your VaR calculator
- Understand when GARCH outperforms constant volatility VaR

---

## 🎯 Key Concepts

### Volatility Forecasting
- Multi-horizon volatility predictions
- Analytical vs Monte Carlo forecasts
- Forecast uncertainty

### GARCH-VaR
- Using forecasted volatility for VaR
- More accurate during volatile periods
- Dynamic risk management

### EGARCH
- Asymmetric volatility response
- Leverage effect modeling
- Better fit for equity returns

---

## 💻 Implementation

Add these methods to your `GARCHForecaster` class in `src/models/garch_model.py`:

```python
def forecast(
    self,
    horizon: int = 10,
    method: str = 'analytic',
    simulations: int = 1000
) -> pd.DataFrame:
    """
    Forecast volatility

    Args:
        horizon: Number of steps ahead
        method: 'analytic' or 'simulation'
        simulations: Number of simulations (if method='simulation')

    Returns:
        DataFrame with variance and volatility forecasts

    Example:
        >>> garch.fit(returns)
        >>> forecast = garch.forecast(horizon=30)
        >>> print(forecast[['Volatility']].head())
    """

    if self.fitted_model is None:
        raise ValueError("Model must be fitted before forecasting")

    logger.info(f"Forecasting {horizon} periods using {method} method...")

    if method == 'analytic':
        # Analytical forecast
        forecasts = self.fitted_model.forecast(horizon=horizon, method='analytic')

        forecast_df = pd.DataFrame({
            'Variance': forecasts.variance.values[-1, :],
            'Volatility': np.sqrt(forecasts.variance.values[-1, :])
        })

    elif method == 'simulation':
        # Simulation-based forecast
        forecasts = self.fitted_model.forecast(
            horizon=horizon,
            method='simulation',
            simulations=simulations
        )

        forecast_df = pd.DataFrame({
            'Variance': forecasts.variance.values[-1, :],
            'Volatility': np.sqrt(forecasts.variance.values[-1, :])
        })

    else:
        raise ValueError(f"Unknown method: {method}")

    # Add horizon index
    forecast_df.index = range(1, horizon + 1)
    forecast_df.index.name = 'Horizon'

    logger.info("Forecast completed")
    logger.info(f"1-step volatility: {forecast_df.iloc[0]['Volatility']:.4f}%")
    logger.info(f"{horizon}-step volatility: {forecast_df.iloc[-1]['Volatility']:.4f}%")

    return forecast_df

def calculate_var(
    self,
    forecast_volatility: pd.Series,
    confidence_level: float = 0.95,
    position_value: float = 1000000
) -> pd.Series:
    """
    Calculate VaR from volatility forecast

    Args:
        forecast_volatility: Forecasted volatility
        confidence_level: Confidence level
        position_value: Position value

    Returns:
        Series with VaR estimates

    Example:
        >>> forecast = garch.forecast(horizon=30)
        >>> var = garch.calculate_var(forecast['Volatility'])
        >>> print(f"10-day VaR: ${var.iloc[9]:,.2f}")
    """

    from scipy import stats

    # Get z-score for confidence level
    z_score = stats.norm.ppf(1 - confidence_level)

    # Calculate VaR (assuming normal distribution)
    # VaR = |z_score| × volatility × position_value / 100
    var = -z_score * forecast_volatility * position_value / 100

    return var
```

---

## 🧪 Test Script

Create `test_garch_forecasting.py`:

```python
import sys
sys.path.append('src')

from data.data_collector import DataCollector
from data.preprocessor import DataPreprocessor
from models.garch_model import GARCHForecaster
from models.var_calculator import VaRCalculator

collector = DataCollector()
preprocessor = DataPreprocessor()

# Fetch data
data = collector.fetch_stock_data("AAPL", period="2y")
returns = preprocessor.prepare_returns_data(data)['Returns']

# Fit GARCH
garch = GARCHForecaster(p=1, q=1)
garch.fit(returns)

# Forecast volatility 30 days
forecast = garch.forecast(horizon=30)
print(forecast.head(10))

# Calculate GARCH-VaR
var_garch = garch.calculate_var(forecast['Volatility'], confidence_level=0.95)
print(f"\n1-day GARCH-VaR: ${var_garch.iloc[0]:,.2f}")
print(f"30-day GARCH-VaR: ${var_garch.iloc[-1]:,.2f}")

# Compare to constant-volatility VaR
var_calc = VaRCalculator(confidence_level=0.95)
var_constant = var_calc.historical_var(returns, position_value=1000000)

print(f"\nConstant Vol VaR: ${var_constant['VaR']:,.2f}")
print(f"GARCH VaR (1-day): ${var_garch.iloc[0]:,.2f}")
print(f"Difference: ${abs(var_constant['VaR'] - var_garch.iloc[0]):,.2f}")
```

---

## ✅ What You Accomplished

✅ Multi-step GARCH volatility forecasts
✅ GARCH-based VaR calculation
✅ Analytical vs simulation forecasting
✅ Integration with VaR calculator
✅ Comparison to constant volatility methods

---

## 🔜 Coming Up in Day 010

- Automatic model selection (GARCH vs EGARCH)
- Grid search for optimal (p,q)
- Model comparison framework
- Visualization module

---

**Excellent work on GARCH forecasting! 🎯**
