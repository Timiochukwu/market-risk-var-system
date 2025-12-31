# Day 011: Backtesting Framework Part 1

**Duration**: 2 hours
**Difficulty**: Intermediate
**Prerequisites**: Completed Day 001-010

---

## 📋 What You'll Build Today

By the end of this session, you will:
- Understand VaR backtesting concepts
- Build a backtesting framework
- Calculate VaR exceptions (breaches)
- Track exception rates over time
- Create a backtesting API endpoint
- Test with real API calls using curl

---

## 🎯 Learning Objectives

### Financial Concepts:
- **VaR Exceptions**: Days when actual loss exceeds VaR
- **Exception Rate**: Percentage of VaR breaches
- **Backtesting**: Validating VaR model accuracy
- **Coverage**: How often VaR is correct

### Regulatory Context:
- Basel Committee requires backtesting
- Exception rate should match confidence level
- Too many exceptions = model is bad
- Too few exceptions = model is too conservative

---

## 💡 Understanding Backtesting (15 minutes)

### What is VaR Backtesting?

**Question**: How do we know if our VaR model is good?

**Answer**: Compare VaR predictions to actual outcomes!

### Example:

```
Day 1:
  VaR (95%): Don't lose more than $10,000
  Actual Loss: $8,000
  Result: ✅ VaR held (no exception)

Day 2:
  VaR (95%): Don't lose more than $10,000
  Actual Loss: $15,000
  Result: ❌ VaR breached (exception!)

Over 100 days:
  Expected exceptions (95% VaR): ~5 days
  Actual exceptions: 4 days
  Result: ✅ Model is accurate!
```

### Good vs Bad Models

```
95% VaR over 250 trading days:

GOOD MODEL:
  Expected exceptions: ~13 days (5%)
  Actual exceptions: 11 days
  → Model is accurate ✅

BAD MODEL (underestimates risk):
  Expected exceptions: ~13 days (5%)
  Actual exceptions: 35 days
  → Model underestimates risk ❌

TOO CONSERVATIVE:
  Expected exceptions: ~13 days (5%)
  Actual exceptions: 2 days
  → Model overestimates risk ⚠️
```

---

## 💻 Step 1: Build Backtesting Module (50 minutes)

### 1.1 Create `src/utils/backtesting.py`

