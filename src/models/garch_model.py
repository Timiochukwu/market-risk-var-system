"""
GARCH Model Module for Market Risk VaR System
Implements GARCH for volatility forecasting
"""

import pandas as pd
import numpy as np
from arch import arch_model
from arch.univariate import ConstantMean, GARCH, Normal, StudentsT
import warnings
import logging
from typing import Dict, Optional, Tuple
import pickle

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GARCHForecaster:
    """GARCH model for volatility forecasting"""

    def __init__(
        self,
        p: int = 1,
        q: int = 1,
        mean: str = 'Zero',
        dist: str = 'normal'
    ):
        """
        Initialize GARCH forecaster

        Args:
            p: GARCH lag order
            q: ARCH lag order
            mean: Mean model ('Zero', 'Constant', 'AR')
            dist: Error distribution ('normal', 't', 'skewt')
        """
        self.p = p
        self.q = q
        self.mean = mean
        self.dist = dist
        self.model = None
        self.fitted_model = None
        self.results = None

    def fit(self, returns: pd.Series, rescale: bool = True) -> None:
        """
        Fit GARCH model to returns

        Args:
            returns: Return series
            rescale: Whether to rescale returns (percentage)
        """
        # Clean data
        returns_clean = returns.dropna()

        # Rescale to percentage if needed
        if rescale:
            returns_clean = returns_clean * 100

        logger.info(f"Fitting GARCH({self.p},{self.q}) model with {self.dist} distribution...")

        try:
            # Create GARCH model
            self.model = arch_model(
                returns_clean,
                mean=self.mean,
                vol='Garch',
                p=self.p,
                q=self.q,
                dist=self.dist
            )

            # Fit model
            self.fitted_model = self.model.fit(disp='off')

            logger.info("Model fitted successfully")

            # Store results
            self.results = {
                'aic': self.fitted_model.aic,
                'bic': self.fitted_model.bic,
                'loglikelihood': self.fitted_model.loglikelihood,
                'num_params': self.fitted_model.num_params,
                'p': self.p,
                'q': self.q
            }

            logger.info(f"AIC: {self.fitted_model.aic:.2f}")
            logger.info(f"BIC: {self.fitted_model.bic:.2f}")
            logger.info(f"Log-Likelihood: {self.fitted_model.loglikelihood:.2f}")

        except Exception as e:
            logger.error(f"Error fitting model: {str(e)}")
            raise

    def forecast(
        self,
        horizon: int = 10,
        method: str = 'analytic',
        simulations: int = 1000
    ) -> pd.DataFrame:
        """
        Forecast volatility

        Args:
            horizon: Forecast horizon
            method: Forecasting method ('analytic' or 'simulation')
            simulations: Number of simulations for simulation method

        Returns:
            DataFrame with variance and volatility forecasts
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")

        logger.info(f"Forecasting {horizon} periods ahead using {method} method...")

        if method == 'analytic':
            # Analytical forecast
            forecasts = self.fitted_model.forecast(horizon=horizon, method='analytic')

            forecast_df = pd.DataFrame({
                'Variance': forecasts.variance.values[-1, :],
                'Volatility': np.sqrt(forecasts.variance.values[-1, :])
            })

        elif method == 'simulation':
            # Simulation-based forecast
            forecasts = self.fitted_model.forecast(
                horizon=horizon,
                method='simulation',
                simulations=simulations
            )

            forecast_df = pd.DataFrame({
                'Variance': forecasts.variance.values[-1, :],
                'Volatility': np.sqrt(forecasts.variance.values[-1, :])
            })

        else:
            raise ValueError(f"Unknown method: {method}")

        # Add horizon index
        forecast_df.index = range(1, horizon + 1)
        forecast_df.index.name = 'Horizon'

        logger.info("Forecast completed")
        return forecast_df

    def conditional_volatility(self) -> pd.Series:
        """
        Get conditional volatility (fitted values)

        Returns:
            Series with conditional volatility
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before getting conditional volatility")

        return self.fitted_model.conditional_volatility

    def standardized_residuals(self) -> pd.Series:
        """
        Get standardized residuals

        Returns:
            Series with standardized residuals
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before getting residuals")

        return self.fitted_model.std_resid

    def get_model_summary(self) -> str:
        """
        Get detailed model summary

        Returns:
            String with model summary
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before getting summary")

        return str(self.fitted_model.summary())

    def get_parameters(self) -> pd.Series:
        """
        Get model parameters

        Returns:
            Series with parameter estimates
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before getting parameters")

        return self.fitted_model.params

    def calculate_var(
        self,
        forecast_volatility: pd.Series,
        confidence_level: float = 0.95,
        position_value: float = 1000000
    ) -> pd.Series:
        """
        Calculate VaR from volatility forecast

        Args:
            forecast_volatility: Forecasted volatility
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            position_value: Position value in currency

        Returns:
            Series with VaR estimates
        """
        from scipy import stats

        # Get z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)

        # Calculate VaR (assuming normal distribution)
        var = -z_score * forecast_volatility * position_value / 100

        return var

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
                'p': self.p,
                'q': self.q,
                'mean': self.mean,
                'dist': self.dist,
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
        self.p = data['p']
        self.q = data['q']
        self.mean = data['mean']
        self.dist = data['dist']
        self.results = data['results']

        logger.info(f"Model loaded from {filepath}")


class EGARCHForecaster:
    """EGARCH model for asymmetric volatility forecasting"""

    def __init__(self, p: int = 1, q: int = 1, dist: str = 'normal'):
        """
        Initialize EGARCH forecaster

        Args:
            p: EGARCH lag order
            q: ARCH lag order
            dist: Error distribution
        """
        self.p = p
        self.q = q
        self.dist = dist
        self.model = None
        self.fitted_model = None

    def fit(self, returns: pd.Series, rescale: bool = True) -> None:
        """
        Fit EGARCH model

        Args:
            returns: Return series
            rescale: Whether to rescale returns
        """
        returns_clean = returns.dropna()

        if rescale:
            returns_clean = returns_clean * 100

        logger.info(f"Fitting EGARCH({self.p},{self.q}) model...")

        try:
            self.model = arch_model(
                returns_clean,
                mean='Zero',
                vol='EGARCH',
                p=self.p,
                q=self.q,
                dist=self.dist
            )

            self.fitted_model = self.model.fit(disp='off')
            logger.info("EGARCH model fitted successfully")

        except Exception as e:
            logger.error(f"Error fitting EGARCH model: {str(e)}")
            raise

    def forecast(self, horizon: int = 10) -> pd.DataFrame:
        """
        Forecast volatility using EGARCH

        Args:
            horizon: Forecast horizon

        Returns:
            DataFrame with forecasts
        """
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")

        forecasts = self.fitted_model.forecast(horizon=horizon)

        forecast_df = pd.DataFrame({
            'Variance': forecasts.variance.values[-1, :],
            'Volatility': np.sqrt(forecasts.variance.values[-1, :])
        })

        forecast_df.index = range(1, horizon + 1)
        forecast_df.index.name = 'Horizon'

        return forecast_df


class GARCHModelSelector:
    """Automatic GARCH model selection"""

    def __init__(self):
        """Initialize model selector"""
        self.best_model = None
        self.best_params = None
        self.results = []

    def find_best_model(
        self,
        returns: pd.Series,
        max_p: int = 3,
        max_q: int = 3,
        distributions: list = ['normal', 't']
    ) -> Tuple[GARCHForecaster, Dict]:
        """
        Find best GARCH model based on AIC

        Args:
            returns: Return series
            max_p: Maximum p value
            max_q: Maximum q value
            distributions: List of distributions to test

        Returns:
            Tuple of (best_model, best_params)
        """
        logger.info("Searching for best GARCH model...")

        best_aic = np.inf
        best_model = None
        best_params = {}

        for p in range(1, max_p + 1):
            for q in range(1, max_q + 1):
                for dist in distributions:
                    try:
                        model = GARCHForecaster(p=p, q=q, dist=dist)
                        model.fit(returns)

                        aic = model.results['aic']

                        self.results.append({
                            'p': p,
                            'q': q,
                            'dist': dist,
                            'aic': aic,
                            'bic': model.results['bic']
                        })

                        if aic < best_aic:
                            best_aic = aic
                            best_model = model
                            best_params = {'p': p, 'q': q, 'dist': dist, 'aic': aic}

                    except Exception as e:
                        logger.warning(f"Failed to fit GARCH({p},{q}) with {dist}: {str(e)}")
                        continue

        logger.info(f"Best model: GARCH({best_params['p']},{best_params['q']}) "
                   f"with {best_params['dist']} distribution")
        logger.info(f"AIC: {best_params['aic']:.2f}")

        self.best_model = best_model
        self.best_params = best_params

        return best_model, best_params

    def get_results_summary(self) -> pd.DataFrame:
        """
        Get summary of all tested models

        Returns:
            DataFrame with model comparison
        """
        return pd.DataFrame(self.results).sort_values('aic')


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
    returns = returns_data['Returns'].dropna()

    # Fit GARCH model
    garch = GARCHForecaster(p=1, q=1, dist='normal')
    garch.fit(returns)

    # Get model summary
    print("\nModel Summary:")
    print(garch.get_model_summary())

    # Forecast volatility
    forecast = garch.forecast(horizon=30)
    print("\nVolatility Forecast:")
    print(forecast)

    # Calculate VaR from forecast
    var = garch.calculate_var(forecast['Volatility'], confidence_level=0.95)
    print("\n95% VaR Forecast:")
    print(var)

    # Find best model
    selector = GARCHModelSelector()
    best_model, params = selector.find_best_model(returns, max_p=2, max_q=2)
    print(f"\nBest Model: GARCH({params['p']},{params['q']}) with {params['dist']}")
