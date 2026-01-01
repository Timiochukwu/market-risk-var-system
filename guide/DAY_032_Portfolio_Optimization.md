# Day 032: Advanced Portfolio Optimization

**Duration**: 2-2.5 hours | **Difficulty**: Advanced | **Prerequisites**: Day 001-031

---

## 📋 What You'll Build

- Mean-Variance Optimization (Markowitz)
- Efficient Frontier calculation
- Risk Parity portfolio
- Maximum Sharpe Ratio portfolio
- Minimum VaR portfolio
- Constraint-based optimization

---

## 💡 Portfolio Optimization Strategies

```
┌──────────────────────────────────────┐
│  Portfolio Optimization Goals        │
├──────────────────────────────────────┤
│  1. Maximize Return (for given risk) │
│  2. Minimize Risk (for given return) │
│  3. Maximize Sharpe Ratio            │
│  4. Minimize VaR                     │
│  5. Risk Parity (equal risk contrib) │
└──────────────────────────────────────┘
```

---

## 💻 Implementation

### Step 1: Install Dependencies

```bash
pip install cvxpy==1.4.1 scipy==1.11.4
```

---

### Step 2: Portfolio Optimizer

Create `src/optimization/portfolio_optimizer.py`:

```python
"""
Advanced Portfolio Optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy.optimize import minimize
import cvxpy as cp
import logging

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """Advanced portfolio optimization strategies"""

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize portfolio optimizer

        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.risk_free_rate = risk_free_rate / 252  # Daily rate

    def calculate_portfolio_metrics(
        self,
        weights: np.ndarray,
        returns_df: pd.DataFrame
    ) -> Dict:
        """
        Calculate portfolio metrics

        Args:
            weights: Portfolio weights
            returns_df: DataFrame of returns (each column is an asset)

        Returns:
            Dictionary of metrics
        """
        # Portfolio returns
        portfolio_returns = (returns_df * weights).sum(axis=1)

        # Expected return (annualized)
        expected_return = portfolio_returns.mean() * 252

        # Volatility (annualized)
        volatility = portfolio_returns.std() * np.sqrt(252)

        # Sharpe Ratio
        sharpe_ratio = (expected_return - self.risk_free_rate * 252) / volatility

        # Covariance matrix
        cov_matrix = returns_df.cov() * 252  # Annualized

        # Portfolio variance
        portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
        portfolio_std = np.sqrt(portfolio_variance)

        return {
            'expected_return': expected_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'weights': weights.tolist(),
            'portfolio_variance': portfolio_variance,
            'portfolio_std': portfolio_std
        }

    def efficient_frontier(
        self,
        returns_df: pd.DataFrame,
        num_portfolios: int = 100
    ) -> List[Dict]:
        """
        Calculate efficient frontier

        Args:
            returns_df: DataFrame of returns
            num_portfolios: Number of portfolios to generate

        Returns:
            List of portfolio metrics along frontier
        """
        logger.info(f"Calculating efficient frontier with {num_portfolios} portfolios")

        n_assets = len(returns_df.columns)
        results = []

        # Calculate return range
        mean_returns = returns_df.mean() * 252
        min_return = mean_returns.min()
        max_return = mean_returns.max()

        target_returns = np.linspace(min_return, max_return, num_portfolios)

        for target_return in target_returns:
            # Optimize for minimum variance given target return
            weights = self._optimize_min_variance(
                returns_df,
                target_return=target_return
            )

            if weights is not None:
                metrics = self.calculate_portfolio_metrics(weights, returns_df)
                metrics['target_return'] = target_return
                results.append(metrics)

        logger.info(f"Calculated {len(results)} efficient portfolios")
        return results

    def _optimize_min_variance(
        self,
        returns_df: pd.DataFrame,
        target_return: float = None
    ) -> np.ndarray:
        """
        Optimize for minimum variance

        Args:
            returns_df: DataFrame of returns
            target_return: Target annual return (if None, just minimize variance)

        Returns:
            Optimal weights
        """
        n_assets = len(returns_df.columns)

        # Covariance matrix (annualized)
        cov_matrix = returns_df.cov().values * 252

        # Variables
        weights = cp.Variable(n_assets)

        # Objective: minimize portfolio variance
        portfolio_variance = cp.quad_form(weights, cov_matrix)
        objective = cp.Minimize(portfolio_variance)

        # Constraints
        constraints = [
            cp.sum(weights) == 1,  # Weights sum to 1
            weights >= 0  # No short selling
        ]

        # Add return constraint if specified
        if target_return is not None:
            mean_returns = returns_df.mean().values * 252
            expected_return = weights @ mean_returns
            constraints.append(expected_return >= target_return)

        # Solve
        problem = cp.Problem(objective, constraints)

        try:
            problem.solve()

            if weights.value is not None:
                return weights.value
            else:
                return None
        except:
            return None

    def max_sharpe_ratio(
        self,
        returns_df: pd.DataFrame
    ) -> Dict:
        """
        Find portfolio with maximum Sharpe ratio

        Args:
            returns_df: DataFrame of returns

        Returns:
            Optimal portfolio metrics
        """
        logger.info("Optimizing for maximum Sharpe ratio")

        n_assets = len(returns_df.columns)
        mean_returns = returns_df.mean().values * 252
        cov_matrix = returns_df.cov().values * 252

        def neg_sharpe(weights):
            """Negative Sharpe ratio (for minimization)"""
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe = (portfolio_return - self.risk_free_rate * 252) / portfolio_std
            return -sharpe

        # Constraints
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Sum to 1
        )

        # Bounds (0 to 1 for each weight, no short selling)
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess (equal weights)
        initial_weights = np.array([1/n_assets] * n_assets)

        # Optimize
        result = minimize(
            neg_sharpe,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            optimal_weights = result.x
            metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            metrics['optimization'] = 'max_sharpe'
            return metrics
        else:
            raise ValueError("Optimization failed")

    def min_var_portfolio(
        self,
        returns_df: pd.DataFrame
    ) -> Dict:
        """
        Find minimum variance portfolio

        Args:
            returns_df: DataFrame of returns

        Returns:
            Minimum variance portfolio metrics
        """
        logger.info("Optimizing for minimum variance")

        optimal_weights = self._optimize_min_variance(returns_df)

        if optimal_weights is not None:
            metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            metrics['optimization'] = 'min_variance'
            return metrics
        else:
            raise ValueError("Optimization failed")

    def risk_parity_portfolio(
        self,
        returns_df: pd.DataFrame
    ) -> Dict:
        """
        Risk Parity portfolio (equal risk contribution)

        Args:
            returns_df: DataFrame of returns

        Returns:
            Risk parity portfolio metrics
        """
        logger.info("Calculating risk parity portfolio")

        n_assets = len(returns_df.columns)
        cov_matrix = returns_df.cov().values * 252

        def risk_contribution_diff(weights):
            """
            Difference in risk contributions
            (should be zero for risk parity)
            """
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib

            # Target: equal risk contribution
            target = portfolio_variance / n_assets

            return np.sum((risk_contrib - target) ** 2)

        # Constraints
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        )

        # Bounds
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess
        initial_weights = np.array([1/n_assets] * n_assets)

        # Optimize
        result = minimize(
            risk_contribution_diff,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            optimal_weights = result.x
            metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
            metrics['optimization'] = 'risk_parity'
            return metrics
        else:
            raise ValueError("Optimization failed")

    def constrained_optimization(
        self,
        returns_df: pd.DataFrame,
        min_weights: Dict[str, float] = None,
        max_weights: Dict[str, float] = None,
        sector_constraints: Dict[str, float] = None
    ) -> Dict:
        """
        Portfolio optimization with constraints

        Args:
            returns_df: DataFrame of returns
            min_weights: Minimum weights per asset
            max_weights: Maximum weights per asset
            sector_constraints: Maximum allocation per sector

        Returns:
            Optimal portfolio with constraints
        """
        logger.info("Optimizing with constraints")

        n_assets = len(returns_df.columns)
        tickers = returns_df.columns.tolist()

        # Default constraints (0-100%)
        if min_weights is None:
            min_weights = {ticker: 0.0 for ticker in tickers}
        if max_weights is None:
            max_weights = {ticker: 1.0 for ticker in tickers}

        mean_returns = returns_df.mean().values * 252
        cov_matrix = returns_df.cov().values * 252

        # Variables
        weights = cp.Variable(n_assets)

        # Objective: maximize Sharpe ratio (minimize negative Sharpe)
        portfolio_return = weights @ mean_returns
        portfolio_variance = cp.quad_form(weights, cov_matrix)
        portfolio_std = cp.sqrt(portfolio_variance)

        # Approximate Sharpe maximization
        objective = cp.Maximize(portfolio_return - 0.5 * portfolio_variance)

        # Constraints
        constraints = [
            cp.sum(weights) == 1,
            weights >= 0
        ]

        # Add min/max constraints
        for i, ticker in enumerate(tickers):
            if ticker in min_weights:
                constraints.append(weights[i] >= min_weights[ticker])
            if ticker in max_weights:
                constraints.append(weights[i] <= max_weights[ticker])

        # Solve
        problem = cp.Problem(objective, constraints)

        try:
            problem.solve()

            if weights.value is not None:
                optimal_weights = weights.value
                metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)
                metrics['optimization'] = 'constrained'
                metrics['constraints'] = {
                    'min_weights': min_weights,
                    'max_weights': max_weights
                }
                return metrics
            else:
                raise ValueError("Optimization failed")
        except Exception as e:
            raise ValueError(f"Optimization failed: {e}")
```

