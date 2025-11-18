"""
VaR backtesting endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import pandas as pd

from src.api.schemas import BacktestRequest, BacktestResponse
from src.api.dependencies import get_data_collector, get_preprocessor
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator
from src.utils.backtesting import VaRBacktester

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])


@router.post("/var", response_model=BacktestResponse)
async def backtest_var(
    request: BacktestRequest,
    data_collector: DataCollector = Depends(get_data_collector),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Backtest VaR model.
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
            raise HTTPException(status_code=400, detail="Only historical and parametric methods supported for backtesting")

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
            method=request.method.value,
            confidence_level=request.confidence_level,
            num_observations=backtest_results['num_observations'],
            num_exceptions=backtest_results['num_exceptions'],
            exception_rate=backtest_results['exception_rate'],
            expected_rate=backtest_results['expected_rate'],
            kupiec_test=backtest_results['kupiec_test'],
            christoffersen_test=backtest_results['christoffersen_test'],
            traffic_light_zone=backtest_results['traffic_light_test']['Zone'],
            mean_excess_loss=float(backtest_results['mean_excess_loss']) if not pd.isna(backtest_results['mean_excess_loss']) else 0.0,
            max_excess_loss=float(backtest_results['max_excess_loss']),
            calculation_date=datetime.now()
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
