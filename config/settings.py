"""
Configuration settings for Market Risk VaR System.
Loads settings from environment variables with sensible defaults.
"""
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Application settings."""

    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR}/data/market_risk.db"
    )

    # =============================================================================
    # API CONFIGURATION
    # =============================================================================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    API_WORKERS: int = int(os.getenv("API_WORKERS", "4"))

    # CORS Settings
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8501"
    ).split(",")
    CORS_ALLOW_CREDENTIALS: bool = (
        os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    )

    # API Security
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")
    API_ALGORITHM: str = os.getenv("API_ALGORITHM", "HS256")
    API_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("API_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    @classmethod
    def validate_production_settings(cls):
        """Validate required settings in production environment."""
        if cls.ENVIRONMENT == "production":
            if not cls.API_SECRET_KEY or cls.API_SECRET_KEY == "":
                raise ValueError(
                    "API_SECRET_KEY must be set in production! "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            if len(cls.API_SECRET_KEY) < 32:
                raise ValueError("API_SECRET_KEY must be at least 32 characters long")
            if cls.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if cls.SMTP_PASSWORD == "" and cls.ENABLE_SCHEDULER:
                raise ValueError("SMTP_PASSWORD required when scheduler is enabled")

    # =============================================================================
    # LOGGING
    # =============================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "market_risk.log"))
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # =============================================================================
    # VAR CALCULATION DEFAULTS
    # =============================================================================
    DEFAULT_CONFIDENCE_LEVEL: float = float(os.getenv("DEFAULT_CONFIDENCE_LEVEL", "0.95"))
    DEFAULT_POSITION_VALUE: float = float(os.getenv("DEFAULT_POSITION_VALUE", "1000000"))
    DEFAULT_HISTORICAL_WINDOW: int = int(os.getenv("DEFAULT_HISTORICAL_WINDOW", "252"))
    DEFAULT_MC_SIMULATIONS: int = int(os.getenv("DEFAULT_MC_SIMULATIONS", "10000"))

    # =============================================================================
    # MODEL CONFIGURATION
    # =============================================================================
    # GARCH defaults
    DEFAULT_GARCH_P: int = int(os.getenv("DEFAULT_GARCH_P", "1"))
    DEFAULT_GARCH_Q: int = int(os.getenv("DEFAULT_GARCH_Q", "1"))
    DEFAULT_GARCH_DIST: str = os.getenv("DEFAULT_GARCH_DIST", "normal")

    # ARIMA defaults
    DEFAULT_ARIMA_P: int = int(os.getenv("DEFAULT_ARIMA_P", "2"))
    DEFAULT_ARIMA_D: int = int(os.getenv("DEFAULT_ARIMA_D", "0"))
    DEFAULT_ARIMA_Q: int = int(os.getenv("DEFAULT_ARIMA_Q", "2"))

    # ML Model settings
    ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", str(BASE_DIR / "data" / "models"))
    ML_ENABLE_GPU: bool = os.getenv("ML_ENABLE_GPU", "False").lower() == "true"
    ML_BATCH_SIZE: int = int(os.getenv("ML_BATCH_SIZE", "32"))
    ML_EPOCHS: int = int(os.getenv("ML_EPOCHS", "100"))

    # =============================================================================
    # EMAIL ALERTS CONFIGURATION
    # =============================================================================
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() == "true"
    ALERT_RECIPIENTS: List[str] = os.getenv("ALERT_RECIPIENTS", "").split(",")

    # =============================================================================
    # SCHEDULER CONFIGURATION
    # =============================================================================
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "False").lower() == "true"
    CALCULATION_SCHEDULE: str = os.getenv("CALCULATION_SCHEDULE", "09:00")
    REPORT_SCHEDULE: str = os.getenv("REPORT_SCHEDULE", "17:00")
    RETRAINING_SCHEDULE: str = os.getenv("RETRAINING_SCHEDULE", "SUNDAY")

    # =============================================================================
    # FRONTEND CONFIGURATION
    # =============================================================================
    NEXT_PUBLIC_API_URL: str = os.getenv(
        "NEXT_PUBLIC_API_URL", "http://localhost:8000/api/v1"
    )
    STREAMLIT_PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))

    # =============================================================================
    # DEVELOPMENT/PRODUCTION
    # =============================================================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # =============================================================================
    # DATA DIRECTORIES
    # =============================================================================
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = DATA_DIR / "models"
    LOGS_DIR: Path = BASE_DIR / "logs"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # =============================================================================
    # PERFORMANCE TUNING
    # =============================================================================
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # seconds
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        for dir_path in [
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
            cls.MODELS_DIR,
            cls.LOGS_DIR,
            cls.REPORTS_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Create settings instance
settings = Settings()

# Ensure directories exist
settings.ensure_directories()

# Validate production settings
settings.validate_production_settings()
