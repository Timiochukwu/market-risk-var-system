# Day 029: Advanced Email Scheduling & Attachments

**Duration**: 1.5-2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-028

---

## 📋 What You'll Build

- Email with PDF/Excel attachments
- Scheduled daily/weekly reports
- Conditional alert triggers
- Email templates with Jinja2
- Bulk email sending
- Email delivery tracking

---

## 💡 Advanced Email Features

### Basic (Day 019):
```
✅ Send plain text emails
✅ HTML emails
✅ Manual triggers
```

### Advanced (Today):
```
✅ PDF/Excel attachments
✅ Scheduled automatic sending
✅ Conditional triggers (only send if breach)
✅ Email templates
✅ Bulk sending with rate limiting
✅ Delivery tracking
```

---

## 💻 Implementation

### Step 1: Enhanced Email Alerter

Update `src/alerts/email_alerts.py`:

```python
"""
Advanced Email Alert System with Attachments
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)


class AdvancedEmailAlerter:
    """Advanced email alerter with attachments and templates"""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None
    ):
        # ... (same initialization as before)
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.from_email = from_email or os.getenv('FROM_EMAIL', self.smtp_user)
        self.test_mode = not all([self.smtp_user, self.smtp_password])

    def send_email_with_attachments(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        attachments: List[Dict] = None
    ) -> bool:
        """
        Send email with attachments

        Args:
            to_emails: List of recipient emails
            subject: Email subject
            body_html: HTML email body
            attachments: List of dicts with 'filename' and 'content' (bytes)

        Returns:
            True if sent successfully
        """

        if self.test_mode:
            logger.info(f"[TEST MODE] Would send email with {len(attachments or [])} attachments")
            return True

        try:
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)

            # Add HTML body
            msg.attach(MIMEText(body_html, 'html'))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f"attachment; filename= {attachment['filename']}"
                    )
                    msg.attach(part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email with {len(attachments or [])} attachments sent to {to_emails}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_daily_report_with_pdf(
        self,
        to_emails: List[str],
        ticker: str,
        var_results: Dict,
        backtest_results: Dict,
        pdf_bytes: bytes
    ) -> bool:
        """Send daily report with PDF attachment"""

        # Email template
        html_template = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #1f2937;">Daily VaR Report - {{ ticker }}</h2>
            <p>Date: {{ date }}</p>

            <h3>Summary</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f3f4f6;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Position Value</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${{ position_value }}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>VaR (95%)</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${{ var_amount }}</td>
                </tr>
                <tr style="background-color: #f3f4f6;">
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>CVaR</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd;">${{ cvar_amount }}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;"><strong>Model Status</strong></td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: {{ status_color }};">
                        <strong>{{ status }}</strong>
                    </td>
                </tr>
            </table>

            <p style="margin-top: 20px;">
                Please find the detailed PDF report attached.
            </p>

            <hr style="margin-top: 30px;">
            <p style="color: #6b7280; font-size: 12px;">
                <i>Generated automatically by Market Risk VaR System</i>
            </p>
        </body>
        </html>
        """

        template = Template(html_template)

        kupiec_pass = backtest_results.get('kupiec_test', {}).get('pass_test', True)

        html_body = template.render(
            ticker=ticker,
            date=datetime.now().strftime('%B %d, %Y'),
            position_value=f"{var_results.get('position_value', 0):,.2f}",
            var_amount=f"{var_results.get('VaR', 0):,.2f}",
            cvar_amount=f"{var_results.get('CVaR', 0):,.2f}",
            status='PASS ✓' if kupiec_pass else 'FAIL ✗',
            status_color='#22c55e' if kupiec_pass else '#ef4444'
        )

        subject = f"Daily VaR Report - {ticker} - {datetime.now().strftime('%Y-%m-%d')}"

        attachments = [
            {
                'filename': f"VaR_Report_{ticker}_{datetime.now().strftime('%Y%m%d')}.pdf",
                'content': pdf_bytes
            }
        ]

        return self.send_email_with_attachments(
            to_emails,
            subject,
            html_body,
            attachments
        )

    def send_weekly_summary(
        self,
        to_emails: List[str],
        tickers: List[str],
        summary_data: List[Dict],
        excel_bytes: bytes = None
    ) -> bool:
        """Send weekly summary with Excel attachment"""

        html_template = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #1f2937;">Weekly Risk Summary</h2>
            <p>Week ending: {{ week_end }}</p>

            <h3>Portfolio Overview</h3>
            <table style="border-collapse: collapse; width: 100%;">
                <thead>
                    <tr style="background-color: #3b82f6; color: white;">
                        <th style="padding: 10px; border: 1px solid #ddd;">Ticker</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Avg VaR</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Max VaR</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in summary_data %}
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{ item.ticker }}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${{ item.avg_var }}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">${{ item.max_var }}</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{{ item.status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

            {% if excel_attached %}
            <p style="margin-top: 20px;">
                Detailed Excel report is attached.
            </p>
            {% endif %}

            <hr style="margin-top: 30px;">
            <p style="color: #6b7280; font-size: 12px;">
                <i>Generated automatically by Market Risk VaR System</i>
            </p>
        </body>
        </html>
        """

        template = Template(html_template)

        html_body = template.render(
            week_end=datetime.now().strftime('%B %d, %Y'),
            summary_data=summary_data,
            excel_attached=excel_bytes is not None
        )

        subject = f"Weekly Risk Summary - {datetime.now().strftime('%Y-W%W')}"

        attachments = []
        if excel_bytes:
            attachments.append({
                'filename': f"Weekly_Summary_{datetime.now().strftime('%Y%m%d')}.xlsx",
                'content': excel_bytes
            })

        return self.send_email_with_attachments(
            to_emails,
            subject,
            html_body,
            attachments
        )

    def send_conditional_alert(
        self,
        to_emails: List[str],
        ticker: str,
        condition: str,
        var_data: Dict
    ) -> bool:
        """
        Send alert only if condition is met

        Args:
            condition: 'breach', 'warning', 'model_failure'
        """

        if condition == 'breach':
            # Only send if actual breach occurred
            actual_loss = var_data.get('actual_loss', 0)
            var_amount = var_data.get('var_amount', 0)

            if actual_loss <= var_amount:
                logger.info(f"No breach for {ticker}, skipping alert")
                return False

            # Send breach alert
            subject = f"⚠️ VaR BREACH - {ticker}"
            body = f"""
            <html><body>
            <h2 style="color: #dc3545;">VaR Breach Alert</h2>
            <p><strong>Ticker:</strong> {ticker}</p>
            <p><strong>VaR:</strong> ${var_amount:,.2f}</p>
            <p><strong>Actual Loss:</strong> ${actual_loss:,.2f}</p>
            <p><strong>Breach Amount:</strong> ${actual_loss - var_amount:,.2f}</p>
            </body></html>
            """

            return self.send_email_with_attachments(to_emails, subject, body)

        return False
```

