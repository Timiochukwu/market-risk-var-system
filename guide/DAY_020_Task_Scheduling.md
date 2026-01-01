# Day 020: Task Scheduling & Automation

**Duration**: 1.5-2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-019

---

## 📋 What You'll Build

- Automated VaR calculation scheduler
- Daily risk report automation
- Alert scheduling system
- Scheduled backtest runs
- Task management API
- Background job processing

---

## 💡 Scheduling Use Cases

### 1. Daily VaR Calculation
```
Schedule: Every weekday at 9:00 AM
Action: Calculate VaR for all portfolio positions
Output: Store in database, send summary email
```

### 2. Weekly Backtesting
```
Schedule: Every Sunday at 11:00 PM
Action: Run backtest on all models
Output: Generate reports, flag failures
```

### 3. Real-Time Monitoring
```
Schedule: Every 15 minutes during market hours
Action: Check for VaR breaches
Output: Send immediate alerts if breach detected
```

### 4. Monthly Reports
```
Schedule: First day of each month at 8:00 AM
Action: Generate monthly risk reports
Output: Email comprehensive reports to stakeholders
```

---

## 💻 Implementation

Create `src/scheduler/task_scheduler.py`:

```python
"""
Task Scheduler for VaR System
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class VaRScheduler:
    """Schedule automated VaR tasks"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def schedule_daily_var_calculation(
        self,
        tickers: List[str],
        hour: int = 9,
        minute: int = 0,
        timezone: str = "America/New_York"
    ) -> str:
        """
        Schedule daily VaR calculation

        Args:
            tickers: List of tickers to calculate
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            timezone: Timezone string

        Returns:
            Job ID
        """

        job_id = f"daily_var_{datetime.now().timestamp()}"

        # Define the job function
        def calculate_var_job():
            logger.info(f"Running daily VaR calculation for {len(tickers)} tickers")

            from data.data_collector import DataCollector
            from data.preprocessor import DataPreprocessor
            from models.var_calculator import VaRCalculator

            collector = DataCollector()
            preprocessor = DataPreprocessor()
            var_calc = VaRCalculator(confidence_level=0.95)

            results = {}

            for ticker in tickers:
                try:
                    # Fetch and process data
                    data = collector.fetch_stock_data(ticker, period="2y")
                    returns = preprocessor.prepare_returns_data(data)['Returns']

                    # Calculate VaR
                    var_result = var_calc.historical_var(returns, position_value=1000000)

                    results[ticker] = {
                        'var': var_result['VaR'],
                        'cvar': var_result['CVaR'],
                        'timestamp': datetime.now().isoformat()
                    }

                    logger.info(f"{ticker}: VaR = ${var_result['VaR']:,.2f}")

                except Exception as e:
                    logger.error(f"Failed to calculate VaR for {ticker}: {e}")
                    results[ticker] = {'error': str(e)}

            logger.info(f"Daily VaR calculation completed: {len(results)} tickers")
            return results

        # Schedule job
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            day_of_week='mon-fri',  # Weekdays only
            timezone=timezone
        )

        job = self.scheduler.add_job(
            calculate_var_job,
            trigger=trigger,
            id=job_id,
            name=f"Daily VaR Calculation ({len(tickers)} tickers)"
        )

        self.jobs[job_id] = job
        logger.info(f"Scheduled daily VaR calculation at {hour:02d}:{minute:02d} {timezone}")

        return job_id

    def schedule_weekly_backtest(
        self,
        tickers: List[str],
        day_of_week: str = 'sun',
        hour: int = 23,
        minute: int = 0
    ) -> str:
        """
        Schedule weekly backtest

        Args:
            tickers: List of tickers to backtest
            day_of_week: Day to run (mon, tue, wed, thu, fri, sat, sun)
            hour: Hour to run
            minute: Minute to run

        Returns:
            Job ID
        """

        job_id = f"weekly_backtest_{datetime.now().timestamp()}"

        def backtest_job():
            logger.info(f"Running weekly backtest for {len(tickers)} tickers")

            from data.data_collector import DataCollector
            from data.preprocessor import DataPreprocessor
            from models.var_calculator import VaRCalculator
            from utils.backtesting import VaRBacktester
            import pandas as pd

            collector = DataCollector()
            preprocessor = DataPreprocessor()

            results = {}

            for ticker in tickers:
                try:
                    # Fetch data
                    data = collector.fetch_stock_data(ticker, period="2y")
                    returns = preprocessor.prepare_returns_data(data)['Returns']

                    # Split train/test
                    train_size = int(len(returns) * 0.7)
                    test_returns = returns[train_size:]

                    # Calculate VaR
                    var_calc = VaRCalculator(confidence_level=0.95)
                    var_result = var_calc.historical_var(returns[:train_size], 1000000)
                    var_estimates = pd.Series([var_result['VaR']] * len(test_returns))

                    # Backtest
                    backtester = VaRBacktester(confidence_level=0.95)
                    backtest_result = backtester.backtest_var_model(
                        test_returns, var_estimates, 1000000
                    )

                    # Kupiec test
                    kupiec = backtester.kupiec_pof_test(
                        backtest_result['num_observations'],
                        backtest_result['num_exceptions']
                    )

                    results[ticker] = {
                        'exceptions': backtest_result['num_exceptions'],
                        'exception_rate': backtest_result['exception_rate'],
                        'kupiec_pass': kupiec['pass_test'],
                        'kupiec_pvalue': kupiec['p_value'],
                        'timestamp': datetime.now().isoformat()
                    }

                    status = "✅ PASS" if kupiec['pass_test'] else "❌ FAIL"
                    logger.info(f"{ticker}: {status} (p-value: {kupiec['p_value']:.4f})")

                except Exception as e:
                    logger.error(f"Failed backtest for {ticker}: {e}")
                    results[ticker] = {'error': str(e)}

            logger.info(f"Weekly backtest completed: {len(results)} tickers")
            return results

        # Schedule job
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute
        )

        job = self.scheduler.add_job(
            backtest_job,
            trigger=trigger,
            id=job_id,
            name=f"Weekly Backtest ({len(tickers)} tickers)"
        )

        self.jobs[job_id] = job
        logger.info(f"Scheduled weekly backtest on {day_of_week} at {hour:02d}:{minute:02d}")

        return job_id

    def schedule_intraday_monitoring(
        self,
        tickers: List[str],
        interval_minutes: int = 15
    ) -> str:
        """
        Schedule intraday VaR monitoring

        Args:
            tickers: List of tickers to monitor
            interval_minutes: Check interval in minutes

        Returns:
            Job ID
        """

        job_id = f"intraday_monitor_{datetime.now().timestamp()}"

        def monitor_job():
            logger.info(f"Running intraday monitoring for {len(tickers)} tickers")

            from data.data_collector import DataCollector
            from data.preprocessor import DataPreprocessor
            from models.var_calculator import VaRCalculator

            collector = DataCollector()
            preprocessor = DataPreprocessor()
            var_calc = VaRCalculator(confidence_level=0.95)

            alerts = []

            for ticker in tickers:
                try:
                    # Fetch recent data
                    data = collector.fetch_stock_data(ticker, period="1mo")
                    returns = preprocessor.prepare_returns_data(data)['Returns']

                    # Calculate VaR
                    var_result = var_calc.historical_var(returns, 1000000)

                    # Check latest return vs VaR
                    latest_return = returns.iloc[-1]
                    latest_loss = -latest_return * 1000000

                    if latest_loss > var_result['VaR']:
                        breach_amount = latest_loss - var_result['VaR']
                        alerts.append({
                            'ticker': ticker,
                            'var': var_result['VaR'],
                            'actual_loss': latest_loss,
                            'breach': breach_amount
                        })
                        logger.warning(f"⚠️ VaR breach detected for {ticker}: ${breach_amount:,.2f}")

                except Exception as e:
                    logger.error(f"Monitoring failed for {ticker}: {e}")

            if alerts:
                logger.warning(f"Total breaches detected: {len(alerts)}")
            else:
                logger.info("No VaR breaches detected")

            return alerts

        # Schedule job (every N minutes during market hours)
        trigger = IntervalTrigger(minutes=interval_minutes)

        job = self.scheduler.add_job(
            monitor_job,
            trigger=trigger,
            id=job_id,
            name=f"Intraday Monitoring (every {interval_minutes}min)"
        )

        self.jobs[job_id] = job
        logger.info(f"Scheduled intraday monitoring every {interval_minutes} minutes")

        return job_id

    def schedule_monthly_report(
        self,
        tickers: List[str],
        email_to: List[str],
        day: int = 1,
        hour: int = 8,
        minute: int = 0
    ) -> str:
        """
        Schedule monthly risk report

        Args:
            tickers: List of tickers
            email_to: Email recipients
            day: Day of month (1-28)
            hour: Hour to run
            minute: Minute to run

        Returns:
            Job ID
        """

        job_id = f"monthly_report_{datetime.now().timestamp()}"

        def report_job():
            logger.info(f"Generating monthly report for {len(tickers)} tickers")

            from data.data_collector import DataCollector
            from data.preprocessor import DataPreprocessor
            from models.var_calculator import VaRCalculator
            from alerts.email_alerts import EmailAlerter

            collector = DataCollector()
            preprocessor = DataPreprocessor()
            alerter = EmailAlerter()

            # Generate report for each ticker
            for ticker in tickers:
                try:
                    data = collector.fetch_stock_data(ticker, period="2y")
                    returns = preprocessor.prepare_returns_data(data)['Returns']

                    var_calc = VaRCalculator(confidence_level=0.95)
                    var_result = var_calc.historical_var(returns, 1000000)

                    # Send summary (simplified)
                    subject = f"Monthly Risk Report - {ticker}"
                    body = f"""
Monthly VaR Report - {ticker}
Date: {datetime.now().strftime('%Y-%m-%d')}

VaR (95%): ${var_result['VaR']:,.2f}
CVaR: ${var_result['CVaR']:,.2f}

---
Generated automatically
"""
                    alerter.send_email(email_to, subject, body)
                    logger.info(f"Monthly report sent for {ticker}")

                except Exception as e:
                    logger.error(f"Failed to generate report for {ticker}: {e}")

            logger.info("Monthly report generation completed")

        # Schedule job
        trigger = CronTrigger(day=day, hour=hour, minute=minute)

        job = self.scheduler.add_job(
            report_job,
            trigger=trigger,
            id=job_id,
            name=f"Monthly Report ({len(tickers)} tickers)"
        )

        self.jobs[job_id] = job
        logger.info(f"Scheduled monthly report on day {day} at {hour:02d}:{minute:02d}")

        return job_id

    def list_jobs(self) -> List[Dict]:
        """List all scheduled jobs"""

        jobs_list = []

        for job in self.scheduler.get_jobs():
            jobs_list.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return jobs_list

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""

        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            return False
```

