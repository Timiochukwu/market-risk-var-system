# Day 014: Basel Traffic Light System

**Duration**: 1.5 hours | **Difficulty**: Beginner-Intermediate | **Prerequisites**: Day 001-013

---

## 📋 What You'll Build

- Basel Traffic Light framework
- Green/Yellow/Red zone classification
- Multiplier calculation for capital requirements
- Traffic light API endpoint

---

## 💡 Basel Traffic Light Zones

**Basel Committee Classification**:

```
GREEN ZONE (0-4 exceptions in 250 days):
  ✅ Model is acceptable
  ✅ No additional capital required
  ✅ Multiplier: 3.0

YELLOW ZONE (5-9 exceptions):
  ⚠️  Model needs review
  ⚠️  Additional capital may be required
  ⚠️  Multiplier: 3.0 to 3.4 (increases with exceptions)

RED ZONE (10+ exceptions):
  ❌ Model is inadequate
  ❌ Must increase capital requirements
  ❌ Multiplier: 3.4 to 4.0
  ❌ Model must be revised
```

**Example**:
```
250 trading days, 95% VaR:
  3 exceptions  → GREEN  ✅
  7 exceptions  → YELLOW ⚠️
  12 exceptions → RED    ❌
```

---

## 💻 Implementation

Add to `src/utils/backtesting.py`:

```python
def basel_traffic_light_test(
    self,
    num_observations: int,
    num_exceptions: int,
    base_days: int = 250
) -> Dict[str, any]:
    """
    Basel Traffic Light Test
    
    Classifies model into Green/Yellow/Red zones
    """
    
    # Scale to 250 trading days
    scaled_exceptions = (num_exceptions / num_observations) * base_days
    
    # Determine zone
    if scaled_exceptions < 5:
        zone = "Green"
        status = "Acceptable"
        action = "None required"
        multiplier = 3.0
    elif scaled_exceptions < 10:
        zone = "Yellow"
        status = "Warning"
        action = "Review model"
        # Multiplier increases from 3.0 to 3.4
        multiplier = 3.0 + ((scaled_exceptions - 5) / 5) * 0.4
    else:
        zone = "Red"
        status = "Unacceptable"
        action = "Revise model immediately"
        # Multiplier increases from 3.4 to 4.0
        multiplier = 3.4 + min((scaled_exceptions - 10) / 10, 1) * 0.6
    
    return {
        'Zone': zone,
        'Status': status,
        'Action': action,
        'Multiplier': round(multiplier, 2),
        'Scaled_Exceptions': round(scaled_exceptions, 1),
        'Base_Days': base_days
    }
```

---

## 🧪 Test with curl

```bash
# Test Basel Traffic Light
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.95
  }' | jq '.traffic_light_test'
```

**Expected Response**:
```json
{
  "Zone": "Green",
  "Status": "Acceptable",
  "Action": "None required",
  "Multiplier": 3.0,
  "Scaled_Exceptions": 3.2,
  "Base_Days": 250
}
```

### Test Different Stocks

```bash
for ticker in AAPL TSLA JNJ; do
  echo "\n=== $ticker ==="
  curl -s -X POST "http://localhost:8000/api/v1/backtest" \
    -d "{\"ticker\": \"$ticker\"}" -H "Content-Type: application/json" \
    | jq '{ticker: "'$ticker'", zone: .traffic_light_test.Zone, multiplier: .traffic_light_test.Multiplier}'
done
```

---

## ✅ Completed

✅ Basel Traffic Light implementation
✅ Green/Yellow/Red classification
✅ Capital multiplier calculation
✅ Regulatory compliance framework

**Next**: Advanced Risk Metrics (Day 015)