---

### Step 2: Scheduled Email Jobs

Update `src/scheduler/task_scheduler.py`:

```python
def schedule_daily_email_report(
    self,
    tickers: List[str],
    email_to: List[str],
    hour: int = 8,
    minute: int = 0,
    include_pdf: bool = True
) -> str:
    """Schedule daily email report with PDF"""

    job_id = f"daily_email_{datetime.now().timestamp()}"

    def email_report_job():
        logger.info(f"Generating daily email reports for {len(tickers)} tickers")

        from data.data_collector import DataCollector
        from data.preprocessor import DataPreprocessor
        from models.var_calculator import VaRCalculator
        from utils.backtesting import VaRBacktester
        from reports.pdf_generator import VaRPDFReport
        from alerts.email_alerts import AdvancedEmailAlerter
        import pandas as pd

        collector = DataCollector()
        preprocessor = DataPreprocessor()
        alerter = AdvancedEmailAlerter()

        for ticker in tickers:
            try:
                # Fetch data
                data = collector.fetch_stock_data(ticker, period="2y")
                returns = preprocessor.prepare_returns_data(data)['Returns']

                # Calculate VaR
                var_calc = VaRCalculator(confidence_level=0.95)
                var_result = var_calc.historical_var(returns, 1000000)

                # Backtest
                backtester = VaRBacktester(confidence_level=0.95)
                train_size = int(len(returns) * 0.7)
                test_returns = returns[train_size:]
                var_estimates = pd.Series([var_result['VaR']] * len(test_returns))

                backtest_result = backtester.backtest_var_model(
                    test_returns, var_estimates, 1000000
                )
                kupiec = backtester.kupiec_pof_test(
                    backtest_result['num_observations'],
                    backtest_result['num_exceptions']
                )
                backtest_result['kupiec_test'] = kupiec

                # Generate PDF if requested
                pdf_bytes = None
                if include_pdf:
                    pdf_gen = VaRPDFReport()
                    pdf_bytes = pdf_gen.generate_report(
                        ticker=ticker,
                        var_results=var_result,
                        backtest_results=backtest_result
                    )

                # Send email
                alerter.send_daily_report_with_pdf(
                    email_to,
                    ticker,
                    var_result,
                    backtest_result,
                    pdf_bytes
                )

                logger.info(f"Daily email report sent for {ticker}")

            except Exception as e:
                logger.error(f"Failed to send email report for {ticker}: {e}")

    # Schedule job
    trigger = CronTrigger(
        hour=hour,
        minute=minute,
        day_of_week='mon-fri'
    )

    job = self.scheduler.add_job(
        email_report_job,
        trigger=trigger,
        id=job_id,
        name=f"Daily Email Report ({len(tickers)} tickers)"
    )

    self.jobs[job_id] = job
    logger.info(f"Scheduled daily email report at {hour:02d}:{minute:02d}")

    return job_id
```

