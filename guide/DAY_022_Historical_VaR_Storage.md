# Day 022: Historical VaR Storage & Trends

**Duration**: 1.5-2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-021

---

## 📋 What You'll Build

- Time-series VaR storage
- Trend analysis endpoints
- VaR comparison across methods
- Historical chart data preparation
- Batch VaR calculations
- Automated daily storage

---

## 💡 Why Track Historical VaR?

### Use Cases:

```
1. Trend Analysis
   - Is risk increasing or decreasing?
   - Seasonal patterns in volatility

2. Model Comparison
   - Which method is most stable?
   - Historical vs Parametric vs GARCH over time

3. Regulatory Reporting
   - 250-day VaR history (Basel requirement)
   - Demonstrate model performance

4. Early Warning System
   - Detect VaR spikes
   - Alert when risk exceeds thresholds
```

---

## 💻 Implementation

### Step 1: Historical Analysis Module

Create `src/database/historical_analysis.py`:

```python
"""
Historical VaR Analysis
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime, timedelta
import pandas as pd

from .models import Position, VaRCalculation, BacktestResult
from . import crud


class HistoricalVaRAnalyzer:
    """Analyze historical VaR data"""

    def __init__(self, db: Session):
        self.db = db

    def get_var_timeseries(
        self,
        ticker: str,
        method: str = None,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Get VaR time series as DataFrame

        Returns:
            DataFrame with columns: date, var_amount, var_percentage, cvar_amount
        """

        calculations = crud.get_var_calculations(
            self.db,
            ticker=ticker,
            method=method,
            days=days
        )

        if not calculations:
            return pd.DataFrame()

        data = []
        for calc in calculations:
            data.append({
                'date': calc.calculation_date,
                'method': calc.method,
                'var_amount': calc.var_amount,
                'var_percentage': calc.var_percentage,
                'cvar_amount': calc.cvar_amount,
                'confidence_level': calc.confidence_level
            })

        df = pd.DataFrame(data)
        df = df.sort_values('date')
        return df

    def calculate_var_trend(
        self,
        ticker: str,
        method: str = None,
        days: int = 30
    ) -> Dict:
        """
        Calculate VaR trend (increasing/decreasing)

        Returns:
            Dict with trend analysis
        """

        df = self.get_var_timeseries(ticker, method, days)

        if df.empty or len(df) < 2:
            return {'trend': 'insufficient_data'}

        # Calculate trend
        first_var = df.iloc[0]['var_amount']
        last_var = df.iloc[-1]['var_amount']
        change = last_var - first_var
        change_pct = (change / first_var) * 100

        # Determine trend direction
        if abs(change_pct) < 5:
            trend = 'stable'
        elif change_pct > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'

        # Calculate volatility of VaR (how stable is the VaR estimate?)
        var_volatility = df['var_amount'].std()

        return {
            'trend': trend,
            'first_var': first_var,
            'last_var': last_var,
            'change_amount': change,
            'change_percentage': change_pct,
            'average_var': df['var_amount'].mean(),
            'min_var': df['var_amount'].min(),
            'max_var': df['var_amount'].max(),
            'var_volatility': var_volatility,
            'data_points': len(df)
        }

    def compare_methods(
        self,
        ticker: str,
        days: int = 30
    ) -> Dict:
        """
        Compare VaR across different methods

        Returns:
            Dict with comparison data
        """

        methods = ['historical', 'parametric', 'monte_carlo', 'garch']
        comparison = {}

        for method in methods:
            df = self.get_var_timeseries(ticker, method, days)

            if not df.empty:
                comparison[method] = {
                    'average_var': df['var_amount'].mean(),
                    'min_var': df['var_amount'].min(),
                    'max_var': df['var_amount'].max(),
                    'std_var': df['var_amount'].std(),
                    'count': len(df)
                }

        if not comparison:
            return {'error': 'No data available'}

        # Find most conservative (highest VaR) and least conservative
        avg_vars = {k: v['average_var'] for k, v in comparison.items()}
        most_conservative = max(avg_vars, key=avg_vars.get)
        least_conservative = min(avg_vars, key=avg_vars.get)

        return {
            'methods': comparison,
            'most_conservative': most_conservative,
            'least_conservative': least_conservative,
            'var_range': {
                'min': min(avg_vars.values()),
                'max': max(avg_vars.values()),
                'spread': max(avg_vars.values()) - min(avg_vars.values())
            }
        }

    def detect_var_spikes(
        self,
        ticker: str,
        method: str = None,
        days: int = 30,
        threshold_std: float = 2.0
    ) -> List[Dict]:
        """
        Detect VaR spikes (outliers)

        Args:
            threshold_std: Number of standard deviations for spike detection

        Returns:
            List of spike events
        """

        df = self.get_var_timeseries(ticker, method, days)

        if df.empty or len(df) < 5:
            return []

        # Calculate mean and std
        mean_var = df['var_amount'].mean()
        std_var = df['var_amount'].std()

        # Find spikes
        spikes = []
        for _, row in df.iterrows():
            z_score = (row['var_amount'] - mean_var) / std_var

            if abs(z_score) > threshold_std:
                spikes.append({
                    'date': row['date'].isoformat(),
                    'var_amount': row['var_amount'],
                    'z_score': z_score,
                    'deviation_from_mean': row['var_amount'] - mean_var,
                    'severity': 'high' if abs(z_score) > 3 else 'medium'
                })

        return spikes

    def get_var_statistics(
        self,
        ticker: str,
        method: str = None,
        days: int = 90
    ) -> Dict:
        """
        Get comprehensive VaR statistics

        Returns:
            Dict with statistical summary
        """

        df = self.get_var_timeseries(ticker, method, days)

        if df.empty:
            return {'error': 'No data available'}

        return {
            'ticker': ticker,
            'method': method or 'all',
            'period_days': days,
            'total_calculations': len(df),
            'var_statistics': {
                'mean': df['var_amount'].mean(),
                'median': df['var_amount'].median(),
                'std': df['var_amount'].std(),
                'min': df['var_amount'].min(),
                'max': df['var_amount'].max(),
                'q25': df['var_amount'].quantile(0.25),
                'q75': df['var_amount'].quantile(0.75)
            },
            'var_percentage_statistics': {
                'mean': df['var_percentage'].mean(),
                'min': df['var_percentage'].min(),
                'max': df['var_percentage'].max()
            },
            'date_range': {
                'first': df['date'].min().isoformat(),
                'last': df['date'].max().isoformat()
            }
        }

    def prepare_chart_data(
        self,
        ticker: str,
        days: int = 30
    ) -> Dict:
        """
        Prepare data for frontend charting

        Returns:
            Dict with chart-ready data
        """

        methods = ['historical', 'parametric', 'monte_carlo']
        chart_data = {
            'labels': [],
            'datasets': []
        }

        # Get data for each method
        all_dates = set()
        method_data = {}

        for method in methods:
            df = self.get_var_timeseries(ticker, method, days)

            if not df.empty:
                df = df.sort_values('date')
                method_data[method] = df
                all_dates.update(df['date'].tolist())

        if not all_dates:
            return chart_data

        # Sort dates
        sorted_dates = sorted(all_dates)
        chart_data['labels'] = [d.strftime('%Y-%m-%d') for d in sorted_dates]

        # Add dataset for each method
        for method, df in method_data.items():
            # Create date index
            df_indexed = df.set_index('date')

            values = []
            for date in sorted_dates:
                if date in df_indexed.index:
                    values.append(float(df_indexed.loc[date, 'var_amount']))
                else:
                    values.append(None)  # Gap in data

            chart_data['datasets'].append({
                'label': method.replace('_', ' ').title(),
                'data': values
            })

        return chart_data
```

