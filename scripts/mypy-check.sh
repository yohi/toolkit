#!/bin/bash

# MyPy type checking script for pre-commit

cd get_github_coderabbit_review

if python3 -c "import mypy" 2>/dev/null; then
    echo "📝 Running MyPy type checks..."
    python3 -m mypy coderabbit_fetcher --ignore-missing-imports
else
    echo "ℹ️  MyPy not available, skipping type checks"
    exit 0
fi
