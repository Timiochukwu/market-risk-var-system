# Day 012: Kupiec POF Test

**Duration**: 1.5-2 hours
**Difficulty**: Intermediate
**Prerequisites**: Completed Day 001-011

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Understand the Kupiec Proportion of Failures (POF) test
- Implement likelihood ratio testing
- Calculate test statistics and p-values
- Determine if VaR model is statistically acceptable
- Add Kupiec test to backtest API
- Test with curl commands

---

## 🎯 Learning Objectives

### Statistical Concepts:
- **Hypothesis Testing**: Formal statistical tests
- **Likelihood Ratio Test**: Comparing probabilities
- **Chi-square Distribution**: Test statistic distribution
- **p-value**: Probability of observing results by chance
- **Significance Level**: Threshold for rejection (typically 0.05)

### Regulatory Context:
- Basel Committee uses Kupiec test
- Helps determine capital requirements
- Part of model validation process

---

## 💡 Understanding the Kupiec Test (20 minutes)

### What Does It Test?

**Question**: Is the observed exception rate statistically different from the expected rate?

**Hypotheses:**
- **H₀ (Null)**: Exception rate = Expected rate (model is correct)
- **H₁ (Alternative)**: Exception rate ≠ Expected rate (model is wrong)

### Example:

```
95% VaR over 250 days:

Expected exceptions: 250 × 0.05 = 12.5 ≈ 13 days
Observed exceptions: 15 days

Question: Is 15 significantly different from 13?
Answer: Run Kupiec test!

If p-value > 0.05: ✅ Not significantly different (model OK)
If p-value < 0.05: ❌ Significantly different (model failed)
```

---

## 📊 The Kupiec Formula

### Likelihood Ratio Statistic:

```
LR = -2 × ln[(1-p)^(T-N) × p^N / (1-π)^(T-N) × π^N]

where:
  T = Total observations
  N = Number of exceptions
  p = Expected exception rate (e.g., 0.05 for 95% VaR)
  π = Observed exception rate (N/T)
  ln = Natural logarithm

Under H₀, LR follows χ²(1) distribution
```

### Decision Rule:

```
Calculate LR statistic
Find p-value from χ²(1) distribution

If p-value > 0.05: Accept H₀ (model is good)
If p-value ≤ 0.05: Reject H₀ (model failed)
```

---

## 💻 Step 1: Implement Kupiec Test (40 minutes)

### 1.1 Add to `src/utils/backtesting.py`

Add this method to your `VaRBacktester` class:

