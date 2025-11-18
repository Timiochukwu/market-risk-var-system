# Market Risk VaR System (ARIMA/GARCH)

A comprehensive Value at Risk (VaR) calculation and analysis system using time series models (ARIMA and GARCH). This system provides multiple VaR calculation methods, volatility forecasting, backtesting, and interactive dashboards for market risk management.

## 🌟 Features

### Core Functionality
- **Multiple VaR Methods**: Historical, Parametric, Monte Carlo, and GARCH-based VaR
- **ARIMA Models**: Price and returns forecasting with automatic order optimization
- **GARCH Models**: Volatility forecasting with multiple distributions (Normal, Student's t)
- **Comprehensive Backtesting**: Kupiec POF, Christoffersen independence, and Basel Traffic Light tests
- **Interactive Dashboard**: Streamlit-based web interface for real-time analysis
- **REST API**: FastAPI backend for programmatic access
- **Visualization**: Professional charts and graphs using Plotly

### Supported VaR Methods
1. **Historical VaR**: Non-parametric method based on historical data
2. **Parametric VaR**: Variance-covariance method with Normal or Student's t distribution
3. **Monte Carlo VaR**: Simulation-based approach with bootstrap or parametric methods
4. **GARCH VaR**: Volatility-adjusted VaR using GARCH forecasts

### 🚀 Advanced Features (NEW!)
- **Advanced Risk Metrics**: CVaR/Expected Shortfall, Maximum Drawdown, Sharpe/Sortino/Calmar Ratios, VaR Decomposition
- **Stress Testing**: Market crash scenarios, volatility spikes, correlation breakdown, historical crisis replays, reverse stress testing
- **Report Generation**: Professional Excel, HTML, and text reports for management and regulatory compliance
- **Portfolio Analytics**: Multi-asset VaR, diversification benefit analysis, correlation matrices

### 🤖 Machine Learning & Integration (NEW!)
- **ML VaR Models**: LSTM and GRU deep learning models for superior predictions, Ensemble methods, Anomaly detection
- **Database Integration**: Full SQLAlchemy ORM with 5 tables for historical tracking, audit trails, and regulatory compliance
- **Email Alerts**: Automated notifications for VaR breaches, anomalies, backtest failures with HTML formatting
- **Task Scheduler**: Automated daily calculations, weekly retraining, real-time monitoring, EOD reports

📖 **See [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) and [ML_AND_INTEGRATION_GUIDE.md](ML_AND_INTEGRATION_GUIDE.md) for detailed documentation with examples!**

## 📁 Project Structure

```
market-risk-var/
├── data/
│   ├── raw/                    # Downloaded market data
│   └── processed/              # Processed returns
├── src/
│   ├── data/
│   │   ├── data_collector.py   # Fetch stock/FX data
│   │   └── preprocessor.py     # Calculate returns, clean data
│   ├── models/
│   │   ├── garch_model.py      # GARCH volatility forecasting
│   │   ├── arima_model.py      # ARIMA price forecasting
│   │   ├── var_calculator.py   # VaR calculation methods
│   │   └── ml_var_models.py    # ML VaR (LSTM/GRU/Ensemble) (NEW)
│   ├── api/
│   │   ├── schemas.py          # API data models
│   │   └── main.py             # FastAPI application
│   └── utils/
│       ├── backtesting.py      # VaR backtesting
│       ├── visualization.py    # Plotting functions
│       ├── advanced_metrics.py # Advanced risk metrics (NEW)
│       ├── stress_testing.py   # Stress testing (NEW)
│       ├── report_generator.py # Report generation (NEW)
│       ├── database.py         # Database integration (NEW)
│       ├── email_alerts.py     # Email alerting system (NEW)
│       └── scheduler.py        # Task scheduler (NEW)
├── dashboard/
│   └── streamlit_app.py        # Monitoring dashboard
├── models/                      # Saved models
├── reports/                     # Generated reports
└── requirements.txt
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. **Clone or navigate to the project directory**:
```bash
cd market-risk-var
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## 💻 Usage

### 1. Command Line Interface

#### Fetch and Analyze Data
```python
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator

# Collect data
collector = DataCollector()
data = collector.fetch_stock_data("AAPL", period="2y")

# Preprocess
preprocessor = DataPreprocessor()
returns_data = preprocessor.prepare_returns_data(data)
returns = returns_data['Returns'].dropna()

# Calculate VaR
var_calc = VaRCalculator(confidence_level=0.95)
var_results = var_calc.calculate_all_methods(
    returns,
    position_value=1000000
)

print(var_results)
```

#### GARCH Volatility Forecasting
```python
from src.models.garch_model import GARCHForecaster

# Fit GARCH model
garch = GARCHForecaster(p=1, q=1, dist='normal')
garch.fit(returns)

# Forecast volatility
forecast = garch.forecast(horizon=30)
print(forecast)

# Calculate VaR from forecast
var = garch.calculate_var(forecast['Volatility'], confidence_level=0.95)
print(f"1-Day VaR: ${var.iloc[0]:,.2f}")
```

#### ARIMA Price Forecasting
```python
from src.models.arima_model import ARIMAForecaster

# Fit ARIMA model
arima = ARIMAForecaster(order=(2, 0, 2))
arima.fit(returns, optimize=False)

# Generate forecast
forecast = arima.forecast(steps=30)
print(forecast)
```

#### Backtest VaR Model
```python
from src.utils.backtesting import VaRBacktester

# Split data
train_returns = returns.iloc[:int(len(returns)*0.7)]
test_returns = returns.iloc[int(len(returns)*0.7):]

# Calculate VaR
var_result = var_calc.historical_var(train_returns, 1000000)
var_estimates = pd.Series(var_result['VaR'], index=test_returns.index)

# Backtest
backtester = VaRBacktester(confidence_level=0.95)
results = backtester.backtest_var_model(test_returns, var_estimates, 1000000)

print(f"Exception Rate: {results['exception_rate']:.2%}")
print(f"Kupiec Test P-value: {results['kupiec_test']['P_Value']:.4f}")
print(f"Traffic Light Zone: {results['traffic_light_test']['Zone']}")
```

### 2. REST API

#### Start the API Server
```bash
cd src/api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

#### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Example API Requests

**Calculate VaR**:
```bash
curl -X POST "http://localhost:8000/api/v1/var/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.95,
    "position_value": 1000000,
    "method": "historical"
  }'
