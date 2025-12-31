# Day 013: Christoffersen Independence Test

**Duration**: 1.5 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-012

---

## 📋 What You'll Build

- Christoffersen Independence Test
- Test for exception clustering
- Combined conditional coverage test
- Enhanced backtest API with all tests

---

## 💡 Key Concept

**Independence Test**: Are VaR exceptions independent or do they cluster?

**Problem**: If exceptions cluster (come in groups), VaR model fails to adapt quickly enough.

**Example**:
```
Good Model (independent exceptions):
  Day 1: Exception
  Day 5: Exception
  Day 12: Exception  ← Spread out ✅

Bad Model (clustering):
  Day 1: Exception
  Day 2: Exception
  Day 3: Exception  ← Clustered together ❌
```

---

## 💻 Implementation

Add to `src/utils/backtesting.py`:

```python
def christoffersen_independence_test(
    self,
    exceptions: pd.Series
) -> Dict[str, float]:
    """
    Christoffersen Independence Test
    
    Tests if exceptions are independent (not clustered)
    
    H₀: Exceptions are independent
    H₁: Exceptions are clustered
    """
    
    from scipy import stats as scipy_stats
    
    # Convert to binary array
    exc_array = exceptions.values.astype(int)
    
    # Count transitions
    n00 = 0  # No exception → No exception
    n01 = 0  # No exception → Exception
    n10 = 0  # Exception → No exception
    n11 = 0  # Exception → Exception
    
    for i in range(len(exc_array) - 1):
        if exc_array[i] == 0 and exc_array[i+1] == 0:
            n00 += 1
        elif exc_array[i] == 0 and exc_array[i+1] == 1:
            n01 += 1
        elif exc_array[i] == 1 and exc_array[i+1] == 0:
            n10 += 1
        else:  # exc_array[i] == 1 and exc_array[i+1] == 1
            n11 += 1
    
    # Calculate probabilities
    π01 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0
    π11 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0
    π = (n01 + n11) / (n00 + n01 + n10 + n11)
    
    # Likelihood ratio statistic
    if π01 > 0 and π11 > 0 and π > 0:
        lr_ind = -2 * (
            np.log((1-π)**(n00+n10) * π**(n01+n11)) -
            np.log((1-π01)**n00 * π01**n01 * (1-π11)**n10 * π11**n11)
        )
    else:
        lr_ind = 0
    
    # p-value from chi-square(1)
    p_value = 1 - scipy_stats.chi2.cdf(lr_ind, df=1)
    
    pass_test = p_value > 0.05
    
    return {
        'lr_statistic': lr_ind,
        'p_value': p_value,
        'pass_test': pass_test,
        'n00': n00, 'n01': n01, 'n10': n10, 'n11': n11,
        'pi01': π01, 'pi11': π11
    }

def conditional_coverage_test(
    self,
    num_observations: int,
    num_exceptions: int,
    exceptions: pd.Series
) -> Dict[str, float]:
    """
    Combined Conditional Coverage Test
    
    Combines Kupiec POF + Christoffersen Independence
    """
    
    from scipy import stats as scipy_stats
    
    # Run both tests
    kupiec = self.kupiec_pof_test(num_observations, num_exceptions)
    christ = self.christoffersen_independence_test(exceptions)
    
    # Combined LR statistic
    lr_cc = kupiec['lr_statistic'] + christ['lr_statistic']
    
    # p-value from chi-square(2)
    p_value = 1 - scipy_stats.chi2.cdf(lr_cc, df=2)
    
    pass_test = p_value > 0.05
    
    return {
        'lr_statistic': lr_cc,
        'p_value': p_value,
        'pass_test': pass_test,
        'kupiec_pass': kupiec['pass_test'],
        'christoffersen_pass': christ['pass_test']
    }
```

---

## 🧪 Test with curl

```bash
# Test with enhanced backtest endpoint
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.95
  }' | jq '{
    kupiec: .kupiec_test.pass_test,
    christoffersen: .christoffersen_test.pass_test,
    conditional_coverage: .combined_test.pass_test
  }'
```

---

## ✅ Completed

✅ Christoffersen independence test
✅ Conditional coverage test
✅ Full statistical validation framework

**Next**: Basel Traffic Light System (Day 014)
