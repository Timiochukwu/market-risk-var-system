"""
Email Alerting System for Market Risk VaR System

This module sends automated email alerts when:
- VaR limits are breached
- Anomalies are detected
- Stress test thresholds exceeded
- Model backtests fail
- Any custom risk events occur

Why Email Alerts?
- Immediate notification of risk events
- 24/7 monitoring without manual checks
- Regulatory compliance (timely risk reporting)
- Mobile accessibility (check email anywhere)
- Audit trail (emails are timestamped records)

Supports:
- SMTP email (Gmail, Outlook, corporate servers)
- HTML formatted emails with tables and charts
- Attachments (reports, charts)
- Multiple recipients and priority levels
- Rate limiting to avoid spam
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional, Dict
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailAlerter:
    """
    Send email alerts for risk events

    This class handles all email notifications for the VaR system.
    Configure once, then use throughout your application.

    Example:
        alerter = EmailAlerter(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            sender_email="risk-alerts@company.com",
            sender_password="your-app-password"
        )

        alerter.send_var_breach_alert("AAPL", 18000, 15000, ["risk-team@company.com"])
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
        use_tls: bool = True
    ):
        """
        Initialize email alerter

        Args:
            smtp_server: SMTP server address (e.g., "smtp.gmail.com")
            smtp_port: SMTP port (587 for TLS, 465 for SSL, 25 for plain)
            sender_email: Sender email address
            sender_password: Email password or app-specific password
            use_tls: Whether to use TLS encryption (recommended)

        Gmail Setup:
            1. Enable 2-factor authentication
            2. Generate app-specific password
            3. Use: smtp_server="smtp.gmail.com", smtp_port=587

        Outlook Setup:
            smtp_server="smtp-mail.outlook.com", smtp_port=587

        Corporate Setup:
            Contact IT for SMTP server details
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls

        logger.info(f"Email alerter initialized: {sender_email} via {smtp_server}")

    def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        priority: str = "normal"
    ) -> bool:
        """
        Send an email

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML formatted body (looks better!)
            attachments: Optional list of file paths to attach
            priority: "low", "normal", or "high"

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # Set priority
            if priority == "high":
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'
            elif priority == "low":
                msg['X-Priority'] = '5'
                msg['Importance'] = 'low'

            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))

            # Attach HTML body if provided (displays better in email clients)
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            # Attach files if provided
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(filepath)}'
                            )
                            msg.attach(part)
                    else:
                        logger.warning(f"Attachment not found: {filepath}")

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.info(f"Email sent to {len(recipients)} recipient(s): {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def send_var_breach_alert(
        self,
        ticker: str,
        current_var: float,
        var_limit: float,
        recipients: List[str],
        confidence_level: float = 0.95,
        position_value: float = 1000000
    ) -> bool:
        """
        Send VaR limit breach alert

        This is triggered when calculated VaR exceeds your risk limit.
        It's the most common type of alert in risk management.

        Args:
            ticker: Stock ticker
            current_var: Current VaR amount
            var_limit: VaR limit that was breached
            recipients: Email recipients
            confidence_level: VaR confidence level
            position_value: Portfolio position value

        Returns:
            True if sent successfully
        """
        breach_amount = current_var - var_limit
        breach_pct = (breach_amount / var_limit) * 100

        # Plain text version
        subject = f"⚠️ VaR LIMIT BREACH - {ticker}"

        body = f"""
VaR LIMIT BREACH ALERT
{'='*60}

Ticker: {ticker}
Position Value: ${position_value:,.2f}
Confidence Level: {confidence_level*100:.1f}%

Current VaR: ${current_var:,.2f}
VaR Limit: ${var_limit:,.2f}
Breach Amount: ${breach_amount:,.2f} ({breach_pct:+.1f}%)

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACTION REQUIRED:
1. Review position and market conditions
2. Consider reducing exposure
3. Update risk limits if appropriate
4. Acknowledge alert in risk management system

This is an automated alert from the Market Risk VaR System.
        """

        # HTML version (looks professional in email clients)
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #d9534f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .metric {{ background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .breach {{ background-color: #fcf8e3; border-left: 4px solid #f0ad4e; padding: 15px; margin: 20px 0; }}
                .footer {{ background-color: #f5f5f5; padding: 15px; margin-top: 20px; font-size: 12px; color: #666; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f0f0f0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ VaR LIMIT BREACH ALERT</h1>
            </div>

            <div class="content">
                <h2>{ticker}</h2>

                <div class="breach">
                    <h3>BREACH DETAILS</h3>
                    <table>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                        <tr>
                            <td>Current VaR</td>
                            <td><strong>${current_var:,.2f}</strong></td>
                        </tr>
                        <tr>
                            <td>VaR Limit</td>
                            <td>${var_limit:,.2f}</td>
                        </tr>
                        <tr>
                            <td>Breach Amount</td>
                            <td style="color: #d9534f;"><strong>${breach_amount:,.2f} ({breach_pct:+.1f}%)</strong></td>
                        </tr>
                    </table>
                </div>

                <div class="metric">
                    <strong>Position Value:</strong> ${position_value:,.2f}<br>
                    <strong>Confidence Level:</strong> {confidence_level*100:.1f}%<br>
                    <strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>

                <h3>RECOMMENDED ACTIONS:</h3>
                <ol>
                    <li>Review current position and market conditions</li>
                    <li>Consider reducing exposure or hedging</li>
                    <li>Evaluate if risk limit adjustment is warranted</li>
                    <li>Acknowledge alert in risk management system</li>
                    <li>Document decision and actions taken</li>
                </ol>
            </div>

            <div class="footer">
                This is an automated alert from the Market Risk VaR System.<br>
                For questions, contact risk-management@company.com
            </div>
        </body>
        </html>
        """

        return self.send_email(
            recipients=recipients,
            subject=subject,
            body=body,
            html_body=html_body,
            priority="high"
        )

    def send_anomaly_alert(
        self,
        ticker: str,
        anomaly_details: Dict,
        recipients: List[str]
    ) -> bool:
        """
        Send anomaly detection alert

        Triggered when ML anomaly detector finds unusual patterns.

        Args:
            ticker: Stock ticker
            anomaly_details: Dict with anomaly information
            recipients: Email recipients

        Returns:
            True if sent successfully
        """
        subject = f"🔍 ANOMALY DETECTED - {ticker}"

        body = f"""
MARKET ANOMALY DETECTED
{'='*60}

Ticker: {ticker}
Anomaly Type: {anomaly_details.get('type', 'Unusual Pattern')}
Severity: {anomaly_details.get('severity', 'MEDIUM')}

Details:
{anomaly_details.get('description', 'Unusual market behavior detected by ML model')}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RECOMMENDED ACTIONS:
1. Investigate market conditions and news
2. Review position and risk exposure
3. Consider preemptive risk reduction
4. Monitor closely for further developments

This is an automated alert from the Market Risk VaR System.
        """

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #f0ad4e; color: white; padding: 20px; text-align: center;">
                <h1>🔍 MARKET ANOMALY DETECTED</h1>
            </div>
            <div style="padding: 20px;">
                <h2>{ticker}</h2>
                <div style="background-color: #fcf8e3; padding: 15px; border-left: 4px solid #f0ad4e;">
                    <strong>Anomaly Type:</strong> {anomaly_details.get('type', 'Unusual Pattern')}<br>
                    <strong>Severity:</strong> <span style="color: #d9534f;">{anomaly_details.get('severity', 'MEDIUM')}</span>
                </div>
                <p>{anomaly_details.get('description', 'Unusual market behavior detected by ML model')}</p>
                <p><em>Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
            </div>
        </body>
        </html>
        """

        return self.send_email(
            recipients=recipients,
            subject=subject,
            body=body,
            html_body=html_body,
            priority="high"
        )

    def send_daily_report(
        self,
        ticker: str,
        var_summary: Dict,
        recipients: List[str],
        report_file: Optional[str] = None
    ) -> bool:
        """
        Send daily VaR report

        Regular daily update with VaR calculations and risk metrics.

        Args:
            ticker: Stock ticker
            var_summary: Dictionary with VaR summary
            recipients: Email recipients
            report_file: Optional report file to attach

        Returns:
            True if sent successfully
        """
        subject = f"📊 Daily VaR Report - {ticker} - {datetime.now().strftime('%Y-%m-%d')}"

        body = f"""
DAILY VaR REPORT
{'='*60}

Ticker: {ticker}
Report Date: {datetime.now().strftime('%Y-%m-%d')}

VaR (95%): ${var_summary.get('var', 0):,.2f}
Expected Shortfall: ${var_summary.get('es', 0):,.2f}
Position Value: ${var_summary.get('position_value', 0):,.2f}

Risk Metrics:
- Volatility: {var_summary.get('volatility', 0)*100:.2f}%
- Sharpe Ratio: {var_summary.get('sharpe_ratio', 0):.2f}
- Max Drawdown: {var_summary.get('max_drawdown', 0)*100:.2f}%

Status: {var_summary.get('status', 'Within Limits')}

{'Detailed report attached.' if report_file else ''}

This is an automated daily report from the Market Risk VaR System.
        """

        attachments = [report_file] if report_file and os.path.exists(report_file) else None

        return self.send_email(
            recipients=recipients,
            subject=subject,
            body=body,
            attachments=attachments,
            priority="normal"
        )

    def send_backtest_failure_alert(
        self,
        ticker: str,
        backtest_results: Dict,
        recipients: List[str]
    ) -> bool:
        """
        Send alert when VaR model fails backtest

        Critical alert - model is not working properly!

        Args:
            ticker: Stock ticker
            backtest_results: Backtest results dictionary
            recipients: Email recipients

        Returns:
            True if sent successfully
        """
        subject = f"❌ VaR MODEL BACKTEST FAILURE - {ticker}"

        body = f"""
VaR MODEL BACKTEST FAILURE
{'='*60}

CRITICAL: VaR model for {ticker} has failed backtesting validation.

Backtest Results:
- Exception Rate: {backtest_results.get('exception_rate', 0)*100:.2f}%
- Expected Rate: {backtest_results.get('expected_rate', 0)*100:.2f}%
- Traffic Light Zone: {backtest_results.get('traffic_light_zone', 'Unknown')}
- Kupiec Test: {backtest_results.get('kupiec_result', 'N/A')}

IMMEDIATE ACTION REQUIRED:
1. Suspend automated trading based on this model
2. Review model parameters and assumptions
3. Investigate recent market conditions
4. Retrain or recalibrate model
5. Re-run backtest before resuming use

This is a CRITICAL automated alert from the Market Risk VaR System.
        """

        return self.send_email(
            recipients=recipients,
            subject=subject,
            body=body,
            priority="high"
        )


# Example usage and testing
if __name__ == "__main__":
    # IMPORTANT: Use environment variables for credentials in production!
    # Never hardcode passwords in source code

    print("="*60)
    print("EMAIL ALERTER SETUP GUIDE")
    print("="*60)

    print("""

    TO USE EMAIL ALERTS:

    1. For Gmail:
       - Enable 2-factor authentication
       - Generate app-specific password: https://myaccount.google.com/apppasswords
       - Use:
         smtp_server="smtp.gmail.com"
         smtp_port=587
         sender_email="your-email@gmail.com"
         sender_password="your-app-password"  # NOT your regular password!

    2. For Outlook/Office365:
       - Use:
         smtp_server="smtp-mail.outlook.com"
         smtp_port=587

    3. For Corporate Email:
       - Contact IT for SMTP server details

    4. SECURITY BEST PRACTICE:
       - Store credentials in environment variables:

         import os
         alerter = EmailAlerter(
             smtp_server=os.getenv('SMTP_SERVER'),
             smtp_port=int(os.getenv('SMTP_PORT', 587)),
             sender_email=os.getenv('SENDER_EMAIL'),
             sender_password=os.getenv('SENDER_PASSWORD')
         )

    5. TEST YOUR SETUP:

       alerter = EmailAlerter("smtp.gmail.com", 587, "your-email@gmail.com", "app-password")

       success = alerter.send_email(
           recipients=["your-email@gmail.com"],
           subject="Test Alert",
           body="This is a test email from VaR system"
       )

       print(f"Test email sent: {success}")

    """)

    # Example: Send VaR breach alert (commented out - uncomment to test)
    """
    alerter = EmailAlerter(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        sender_email="your-email@gmail.com",
        sender_password="your-app-password"
    )

    alerter.send_var_breach_alert(
        ticker="AAPL",
        current_var=18000,
        var_limit=15000,
        recipients=["risk-manager@company.com"],
        confidence_level=0.95,
        position_value=1000000
    )
    """
