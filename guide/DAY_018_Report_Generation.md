# Day 018: Report Generation

**Duration**: 1.5-2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-017

---

## 📋 What You'll Build

- Excel report generator
- HTML report with charts
- Text-based summary reports
- Report templates
- Report API endpoint

---

## 💡 Report Types

### 1. Excel Reports
```
VaR_Report_AAPL_2024-01-15.xlsx
├── Summary Sheet
├── Backtest Results
├── Historical VaR Data
└── Risk Metrics
```

### 2. HTML Reports
```html
Interactive dashboard with:
- Risk metrics summary
- VaR charts (time series)
- Exception analysis
- Traffic light indicators
```

### 3. Text Reports
```
═══════════════════════════════════════
VaR RISK REPORT - AAPL
═══════════════════════════════════════
Date: 2024-01-15
Position: $1,000,000
Confidence: 95%
---
VaR (1-day): $28,456
CVaR: $42,123
Sharpe Ratio: 1.85
Max Drawdown: -12.3%
═══════════════════════════════════════
```

---

## 💻 Implementation

Create `src/reports/report_generator.py`:

```python
"""
Report Generation Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import io


class ReportGenerator:
    """Generate VaR reports in multiple formats"""

    def __init__(self):
        self.report_date = datetime.now()

    def generate_excel_report(
        self,
        ticker: str,
        var_results: Dict,
        backtest_results: Dict,
        metrics: Dict,
        output_path: str = None
    ) -> bytes:
        """
        Generate Excel report

        Returns:
            Excel file as bytes (can be sent via API)
        """

        # Create Excel writer (in-memory)
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:

            # Sheet 1: Summary
            summary_data = {
                'Metric': [
                    'Ticker',
                    'Report Date',
                    'Position Value',
                    'Confidence Level',
                    'VaR (1-day)',
                    'VaR %',
                    'CVaR',
                    'Method'
                ],
                'Value': [
                    ticker,
                    self.report_date.strftime('%Y-%m-%d'),
                    f"${var_results.get('position_value', 0):,.2f}",
                    f"{var_results.get('confidence_level', 0)*100:.0f}%",
                    f"${var_results.get('VaR', 0):,.2f}",
                    f"{var_results.get('VaR_Percentage', 0):.4f}%",
                    f"${var_results.get('CVaR', 0):,.2f}",
                    var_results.get('method', 'N/A')
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Sheet 2: Backtest Results
            if backtest_results:
                backtest_data = {
                    'Metric': [
                        'Total Observations',
                        'Number of Exceptions',
                        'Exception Rate',
                        'Expected Rate',
                        'Mean Excess Loss',
                        'Max Excess Loss',
                        'Kupiec p-value',
                        'Kupiec Result'
                    ],
                    'Value': [
                        backtest_results.get('num_observations', 0),
                        backtest_results.get('num_exceptions', 0),
                        f"{backtest_results.get('exception_rate', 0)*100:.2f}%",
                        f"{backtest_results.get('expected_rate', 0)*100:.2f}%",
                        f"${backtest_results.get('mean_excess_loss', 0):,.2f}",
                        f"${backtest_results.get('max_excess_loss', 0):,.2f}",
                        f"{backtest_results.get('kupiec_test', {}).get('p_value', 0):.4f}",
                        'PASS' if backtest_results.get('kupiec_test', {}).get('pass_test', False) else 'FAIL'
                    ]
                }
                backtest_df = pd.DataFrame(backtest_data)
                backtest_df.to_excel(writer, sheet_name='Backtest', index=False)

            # Sheet 3: Risk Metrics
            if metrics:
                metrics_data = {
                    'Metric': list(metrics.keys()),
                    'Value': [f"{v:.4f}" if isinstance(v, float) else str(v)
                             for v in metrics.values()]
                }
                metrics_df = pd.DataFrame(metrics_data)
                metrics_df.to_excel(writer, sheet_name='Risk Metrics', index=False)

        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(output.getvalue())

        output.seek(0)
        return output.getvalue()

    def generate_html_report(
        self,
        ticker: str,
        var_results: Dict,
        backtest_results: Dict,
        metrics: Dict
    ) -> str:
        """Generate HTML report"""

        # Determine status color
        kupiec_pass = backtest_results.get('kupiec_test', {}).get('pass_test', False)
        status_color = '#28a745' if kupiec_pass else '#dc3545'
        status_text = 'PASS ✓' if kupiec_pass else 'FAIL ✗'

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>VaR Report - {ticker}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }}
        .metric-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            color: white;
            background-color: {status_color};
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Value at Risk Report - {ticker}</h1>
        <p><strong>Report Date:</strong> {self.report_date.strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>VaR Summary</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Position Value</div>
                <div class="metric-value">${var_results.get('position_value', 0):,.0f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">VaR (1-day, {var_results.get('confidence_level', 0)*100:.0f}%)</div>
                <div class="metric-value">${var_results.get('VaR', 0):,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">VaR Percentage</div>
                <div class="metric-value">{var_results.get('VaR_Percentage', 0):.3f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">CVaR (Expected Shortfall)</div>
                <div class="metric-value">${var_results.get('CVaR', 0):,.2f}</div>
            </div>
        </div>

        <h2>Backtest Results <span class="status-badge">{status_text}</span></h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Observations</td>
                <td>{backtest_results.get('num_observations', 0)}</td>
            </tr>
            <tr>
                <td>Number of Exceptions</td>
                <td>{backtest_results.get('num_exceptions', 0)}</td>
            </tr>
            <tr>
                <td>Exception Rate</td>
                <td>{backtest_results.get('exception_rate', 0)*100:.2f}%</td>
            </tr>
            <tr>
                <td>Expected Rate</td>
                <td>{backtest_results.get('expected_rate', 0)*100:.2f}%</td>
            </tr>
            <tr>
                <td>Kupiec p-value</td>
                <td>{backtest_results.get('kupiec_test', {}).get('p_value', 0):.4f}</td>
            </tr>
        </table>

        <h2>Advanced Risk Metrics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Sharpe Ratio</div>
                <div class="metric-value">{metrics.get('sharpe_ratio', 0):.3f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Sortino Ratio</div>
                <div class="metric-value">{metrics.get('sortino_ratio', 0):.3f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Max Drawdown</div>
                <div class="metric-value">{metrics.get('max_drawdown', 0)*100:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Calmar Ratio</div>
                <div class="metric-value">{metrics.get('calmar_ratio', 0):.3f}</div>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Market Risk VaR System | Method: {var_results.get('method', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def generate_text_report(
        self,
        ticker: str,
        var_results: Dict,
        backtest_results: Dict,
        metrics: Dict
    ) -> str:
        """Generate text-based report"""

        report = f"""
{'='*70}
VALUE AT RISK REPORT - {ticker}
{'='*70}
Report Date: {self.report_date.strftime('%Y-%m-%d %H:%M:%S')}
Method: {var_results.get('method', 'N/A')}

{'='*70}
VaR SUMMARY
{'='*70}
Position Value:         ${var_results.get('position_value', 0):,.2f}
Confidence Level:       {var_results.get('confidence_level', 0)*100:.0f}%
VaR (1-day):           ${var_results.get('VaR', 0):,.2f}
VaR Percentage:        {var_results.get('VaR_Percentage', 0):.4f}%
CVaR:                  ${var_results.get('CVaR', 0):,.2f}

{'='*70}
BACKTEST RESULTS
{'='*70}
Total Observations:     {backtest_results.get('num_observations', 0)}
Exceptions:            {backtest_results.get('num_exceptions', 0)}
Exception Rate:        {backtest_results.get('exception_rate', 0)*100:.2f}%
Expected Rate:         {backtest_results.get('expected_rate', 0)*100:.2f}%
Mean Excess Loss:      ${backtest_results.get('mean_excess_loss', 0):,.2f}
Max Excess Loss:       ${backtest_results.get('max_excess_loss', 0):,.2f}

Kupiec Test:
  LR Statistic:        {backtest_results.get('kupiec_test', {}).get('lr_statistic', 0):.4f}
  p-value:             {backtest_results.get('kupiec_test', {}).get('p_value', 0):.4f}
  Result:              {'PASS ✓' if backtest_results.get('kupiec_test', {}).get('pass_test', False) else 'FAIL ✗'}

{'='*70}
ADVANCED RISK METRICS
{'='*70}
Sharpe Ratio:          {metrics.get('sharpe_ratio', 0):.4f}
Sortino Ratio:         {metrics.get('sortino_ratio', 0):.4f}
Max Drawdown:          {metrics.get('max_drawdown', 0)*100:.2f}%
Calmar Ratio:          {metrics.get('calmar_ratio', 0):.4f}
Daily Volatility:      {metrics.get('volatility', 0)*100:.2f}%
Skewness:              {metrics.get('skewness', 0):.4f}
Kurtosis:              {metrics.get('kurtosis', 0):.4f}

{'='*70}
Generated by Market Risk VaR System
{'='*70}
"""
        return report
```

