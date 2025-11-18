# Advanced Features Guide

## 🚀 New Advanced Features Added

This document describes the advanced risk management features added to the Market Risk VaR System. These features transform the system from a basic VaR calculator into a comprehensive enterprise-grade risk management platform.

---

## 📊 1. Advanced Risk Metrics

**File**: `src/utils/advanced_metrics.py`

### What It Does
Goes beyond basic VaR to provide a complete picture of portfolio risk using industry-standard metrics.

### Key Features

#### **Conditional VaR (CVaR / Expected Shortfall)**
- **What it is**: Average loss in the worst X% of scenarios
- **Why it matters**: VaR tells you "you won't lose more than X", but CVaR tells you "IF you lose more than X, here's how bad it gets"
- **Example**:
  - 95% VaR = $10,000
  - 95% CVaR = $15,000
  - Meaning: In the worst 5% of cases, average loss is $15,000

```python
from src.utils.advanced_metrics import AdvancedRiskMetrics

metrics = AdvancedRiskMetrics(risk_free_rate=0.02)
cvar_result = metrics.calculate_cvar(
    returns=returns,
    confidence_level=0.95,
    position_value=1000000
)

print(f"CVaR: ${cvar_result['CVaR']:,.2f}")
print(f"Tail Risk: ${cvar_result['Tail_Risk']:,.2f}")
```

#### **Maximum Drawdown (MDD)**
- **What it is**: Largest peak-to-trough decline in portfolio value
- **Why it matters**: Shows the worst loss an investor would have experienced
- **Use case**: Risk tolerance assessment, manager evaluation

```python
mdd_result = metrics.calculate_maximum_drawdown(prices)
print(f"Max Drawdown: {mdd_result['Max_Drawdown_Percentage']:.2f}%")
print(f"Recovery took: {mdd_result['Recovery_Days']} days")
```

#### **Sharpe Ratio**
- **What it is**: (Return - Risk-Free Rate) / Volatility
- **Why it matters**: Measures risk-adjusted returns
- **Interpretation**:
  - < 1.0: Poor
  - 1.0-2.0: Good
  - 2.0-3.0: Very good
  - > 3.0: Excellent

```python
sharpe = metrics.calculate_sharpe_ratio(returns)
print(f"Sharpe Ratio: {sharpe:.4f}")
```

#### **Sortino Ratio**
- **What it is**: Like Sharpe, but only considers downside volatility
- **Why it's better**: Upside volatility is good (big gains), so it's not penalized
- **Use case**: More investor-friendly than Sharpe

#### **Calmar Ratio**
- **What it is**: Annual Return / Maximum Drawdown
- **Why it matters**: Shows if returns justify the pain of drawdowns

#### **VaR Decomposition**
- **What it is**: Shows how much each asset contributes to portfolio VaR
- **Why it matters**:
  - Identify main risk drivers
  - Rebalancing decisions
  - Risk budgeting

```python
decomposition = metrics.calculate_var_decomposition(
    returns_df=portfolio_returns,
    weights=np.array([0.4, 0.3, 0.3]),
    confidence_level=0.95
)
# Shows: Stock A contributes 60% of VaR, Stock B 40%, etc.
```

---

## 🔥 2. Stress Testing & Scenario Analysis

**File**: `src/utils/stress_testing.py`

### What It Does
Answers critical "What if?" questions about extreme market scenarios.

### Why Stress Testing Matters
- **Regulatory Requirement**: Basel III, Dodd-Frank mandate stress testing
- **Risk Discovery**: Identifies vulnerabilities before they cause losses
- **Capital Planning**: Determines how much capital to hold in reserve
- **Board Communication**: Shows executives worst-case scenarios

### Scenarios Included

#### **Market Crash Scenarios**
Tests portfolio against various crash magnitudes:

```python
from src.utils.stress_testing import StressTester

tester = StressTester()

# Test -20% market crash
crash_result = tester.market_crash_scenario(
    returns=returns,
    crash_magnitude=-0.20,
    position_value=1000000
)

print(f"Portfolio Loss: ${crash_result['Portfolio_Loss']:,.2f}")
print(f"This is a {crash_result['Sigma_Event']:.1f}-sigma event")
```

**Common Crash Magnitudes**:
- Flash crash: -10% (like 2010)
- Major crash: -20% (like Black Monday 1987)
- Extreme crash: -30% (like 1929)

#### **Volatility Spike Scenarios**
Tests what happens when volatility doubles or triples:

```python
vol_result = tester.volatility_spike_scenario(
    returns=returns,
    current_position=1000000,
    vol_multiplier=2.0  # Volatility doubles
)

print(f"Current VaR: ${vol_result['Current_VaR']:,.2f}")
print(f"Stressed VaR: ${vol_result['Stressed_VaR']:,.2f}")
```

**When This Happens**:
- Market panics (VIX spikes)
- Economic crises
- Geopolitical events

#### **Correlation Breakdown**
Tests when diversification fails (all assets move together):

```python
corr_result = tester.correlation_breakdown_scenario(
    returns_df=portfolio_returns,
    weights=weights,
    correlation_target=1.0  # Perfect correlation
)

print(f"Volatility increases by {corr_result['Volatility_Increase_Percentage']:.1f}%")
```

