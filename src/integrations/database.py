"""
Database Integration Module for Market Risk VaR System

This module provides database connectivity and ORM models for persisting:
- Historical VaR calculations
- Model parameters and results
- Backtest results
- Risk metrics
- Alerts and notifications

Supports both PostgreSQL and MongoDB for flexibility.

Why Database Integration?
- Historical tracking of risk metrics
- Audit trail for regulatory compliance
- Faster queries than flat files
- Multi-user support
- Automated reporting capabilities
"""

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create base class for ORM models
Base = declarative_base()


class VaRCalculation(Base):
    """
    Stores historical VaR calculations

    This table keeps a record of every VaR calculation performed,
    allowing you to track how risk changes over time and meet
    regulatory requirements for audit trails.
    """
    __tablename__ = 'var_calculations'

    # Primary key - unique identifier for each calculation
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Calculation metadata
    calculation_date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)

    # VaR parameters
    confidence_level = Column(Float, nullable=False)
    position_value = Column(Float, nullable=False)
    method = Column(String(50), nullable=False)  # historical, parametric, monte_carlo, garch

    # VaR results
    var_amount = Column(Float, nullable=False)
    var_percentage = Column(Float, nullable=False)
    expected_shortfall = Column(Float)  # CVaR/ES

    # Additional metrics stored as JSON for flexibility
    additional_metrics = Column(JSON)

    # Model parameters (also JSON for flexibility)
    model_parameters = Column(JSON)

    def __repr__(self):
        return f"<VaRCalculation(ticker={self.ticker}, date={self.calculation_date}, VaR={self.var_amount})>"


class BacktestResult(Base):
    """
    Stores VaR backtesting results

    Backtesting validates your VaR models. Regulators require
    evidence that your models work correctly. This table stores
    all backtest results for compliance and model validation.
    """
    __tablename__ = 'backtest_results'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Backtest metadata
    backtest_date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    method = Column(String(50), nullable=False)

    # Backtest parameters
    confidence_level = Column(Float, nullable=False)
    num_observations = Column(Integer, nullable=False)
    train_ratio = Column(Float, nullable=False)

    # Backtest results
    num_exceptions = Column(Integer, nullable=False)
    exception_rate = Column(Float, nullable=False)
    expected_rate = Column(Float, nullable=False)

    # Statistical test results
    kupiec_test_pvalue = Column(Float)
    kupiec_test_result = Column(String(20))  # PASSED or FAILED
    christoffersen_pvalue = Column(Float)
    christoffersen_result = Column(String(20))
    traffic_light_zone = Column(String(20))  # Green, Yellow, Red

    # Additional statistics
    mean_excess_loss = Column(Float)
    max_excess_loss = Column(Float)

    def __repr__(self):
        return f"<BacktestResult(ticker={self.ticker}, zone={self.traffic_light_zone})>"


class RiskMetric(Base):
    """
    Stores advanced risk metrics over time

    Tracks metrics like Sharpe Ratio, Maximum Drawdown, CVaR, etc.
    This allows you to monitor how risk-adjusted returns evolve
    and identify trends.
    """
    __tablename__ = 'risk_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Metric metadata
    calculation_date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)

    # Position info
    position_value = Column(Float, nullable=False)

    # Risk metrics
    cvar = Column(Float)  # Conditional VaR
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    calmar_ratio = Column(Float)

    # Volatility metrics
    historical_volatility = Column(Float)
    garch_volatility = Column(Float)

    # Additional metrics as JSON
    additional_data = Column(JSON)

    def __repr__(self):
        return f"<RiskMetric(ticker={self.ticker}, sharpe={self.sharpe_ratio})>"


class StressTestResult(Base):
    """
    Stores stress testing results

    Regulators want to see how your portfolio performs under
    extreme scenarios. This table keeps a historical record of
    all stress tests for compliance and risk monitoring.
    """
    __tablename__ = 'stress_test_results'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Test metadata
    test_date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    scenario_name = Column(String(100), nullable=False)

    # Position info
    position_value = Column(Float, nullable=False)

    # Scenario parameters
    scenario_type = Column(String(50))  # market_crash, volatility_spike, etc.
    shock_magnitude = Column(Float)

    # Results
    portfolio_loss = Column(Float)
    new_portfolio_value = Column(Float)
    stressed_var = Column(Float)

    # Additional scenario data
    scenario_data = Column(JSON)

    def __repr__(self):
        return f"<StressTestResult(scenario={self.scenario_name}, loss={self.portfolio_loss})>"


