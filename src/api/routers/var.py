"""
VaR calculation endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from src.api.schemas import VaRRequest, VaRResponse, MultiVaRRequest, MultiVaRResponse
from src.api.dependencies import get_data_collector, get_preprocessor
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator
from src.models.garch_model import GARCHForecaster

router = APIRouter(prefix="/api/v1/var", tags=["var"])


@router.post("/calculate", response_model=VaRResponse)
async def calculate_var(
    request: VaRRequest,
    data_collector: DataCollector = Depends(get_data_collector),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Calculate VaR for a single ticker using specified method.
    """
    try:
        # Fetch and prepare data
        data = data_collector.fetch_stock_data(request.ticker, period="2y")
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.ticker}")

        returns_data = preprocessor.prepare_returns_data(data)
        returns = returns_data['Returns'].dropna()

        # Initialize VaR calculator
        var_calc = VaRCalculator(confidence_level=request.confidence_level)

        # Calculate VaR based on method
        if request.method == "historical":
            result = var_calc.historical_var(
                returns,
                position_value=request.position_value,
                window=request.window
            )

        elif request.method == "parametric":
            result = var_calc.parametric_var(
                returns,
                position_value=request.position_value,
                distribution=request.distribution.value
            )

        elif request.method == "monte_carlo":
            result = var_calc.monte_carlo_var(
                returns,
                position_value=request.position_value,
                simulations=request.simulations,
                horizon=request.horizon
            )

        elif request.method == "garch":
            # Fit GARCH model
            garch = GARCHForecaster(p=1, q=1)
            garch.fit(returns)
            forecast = garch.forecast(horizon=1)

            result = var_calc.garch_var(
                forecast['Volatility'],
                position_value=request.position_value,
                distribution=request.distribution.value
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid VaR method")

        # Create response
        response = VaRResponse(
            ticker=request.ticker,
            method=result['Method'],
            confidence_level=request.confidence_level,
            position_value=request.position_value,
            var_amount=result['VaR'],
            var_percentage=result.get('VaR_Percentage', 0),
            expected_shortfall=result.get('ES'),
            calculation_date=datetime.now(),
            additional_info={
                k: v for k, v in result.items()
                if k not in ['VaR', 'ES', 'VaR_Percentage', 'Method']
            }
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=MultiVaRResponse)
async def compare_var_methods(
    request: MultiVaRRequest,
    data_collector: DataCollector = Depends(get_data_collector),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Calculate VaR using all methods and compare.
    """
    try:
        # Fetch and prepare data
        data = data_collector.fetch_stock_data(request.ticker, period="2y")
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.ticker}")

        returns_data = preprocessor.prepare_returns_data(data)
        returns = returns_data['Returns'].dropna()

        # Initialize calculator
        var_calc = VaRCalculator(confidence_level=request.confidence_level)

        # Get GARCH forecast if requested
        garch_forecast = None
        if request.include_garch:
            garch = GARCHForecaster(p=1, q=1)
            garch.fit(returns)
            garch_forecast = garch.forecast(horizon=1)['Volatility']

        # Calculate all methods
        all_results = var_calc.calculate_all_methods(
            returns,
            position_value=request.position_value,
            garch_forecast=garch_forecast
        )

        # Convert to VaRResponse list
        var_estimates = []
        for _, row in all_results.iterrows():
            var_estimates.append(
                VaRResponse(
                    ticker=request.ticker,
                    method=row['Method'],
                    confidence_level=request.confidence_level,
                    position_value=request.position_value,
                    var_amount=row['VaR'],
                    var_percentage=row.get('VaR_Percentage', 0),
                    expected_shortfall=row.get('ES'),
                    calculation_date=datetime.now()
                )
            )

        # Calculate summary
        summary = {
            "min_var": float(all_results['VaR'].min()),
            "max_var": float(all_results['VaR'].max()),
            "mean_var": float(all_results['VaR'].mean()),
            "std_var": float(all_results['VaR'].std())
        }

        response = MultiVaRResponse(
            ticker=request.ticker,
            confidence_level=request.confidence_level,
            position_value=request.position_value,
            var_estimates=var_estimates,
            calculation_date=datetime.now(),
            summary=summary
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