---

### Step 3: API Endpoints

Add to `src/api/main.py`:

```python
from optimization.portfolio_optimizer import PortfolioOptimizer

@app.post("/api/v1/portfolio/optimize")
async def optimize_portfolio(
    tickers: List[str],
    strategy: str = "max_sharpe",  # max_sharpe, min_variance, risk_parity
    constraints: dict = None,
    current_user: User = Depends(get_current_active_user)
):
    """Optimize portfolio allocation"""

    # Fetch data for all tickers
    from data.async_collector import fetch_multiple_sync
    ticker_data = fetch_multiple_sync(tickers, period="2y")

    # Calculate returns for each ticker
    returns_dict = {}
    for ticker, data in ticker_data.items():
        returns = preprocessor.prepare_returns_data(data)['Returns']
        returns_dict[ticker] = returns

    # Create returns DataFrame
    returns_df = pd.DataFrame(returns_dict)

    # Initialize optimizer
    optimizer = PortfolioOptimizer(risk_free_rate=0.02)

    # Optimize based on strategy
    if strategy == "max_sharpe":
        result = optimizer.max_sharpe_ratio(returns_df)
    elif strategy == "min_variance":
        result = optimizer.min_var_portfolio(returns_df)
    elif strategy == "risk_parity":
        result = optimizer.risk_parity_portfolio(returns_df)
    elif strategy == "constrained":
        result = optimizer.constrained_optimization(
            returns_df,
            min_weights=constraints.get('min_weights'),
            max_weights=constraints.get('max_weights')
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid strategy")

    # Format weights with tickers
    allocation = {
        ticker: weight
        for ticker, weight in zip(tickers, result['weights'])
    }

    return {
        "tickers": tickers,
        "strategy": strategy,
        "allocation": allocation,
        "expected_return": result['expected_return'],
        "volatility": result['volatility'],
        "sharpe_ratio": result['sharpe_ratio']
    }


@app.post("/api/v1/portfolio/efficient-frontier")
async def calculate_efficient_frontier(
    tickers: List[str],
    num_portfolios: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """Calculate efficient frontier"""

    # Fetch data
    from data.async_collector import fetch_multiple_sync
    ticker_data = fetch_multiple_sync(tickers, period="2y")

    # Calculate returns
    returns_dict = {}
    for ticker, data in ticker_data.items():
        returns = preprocessor.prepare_returns_data(data)['Returns']
        returns_dict[ticker] = returns

    returns_df = pd.DataFrame(returns_dict)

    # Calculate frontier
    optimizer = PortfolioOptimizer()
    frontier = optimizer.efficient_frontier(returns_df, num_portfolios)

    return {
        "tickers": tickers,
        "num_portfolios": len(frontier),
        "frontier": frontier
    }
```

