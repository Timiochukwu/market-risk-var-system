# Day 017: Stress Testing & Scenarios

**Duration**: 1.5-2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-016

---

## 📋 What You'll Build

- Stress testing framework
- Predefined scenarios (market crash, volatility spike)
- Custom scenario builder
- Reverse stress testing
- Stress test API endpoint

---

## 💡 Stress Testing vs VaR

**VaR**: "What loss is likely under normal conditions?"
**Stress Test**: "What happens in extreme events?"

```
VaR (95%):
  Normal market conditions
  95% confidence
  ~$30,000 loss

Stress Test (Market Crash -20%):
  Extreme scenario
  100% probability of scenario
  ~$200,000 loss
```

---

## 💻 Implementation

Create `src/utils/stress_testing.py`:

```python
"""
Stress Testing Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class StressTester:
    """Stress testing for VaR models"""
    
    def __init__(self):
        self.scenarios = self._define_scenarios()
    
    def _define_scenarios(self) -> Dict[str, Dict]:
        """Predefined stress scenarios"""
        
        return {
            'market_crash': {
                'name': 'Market Crash',
                'description': '2008-style financial crisis',
                'shock_pct': -0.20,  # -20%
                'volatility_multiplier': 3.0
            },
            'flash_crash': {
                'name': 'Flash Crash',
                'description': 'Sudden 10% drop',
                'shock_pct': -0.10,
                'volatility_multiplier': 2.0
            },
            'volatility_spike': {
                'name': 'Volatility Spike',
                'description': 'VIX doubles',
                'shock_pct': 0.0,
                'volatility_multiplier': 2.0
            },
            'correlation_breakdown': {
                'name': 'Correlation Breakdown',
                'description': 'All correlations → 1.0',
                'correlation_shock': 1.0
            }
        }
    
    def apply_scenario(
        self,
        returns: pd.Series,
        scenario_name: str,
        position_value: float = 1000000
    ) -> Dict[str, float]:
        """Apply stress scenario"""
        
        scenario = self.scenarios[scenario_name]
        
        # Apply shock
        if 'shock_pct' in scenario:
            shock = scenario['shock_pct']
            stressed_return = returns.mean() + shock
            loss = -stressed_return * position_value
        
        # Apply volatility multiplier
        if 'volatility_multiplier' in scenario:
            vol_mult = scenario['volatility_multiplier']
            stressed_vol = returns.std() * vol_mult
            
            # VaR with stressed volatility
            from scipy import stats
            z_score = stats.norm.ppf(0.05)  # 95% VaR
            stressed_var = -z_score * stressed_vol * position_value
        else:
            stressed_var = None
        
        return {
            'scenario': scenario['name'],
            'description': scenario['description'],
            'stressed_loss': loss if 'shock_pct' in scenario else None,
            'stressed_var': stressed_var,
            'shock_pct': scenario.get('shock_pct', 0) * 100,
            'vol_multiplier': scenario.get('volatility_multiplier', 1.0)
        }
    
    def custom_scenario(
        self,
        returns: pd.Series,
        shock_pct: float,
        vol_multiplier: float = 1.0,
        position_value: float = 1000000
    ) -> Dict[str, float]:
        """Create custom stress scenario"""
        
        # Apply return shock
        stressed_return = returns.mean() + shock_pct
        loss = -stressed_return * position_value
        
        # Apply volatility shock
        stressed_vol = returns.std() * vol_multiplier
        
        from scipy import stats
        z_score = stats.norm.ppf(0.05)
        stressed_var = -z_score * stressed_vol * position_value
        
        return {
            'scenario': 'Custom',
            'stressed_loss': loss,
            'stressed_var': stressed_var,
            'shock_pct': shock_pct * 100,
            'vol_multiplier': vol_multiplier
        }
    
    def reverse_stress_test(
        self,
        returns: pd.Series,
        target_loss: float,
        position_value: float = 1000000
    ) -> float:
        """
        Reverse stress test: Find shock needed for target loss
        
        Returns:
            Required shock percentage
        """
        
        required_return = -target_loss / position_value
        current_mean = returns.mean()
        
        required_shock = required_return - current_mean
        
        return required_shock * 100  # As percentage
```

---

## 🧪 API Endpoint

```python
@app.post("/api/v1/stress/test")
async def stress_test(
    ticker: str,
    scenario: str = "market_crash",
    position_value: float = 1000000
):
    """Run stress test"""
    
    from utils.stress_testing import StressTester
    
    # Fetch data
    data = data_collector.fetch_stock_data(ticker, period="2y")
    returns = preprocessor.prepare_returns_data(data)['Returns']
    
    # Run stress test
    tester = StressTester()
    result = tester.apply_scenario(returns, scenario, position_value)
    
    return result
```

---

## 🧪 Test with curl

```bash
# Market crash scenario
curl -X POST "http://localhost:8000/api/v1/stress/test" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "scenario": "market_crash",
    "position_value": 1000000
  }' | jq '.'
```

**Expected:**
```json
{
  "scenario": "Market Crash",
  "description": "2008-style financial crisis",
  "stressed_loss": 203456.78,
  "stressed_var": 95678.90,
  "shock_pct": -20.0,
  "vol_multiplier": 3.0
}
```

### Test All Scenarios:

```bash
for scenario in market_crash flash_crash volatility_spike; do
  echo "\n=== $scenario ==="
  curl -s POST "http://localhost:8000/api/v1/stress/test" \
    -d "{\"ticker\": \"AAPL\", \"scenario\": \"$scenario\"}" \
    | jq '{scenario, stressed_loss}'
done
```

---

## ✅ Completed

✅ Stress testing framework
✅ Predefined scenarios
✅ Custom scenario builder
✅ Reverse stress testing
✅ curl-based API testing

**Next**: Report Generation (Day 018)
