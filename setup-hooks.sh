#!/bin/bash

# Git フックセットアップスクリプト
# get_github_coderabbit_review プロジェクト用

set -e

echo "🔧 Setting up Git hooks for get_github_coderabbit_review project..."

# リポジトリのルートディレクトリを確認
REPO_ROOT=$(git rev-parse --show-toplevel)
echo "📁 Repository root: $REPO_ROOT"

# .githooksディレクトリの存在確認
HOOKS_DIR="$REPO_ROOT/.githooks"
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ Hooks directory not found: $HOOKS_DIR"
    exit 1
fi

# pre-pushフックの存在確認
PRE_PUSH_HOOK="$HOOKS_DIR/pre-push"
if [ ! -f "$PRE_PUSH_HOOK" ]; then
    echo "❌ pre-push hook not found: $PRE_PUSH_HOOK"
    exit 1
fi

# 実行権限の確認・付与
if [ ! -x "$PRE_PUSH_HOOK" ]; then
    echo "🔑 Adding execute permission to pre-push hook..."
    chmod +x "$PRE_PUSH_HOOK"
fi

# Gitフックパスの設定
echo "⚙️  Configuring Git hooks path..."
git config core.hooksPath .githooks

# 設定確認
CONFIGURED_PATH=$(git config core.hooksPath)
echo "✅ Git hooks path configured: $CONFIGURED_PATH"

# プロジェクトディレクトリの存在確認
PROJECT_DIR="$REPO_ROOT/get_github_coderabbit_review"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

# テストファイルの存在確認
TEST_FILE="$PROJECT_DIR/tests/pr38/test_pr38_final.py"
if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Test file not found: $TEST_FILE"
    exit 1
fi

echo "🧪 Testing pre-push hook with dummy data..."

# ダミーデータでフックをテスト
cd "$REPO_ROOT"
echo "refs/heads/dummy 0000000000000000000000000000000000000000 refs/heads/dummy $(git rev-parse HEAD)" | "$PRE_PUSH_HOOK" origin https://example.com/repo.git

echo ""
echo "🎉 Git hooks setup completed successfully!"
echo ""
echo "📋 Usage:"
echo "  Normal push:  git push origin branch-name"
echo "  Quick test:   QUICK_TEST=true git push origin branch-name"
echo "  Skip hook:    git push --no-verify origin branch-name"
echo ""
echo "📚 For more information, see .githooks/README.md"
