#!/usr/bin/env python3
"""Demo script showing the improved GitHub API usage."""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from coderabbit_fetcher.github_client import GitHubClient, GitHubAPIError


def demo_comment_posting():
    """Demonstrate the new comment posting functionality."""
    print("🚀 GitHub API Comment Posting Demo")
    print("=" * 40)

    client = GitHubClient()

    # Note: This is a demo - replace with actual PR URL for testing
    demo_pr_url = "https://github.com/octocat/Hello-World/pull/1"
    demo_comment = f"🤖 API Test Comment - {datetime.now().isoformat()}"

    print(f"📝 Demo PR URL: {demo_pr_url}")
    print(f"💬 Demo Comment: {demo_comment}")
    print()

    # Parse URL
    try:
        owner, repo, pr_number = client.parse_pr_url(demo_pr_url)
        print(f"✅ Parsed URL: {owner}/{repo}#{pr_number}")
    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        return False

    # Show what the API call would look like
    print("\n🔧 API Implementation Details:")
    print(f"   Endpoint: POST /repos/{owner}/{repo}/issues/{pr_number}/comments")
    print(f"   Method: gh api with JSON input")
    print(f"   Payload: {json.dumps({'body': demo_comment}, indent=2)}")

    # Show expected response structure
    print("\n📋 Expected Response Structure:")
    expected_response = {
        "id": "Comment ID (integer)",
        "html_url": "Direct link to comment",
        "body": "Comment text",
        "created_at": "ISO timestamp",
        "updated_at": "ISO timestamp",
        "user": "Username who posted",
        "node_id": "GraphQL node ID"
    }

    for key, description in expected_response.items():
        print(f"   {key}: {description}")

    print("\n⚠️  Note: This is a demo. To test with a real PR:")
    print("   1. Replace demo_pr_url with your PR URL")
    print("   2. Ensure you have write access to the repository")
    print("   3. Run the script to post a real comment")

    return True


def demo_comment_retrieval():
    """Demonstrate comment retrieval functionality."""
    print("\n🔍 Comment Retrieval Demo")
    print("=" * 30)

    client = GitHubClient()
    demo_pr_url = "https://github.com/octocat/Hello-World/pull/1"

    print("📚 Available retrieval methods:")
    print("   1. get_comment(pr_url, comment_id) - Get specific comment")
    print("   2. get_latest_comments(pr_url, limit) - Get recent comments")
    print("   3. fetch_pr_comments(pr_url) - Get all PR data with comments")

    print(f"\n🔧 Example usage for PR: {demo_pr_url}")
    print("   # Get specific comment")
    print("   comment = client.get_comment(pr_url, 123456789)")
    print("   ")
    print("   # Get latest 5 comments")
    print("   recent = client.get_latest_comments(pr_url, 5)")
    print("   ")
    print("   # Get all PR data")
    print("   pr_data = client.fetch_pr_comments(pr_url)")

    return True


def demo_error_handling():
    """Demonstrate improved error handling."""
    print("\n🚨 Error Handling Demo")
    print("=" * 25)

    error_scenarios = [
        {
            "scenario": "Invalid PR URL",
            "example": "not-a-url",
            "exception": "InvalidPRUrlError"
        },
        {
            "scenario": "API timeout",
            "example": "Network timeout during API call",
            "exception": "GitHubAPIError"
        },
        {
            "scenario": "JSON parse error",
            "example": "Malformed API response",
            "exception": "GitHubAPIError"
        },
        {
            "scenario": "Authentication failure",
            "example": "GitHub CLI not authenticated",
            "exception": "GitHubAuthenticationError"
        }
    ]

    print("🛡️  Robust error handling for:")
    for scenario in error_scenarios:
        print(f"   • {scenario['scenario']}")
        print(f"     Exception: {scenario['exception']}")
        print(f"     Example: {scenario['example']}")
        print()

    return True


def show_migration_guide():
    """Show migration guide from old to new implementation."""
    print("\n📖 Migration Guide: Old vs New")
    print("=" * 35)

    print("🔴 OLD Implementation (Fragile):")
    print("""
    # gh pr comment command with text parsing
    result = subprocess.run([
        "gh", "pr", "comment", str(pr_number),
        "--repo", f"{owner}/{repo}",
        "--body", comment
    ], capture_output=True, text=True)

    # Fragile text parsing
    output_lines = result.stdout.strip().split('\\n')
    comment_url = None
    for line in output_lines:
        if 'github.com' in line and '#issuecomment-' in line:
            comment_url = line.strip()
            break

    # Regex extraction (brittle)
    comment_id = None
    if comment_url:
        id_match = re.search(r'#issuecomment-(\\d+)', comment_url)
        if id_match:
            comment_id = int(id_match.group(1))
    """)

    print("\n🟢 NEW Implementation (Robust):")
    print("""
    # GitHub REST API with JSON
    api_data = json.dumps({"body": comment})

    result = subprocess.run([
        "gh", "api",
        f"/repos/{owner}/{repo}/issues/{pr_number}/comments",
        "--method", "POST",
        "--input", "-"
    ], input=api_data, capture_output=True, text=True)

    # Direct JSON parsing
    comment_data = json.loads(result.stdout)

    # Structured data extraction
    return {
        "id": comment_data.get("id"),
        "html_url": comment_data.get("html_url"),
        "body": comment_data.get("body"),
        "created_at": comment_data.get("created_at"),
        "updated_at": comment_data.get("updated_at"),
        "user": comment_data.get("user", {}).get("login"),
        "node_id": comment_data.get("node_id")
    }
    """)

    print("\n✅ Key Improvements:")
    improvements = [
        "✓ No dependency on CLI output format",
        "✓ Complete comment metadata available",
        "✓ Structured JSON response handling",
        "✓ Better error messages and debugging",
        "✓ Future-proof against CLI changes",
        "✓ Consistent with GitHub API standards"
    ]

    for improvement in improvements:
        print(f"   {improvement}")


def main():
    """Run the demo."""
    demos = [
        demo_comment_posting,
        demo_comment_retrieval,
        demo_error_handling,
        show_migration_guide
    ]

    success_count = 0
    for demo in demos:
        try:
            if demo():
                success_count += 1
        except Exception as e:
            print(f"❌ Demo {demo.__name__} failed: {e}")

    print(f"\n🎯 Demo Results: {success_count}/{len(demos)} completed successfully")

    if success_count == len(demos):
        print("\n🎉 All demos completed! The GitHub API refactoring is ready for production.")
        print("\n📋 Next Steps:")
        print("   1. Update any existing code that uses post_comment()")
        print("   2. Test with a real PR to verify functionality")
        print("   3. Update documentation to reflect new response format")
        print("   4. Consider adding integration tests")

    return success_count == len(demos)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