---

### Step 2: API Endpoints

Add to `src/api/main.py`:

```python
from database.historical_analysis import HistoricalVaRAnalyzer

@app.get("/api/v1/var/trend/{ticker}")
async def get_var_trend(
    ticker: str,
    method: str = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get VaR trend analysis"""

    analyzer = HistoricalVaRAnalyzer(db)
    trend = analyzer.calculate_var_trend(ticker, method, days)

    return {
        "ticker": ticker,
        "method": method or "all",
        "days": days,
        "trend": trend
    }


@app.get("/api/v1/var/compare/{ticker}")
async def compare_var_methods(
    ticker: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Compare VaR across different methods"""

    analyzer = HistoricalVaRAnalyzer(db)
    comparison = analyzer.compare_methods(ticker, days)

    return {
        "ticker": ticker,
        "days": days,
        "comparison": comparison
    }


@app.get("/api/v1/var/spikes/{ticker}")
async def detect_var_spikes(
    ticker: str,
    method: str = None,
    days: int = 30,
    threshold_std: float = 2.0,
    db: Session = Depends(get_db)
):
    """Detect VaR spikes (outliers)"""

    analyzer = HistoricalVaRAnalyzer(db)
    spikes = analyzer.detect_var_spikes(ticker, method, days, threshold_std)

    return {
        "ticker": ticker,
        "spikes_detected": len(spikes),
        "threshold_std": threshold_std,
        "spikes": spikes
    }


@app.get("/api/v1/var/statistics/{ticker}")
async def get_var_statistics(
    ticker: str,
    method: str = None,
    days: int = 90,
    db: Session = Depends(get_db)
):
    """Get VaR statistics"""

    analyzer = HistoricalVaRAnalyzer(db)
    stats = analyzer.get_var_statistics(ticker, method, days)

    return stats


@app.get("/api/v1/var/chart/{ticker}")
async def get_chart_data(
    ticker: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get chart-ready data for frontend"""

    analyzer = HistoricalVaRAnalyzer(db)
    chart_data = analyzer.prepare_chart_data(ticker, days)

    return chart_data


@app.post("/api/v1/var/batch-store")
async def batch_store_var(
    tickers: List[str],
    method: str = "historical",
    position_value: float = 1000000,
    db: Session = Depends(get_db)
):
    """Batch store VaR for multiple tickers"""

    results = []

    for ticker in tickers:
        try:
            # Calculate VaR
            data = data_collector.fetch_stock_data(ticker, period="2y")
            returns = preprocessor.prepare_returns_data(data)['Returns']

            var_calc = VaRCalculator(confidence_level=0.95)
            var_result = var_calc.historical_var(returns, position_value)

            # Store in database
            position = crud.get_or_create_position(db, ticker, position_value)
            var_record = crud.create_var_calculation(
                db=db,
                position_id=position.id,
                method=method,
                confidence_level=0.95,
                var_amount=var_result['VaR'],
                var_percentage=var_result['VaR_Percentage'],
                cvar_amount=var_result.get('CVaR')
            )

            results.append({
                'ticker': ticker,
                'success': True,
                'var_id': var_record.id,
                'var_amount': var_record.var_amount
            })

        except Exception as e:
            results.append({
                'ticker': ticker,
                'success': False,
                'error': str(e)
            })

    successful = sum(1 for r in results if r['success'])

    return {
        'total': len(tickers),
        'successful': successful,
        'failed': len(tickers) - successful,
        'results': results
    }
```

