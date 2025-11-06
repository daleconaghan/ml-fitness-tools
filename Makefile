.PHONY: help install install-dev test lint format security clean run

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

test:  ## Run tests
	pytest tests/ -v

test-cov:  ## Run tests with coverage report
	pytest tests/ --cov=. --cov-report=html --cov-report=term

lint:  ## Run code quality checks
	@echo "Running Ruff..."
	ruff check .
	@echo "\nRunning Black..."
	black --check .
	@echo "\nRunning isort..."
	isort --check-only .

format:  ## Auto-format code
	@echo "Formatting with Black..."
	black .
	@echo "Sorting imports with isort..."
	isort .
	@echo "Fixing with Ruff..."
	ruff check --fix .

security:  ## Run security checks
	@echo "Running Bandit..."
	bandit -r . -c pyproject.toml
	@echo "\nChecking dependencies with Safety..."
	safety check

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ coverage.xml bandit-report.json

run:  ## Run the API server
	python recovery_api.py

ci:  ## Run all CI checks locally
	@echo "Running all CI checks..."
	@$(MAKE) test
	@$(MAKE) lint
	@$(MAKE) security
	@echo "\n✅ All CI checks completed!"