---

## 🧪 Test with curl

### Maximum Sharpe Ratio Portfolio:

```bash
# Find optimal portfolio weights (max Sharpe)
curl -X POST "http://localhost:8000/api/v1/portfolio/optimize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL", "JNJ", "JPM"],
    "strategy": "max_sharpe"
  }' | jq '.'
```

**Expected:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL", "JNJ", "JPM"],
  "strategy": "max_sharpe",
  "allocation": {
    "AAPL": 0.35,
    "MSFT": 0.28,
    "GOOGL": 0.22,
    "JNJ": 0.10,
    "JPM": 0.05
  },
  "expected_return": 0.185,
  "volatility": 0.22,
  "sharpe_ratio": 0.75
}
```

### Minimum Variance Portfolio:

```bash
# Find minimum risk portfolio
curl -X POST "http://localhost:8000/api/v1/portfolio/optimize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL", "JNJ", "JPM"],
    "strategy": "min_variance"
  }' | jq '.allocation'
```

### Risk Parity Portfolio:

```bash
# Equal risk contribution
curl -X POST "http://localhost:8000/api/v1/portfolio/optimize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL", "JNJ", "JPM"],
    "strategy": "risk_parity"
  }' | jq '.'
```

### Constrained Optimization:

```bash
# Optimize with constraints (min 10% in JNJ, max 30% in any tech stock)
curl -X POST "http://localhost:8000/api/v1/portfolio/optimize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL", "JNJ", "JPM"],
    "strategy": "constrained",
    "constraints": {
      "min_weights": {"JNJ": 0.10},
      "max_weights": {"AAPL": 0.30, "MSFT": 0.30, "GOOGL": 0.30}
    }
  }' | jq '.allocation'
