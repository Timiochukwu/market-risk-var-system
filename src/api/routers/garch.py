"""
GARCH model forecasting endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from src.api.schemas import GARCHRequest, GARCHResponse
from src.api.dependencies import get_data_collector, get_preprocessor
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.garch_model import GARCHForecaster

router = APIRouter(prefix="/api/v1/garch", tags=["garch"])


@router.post("/forecast", response_model=GARCHResponse)
async def garch_forecast(
    request: GARCHRequest,
    data_collector: DataCollector = Depends(get_data_collector),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Fit GARCH model and forecast volatility.
    """
    try:
        # Fetch and prepare data
        data = data_collector.fetch_stock_data(request.ticker, period="2y")
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.ticker}")

        returns_data = preprocessor.prepare_returns_data(data)
        returns = returns_data['Returns'].dropna()

        # Fit GARCH model
        garch = GARCHForecaster(
            p=request.p,
            q=request.q,
            dist=request.distribution.value
        )
        garch.fit(returns)

        # Forecast
        forecast = garch.forecast(horizon=request.forecast_horizon)

        # Convert forecast to list of dicts
        forecast_list = [
            {
                "horizon": i + 1,
                "variance": float(forecast.iloc[i]['Variance']),
                "volatility": float(forecast.iloc[i]['Volatility'])
            }
            for i in range(len(forecast))
        ]

        response = GARCHResponse(
            ticker=request.ticker,
            model_order=f"GARCH({request.p},{request.q})",
            distribution=request.distribution.value,
            aic=garch.results['aic'],
            bic=garch.results['bic'],
            forecast=forecast_list,
            calculation_date=datetime.now()
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
