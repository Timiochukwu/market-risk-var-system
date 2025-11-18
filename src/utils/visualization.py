"""
Visualization Module for Market Risk VaR System
Plotting functions for analysis and reporting
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VaRVisualizer:
    """Create visualizations for VaR analysis"""

    def __init__(self, template: str = 'plotly_white'):
        """
        Initialize visualizer

        Args:
            template: Plotly template to use
        """
        self.template = template

    def plot_price_and_returns(
        self,
        data: pd.DataFrame,
        ticker: str = "Asset"
    ) -> go.Figure:
        """
        Plot price and returns time series

        Args:
            data: DataFrame with 'Price' and 'Returns' columns
            ticker: Asset ticker name

        Returns:
            Plotly figure
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(f'{ticker} Price', f'{ticker} Returns'),
            vertical_spacing=0.1
        )

        # Price plot
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Price'],
                name='Price',
                line=dict(color='blue')
            ),
            row=1, col=1
        )

        # Returns plot
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Returns'],
                name='Returns',
                line=dict(color='green')
            ),
            row=2, col=1
        )

        # Add zero line for returns
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Returns", row=2, col=1)

        fig.update_layout(
            height=600,
            template=self.template,
            showlegend=False,
            title_text=f"{ticker} - Price and Returns Analysis"
        )

        return fig

    def plot_returns_distribution(
        self,
        returns: pd.Series,
        var_estimates: Optional[dict] = None,
        bins: int = 50
    ) -> go.Figure:
        """
        Plot returns distribution with VaR estimates

        Args:
            returns: Returns series
            var_estimates: Dictionary with VaR estimates
            bins: Number of histogram bins

        Returns:
            Plotly figure
        """
        fig = go.Figure()

        # Histogram
        fig.add_trace(
            go.Histogram(
                x=returns,
                nbinsx=bins,
                name='Returns',
                histnorm='probability density',
                opacity=0.7
            )
        )

        # Fitted normal distribution
        mu = returns.mean()
        sigma = returns.std()
        x = np.linspace(returns.min(), returns.max(), 100)
        normal_dist = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

        fig.add_trace(
            go.Scatter(
                x=x,
                y=normal_dist,
                name='Normal Distribution',
                line=dict(color='red', dash='dash')
            )
        )

        # Add VaR lines if provided
        if var_estimates:
            colors = ['orange', 'red', 'darkred']
            for i, (method, var_pct) in enumerate(var_estimates.items()):
                fig.add_vline(
                    x=-var_pct / 100,
                    line_dash="dash",
                    line_color=colors[i % len(colors)],
                    annotation_text=f"{method}: {var_pct:.2f}%",
                    annotation_position="top"
                )

        fig.update_layout(
            title="Returns Distribution with VaR Estimates",
            xaxis_title="Returns",
            yaxis_title="Density",
            template=self.template,
            height=500
        )

        return fig

    def plot_var_comparison(
        self,
        var_results: pd.DataFrame
    ) -> go.Figure:
        """
        Compare VaR estimates from different methods

        Args:
            var_results: DataFrame with VaR results

        Returns:
            Plotly figure
        """
        fig = go.Figure()

        methods = var_results['Method'].values
        var_values = var_results['VaR'].values

        fig.add_trace(
            go.Bar(
                x=methods,
                y=var_values,
                text=[f'${v:,.0f}' for v in var_values],
                textposition='outside',
                marker_color='indianred'
            )
        )

        fig.update_layout(
            title="VaR Comparison Across Methods",
            xaxis_title="Method",
            yaxis_title="VaR (USD)",
            template=self.template,
            height=500
        )

        return fig

    def plot_garch_volatility(
        self,
        conditional_volatility: pd.Series,
        returns: Optional[pd.Series] = None
    ) -> go.Figure:
        """
        Plot GARCH conditional volatility

        Args:
            conditional_volatility: Conditional volatility series
            returns: Optional returns series

        Returns:
            Plotly figure
        """
        if returns is not None:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Returns', 'Conditional Volatility'),
                vertical_spacing=0.1
            )

            # Returns
            fig.add_trace(
                go.Scatter(
                    x=returns.index,
                    y=returns,
                    name='Returns',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )

            # Volatility
            fig.add_trace(
                go.Scatter(
                    x=conditional_volatility.index,
                    y=conditional_volatility,
                    name='Volatility',
                    line=dict(color='red')
                ),
                row=2, col=1
            )

            fig.update_xaxes(title_text="Date", row=2, col=1)
            fig.update_yaxes(title_text="Returns", row=1, col=1)
            fig.update_yaxes(title_text="Volatility (%)", row=2, col=1)

            fig.update_layout(
                height=600,
                template=self.template,
                title_text="GARCH Conditional Volatility"
            )

        else:
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=conditional_volatility.index,
                    y=conditional_volatility,
                    name='Volatility',
                    line=dict(color='red')
                )
            )

            fig.update_layout(
                title="GARCH Conditional Volatility",
                xaxis_title="Date",
                yaxis_title="Volatility (%)",
                template=self.template,
                height=400
            )

        return fig

    def plot_volatility_forecast(
        self,
        forecast: pd.DataFrame,
        historical_vol: Optional[pd.Series] = None
    ) -> go.Figure:
        """
        Plot volatility forecast

        Args:
            forecast: DataFrame with volatility forecast
            historical_vol: Optional historical volatility

        Returns:
            Plotly figure
        """
        fig = go.Figure()

        if historical_vol is not None:
            # Plot historical volatility
            fig.add_trace(
                go.Scatter(
                    x=historical_vol.index,
                    y=historical_vol,
                    name='Historical',
                    line=dict(color='blue')
                )
            )

        # Plot forecast
        forecast_index = pd.date_range(
            start=historical_vol.index[-1] if historical_vol is not None else 0,
            periods=len(forecast) + 1,
            freq='D'
        )[1:]

        fig.add_trace(
            go.Scatter(
                x=forecast_index,
                y=forecast['Volatility'],
                name='Forecast',
                line=dict(color='red', dash='dash'),
                mode='lines+markers'
            )
        )

        fig.update_layout(
            title="Volatility Forecast",
            xaxis_title="Date" if historical_vol is not None else "Horizon",
            yaxis_title="Volatility (%)",
            template=self.template,
            height=400
        )

        return fig

    def plot_backtest_exceptions(
        self,
        exception_results: pd.DataFrame
    ) -> go.Figure:
        """
        Plot backtest exceptions

        Args:
            exception_results: DataFrame with backtest results

        Returns:
            Plotly figure
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Actual Loss vs VaR', 'Cumulative Exceptions'),
            vertical_spacing=0.12
        )

        # Actual loss vs VaR
        fig.add_trace(
            go.Scatter(
                x=exception_results.index,
                y=exception_results['Actual_Loss'],
                name='Actual Loss',
                line=dict(color='blue'),
                opacity=0.6
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=exception_results.index,
                y=exception_results['VaR_Estimate'],
                name='VaR Estimate',
                line=dict(color='red', dash='dash')
            ),
            row=1, col=1
        )

        # Highlight exceptions
        exceptions_data = exception_results[exception_results['Exception']]
        fig.add_trace(
            go.Scatter(
                x=exceptions_data.index,
                y=exceptions_data['Actual_Loss'],
                mode='markers',
                name='Exceptions',
                marker=dict(color='red', size=8, symbol='x')
            ),
            row=1, col=1
        )

        # Cumulative exceptions
        cumulative_exceptions = exception_results['Exception'].cumsum()
        fig.add_trace(
            go.Scatter(
                x=exception_results.index,
                y=cumulative_exceptions,
                name='Cumulative',
                line=dict(color='green'),
                fill='tozeroy'
            ),
            row=2, col=1
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Loss (USD)", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)

        fig.update_layout(
            height=700,
            template=self.template,
            title_text="VaR Backtest - Exception Analysis"
        )

        return fig

    def plot_rolling_var(
        self,
        returns: pd.Series,
        rolling_var: pd.Series
    ) -> go.Figure:
        """
        Plot rolling VaR

        Args:
            returns: Returns series
            rolling_var: Rolling VaR estimates

        Returns:
            Plotly figure
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Returns', 'Rolling VaR'),
            vertical_spacing=0.1
        )

        # Returns
        fig.add_trace(
            go.Scatter(
                x=returns.index,
                y=returns * 1000000,  # Assuming $1M position
                name='Returns',
                line=dict(color='blue')
            ),
            row=1, col=1
        )

        # Rolling VaR
        fig.add_trace(
            go.Scatter(
                x=rolling_var.index,
                y=rolling_var,
                name='Rolling VaR',
                line=dict(color='red')
            ),
            row=2, col=1
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Returns (USD)", row=1, col=1)
        fig.update_yaxes(title_text="VaR (USD)", row=2, col=1)

        fig.update_layout(
            height=600,
            template=self.template,
            title_text="Rolling VaR Analysis"
        )

        return fig

    def plot_qq(
        self,
        returns: pd.Series
    ) -> go.Figure:
        """
        Q-Q plot for normality testing

        Args:
            returns: Returns series

        Returns:
            Plotly figure
        """
        from scipy import stats

        # Calculate theoretical and sample quantiles
        returns_clean = returns.dropna()
        osm, osr = stats.probplot(returns_clean, dist="norm")

        fig = go.Figure()

        # Q-Q plot
        fig.add_trace(
            go.Scatter(
                x=osm[0],
                y=osm[1],
                mode='markers',
                name='Sample',
                marker=dict(color='blue')
            )
        )

        # 45-degree line
        fig.add_trace(
            go.Scatter(
                x=osm[0],
                y=osm[0],
                mode='lines',
                name='Theoretical',
                line=dict(color='red', dash='dash')
            )
        )

        fig.update_layout(
            title="Q-Q Plot - Normality Test",
            xaxis_title="Theoretical Quantiles",
            yaxis_title="Sample Quantiles",
            template=self.template,
            height=500
        )

        return fig

    def plot_monte_carlo_simulation(
        self,
        simulated_returns: np.ndarray,
        var_percentile: float,
        bins: int = 50
    ) -> go.Figure:
        """
        Plot Monte Carlo simulation results

        Args:
            simulated_returns: Array of simulated returns
            var_percentile: VaR percentile value
            bins: Number of histogram bins

        Returns:
            Plotly figure
        """
        fig = go.Figure()

        # Histogram of simulated returns
        fig.add_trace(
            go.Histogram(
                x=simulated_returns,
                nbinsx=bins,
                name='Simulated Returns',
                histnorm='probability density',
                opacity=0.7
            )
        )

        # VaR line
        fig.add_vline(
            x=var_percentile,
            line_dash="dash",
            line_color="red",
            annotation_text=f"VaR: {var_percentile:.4f}",
            annotation_position="top right"
        )

        fig.update_layout(
            title="Monte Carlo Simulation - Returns Distribution",
            xaxis_title="Simulated Returns",
            yaxis_title="Density",
            template=self.template,
            height=500
        )

        return fig

    def create_var_dashboard(
        self,
        data: pd.DataFrame,
        var_results: pd.DataFrame,
        garch_vol: pd.Series,
        backtest_results: pd.DataFrame,
        ticker: str = "Asset"
    ) -> go.Figure:
        """
        Create comprehensive VaR dashboard

        Args:
            data: DataFrame with price and returns
            var_results: VaR comparison results
            garch_vol: GARCH conditional volatility
            backtest_results: Backtest exception results
            ticker: Asset ticker

        Returns:
            Plotly figure with subplots
        """
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                f'{ticker} Price',
                'VaR Comparison',
                f'{ticker} Returns',
                'Conditional Volatility',
                'Actual Loss vs VaR',
                'Returns Distribution'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "scatter"}],
                [{"type": "scatter"}, {"type": "histogram"}]
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )

        # 1. Price
        fig.add_trace(
            go.Scatter(x=data.index, y=data['Price'], name='Price', line=dict(color='blue')),
            row=1, col=1
        )

        # 2. VaR Comparison
        fig.add_trace(
            go.Bar(x=var_results['Method'], y=var_results['VaR'], name='VaR', marker_color='indianred'),
            row=1, col=2
        )

        # 3. Returns
        fig.add_trace(
            go.Scatter(x=data.index, y=data['Returns'], name='Returns', line=dict(color='green')),
            row=2, col=1
        )

        # 4. Volatility
        fig.add_trace(
            go.Scatter(x=garch_vol.index, y=garch_vol, name='Volatility', line=dict(color='red')),
            row=2, col=2
        )

        # 5. Backtest
        fig.add_trace(
            go.Scatter(x=backtest_results.index, y=backtest_results['Actual_Loss'],
                      name='Actual', line=dict(color='blue')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=backtest_results.index, y=backtest_results['VaR_Estimate'],
                      name='VaR', line=dict(color='red', dash='dash')),
            row=3, col=1
        )

        # 6. Distribution
        fig.add_trace(
            go.Histogram(x=data['Returns'].dropna(), nbinsx=50, name='Distribution'),
            row=3, col=2
        )

        fig.update_layout(
            height=1000,
            template=self.template,
            title_text=f"{ticker} - Comprehensive VaR Dashboard",
            showlegend=False
        )

        return fig


if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append('..')
    from data.data_collector import DataCollector
    from data.preprocessor import DataPreprocessor
    from models.var_calculator import VaRCalculator
    from models.garch_model import GARCHForecaster

    # Collect data
    collector = DataCollector()
    data = collector.fetch_stock_data("AAPL", period="1y")

    # Preprocess
    preprocessor = DataPreprocessor()
    returns_data = preprocessor.prepare_returns_data(data)

    # Calculate VaR
    var_calc = VaRCalculator(confidence_level=0.95)
    returns = returns_data['Returns'].dropna()
    var_results = var_calc.calculate_all_methods(returns, position_value=1000000)

    # Fit GARCH
    garch = GARCHForecaster()
    garch.fit(returns)
    garch_vol = garch.conditional_volatility()

    # Visualize
    viz = VaRVisualizer()

    # Plot price and returns
    fig1 = viz.plot_price_and_returns(returns_data, ticker="AAPL")
    fig1.show()

    # Plot VaR comparison
    fig2 = viz.plot_var_comparison(var_results)
    fig2.show()

    # Plot GARCH volatility
    fig3 = viz.plot_garch_volatility(garch_vol, returns)
    fig3.show()

    logger.info("Visualizations created successfully")
