"""
ARIMA model forecasting endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from src.api.schemas import ARIMARequest, ARIMAResponse
from src.api.dependencies import get_data_collector, get_preprocessor
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.arima_model import ARIMAForecaster

router = APIRouter(prefix="/api/v1/arima", tags=["arima"])


@router.post("/forecast", response_model=ARIMAResponse)
async def arima_forecast(
    request: ARIMARequest,
    data_collector: DataCollector = Depends(get_data_collector),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Fit ARIMA model and forecast returns.
    """
    try:
        # Fetch and prepare data
        data = data_collector.fetch_stock_data(request.ticker, period="2y")
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {request.ticker}")

        returns_data = preprocessor.prepare_returns_data(data)
        returns = returns_data['Returns'].dropna()

        # Fit ARIMA model
        arima = ARIMAForecaster(order=(request.p, request.d, request.q))
        arima.fit(returns, optimize=request.optimize)

        # Forecast
        forecast = arima.forecast(steps=request.forecast_steps)

        # Convert forecast to list of dicts
        forecast_list = [
            {
                "step": i + 1,
                "forecast": float(forecast.iloc[i]['Forecast']),
                "lower_ci": float(forecast.iloc[i]['Lower_CI']),
                "upper_ci": float(forecast.iloc[i]['Upper_CI'])
            }
            for i in range(len(forecast))
        ]

        response = ARIMAResponse(
            ticker=request.ticker,
            model_order=f"ARIMA{arima.order}",
            aic=arima.results['aic'],
            bic=arima.results['bic'],
            forecast=forecast_list,
            calculation_date=datetime.now()
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
