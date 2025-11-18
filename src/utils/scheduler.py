"""
Task Scheduler for Market Risk VaR System

This module automates recurring risk management tasks:
- Daily VaR calculations
- Weekly model retraining
- Monthly backtesting
- Hourly anomaly checks
- End-of-day reporting

Why Automation?
- Consistency (never forget a calculation)
- Timeliness (reports generated on schedule)
- Efficiency (frees up analyst time)
- Compliance (regulatory reporting deadlines)
- 24/7 monitoring (works while you sleep!)

Supports two scheduling approaches:
1. Simple schedule - Easy to use, good for basic tasks
2. APScheduler - Advanced, production-grade scheduling
"""

import schedule
import time
from datetime import datetime, timedelta
from typing import Callable, List, Optional, Dict
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleScheduler:
    """
    Simple task scheduler using the 'schedule' library

    Great for straightforward scheduling needs:
    - Daily reports at specific time
    - Weekly model updates
    - Hourly checks

    Example:
        scheduler = SimpleScheduler()

        # Daily VaR calculation at 9 AM
        scheduler.add_daily_task(calculate_var, "09:00", name="Daily VaR")

        # Run every 5 minutes
        scheduler.add_interval_task(check_alerts, minutes=5, name="Alert Check")

        # Start scheduler
        scheduler.run()
    """

    def __init__(self):
        """Initialize simple scheduler"""
        self.jobs = []
        self.running = False

    def add_daily_task(
        self,
        func: Callable,
        time_str: str,
        name: Optional[str] = None,
        **kwargs
    ):
        """
        Schedule a task to run daily at specific time

        Args:
            func: Function to execute
            time_str: Time in "HH:MM" format (24-hour)
            name: Optional task name for logging
            **kwargs: Arguments to pass to function

        Example:
            def morning_var_calc():
                print("Calculating morning VaR...")

            scheduler.add_daily_task(morning_var_calc, "09:00", name="Morning VaR")
        """
        job = schedule.every().day.at(time_str).do(func, **kwargs)

        self.jobs.append({
            'job': job,
            'name': name or func.__name__,
            'schedule': f"Daily at {time_str}"
        })

        logger.info(f"Scheduled daily task '{name or func.__name__}' at {time_str}")

    def add_interval_task(
        self,
        func: Callable,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs
    ):
        """
        Schedule a task to run at regular intervals

        Args:
            func: Function to execute
            minutes: Run every N minutes
            hours: Run every N hours
            name: Optional task name
            **kwargs: Arguments to pass to function

        Example:
            def check_var_limits():
                print("Checking VaR limits...")

            # Run every 15 minutes
            scheduler.add_interval_task(check_var_limits, minutes=15)

            # Run every 6 hours
            scheduler.add_interval_task(retrain_models, hours=6)
        """
        if minutes:
            job = schedule.every(minutes).minutes.do(func, **kwargs)
            schedule_str = f"Every {minutes} minute(s)"
        elif hours:
            job = schedule.every(hours).hours.do(func, **kwargs)
            schedule_str = f"Every {hours} hour(s)"
        else:
            raise ValueError("Must specify either minutes or hours")

        self.jobs.append({
            'job': job,
            'name': name or func.__name__,
            'schedule': schedule_str
        })

        logger.info(f"Scheduled interval task '{name or func.__name__}': {schedule_str}")

    def add_weekly_task(
        self,
        func: Callable,
        day: str,
        time_str: str,
        name: Optional[str] = None,
        **kwargs
    ):
        """
        Schedule a task to run weekly on specific day

        Args:
            func: Function to execute
            day: Day of week (monday, tuesday, etc.)
            time_str: Time in "HH:MM" format
            name: Optional task name
            **kwargs: Arguments to pass to function

        Example:
            def weekly_backtest():
                print("Running weekly backtest...")

            scheduler.add_weekly_task(
                weekly_backtest,
                day="friday",
                time_str="17:00",
                name="Weekly Backtest"
            )
        """
        day_lower = day.lower()

        if day_lower == "monday":
            job = schedule.every().monday.at(time_str).do(func, **kwargs)
        elif day_lower == "tuesday":
            job = schedule.every().tuesday.at(time_str).do(func, **kwargs)
        elif day_lower == "wednesday":
            job = schedule.every().wednesday.at(time_str).do(func, **kwargs)
        elif day_lower == "thursday":
            job = schedule.every().thursday.at(time_str).do(func, **kwargs)
        elif day_lower == "friday":
            job = schedule.every().friday.at(time_str).do(func, **kwargs)
        elif day_lower == "saturday":
            job = schedule.every().saturday.at(time_str).do(func, **kwargs)
        elif day_lower == "sunday":
            job = schedule.every().sunday.at(time_str).do(func, **kwargs)
        else:
            raise ValueError(f"Invalid day: {day}")

        self.jobs.append({
            'job': job,
            'name': name or func.__name__,
            'schedule': f"Weekly on {day.capitalize()} at {time_str}"
        })

        logger.info(f"Scheduled weekly task '{name or func.__name__}' on {day} at {time_str}")

    def list_jobs(self):
        """Print all scheduled jobs"""
        print("\n" + "="*60)
        print("SCHEDULED JOBS")
        print("="*60)

        if not self.jobs:
            print("No jobs scheduled")
        else:
            for i, job_info in enumerate(self.jobs, 1):
                print(f"{i}. {job_info['name']}")
                print(f"   Schedule: {job_info['schedule']}")
                print(f"   Next run: {job_info['job'].next_run}")
                print()

    def run(self, run_pending_on_start: bool = False):
        """
        Start the scheduler (runs forever)

        Args:
            run_pending_on_start: Run all pending jobs immediately before starting loop

        Note:
            This blocks! Run in background thread if needed, or use Ctrl+C to stop.
        """
        logger.info("Starting scheduler...")
        self.list_jobs()

        if run_pending_on_start:
            schedule.run_all()

        self.running = True

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)  # Check every second
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self.running = False


