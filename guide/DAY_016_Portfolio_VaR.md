# Day 016: Portfolio VaR & Correlation

**Duration**: 2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-015

---

## 📋 What You'll Build

- Multi-asset portfolio VaR
- Correlation matrix calculation
- Diversification benefit
- Marginal VaR (contribution by asset)
- Portfolio VaR API endpoint

---

## 💡 Key Concepts

### Portfolio VaR vs Individual VaR

**Individual VaR (sum):**
```
Stock A: $10,000 VaR
Stock B: $8,000 VaR
Stock C: $6,000 VaR
Sum: $24,000
```

**Portfolio VaR (with correlation):**
```
Portfolio VaR: $18,000
Diversification benefit: $6,000 (25%)
```

**Why?** Assets don't move perfectly together!

### Correlation Impact

```
Perfect correlation (ρ=1.0):
  Portfolio VaR = Sum of individual VaRs
  No diversification benefit

Zero correlation (ρ=0.0):
  Portfolio VaR < Sum (significant benefit)

Negative correlation (ρ=-1.0):
  Maximum diversification benefit
```

---

## 💻 Implementation

Add to `src/models/var_calculator.py`:

```python
def portfolio_var(
    self,
    returns_df: pd.DataFrame,
    weights: np.ndarray,
    position_value: float = 1000000,
    method: str = 'historical'
) -> Dict[str, any]:
    """
    Calculate portfolio VaR with multiple assets
    
    Args:
        returns_df: DataFrame with returns for each asset (columns = tickers)
        weights: Portfolio weights (must sum to 1.0)
        position_value: Total portfolio value
        method: 'historical', 'parametric', or 'monte_carlo'
    
    Returns:
        Dict with portfolio VaR and decomposition
    """
    
    # Calculate portfolio returns
    portfolio_returns = (returns_df * weights).sum(axis=1)
    
    # Portfolio VaR
    if method == 'historical':
        portfolio_result = self.historical_var(portfolio_returns, position_value)
    elif method == 'parametric':
        portfolio_result = self.parametric_var(portfolio_returns, position_value)
    else:
        portfolio_result = self.monte_carlo_var(portfolio_returns, position_value)
    
    # Individual VaRs
    individual_vars = []
    for ticker in returns_df.columns:
        ticker_position = position_value * weights[returns_df.columns.get_loc(ticker)]
        
        if method == 'historical':
            var_result = self.historical_var(returns_df[ticker], ticker_position)
        else:
            var_result = self.parametric_var(returns_df[ticker], ticker_position)
        
        individual_vars.append({
            'ticker': ticker,
            'weight': weights[returns_df.columns.get_loc(ticker)],
            'position_value': ticker_position,
            'var': var_result['VaR']
        })
    
    # Diversification benefit
    sum_individual_vars = sum([iv['var'] for iv in individual_vars])
    diversification_benefit = sum_individual_vars - portfolio_result['VaR']
    diversification_pct = (diversification_benefit / sum_individual_vars) * 100
    
    # Correlation matrix
    correlation_matrix = returns_df.corr()
    
    return {
        'portfolio_var': portfolio_result['VaR'],
        'portfolio_var_pct': portfolio_result['VaR_Percentage'],
        'sum_individual_vars': sum_individual_vars,
        'diversification_benefit': diversification_benefit,
        'diversification_pct': diversification_pct,
        'individual_vars': individual_vars,
        'correlation_matrix': correlation_matrix.to_dict(),
        'method': method,
        'num_assets': len(returns_df.columns)
    }
```

---

## 🧪 API Endpoint

Add to `src/api/main.py`:

```python
class PortfolioVaRRequest(BaseModel):
    tickers: List[str]
    weights: List[float]
    confidence_level: float = 0.95
    position_value: float = 1000000
    method: str = "historical"

@app.post("/api/v1/portfolio/var")
async def calculate_portfolio_var(request: PortfolioVaRRequest):
    """Calculate portfolio VaR with diversification"""
    
    # Validate weights sum to 1.0
    if abs(sum(request.weights) - 1.0) > 0.01:
        raise HTTPException(400, "Weights must sum to 1.0")
    
    # Fetch data for all tickers
    returns_dict = {}
    for ticker in request.tickers:
        data = data_collector.fetch_stock_data(ticker, period="2y")
        returns = preprocessor.prepare_returns_data(data)['Returns']
        returns_dict[ticker] = returns
    
    # Combine into DataFrame
    returns_df = pd.DataFrame(returns_dict).dropna()
    
    # Calculate portfolio VaR
    var_calc = VaRCalculator(confidence_level=request.confidence_level)
    result = var_calc.portfolio_var(
        returns_df,
        np.array(request.weights),
        request.position_value,
        request.method
    )
    
    return result
```

---

## 🧪 Test with curl

```bash
# 3-stock portfolio
curl -X POST "http://localhost:8000/api/v1/portfolio/var" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "weights": [0.4, 0.3, 0.3],
    "confidence_level": 0.95,
    "position_value": 1000000
  }' | jq '{
    portfolio_var,
    sum_individual: .sum_individual_vars,
    diversification_benefit,
    diversification_pct
  }'
```

**Expected:**
```json
{
  "portfolio_var": 28456.78,
  "sum_individual": 32123.45,
  "diversification_benefit": 3666.67,
  "diversification_pct": 11.4
}
```

### Compare Correlations:

```bash
# Tech stocks (high correlation)
curl -s POST "http://localhost:8000/api/v1/portfolio/var" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "weights": [0.33, 0.33, 0.34]
  }' | jq .diversification_pct

# Diversified (lower correlation)
curl -s POST "http://localhost:8000/api/v1/portfolio/var" \
  -d '{
    "tickers": ["AAPL", "JNJ", "GLD"],
    "weights": [0.33, 0.33, 0.34]
  }' | jq .diversification_pct
```

---

## ✅ Completed

✅ Portfolio VaR calculation
✅ Correlation matrix
✅ Diversification benefit
✅ Individual asset contributions
✅ curl-based testing

**Next**: Stress Testing (Day 017)