---

## 🧪 API Endpoint

Add to `src/api/main.py`:

```python
from fastapi.responses import Response, HTMLResponse

@app.post("/api/v1/reports/excel")
async def generate_excel_report(
    ticker: str,
    confidence_level: float = 0.95,
    position_value: float = 1000000
):
    """Generate Excel report"""

    from reports.report_generator import ReportGenerator

    # Get VaR results
    data = data_collector.fetch_stock_data(ticker, period="2y")
    returns = preprocessor.prepare_returns_data(data)['Returns']

    var_calc = VaRCalculator(confidence_level=confidence_level)
    var_results = var_calc.historical_var(returns, position_value)

    # Get backtest results
    backtester = VaRBacktester(confidence_level=confidence_level)
    train_size = int(len(returns) * 0.7)
    test_returns = returns[train_size:]
    var_estimates = pd.Series([var_results['VaR']] * len(test_returns))

    backtest_results = backtester.backtest_var_model(
        test_returns, var_estimates, position_value
    )

    kupiec = backtester.kupiec_pof_test(
        backtest_results['num_observations'],
        backtest_results['num_exceptions']
    )
    backtest_results['kupiec_test'] = kupiec

    # Get advanced metrics
    from utils.advanced_metrics import AdvancedMetrics
    advanced = AdvancedMetrics()
    metrics = advanced.calculate_all_metrics(returns)

    # Generate report
    generator = ReportGenerator()
    excel_bytes = generator.generate_excel_report(
        ticker, var_results, backtest_results, metrics
    )

    # Return as downloadable file
    filename = f"VaR_Report_{ticker}_{datetime.now().strftime('%Y%m%d')}.xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/v1/reports/html", response_class=HTMLResponse)
async def generate_html_report(
    ticker: str,
    confidence_level: float = 0.95,
    position_value: float = 1000000
):
    """Generate HTML report"""

    from reports.report_generator import ReportGenerator

    # ... (same data collection as Excel endpoint)

    generator = ReportGenerator()
    html = generator.generate_html_report(
        ticker, var_results, backtest_results, metrics
    )

    return HTMLResponse(content=html)


@app.post("/api/v1/reports/text")
async def generate_text_report(
    ticker: str,
    confidence_level: float = 0.95,
    position_value: float = 1000000
):
    """Generate text report"""

    from reports.report_generator import ReportGenerator

    # ... (same data collection)

    generator = ReportGenerator()
    text = generator.generate_text_report(
        ticker, var_results, backtest_results, metrics
    )

    return {"report": text}
```

