.PHONY: help install test lint format clean docker-build docker-up docker-down run-api run-dashboard

# Default target
help:
	@echo "Market Risk VaR System - Available Commands"
	@echo "==========================================="
	@echo "install          Install Python dependencies"
	@echo "install-dev      Install development dependencies"
	@echo "test             Run tests"
	@echo "test-cov         Run tests with coverage"
	@echo "lint             Run linters (flake8, mypy)"
	@echo "format           Format code with black and isort"
	@echo "clean            Clean build artifacts"
	@echo "docker-build     Build Docker images"
	@echo "docker-up        Start Docker containers"
	@echo "docker-down      Stop Docker containers"
	@echo "run-api          Run FastAPI server locally"
	@echo "run-dashboard    Run Streamlit dashboard locally"
	@echo "run-frontend     Run Next.js frontend locally"
	@echo "setup-db         Setup database schema"
	@echo "backtest         Run VaR backtesting (use TICKER=AAPL)"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Testing
test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

# Code Quality
lint:
	flake8 src tests
	mypy src

format:
	black src tests scripts
	isort src tests scripts

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist .pytest_cache .mypy_cache htmlcov .coverage

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Local Development
run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard:
	streamlit run dashboard/streamlit_app.py --server.port 8501

run-frontend:
	cd frontend && npm run dev

# Database
setup-db:
	python scripts/setup_db.py

# Backtesting
backtest:
	python scripts/run_backtest.py $(TICKER)

# Install and setup everything
setup-all: install-dev setup-db
	@echo "✓ Setup complete!"