```

### Efficient Frontier:

```bash
# Calculate 100 efficient portfolios
curl -X POST "http://localhost:8000/api/v1/portfolio/efficient-frontier" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "num_portfolios": 100
  }' | jq '.frontier | length'
```

**Expected:**
```json
100
```

View specific frontier points:

```bash
curl -X POST "http://localhost:8000/api/v1/portfolio/efficient-frontier" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tickers": ["AAPL", "MSFT", "GOOGL"]}' \
  -H "Content-Type: application/json" \
  | jq '.frontier[0:5] | .[] | {return: .expected_return, risk: .volatility, sharpe: .sharpe_ratio}'
```

---

## 📊 Portfolio Strategies Comparison

| Strategy | Goal | Best For | Constraints |
|----------|------|----------|-------------|
| **Max Sharpe** | Best risk-adjusted return | Growth portfolios | None |
| **Min Variance** | Lowest risk | Conservative investors | None |
| **Risk Parity** | Equal risk from each asset | Diversification | None |
| **Constrained** | Custom requirements | Institutional mandates | Custom |

---

## ✅ Completed

✅ Mean-Variance Optimization (Markowitz)
✅ Efficient Frontier calculation
✅ Maximum Sharpe Ratio portfolio
✅ Minimum Variance portfolio
✅ Risk Parity portfolio
✅ Constrained optimization
✅ API endpoints for all strategies
✅ curl-based testing

**Next**: Regulatory Reporting (Basel III) (Day 033)