**Note**: You'll need to install openpyxl:
```bash
pip install openpyxl==3.1.2
```

---

## 🧪 Test with curl

### Excel Report (download file):

```bash
# Generate and download Excel report
curl -X POST "http://localhost:8000/api/v1/reports/excel?ticker=AAPL&confidence_level=0.95" \
  --output VaR_Report_AAPL.xlsx

# Verify file was created
ls -lh VaR_Report_AAPL.xlsx
```

### HTML Report (view in browser):

```bash
# Generate HTML and save to file
curl -X POST "http://localhost:8000/api/v1/reports/html?ticker=AAPL" \
  --output report.html

# Open in browser (Mac)
open report.html

# Or Linux
xdg-open report.html
```

### Text Report:

```bash
# Generate text report
curl -X POST "http://localhost:8000/api/v1/reports/text?ticker=AAPL" \
  | jq -r '.report'
```

**Expected Output:**
```
======================================================================
VALUE AT RISK REPORT - AAPL
======================================================================
Report Date: 2024-01-15 14:30:22
Method: historical

======================================================================
VaR SUMMARY
======================================================================
Position Value:         $1,000,000.00
Confidence Level:       95%
VaR (1-day):           $28,456.78
VaR Percentage:        2.8457%
CVaR:                  $42,123.45

======================================================================
BACKTEST RESULTS
======================================================================
...
```

### Generate Multiple Reports:

```bash
# Generate reports for multiple stocks
for ticker in AAPL MSFT GOOGL; do
  echo "Generating report for $ticker..."
  curl -X POST "http://localhost:8000/api/v1/reports/excel?ticker=$ticker" \
    --output "VaR_Report_${ticker}.xlsx"
done

ls -lh VaR_Report_*.xlsx
```

---

## ✅ Completed

✅ Excel report generator with openpyxl
✅ HTML interactive reports
✅ Text-based summary reports
✅ Report download via API
✅ curl-based report generation

**Next**: Email Alerts (Day 019)
