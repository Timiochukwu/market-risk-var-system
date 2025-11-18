"""
ARIMA Model Module for Market Risk VaR System
Implements ARIMA for price and returns forecasting
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import warnings
import logging
from typing import Tuple, Optional, Dict
import pickle

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ARIMAForecaster:
    """ARIMA model for time series forecasting"""

    def __init__(self, order: Tuple[int, int, int] = (1, 0, 1)):
        """
        Initialize ARIMA forecaster

        Args:
            order: ARIMA order (p, d, q)
                p: autoregressive order
                d: differencing order
                q: moving average order
        """
        self.order = order
        self.model = None
        self.fitted_model = None
        self.results = None

    def check_stationarity(self, timeseries: pd.Series, alpha: float = 0.05) -> Dict:
        """
        Check if time series is stationary using Augmented Dickey-Fuller test

        Args:
            timeseries: Time series to test
            alpha: Significance level

        Returns:
            Dictionary with test results
        """
        # Drop NaN values
        ts_clean = timeseries.dropna()

        # Perform ADF test
        adf_result = adfuller(ts_clean, autolag='AIC')

        results = {
            'adf_statistic': adf_result[0],
            'p_value': adf_result[1],
            'critical_values': adf_result[4],
            'is_stationary': adf_result[1] < alpha
        }

        logger.info(f"ADF Statistic: {results['adf_statistic']:.4f}")
        logger.info(f"P-value: {results['p_value']:.4f}")
        logger.info(f"Is Stationary: {results['is_stationary']}")

        return results

    def find_optimal_order(
        self,
        timeseries: pd.Series,
        max_p: int = 5,
        max_d: int = 2,
        max_q: int = 5
    ) -> Tuple[int, int, int]:
        """
        Find optimal ARIMA order using AIC

        Args:
            timeseries: Time series data
            max_p: Maximum p value to test
            max_d: Maximum d value to test
            max_q: Maximum q value to test

        Returns:
            Optimal (p, d, q) order
        """
        logger.info("Searching for optimal ARIMA order...")

        best_aic = np.inf
        best_order = (1, 0, 1)

        ts_clean = timeseries.dropna()

        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    try:
                        model = ARIMA(ts_clean, order=(p, d, q))
                        fitted = model.fit()
                        aic = fitted.aic

                        if aic < best_aic:
                            best_aic = aic
                            best_order = (p, d, q)

                    except Exception:
                        continue

        logger.info(f"Optimal order: {best_order} with AIC: {best_aic:.2f}")
        self.order = best_order
        return best_order

    def fit(self, timeseries: pd.Series, optimize: bool = False) -> None:
        """
        Fit ARIMA model to time series

        Args:
            timeseries: Time series data
            optimize: Whether to optimize order automatically
        """
        ts_clean = timeseries.dropna()

        if optimize:
            self.find_optimal_order(ts_clean)

        logger.info(f"Fitting ARIMA{self.order} model...")

        try:
            self.model = ARIMA(ts_clean, order=self.order)
            self.fitted_model = self.model.fit()
            logger.info("Model fitted successfully")

            # Store results
            self.results = {
                'aic': self.fitted_model.aic,
                'bic': self.fitted_model.bic,
                'hqic': self.fitted_model.hqic,
                'order': self.order
            }

            logger.info(f"AIC: {self.fitted_model.aic:.2f}")
            logger.info(f"BIC: {self.fitted_model.bic:.2f}")

        except Exception as e:
            logger.error(f"Error fitting model: {str(e)}")
            raise

    def forecast(self, steps: int = 10, alpha: float = 0.05) -> pd.DataFrame:
        """
        Generate forecasts

        Args:
            steps: Number of steps to forecast
            alpha: Significance level for confidence intervals

        Returns:
            DataFrame with forecasts and confidence intervals
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")

        logger.info(f"Generating {steps}-step forecast...")

        # Generate forecast
        forecast_result = self.fitted_model.forecast(steps=steps, alpha=alpha)

        # Get prediction results with confidence intervals
        predictions = self.fitted_model.get_forecast(steps=steps, alpha=alpha)
        forecast_df = predictions.summary_frame()

        # Rename columns for clarity
        forecast_df.columns = ['Forecast', 'Std_Error', 'Lower_CI', 'Upper_CI']

        logger.info(f"Forecast generated for {steps} periods")
        return forecast_df

    def predict_in_sample(self) -> pd.Series:
        """
        Generate in-sample predictions

        Returns:
            Series with in-sample predictions
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before prediction")

        predictions = self.fitted_model.fittedvalues
        return predictions

    def calculate_residuals(self) -> pd.Series:
        """
        Calculate model residuals

        Returns:
            Series with residuals
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before calculating residuals")

        return self.fitted_model.resid

    def get_model_summary(self) -> str:
        """
        Get detailed model summary

        Returns:
            String with model summary
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before getting summary")

        return str(self.fitted_model.summary())

    def evaluate_forecast_accuracy(
        self,
        actual: pd.Series,
        predicted: pd.Series
    ) -> Dict[str, float]:
        """
        Evaluate forecast accuracy

        Args:
            actual: Actual values
            predicted: Predicted values

        Returns:
            Dictionary with accuracy metrics
        """
        # Align series
        actual = actual.dropna()
        predicted = predicted.dropna()

        # Calculate metrics
        errors = actual - predicted
        mse = np.mean(errors ** 2)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(errors))
        mape = np.mean(np.abs(errors / actual)) * 100

        metrics = {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape
        }

        logger.info("Forecast Accuracy Metrics:")
        for key, value in metrics.items():
            logger.info(f"{key}: {value:.6f}")

        return metrics

    def save_model(self, filepath: str) -> None:
        """
        Save fitted model to file

        Args:
            filepath: Path to save model
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before saving")

        with open(filepath, 'wb') as f:
            pickle.dump({
                'fitted_model': self.fitted_model,
                'order': self.order,
                'results': self.results
            }, f)

        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str) -> None:
        """
        Load fitted model from file

        Args:
            filepath: Path to load model from
        """
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.fitted_model = data['fitted_model']
        self.order = data['order']
        self.results = data['results']

        logger.info(f"Model loaded from {filepath}")

    def diagnose_residuals(self) -> pd.DataFrame:
        """
        Diagnose model residuals

        Returns:
            DataFrame with residual statistics
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before diagnosing residuals")

        residuals = self.calculate_residuals()

        diagnostics = pd.DataFrame({
            'Mean': [residuals.mean()],
            'Std': [residuals.std()],
            'Min': [residuals.min()],
            'Max': [residuals.max()],
            'Skewness': [residuals.skew()],
            'Kurtosis': [residuals.kurtosis()]
        })

        return diagnostics


class AutoARIMA:
    """Automated ARIMA model selection and forecasting"""

    def __init__(self):
        """Initialize AutoARIMA"""
        self.best_model = None
        self.best_order = None

    def fit_predict(
        self,
        timeseries: pd.Series,
        forecast_steps: int = 10,
        max_p: int = 3,
        max_d: int = 2,
        max_q: int = 3
    ) -> Tuple[ARIMAForecaster, pd.DataFrame]:
        """
        Automatically fit and predict using best ARIMA model

        Args:
            timeseries: Time series data
            forecast_steps: Number of steps to forecast
            max_p: Maximum p value
            max_d: Maximum d value
            max_q: Maximum q value

        Returns:
            Tuple of (fitted_model, forecast_dataframe)
        """
        forecaster = ARIMAForecaster()

        # Find optimal order
        best_order = forecaster.find_optimal_order(
            timeseries, max_p=max_p, max_d=max_d, max_q=max_q
        )

        # Fit model
        forecaster.fit(timeseries)

        # Generate forecast
        forecast = forecaster.forecast(steps=forecast_steps)

        self.best_model = forecaster
        self.best_order = best_order

        return forecaster, forecast


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor

    # Collect and prepare data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="2y")

    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)

    # Use returns for forecasting
    returns = returns_data['Returns'].dropna()

    # Initialize ARIMA model
    arima = ARIMAForecaster(order=(2, 0, 2))

    # Check stationarity
    stationarity = arima.check_stationarity(returns)

    # Fit model
    arima.fit(returns, optimize=False)

    # Generate forecast
    forecast = arima.forecast(steps=30)
    print("\nForecast:")
    print(forecast)

    # Get model summary
    print("\nModel Summary:")
    print(arima.get_model_summary())

    # Evaluate in-sample predictions
    predictions = arima.predict_in_sample()
    metrics = arima.evaluate_forecast_accuracy(
        returns[len(returns) - len(predictions):], predictions
    )