```python
def kupiec_pof_test(
    self,
    num_observations: int,
    num_exceptions: int
) -> Dict[str, float]:
    """
    Kupiec Proportion of Failures (POF) Test

    Tests if observed exception rate matches expected rate

    Args:
        num_observations: Total number of observations
        num_exceptions: Number of VaR exceptions

    Returns:
        Dictionary with test results

    Example:
        >>> result = backtester.kupiec_pof_test(250, 15)
        >>> print(f"p-value: {result['p_value']:.4f}")
        >>> print(f"Pass: {result['pass_test']}")
    """

    from scipy import stats as scipy_stats

    logger.info("Running Kupiec POF test...")

    # Expected exception rate
    p = self.alpha  # e.g., 0.05 for 95% VaR

    # Observed exception rate
    pi = num_exceptions / num_observations

    # Handle edge cases
    if num_exceptions == 0:
        # No exceptions: check if this is reasonable
        lr_stat = -2 * num_observations * np.log(1 - p)
    elif num_exceptions == num_observations:
        # All exceptions: model is terrible
        lr_stat = -2 * num_observations * np.log(p)
    else:
        # Standard case: calculate likelihood ratio
        # LR = -2 * ln(L(p) / L(π))

        # Likelihood under null hypothesis (p)
        log_l_p = (num_observations - num_exceptions) * np.log(1 - p) + \
                  num_exceptions * np.log(p)

        # Likelihood under alternative (π)
        log_l_pi = (num_observations - num_exceptions) * np.log(1 - pi) + \
                   num_exceptions * np.log(pi)

        # Likelihood ratio statistic
        lr_stat = -2 * (log_l_p - log_l_pi)

    # p-value from chi-square distribution with 1 degree of freedom
    p_value = 1 - scipy_stats.chi2.cdf(lr_stat, df=1)

    # Test decision (significance level = 0.05)
    pass_test = p_value > 0.05

    result = {
        'lr_statistic': lr_stat,
        'p_value': p_value,
        'num_observations': num_observations,
        'num_exceptions': num_exceptions,
        'expected_rate': p,
        'observed_rate': pi,
        'pass_test': pass_test,
        'critical_value_95': scipy_stats.chi2.ppf(0.95, df=1)  # 3.841
    }

    logger.info(f"LR Statistic: {lr_stat:.4f}")
    logger.info(f"p-value: {p_value:.4f}")
    logger.info(f"Test result: {'PASS ✅' if pass_test else 'FAIL ❌'}")

    return result

def print_kupiec_result(self, result: Dict[str, float]):
    """
    Print Kupiec test results

    Args:
        result: Dictionary from kupiec_pof_test()

    Example:
        >>> result = backtester.kupiec_pof_test(250, 15)
        >>> backtester.print_kupiec_result(result)
    """

    print("\n" + "="*70)
    print("KUPIEC PROPORTION OF FAILURES (POF) TEST")
    print("="*70)

    print(f"\n📊 Test Data:")
    print(f"  Observations:        {result['num_observations']}")
    print(f"  Exceptions:          {result['num_exceptions']}")
    print(f"  Expected Rate:       {result['expected_rate']*100:.2f}%")
    print(f"  Observed Rate:       {result['observed_rate']*100:.2f}%")

    print(f"\n📈 Test Statistics:")
    print(f"  LR Statistic:        {result['lr_statistic']:.4f}")
    print(f"  p-value:             {result['p_value']:.4f}")
    print(f"  Critical Value (5%): {result['critical_value_95']:.4f}")

    print(f"\n📖 Interpretation:")
    print(f"  H₀: Exception rate = {result['expected_rate']*100:.2f}%")
    print(f"  H₁: Exception rate ≠ {result['expected_rate']*100:.2f}%")

    if result['pass_test']:
        print(f"\n  ✅ PASS: p-value ({result['p_value']:.4f}) > 0.05")
        print(f"  ✅ Cannot reject H₀")
        print(f"  ✅ Model is statistically acceptable")
    else:
        print(f"\n  ❌ FAIL: p-value ({result['p_value']:.4f}) ≤ 0.05")
        print(f"  ❌ Reject H₀")
        print(f"  ❌ Exception rate significantly different from expected")

        if result['observed_rate'] > result['expected_rate']:
            print(f"  ⚠️  Model UNDERESTIMATES risk (too many exceptions)")
        else:
            print(f"  ⚠️  Model OVERESTIMATES risk (too few exceptions)")

    print("="*70 + "\n")
```

---

## 💻 Step 2: Update API (20 minutes)

### 2.1 Update `src/api/schemas.py`

Add to `BacktestResponse`:

```python
class BacktestResponse(BaseModel):
    """Response from VaR backtesting"""
    ticker: str
    method: str
    confidence_level: float
    num_observations: int
    num_exceptions: int
    exception_rate: float
    expected_rate: float

    # Kupiec test results
    kupiec_test: Dict[str, float]

    mean_excess_loss: float
    max_excess_loss: float
    calculation_date: datetime
```

### 2.2 Update backtest endpoint in `src/api/main.py`

Update the backtest endpoint to include Kupiec test:

```python
@app.post("/api/v1/backtest", response_model=BacktestResponse)
async def backtest_var(request: BacktestRequest):
    """Backtest VaR model with Kupiec test"""
    try:
        # ... (existing code for fetching data and calculating VaR)

        # Backtest
        backtester = VaRBacktester(confidence_level=request.confidence_level)
        backtest_results = backtester.backtest_var_model(
            test_returns,
            var_estimates,
            request.position_value
        )

        # Add Kupiec test
        kupiec_result = backtester.kupiec_pof_test(
            backtest_results['num_observations'],
            backtest_results['num_exceptions']
        )

        response = BacktestResponse(
            ticker=request.ticker,
            method=request.method,
            confidence_level=request.confidence_level,
            num_observations=backtest_results['num_observations'],
            num_exceptions=backtest_results['num_exceptions'],
            exception_rate=backtest_results['exception_rate'],
            expected_rate=backtest_results['expected_rate'],
            kupiec_test=kupiec_result,  # Add Kupiec results
            mean_excess_loss=float(backtest_results['mean_excess_loss']),
            max_excess_loss=float(backtest_results['max_excess_loss']),
            calculation_date=datetime.now()
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🧪 Step 3: Test with curl (15 minutes)

### 3.1 Start API Server

```bash
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3.2 Test Kupiec Test

```bash
# Test 1: AAPL backtest with Kupiec test
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.95,
    "position_value": 1000000,
    "method": "historical"
  }' | jq '{
    ticker,
    exceptions: .num_exceptions,
    exception_rate,
    kupiec: .kupiec_test
  }'
```