class RiskAlert(Base):
    """
    Stores risk alerts and notifications

    When VaR limits are breached or unusual patterns detected,
    alerts are logged here. This creates an audit trail and
    ensures nothing is missed.
    """
    __tablename__ = 'risk_alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Alert metadata
    alert_date = Column(DateTime, default=datetime.now, nullable=False, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # var_breach, volatility_spike, etc.

    # Alert details
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(String(500), nullable=False)

    # Current metrics that triggered alert
    current_var = Column(Float)
    var_limit = Column(Float)
    breach_amount = Column(Float)

    # Alert status
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_date = Column(DateTime)

    # Actions taken
    action_taken = Column(String(500))

    def __repr__(self):
        return f"<RiskAlert(type={self.alert_type}, severity={self.severity})>"


class DatabaseManager:
    """
    Manages database connections and operations

    This class handles all database interactions:
    - Creating tables
    - Saving calculations
    - Querying historical data
    - Generating reports from database

    Supports both SQLite (for development) and PostgreSQL (for production)
    """

    def __init__(self, database_url: str = "sqlite:///var_system.db"):
        """
        Initialize database manager

        Args:
            database_url: SQLAlchemy database URL
                Examples:
                - SQLite: "sqlite:///var_system.db"
                - PostgreSQL: "postgresql://user:pass@localhost/var_db"
                - MySQL: "mysql://user:pass@localhost/var_db"
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        logger.info(f"Database manager initialized: {database_url}")

    def create_tables(self):
        """
        Create all tables in the database

        Run this once when setting up the system for the first time.
        It's safe to run multiple times - won't overwrite existing data.
        """
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")

    def get_session(self) -> Session:
        """
        Get a database session for queries

        Returns:
            SQLAlchemy session object

        Usage:
            session = db.get_session()
            results = session.query(VaRCalculation).all()
            session.close()
        """
        return self.SessionLocal()

    def save_var_calculation(
        self,
        ticker: str,
        confidence_level: float,
        position_value: float,
        method: str,
        var_amount: float,
        var_percentage: float,
        expected_shortfall: Optional[float] = None,
        additional_metrics: Optional[Dict] = None,
        model_parameters: Optional[Dict] = None
    ) -> int:
        """
        Save a VaR calculation to database

        Args:
            ticker: Stock ticker
            confidence_level: VaR confidence level
            position_value: Portfolio value
            method: VaR method used
            var_amount: VaR in dollars
            var_percentage: VaR as percentage
            expected_shortfall: CVaR value
            additional_metrics: Any additional metrics
            model_parameters: Model parameters used

        Returns:
            ID of saved record
        """
        session = self.get_session()

        try:
            var_calc = VaRCalculation(
                ticker=ticker,
                confidence_level=confidence_level,
                position_value=position_value,
                method=method,
                var_amount=var_amount,
                var_percentage=var_percentage,
                expected_shortfall=expected_shortfall,
                additional_metrics=additional_metrics,
                model_parameters=model_parameters
            )

            session.add(var_calc)
            session.commit()

            record_id = var_calc.id
            logger.info(f"VaR calculation saved: ID={record_id}")

            return record_id

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving VaR calculation: {str(e)}")
            raise
        finally:
            session.close()

    def save_backtest_result(
        self,
        ticker: str,
        method: str,
        confidence_level: float,
        num_observations: int,
        train_ratio: float,
        num_exceptions: int,
        exception_rate: float,
        expected_rate: float,
        kupiec_pvalue: float,
        kupiec_result: str,
        christoffersen_pvalue: float,
        christoffersen_result: str,
        traffic_light_zone: str,
        mean_excess_loss: Optional[float] = None,
        max_excess_loss: Optional[float] = None
    ) -> int:
        """Save backtest result to database"""
        session = self.get_session()

        try:
            backtest = BacktestResult(
                ticker=ticker,
                method=method,
                confidence_level=confidence_level,
                num_observations=num_observations,
                train_ratio=train_ratio,
                num_exceptions=num_exceptions,
                exception_rate=exception_rate,
                expected_rate=expected_rate,
                kupiec_test_pvalue=kupiec_pvalue,
                kupiec_test_result=kupiec_result,
                christoffersen_pvalue=christoffersen_pvalue,
                christoffersen_result=christoffersen_result,
                traffic_light_zone=traffic_light_zone,
                mean_excess_loss=mean_excess_loss,
                max_excess_loss=max_excess_loss
            )

            session.add(backtest)
            session.commit()

            record_id = backtest.id
            logger.info(f"Backtest result saved: ID={record_id}")

            return record_id

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving backtest result: {str(e)}")
            raise
        finally:
            session.close()

    def save_risk_alert(
        self,
        ticker: str,
        alert_type: str,
        severity: str,
        message: str,
        current_var: Optional[float] = None,
        var_limit: Optional[float] = None,
        breach_amount: Optional[float] = None
    ) -> int:
        """
        Save a risk alert to database

        Args:
            ticker: Stock ticker
            alert_type: Type of alert (var_breach, volatility_spike, etc.)
            severity: LOW, MEDIUM, HIGH, CRITICAL
            message: Alert message
            current_var: Current VaR value
            var_limit: VaR limit that was breached
            breach_amount: Amount of breach

        Returns:
            ID of saved alert
        """
        session = self.get_session()

        try:
            alert = RiskAlert(
                ticker=ticker,
                alert_type=alert_type,
                severity=severity,
                message=message,
                current_var=current_var,
                var_limit=var_limit,
                breach_amount=breach_amount
            )

            session.add(alert)
            session.commit()

            record_id = alert.id
            logger.info(f"Risk alert saved: ID={record_id}, Severity={severity}")

            return record_id

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving risk alert: {str(e)}")
            raise
        finally:
            session.close()

    def get_var_history(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        method: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve VaR calculation history

        Args:
            ticker: Stock ticker
            start_date: Start date for history
            end_date: End date for history
            method: Filter by VaR method

        Returns:
            DataFrame with VaR history
        """
        session = self.get_session()

        try:
            query = session.query(VaRCalculation).filter(
                VaRCalculation.ticker == ticker
            )

            if start_date:
                query = query.filter(VaRCalculation.calculation_date >= start_date)
            if end_date:
                query = query.filter(VaRCalculation.calculation_date <= end_date)
            if method:
                query = query.filter(VaRCalculation.method == method)

            query = query.order_by(VaRCalculation.calculation_date)

            results = query.all()

            # Convert to DataFrame
            data = [{
                'date': r.calculation_date,
                'ticker': r.ticker,
                'method': r.method,
                'confidence_level': r.confidence_level,
                'position_value': r.position_value,
                'var_amount': r.var_amount,
                'var_percentage': r.var_percentage,
                'expected_shortfall': r.expected_shortfall
            } for r in results]

            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} VaR records")

            return df

        finally:
            session.close()

    def get_unacknowledged_alerts(self) -> List[RiskAlert]:
        """
        Get all unacknowledged risk alerts

        Returns:
            List of unacknowledged alerts
        """
        session = self.get_session()

        try:
            alerts = session.query(RiskAlert).filter(
                RiskAlert.acknowledged == False
            ).order_by(
                RiskAlert.alert_date.desc()
            ).all()

            logger.info(f"Found {len(alerts)} unacknowledged alerts")
            return alerts

        finally:
            session.close()

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str, action_taken: Optional[str] = None):
        """
        Acknowledge a risk alert

        Args:
            alert_id: Alert ID
            acknowledged_by: Person acknowledging
            action_taken: Actions taken in response
        """
        session = self.get_session()

        try:
            alert = session.query(RiskAlert).filter(RiskAlert.id == alert_id).first()

            if alert:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_date = datetime.now()
                alert.action_taken = action_taken

                session.commit()
                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            else:
                logger.warning(f"Alert {alert_id} not found")

        except Exception as e:
            session.rollback()
            logger.error(f"Error acknowledging alert: {str(e)}")
            raise
        finally:
            session.close()


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = DatabaseManager("sqlite:///var_system.db")

    # Create tables
    db.create_tables()
    print("✓ Database tables created")

    # Save a sample VaR calculation
    var_id = db.save_var_calculation(
        ticker="AAPL",
        confidence_level=0.95,
        position_value=1000000,
        method="historical",
        var_amount=15234.56,
        var_percentage=1.52,
        expected_shortfall=18456.78,
        additional_metrics={'volatility': 0.025, 'sharpe_ratio': 1.45}
    )
    print(f"✓ VaR calculation saved: ID={var_id}")

    # Save a sample alert
    alert_id = db.save_risk_alert(
        ticker="AAPL",
        alert_type="var_breach",
        severity="HIGH",
        message="VaR limit breached: Current VaR exceeds 95% limit",
        current_var=18000,
        var_limit=15000,
        breach_amount=3000
    )
    print(f"✓ Risk alert saved: ID={alert_id}")

    # Retrieve VaR history
    history = db.get_var_history("AAPL")
    print(f"\n✓ VaR History:")
    print(history)

    # Get unacknowledged alerts
    alerts = db.get_unacknowledged_alerts()
    print(f"\n✓ Unacknowledged Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert.alert_type}: {alert.message} (Severity: {alert.severity})")
