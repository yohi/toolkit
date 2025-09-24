#!/bin/bash

# CodeRabbit Review Tool validation script for pre-commit
# This script runs comprehensive validation when changes are detected in get_github_coderabbit_review/

set -e

PROJECT_DIR="get_github_coderabbit_review"
REPO_ROOT="/home/y_ohi/program/toolkit"
PROJECT_PATH="$REPO_ROOT/$PROJECT_DIR"

echo "🔍 CodeRabbit Review Tool validation started..."

# Change to project directory
if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ Project directory not found: $PROJECT_PATH"
    exit 1
fi

cd "$PROJECT_PATH"

# Function to run validation tests
run_validation() {
    local test_type="$1"

    case "$test_type" in
        "quick")
            echo "⚡ Running quick validation..."
            if python3 tests/pr38/test_pr38_direct.py; then
                echo "✅ Quick validation passed!"
                return 0
            else
                echo "❌ Quick validation failed!"
                return 1
            fi
            ;;
        "full")
            echo "🚀 Running full validation..."
            if python3 tests/pr38/test_pr38_final.py; then
                echo "✅ Full validation passed!"
                return 0
            else
                echo "❌ Full validation failed!"
                return 1
            fi
            ;;
        *)
            echo "❌ Unknown test type: $test_type"
            return 1
            ;;
    esac
}

# Function to check if GitHub CLI is available
check_github_cli() {
    if ! command -v gh >/dev/null 2>&1; then
        echo "⚠️  GitHub CLI (gh) not found. Some tests may fail."
        echo "   Install with: https://cli.github.com/"
        return 1
    fi

    if ! gh auth status >/dev/null 2>&1; then
        echo "⚠️  GitHub CLI not authenticated. Some tests may fail."
        echo "   Authenticate with: gh auth login"
        return 1
    fi

    echo "✅ GitHub CLI is available and authenticated"
    return 0
}

# Function to run linting checks
run_lint_checks() {
    echo "🔍 Running code quality checks..."

    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        echo "❌ pyproject.toml not found. Are we in the right directory?"
        return 1
    fi

    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "🐍 Python version: $python_version"

    # Type checking (if mypy is available)
    if command -v mypy >/dev/null 2>&1; then
        echo "📝 Running type checks..."
        if mypy coderabbit_fetcher --ignore-missing-imports; then
            echo "✅ Type checks passed"
        else
            echo "⚠️  Type checks found issues (non-blocking)"
        fi
    else
        echo "ℹ️  MyPy not available, skipping type checks"
    fi

    return 0
}

# Main execution
main() {
    echo "🎯 CodeRabbit Review Tool Validation"
    echo "📍 Project path: $PROJECT_PATH"
    echo "📍 Working directory: $(pwd)"

    # Check environment
    check_github_cli
    gh_available=$?

    # Run linting checks
    run_lint_checks

    # Determine test type based on environment variables
    if [ "${QUICK_TEST:-false}" = "true" ]; then
        test_type="quick"
    elif [ "${FULL_TEST:-true}" = "true" ]; then
        test_type="full"
    else
        test_type="quick"
    fi

    echo ""
    echo "🧪 Running validation tests (mode: $test_type)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Skip validation if GitHub CLI is not available and we're running in CI
    if [ $gh_available -ne 0 ] && [ "${CI:-false}" = "true" ]; then
        echo "⚠️  Skipping validation tests in CI environment without GitHub CLI"
        echo "✅ Validation completed (skipped)"
        return 0
    fi

    # Run validation
    if run_validation "$test_type"; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🎉 All validation tests passed!"
        return 0
    else
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "❌ Validation tests failed!"
        echo ""
        echo "💡 Troubleshooting tips:"
        echo "   - Run manually: cd $PROJECT_DIR && python3 tests/pr38/test_pr38_final.py"
        echo "   - Quick test: QUICK_TEST=true pre-commit run --hook-stage pre-push"
        echo "   - Skip validation: git push --no-verify"
        return 1
    fi
}

# Execute main function
main "$@"