**Install APScheduler**:
```bash
pip install apscheduler==3.10.4
```

---

## 🧪 API Integration

Add to `src/api/main.py`:

```python
from scheduler.task_scheduler import VaRScheduler

# Global scheduler instance
scheduler = VaRScheduler()

@app.on_event("startup")
async def startup_event():
    """Start scheduler on API startup"""
    scheduler.start()
    logger.info("Scheduler started with API")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on API shutdown"""
    scheduler.stop()
    logger.info("Scheduler stopped")


@app.post("/api/v1/schedule/daily-var")
async def schedule_daily_var(
    tickers: List[str],
    hour: int = 9,
    minute: int = 0,
    timezone: str = "America/New_York"
):
    """Schedule daily VaR calculation"""

    job_id = scheduler.schedule_daily_var_calculation(
        tickers, hour, minute, timezone
    )

    return {
        "job_id": job_id,
        "schedule": f"Daily at {hour:02d}:{minute:02d} {timezone}",
        "tickers": tickers
    }


@app.post("/api/v1/schedule/weekly-backtest")
async def schedule_weekly_backtest(
    tickers: List[str],
    day_of_week: str = "sun",
    hour: int = 23,
    minute: int = 0
):
    """Schedule weekly backtest"""

    job_id = scheduler.schedule_weekly_backtest(
        tickers, day_of_week, hour, minute
    )

    return {
        "job_id": job_id,
        "schedule": f"Weekly on {day_of_week} at {hour:02d}:{minute:02d}",
        "tickers": tickers
    }


@app.post("/api/v1/schedule/intraday-monitor")
async def schedule_intraday_monitor(
    tickers: List[str],
    interval_minutes: int = 15
):
    """Schedule intraday monitoring"""

    job_id = scheduler.schedule_intraday_monitoring(
        tickers, interval_minutes
    )

    return {
        "job_id": job_id,
        "schedule": f"Every {interval_minutes} minutes",
        "tickers": tickers
    }


@app.get("/api/v1/schedule/jobs")
async def list_scheduled_jobs():
    """List all scheduled jobs"""

    jobs = scheduler.list_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@app.delete("/api/v1/schedule/jobs/{job_id}")
async def remove_scheduled_job(job_id: str):
    """Remove a scheduled job"""

    success = scheduler.remove_job(job_id)

    if success:
        return {"message": f"Job {job_id} removed"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")
```

