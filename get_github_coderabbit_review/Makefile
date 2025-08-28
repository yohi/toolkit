# CodeRabbit Comment Fetcher - Development Makefile

.PHONY: help install install-dev test test-unit test-integration test-performance
.PHONY: lint format type-check pre-commit clean build publish
.PHONY: uvx-test docker-build docker-run docs serve-docs
.PHONY: coverage coverage-html coverage-report security-scan

# Default target
help: ## Show this help message
	@echo "CodeRabbit Comment Fetcher - Development Commands"
	@echo "================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install package in development mode
	pip install -e .

install-dev: ## Install package with development dependencies
	pip install -e ".[dev,performance,docs]"

install-full: ## Install package with all optional dependencies
	pip install -e ".[all]"

# Testing
test: ## Run all tests
	python tests/test_runner.py --type all

test-unit: ## Run unit tests only
	python tests/test_runner.py --type unit

test-integration: ## Run integration tests only
	python tests/test_runner.py --type integration

test-performance: ## Run performance tests only
	python tests/test_runner.py --type performance

test-fast: ## Run fast tests (exclude performance)
	pytest tests/unit tests/integration -v

test-verbose: ## Run tests with verbose output
	python tests/test_runner.py --type all --verbosity 2

# Test Coverage
coverage: ## Run tests with coverage
	python tests/test_runner.py --coverage

coverage-html: ## Generate HTML coverage report
	pytest --cov=coderabbit_fetcher --cov-report=html tests/

coverage-report: ## Show coverage report in terminal
	pytest --cov=coderabbit_fetcher --cov-report=term-missing tests/

# Code Quality
lint: ## Run all linters
	ruff check coderabbit_fetcher tests scripts
	mypy coderabbit_fetcher

lint-fix: ## Fix linting issues automatically
	ruff check --fix coderabbit_fetcher tests scripts
	isort coderabbit_fetcher tests scripts
	black coderabbit_fetcher tests scripts

format: ## Format code with black and isort
	black coderabbit_fetcher tests scripts
	isort coderabbit_fetcher tests scripts

type-check: ## Run type checking with mypy
	mypy coderabbit_fetcher

# Git hooks
pre-commit-install: ## Install pre-commit hooks
	pre-commit install

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

# Package Management
clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build package
	python -m build

build-wheel: ## Build wheel only
	python -m build --wheel

build-sdist: ## Build source distribution only
	python -m build --sdist

# uvx Testing
uvx-test: ## Test uvx compatibility
	python scripts/test_uvx_installation.py

uvx-install-test: ## Test installation with uvx
	uvx --help || (echo "uvx not found. Install with: pip install uv" && exit 1)
	@echo "Testing uvx installation..."
	uvx --from . coderabbit-fetch --help

# Docker
docker-build: ## Build Docker image
	docker build -t coderabbit-fetcher .

docker-run: ## Run Docker container (interactive)
	docker run -it --rm \
		-v ~/.config/gh:/root/.config/gh:ro \
		-v $(PWD)/examples:/app/examples:ro \
		coderabbit-fetcher --help

docker-test: ## Test Docker image
	docker run --rm coderabbit-fetcher --version

# Documentation
docs: ## Build documentation
	mkdocs build

serve-docs: ## Serve documentation locally
	mkdocs serve

docs-clean: ## Clean documentation build
	rm -rf site/

# Security
security-scan: ## Run security scans
	bandit -r coderabbit_fetcher/
	safety check

# Release Management
check-release: ## Check if ready for release
	@echo "Checking release readiness..."
	@python -c "import coderabbit_fetcher; print(f'Version: {coderabbit_fetcher.__version__}')"
	@echo "Running tests..."
	@$(MAKE) test
	@echo "Running linting..."
	@$(MAKE) lint
	@echo "Testing uvx compatibility..."
	@$(MAKE) uvx-test
	@echo "✅ Release checks completed"

publish-test: ## Publish to Test PyPI
	python -m build
	twine upload --repository testpypi dist/*

publish: ## Publish to PyPI (production)
	python -m build
	twine upload dist/*

# Development Utilities
show-deps: ## Show dependency tree
	pip-tree || pip install pipdeptree && pipdeptree

show-outdated: ## Show outdated dependencies
	pip list --outdated

update-deps: ## Update development dependencies
	pip-compile --upgrade requirements-dev.in

# Project Statistics
stats: ## Show project statistics
	@echo "Project Statistics"
	@echo "=================="
	@echo "Python files:"
	@find coderabbit_fetcher -name "*.py" | wc -l
	@echo "Lines of code:"
	@find coderabbit_fetcher -name "*.py" -exec wc -l {} + | tail -1
	@echo "Test files:"
	@find tests -name "*.py" | wc -l
	@echo "Test lines:"
	@find tests -name "*.py" -exec wc -l {} + | tail -1

# Environment Setup
setup-dev: ## Set up development environment
	@echo "Setting up development environment..."
	pip install --upgrade pip setuptools wheel
	$(MAKE) install-dev
	$(MAKE) pre-commit-install
	@echo "✅ Development environment ready"

# Quick Start
quick-start: setup-dev test lint ## Set up and validate development environment
	@echo "🚀 Quick start completed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "  - Run tests: make test"
	@echo "  - Format code: make format"
	@echo "  - Test uvx: make uvx-test"
	@echo "  - Build package: make build"

# Continuous Integration Targets
ci-test: ## CI testing pipeline
	$(MAKE) install-dev
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) coverage

ci-security: ## CI security checks
	$(MAKE) security-scan

ci-compatibility: ## CI compatibility checks
	$(MAKE) uvx-test

# Help for common tasks
help-development: ## Show development workflow help
	@echo "Development Workflow"
	@echo "==================="
	@echo ""
	@echo "1. Setup:           make setup-dev"
	@echo "2. Make changes:    edit code"
	@echo "3. Format:          make format"
	@echo "4. Test:            make test"
	@echo "5. Lint:            make lint"
	@echo "6. Commit:          git commit (pre-commit will run)"
	@echo ""
	@echo "Release Process:"
	@echo "1. Check:           make check-release"
	@echo "2. Build:           make build"
	@echo "3. Test publish:    make publish-test"
	@echo "4. Publish:         make publish"

help-testing: ## Show testing help
	@echo "Testing Commands"
	@echo "==============="
	@echo ""
	@echo "make test           - Run all tests"
	@echo "make test-unit      - Unit tests only"
	@echo "make test-integration - Integration tests only"
	@echo "make test-performance - Performance tests only"
	@echo "make coverage       - Tests with coverage"
	@echo "make uvx-test       - Test uvx compatibility"
	@echo ""
	@echo "Test files are in tests/ directory:"
	@echo "  tests/unit/        - Unit tests"
	@echo "  tests/integration/ - Integration tests"  
	@echo "  tests/performance/ - Performance tests"
