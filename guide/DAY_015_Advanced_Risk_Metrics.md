# Day 015: Advanced Risk Metrics

**Duration**: 2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-014

---

## 📋 What You'll Build

- CVaR (Expected Shortfall) calculator
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Advanced metrics API endpoint

---

## 💡 Advanced Risk Metrics

### 1. CVaR (Conditional VaR / Expected Shortfall)

**What it measures**: Average loss beyond VaR

```
VaR (95%): "Won't lose more than $10K with 95% confidence"
CVaR: "IF we breach VaR, expect to lose $15K on average"

CVaR is always ≥ VaR
CVaR better captures tail risk
```

### 2. Sharpe Ratio

**What it measures**: Risk-adjusted return

```
Sharpe = (Return - Risk-Free Rate) / Volatility

Example:
  Annual return: 12%
  Risk-free rate: 2%
  Volatility: 15%
  Sharpe = (0.12 - 0.02) / 0.15 = 0.67

Interpretation:
  > 1.0: Good
  > 2.0: Very good
  > 3.0: Excellent
```

### 3. Sortino Ratio

**What it measures**: Downside risk-adjusted return

```
Sortino = (Return - Risk-Free Rate) / Downside Deviation

Only penalizes downside volatility (losses)
Better than Sharpe for asymmetric returns
```

### 4. Maximum Drawdown

**What it measures**: Largest peak-to-trough decline

```
Example:
  Peak: $100K
  Trough: $70K
  Max Drawdown: -30%

Shows worst historical loss
Important for risk tolerance
```

### 5. Calmar Ratio

**What it measures**: Return relative to max drawdown

```
Calmar = Annual Return / |Max Drawdown|

Example:
  Annual return: 15%
  Max drawdown: 20%
  Calmar = 0.15 / 0.20 = 0.75

Higher is better
```

---

## 💻 Implementation

Create `src/utils/advanced_metrics.py`:

```python
"""
Advanced Risk Metrics Module
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95,
    position_value: float = 1000000
) -> Dict[str, float]:
    """Calculate CVaR (Expected Shortfall)"""
    
    alpha = 1 - confidence_level
    var_percentile = returns.quantile(alpha)
    
    # Returns worse than VaR
    tail_returns = returns[returns <= var_percentile]
    
    cvar_percentile = tail_returns.mean()
    cvar = -cvar_percentile * position_value
    
    return {
        'CVaR': cvar,
        'CVaR_Percentage': -cvar_percentile * 100,
        'Tail_Observations': len(tail_returns)
    }


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """Calculate annualized Sharpe ratio"""
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    sharpe = np.sqrt(periods_per_year) * excess_returns.mean() / returns.std()
    
    return sharpe


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """Calculate Sortino ratio (downside deviation)"""
    
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    # Only negative returns
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std()
    
    if downside_std == 0:
        return np.inf
    
    sortino = np.sqrt(periods_per_year) * excess_returns.mean() / downside_std
    
    return sortino


def calculate_max_drawdown(returns: pd.Series) -> Dict[str, float]:
    """Calculate maximum drawdown"""
    
    # Cumulative returns
    cum_returns = (1 + returns).cumprod()
    
    # Running maximum
    running_max = cum_returns.expanding().max()
    
    # Drawdown
    drawdown = (cum_returns - running_max) / running_max
    
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin()
    
    return {
        'Max_Drawdown': max_dd,
        'Max_Drawdown_Pct': max_dd * 100,
        'Max_Drawdown_Date': max_dd_date
    }


def calculate_calmar_ratio(
    returns: pd.Series,
    periods_per_year: int = 252
) -> float:
    """Calculate Calmar ratio"""
    
    annual_return = returns.mean() * periods_per_year
    max_dd = calculate_max_drawdown(returns)['Max_Drawdown']
    
    if max_dd == 0:
        return np.inf
    
    calmar = annual_return / abs(max_dd)
    
    return calmar


def calculate_all_metrics(
    returns: pd.Series,
    position_value: float = 1000000,
    confidence_level: float = 0.95,
    risk_free_rate: float = 0.02
) -> Dict[str, any]:
    """Calculate all advanced metrics"""
    
    cvar = calculate_cvar(returns, confidence_level, position_value)
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
    sortino = calculate_sortino_ratio(returns, risk_free_rate)
    max_dd = calculate_max_drawdown(returns)
    calmar = calculate_calmar_ratio(returns)
    
    return {
        'CVaR': cvar['CVaR'],
        'CVaR_Percentage': cvar['CVaR_Percentage'],
        'Sharpe_Ratio': sharpe,
        'Sortino_Ratio': sortino,
        'Max_Drawdown': max_dd['Max_Drawdown'],
        'Max_Drawdown_Pct': max_dd['Max_Drawdown_Pct'],
        'Calmar_Ratio': calmar,
        'Annual_Return': returns.mean() * 252,
        'Annual_Volatility': returns.std() * np.sqrt(252)
    }
```

---

## 🧪 Test with curl

Add this endpoint to `src/api/main.py`:

```python
@app.post("/api/v1/metrics/advanced")
async def calculate_advanced_metrics(request: DataRequest):
    """Calculate advanced risk metrics"""
    
    from utils.advanced_metrics import calculate_all_metrics
    
    data = data_collector.fetch_stock_data(request.ticker, period="2y")
    returns = preprocessor.prepare_returns_data(data)['Returns']
    
    metrics = calculate_all_metrics(returns)
    
    return metrics
```

### Test Advanced Metrics:

```bash
# Get all advanced metrics for AAPL
curl -X POST "http://localhost:8000/api/v1/metrics/advanced" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}' | jq '.'
```

**Expected Response**:
```json
{
  "CVaR": 38456.78,
  "CVaR_Percentage": 3.85,
  "Sharpe_Ratio": 0.89,
  "Sortino_Ratio": 1.23,
  "Max_Drawdown": -0.28,
  "Max_Drawdown_Pct": -28.0,
  "Calmar_Ratio": 0.71,
  "Annual_Return": 0.20,
  "Annual_Volatility": 0.32
}
```

### Compare Stocks:

```bash
for ticker in AAPL MSFT GOOGL TSLA JNJ; do
  echo "\n=== $ticker ==="
  curl -s -X POST "http://localhost:8000/api/v1/metrics/advanced" \
    -d "{\"ticker\": \"$ticker\"}" -H "Content-Type: application/json" \
    | jq '{ticker: "'$ticker'", sharpe: .Sharpe_Ratio, max_dd: .Max_Drawdown_Pct}'
done
```

---

## ✅ Week 3 Complete!

You've built:

✅ Complete backtesting framework
✅ Kupiec POF test
✅ Christoffersen independence test
✅ Basel Traffic Light system
✅ Advanced risk metrics (CVaR, Sharpe, Sortino, Max DD, Calmar)

**Total system capabilities**: 
- 6 VaR methods
- ARIMA & GARCH forecasting
- Full statistical backtesting
- Regulatory compliance framework
- Advanced risk metrics

---

## 🔜 Coming Up (Days 16-20)

- Portfolio VaR with correlation
- Stress testing & scenarios
- Report generation (Excel/HTML)
- Email alerts
- Task scheduling

**Next**: Portfolio Risk Analysis (Day 016)
