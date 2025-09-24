#!/bin/bash

# Pre-push フックのテスト用スクリプト

echo "🧪 Testing pre-push hook with simulated changes..."

# 現在のコミットハッシュを取得
CURRENT_COMMIT=$(git rev-parse HEAD)
PARENT_COMMIT=$(git rev-parse HEAD~1)

# get_github_coderabbit_review ディレクトリに変更があったという状況をシミュレート
echo "refs/heads/test-branch $PARENT_COMMIT refs/heads/test-branch $CURRENT_COMMIT" | .githooks/pre-push origin https://example.com/repo.git
