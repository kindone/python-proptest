# Makefile for python-proptest development tasks

.PHONY: help install test lint format type-check security clean quick-check pre-commit all-checks test-python38 test-all-python clean-whitespace build-package test-package upload-testpypi upload-pypi bump-version

# Default target
help:
	@echo "python-proptest Development Commands"
	@echo "==============================="
	@echo ""
	@echo "Quick Commands:"
	@echo "  make quick-check    - Run quick pre-commit checks (fast)"
	@echo "  make pre-commit     - Run full pre-commit checks"
	@echo "  make all-checks     - Run all CI checks"
	@echo ""
	@echo "Individual Checks:"
	@echo "  make install        - Install dependencies"
	@echo "  make test           - Run all tests (unittest + pytest)"
	@echo "  make lint           - Run flake8 linting"
	@echo "  make format         - Format code with black and isort"
	@echo "  make type-check     - Run mypy type checking"
	@echo "  make security       - Run security analysis"
	@echo ""
	@echo "Python Version Testing:"
	@echo "  make test-python38  - Test Python 3.8 compatibility"
	@echo "  make test-all-python - Test all available Python versions"
	@echo ""
	@echo "PyPI Publishing:"
	@echo "  make bump-version   - Bump version (patch/minor/major)"
	@echo "  make build-package  - Build package for PyPI distribution"
	@echo "  make test-package   - Test built package locally"
	@echo "  make upload-testpypi - Upload to TestPyPI"
	@echo "  make upload-pypi    - Upload to production PyPI"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Clean up generated files"
	@echo "  make clean-whitespace - Clean trailing whitespaces from all files"
	@echo "  make help           - Show this help message"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -e ".[dev]"

# Run all tests
test:
	@echo "🧪 Running unittest tests..."
	python -m unittest discover tests -v
	@echo "🧪 Running pytest tests..."
	pytest --cov=python_proptest --cov-report=term-missing -v

# Run linting
lint:
	@echo "🔍 Running flake8 linting..."
	flake8 python_proptest --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 python_proptest --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

# Format code
format:
	@echo "🎨 Formatting code with black..."
	black python_proptest/ tests/
	@echo "📋 Sorting imports with isort..."
	isort python_proptest/ tests/

# Type checking
type-check:
	@echo "🔍 Running mypy type checking..."
	mypy python_proptest/

# Security analysis
security:
	@echo "🔒 Running security analysis..."
	bandit -r python_proptest/ -s B311,B110 -f json -o bandit-report.json
	safety check --json > safety-report.json || true

# Quick pre-commit check (fast)
quick-check:
	@echo "⚡ Running quick pre-commit checks..."
	./scripts/quick-check.sh

# Full pre-commit check
pre-commit:
	@echo "🚀 Running full pre-commit checks..."
	./scripts/pre-commit-checks.sh

# All CI checks
all-checks: install lint format type-check test security
	@echo "✅ All CI checks completed!"

# Test Python 3.8 compatibility
test-python38:
	@echo "🐍 Testing Python 3.8 compatibility..."
	./scripts/test-python38.sh

# Test all available Python versions
test-all-python:
	@echo "🐍 Testing all available Python versions..."
	./scripts/test-all-python-versions.sh

# Clean trailing whitespaces
clean-whitespace:
	@echo "🧹 Cleaning trailing whitespaces..."
	./scripts/clean-whitespace.sh

# PyPI Publishing Commands
bump-version:
	@echo "📈 Bumping version..."
	./scripts/bump-version.sh

build-package:
	@echo "📦 Building package for PyPI..."
	./scripts/build-package.sh

test-package:
	@echo "🧪 Testing built package..."
	./scripts/test-package.sh

upload-testpypi:
	@echo "🚀 Uploading to TestPyPI..."
	./scripts/upload-testpypi.sh

upload-pypi:
	@echo "🚀 Uploading to PyPI..."
	./scripts/upload-pypi.sh

# Clean up generated files
clean:
	@echo "🧹 Cleaning up generated files..."
	rm -f bandit-report.json
	rm -f safety-report.json
	rm -f coverage.xml
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf __pycache__
	rm -rf .venv-*-test
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
