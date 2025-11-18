"""
Data-related schemas.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class DataRequest(BaseModel):
    """Request schema for fetching market data."""
    ticker: str = Field(..., description="Stock ticker symbol", example="AAPL")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)", example="2022-01-01")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)", example="2024-01-01")
    period: Optional[str] = Field("2y", description="Period to fetch", example="2y")

    @validator('ticker')
    def ticker_must_be_uppercase(cls, v):
        return v.upper()