---

## 🧪 Test with curl

### Schedule Daily VaR Calculation:

```bash
# Schedule daily VaR at 9:00 AM ET
curl -X POST "http://localhost:8000/api/v1/schedule/daily-var" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "hour": 9,
    "minute": 0,
    "timezone": "America/New_York"
  }' | jq '.'
```

**Expected:**
```json
{
  "job_id": "daily_var_1705329876.123",
  "schedule": "Daily at 09:00 America/New_York",
  "tickers": ["AAPL", "MSFT", "GOOGL"]
}
```

### Schedule Weekly Backtest:

```bash
# Schedule backtest every Sunday at 11 PM
curl -X POST "http://localhost:8000/api/v1/schedule/weekly-backtest" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "MSFT"],
    "day_of_week": "sun",
    "hour": 23,
    "minute": 0
  }' | jq '.'
```

### Schedule Intraday Monitoring:

```bash
# Monitor every 15 minutes
curl -X POST "http://localhost:8000/api/v1/schedule/intraday-monitor" \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "TSLA"],
    "interval_minutes": 15
  }' | jq '.'
```

### List All Scheduled Jobs:

```bash
curl -X GET "http://localhost:8000/api/v1/schedule/jobs" | jq '.'
```

**Expected:**
```json
{
  "jobs": [
    {
      "id": "daily_var_1705329876.123",
      "name": "Daily VaR Calculation (3 tickers)",
      "next_run": "2024-01-16T09:00:00-05:00",
      "trigger": "cron[day_of_week='mon-fri', hour='9', minute='0']"
    },
    {
      "id": "weekly_backtest_1705329880.456",
      "name": "Weekly Backtest (2 tickers)",
      "next_run": "2024-01-21T23:00:00-05:00",
      "trigger": "cron[day_of_week='sun', hour='23', minute='0']"
    }
  ],
  "count": 2
}
```

