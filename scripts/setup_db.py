#!/usr/bin/env python3
"""
Setup database schema for Market Risk VaR System.
"""
from sqlalchemy import create_engine
from config.settings import settings
from src.integrations.database import Base, init_db

def main():
    """Initialize database."""
    print(f"Setting up database at: {settings.DATABASE_URL}")

    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)

    print("✓ Database schema created successfully")
    print("✓ All tables initialized")

if __name__ == "__main__":
    main()
