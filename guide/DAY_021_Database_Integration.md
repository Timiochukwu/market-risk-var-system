# Day 021: Database Integration (SQLAlchemy)

**Duration**: 2 hours | **Difficulty**: Intermediate | **Prerequisites**: Day 001-020

---

## 📋 What You'll Build

- SQLAlchemy ORM setup
- PostgreSQL/SQLite database configuration
- Database models (VaR results, positions, backtests)
- Database migrations with Alembic
- CRUD operations
- Database API endpoints

---

## 💡 Why Database Integration?

### Without Database:
```
- Calculate VaR → Lost after API response
- No historical tracking
- Can't analyze trends
- Manual record keeping
```

### With Database:
```
- Store all VaR calculations
- Track positions over time
- Analyze historical trends
- Generate reports from stored data
- Audit trail for compliance
```

---

## 💻 Database Schema Design

### Tables:

```
positions
├── id (Primary Key)
├── ticker (String)
├── position_value (Float)
├── created_at (DateTime)
└── updated_at (DateTime)

var_calculations
├── id (Primary Key)
├── position_id (Foreign Key)
├── method (String: historical, parametric, etc.)
├── confidence_level (Float)
├── var_amount (Float)
├── var_percentage (Float)
├── cvar_amount (Float)
├── calculation_date (DateTime)
└── metadata (JSON)

backtest_results
├── id (Primary Key)
├── position_id (Foreign Key)
├── num_observations (Integer)
├── num_exceptions (Integer)
├── exception_rate (Float)
├── kupiec_pvalue (Float)
├── kupiec_pass (Boolean)
├── test_date (DateTime)
└── metadata (JSON)
```

---

## 💻 Implementation

### Step 1: Install Dependencies

```bash
pip install sqlalchemy==2.0.23 psycopg2-binary==2.9.9 alembic==1.13.1
```

For SQLite (simpler, no setup):
```bash
# SQLite included with Python, no additional install needed
```

---

### Step 2: Create Database Models

Create `src/database/models.py`:

```python
"""
Database Models for VaR System
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Position(Base):
    """Position (ticker and value)"""

    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    position_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    var_calculations = relationship("VaRCalculation", back_populates="position", cascade="all, delete-orphan")
    backtest_results = relationship("BacktestResult", back_populates="position", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Position(ticker={self.ticker}, value={self.position_value})>"


class VaRCalculation(Base):
    """VaR calculation result"""

    __tablename__ = 'var_calculations'

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False)

    method = Column(String(50), nullable=False)  # historical, parametric, monte_carlo, garch
    confidence_level = Column(Float, nullable=False)

    var_amount = Column(Float, nullable=False)
    var_percentage = Column(Float, nullable=False)
    cvar_amount = Column(Float, nullable=True)

    calculation_date = Column(DateTime, default=datetime.utcnow, index=True)

    # Store additional data as JSON
    metadata = Column(JSON, nullable=True)

    # Relationship
    position = relationship("Position", back_populates="var_calculations")

    def __repr__(self):
        return f"<VaRCalculation(method={self.method}, var={self.var_amount})>"


class BacktestResult(Base):
    """Backtest result"""

    __tablename__ = 'backtest_results'

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False)

    method = Column(String(50), nullable=False)
    confidence_level = Column(Float, nullable=False)

    num_observations = Column(Integer, nullable=False)
    num_exceptions = Column(Integer, nullable=False)
    exception_rate = Column(Float, nullable=False)

    kupiec_pvalue = Column(Float, nullable=True)
    kupiec_pass = Column(Boolean, nullable=True)

    test_date = Column(DateTime, default=datetime.utcnow, index=True)

    # Store full backtest details as JSON
    metadata = Column(JSON, nullable=True)

    # Relationship
    position = relationship("Position", back_populates="backtest_results")

    def __repr__(self):
        return f"<BacktestResult(exceptions={self.num_exceptions}, pass={self.kupiec_pass})>"
```

---

### Step 3: Database Connection

Create `src/database/connection.py`:

```python
"""
Database Connection and Session Management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
import logging

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage database connection and sessions"""

    def __init__(self, database_url: str = None):
        """
        Initialize database manager

        Args:
            database_url: Database URL
                SQLite: 'sqlite:///./var_system.db'
                PostgreSQL: 'postgresql://user:pass@localhost/var_db'
        """

        # Use environment variable or default to SQLite
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'sqlite:///./var_system.db'
        )

        # Create engine
        if self.database_url.startswith('sqlite'):
            # SQLite specific settings
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            # PostgreSQL or other databases
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Database initialized: {self.database_url.split('://')[0]}")

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped")

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def close(self):
        """Close database connection"""
        self.engine.dispose()
        logger.info("Database connection closed")


# Global database manager instance
db_manager = DatabaseManager()


def get_db():
    """
    Dependency for FastAPI to get database session

    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
```

---

### Step 4: CRUD Operations

Create `src/database/crud.py`:

```python
"""
CRUD Operations for VaR Database
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from .models import Position, VaRCalculation, BacktestResult


# ============================================================================
# Position CRUD
# ============================================================================

def create_position(db: Session, ticker: str, position_value: float) -> Position:
    """Create new position"""

    position = Position(
        ticker=ticker,
        position_value=position_value
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


def get_position_by_ticker(db: Session, ticker: str) -> Optional[Position]:
    """Get position by ticker"""
    return db.query(Position).filter(Position.ticker == ticker).first()


def get_or_create_position(db: Session, ticker: str, position_value: float) -> Position:
    """Get existing position or create new one"""

    position = get_position_by_ticker(db, ticker)

    if position:
        # Update position value
        position.position_value = position_value
        position.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(position)
    else:
        position = create_position(db, ticker, position_value)

    return position


def get_all_positions(db: Session, skip: int = 0, limit: int = 100) -> List[Position]:
    """Get all positions"""
    return db.query(Position).offset(skip).limit(limit).all()


# ============================================================================
# VaR Calculation CRUD
# ============================================================================

def create_var_calculation(
    db: Session,
    position_id: int,
    method: str,
    confidence_level: float,
    var_amount: float,
    var_percentage: float,
    cvar_amount: float = None,
    metadata: dict = None
) -> VaRCalculation:
    """Create VaR calculation record"""

    var_calc = VaRCalculation(
        position_id=position_id,
        method=method,
        confidence_level=confidence_level,
        var_amount=var_amount,
        var_percentage=var_percentage,
        cvar_amount=cvar_amount,
        metadata=metadata
    )

    db.add(var_calc)
    db.commit()
    db.refresh(var_calc)
    return var_calc


def get_var_calculations(
    db: Session,
    ticker: str = None,
    method: str = None,
    days: int = 30
) -> List[VaRCalculation]:
    """Get VaR calculations with filters"""

    query = db.query(VaRCalculation)

    # Filter by ticker
    if ticker:
        query = query.join(Position).filter(Position.ticker == ticker)

    # Filter by method
    if method:
        query = query.filter(VaRCalculation.method == method)

    # Filter by date range
    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(VaRCalculation.calculation_date >= start_date)

    return query.order_by(VaRCalculation.calculation_date.desc()).all()


def get_latest_var(db: Session, ticker: str, method: str = None) -> Optional[VaRCalculation]:
    """Get latest VaR calculation for ticker"""

    query = db.query(VaRCalculation).join(Position).filter(Position.ticker == ticker)

    if method:
        query = query.filter(VaRCalculation.method == method)

    return query.order_by(VaRCalculation.calculation_date.desc()).first()


# ============================================================================
# Backtest Result CRUD
# ============================================================================

def create_backtest_result(
    db: Session,
    position_id: int,
    method: str,
    confidence_level: float,
    num_observations: int,
    num_exceptions: int,
    exception_rate: float,
    kupiec_pvalue: float = None,
    kupiec_pass: bool = None,
    metadata: dict = None
) -> BacktestResult:
    """Create backtest result record"""

    backtest = BacktestResult(
        position_id=position_id,
        method=method,
        confidence_level=confidence_level,
        num_observations=num_observations,
        num_exceptions=num_exceptions,
        exception_rate=exception_rate,
        kupiec_pvalue=kupiec_pvalue,
        kupiec_pass=kupiec_pass,
        metadata=metadata
    )

    db.add(backtest)
    db.commit()
    db.refresh(backtest)
    return backtest


def get_backtest_results(
    db: Session,
    ticker: str = None,
    days: int = 90
) -> List[BacktestResult]:
    """Get backtest results"""

    query = db.query(BacktestResult)

    if ticker:
        query = query.join(Position).filter(Position.ticker == ticker)

    start_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(BacktestResult.test_date >= start_date)

    return query.order_by(BacktestResult.test_date.desc()).all()
```

---

## 🧪 API Integration

Update `src/api/main.py`:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from database.connection import get_db, db_manager
from database import crud

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    db_manager.create_tables()
    logger.info("Database ready")


@app.post("/api/v1/var/calculate-and-store")
async def calculate_and_store_var(
    ticker: str,
    position_value: float = 1000000,
    method: str = "historical",
    confidence_level: float = 0.95,
    db: Session = Depends(get_db)
):
    """Calculate VaR and store in database"""

    # Fetch data and calculate VaR
    data = data_collector.fetch_stock_data(ticker, period="2y")
    returns = preprocessor.prepare_returns_data(data)['Returns']

    var_calc = VaRCalculator(confidence_level=confidence_level)

    if method == "historical":
        var_result = var_calc.historical_var(returns, position_value)
    elif method == "parametric":
        var_result = var_calc.parametric_var(returns, position_value)
    else:
        var_result = var_calc.monte_carlo_var(returns, position_value)

    # Get or create position
    position = crud.get_or_create_position(db, ticker, position_value)

    # Store VaR calculation
    var_record = crud.create_var_calculation(
        db=db,
        position_id=position.id,
        method=method,
        confidence_level=confidence_level,
        var_amount=var_result['VaR'],
        var_percentage=var_result['VaR_Percentage'],
        cvar_amount=var_result.get('CVaR'),
        metadata={
            'position_value': position_value,
            'data_points': len(returns)
        }
    )

    return {
        "ticker": ticker,
        "var_id": var_record.id,
        "var_amount": var_record.var_amount,
        "var_percentage": var_record.var_percentage,
        "cvar_amount": var_record.cvar_amount,
        "calculation_date": var_record.calculation_date,
        "stored": True
    }