```python
"""
Backtesting Module for VaR Models
Validates VaR model accuracy by comparing predictions to actual outcomes
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VaRBacktester:
    """
    Backtest VaR models to validate accuracy

    Compares VaR predictions to actual returns to assess model quality
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize backtester

        Args:
            confidence_level: VaR confidence level (e.g., 0.95 for 95%)

        Example:
            >>> backtester = VaRBacktester(confidence_level=0.95)
        """
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level

        logger.info(f"VaR Backtester initialized with {confidence_level*100}% confidence")

    def calculate_exceptions(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        position_value: float = 1000000
    ) -> pd.Series:
        """
        Calculate VaR exceptions (breaches)

        An exception occurs when actual loss exceeds VaR

        Args:
            returns: Actual returns
            var_estimates: VaR estimates (as positive dollar amounts)
            position_value: Portfolio value

        Returns:
            Boolean series (True = exception, False = no exception)

        Example:
            >>> exceptions = backtester.calculate_exceptions(returns, var_series)
            >>> print(f"Total exceptions: {exceptions.sum()}")
        """

        # Convert returns to dollar losses (negative returns = losses)
        actual_losses = -returns * position_value

        # Exception occurs when actual loss > VaR
        exceptions = actual_losses > var_estimates

        num_exceptions = exceptions.sum()
        total_obs = len(exceptions)
        exception_rate = num_exceptions / total_obs

        logger.info(f"Exceptions: {num_exceptions}/{total_obs} ({exception_rate*100:.2f}%)")
        logger.info(f"Expected rate: {self.alpha*100:.2f}%")

        return exceptions

    def calculate_excess_losses(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        position_value: float = 1000000
    ) -> pd.Series:
        """
        Calculate excess losses beyond VaR

        Excess loss = Actual loss - VaR (only for exceptions)

        Args:
            returns: Actual returns
            var_estimates: VaR estimates
            position_value: Portfolio value

        Returns:
            Series with excess losses (0 if no exception)

        Example:
            >>> excess = backtester.calculate_excess_losses(returns, var_series)
            >>> mean_excess = excess[excess > 0].mean()
        """

        actual_losses = -returns * position_value
        excess = actual_losses - var_estimates

        # Set non-exceptions to 0
        excess[excess < 0] = 0

        num_excess = (excess > 0).sum()
        mean_excess = excess[excess > 0].mean() if num_excess > 0 else 0

        logger.info(f"Excess losses: {num_excess} instances")
        logger.info(f"Mean excess loss: ${mean_excess:,.2f}")

        return excess

    def backtest_var_model(
        self,
        returns: pd.Series,
        var_estimates: pd.Series,
        position_value: float = 1000000
    ) -> Dict[str, any]:
        """
        Comprehensive backtest of VaR model

        Args:
            returns: Actual returns
            var_estimates: VaR estimates
            position_value: Portfolio value

        Returns:
            Dictionary with backtest results

        Example:
            >>> results = backtester.backtest_var_model(test_returns, var_estimates)
            >>> print(f"Exception rate: {results['exception_rate']:.2%}")
        """

        logger.info("Running comprehensive VaR backtest...")

        # Align series
        common_index = returns.index.intersection(var_estimates.index)
        returns_aligned = returns.loc[common_index]
        var_aligned = var_estimates.loc[common_index]

        # Calculate exceptions
        exceptions = self.calculate_exceptions(
            returns_aligned,
            var_aligned,
            position_value
        )

        # Calculate excess losses
        excess_losses = self.calculate_excess_losses(
            returns_aligned,
            var_aligned,
            position_value
        )

        # Calculate statistics
        num_observations = len(returns_aligned)
        num_exceptions = exceptions.sum()
        exception_rate = num_exceptions / num_observations
        expected_rate = self.alpha

        # Excess loss statistics
        excess_values = excess_losses[excess_losses > 0]
        mean_excess = excess_values.mean() if len(excess_values) > 0 else 0
        max_excess = excess_values.max() if len(excess_values) > 0 else 0

        # Cumulative exceptions over time
        cumulative_exceptions = exceptions.cumsum()

        results = {
            'num_observations': num_observations,
            'num_exceptions': int(num_exceptions),
            'exception_rate': exception_rate,
            'expected_rate': expected_rate,
            'exceptions': exceptions,
            'excess_losses': excess_losses,
            'cumulative_exceptions': cumulative_exceptions,
            'mean_excess_loss': mean_excess,
            'max_excess_loss': max_excess,
            'exception_dates': exceptions[exceptions].index.tolist()
        }

        logger.info("Backtest completed")
        logger.info(f"Exception rate: {exception_rate*100:.2f}% (expected: {expected_rate*100:.2f}%)")

        return results

    def print_backtest_report(self, results: Dict[str, any]):
        """
        Print comprehensive backtest report

        Args:
            results: Dictionary from backtest_var_model()

        Example:
            >>> results = backtester.backtest_var_model(returns, var_estimates)
            >>> backtester.print_backtest_report(results)
        """

        print("\n" + "="*70)
        print(f"VaR BACKTEST REPORT ({self.confidence_level*100}% Confidence)")
        print("="*70)

        print(f"\n📊 Test Period:")
        print(f"  Observations:        {results['num_observations']}")
        print(f"  Confidence Level:    {self.confidence_level*100}%")

        print(f"\n📈 Exception Analysis:")
        print(f"  Total Exceptions:    {results['num_exceptions']}")
        print(f"  Exception Rate:      {results['exception_rate']*100:.2f}%")
        print(f"  Expected Rate:       {results['expected_rate']*100:.2f}%")

        # Interpretation
        diff = abs(results['exception_rate'] - results['expected_rate'])
        if diff < 0.01:
            print(f"  Status:              ✅ Excellent match!")
        elif diff < 0.02:
            print(f"  Status:              ✅ Good match")
        elif diff < 0.03:
            print(f"  Status:              ⚠️  Acceptable")
        else:
            print(f"  Status:              ❌ Poor match")

        print(f"\n💰 Excess Loss Statistics:")
        print(f"  Mean Excess Loss:    ${results['mean_excess_loss']:,.2f}")
        print(f"  Max Excess Loss:     ${results['max_excess_loss']:,.2f}")

        if len(results['exception_dates']) > 0:
            print(f"\n📅 Exception Dates ({min(5, len(results['exception_dates']))} most recent):")
            for date in results['exception_dates'][-5:]:
                print(f"  - {date.date() if hasattr(date, 'date') else date}")

        print("="*70 + "\n")


# Test the module
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor
    from models.var_calculator import VaRCalculator

    print("="*70)
    print("Testing VaR Backtester")
    print("="*70)

    # Fetch and prepare data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)
    returns = returns_data['Returns'].dropna()

    # Split into train and test
    train_size = int(len(returns) * 0.7)
    train_returns = returns.iloc[:train_size]
    test_returns = returns.iloc[train_size:]

    print(f"\nTraining set: {len(train_returns)} observations")
    print(f"Test set:     {len(test_returns)} observations")

    # Calculate VaR on training set
    var_calc = VaRCalculator(confidence_level=0.95)
    var_result = var_calc.historical_var(train_returns, position_value=1000000)

    print(f"\nVaR calculated on training set:")
    print(f"  95% VaR: ${var_result['VaR']:,.2f}")

    # Create constant VaR estimates for test period
    var_estimates = pd.Series(
        var_result['VaR'],
        index=test_returns.index
    )

    # Backtest
    backtester = VaRBacktester(confidence_level=0.95)
    results = backtester.backtest_var_model(
        test_returns,
        var_estimates,
        position_value=1000000
    )

    # Print report
    backtester.print_backtest_report(results)

    print("\n✅ Backtesting module working!")
```