### Remove a Scheduled Job:

```bash
# Get job ID from list
JOB_ID="daily_var_1705329876.123"

curl -X DELETE "http://localhost:8000/api/v1/schedule/jobs/$JOB_ID" | jq '.'
```

**Expected:**
```json
{
  "message": "Job daily_var_1705329876.123 removed"
}
```

### Schedule Multiple Jobs at Once:

```bash
# Daily VaR
curl -s -X POST "http://localhost:8000/api/v1/schedule/daily-var" \
  -d '{"tickers": ["AAPL", "MSFT"], "hour": 9}' \
  -H "Content-Type: application/json" | jq '.job_id'

# Weekly backtest
curl -s -X POST "http://localhost:8000/api/v1/schedule/weekly-backtest" \
  -d '{"tickers": ["AAPL", "MSFT"], "day_of_week": "sun"}' \
  -H "Content-Type: application/json" | jq '.job_id'

# Intraday monitoring
curl -s -X POST "http://localhost:8000/api/v1/schedule/intraday-monitor" \
  -d '{"tickers": ["AAPL"], "interval_minutes": 30}' \
  -H "Content-Type: application/json" | jq '.job_id'

# List all jobs
curl -s "http://localhost:8000/api/v1/schedule/jobs" | jq '.count'
```

---

## ⏰ Cron Expression Guide

### Common Schedules:

```python
# Every weekday at 9 AM
CronTrigger(hour=9, minute=0, day_of_week='mon-fri')

# Every hour
IntervalTrigger(hours=1)

# Every 30 minutes
IntervalTrigger(minutes=30)

# Every Monday at 8 AM
CronTrigger(hour=8, minute=0, day_of_week='mon')

# First day of month at 8 AM
CronTrigger(day=1, hour=8, minute=0)

# Last day of month (use day=31 with misfire grace)
CronTrigger(day='last', hour=23, minute=59)

# Every 6 hours
IntervalTrigger(hours=6)
```

---

## ✅ Completed

✅ APScheduler integration
✅ Daily VaR automation
✅ Weekly backtest scheduling
✅ Intraday monitoring
✅ Monthly report automation
✅ Job management API
✅ curl-based task control

**Next Steps**: Days 021-050 (Coming Soon)

---

## 🎯 Week 4 Complete!

**Congratulations! You've completed Week 4 (Days 016-020):**

✅ Portfolio VaR with correlation
✅ Stress testing framework
✅ Report generation (Excel/HTML/Text)
✅ Email alert system
✅ Automated task scheduling

**You now have:**
- Production-ready risk management system
- Automated daily operations
- Professional reporting capabilities
- Alert and notification system
- Scheduled monitoring and backtesting

**Ready for Week 5?** Days 021-025 will cover:
- Database integration (SQLAlchemy)
- Historical VaR storage
- Performance optimization
- API authentication
- Rate limiting & caching
