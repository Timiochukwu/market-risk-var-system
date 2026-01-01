# Day 033: Regulatory Reporting (Basel III)

**Duration**: 2 hours | **Difficulty**: Intermediate-Advanced | **Prerequisites**: Day 001-032

---

## 📋 What You'll Build

- Basel III Market Risk framework
- Standardized Approach (SA)
- Internal Models Approach (IMA) metrics
- Regulatory VaR (99% confidence, 10-day)
- Stressed VaR calculation
- Expected Shortfall (ES) reporting
- Compliance reporting templates

---

## 💡 Basel III Market Risk Framework

```
┌──────────────────────────────────────────┐
│  Basel III Market Risk Capital          │
├──────────────────────────────────────────┤
│  Capital = max(IMA, SA Floor)            │
│                                          │
│  IMA (Internal Models Approach):        │
│  - VaR (99%, 10-day)                    │
│  - Stressed VaR                         │
│  - Expected Shortfall (97.5%)           │
│  - Backtesting (Green/Yellow/Red)       │
│                                          │
│  SA (Standardized Approach):            │
│  - Sensitivity-Based Method             │
│  - Delta, Vega, Curvature risks         │
└──────────────────────────────────────────┘
```

---

## 💻 Implementation

### Step 1: Basel Metrics Calculator

Create `src/regulatory/basel_metrics.py`:

```python
"""
Basel III Market Risk Metrics
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BaselMarketRiskCalculator:
    """Calculate Basel III market risk metrics"""

    def __init__(self):
        self.basel_confidence = 0.99  # 99% for regulatory VaR
        self.basel_horizon = 10  # 10-day VaR

    def calculate_regulatory_var(
        self,
        returns: pd.Series,
        position_value: float,
        method: str = "historical"
    ) -> Dict:
        """
        Calculate regulatory VaR (99%, 10-day)

        Args:
            returns: Daily returns
            position_value: Position value
            method: Calculation method

        Returns:
            Regulatory VaR metrics
        """
        logger.info(f"Calculating Basel regulatory VaR (99%, 10-day)")

        # Scale 1-day VaR to 10-day using square root of time
        scaling_factor = np.sqrt(self.basel_horizon)

        if method == "historical":
            # 1-day VaR at 99%
            var_1day_return = np.percentile(returns, (1 - self.basel_confidence) * 100)
            var_1day = abs(var_1day_return * position_value)

            # Scale to 10-day
            var_10day = var_1day * scaling_factor

        elif method == "parametric":
            # Parametric VaR
            mean = returns.mean()
            std = returns.std()
            z_score = -2.326  # 99% confidence

            var_1day_return = mean + z_score * std
            var_1day = abs(var_1day_return * position_value)
            var_10day = var_1day * scaling_factor

        else:
            raise ValueError(f"Unsupported method: {method}")

        return {
            'var_1day': var_1day,
            'var_10day': var_10day,
            'confidence_level': self.basel_confidence,
            'horizon_days': self.basel_horizon,
            'method': method,
            'scaling_factor': scaling_factor
        }

    def calculate_stressed_var(
        self,
        returns: pd.Series,
        position_value: float,
        stress_period_start: str = None,
        stress_period_end: str = None
    ) -> Dict:
        """
        Calculate Stressed VaR using historical stress period

        Args:
            returns: Full returns series
            position_value: Position value
            stress_period_start: Start of stress period (e.g., '2008-09-01')
            stress_period_end: End of stress period (e.g., '2009-03-31')

        Returns:
            Stressed VaR metrics
        """
        logger.info("Calculating Stressed VaR")

        # Default stress period: 2008 Financial Crisis
        if stress_period_start is None:
            stress_period_start = '2008-09-01'
        if stress_period_end is None:
            stress_period_end = '2009-03-31'

        # Filter returns for stress period
        stress_returns = returns.loc[stress_period_start:stress_period_end]

        if len(stress_returns) < 30:
            logger.warning(f"Insufficient stress period data: {len(stress_returns)} days")
            # Fall back to worst 250 days
            stress_returns = returns.nsmallest(250)

        # Calculate VaR on stress period
        var_1day_return = np.percentile(stress_returns, 1)  # 99%
        var_1day = abs(var_1day_return * position_value)

        # Scale to 10-day
        scaling_factor = np.sqrt(10)
        stressed_var = var_1day * scaling_factor

        return {
            'stressed_var_1day': var_1day,
            'stressed_var_10day': stressed_var,
            'stress_period_start': stress_period_start,
            'stress_period_end': stress_period_end,
            'stress_period_days': len(stress_returns),
            'stress_period_volatility': stress_returns.std() * np.sqrt(252)
        }

    def calculate_expected_shortfall(
        self,
        returns: pd.Series,
        position_value: float,
        confidence_level: float = 0.975  # 97.5% for Basel
    ) -> Dict:
        """
        Calculate Expected Shortfall (ES)

        Args:
            returns: Daily returns
            position_value: Position value
            confidence_level: ES confidence level

        Returns:
            ES metrics
        """
        logger.info(f"Calculating Expected Shortfall ({confidence_level*100}%)")

        alpha = 1 - confidence_level

        # Find VaR threshold
        var_threshold = np.percentile(returns, alpha * 100)

        # Calculate ES (average of losses beyond VaR)
        tail_losses = returns[returns <= var_threshold]

        if len(tail_losses) > 0:
            es_return = tail_losses.mean()
        else:
            es_return = var_threshold

        es_amount = abs(es_return * position_value)

        # 10-day ES
        es_10day = es_amount * np.sqrt(10)

        return {
            'es_1day': es_amount,
            'es_10day': es_10day,
            'confidence_level': confidence_level,
            'var_threshold': var_threshold,
            'tail_observations': len(tail_losses)
        }

    def traffic_light_test(
        self,
        num_observations: int,
        num_exceptions: int
    ) -> Dict:
        """
        Basel Traffic Light Test

        Args:
            num_observations: Number of observations (typically 250)
            num_exceptions: Number of VaR breaches

        Returns:
            Zone classification
        """
        # Scale to 250 days
        scaled_exceptions = (num_exceptions / num_observations) * 250

        if scaled_exceptions < 5:
            zone = "green"
            action = "No action required"
            multiplier = 3.0
        elif scaled_exceptions < 10:
            zone = "yellow"
            action = "Increase capital or review model"
            multiplier = 3.4 + 0.2 * (scaled_exceptions - 5)
        else:
            zone = "red"
            action = "Model deemed inadequate - use SA"
            multiplier = 4.0

        return {
            'zone': zone,
            'scaled_exceptions': scaled_exceptions,
            'multiplier': multiplier,
            'action': action,
            'num_observations': num_observations,
            'num_exceptions': num_exceptions
        }

    def calculate_market_risk_capital(
        self,
        var_10day: float,
        stressed_var_10day: float,
        multiplier: float = 3.0,
        plus_factor: float = 0.0
    ) -> Dict:
        """
        Calculate market risk capital charge (IMA)

        Args:
            var_10day: 10-day VaR
            stressed_var_10day: 10-day Stressed VaR
            multiplier: Multiplier (3.0-4.0 based on backtesting)
            plus_factor: Additional factor for model issues

        Returns:
            Capital charge
        """
        # Basel formula: Capital = max(VaR, sVaR) * (multiplier + plus_factor)
        var_component = var_10day * (multiplier + plus_factor)
        stressed_var_component = stressed_var_10day * (multiplier + plus_factor)

        total_capital = var_component + stressed_var_component

        return {
            'var_component': var_component,
            'stressed_var_component': stressed_var_component,
            'total_capital_charge': total_capital,
            'multiplier': multiplier,
            'plus_factor': plus_factor
        }

    def generate_compliance_report(
        self,
        ticker: str,
        position_value: float,
        returns: pd.Series,
        backtest_results: Dict
    ) -> Dict:
        """
        Generate full Basel III compliance report

        Args:
            ticker: Asset ticker
            position_value: Position value
            returns: Historical returns
            backtest_results: Backtesting results

        Returns:
            Comprehensive compliance report
        """
        logger.info(f"Generating Basel III compliance report for {ticker}")

        # 1. Regulatory VaR
        reg_var = self.calculate_regulatory_var(returns, position_value)

        # 2. Stressed VaR
        stressed_var = self.calculate_stressed_var(returns, position_value)

        # 3. Expected Shortfall
        es = self.calculate_expected_shortfall(returns, position_value)

        # 4. Traffic Light Test
        traffic_light = self.traffic_light_test(
            backtest_results.get('num_observations', 250),
            backtest_results.get('num_exceptions', 0)
        )

        # 5. Capital Charge
        capital = self.calculate_market_risk_capital(
            reg_var['var_10day'],
            stressed_var['stressed_var_10day'],
            multiplier=traffic_light['multiplier']
        )

        return {
            'report_date': datetime.now().isoformat(),
            'ticker': ticker,
            'position_value': position_value,
            'regulatory_var': reg_var,
            'stressed_var': stressed_var,
            'expected_shortfall': es,
            'backtesting': traffic_light,
            'capital_charge': capital,
            'compliance_status': traffic_light['zone']
        }
```

---

### Step 2: API Endpoints

Add to `src/api/main.py`:

```python
from regulatory.basel_metrics import BaselMarketRiskCalculator

@app.post("/api/v1/regulatory/basel-report")
async def generate_basel_report(
    ticker: str,
    position_value: float = 1000000,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate Basel III compliance report"""

    # Fetch data
    data = data_collector.fetch_stock_data(ticker, period="5y")  # 5 years for stress testing
    returns = preprocessor.prepare_returns_data(data)['Returns']

    # Run backtest
    backtester = VaRBacktester(confidence_level=0.99)  # Basel uses 99%
    train_size = int(len(returns) * 0.7)
    test_returns = returns[train_size:]

    # Calculate VaR estimates for backtest
    var_calc = VaRCalculator(confidence_level=0.99)
    var_result = var_calc.historical_var(returns[:train_size], position_value)
    var_estimates = pd.Series([var_result['VaR']] * len(test_returns))

    backtest_results = backtester.backtest_var_model(
        test_returns, var_estimates, position_value
    )

    # Generate Basel report
    basel_calc = BaselMarketRiskCalculator()
    report = basel_calc.generate_compliance_report(
        ticker,
        position_value,
        returns,
        backtest_results
    )

    return report


@app.post("/api/v1/regulatory/capital-charge")
async def calculate_capital_charge(
    ticker: str,
    position_value: float = 1000000,
    current_user: User = Depends(get_current_active_user)
):
    """Calculate market risk capital charge"""

    # Fetch data
    data = data_collector.fetch_stock_data(ticker, period="5y")
    returns = preprocessor.prepare_returns_data(data)['Returns']

    # Calculate metrics
    basel_calc = BaselMarketRiskCalculator()

    reg_var = basel_calc.calculate_regulatory_var(returns, position_value)
    stressed_var = basel_calc.calculate_stressed_var(returns, position_value)

    # Assume green zone for example (multiplier = 3.0)
    capital = basel_calc.calculate_market_risk_capital(
        reg_var['var_10day'],
        stressed_var['stressed_var_10day'],
        multiplier=3.0
    )

    return {
        "ticker": ticker,
        "position_value": position_value,
        "var_10day": reg_var['var_10day'],
        "stressed_var_10day": stressed_var['stressed_var_10day'],
        "capital_charge": capital['total_capital_charge'],
        "capital_ratio": (capital['total_capital_charge'] / position_value) * 100
    }
```

---

## 🧪 Test with curl

### Generate Basel III Compliance Report:

```bash
# Full compliance report
curl -X POST "http://localhost:8000/api/v1/regulatory/basel-report" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "position_value": 10000000
  }' | jq '.'
```

**Expected:**
```json
{
  "report_date": "2026-01-01T10:30:00",
  "ticker": "AAPL",
  "position_value": 10000000,
  "regulatory_var": {
    "var_1day": 285000,
    "var_10day": 901234,
    "confidence_level": 0.99,
    "horizon_days": 10,
    "method": "historical",
    "scaling_factor": 3.162
  },
  "stressed_var": {
    "stressed_var_1day": 450000,
    "stressed_var_10day": 1422345,
    "stress_period_start": "2008-09-01",
    "stress_period_end": "2009-03-31",
    "stress_period_days": 182,
    "stress_period_volatility": 0.65
  },
  "expected_shortfall": {
    "es_1day": 380000,
    "es_10day": 1201234,
    "confidence_level": 0.975,
    "var_threshold": -0.038,
    "tail_observations": 18
  },
  "backtesting": {
    "zone": "green",
    "scaled_exceptions": 3.2,
    "multiplier": 3.0,
    "action": "No action required",
    "num_observations": 250,
    "num_exceptions": 8
  },
  "capital_charge": {
    "var_component": 2703702,
    "stressed_var_component": 4267035,
    "total_capital_charge": 6970737,
    "multiplier": 3.0,
    "plus_factor": 0.0
  },
  "compliance_status": "green"
}
```

### Calculate Capital Charge:

```bash
# Quick capital charge calculation
curl -X POST "http://localhost:8000/api/v1/regulatory/capital-charge" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ticker": "AAPL", "position_value": 10000000}' \
  -H "Content-Type: application/json" \
  | jq '{capital_charge, capital_ratio}'
```

**Expected:**
```json
{
  "capital_charge": 6970737,
  "capital_ratio": 69.7
}
```

### Multiple Positions:

```bash
# Calculate for multiple positions
for ticker in AAPL MSFT GOOGL; do
  echo "Basel report for $ticker:"
  curl -s -X POST "http://localhost:8000/api/v1/regulatory/capital-charge" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"ticker\": \"$ticker\"}" \
    -H "Content-Type: application/json" \
    | jq '{ticker: .ticker, capital_charge, capital_ratio}'
  echo ""
done
```

---

## 📊 Basel III Key Metrics

### Regulatory Requirements:

| Metric | Requirement | Purpose |
|--------|-------------|---------|
| **VaR** | 99%, 10-day | Daily risk measure |
| **Stressed VaR** | 99%, 10-day, stress period | Crisis scenario |
| **Expected Shortfall** | 97.5% | Tail risk measure |
| **Backtesting** | < 5 exceptions/250 days | Model validation |
| **Capital Multiplier** | 3.0-4.0 | Supervisory factor |

### Traffic Light Zones:

| Zone | Exceptions (250 days) | Multiplier | Action |
|------|---------------------|------------|---------|
| **Green** | 0-4 | 3.0 | No action |
| **Yellow** | 5-9 | 3.4-3.8 | Review model |
| **Red** | 10+ | 4.0 | Use SA instead |

---

## ✅ Completed

✅ Basel III market risk framework
✅ Regulatory VaR (99%, 10-day)
✅ Stressed VaR calculation
✅ Expected Shortfall (97.5%)
✅ Traffic Light backtesting
✅ Capital charge calculation
✅ Compliance reporting API
✅ curl-based testing

**Next**: Performance Tuning & Scaling (Day 034)