---

## 🧪 Test with curl

### First, Store Some Historical Data:

```bash
# Store VaR calculations over several "days" (simulate historical data)
# In real usage, this would run daily via scheduler

for i in {1..10}; do
  echo "Storing VaR calculation $i..."
  curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
    -d '{"ticker": "AAPL", "method": "historical"}' \
    -H "Content-Type: application/json" | jq '.var_id'
  sleep 1  # Small delay
done
```

### Get VaR Trend:

```bash
# Analyze VaR trend
curl -X GET "http://localhost:8000/api/v1/var/trend/AAPL?days=30" | jq '.'
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "method": "all",
  "days": 30,
  "trend": {
    "trend": "stable",
    "first_var": 28456.78,
    "last_var": 29123.45,
    "change_amount": 666.67,
    "change_percentage": 2.34,
    "average_var": 28890.12,
    "min_var": 27890.23,
    "max_var": 30123.56,
    "var_volatility": 654.32,
    "data_points": 10
  }
}
```

### Compare Methods:

```bash
# First store VaR with different methods
curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -d '{"ticker": "AAPL", "method": "parametric"}' \
  -H "Content-Type: application/json" > /dev/null

curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -d '{"ticker": "AAPL", "method": "monte_carlo"}' \
  -H "Content-Type: application/json" > /dev/null

# Compare methods
curl -X GET "http://localhost:8000/api/v1/var/compare/AAPL?days=30" | jq '.'
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "days": 30,
  "comparison": {
    "methods": {
      "historical": {
        "average_var": 28890.12,
        "min_var": 27890.23,
        "max_var": 30123.56,
        "std_var": 654.32,
        "count": 10
      },
      "parametric": {
        "average_var": 29456.78,
        "min_var": 29456.78,
        "max_var": 29456.78,
        "std_var": 0,
        "count": 1
      }
    },
    "most_conservative": "parametric",
    "least_conservative": "historical",
    "var_range": {
      "min": 28890.12,
      "max": 29456.78,
      "spread": 566.66
    }
  }
}
```