```

**Compare VaR Methods**:
```bash
curl -X POST "http://localhost:8000/api/v1/var/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.95,
    "position_value": 1000000,
    "include_garch": true
  }'
```

**GARCH Forecast**:
```bash
curl -X POST "http://localhost:8000/api/v1/garch/forecast" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "p": 1,
    "q": 1,
    "distribution": "normal",
    "forecast_horizon": 30
  }'
```

**Backtest VaR**:
```bash
curl -X POST "http://localhost:8000/api/v1/backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "confidence_level": 0.95,
    "position_value": 1000000,
    "method": "historical",
    "train_ratio": 0.7
  }'
```

### 3. Streamlit Dashboard

#### Start the Dashboard
```bash
streamlit run dashboard/streamlit_app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

#### Dashboard Features

**Overview Tab**:
- Price and returns visualization
- Summary statistics
- Distribution analysis
- Q-Q plot for normality testing

**VaR Analysis Tab**:
- Compare all VaR methods
- VaR at different confidence levels
- Distribution with VaR estimates

**GARCH Model Tab**:
- Fit GARCH models with custom parameters
- Conditional volatility visualization
- Volatility forecasting
- Automatic model selection

**ARIMA Model Tab**:
- Fit ARIMA models
- Stationarity testing
- Returns forecasting
- Confidence intervals

**Backtesting Tab**:
- Run comprehensive backtests
- Kupiec and Christoffersen tests
- Basel Traffic Light zones
- Exception analysis visualization

## 📊 Example Outputs

