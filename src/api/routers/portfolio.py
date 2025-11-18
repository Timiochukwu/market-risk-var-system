"""
Portfolio VaR calculation endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import pandas as pd
import numpy as np

from src.api.schemas import PortfolioVaRRequest, PortfolioVaRResponse
from src.api.dependencies import get_data_collector, get_preprocessor
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


@router.post("/var", response_model=PortfolioVaRResponse)
async def calculate_portfolio_var(
    request: PortfolioVaRRequest,
    data_collector: DataCollector = Depends(get_data_collector),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Calculate portfolio VaR with multiple tickers.
    """
    try:
        # Fetch data for all tickers
        returns_dict = {}

        for ticker in request.tickers:
            data = data_collector.fetch_stock_data(ticker, period="2y")
            if data.empty:
                raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

            returns_data = preprocessor.prepare_returns_data(data)
            returns_dict[ticker] = returns_data['Returns'].dropna()

        # Combine returns into DataFrame
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()

        # Calculate weighted portfolio returns
        weights = np.array(request.weights)
        portfolio_returns = (returns_df * weights).sum(axis=1)

        # Calculate portfolio VaR
        var_calc = VaRCalculator(confidence_level=request.confidence_level)

        if request.method == "historical":
            portfolio_result = var_calc.historical_var(portfolio_returns, request.position_value)
        elif request.method == "parametric":
            portfolio_result = var_calc.parametric_var(portfolio_returns, request.position_value)
        else:
            portfolio_result = var_calc.monte_carlo_var(portfolio_returns, request.position_value)

        # Calculate individual VaRs
        individual_vars = []
        for ticker, weight in zip(request.tickers, request.weights):
            individual_position = request.position_value * weight
            if request.method == "historical":
                ind_result = var_calc.historical_var(returns_df[ticker], individual_position)
            else:
                ind_result = var_calc.parametric_var(returns_df[ticker], individual_position)

            individual_vars.append({
                "ticker": ticker,
                "weight": weight,
                "var": ind_result['VaR']
            })

        # Calculate diversification benefit
        sum_individual_vars = sum([iv['var'] for iv in individual_vars])
        diversification_benefit = sum_individual_vars - portfolio_result['VaR']

        # Calculate correlation matrix
        corr_matrix = returns_df.corr().values.tolist()

        response = PortfolioVaRResponse(
            tickers=request.tickers,
            weights=request.weights,
            confidence_level=request.confidence_level,
            position_value=request.position_value,
            portfolio_var=portfolio_result['VaR'],
            portfolio_es=portfolio_result.get('ES', 0),
            diversification_benefit=diversification_benefit,
            individual_vars=individual_vars,
            correlation_matrix=corr_matrix,
            calculation_date=datetime.now()
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
