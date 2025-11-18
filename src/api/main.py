"""
FastAPI Main Application for Market Risk VaR System
REST API for VaR calculations and risk analysis
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pandas as pd
import numpy as np
import sys
import os
from typing import List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.schemas import (
    DataRequest, VaRRequest, VaRResponse, MultiVaRRequest, MultiVaRResponse,
    GARCHRequest, GARCHResponse, ARIMARequest, ARIMAResponse,
    BacktestRequest, BacktestResponse, PortfolioVaRRequest, PortfolioVaRResponse,
    HealthResponse, ErrorResponse
)
from data.data_collector import DataCollector
from data.preprocessor import DataPreprocessor
from models.var_calculator import VaRCalculator
from models.garch_model import GARCHForecaster
from models.arima_model import ARIMAForecaster
from utils.backtesting import VaRBacktester

# Initialize FastAPI app
app = FastAPI(
    title="Market Risk VaR API",
    description="REST API for Value at Risk calculations using ARIMA and GARCH models",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
data_collector = DataCollector()
preprocessor = DataPreprocessor()


@app.get("/", response_model=HealthResponse)
async def root():
    """API root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now()
    )


@app.post("/api/v1/data/fetch")
async def fetch_data(request: DataRequest):
    """
    Fetch market data for a ticker

    Returns price and returns data
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
            raise HTTPException(status_code=404, detail=f"No data found for ticker {request.ticker}")

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


@app.post("/api/v1/var/calculate", response_model=VaRResponse)
async def calculate_var(request: VaRRequest):
    """
    Calculate VaR for a single ticker using specified method
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


@app.post("/api/v1/var/compare", response_model=MultiVaRResponse)
async def compare_var_methods(request: MultiVaRRequest):
    """
    Calculate VaR using all methods and compare
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


@app.post("/api/v1/garch/forecast", response_model=GARCHResponse)
async def garch_forecast(request: GARCHRequest):
    """
    Fit GARCH model and forecast volatility
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


@app.post("/api/v1/arima/forecast", response_model=ARIMAResponse)
async def arima_forecast(request: ARIMARequest):
    """
    Fit ARIMA model and forecast returns
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


@app.post("/api/v1/backtest", response_model=BacktestResponse)
async def backtest_var(request: BacktestRequest):
    """
    Backtest VaR model
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


@app.post("/api/v1/portfolio/var", response_model=PortfolioVaRResponse)
async def calculate_portfolio_var(request: PortfolioVaRRequest):
    """
    Calculate portfolio VaR with multiple tickers
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
