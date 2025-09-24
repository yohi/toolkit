#!/bin/bash

# MyPy type checking script for pre-commit

cd get_github_coderabbit_review

if python3 -c "import mypy" 2>/dev/null; then
    echo "📝 Running MyPy type checks (with relaxed settings)..."
    # より寛容な設定でmypyを実行
    python3 -m mypy coderabbit_fetcher \
        --ignore-missing-imports \
        --no-strict-optional \
        --allow-untyped-calls \
        --allow-untyped-defs \
        --allow-incomplete-defs \
        --no-warn-return-any \
        --no-warn-unused-ignores
else
    echo "ℹ️  MyPy not available, skipping type checks"
    exit 0
fi