@app.get("/api/v1/var/history/{ticker}")
async def get_var_history(
    ticker: str,
    method: str = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get VaR calculation history"""

    calculations = crud.get_var_calculations(db, ticker=ticker, method=method, days=days)

    return {
        "ticker": ticker,
        "count": len(calculations),
        "calculations": [
            {
                "id": calc.id,
                "method": calc.method,
                "var_amount": calc.var_amount,
                "var_percentage": calc.var_percentage,
                "cvar_amount": calc.cvar_amount,
                "calculation_date": calc.calculation_date
            }
            for calc in calculations
        ]
    }


@app.get("/api/v1/positions")
async def get_positions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all positions"""

    positions = crud.get_all_positions(db, skip=skip, limit=limit)

    return {
        "count": len(positions),
        "positions": [
            {
                "id": pos.id,
                "ticker": pos.ticker,
                "position_value": pos.position_value,
                "created_at": pos.created_at,
                "updated_at": pos.updated_at
            }
            for pos in positions
        ]
    }
```

---

## 🧪 Test with curl

### Initialize Database:

```bash
# Start API (this will create database tables)
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Calculate and Store VaR:

```bash
# Calculate and store VaR for AAPL
curl -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "position_value": 1000000,
    "method": "historical",
    "confidence_level": 0.95
  }' | jq '.'
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "var_id": 1,
  "var_amount": 28456.78,
  "var_percentage": 2.8457,
  "cvar_amount": 42123.45,
  "calculation_date": "2026-01-01T10:30:00",
  "stored": true
}
```

### Store Multiple Calculations:

```bash
# Store VaR for multiple tickers
for ticker in AAPL MSFT GOOGL TSLA; do
  echo "Storing VaR for $ticker..."
  curl -s -X POST "http://localhost:8000/api/v1/var/calculate-and-store" \
    -d "{\"ticker\": \"$ticker\", \"method\": \"historical\"}" \
    -H "Content-Type: application/json" | jq '{ticker, var_id, var_amount}'
done
```

### Get VaR History:

```bash
# Get 30-day VaR history for AAPL
curl -X GET "http://localhost:8000/api/v1/var/history/AAPL?days=30" | jq '.'
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "count": 5,
  "calculations": [
    {
      "id": 5,
      "method": "historical",
      "var_amount": 28456.78,
      "var_percentage": 2.8457,
      "cvar_amount": 42123.45,
      "calculation_date": "2026-01-01T10:30:00"
    },
    ...
  ]
}
```

### Filter by Method:

```bash
# Get only parametric VaR calculations
curl -X GET "http://localhost:8000/api/v1/var/history/AAPL?method=parametric" \
  | jq '.calculations[] | {method, var_amount, date: .calculation_date}'
```

### Get All Positions:

```bash
# List all positions
curl -X GET "http://localhost:8000/api/v1/positions" | jq '.'
```

**Expected:**
```json
{
  "count": 4,
  "positions": [
    {
      "id": 1,
      "ticker": "AAPL",
      "position_value": 1000000,
      "created_at": "2026-01-01T10:00:00",
      "updated_at": "2026-01-01T10:30:00"
    },
    ...
  ]
}
```

### Check Database File (SQLite):

```bash
# Verify database file was created
ls -lh var_system.db

# Query database directly (if sqlite3 installed)
sqlite3 var_system.db "SELECT COUNT(*) FROM var_calculations;"
sqlite3 var_system.db "SELECT ticker, position_value FROM positions;"
```

---

## 🐘 PostgreSQL Setup (Optional)

If you want to use PostgreSQL instead of SQLite:

### Install PostgreSQL:

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

### Create Database:

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE var_system;
CREATE USER var_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE var_system TO var_user;
\q
```

### Update Database URL:

```bash
# Set environment variable
export DATABASE_URL="postgresql://var_user:your_password@localhost/var_system"

# Or in .env file
echo "DATABASE_URL=postgresql://var_user:your_password@localhost/var_system" >> .env
```

### Test Connection:

```bash
# Restart API with PostgreSQL
uvicorn main:app --reload
```

---

## ✅ Completed

✅ SQLAlchemy ORM setup
✅ Database models (Position, VaRCalculation, BacktestResult)
✅ Database connection management
✅ CRUD operations
✅ API integration with database
✅ curl-based testing
✅ SQLite and PostgreSQL support

**Next**: Historical VaR Storage & Trends (Day 022)