**Reality Check**: During 2008 crisis, many asset correlations spiked to 0.9+

#### **Historical Scenarios**
Replays actual historical crises:

```python
# Predefined historical scenarios
HISTORICAL_SCENARIOS = {
    'Black Monday 1987': -0.226,
    '2008 Financial Crisis': -0.38,
    'COVID-19 Crash 2020': -0.34,
    'Dot-com Crash 2000-2002': -0.49
}

for name, return_val in HISTORICAL_SCENARIOS.items():
    result = tester.historical_scenario(
        returns=returns,
        scenario_name=name,
        scenario_return=return_val,
        position_value=1000000
    )
```

#### **Reverse Stress Testing**
Answers: "What scenario would wipe me out?"

```python
reverse_result = tester.reverse_stress_test(
    returns=returns,
    position_value=1000000,
    loss_threshold=0.50  # 50% loss
)

print(f"To lose 50%, need return of: {reverse_result['Breaking_Point_Return']:.2f}%")
print(f"This is a {reverse_result['Sigma_Event']:.1f}-sigma event")
print(f"Seen {reverse_result['Historical_Occurrences']} times in history")
```

**Regulatory Requirement**: Many regulators require reverse stress testing

#### **Comprehensive Stress Test**
Runs all scenarios at once:

```python
all_results = tester.run_comprehensive_stress_test(
    returns=returns,
    position_value=1000000
)

# Returns DataFrame with all scenario results
print(all_results[['Scenario', 'Portfolio_Loss', 'New_Portfolio_Value']])
```

---

## 📄 3. Report Generation

**File**: `src/utils/report_generator.py`

### What It Does
Creates professional risk reports in multiple formats for different audiences.

### Report Types

#### **Excel Reports** (For Analysts)
Multi-sheet workbook with all analyses:

```python
from src.utils.report_generator import RiskReportGenerator

report_gen = RiskReportGenerator(output_dir="../../reports")

excel_file = report_gen.save_excel_report(
    ticker='AAPL',
    var_results=var_results,
    garch_forecast=garch_forecast,
    arima_forecast=arima_forecast,
    backtest_results=backtest_results,
    advanced_metrics=advanced_metrics
)

print(f"Excel report saved: {excel_file}")
```

**Sheets Included**:
1. VaR Summary
2. GARCH Forecast
3. ARIMA Forecast
4. Backtest Results
5. Advanced Metrics
6. Report Info

**Use Cases**:
- Send to analysts for further analysis
- Archive for compliance
- Share with portfolio managers

#### **HTML Reports** (For Web/Email)
Professional web-ready reports:

```python
html_file = report_gen.generate_html_report(
    ticker='AAPL',
    var_results=var_results,
    position_value=1000000,
    confidence_level=0.95
)
```

**Features**:
- Professional styling
- Mobile-friendly
- Can be emailed or published to intranet
- Interactive tables

#### **Text Summary Reports** (For Email)
Concise text summaries perfect for daily risk reports:

```python
text_report = report_gen.generate_var_summary_report(
    ticker='AAPL',
    var_results=var_results,
    position_value=1000000,
    confidence_level=0.95,
    backtest_results=backtest_results
)

# Save to file
report_gen.save_report(text_report, 'daily_var_report.txt')

# Or email it
send_email(subject="Daily VaR Report", body=text_report)
```

#### **Stress Test Reports**
Specialized reports for stress testing:

```python
stress_report = report_gen.generate_stress_test_report(
    ticker='AAPL',
    stress_results=stress_results
)
```

---

## 🎯 Integration Examples

### Complete Risk Analysis Workflow

```python
from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor
from src.models.var_calculator import VaRCalculator
from src.models.garch_model import GARCHForecaster
from src.utils.advanced_metrics import AdvancedRiskMetrics
from src.utils.stress_testing import StressTester
from src.utils.report_generator import RiskReportGenerator

# 1. Collect Data
collector = DataCollector()
data = collector.fetch_stock_data("AAPL", period="2y")

# 2. Preprocess
preprocessor = DataPreprocessor()
returns_data = preprocessor.prepare_returns_data(data)
returns = returns_data['Returns'].dropna()

# 3. Calculate VaR (All Methods)
var_calc = VaRCalculator(confidence_level=0.95)
garch = GARCHForecaster(p=1, q=1)
garch.fit(returns)
garch_forecast = garch.forecast(horizon=1)

var_results = var_calc.calculate_all_methods(
    returns,
    position_value=1000000,
    garch_forecast=garch_forecast['Volatility']
)

# 4. Calculate Advanced Metrics
advanced = AdvancedRiskMetrics(risk_free_rate=0.02)
all_metrics = advanced.calculate_all_metrics(
    returns,
    returns_data['Price'],
    position_value=1000000
)

# 5. Run Stress Tests
stress_tester = StressTester()
stress_results = stress_tester.run_comprehensive_stress_test(
    returns,
    position_value=1000000
)

# 6. Generate Reports
report_gen = RiskReportGenerator()

# Excel report (for detailed analysis)
excel_file = report_gen.save_excel_report(
    ticker='AAPL',
    var_results=var_results,
    garch_forecast=garch_forecast,
    advanced_metrics=all_metrics
)

# HTML report (for web viewing)
html_file = report_gen.generate_html_report(
    ticker='AAPL',
    var_results=var_results,
    position_value=1000000,
    confidence_level=0.95
)

# Text report (for email)
text_report = report_gen.generate_var_summary_report(
    ticker='AAPL',
    var_results=var_results,
    position_value=1000000,
    confidence_level=0.95
)

print("✓ VaR Analysis Complete")
print("✓ Advanced Metrics Calculated")
print("✓ Stress Tests Run")
print("✓ Reports Generated")
```

