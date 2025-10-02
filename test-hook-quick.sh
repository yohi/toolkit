#!/bin/bash

# Pre-push フックのクイックテスト用スクリプト

echo "⚡ Testing pre-push hook with QUICK_TEST mode..."

# 現在のコミットハッシュを取得
CURRENT_COMMIT=$(git rev-parse HEAD)
PARENT_COMMIT=$(git rev-parse HEAD~1)

# クイックテストモードで実行
export QUICK_TEST=true
echo "refs/heads/test-branch $PARENT_COMMIT refs/heads/test-branch $CURRENT_COMMIT" | .githooks/pre-push origin https://example.com/repo.git