**Expected Response:**
```json
{
  "ticker": "AAPL",
  "exceptions": 8,
  "exception_rate": 0.0530,
  "kupiec": {
    "lr_statistic": 0.1234,
    "p_value": 0.7253,
    "num_observations": 151,
    "num_exceptions": 8,
    "expected_rate": 0.05,
    "observed_rate": 0.0530,
    "pass_test": true,
    "critical_value_95": 3.841
  }
}
```

### 3.3 Test Different Confidence Levels

```bash
# Test 99% VaR (should have fewer exceptions)
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.99,
    "method": "historical"
  }' | jq '.kupiec_test | {p_value, pass_test}'
```

### 3.4 Compare Multiple Stocks

```bash
# Test Kupiec for multiple stocks
for ticker in AAPL MSFT GOOGL TSLA JNJ; do
  echo "\n=== $ticker ==="
  curl -s -X POST "http://localhost:8000/api/v1/backtest" \
    -H "Content-Type: application/json" \
    -d "{\"ticker\": \"$ticker\"}" \
    | jq '{
        ticker: .ticker,
        exceptions: .num_exceptions,
        kupiec_pvalue: .kupiec_test.p_value,
        pass: .kupiec_test.pass_test
      }'
done
```

---

## 📊 Step 4: Interpret Results (10 minutes)

### Pass Example:

```json
{
  "lr_statistic": 0.1234,
  "p_value": 0.7253,
  "pass_test": true
}
```
**Interpretation**: ✅ p-value (0.73) > 0.05 → Model is good!

### Fail Example (Too Many Exceptions):

```json
{
  "lr_statistic": 5.234,
  "p_value": 0.0221,
  "pass_test": false,
  "observed_rate": 0.0850
}
```
**Interpretation**: ❌ p-value (0.02) < 0.05 → Model underestimates risk!

### Fail Example (Too Few Exceptions):

```json
{
  "lr_statistic": 4.123,
  "p_value": 0.0423,
  "pass_test": false,
  "observed_rate": 0.0120
}
```
**Interpretation**: ❌ p-value (0.04) < 0.05 → Model is too conservative!

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Understood likelihood ratio testing
✅ Implemented Kupiec POF test
✅ Calculated test statistics and p-values
✅ Integrated with backtesting API
✅ Tested with curl commands
✅ Learned to interpret statistical test results

---

## 🎯 Practice Exercises

### Exercise 1: Test Sensitivity

```bash
# How sensitive is Kupiec test to small differences?
# Test with different sample sizes by changing train_ratio

for ratio in 0.5 0.6 0.7 0.8; do
  echo "\nTrain ratio: $ratio"
  curl -s -X POST "http://localhost:8000/api/v1/backtest" \
    -H "Content-Type: application/json" \
    -d "{\"ticker\": \"AAPL\", \"train_ratio\": $ratio}" \
    | jq '.kupiec_test | {observations: .num_observations, p_value, pass_test}'
done
```

### Exercise 2: Historical vs Parametric

```bash
# Compare Kupiec results for different methods
for method in historical parametric; do
  echo "\nMethod: $method"
  curl -s -X POST "http://localhost:8000/api/v1/backtest" \
    -H "Content-Type: application/json" \
    -d "{\"ticker\": \"AAPL\", \"method\": \"$method\"}" \
    | jq '.kupiec_test | {method: "'$method'", p_value, pass_test}'
done
```

### Exercise 3: Volatile vs Stable Stocks

```bash
# Compare tech (volatile) vs defensive (stable)
curl -s -X POST "http://localhost:8000/api/v1/backtest" \
  -d '{"ticker": "TSLA"}' -H "Content-Type: application/json" \
  | jq '{stock: "TSLA (volatile)", kupiec_pass: .kupiec_test.pass_test}'

curl -s -X POST "http://localhost:8000/api/v1/backtest" \
  -d '{"ticker": "JNJ"}' -H "Content-Type: application/json" \
  | jq '{stock: "JNJ (stable)", kupiec_pass: .kupiec_test.pass_test}'
```

---

## 🔜 Coming Up in Day 013

Tomorrow you'll learn:
- **Christoffersen Independence Test**: Test for exception clustering
- **Conditional Coverage**: Combining Kupiec + Christoffersen
- **Serial Correlation**: Are exceptions independent?

**File you'll update**: `src/utils/backtesting.py` (Part 3)

---

**Excellent work! You've mastered statistical testing! 📊**
