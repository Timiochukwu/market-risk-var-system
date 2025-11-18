"""
Data fetching endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends

from src.api.schemas import DataRequest
from src.api.dependencies import get_data_collector, get_preprocessor
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor

router = APIRouter(prefix="/api/v1/data", tags=["data"])


@router.post("/fetch")
async def fetch_data(
    request: DataRequest,
    data_collector: DataCollector = Depends(get_data_collector),
    preprocessor: DataPreprocessor = Depends(get_preprocessor)
):
    """
    Fetch market data for a ticker.

    Returns price and returns data.
    """
    try:
        # Fetch data
        data = data_collector.fetch_stock_data(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            period=request.period
        )

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker {request.ticker}"
            )

        # Prepare returns
        returns_data = preprocessor.prepare_returns_data(data)

        # Convert to dict for response
        response = {
            "ticker": request.ticker,
            "num_records": len(returns_data),
            "start_date": str(returns_data.index[0].date()),
            "end_date": str(returns_data.index[-1].date()),
            "summary": preprocessor.get_summary_statistics(returns_data['Returns']),
            "latest_price": float(returns_data['Price'].iloc[-1])
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
