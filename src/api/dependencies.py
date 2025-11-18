"""
Shared dependencies for API endpoints.
"""
from functools import lru_cache

from src.data.data_collector import DataCollector
from src.data.preprocessor import DataPreprocessor


@lru_cache()
def get_data_collector() -> DataCollector:
    """Get data collector instance (singleton)."""
    return DataCollector()


@lru_cache()
def get_preprocessor() -> DataPreprocessor:
    """Get preprocessor instance (singleton)."""
    return DataPreprocessor()