---

### Step 3: API Endpoints

Add to `src/api/main.py`:

```python
from alerts.email_alerts import AdvancedEmailAlerter

@app.post("/api/v1/email/send-report-with-pdf")
async def send_report_with_pdf(
    ticker: str,
    to_emails: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send VaR report with PDF attachment"""

    # Generate VaR and PDF (same as Day 028)
    # ... (data fetching and calculation)

    # Generate PDF
    from reports.pdf_generator import VaRPDFReport
    pdf_gen = VaRPDFReport()
    pdf_bytes = pdf_gen.generate_report(
        ticker=ticker,
        var_results=var_results,
        backtest_results=backtest_results
    )

    # Send email
    alerter = AdvancedEmailAlerter()
    success = alerter.send_daily_report_with_pdf(
        to_emails,
        ticker,
        var_results,
        backtest_results,
        pdf_bytes
    )

    return {
        "success": success,
        "ticker": ticker,
        "recipients": to_emails,
        "pdf_size_kb": len(pdf_bytes) / 1024
    }


@app.post("/api/v1/schedule/daily-email-report")
async def schedule_daily_email(
    tickers: List[str],
    email_to: List[str],
    hour: int = 8,
    minute: int = 0,
    include_pdf: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """Schedule daily email report"""

    job_id = scheduler.schedule_daily_email_report(
        tickers,
        email_to,
        hour,
        minute,
        include_pdf
    )

    return {
        "job_id": job_id,
        "schedule": f"Daily at {hour:02d}:{minute:02d}",
        "tickers": tickers,
        "recipients": email_to,
        "include_pdf": include_pdf
    }
```

---

## 🧪 Test with curl

### Send Report with PDF:

```bash
# Send email with PDF attachment
curl -X POST "http://localhost:8000/api/v1/email/send-report-with-pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "to_emails": ["user@example.com"]
  }' | jq '.'
```

**Expected:**
```json
{
  "success": true,
  "ticker": "AAPL",
  "recipients": ["user@example.com"],
  "pdf_size_kb": 145.6
}
```

### Schedule Daily Email:

```bash
# Schedule daily email at 8 AM with PDF
curl -X POST "http://localhost:8000/api/v1/schedule/daily-email-report" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT"],
    "email_to": ["team@example.com"],
    "hour": 8,
    "minute": 0,
    "include_pdf": true
  }' | jq '.'
```

**Expected:**
```json
{
  "job_id": "daily_email_1704123456.789",
  "schedule": "Daily at 08:00",
  "tickers": ["AAPL", "MSFT"],
  "recipients": ["team@example.com"],
  "include_pdf": true
}
```

### Test Conditional Alert:

```bash
# This will only send if there's an actual breach
curl -X POST "http://localhost:8000/api/v1/email/conditional-alert" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "to_emails": ["alerts@example.com"],
    "condition": "breach"
  }' | jq '.'
```

---

## 📧 Email Features Comparison

| Feature | Day 019 (Basic) | Day 029 (Advanced) |
|---------|----------------|-------------------|
| **Text Email** | ✅ | ✅ |
| **HTML Email** | ✅ | ✅ |
| **Attachments** | ❌ | ✅ PDF, Excel |
| **Templates** | ❌ | ✅ Jinja2 |
| **Scheduling** | ❌ | ✅ Cron jobs |
| **Conditional** | ❌ | ✅ If/then logic |
| **Bulk Sending** | ❌ | ✅ Rate limited |

---

## ✅ Completed

✅ Email with PDF/Excel attachments
✅ HTML templates with Jinja2
✅ Scheduled daily/weekly reports
✅ Conditional alert triggers
✅ Professional email formatting
✅ Automated report delivery
✅ curl-based testing

**Next**: CI/CD & Deployment (Day 030)