---

## 💻 Step 2: Add Backtest API Endpoint (30 minutes)

### 2.1 Update `src/api/schemas.py`

Add these Pydantic models:

```python
class BacktestRequest(BaseModel):
    """Request for VaR backtesting"""
    ticker: str
    confidence_level: float = 0.95
    position_value: float = 1000000
    method: str = "historical"  # historical, parametric, monte_carlo
    train_ratio: float = 0.7  # 70% train, 30% test

class BacktestResponse(BaseModel):
    """Response from VaR backtesting"""
    ticker: str
    method: str
    confidence_level: float
    num_observations: int
    num_exceptions: int
    exception_rate: float
    expected_rate: float
    mean_excess_loss: float
    max_excess_loss: float
    calculation_date: datetime
```

### 2.2 Update `src/api/main.py`

Add this endpoint:

```python
from utils.backtesting import VaRBacktester

@app.post("/api/v1/backtest", response_model=BacktestResponse)
async def backtest_var(request: BacktestRequest):
    """
    Backtest VaR model

    Tests VaR model accuracy by comparing predictions to actual outcomes
    """
    try:
        # Fetch and prepare data
        data = data_collector.fetch_stock_data(request.ticker, period="2y")
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.ticker}")

        returns_data = preprocessor.prepare_returns_data(data)
        returns = returns_data['Returns'].dropna()

        # Split data
        train_size = int(len(returns) * request.train_ratio)
        train_returns = returns.iloc[:train_size]
        test_returns = returns.iloc[train_size:]

        # Calculate VaR on training set
        var_calc = VaRCalculator(confidence_level=request.confidence_level)

        if request.method == "historical":
            var_result = var_calc.historical_var(train_returns, request.position_value)
        elif request.method == "parametric":
            var_result = var_calc.parametric_var(train_returns, request.position_value)
        else:
            raise HTTPException(status_code=400, detail="Only historical and parametric supported")

        # Create constant VaR estimates
        var_estimates = pd.Series(var_result['VaR'], index=test_returns.index)

        # Backtest
        backtester = VaRBacktester(confidence_level=request.confidence_level)
        backtest_results = backtester.backtest_var_model(
            test_returns,
            var_estimates,
            request.position_value
        )

        response = BacktestResponse(
            ticker=request.ticker,
            method=request.method,
            confidence_level=request.confidence_level,
            num_observations=backtest_results['num_observations'],
            num_exceptions=backtest_results['num_exceptions'],
            exception_rate=backtest_results['exception_rate'],
            expected_rate=backtest_results['expected_rate'],
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

### 3.1 Start the API Server

```bash
cd /home/user/market-risk-var-system/src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3.2 Test Backtest Endpoint