### VaR Comparison
```
Method                           VaR          ES      VaR_Percentage
Historical                   $16,234.56  $21,345.67      1.62%
Parametric (Normal)          $15,892.34  $20,234.45      1.59%
Parametric (Student's t)     $17,456.78  $22,567.89      1.75%
Monte Carlo (Bootstrap)      $16,123.45  $21,234.56      1.61%
Monte Carlo (Parametric)     $15,967.23  $20,456.78      1.60%
GARCH                        $16,789.12  N/A             1.68%
```

### Backtest Results
```
Observations: 150
Exceptions: 8
Exception Rate: 5.33%
Expected Rate: 5.00%

Kupiec Test:
  LR Statistic: 0.0856
  P-value: 0.7697
  Result: ACCEPTED ✓

Christoffersen Test:
  LR Statistic: 0.1234
  P-value: 0.7253
  Result: ACCEPTED ✓

Traffic Light Zone: Green (ACCEPTABLE) ✓
```

## 🧪 Testing

Run individual module tests:

```bash
# Test data collection
python src/data/data_collector.py

# Test preprocessing
python src/data/preprocessor.py

# Test ARIMA model
python src/models/arima_model.py

# Test GARCH model
python src/models/garch_model.py

# Test VaR calculator
python src/models/var_calculator.py

# Test backtesting
python src/utils/backtesting.py

# Test visualization
python src/utils/visualization.py
```

## 📈 Use Cases

### Risk Management
- Daily VaR calculation for trading portfolios
- Regulatory capital requirements (Basel III)
- Risk limit monitoring and alerting

### Portfolio Analysis
- Multi-asset portfolio VaR
- Diversification benefit analysis
- Stress testing and scenario analysis

### Model Validation
- Backtesting VaR models
- Model comparison and selection
- Regulatory compliance reporting

### Research
- Volatility forecasting studies
- Time series model comparison
- Financial econometrics research

## 🔧 Configuration

### VaR Parameters
- **Confidence Level**: 90%, 95%, 99% (typical values)
- **Position Value**: Portfolio value in USD
- **Historical Window**: 252 days (1 year), 504 days (2 years)
- **Monte Carlo Simulations**: 10,000+ recommended

### GARCH Parameters
- **p**: GARCH lag order (typically 1-2)
- **q**: ARCH lag order (typically 1-2)
- **Distribution**: Normal, Student's t, Skewed Student's t

### ARIMA Parameters
- **p**: Autoregressive order (0-5)
- **d**: Differencing order (0-2)
- **q**: Moving average order (0-5)

## 📚 Technical Details

### VaR Calculation Methods

**Historical VaR**:
- Percentile-based approach
- No distribution assumptions
- Accounts for fat tails and skewness

**Parametric VaR**:
- Assumes returns distribution (Normal or Student's t)
- Variance-covariance method
- Fast computation

**Monte Carlo VaR**:
- Simulation-based approach
- Bootstrap resampling or parametric simulation
- Handles complex portfolios

**GARCH VaR**:
- Time-varying volatility
- Accounts for volatility clustering
- More accurate during volatile periods

### Backtesting Methods

**Kupiec POF Test**:
- Tests if exception rate matches expected rate
- Likelihood ratio test
- Null hypothesis: Model is accurate

**Christoffersen Independence Test**:
- Tests if exceptions are independent (no clustering)
- Identifies systematic model failures

**Basel Traffic Light Test**:
- Green Zone: 0-4 exceptions (acceptable)
- Yellow Zone: 5-9 exceptions (warning)
- Red Zone: 10+ exceptions (unacceptable)

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional VaR methods (e.g., Cornish-Fisher VaR)
- More backtesting metrics
- Portfolio optimization integration
- Real-time data streaming
- Machine learning models

## 📄 License

This project is provided as-is for educational and research purposes.

## ⚠️ Disclaimer

This system is for educational and research purposes only. It should not be used as the sole basis for investment decisions or risk management. Always validate results and consult with qualified financial professionals.

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review the example notebooks

## 🔄 Updates

**Version 1.0.0** (Current)
- Initial release
- Core VaR calculation methods
- ARIMA and GARCH models
- Backtesting framework
- REST API
- Streamlit dashboard

---

**Built with**: Python, FastAPI, Streamlit, statsmodels, arch, yfinance, plotly

**Happy Risk Management! 📊💰**
