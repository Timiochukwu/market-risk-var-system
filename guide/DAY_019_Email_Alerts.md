# Day 019: Email Alerts & Notifications

**Duration**: 1.5-2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-018

---

## 📋 What You'll Build

- Email alert system with SMTP
- VaR breach notifications
- Daily risk summary emails
- Scheduled alert triggers
- Email templates (HTML & Text)
- Alert API endpoint

---

## 💡 Alert Types

### 1. VaR Breach Alert
```
Subject: ⚠️ VaR BREACH - AAPL - 2024-01-15

Your AAPL position exceeded VaR threshold:
- VaR (95%): $28,456
- Actual Loss: $35,678
- Breach Amount: $7,222
- Severity: MEDIUM
```

### 2. Daily Risk Summary
```
Subject: 📊 Daily Risk Report - 2024-01-15

Portfolio Summary:
- Total VaR: $45,678
- Sharpe Ratio: 1.85
- Max Drawdown: -12.3%
- Status: GREEN (All tests passed)
```

### 3. Backtest Failure Alert
```
Subject: ❌ VaR Model Failed - AAPL

Kupiec test failed:
- p-value: 0.023 (< 0.05)
- Exception rate: 8.5% (expected 5%)
- Action Required: Review model
```

---

## 💻 Implementation

Create `src/alerts/email_alerts.py`:

```python
"""
Email Alert System
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class EmailAlerter:
    """Send email alerts for VaR events"""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_email: str = None
    ):
        """
        Initialize email alerter

        For Gmail:
            smtp_host: 'smtp.gmail.com'
            smtp_port: 587
            smtp_user: your_email@gmail.com
            smtp_password: your_app_password (NOT your regular password!)

        For testing (no real emails):
            Leave all parameters None
        """

        # Use environment variables if not provided
        self.smtp_host = smtp_host or os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = smtp_user or os.getenv('SMTP_USER')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.from_email = from_email or os.getenv('FROM_EMAIL', self.smtp_user)

        # Test mode if no credentials
        self.test_mode = not all([self.smtp_user, self.smtp_password])

        if self.test_mode:
            logger.warning("Email alerter in TEST MODE (no credentials)")

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_text: str,
        body_html: str = None
    ) -> bool:
        """
        Send email

        Returns:
            True if sent successfully
        """

        if self.test_mode:
            logger.info(f"[TEST MODE] Would send email:")
            logger.info(f"  To: {to_emails}")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Body:\n{body_text}")
            return True

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)

            # Add text version
            msg.attach(MIMEText(body_text, 'plain'))

            # Add HTML version if provided
            if body_html:
                msg.attach(MIMEText(body_html, 'html'))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_emails}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_var_breach_alert(
        self,
        to_emails: List[str],
        ticker: str,
        var_amount: float,
        actual_loss: float,
        breach_amount: float,
        position_value: float
    ) -> bool:
        """Send VaR breach alert"""

        breach_pct = (breach_amount / var_amount) * 100

        # Severity
        if breach_pct < 20:
            severity = "LOW"
            icon = "⚠️"
        elif breach_pct < 50:
            severity = "MEDIUM"
            icon = "⚠️⚠️"
        else:
            severity = "HIGH"
            icon = "🔴"

        subject = f"{icon} VaR BREACH - {ticker} - {datetime.now().strftime('%Y-%m-%d')}"

        body_text = f"""
VaR BREACH ALERT

Ticker: {ticker}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Severity: {severity}

Position Details:
  Position Value:    ${position_value:,.2f}
  VaR (95%):        ${var_amount:,.2f}
  Actual Loss:      ${actual_loss:,.2f}
  Breach Amount:    ${breach_amount:,.2f}
  Breach %:         {breach_pct:.1f}%

Action Required:
  1. Review position immediately
  2. Assess risk exposure
  3. Consider position reduction
  4. Update risk limits if necessary

---
Generated by Market Risk VaR System
"""

        body_html = f"""
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #dc3545;">{icon} VaR BREACH ALERT</h2>
    <p><strong>Ticker:</strong> {ticker}<br>
    <strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
    <strong>Severity:</strong> <span style="color: #dc3545; font-weight: bold;">{severity}</span></p>

    <h3>Position Details</h3>
    <table style="border-collapse: collapse;">
        <tr><td style="padding: 5px;"><strong>Position Value:</strong></td><td style="padding: 5px;">${position_value:,.2f}</td></tr>
        <tr><td style="padding: 5px;"><strong>VaR (95%):</strong></td><td style="padding: 5px;">${var_amount:,.2f}</td></tr>
        <tr><td style="padding: 5px;"><strong>Actual Loss:</strong></td><td style="padding: 5px; color: #dc3545;">${actual_loss:,.2f}</td></tr>
        <tr><td style="padding: 5px;"><strong>Breach Amount:</strong></td><td style="padding: 5px; color: #dc3545;">${breach_amount:,.2f}</td></tr>
        <tr><td style="padding: 5px;"><strong>Breach %:</strong></td><td style="padding: 5px; color: #dc3545;">{breach_pct:.1f}%</td></tr>
    </table>

    <h3>Action Required</h3>
    <ol>
        <li>Review position immediately</li>
        <li>Assess risk exposure</li>
        <li>Consider position reduction</li>
        <li>Update risk limits if necessary</li>
    </ol>

    <hr>
    <p style="color: #666; font-size: 12px;">Generated by Market Risk VaR System</p>
</body>
</html>
"""

        return self.send_email(to_emails, subject, body_text, body_html)

    def send_daily_summary(
        self,
        to_emails: List[str],
        ticker: str,
        var_results: Dict,
        backtest_results: Dict,
        metrics: Dict
    ) -> bool:
        """Send daily risk summary"""

        # Status icon
        kupiec_pass = backtest_results.get('kupiec_test', {}).get('pass_test', True)
        status_icon = "✅" if kupiec_pass else "❌"
        status = "PASS" if kupiec_pass else "FAIL"

        subject = f"📊 Daily Risk Report - {ticker} - {datetime.now().strftime('%Y-%m-%d')}"

        body_text = f"""
DAILY RISK SUMMARY

Ticker: {ticker}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {status_icon} {status}

VaR Summary:
  Position Value:    ${var_results.get('position_value', 0):,.2f}
  VaR (1-day):      ${var_results.get('VaR', 0):,.2f}
  VaR %:            {var_results.get('VaR_Percentage', 0):.3f}%
  CVaR:             ${var_results.get('CVaR', 0):,.2f}
  Method:           {var_results.get('method', 'N/A')}

Backtest Results:
  Observations:     {backtest_results.get('num_observations', 0)}
  Exceptions:       {backtest_results.get('num_exceptions', 0)}
  Exception Rate:   {backtest_results.get('exception_rate', 0)*100:.2f}%
  Kupiec p-value:   {backtest_results.get('kupiec_test', {}).get('p_value', 0):.4f}

Risk Metrics:
  Sharpe Ratio:     {metrics.get('sharpe_ratio', 0):.3f}
  Sortino Ratio:    {metrics.get('sortino_ratio', 0):.3f}
  Max Drawdown:     {metrics.get('max_drawdown', 0)*100:.2f}%
  Calmar Ratio:     {metrics.get('calmar_ratio', 0):.3f}

---
Generated by Market Risk VaR System
"""

        return self.send_email(to_emails, subject, body_text)

    def send_backtest_failure_alert(
        self,
        to_emails: List[str],
        ticker: str,
        backtest_results: Dict
    ) -> bool:
        """Send backtest failure alert"""

        kupiec = backtest_results.get('kupiec_test', {})

        subject = f"❌ VaR Model Failed - {ticker} - {datetime.now().strftime('%Y-%m-%d')}"

        body_text = f"""
BACKTEST FAILURE ALERT

Ticker: {ticker}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Kupiec Test FAILED:
  LR Statistic:     {kupiec.get('lr_statistic', 0):.4f}
  p-value:          {kupiec.get('p_value', 0):.4f} (< 0.05)
  Expected Rate:    {kupiec.get('expected_rate', 0)*100:.2f}%
  Observed Rate:    {kupiec.get('observed_rate', 0)*100:.2f}%

Exception Details:
  Total Observations: {backtest_results.get('num_observations', 0)}
  Exceptions:        {backtest_results.get('num_exceptions', 0)}
  Exception Rate:    {backtest_results.get('exception_rate', 0)*100:.2f}%

Recommended Actions:
  1. Review VaR model parameters
  2. Consider using different method (GARCH, Monte Carlo)
  3. Increase confidence level if appropriate
  4. Check for data quality issues
  5. Re-calibrate model with recent data

---
Generated by Market Risk VaR System
"""

        return self.send_email(to_emails, subject, body_text)
```

---

## 🧪 API Endpoint

Add to `src/api/main.py`:

```python
from pydantic import BaseModel, EmailStr
from typing import List

class EmailAlertRequest(BaseModel):
    ticker: str
    to_emails: List[EmailStr]
    alert_type: str = "daily_summary"  # daily_summary, breach, backtest_failure
    confidence_level: float = 0.95
    position_value: float = 1000000


@app.post("/api/v1/alerts/send")
async def send_alert(request: EmailAlertRequest):
    """Send email alert"""

    from alerts.email_alerts import EmailAlerter

    # Initialize alerter
    alerter = EmailAlerter()

    # Fetch data and calculate VaR
    data = data_collector.fetch_stock_data(request.ticker, period="2y")
    returns = preprocessor.prepare_returns_data(data)['Returns']

    var_calc = VaRCalculator(confidence_level=request.confidence_level)
    var_results = var_calc.historical_var(returns, request.position_value)

    # Backtest
    backtester = VaRBacktester(confidence_level=request.confidence_level)
    train_size = int(len(returns) * 0.7)
    test_returns = returns[train_size:]
    var_estimates = pd.Series([var_results['VaR']] * len(test_returns))

    backtest_results = backtester.backtest_var_model(
        test_returns, var_estimates, request.position_value
    )

    kupiec = backtester.kupiec_pof_test(
        backtest_results['num_observations'],
        backtest_results['num_exceptions']
    )
    backtest_results['kupiec_test'] = kupiec

    # Get metrics
    from utils.advanced_metrics import AdvancedMetrics
    advanced = AdvancedMetrics()
    metrics = advanced.calculate_all_metrics(returns)

    # Send appropriate alert
    success = False

    if request.alert_type == "daily_summary":
        success = alerter.send_daily_summary(
            request.to_emails,
            request.ticker,
            var_results,
            backtest_results,
            metrics
        )

    elif request.alert_type == "backtest_failure":
        if not kupiec.get('pass_test', True):
            success = alerter.send_backtest_failure_alert(
                request.to_emails,
                request.ticker,
                backtest_results
            )
        else:
            return {"message": "Backtest passed, no alert sent"}

    elif request.alert_type == "breach":
        # Simulate breach for testing
        actual_loss = var_results['VaR'] * 1.3  # 30% over VaR
        breach_amount = actual_loss - var_results['VaR']

        success = alerter.send_var_breach_alert(
            request.to_emails,
            request.ticker,
            var_results['VaR'],
            actual_loss,
            breach_amount,
            request.position_value
        )

    return {
        "success": success,
        "alert_type": request.alert_type,
        "ticker": request.ticker,
        "recipients": request.to_emails
    }
```

---

## 🧪 Test with curl

### Setup (Optional - for real emails):

```bash
# Set environment variables for Gmail
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT=587
export SMTP_USER="your_email@gmail.com"
export SMTP_PASSWORD="your_app_password"  # NOT your regular password!
export FROM_EMAIL="your_email@gmail.com"

# Note: For Gmail, you need to create an "App Password"
# Go to: Google Account > Security > 2-Step Verification > App passwords
```

### Test Daily Summary (Test Mode):

```bash
# Send daily summary (test mode - no real email)
curl -X POST "http://localhost:8000/api/v1/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "to_emails": ["user@example.com"],
    "alert_type": "daily_summary"
  }' | jq '.'
```

**Expected:**
```json
{
  "success": true,
  "alert_type": "daily_summary",
  "ticker": "AAPL",
  "recipients": ["user@example.com"]
}
```

**Check logs** to see the email content:
```
[TEST MODE] Would send email:
  To: ['user@example.com']
  Subject: 📊 Daily Risk Report - AAPL - 2024-01-15
  Body:
  DAILY RISK SUMMARY
  ...
```

### Test Breach Alert:

```bash
# Send breach alert
curl -X POST "http://localhost:8000/api/v1/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "to_emails": ["risk@example.com"],
    "alert_type": "breach"
  }' | jq '.'
```

### Test Backtest Failure:

```bash
# Send backtest failure alert (if model fails)
curl -X POST "http://localhost:8000/api/v1/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "TSLA",
    "to_emails": ["risk@example.com"],
    "alert_type": "backtest_failure"
  }' | jq '.'
```

### Test Multiple Recipients:

```bash
# Send to multiple email addresses
curl -X POST "http://localhost:8000/api/v1/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "to_emails": ["risk@example.com", "cfo@example.com", "trader@example.com"],
    "alert_type": "daily_summary"
  }' | jq '.recipients'
```

### Test Different Stocks:

```bash
# Send alerts for multiple stocks
for ticker in AAPL MSFT GOOGL; do
  echo "Sending alert for $ticker..."
  curl -s -X POST "http://localhost:8000/api/v1/alerts/send" \
    -H "Content-Type: application/json" \
    -d "{
      \"ticker\": \"$ticker\",
      \"to_emails\": [\"user@example.com\"],
      \"alert_type\": \"daily_summary\"
    }" | jq '{ticker, success}'
done
```

---

## 📧 Gmail Setup (Real Emails)

### Step 1: Enable 2-Factor Authentication

1. Go to Google Account settings
2. Security > 2-Step Verification
3. Enable 2FA

### Step 2: Create App Password

1. Security > App passwords
2. Select app: Mail
3. Select device: Other (Custom name)
4. Name it: "VaR System"
5. Click Generate
6. Copy the 16-character password

### Step 3: Use App Password

```bash
export SMTP_PASSWORD="abcd efgh ijkl mnop"  # Your app password (no spaces)
```

### Step 4: Test Real Email

```bash
# This will send a REAL email
curl -X POST "http://localhost:8000/api/v1/alerts/send" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "to_emails": ["your_real_email@gmail.com"],
    "alert_type": "daily_summary"
  }'

# Check your inbox!
```

---

## ✅ Completed

✅ Email alert system with SMTP
✅ VaR breach notifications
✅ Daily summary emails
✅ Backtest failure alerts
✅ HTML and text templates
✅ Test mode for development
✅ curl-based alert triggers

**Next**: Task Scheduling (Day 020)
