"""
Report Generation Module for Market Risk VaR System

This module creates professional risk reports in multiple formats:
- Excel spreadsheets (for further analysis)
- HTML reports (for web viewing)
- Summary text reports (for email)

Risk reports are essential for:
1. Management communication
2. Regulatory compliance (Basel III, MiFID II)
3. Board meetings and investor updates
4. Internal risk monitoring
5. Audit trails
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskReportGenerator:
    """
    Generate comprehensive risk reports in various formats

    This class takes all your risk calculations and packages them
    into professional reports that executives, regulators, and
    investors can understand.

    Think of this as your "risk communication layer"
    """

    def __init__(self, output_dir: str = "../../reports"):
        """
        Initialize report generator

        Args:
            output_dir: Directory where reports will be saved
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_var_summary_report(
        self,
        ticker: str,
        var_results: pd.DataFrame,
        position_value: float,
        confidence_level: float,
        backtest_results: Optional[Dict] = None
    ) -> str:
        """
        Generate a text summary report for VaR analysis

        This creates a concise, readable summary perfect for:
        - Email updates
        - Quick reviews
        - Dashboard summaries

        Args:
            ticker: Stock ticker symbol
            var_results: DataFrame with VaR calculations
            position_value: Portfolio value
            confidence_level: Confidence level used
            backtest_results: Optional backtest results

        Returns:
            String with formatted report
        """
        report = []
        report.append("=" * 80)
        report.append(f"VALUE AT RISK (VaR) SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Ticker: {ticker}")
        report.append(f"Position Value: ${position_value:,.2f}")
        report.append(f"Confidence Level: {confidence_level*100:.1f}%")
        report.append("=" * 80)
        report.append("")

        # VaR estimates section
        report.append("VaR ESTIMATES BY METHOD")
        report.append("-" * 80)

        for _, row in var_results.iterrows():
            report.append(f"{row['Method']:30s} ${row['VaR']:>15,.2f}")

        report.append("-" * 80)
        report.append(f"{'Minimum VaR:':30s} ${var_results['VaR'].min():>15,.2f}")
        report.append(f"{'Maximum VaR:':30s} ${var_results['VaR'].max():>15,.2f}")
        report.append(f"{'Average VaR:':30s} ${var_results['VaR'].mean():>15,.2f}")
        report.append("")

        # Interpretation section
        report.append("INTERPRETATION")
        report.append("-" * 80)
        avg_var = var_results['VaR'].mean()
        var_pct = (avg_var / position_value) * 100
        report.append(f"With {confidence_level*100:.0f}% confidence, we expect that losses will NOT exceed")
        report.append(f"${avg_var:,.2f} ({var_pct:.2f}% of portfolio) in a single day.")
        report.append("")
        report.append(f"In other words: There is a {(1-confidence_level)*100:.0f}% chance of losing more than ${avg_var:,.2f}")
        report.append(f"in one day.")
        report.append("")

        # Backtest results if available
        if backtest_results:
            report.append("BACKTEST VALIDATION")
            report.append("-" * 80)
            report.append(f"Number of Exceptions: {backtest_results['num_exceptions']}")
            report.append(f"Exception Rate: {backtest_results['exception_rate']*100:.2f}%")
            report.append(f"Expected Rate: {backtest_results['expected_rate']*100:.2f}%")
            report.append(f"Traffic Light Zone: {backtest_results['traffic_light_test']['Zone']}")

            # Interpretation
            if backtest_results['traffic_light_test']['Zone'] == 'Green':
                report.append("\n✓ Model validation: PASSED (Acceptable)")
            elif backtest_results['traffic_light_test']['Zone'] == 'Yellow':
                report.append("\n⚠ Model validation: WARNING (Needs monitoring)")
            else:
                report.append("\n✗ Model validation: FAILED (Model adjustment required)")
            report.append("")

        # Risk warnings
        report.append("RISK WARNINGS")
        report.append("-" * 80)
        report.append("• VaR does not predict maximum possible loss")
        report.append("• Past performance does not guarantee future results")
        report.append("• Consider stress testing for extreme scenarios")
        report.append("• VaR assumes normal market conditions")
        report.append("")

        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)

        return "\n".join(report)

    def save_excel_report(
        self,
        ticker: str,
        var_results: pd.DataFrame,
        garch_forecast: Optional[pd.DataFrame] = None,
        arima_forecast: Optional[pd.DataFrame] = None,
        backtest_results: Optional[pd.DataFrame] = None,
        advanced_metrics: Optional[Dict] = None
    ) -> str:
        """
        Generate a comprehensive Excel report with multiple sheets

        Excel reports are great because:
        - Stakeholders can do their own analysis
        - Easy to share and distribute
        - Can include charts and formatting
        - Familiar format for everyone

        Args:
            ticker: Stock ticker
            var_results: VaR calculation results
            garch_forecast: GARCH volatility forecast
            arima_forecast: ARIMA returns forecast
            backtest_results: Backtest exception details
            advanced_metrics: Advanced risk metrics

        Returns:
            Path to saved Excel file
        """
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"VaR_Report_{ticker}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)

        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: VaR Summary
            var_results.to_excel(writer, sheet_name='VaR Summary', index=False)

            # Sheet 2: GARCH Forecast (if available)
            if garch_forecast is not None:
                garch_forecast.to_excel(writer, sheet_name='GARCH Forecast', index=True)

            # Sheet 3: ARIMA Forecast (if available)
            if arima_forecast is not None:
                arima_forecast.to_excel(writer, sheet_name='ARIMA Forecast', index=True)

            # Sheet 4: Backtest Results (if available)
            if backtest_results is not None:
                backtest_results.to_excel(writer, sheet_name='Backtest Results', index=True)

            # Sheet 5: Advanced Metrics (if available)
            if advanced_metrics is not None:
                # Convert nested dict to flat DataFrame
                metrics_data = []

                if 'CVaR' in advanced_metrics:
                    cvar = advanced_metrics['CVaR']
                    metrics_data.append(['CVaR', f"${cvar['CVaR']:,.2f}"])
                    metrics_data.append(['Tail Risk', f"${cvar['Tail_Risk']:,.2f}"])

                if 'Maximum_Drawdown' in advanced_metrics:
                    mdd = advanced_metrics['Maximum_Drawdown']
                    metrics_data.append(['Max Drawdown', f"{mdd['Max_Drawdown_Percentage']:.2f}%"])

                if 'Sharpe_Ratio' in advanced_metrics:
                    metrics_data.append(['Sharpe Ratio', f"{advanced_metrics['Sharpe_Ratio']:.4f}"])

                if 'Sortino_Ratio' in advanced_metrics:
                    metrics_data.append(['Sortino Ratio', f"{advanced_metrics['Sortino_Ratio']:.4f}"])

                if 'Calmar_Ratio' in advanced_metrics:
                    metrics_data.append(['Calmar Ratio', f"{advanced_metrics['Calmar_Ratio']:.4f}"])

                metrics_df = pd.DataFrame(metrics_data, columns=['Metric', 'Value'])
                metrics_df.to_excel(writer, sheet_name='Advanced Metrics', index=False)

            # Sheet 6: Report Info
            info_data = [
                ['Report Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Ticker', ticker],
                ['Report Type', 'Comprehensive VaR Analysis'],
                ['Generated By', 'Market Risk VaR System v1.0']
            ]
            info_df = pd.DataFrame(info_data, columns=['Field', 'Value'])
            info_df.to_excel(writer, sheet_name='Report Info', index=False)

        logger.info(f"Excel report saved: {filepath}")
        return filepath

    def generate_html_report(
        self,
        ticker: str,
        var_results: pd.DataFrame,
        position_value: float,
        confidence_level: float
    ) -> str:
        """
        Generate an HTML report for web viewing

        HTML reports are perfect for:
        - Sharing via email
        - Publishing to intranet
        - Dashboard integration
        - Mobile viewing

        Args:
            ticker: Stock ticker
            var_results: VaR calculation results
            position_value: Portfolio value
            confidence_level: Confidence level

        Returns:
            Path to saved HTML file
        """
        # Create filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"VaR_Report_{ticker}_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)

        # HTML template with styling
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
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .metric {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Value at Risk (VaR) Report</h1>

                <div class="metric">
                    <strong>Ticker:</strong> {ticker}<br>
                    <strong>Position Value:</strong> ${position_value:,.2f}<br>
                    <strong>Confidence Level:</strong> {confidence_level*100:.1f}%<br>
                    <strong>Report Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>

                <h2>VaR Estimates by Method</h2>
                <table>
                    <tr>
                        <th>Method</th>
                        <th>VaR (USD)</th>
                        <th>VaR (%)</th>
                    </tr>
        """

        # Add VaR results to table
        for _, row in var_results.iterrows():
            var_pct = (row['VaR'] / position_value) * 100
            html += f"""
                    <tr>
                        <td>{row['Method']}</td>
                        <td>${row['VaR']:,.2f}</td>
                        <td>{var_pct:.2f}%</td>
                    </tr>
            """

        # Add summary statistics
        avg_var = var_results['VaR'].mean()
        min_var = var_results['VaR'].min()
        max_var = var_results['VaR'].max()

        html += f"""
                </table>

                <h2>Summary Statistics</h2>
                <div class="metric">
                    <strong>Average VaR:</strong> ${avg_var:,.2f}<br>
                    <strong>Minimum VaR:</strong> ${min_var:,.2f}<br>
                    <strong>Maximum VaR:</strong> ${max_var:,.2f}<br>
                    <strong>Range:</strong> ${max_var - min_var:,.2f}
                </div>

                <h2>Interpretation</h2>
                <p>
                    With {confidence_level*100:.0f}% confidence, we expect that losses will <strong>NOT exceed
                    ${avg_var:,.2f}</strong> ({(avg_var/position_value)*100:.2f}% of portfolio) in a single day.
                </p>
                <p>
                    In other words: There is a <strong>{(1-confidence_level)*100:.0f}% chance</strong> of losing
                    more than ${avg_var:,.2f} in one day.
                </p>

                <div class="warning">
                    <strong>⚠ Risk Warnings:</strong><br>
                    • VaR does not predict maximum possible loss<br>
                    • Past performance does not guarantee future results<br>
                    • Consider stress testing for extreme scenarios<br>
                    • VaR assumes normal market conditions
                </div>

                <div class="footer">
                    Generated by Market Risk VaR System v1.0<br>
                    This report is for informational purposes only and does not constitute investment advice.
                </div>
            </div>
        </body>
        </html>
        """

        # Save HTML file
        with open(filepath, 'w') as f:
            f.write(html)

        logger.info(f"HTML report saved: {filepath}")
        return filepath

    def generate_stress_test_report(
        self,
        ticker: str,
        stress_results: pd.DataFrame
    ) -> str:
        """
        Generate a stress test summary report

        Args:
            ticker: Stock ticker
            stress_results: Stress test results DataFrame

        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 80)
        report.append(f"STRESS TEST REPORT - {ticker}")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")

        report.append("SCENARIO ANALYSIS RESULTS")
        report.append("-" * 80)

        # Show each scenario
        for _, row in stress_results.iterrows():
            report.append(f"\nScenario: {row['Scenario']}")

            if 'Portfolio_Loss' in row and pd.notna(row['Portfolio_Loss']):
                report.append(f"  Portfolio Loss: ${row['Portfolio_Loss']:,.2f}")

            if 'New_Portfolio_Value' in row and pd.notna(row['New_Portfolio_Value']):
                report.append(f"  New Portfolio Value: ${row['New_Portfolio_Value']:,.2f}")

            if 'Stressed_VaR' in row and pd.notna(row['Stressed_VaR']):
                report.append(f"  Stressed VaR: ${row['Stressed_VaR']:,.2f}")

        report.append("")
        report.append("=" * 80)
        report.append("KEY INSIGHTS")
        report.append("=" * 80)

        # Find worst scenario
        if 'Portfolio_Loss' in stress_results.columns:
            worst_idx = stress_results['Portfolio_Loss'].idxmax()
            worst_scenario = stress_results.loc[worst_idx]
            report.append(f"\nWorst Case Scenario: {worst_scenario['Scenario']}")
            report.append(f"Potential Loss: ${worst_scenario['Portfolio_Loss']:,.2f}")

        report.append("\n" + "=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)
        report.append("1. Review portfolio hedging strategies")
        report.append("2. Consider tail risk hedging instruments")
        report.append("3. Ensure adequate capital reserves")
        report.append("4. Monitor market conditions closely")
        report.append("")

        return "\n".join(report)

    def save_report(self, report_text: str, filename: str) -> str:
        """
        Save a text report to file

        Args:
            report_text: Report content
            filename: Filename (without path)

        Returns:
            Path to saved file
        """
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w') as f:
            f.write(report_text)

        logger.info(f"Report saved: {filepath}")
        return filepath


# Example usage
if __name__ == "__main__":
    # Create sample data for demonstration
    import sys
    sys.path.append('../..')

    # Sample VaR results
    var_results = pd.DataFrame({
        'Method': ['Historical', 'Parametric', 'Monte Carlo'],
        'VaR': [15234.56, 14892.34, 15567.89]
    })

    # Generate reports
    report_gen = RiskReportGenerator()

    # Text report
    print("\n" + "="*80)
    print("GENERATING SAMPLE REPORTS")
    print("="*80)

    text_report = report_gen.generate_var_summary_report(
        ticker='AAPL',
        var_results=var_results,
        position_value=1000000,
        confidence_level=0.95
    )

    print(text_report)

    # Save reports
    text_file = report_gen.save_report(text_report, 'sample_var_report.txt')
    print(f"\nText report saved to: {text_file}")

    excel_file = report_gen.save_excel_report(
        ticker='AAPL',
        var_results=var_results
    )
    print(f"Excel report saved to: {excel_file}")

    html_file = report_gen.generate_html_report(
        ticker='AAPL',
        var_results=var_results,
        position_value=1000000,
        confidence_level=0.95
    )
    print(f"HTML report saved to: {html_file}")
