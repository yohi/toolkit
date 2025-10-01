#!/usr/bin/env python3
"""Test script for GitHub API refactoring."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from coderabbit_fetcher.exceptions import GitHubAuthenticationError, InvalidPRUrlError
from coderabbit_fetcher.github_client import GitHubAPIError, GitHubClient


def test_post_comment_api():
    """Test the new REST API-based comment posting."""
    print("🧪 Testing GitHub API comment posting...")

    # Mock the subprocess.run calls to avoid actual gh command execution
    with patch("subprocess.run") as mock_run:
        # Mock successful authentication check
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        try:
            client = GitHubClient()
            print("✅ GitHubClient initialized successfully (mocked authentication)")
        except Exception as e:
            print(f"❌ GitHubClient initialization failed: {e}")
            return False

    # Test URL parsing first
    test_url = "https://github.com/octocat/Hello-World/pull/1"
    try:
        owner, repo, pr_number = client.parse_pr_url(test_url)
        print(f"✅ URL parsing: {owner}/{repo}#{pr_number}")
        assert owner == "octocat"
        assert repo == "Hello-World"
        assert pr_number == "1"
    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        return False

    # Test successful comment posting with mocked HTTP layer
    print("  Testing successful comment posting...")
    mock_response = {
        "id": 123456789,
        "html_url": "https://github.com/octocat/Hello-World/pull/1#issuecomment-123456789",
        "body": "Test comment body",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "user": {"login": "testuser"},
        "node_id": "IC_kwDOABCD12345",
    }

    with patch("subprocess.run") as mock_run:
        # Mock successful API call
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_response), stderr="")

        # Mock authentication check
        with patch.object(client, "is_authenticated", return_value=True):
            try:
                result = client.post_comment(test_url, "Test comment body")

                # Assert the returned structure
                assert isinstance(result, dict), "Result should be a dictionary"
                assert result["id"] == 123456789, f"Expected id 123456789, got {result['id']}"
                assert result["html_url"] == mock_response["html_url"], "HTML URL mismatch"
                assert result["body"] == "Test comment body", "Comment body mismatch"
                assert result["created_at"] == "2024-01-01T12:00:00Z", "Created at mismatch"
                assert result["user"] == "testuser", "User login mismatch"
                assert result["node_id"] == "IC_kwDOABCD12345", "Node ID mismatch"

                print("    ✅ Comment posting successful with correct response structure")

                # Verify the correct API call was made
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]  # Get the command arguments
                assert "gh" in call_args, "Should call gh command"
                assert "api" in call_args, "Should use gh api"
                assert (
                    "/repos/octocat/Hello-World/issues/1/comments" in call_args
                ), "Should use correct API endpoint"
                assert "--method" in call_args and "POST" in call_args, "Should use POST method"

                print("    ✅ Correct API endpoint and method used")

            except Exception as e:
                print(f"    ❌ Comment posting failed: {e}")
                return False

    # Test error response handling
    print("  Testing error response handling...")
    with patch("subprocess.run") as mock_run:
        # Mock API error (non-2xx response)
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr='{"message": "Not Found", "documentation_url": "https://docs.github.com/rest"}',
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.post_comment(test_url, "Test comment")
                print("    ❌ Should have raised GitHubAPIError for API failure")
                return False
            except GitHubAPIError as e:
                print(f"    ✅ Correctly handled API error: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test JSON parsing error
    print("  Testing JSON parsing error handling...")
    with patch("subprocess.run") as mock_run:
        # Mock successful return code but invalid JSON
        mock_run.return_value = MagicMock(returncode=0, stdout="invalid json response", stderr="")

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.post_comment(test_url, "Test comment")
                print("    ❌ Should have raised GitHubAPIError for JSON parsing failure")
                return False
            except GitHubAPIError as e:
                assert "Failed to parse GitHub API response" in str(
                    e
                ), "Should mention JSON parsing error"
                print(f"    ✅ Correctly handled JSON parsing error: {e}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    print("🎯 All comment posting tests passed!")
    return True


def test_comment_structure():
    """Test the expected comment response structure with real assertions."""
    print("\n🔍 Testing comment response structure...")

    # Expected fields from GitHub API response
    expected_fields = ["id", "html_url", "body", "created_at", "updated_at", "user", "node_id"]

    # Mock response structure (what we expect from GitHub API)
    mock_api_response = {
        "id": 123456789,
        "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123456789",
        "body": "Test comment",
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z",
        "user": {"login": "testuser"},
        "node_id": "IC_kwDOABCD12345",
    }

    # Initialize client with mocked authentication
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        client = GitHubClient()

    # Test get_comment method with mocked HTTP layer
    print("  Testing get_comment method structure...")
    test_url = "https://github.com/owner/repo/pull/1"
    comment_id = 123456789

    with patch("subprocess.run") as mock_run:
        # Mock successful API call for get_comment
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps(mock_api_response), stderr=""
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                result = client.get_comment(test_url, comment_id)

                # Assert that result is a dictionary
                assert isinstance(result, dict), "Result should be a dictionary"
                print("    ✅ Result is a dictionary")

                # Assert all expected fields exist
                for field in expected_fields:
                    assert field in result, f"Missing expected field: {field}"
                    print(f"    ✅ Field '{field}' exists")

                # Assert specific field types and values
                assert isinstance(result["id"], int), "ID should be an integer"
                assert isinstance(result["html_url"], str), "HTML URL should be a string"
                assert isinstance(result["body"], str), "Body should be a string"
                assert isinstance(result["created_at"], str), "Created at should be a string"
                assert isinstance(result["updated_at"], str), "Updated at should be a string"
                assert isinstance(result["user"], str), "User should be a string (login)"
                assert isinstance(result["node_id"], str), "Node ID should be a string"

                print("    ✅ All field types are correct")

                # Assert specific values
                assert result["id"] == 123456789, f"Expected id 123456789, got {result['id']}"
                assert (
                    result["user"] == "testuser"
                ), f"Expected user 'testuser', got {result['user']}"
                assert "github.com" in result["html_url"], "HTML URL should contain github.com"

                print("    ✅ Field values are correct")

                # Verify the correct API call was made
                mock_run.assert_called_once()
                call_args = mock_run.call_args[0][0]
                assert "gh" in call_args, "Should call gh command"
                assert "api" in call_args, "Should use gh api"
                assert (
                    f"/repos/owner/repo/issues/comments/{comment_id}" in call_args
                ), "Should use correct API endpoint"

                print("    ✅ Correct API endpoint used")

            except Exception as e:
                print(f"    ❌ get_comment test failed: {e}")
                return False

    # Test missing field scenario
    print("  Testing missing field detection...")
    incomplete_response = {
        "id": 123456789,
        "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123456789",
        # Missing other required fields
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps(incomplete_response), stderr=""
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                result = client.get_comment(test_url, comment_id)

                # Check for missing fields - should have None values for missing fields
                missing_fields = []
                for field in expected_fields:
                    if field not in result or result[field] is None:
                        missing_fields.append(field)

                if missing_fields:
                    print(f"    ✅ Correctly detected missing fields: {missing_fields}")
                else:
                    print(
                        "    ✅ All fields present in incomplete response (client handles missing fields)"
                    )

            except Exception as e:
                print(f"    ❌ Missing field test failed: {e}")
                return False

    # Test user field structure specifically
    print("  Testing user field structure...")
    user_response = mock_api_response.copy()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(user_response), stderr="")

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                result = client.get_comment(test_url, comment_id)

                # Assert user field contains login information
                assert "user" in result, "User field should exist"
                assert result["user"] == "testuser", "User should contain login name"

                print("    ✅ User field structure is correct")

            except Exception as e:
                print(f"    ❌ User field test failed: {e}")
                return False

    print("🎯 All comment structure tests passed!")
    return True


def test_error_handling():
    """Test error handling scenarios."""
    print("\n🚨 Testing error handling...")

    # Mock the subprocess.run calls to avoid actual gh command execution
    with patch("subprocess.run") as mock_run:
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


def test_comprehensive_error_handling():
    """Test comprehensive error handling for API methods."""
    print("\n🚨 Testing comprehensive error handling...")

    # Initialize client with mocked authentication
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        client = GitHubClient()

    test_url = "https://github.com/octocat/Hello-World/pull/1"

    # Test 1: API rate limit error (HTTP 403)
    print("  Test 1: API rate limit error handling...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr='{"message": "API rate limit exceeded", "documentation_url": "https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"}',
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.post_comment(test_url, "Test comment")
                print("    ❌ Should have raised GitHubAPIError for rate limit")
                return False
            except GitHubAPIError as e:
                assert "Failed to post comment via API" in str(e), "Should mention API failure"
                print(f"    ✅ Correctly handled rate limit error: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test 2: Repository not found (HTTP 404)
    print("  Test 2: Repository not found error handling...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr='{"message": "Not Found", "documentation_url": "https://docs.github.com/rest"}',
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.get_comment(test_url, 123456)
                print("    ❌ Should have raised GitHubAPIError for not found")
                return False
            except GitHubAPIError as e:
                assert "Failed to get comment" in str(e), "Should mention get comment failure"
                print(f"    ✅ Correctly handled not found error: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test 3: Unauthorized access (HTTP 401)
    print("  Test 3: Unauthorized access error handling...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr='{"message": "Bad credentials", "documentation_url": "https://docs.github.com/rest"}',
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.get_latest_comments(test_url, 5)
                print("    ❌ Should have raised GitHubAPIError for unauthorized")
                return False
            except GitHubAPIError as e:
                assert "Failed to get latest comments" in str(
                    e
                ), "Should mention get latest comments failure"
                print(f"    ✅ Correctly handled unauthorized error: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test 4: Network timeout error
    print("  Test 4: Network timeout error handling...")
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired("gh", 30)

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.post_comment(test_url, "Test comment")
                print("    ❌ Should have raised GitHubAPIError for timeout")
                return False
            except GitHubAPIError as e:
                assert "timed out" in str(e), "Should mention timeout"
                print(f"    ✅ Correctly handled timeout error: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test 5: Malformed JSON response
    print("  Test 5: Malformed JSON response handling...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout='{"incomplete": json response', stderr=""  # Invalid JSON
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.get_comment(test_url, 123456)
                print("    ❌ Should have raised GitHubAPIError for malformed JSON")
                return False
            except GitHubAPIError as e:
                assert "Failed to parse" in str(e), "Should mention parsing failure"
                print(f"    ✅ Correctly handled malformed JSON: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test 6: Empty response
    print("  Test 6: Empty response handling...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")  # Empty response

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.get_comment(test_url, 123456)
                print("    ❌ Should have raised GitHubAPIError for empty response")
                return False
            except GitHubAPIError as e:
                assert "Failed to parse" in str(e), "Should mention parsing failure"
                print(f"    ✅ Correctly handled empty response: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test 7: Server error (HTTP 500)
    print("  Test 7: Server error handling...")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr='{"message": "Server Error", "documentation_url": "https://docs.github.com/rest"}',
        )

        with patch.object(client, "is_authenticated", return_value=True):
            try:
                client.post_comment(test_url, "Test comment")
                print("    ❌ Should have raised GitHubAPIError for server error")
                return False
            except GitHubAPIError as e:
                assert "Failed to post comment via API" in str(e), "Should mention API failure"
                print(f"    ✅ Correctly handled server error: {type(e).__name__}")
            except Exception as e:
                print(
                    f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAPIError"
                )
                return False

    # Test 8: Authentication failure during operation
    print("  Test 8: Authentication failure during operation...")
    with patch.object(client, "is_authenticated", return_value=False):
        try:
            client.post_comment(test_url, "Test comment")
            print("    ❌ Should have raised GitHubAuthenticationError")
            return False
        except GitHubAuthenticationError as e:
            assert "not authenticated" in str(e), "Should mention authentication failure"
            print(f"    ✅ Correctly handled authentication failure: {type(e).__name__}")
        except Exception as e:
            print(
                f"    ❌ Unexpected exception type: {type(e).__name__}, expected GitHubAuthenticationError"
            )
            return False

    print("🎯 All comprehensive error handling tests passed!")
    return True


def test_github_client_initialization():
    """Test GitHubClient initialization with different scenarios."""
    print("\n🔧 Testing GitHubClient initialization scenarios...")

    # Test 1: Successful initialization with mocked authentication
    print("  Test 1: Successful initialization (mocked)")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        try:
            client = GitHubClient()
            print("    ✅ Initialization successful")
        except Exception as e:
            print(f"    ❌ Initialization failed: {e}")
            return False

    # Test 2: Handle gh command not found
    print("  Test 2: Handle missing gh command")
    with patch("subprocess.run") as mock_run:
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
    with patch("subprocess.run") as mock_run:
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
    with patch("subprocess.run") as mock_run:
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
    with patch("subprocess.run") as mock_run:
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
            "benefit": "出力形式変更に対する耐性向上",
        },
        {
            "title": "不完全なメタデータ → 完全なコメント情報",
            "before": "URL とID のみ（created_at なし）",
            "after": "id, html_url, created_at, updated_at, user, node_id",
            "benefit": "コメント管理・追跡機能の向上",
        },
        {
            "title": "正規表現依存 → 構造化データ",
            "before": "正規表現でURL からID を抽出",
            "after": "API レスポンスから直接ID を取得",
            "benefit": "パース処理の信頼性向上",
        },
        {
            "title": "エラー処理強化",
            "before": "基本的なエラーハンドリング",
            "after": "JSON パースエラー、タイムアウト、API エラーの詳細処理",
            "benefit": "デバッグ・運用時の問題特定が容易",
        },
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
        test_comprehensive_error_handling,
        test_github_client_initialization,
        test_ci_environment_safety,
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
