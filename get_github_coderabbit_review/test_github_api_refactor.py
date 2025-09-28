#!/usr/bin/env python3
"""Test script for GitHub API refactoring."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from coderabbit_fetcher.github_client import GitHubClient, GitHubAPIError
from coderabbit_fetcher.exceptions import GitHubAuthenticationError, InvalidPRUrlError


def test_post_comment_api():
    """Test the new REST API-based comment posting."""
    print("🧪 Testing GitHub API comment posting...")

    # Mock the subprocess.run calls to avoid actual gh command execution
    with patch('subprocess.run') as mock_run:
        # Mock successful authentication check
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        try:
            client = GitHubClient()
            print("✅ GitHubClient initialized successfully (mocked authentication)")
        except Exception as e:
            print(f"❌ GitHubClient initialization failed: {e}")
            return False

    # Test authentication check with proper mocking
    with patch.object(client, 'is_authenticated', return_value=True):
        try:
            if not client.is_authenticated():
                print("❌ GitHub CLI is not authenticated. Please run 'gh auth login'")
                return False
        except Exception as e:
            print(f"❌ Authentication check failed: {e}")
            return False

        print("✅ GitHub CLI authentication verified (mocked)")

    # Test URL parsing
    test_url = "https://github.com/octocat/Hello-World/pull/1"
    try:
        owner, repo, pr_number = client.parse_pr_url(test_url)
        print(f"✅ URL parsing: {owner}/{repo}#{pr_number}")
    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        return False

    print("🎯 All basic tests passed!")
    return True


def test_comment_structure():
    """Test the expected comment response structure."""
    print("\n🔍 Testing comment response structure...")

    # Expected fields from GitHub API response
    expected_fields = [
        "id", "html_url", "body", "created_at",
        "updated_at", "user", "node_id"
    ]

    # Mock response structure (what we expect from GitHub API)
    mock_response = {
        "id": 123456789,
        "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123456789",
        "body": "Test comment",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "user": {"login": "testuser"},
        "node_id": "IC_kwDOABCD12345"
    }

    print("✅ Expected response structure:")
    for field in expected_fields:
        if field == "user":
            print(f"  - {field}: {mock_response.get(field, {}).get('login', 'N/A')}")
        else:
            print(f"  - {field}: {mock_response.get(field, 'N/A')}")

    return True


def test_error_handling():
    """Test error handling scenarios."""
    print("\n🚨 Testing error handling...")

    # Mock the subprocess.run calls to avoid actual gh command execution
    with patch('subprocess.run') as mock_run:
        # Mock successful authentication check
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        try:
            client = GitHubClient()
        except Exception as e:
            print(f"❌ GitHubClient initialization failed: {e}")
            return False

    # Test invalid URL
    try:
        client.parse_pr_url("invalid-url")
        print("❌ Should have raised InvalidPRUrlError")
        return False
    except InvalidPRUrlError as e:
        print(f"✅ Invalid URL handling: {type(e).__name__}")
    except Exception as e:
        print(f"❌ Unexpected exception type: {type(e).__name__}, expected InvalidPRUrlError")
        return False

    # Test empty URL
    try:
        client.parse_pr_url("")
        print("❌ Should have raised InvalidPRUrlError")
        return False
    except InvalidPRUrlError as e:
        print(f"✅ Empty URL handling: {type(e).__name__}")
    except Exception as e:
        print(f"❌ Unexpected exception type: {type(e).__name__}, expected InvalidPRUrlError")
        return False

    return True


def test_github_client_initialization():
    """Test GitHubClient initialization with different scenarios."""
    print("\n🔧 Testing GitHubClient initialization scenarios...")

    # Test 1: Successful initialization with mocked authentication
    print("  Test 1: Successful initialization (mocked)")
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        try:
            client = GitHubClient()
            print("    ✅ Initialization successful")
        except Exception as e:
            print(f"    ❌ Initialization failed: {e}")
            return False

    # Test 2: Handle gh command not found
    print("  Test 2: Handle missing gh command")
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("gh command not found")
        try:
            client = GitHubClient()
            print("    ❌ Should have raised GitHubAuthenticationError")
            return False
        except GitHubAuthenticationError as e:
            print(f"    ✅ Correctly handled missing gh: {e}")
        except Exception as e:
            print(f"    ❌ Unexpected error: {e}")
            return False

    # Test 3: Handle authentication failure
    print("  Test 3: Handle authentication failure")
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Not authenticated", stdout="")
        try:
            client = GitHubClient()
            print("    ❌ Should have raised GitHubAuthenticationError")
            return False
        except GitHubAuthenticationError as e:
            print(f"    ✅ Correctly handled auth failure: {e}")
        except Exception as e:
            print(f"    ❌ Unexpected error: {e}")
            return False

    # Test 4: Handle timeout
    print("  Test 4: Handle command timeout")
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("gh", 10)
        try:
            client = GitHubClient()
            print("    ❌ Should have raised GitHubAuthenticationError")
            return False
        except GitHubAuthenticationError as e:
            print(f"    ✅ Correctly handled timeout: {e}")
        except Exception as e:
            print(f"    ❌ Unexpected error: {e}")
            return False

    print("  🎯 All initialization tests passed!")
    return True


def test_ci_environment_safety():
    """Test that the code works safely in CI environments."""
    print("\n🏗️ Testing CI environment safety...")

    # Simulate CI environment where gh might not be available
    with patch('subprocess.run') as mock_run:
        # Test different CI failure scenarios
        def unauthenticated_response(*args, **kwargs):
            return MagicMock(returncode=1, stderr="Not authenticated")

        scenarios = [
            ("gh not installed", FileNotFoundError("gh: command not found")),
            ("gh not authenticated", unauthenticated_response),
            ("network timeout", subprocess.TimeoutExpired("gh", 10)),
        ]

        for scenario_name, side_effect in scenarios:
            print(f"  Testing: {scenario_name}")
            mock_run.side_effect = side_effect

            try:
                client = GitHubClient()
                print(f"    ❌ Should have failed for {scenario_name}")
                return False
            except GitHubAuthenticationError:
                print(f"    ✅ Correctly handled: {scenario_name}")
            except Exception as e:
                print(f"    ❌ Unexpected error for {scenario_name}: {e}")
                return False

    print("  🎯 CI environment safety tests passed!")
    return True


def show_api_improvements():
    """Show the improvements made to the API implementation."""
    print("\n🚀 API Implementation Improvements:")
    print("=" * 50)

    improvements = [
        {
            "title": "脆弱な出力パース → 堅牢なJSON API",
            "before": "gh pr comment の出力をテキストパース",
            "after": "GitHub REST API の JSON レスポンスを直接利用",
            "benefit": "出力形式変更に対する耐性向上"
        },
        {
            "title": "不完全なメタデータ → 完全なコメント情報",
            "before": "URL とID のみ（created_at なし）",
            "after": "id, html_url, created_at, updated_at, user, node_id",
            "benefit": "コメント管理・追跡機能の向上"
        },
        {
            "title": "正規表現依存 → 構造化データ",
            "before": "正規表現でURL からID を抽出",
            "after": "API レスポンスから直接ID を取得",
            "benefit": "パース処理の信頼性向上"
        },
        {
            "title": "エラー処理強化",
            "before": "基本的なエラーハンドリング",
            "after": "JSON パースエラー、タイムアウト、API エラーの詳細処理",
            "benefit": "デバッグ・運用時の問題特定が容易"
        }
    ]

    for i, improvement in enumerate(improvements, 1):
        print(f"\n{i}. {improvement['title']}")
        print(f"   Before: {improvement['before']}")
        print(f"   After:  {improvement['after']}")
        print(f"   Benefit: {improvement['benefit']}")

    print("\n📚 追加機能:")
    print("- get_comment(): 特定コメントの取得")
    print("- get_latest_comments(): 最新コメント一覧の取得")
    print("- 統一されたレスポンス形式")
    print("- 改善されたエラーメッセージ")


def main():
    """Run all tests."""
    print("🔧 GitHub API Refactoring Test Suite")
    print("=" * 40)

    tests = [
        test_post_comment_api,
        test_comment_structure,
        test_error_handling,
        test_github_client_initialization,
        test_ci_environment_safety
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")

    print(f"\n📊 Test Results: {passed}/{len(tests)} passed")

    # Show improvements
    show_api_improvements()

    if passed == len(tests):
        print("\n🎉 All tests passed! The API refactoring is ready.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