# Pre-configured scheduler for common VaR system tasks
class VaRSystemScheduler(SimpleScheduler):
    """
    Pre-configured scheduler with common VaR system tasks

    This extends SimpleScheduler with VaR-specific task templates.
    Just provide your functions and desired schedule!

    Example:
        scheduler = VaRSystemScheduler()

        # Add your calculation functions
        scheduler.setup_daily_var_calc(
            tickers=["AAPL", "MSFT", "GOOGL"],
            calculation_time="09:00"
        )

        scheduler.setup_weekly_model_retrain(
            day="saturday",
            time="02:00"
        )

        scheduler.run()
    """

    def setup_daily_var_calc(
        self,
        calc_function: Callable,
        tickers: List[str],
        calculation_time: str = "09:00"
    ):
        """
        Setup daily VaR calculations for multiple tickers

        Args:
            calc_function: Your VaR calculation function
                          Should accept (ticker, date) as arguments
            tickers: List of tickers to calculate
            calculation_time: Time to run (default 9 AM)

        Example:
            def my_var_calc(ticker, date):
                # Your calculation logic
                print(f"Calculating VaR for {ticker} on {date}")

            scheduler.setup_daily_var_calc(
                calc_function=my_var_calc,
                tickers=["AAPL", "MSFT"],
                calculation_time="09:00"
            )
        """
        def daily_wrapper():
            date = datetime.now().strftime('%Y-%m-%d')
            for ticker in tickers:
                try:
                    calc_function(ticker, date)
                    logger.info(f"Completed VaR calc for {ticker}")
                except Exception as e:
                    logger.error(f"Error calculating VaR for {ticker}: {str(e)}")

        self.add_daily_task(
            daily_wrapper,
            calculation_time,
            name=f"Daily VaR for {len(tickers)} tickers"
        )

    def setup_realtime_monitoring(
        self,
        monitor_function: Callable,
        tickers: List[str],
        check_interval_minutes: int = 5
    ):
        """
        Setup real-time VaR monitoring (runs every N minutes)

        Args:
            monitor_function: Your monitoring function
            tickers: List of tickers to monitor
            check_interval_minutes: How often to check (default 5 min)

        Example:
            def monitor_var_limits(ticker):
                # Check if VaR exceeds limits
                current_var = calculate_var(ticker)
                if current_var > LIMIT:
                    send_alert(ticker, current_var)

            scheduler.setup_realtime_monitoring(
                monitor_function=monitor_var_limits,
                tickers=["AAPL"],
                check_interval_minutes=5
            )
        """
        def monitor_wrapper():
            for ticker in tickers:
                try:
                    monitor_function(ticker)
                except Exception as e:
                    logger.error(f"Error monitoring {ticker}: {str(e)}")

        self.add_interval_task(
            monitor_wrapper,
            minutes=check_interval_minutes,
            name=f"Real-time monitoring ({check_interval_minutes}min)"
        )

    def setup_weekly_model_retrain(
        self,
        retrain_function: Callable,
        tickers: List[str],
        day: str = "saturday",
        time: str = "02:00"
    ):
        """
        Setup weekly ML model retraining

        Args:
            retrain_function: Your retraining function
            tickers: List of tickers to retrain
            day: Day of week (default Saturday)
            time: Time to run (default 2 AM)

        Example:
            def retrain_lstm(ticker):
                # Retrain LSTM model
                model = LSTMVaRModel()
                model.fit(get_returns(ticker))
                model.save(f"models/{ticker}")

            scheduler.setup_weekly_model_retrain(
                retrain_function=retrain_lstm,
                tickers=["AAPL", "MSFT"]
            )
        """
        def retrain_wrapper():
            for ticker in tickers:
                try:
                    logger.info(f"Retraining model for {ticker}...")
                    retrain_function(ticker)
                    logger.info(f"Completed retrain for {ticker}")
                except Exception as e:
                    logger.error(f"Error retraining {ticker}: {str(e)}")

        self.add_weekly_task(
            retrain_wrapper,
            day=day,
            time_str=time,
            name=f"Weekly model retrain ({day})"
        )

    def setup_end_of_day_report(
        self,
        report_function: Callable,
        tickers: List[str],
        report_time: str = "17:00"
    ):
        """
        Setup end-of-day report generation

        Args:
            report_function: Your report generation function
            tickers: List of tickers to include
            report_time: Time to generate report (default 5 PM)

        Example:
            def generate_eod_report(tickers):
                # Generate daily report
                report = create_var_summary(tickers)
                send_email_report(report)

            scheduler.setup_end_of_day_report(
                report_function=generate_eod_report,
                tickers=["AAPL", "MSFT", "GOOGL"],
                report_time="17:00"
            )
        """
        def report_wrapper():
            try:
                report_function(tickers)
                logger.info("End-of-day report generated")
            except Exception as e:
                logger.error(f"Error generating EOD report: {str(e)}")

        self.add_daily_task(
            report_wrapper,
            report_time,
            name="End-of-day report"
        )