```bash
# Test 1: Basic backtest for AAPL
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.95,
    "position_value": 1000000,
    "method": "historical",
    "train_ratio": 0.7
  }' | jq '.'
```

**Expected Response:**
```json
{
  "ticker": "AAPL",
  "method": "historical",
  "confidence_level": 0.95,
  "num_observations": 151,
  "num_exceptions": 8,
  "exception_rate": 0.0530,
  "expected_rate": 0.05,
  "mean_excess_loss": 2345.67,
  "max_excess_loss": 8901.23,
  "calculation_date": "2025-12-31T12:00:00Z"
}
```

### 3.3 Test Different Confidence Levels

```bash
# 99% VaR backtest
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.99,
    "position_value": 1000000,
    "method": "historical"
  }' | jq '.exception_rate, .expected_rate'
```

### 3.4 Test Different Stocks

```bash
# Volatile stock (Tesla)
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "TSLA",
    "confidence_level": 0.95,
    "position_value": 1000000,
    "method": "historical"
  }' | jq '.'

# Defensive stock (Johnson & Johnson)
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "JNJ",
    "confidence_level": 0.95,
    "position_value": 1000000,
    "method": "historical"
  }' | jq '.'
```

---

## 📊 Step 4: Interpret Results (10 minutes)

### Good Backtest Results:

```json
{
  "exception_rate": 0.0530,  // 5.3%
  "expected_rate": 0.05      // 5.0%
}
```
**Interpretation**: ✅ Model is accurate (5.3% ≈ 5.0%)

### Bad Results - Underestimates Risk:

```json
{
  "exception_rate": 0.0850,  // 8.5%
  "expected_rate": 0.05      // 5.0%
}
```
**Interpretation**: ❌ Too many exceptions → VaR too low

### Bad Results - Too Conservative:

```json
{
  "exception_rate": 0.0120,  // 1.2%
  "expected_rate": 0.05      // 5.0%
}
```
**Interpretation**: ⚠️ Too few exceptions → VaR too high

---

## ✅ What You Accomplished Today

Congratulations! You have:

✅ Built a complete backtesting framework
✅ Implemented exception tracking
✅ Calculated excess losses beyond VaR
✅ Created backtesting API endpoint
✅ Tested with curl commands
✅ Learned to interpret backtest results

---

## 🎯 Practice Exercises

### Exercise 1: Compare Methods

```bash
# Test all three methods for same stock
for method in historical parametric; do
  echo "Testing $method..."
  curl -X POST "http://localhost:8000/api/v1/backtest" \
    -H "Content-Type: application/json" \
    -d "{\"ticker\": \"AAPL\", \"method\": \"$method\"}" \
    | jq '{method: .method, exception_rate: .exception_rate}'
done
```

### Exercise 2: Different Train/Test Splits

```bash
# Test with different split ratios
for ratio in 0.6 0.7 0.8; do
  curl -X POST "http://localhost:8000/api/v1/backtest" \
    -H "Content-Type: application/json" \
    -d "{\"ticker\": \"AAPL\", \"train_ratio\": $ratio}" \
    | jq '{train_ratio: $ratio, exceptions: .num_exceptions}'
done
```

### Exercise 3: Portfolio Analysis

```bash
# Compare backtests across different stocks
for ticker in AAPL MSFT GOOGL TSLA; do
  echo "\nBacktest for $ticker:"
  curl -s -X POST "http://localhost:8000/api/v1/backtest" \
    -H "Content-Type: application/json" \
    -d "{\"ticker\": \"$ticker\"}" \
    | jq '{ticker: .ticker, exception_rate: .exception_rate, mean_excess: .mean_excess_loss}'
done
```

---

## 🔜 Coming Up in Day 012

Tomorrow you'll learn:
- **Kupiec POF Test**: Statistical test for exception rate
- **Likelihood Ratio Test**: Formal hypothesis testing
- **p-values**: Is our model statistically acceptable?
- **Chi-square Distribution**: Test statistic distribution

**File you'll update**: `src/utils/backtesting.py` (Part 2)

---

**Great work! You've built a working backtesting system! 📊**