### Detect VaR Spikes:

```bash
# Detect outliers/spikes
curl -X GET "http://localhost:8000/api/v1/var/spikes/AAPL?threshold_std=2.0" \
  | jq '.'
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "spikes_detected": 2,
  "threshold_std": 2.0,
  "spikes": [
    {
      "date": "2026-01-01T10:30:00",
      "var_amount": 31234.56,
      "z_score": 2.45,
      "deviation_from_mean": 1344.44,
      "severity": "medium"
    }
  ]
}
```

### Get VaR Statistics:

```bash
# Get comprehensive statistics
curl -X GET "http://localhost:8000/api/v1/var/statistics/AAPL?days=90" \
  | jq '.var_statistics'
```

**Expected:**
```json
{
  "mean": 28890.12,
  "median": 28950.34,
  "std": 654.32,
  "min": 27890.23,
  "max": 30123.56,
  "q25": 28234.45,
  "q75": 29567.89
}
```

### Get Chart Data:

```bash
# Get data formatted for charting
curl -X GET "http://localhost:8000/api/v1/var/chart/AAPL?days=30" | jq '.'
```

**Expected:**
```json
{
  "labels": ["2025-12-02", "2025-12-03", "2025-12-04", ...],
  "datasets": [
    {
      "label": "Historical",
      "data": [28456.78, 28890.12, 29123.45, ...]
    },
    {
      "label": "Parametric",
      "data": [29456.78, null, 29567.89, ...]
    }
  ]
}
```

### Batch Store VaR:

```bash
# Store VaR for multiple tickers at once
curl -X POST "http://localhost:8000/api/v1/var/batch-store" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "JNJ"],
    "method": "historical",
    "position_value": 1000000
  }' | jq '.'
```

**Expected:**
```json
{
  "total": 5,
  "successful": 5,
  "failed": 0,
  "results": [
    {"ticker": "AAPL", "success": true, "var_id": 15, "var_amount": 28456.78},
    {"ticker": "MSFT", "success": true, "var_id": 16, "var_amount": 25678.90},
    {"ticker": "GOOGL", "success": true, "var_id": 17, "var_amount": 32123.45},
    {"ticker": "TSLA", "success": true, "var_id": 18, "var_amount": 45678.12},
    {"ticker": "JNJ", "success": true, "var_id": 19, "var_amount": 18234.56}
  ]
}
```

### Complete Workflow Test:

```bash
#!/bin/bash
# Complete historical VaR analysis workflow

TICKER="AAPL"

echo "=== Batch Storing VaR for Multiple Methods ==="
for method in historical parametric monte_carlo; do
  echo "Storing $method VaR..."
  curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
    -d "{\"ticker\": \"$TICKER\", \"method\": \"$method\"}" \
    -H "Content-Type: application/json" | jq '.var_id'
done

echo -e "\n=== VaR History ==="
curl -s "http://localhost:8000/api/v1/var/history/$TICKER?days=30" \
  | jq '.count'

echo -e "\n=== Method Comparison ==="
curl -s "http://localhost:8000/api/v1/var/compare/$TICKER" \
  | jq '.comparison.most_conservative'

echo -e "\n=== Trend Analysis ==="
curl -s "http://localhost:8000/api/v1/var/trend/$TICKER" \
  | jq '.trend.trend'

echo -e "\n=== Statistics ==="
curl -s "http://localhost:8000/api/v1/var/statistics/$TICKER" \
  | jq '.var_statistics | {mean, min, max}'
```

---

## ✅ Completed

✅ Historical VaR time-series storage
✅ Trend analysis (increasing/decreasing/stable)
✅ Method comparison endpoints
✅ VaR spike detection
✅ Statistical summaries
✅ Chart-ready data preparation
✅ Batch storage operations
✅ curl-based testing

**Next**: Performance Optimization (Day 023)