# Example usage and templates
if __name__ == "__main__":
    print("="*60)
    print("VaR SYSTEM SCHEDULER - EXAMPLE SETUP")
    print("="*60)

    # Example 1: Simple daily task
    def example_daily_var():
        """Example: Daily VaR calculation"""
        print(f"[{datetime.now()}] Running daily VaR calculation...")
        # Your actual calculation would go here
        print("VaR calculated successfully!")

    # Example 2: Real-time monitoring
    def example_monitor():
        """Example: Check VaR limits"""
        print(f"[{datetime.now()}] Checking VaR limits...")
        # Your monitoring logic would go here

    # Example 3: Weekly model retrain
    def example_retrain():
        """Example: Retrain ML models"""
        print(f"[{datetime.now()}] Retraining ML models...")
        # Your retraining logic would go here

    # Create scheduler
    scheduler = VaRSystemScheduler()

    # Schedule tasks (using short intervals for demo)
    print("\nScheduling tasks (demo mode - short intervals):")
    print("1. VaR calculation every 30 seconds")
    print("2. Monitoring every 15 seconds")
    print("3. Model retrain every minute")
    print()

    scheduler.add_interval_task(example_daily_var, minutes=0.5, name="Demo VaR Calc")
    scheduler.add_interval_task(example_monitor, minutes=0.25, name="Demo Monitoring")
    scheduler.add_interval_task(example_retrain, minutes=1, name="Demo Retrain")

    # List scheduled jobs
    scheduler.list_jobs()

    print("\n" + "="*60)
    print("PRODUCTION SETUP EXAMPLE")
    print("="*60)
    print("""

    # For production use:

    from src.utils.scheduler import VaRSystemScheduler

    scheduler = VaRSystemScheduler()

    # Daily VaR at 9 AM
    scheduler.add_daily_task(
        calculate_all_var,
        time_str="09:00",
        name="Morning VaR Calculation"
    )

    # Monitor every 5 minutes during trading hours (9 AM - 4 PM)
    scheduler.add_interval_task(
        monitor_var_limits,
        minutes=5,
        name="Real-time Monitoring"
    )

    # Weekly model retrain (Saturday 2 AM)
    scheduler.add_weekly_task(
        retrain_all_models,
        day="saturday",
        time_str="02:00",
        name="Weekly Model Retrain"
    )

    # End-of-day report (5 PM)
    scheduler.add_daily_task(
        generate_eod_report,
        time_str="17:00",
        name="EOD Report"
    )

    # Start scheduler (runs forever)
    scheduler.run()

    """)

    # Uncomment to run demo:
    # print("\nStarting demo scheduler (Ctrl+C to stop)...")
    # scheduler.run()