---

## 📊 Beginner-Friendly Explanations

### Understanding Risk Metrics in Plain English

#### **VaR (Value at Risk)**
"In 95% of days, I won't lose more than $X"

#### **CVaR (Conditional VaR)**
"In the worst 5% of days, I'll lose $Y on average"

#### **Maximum Drawdown**
"The biggest drop from peak to trough was Z%"

#### **Sharpe Ratio**
"For every 1% of risk I take, I get N% of return"

#### **Correlation**
"My stocks move together X% of the time"

---

## 🎓 Use Cases by Role

### **Risk Managers**
- Daily VaR monitoring
- Stress testing for board reports
- Regulatory compliance (Basel III)
- Limit monitoring and breaches

### **Portfolio Managers**
- Risk-adjusted performance (Sharpe, Sortino)
- Drawdown analysis
- Scenario planning
- Rebalancing decisions

### **Executives/Board**
- Simple summary reports
- Stress test results
- Historical context
- Risk vs return tradeoff

### **Regulators**
- VaR backtesting results
- Stress test documentation
- Model validation evidence
- Reverse stress testing

### **Traders**
- Real-time VaR monitoring
- Position risk limits
- Correlation changes
- Volatility forecasts

---

## 🔧 Configuration Tips

### Recommended Settings by Asset Class

**Equities**:
```python
confidence_level = 0.95  # or 0.99 for conservative
garch_p, garch_q = 1, 1
historical_window = 252  # 1 year
```

**Fixed Income**:
```python
confidence_level = 0.99  # More conservative
garch_p, garch_q = 1, 1
historical_window = 504  # 2 years
```

**FX (Currencies)**:
```python
confidence_level = 0.95
garch_p, garch_q = 1, 2  # More ARCH terms for FX
historical_window = 252
```

**Crypto**:
```python
confidence_level = 0.99  # Very volatile
garch_p, garch_q = 2, 2  # Higher orders
distribution = 't'  # Fat tails
historical_window = 126  # 6 months (faster market)
```

---

## 📈 Best Practices

### 1. **Always Backtest**
Never trust a VaR model without backtesting:
```python
from src.utils.backtesting import VaRBacktester
backtester = VaRBacktester(confidence_level=0.95)
results = backtester.backtest_var_model(test_returns, var_estimates, 1000000)
```

### 2. **Use Multiple Methods**
Different methods capture different risks:
- Historical: Captures actual patterns
- Parametric: Fast, assumes distribution
- Monte Carlo: Handles complex portfolios
- GARCH: Captures volatility clustering

### 3. **Stress Test Regularly**
Market conditions change:
```python
# Run weekly or monthly
stress_results = stress_tester.run_comprehensive_stress_test(returns, 1000000)
```

### 4. **Monitor Metrics Over Time**
Track how risk evolves:
- Rolling VaR
- Time-varying Sharpe Ratio
- Changing correlations

### 5. **Document Everything**
Generate and save reports:
```python
# Automated daily reporting
report_gen.save_excel_report(...)  # For records
text_report = report_gen.generate_var_summary_report(...)  # For email
```

---

## 🚨 Common Pitfalls to Avoid

1. **Don't rely solely on VaR**: Use CVaR and stress tests too
2. **Don't ignore tail events**: Black swans happen
3. **Don't assume stationary**: Markets change
4. **Don't skip backtesting**: Model validation is crucial
5. **Don't use too short historical windows**: Need enough data
6. **Don't ignore correlations**: Diversification can fail

---

## 📚 Further Reading

### Books
- "Value at Risk" by Philippe Jorion
- "Quantitative Risk Management" by McNeil, Frey, Embrechts
- "The Volatility Surface" by Jim Gatheral

### Regulations
- Basel III (BIS)
- Dodd-Frank Act
- MiFID II
- FRTB (Fundamental Review of Trading Book)

### Papers
- RiskMetrics Technical Document (J.P. Morgan, 1996)
- "Conditional Value-at-Risk" by Rockafellar & Uryasev
- "Backtesting" by Kupiec (1995)

---

## 💡 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Try the examples**: Run the example code in each module
3. **Generate a report**: Use the complete workflow above
4. **Customize scenarios**: Add your own stress scenarios
5. **Integrate with your workflow**: API endpoints available

---

**Questions? Check the main README.md or open an issue on GitHub!**
