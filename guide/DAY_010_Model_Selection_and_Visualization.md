# Day 010: Model Selection & Visualization

**Duration**: 2 hours
**Difficulty**: Intermediate
**Prerequisites**: Completed Day 001-009

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Implement automatic GARCH model selection
- Build a grid search for optimal (p,q) orders
- Compare GARCH, EGARCH, and GJR-GARCH
- Create visualization functions for VaR and volatility
- Build a comprehensive model comparison framework

---

## 🎯 Key Concepts

### Model Selection
- AIC/BIC criteria
- Grid search optimization
- Cross-validation for time series
- Out-of-sample testing

### Visualization
- VaR comparison charts
- Volatility time series
- ACF/PACF plots
- Distribution plots with VaR lines

---

## 💻 Implementation

Add to `src/models/garch_model.py`:

```python
class GARCHModelSelector:
    """Automatic GARCH model selection"""

    def __init__(self):
        self.best_model = None
        self.best_params = None
        self.results = []

    def find_best_model(
        self,
        returns: pd.Series,
        max_p: int = 3,
        max_q: int = 3,
        distributions: list = ['normal', 't']
    ) -> Tuple[GARCHForecaster, Dict]:
        """
        Find best GARCH model based on AIC

        Args:
            returns: Return series
            max_p: Maximum p value
            max_q: Maximum q value
            distributions: Distributions to test

        Returns:
            Tuple of (best_model, best_params)
        """

        logger.info("Searching for best GARCH model...")

        best_aic = np.inf
        best_model = None
        best_params = {}

        for p in range(1, max_p + 1):
            for q in range(1, max_q + 1):
                for dist in distributions:
                    try:
                        model = GARCHForecaster(p=p, q=q, dist=dist)
                        model.fit(returns)

                        aic = model.results['aic']

                        self.results.append({
                            'p': p,
                            'q': q,
                            'dist': dist,
                            'aic': aic,
                            'bic': model.results['bic']
                        })

                        if aic < best_aic:
                            best_aic = aic
                            best_model = model
                            best_params = {'p': p, 'q': q, 'dist': dist, 'aic': aic}

                    except:
                        continue

        logger.info(f"Best model: GARCH({best_params['p']},{best_params['q']}) "
                   f"with {best_params['dist']} distribution")

        self.best_model = best_model
        self.best_params = best_params

        return best_model, best_params

    def get_results_summary(self) -> pd.DataFrame:
        """Get summary of all tested models"""
        return pd.DataFrame(self.results).sort_values('aic')
```

Create `src/utils/visualization.py`:

```python
"""
Visualization Module
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from typing import Optional

def plot_var_comparison(
    returns: pd.Series,
    var_methods: dict,
    save_path: Optional[str] = None
):
    """
    Plot VaR comparison across methods

    Args:
        returns: Return series
        var_methods: Dict of {method_name: var_value}
        save_path: Optional path to save
    """

    fig = go.Figure()

    # Add returns histogram
    fig.add_trace(go.Histogram(
        x=returns * 100,
        name='Returns Distribution',
        nbinsx=50
    ))

    # Add VaR lines
    colors = ['red', 'orange', 'purple', 'green', 'blue']
    for (name, var_value), color in zip(var_methods.items(), colors):
        var_pct = -(var_value / 1000000) * 100  # Convert to percentage
        fig.add_vline(
            x=var_pct,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{name}: {var_pct:.2f}%"
        )

    fig.update_layout(
        title="VaR Comparison Across Methods",
        xaxis_title="Return (%)",
        yaxis_title="Frequency",
        showlegend=True
    )

    if save_path:
        fig.write_html(save_path)
    else:
        fig.show()

def plot_volatility_timeseries(
    returns: pd.Series,
    volatility: pd.Series,
    save_path: Optional[str] = None
):
    """Plot returns and volatility together"""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))

    # Returns
    ax1.plot(returns.index, returns * 100, alpha=0.7)
    ax1.set_title('Daily Returns', fontsize=14)
    ax1.set_ylabel('Return (%)')
    ax1.grid(True, alpha=0.3)

    # Volatility
    ax2.plot(volatility.index, volatility, color='red', linewidth=2)
    ax2.set_title('GARCH Conditional Volatility', fontsize=14)
    ax2.set_ylabel('Volatility (%)')
    ax2.set_xlabel('Date')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
```

---

## 🧪 Test All Methods

Create `test_complete_system.py`:

```python
"""
Test Complete VaR System - Days 1-10
"""

import sys
sys.path.append('src')

from data.data_collector import DataCollector
from data.preprocessor import DataPreprocessor
from models.var_calculator import VaRCalculator
from models.arima_model import ARIMAForecaster
from models.garch_model import GARCHForecaster, GARCHModelSelector

print("="*70)
print("COMPLETE VAR SYSTEM TEST")
print("="*70)

# 1. Data Collection
collector = DataCollector()
data = collector.fetch_stock_data("AAPL", period="2y")
print("✅ Data collected")

# 2. Preprocessing
preprocessor = DataPreprocessor()
returns_data = preprocessor.prepare_returns_data(data)
returns = returns_data['Returns']
print("✅ Data preprocessed")

# 3. VaR Methods
var_calc = VaRCalculator(confidence_level=0.95)

var_historical = var_calc.historical_var(returns, 1000000)
var_parametric = var_calc.parametric_var(returns, 1000000)
var_montecarlo = var_calc.monte_carlo_var(returns, 1000000, simulations=10000)

print("✅ VaR methods calculated")
print(f"   Historical:  ${var_historical['VaR']:,.2f}")
print(f"   Parametric:  ${var_parametric['VaR']:,.2f}")
print(f"   Monte Carlo: ${var_montecarlo['VaR']:,.2f}")

# 4. ARIMA Forecast
arima = ARIMAForecaster(order=(1,0,1))
arima.fit(returns, optimize=True)
forecast_arima = arima.forecast(steps=10)
print(f"✅ ARIMA forecasted: {len(forecast_arima)} steps")

# 5. GARCH Volatility
garch = GARCHForecaster(p=1, q=1)
garch.fit(returns)
forecast_garch = garch.forecast(horizon=10)
var_garch = garch.calculate_var(forecast_garch['Volatility'])

print(f"✅ GARCH volatility forecast")
print(f"   1-day VaR:  ${var_garch.iloc[0]:,.2f}")
print(f"   10-day VaR: ${var_garch.iloc[9]:,.2f}")

# 6. Model Selection
selector = GARCHModelSelector()
best_garch, params = selector.find_best_model(returns, max_p=2, max_q=2)
print(f"✅ Best GARCH: ({params['p']},{params['q']}) {params['dist']}")

print("\n" + "="*70)
print("🎉 COMPLETE SYSTEM WORKING!")
print("="*70)
```

---

## ✅ Week 2 Complete!

### What You Built (Days 6-10):

✅ **Day 006**: Stationarity testing (ADF test)
✅ **Day 007**: ARIMA forecasting
✅ **Day 008**: GARCH volatility basics
✅ **Day 009**: GARCH forecasting & VaR
✅ **Day 010**: Model selection & visualization

### Total Capabilities:
- 6 VaR methods
- ARIMA return forecasting
- GARCH volatility modeling
- Automatic model selection
- Comprehensive visualization

---

## 🔜 Coming Up in Week 3 (Days 11-15)

- Backtesting framework
- Statistical tests (Kupiec, Christoffersen)
- Basel Traffic Light system
- Advanced risk metrics (CVaR, Sharpe, Max Drawdown)
- Stress testing

---

**Congratulations on completing Week 2! 🚀**
