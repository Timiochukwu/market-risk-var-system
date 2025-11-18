"""
Streamlit Dashboard for Market Risk VaR System
Interactive web interface for VaR analysis and monitoring
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator
from src.models.garch_model import GARCHForecaster, GARCHModelSelector
from src.models.arima_model import ARIMAForecaster
from src.utils.backtesting import VaRBacktester
from src.utils.visualization import VaRVisualizer

# Page configuration
st.set_page_config(
    page_title="Market Risk VaR Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'returns_data' not in st.session_state:
    st.session_state.returns_data = None
if 'ticker' not in st.session_state:
    st.session_state.ticker = "AAPL"

# Initialize components
@st.cache_resource
def get_components():
    collector = DataCollector()
    preprocessor = DataPreprocessor()
    visualizer = VaRVisualizer()
    return collector, preprocessor, visualizer

collector, preprocessor, visualizer = get_components()

# Title
st.markdown('<div class="main-header">📈 Market Risk VaR Dashboard</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Configuration")

# Ticker selection
ticker = st.sidebar.text_input("Stock Ticker", value=st.session_state.ticker).upper()
st.session_state.ticker = ticker

# Date range
period_options = {
    "6 Months": "6mo",
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y"
}
period_label = st.sidebar.selectbox("Time Period", list(period_options.keys()), index=2)
period = period_options[period_label]

# VaR parameters
st.sidebar.subheader("VaR Parameters")
confidence_level = st.sidebar.slider("Confidence Level", 0.90, 0.99, 0.95, 0.01)
position_value = st.sidebar.number_input("Position Value ($)", value=1000000, step=100000)

# Load data button
if st.sidebar.button("📥 Load Data", type="primary"):
    with st.spinner(f"Fetching data for {ticker}..."):
        try:
            data = collector.fetch_stock_data(ticker, period=period)
            if not data.empty:
                st.session_state.returns_data = preprocessor.prepare_returns_data(data)
                st.session_state.data_loaded = True
                st.sidebar.success(f"✅ Data loaded: {len(data)} records")
            else:
                st.sidebar.error("❌ No data found")
                st.session_state.data_loaded = False
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
            st.session_state.data_loaded = False

# Main content
if st.session_state.data_loaded and st.session_state.returns_data is not None:
    returns_data = st.session_state.returns_data
    returns = returns_data['Returns'].dropna()

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "💰 VaR Analysis",
        "📉 GARCH Model",
        "📈 ARIMA Model",
        "✅ Backtesting"
    ])

    # TAB 1: Overview
    with tab1:
        st.header(f"{ticker} - Market Overview")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        latest_price = returns_data['Price'].iloc[-1]
        price_change = returns_data['Price'].iloc[-1] - returns_data['Price'].iloc[-2]
        price_change_pct = (price_change / returns_data['Price'].iloc[-2]) * 100

        col1.metric("Latest Price", f"${latest_price:.2f}", f"{price_change_pct:+.2f}%")
        col2.metric("Mean Return", f"{returns.mean()*100:.4f}%")
        col3.metric("Volatility (Std)", f"{returns.std()*100:.4f}%")
        col4.metric("Data Points", len(returns_data))

        # Price and Returns plot
        st.subheader("Price and Returns")
        fig1 = visualizer.plot_price_and_returns(returns_data, ticker=ticker)
        st.plotly_chart(fig1, use_container_width=True)

        # Summary statistics
        st.subheader("Summary Statistics")
        summary_stats = preprocessor.get_summary_statistics(returns)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Distribution Statistics**")
            stats_df = pd.DataFrame({
                'Metric': ['Count', 'Mean', 'Std Dev', 'Skewness', 'Kurtosis'],
                'Value': [
                    f"{summary_stats['count']}",
                    f"{summary_stats['mean']:.6f}",
                    f"{summary_stats['std']:.6f}",
                    f"{summary_stats['skewness']:.4f}",
                    f"{summary_stats['kurtosis']:.4f}"
                ]
            })
            st.dataframe(stats_df, hide_index=True)

        with col2:
            st.write("**Risk Metrics**")
            risk_df = pd.DataFrame({
                'Metric': ['Min', 'Max', 'Q25', 'Median', 'Q75'],
                'Value': [
                    f"{summary_stats['min']:.6f}",
                    f"{summary_stats['max']:.6f}",
                    f"{summary_stats['q25']:.6f}",
                    f"{summary_stats['median']:.6f}",
                    f"{summary_stats['q75']:.6f}"
                ]
            })
            st.dataframe(risk_df, hide_index=True)

        # Returns distribution
        st.subheader("Returns Distribution")
        fig_dist = visualizer.plot_returns_distribution(returns)
        st.plotly_chart(fig_dist, use_container_width=True)

        # Q-Q plot
        st.subheader("Normality Test (Q-Q Plot)")
        fig_qq = visualizer.plot_qq(returns)
        st.plotly_chart(fig_qq, use_container_width=True)

    # TAB 2: VaR Analysis
    with tab2:
        st.header("💰 Value at Risk Analysis")

        # Calculate VaR using all methods
        with st.spinner("Calculating VaR..."):
            var_calc = VaRCalculator(confidence_level=confidence_level)

            # Fit GARCH for GARCH-based VaR
            garch = GARCHForecaster(p=1, q=1)
            garch.fit(returns)
            garch_forecast = garch.forecast(horizon=1)

            # Calculate all methods
            var_results = var_calc.calculate_all_methods(
                returns,
                position_value=position_value,
                garch_forecast=garch_forecast['Volatility']
            )

        # Display results
        st.subheader("VaR Estimates Comparison")

        # Format results
        display_results = var_results.copy()
        display_results['VaR'] = display_results['VaR'].apply(lambda x: f"${x:,.2f}")
        if 'ES' in display_results.columns:
            display_results['ES'] = display_results['ES'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
        if 'VaR_Percentage' in display_results.columns:
            display_results['VaR_Percentage'] = display_results['VaR_Percentage'].apply(lambda x: f"{x:.4f}%")

        st.dataframe(display_results, hide_index=True, use_container_width=True)

        # VaR comparison chart
        st.subheader("VaR Comparison Chart")
        fig_var_comp = visualizer.plot_var_comparison(var_results)
        st.plotly_chart(fig_var_comp, use_container_width=True)

        # VaR at different confidence levels
        st.subheader("VaR at Different Confidence Levels")

        col1, col2 = st.columns(2)

        with col1:
            method_for_comparison = st.selectbox(
                "Select Method",
                ["historical", "parametric", "monte_carlo"]
            )

        with col2:
            st.write("")  # Spacer

        confidence_comparison = var_calc.compare_confidence_levels(
            returns,
            position_value=position_value,
            confidence_levels=[0.90, 0.95, 0.99],
            method=method_for_comparison
        )

        # Format for display
        display_comparison = confidence_comparison.copy()
        display_comparison['VaR'] = display_comparison['VaR'].apply(lambda x: f"${x:,.2f}")
        display_comparison['ES'] = display_comparison['ES'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A")
        display_comparison['VaR_Percentage'] = display_comparison['VaR_Percentage'].apply(lambda x: f"{x:.4f}%")

        st.dataframe(display_comparison, hide_index=True, use_container_width=True)

        # Distribution with VaR
        st.subheader("Returns Distribution with VaR Estimates")
        var_estimates_dict = {
            row['Method']: row['VaR_Percentage']
            for _, row in var_results.iterrows()
            if pd.notna(row.get('VaR_Percentage'))
        }
        fig_dist_var = visualizer.plot_returns_distribution(returns, var_estimates=var_estimates_dict)
        st.plotly_chart(fig_dist_var, use_container_width=True)

    # TAB 3: GARCH Model
    with tab3:
        st.header("📉 GARCH Volatility Forecasting")

        col1, col2 = st.columns(2)

        with col1:
            garch_p = st.number_input("GARCH p (lag order)", 1, 5, 1)
            garch_q = st.number_input("ARCH q (lag order)", 1, 5, 1)

        with col2:
            garch_dist = st.selectbox("Distribution", ["normal", "t"])
            forecast_horizon = st.number_input("Forecast Horizon", 1, 100, 30)

        if st.button("🔧 Fit GARCH Model"):
            with st.spinner("Fitting GARCH model..."):
                try:
                    # Fit GARCH
                    garch_model = GARCHForecaster(p=garch_p, q=garch_q, dist=garch_dist)
                    garch_model.fit(returns)

                    # Display model summary
                    st.subheader("Model Summary")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("AIC", f"{garch_model.results['aic']:.2f}")
                    col2.metric("BIC", f"{garch_model.results['bic']:.2f}")
                    col3.metric("Log-Likelihood", f"{garch_model.results['loglikelihood']:.2f}")

                    # Conditional volatility
                    st.subheader("Conditional Volatility")
                    cond_vol = garch_model.conditional_volatility()
                    fig_vol = visualizer.plot_garch_volatility(cond_vol, returns)
                    st.plotly_chart(fig_vol, use_container_width=True)

                    # Forecast
                    st.subheader("Volatility Forecast")
                    forecast = garch_model.forecast(horizon=forecast_horizon)

                    fig_forecast = visualizer.plot_volatility_forecast(forecast, cond_vol)
                    st.plotly_chart(fig_forecast, use_container_width=True)

                    # Display forecast data
                    st.write("**Forecast Data (First 10 periods)**")
                    st.dataframe(forecast.head(10))

                    # Calculate VaR from forecast
                    st.subheader("VaR from GARCH Forecast")
                    var_from_garch = garch_model.calculate_var(
                        forecast['Volatility'],
                        confidence_level=confidence_level,
                        position_value=position_value
                    )

                    st.write(f"**1-Day VaR ({confidence_level*100}%):** ${var_from_garch.iloc[0]:,.2f}")
                    st.write(f"**10-Day VaR ({confidence_level*100}%):** ${var_from_garch.iloc[9]:,.2f}" if len(var_from_garch) >= 10 else "")

                except Exception as e:
                    st.error(f"Error fitting GARCH model: {str(e)}")

        # Model selection
        st.subheader("Automatic Model Selection")
        if st.button("🔍 Find Best GARCH Model"):
            with st.spinner("Searching for best model..."):
                try:
                    selector = GARCHModelSelector()
                    best_model, best_params = selector.find_best_model(
                        returns,
                        max_p=3,
                        max_q=3,
                        distributions=['normal', 't']
                    )

                    st.success(f"Best Model: GARCH({best_params['p']},{best_params['q']}) with {best_params['dist']} distribution")
                    st.write(f"**AIC:** {best_params['aic']:.2f}")

                    # Display results summary
                    results_summary = selector.get_results_summary()
                    st.write("**Model Comparison (Top 10)**")
                    st.dataframe(results_summary.head(10), hide_index=True)

                except Exception as e:
                    st.error(f"Error in model selection: {str(e)}")

    # TAB 4: ARIMA Model
    with tab4:
        st.header("📈 ARIMA Price Forecasting")

        col1, col2, col3 = st.columns(3)

        with col1:
            arima_p = st.number_input("AR order (p)", 0, 5, 1)
        with col2:
            arima_d = st.number_input("Differencing (d)", 0, 2, 0)
        with col3:
            arima_q = st.number_input("MA order (q)", 0, 5, 1)

        forecast_steps = st.number_input("Forecast Steps", 1, 100, 30)
        optimize_order = st.checkbox("Auto-optimize order", value=False)

        if st.button("🔧 Fit ARIMA Model"):
            with st.spinner("Fitting ARIMA model..."):
                try:
                    # Fit ARIMA
                    arima = ARIMAForecaster(order=(arima_p, arima_d, arima_q))

                    # Check stationarity
                    st.subheader("Stationarity Test")
                    stationarity = arima.check_stationarity(returns)

                    col1, col2 = st.columns(2)
                    col1.metric("ADF Statistic", f"{stationarity['adf_statistic']:.4f}")
                    col2.metric("P-value", f"{stationarity['p_value']:.4f}")

                    if stationarity['is_stationary']:
                        st.success("✅ Series is stationary")
                    else:
                        st.warning("⚠️ Series is not stationary. Consider differencing (d > 0)")

                    # Fit model
                    arima.fit(returns, optimize=optimize_order)

                    # Model summary
                    st.subheader("Model Summary")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("AIC", f"{arima.results['aic']:.2f}")
                    col2.metric("BIC", f"{arima.results['bic']:.2f}")
                    col3.metric("Order", str(arima.order))

                    # Forecast
                    st.subheader("Returns Forecast")
                    forecast = arima.forecast(steps=forecast_steps)

                    # Plot forecast
                    import plotly.graph_objects as go
                    fig = go.Figure()

                    # Historical
                    fig.add_trace(go.Scatter(
                        x=returns.index[-100:],
                        y=returns.values[-100:],
                        name='Historical',
                        line=dict(color='blue')
                    ))

                    # Forecast
                    future_dates = pd.date_range(
                        start=returns.index[-1],
                        periods=forecast_steps + 1,
                        freq='D'
                    )[1:]

                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=forecast['Forecast'],
                        name='Forecast',
                        line=dict(color='red', dash='dash')
                    ))

                    # Confidence intervals
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=forecast['Upper_CI'],
                        name='Upper CI',
                        line=dict(color='gray', dash='dot'),
                        showlegend=False
                    ))

                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=forecast['Lower_CI'],
                        name='Lower CI',
                        line=dict(color='gray', dash='dot'),
                        fill='tonexty',
                        fillcolor='rgba(128,128,128,0.2)',
                        showlegend=False
                    ))

                    fig.update_layout(
                        title="ARIMA Forecast",
                        xaxis_title="Date",
                        yaxis_title="Returns",
                        template="plotly_white"
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Display forecast data
                    st.write("**Forecast Data (First 10 periods)**")
                    st.dataframe(forecast.head(10))

                    # Model diagnostics
                    st.subheader("Residual Diagnostics")
                    residuals = arima.calculate_residuals()
                    diagnostics = arima.diagnose_residuals()

                    st.dataframe(diagnostics)

                except Exception as e:
                    st.error(f"Error fitting ARIMA model: {str(e)}")

    # TAB 5: Backtesting
    with tab5:
        st.header("✅ VaR Model Backtesting")

        col1, col2 = st.columns(2)

        with col1:
            backtest_method = st.selectbox(
                "VaR Method",
                ["Historical", "Parametric"],
                key="backtest_method"
            )

        with col2:
            train_ratio = st.slider("Training Data Ratio", 0.5, 0.9, 0.7, 0.05)

        if st.button("🧪 Run Backtest"):
            with st.spinner("Running backtest..."):
                try:
                    # Split data
                    train_size = int(len(returns) * train_ratio)
                    train_returns = returns.iloc[:train_size]
                    test_returns = returns.iloc[train_size:]

                    # Calculate VaR
                    var_calc = VaRCalculator(confidence_level=confidence_level)

                    if backtest_method == "Historical":
                        var_result = var_calc.historical_var(train_returns, position_value)
                    else:
                        var_result = var_calc.parametric_var(train_returns, position_value)

                    # Create constant VaR estimates
                    var_estimates = pd.Series(var_result['VaR'], index=test_returns.index)

                    # Backtest
                    backtester = VaRBacktester(confidence_level=confidence_level)
                    backtest_results = backtester.backtest_var_model(
                        test_returns,
                        var_estimates,
                        position_value
                    )

                    # Display results
                    st.subheader("Backtest Summary")

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Observations", backtest_results['num_observations'])
                    col2.metric("Exceptions", backtest_results['num_exceptions'])
                    col3.metric("Exception Rate", f"{backtest_results['exception_rate']:.2%}")
                    col4.metric("Expected Rate", f"{backtest_results['expected_rate']:.2%}")

                    # Statistical tests
                    st.subheader("Statistical Tests")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Kupiec Test**")
                        kupiec = backtest_results['kupiec_test']
                        st.write(f"LR Statistic: {kupiec['LR_Statistic']:.4f}")
                        st.write(f"P-value: {kupiec['P_Value']:.4f}")
                        if kupiec['Reject_Null']:
                            st.error("❌ Model REJECTED")
                        else:
                            st.success("✅ Model ACCEPTED")

                    with col2:
                        st.write("**Christoffersen Test**")
                        christ = backtest_results['christoffersen_test']
                        st.write(f"LR Statistic: {christ['LR_Statistic']:.4f}")
                        st.write(f"P-value: {christ['P_Value']:.4f}")
                        if christ['Reject_Null']:
                            st.error("❌ Model REJECTED")
                        else:
                            st.success("✅ Model ACCEPTED")

                    # Traffic light test
                    st.subheader("Basel Traffic Light Test")
                    traffic = backtest_results['traffic_light_test']

                    if traffic['Zone'] == 'Green':
                        st.success(f"🟢 {traffic['Zone']} Zone - {traffic['Status']}")
                    elif traffic['Zone'] == 'Yellow':
                        st.warning(f"🟡 {traffic['Zone']} Zone - {traffic['Status']}")
                    else:
                        st.error(f"🔴 {traffic['Zone']} Zone - {traffic['Status']}")

                    # Exception plot
                    st.subheader("Exception Analysis")
                    exception_details = backtest_results['exception_details']
                    fig_exceptions = visualizer.plot_backtest_exceptions(exception_details)
                    st.plotly_chart(fig_exceptions, use_container_width=True)

                except Exception as e:
                    st.error(f"Error in backtesting: {str(e)}")

else:
    # Welcome screen
    st.info("👈 Please configure parameters in the sidebar and click 'Load Data' to begin analysis")

    st.markdown("""
    ## Features

    This dashboard provides comprehensive market risk analysis tools:

    ### 📊 Overview
    - Price and returns visualization
    - Summary statistics
    - Distribution analysis
    - Normality testing

    ### 💰 VaR Analysis
    - Historical VaR
    - Parametric VaR (Normal & Student's t)
    - Monte Carlo VaR (Bootstrap & Parametric)
    - GARCH-based VaR
    - Multi-confidence level comparison

    ### 📉 GARCH Model
    - Volatility forecasting
    - Conditional volatility analysis
    - Automatic model selection
    - VaR calculation from volatility forecast

    ### 📈 ARIMA Model
    - Returns forecasting
    - Stationarity testing
    - Automatic order optimization
    - Forecast confidence intervals

    ### ✅ Backtesting
    - Kupiec POF test
    - Christoffersen independence test
    - Basel Traffic Light test
    - Exception analysis

    ---
    **Get started by entering a ticker symbol and clicking 'Load Data'!**
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Market Risk VaR System v1.0**")
st.sidebar.markdown("Built with Streamlit, ARIMA, and GARCH")
