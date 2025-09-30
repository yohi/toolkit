"""Mock GitHub CLI responses for testing."""

from typing import Dict, List, Any
import json


# Mock GitHub CLI pull request response
MOCK_GH_PR_RESPONSE = {
    "number": 104,
    "title": "リファクタリング",
    "body": "リファクタリング",
    "state": "open",
    "createdAt": "2025-08-27T17:00:00Z",
    "updatedAt": "2025-08-27T17:30:00Z",
    "author": {
        "login": "developer"
    },
    "repository": {
        "name": "repo",
        "owner": {
            "login": "owner"
        }
    },
    "url": "https://github.com/owner/repo/pull/104",
    "baseRepository": {
        "name": "repo",
        "owner": {
            "login": "owner"
        }
    }
}

# Mock GitHub CLI comments response
MOCK_GH_COMMENTS_RESPONSE = [
    {
        "id": 2304764272,
        "author": {
            "login": "coderabbitai[bot]"
        },
        "body": """_💡 Verification agent_

<details>
<summary>🧩 Analysis chain</summary>

**version と updated の情報を現状（2025-08-27）に同期してください。**

- PR 日付（2025-08-27）に対し、`updated: 2024-08-26` は古いです。
- 実装/設定のバージョン（gfp.js / claude_config.json）と `version: 4.2` の整合も確認を。

</details>

**.claude/commands/gfp.md の version と updated をコードに合わせて修正してください**

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In .claude/commands/gfp.md around lines 5 to 7, update the frontmatter to match
the code: change version from 4.2 to 4.0 and set updated to 2025-08-27 so it
matches gfp.js / claude_config.json; save the file with those two fields
adjusted.
```

</details>""",
        "createdAt": "2025-08-27T17:20:22Z",
        "updatedAt": "2025-08-27T17:20:25Z",
        "path": ".claude/commands/gfp.md",
        "line": None,
        "startLine": None,
        "side": "RIGHT",
        "position": 1,
        "commitId": "6714ee424cba179d9289a955109f9e09bd98d42f",
        "pullRequestReviewId": None,
        "inReplyToId": None
    },
    {
        "id": 2304764288,
        "author": {
            "login": "coderabbitai[bot]"
        },
        "body": """_🛠️ Refactor suggestion_

**「完全自動処理」表現を"原則自動（フォールバックあり）"へトーンダウン。**

本文末尾で手動返信フォールバックを明記しているため、冒頭の「完全自動」「ユーザー確認不要」は強すぎます。読者が誤解します。

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In .claude/commands/gfp.md around lines 48-57, the phrase "完全自動処理" and
"ユーザー確認不要、承認プロセス不要" is too strong given the manual fallback later; change the
wording to "原則自動（フォールバックあり）".
```

</details>""",
        "createdAt": "2025-08-27T17:20:23Z",
        "updatedAt": "2025-08-27T17:20:25Z",
        "path": ".claude/commands/gfp.md",
        "line": None,
        "startLine": None,
        "side": "RIGHT",
        "position": 1,
        "commitId": "6714ee424cba179d9289a955109f9e09bd98d42f",
        "pullRequestReviewId": None,
        "inReplyToId": None
    },
    {
        "id": 2304764300,
        "author": {
            "login": "developer"
        },
        "body": "@coderabbitai ありがとうございます。修正します。",
        "createdAt": "2025-08-27T17:21:00Z",
        "updatedAt": "2025-08-27T17:21:00Z",
        "path": ".claude/commands/gfp.md",
        "line": None,
        "startLine": None,
        "side": "RIGHT",
        "position": 1,
        "commitId": "6714ee424cba179d9289a955109f9e09bd98d42f",
        "pullRequestReviewId": None,
        "inReplyToId": 2304764288
    }
]

# Mock GitHub CLI reviews response
MOCK_GH_REVIEWS_RESPONSE = [
    {
        "id": "REV_1",
        "author": {
            "login": "coderabbitai[bot]"
        },
        "state": "COMMENTED",
        "body": """**Actionable comments posted: 26**

> [!TIP]
> Overall code quality has improved significantly. Please address the remaining issues for optimal results.

⚠️ Outside diff range comment (1)

<details>
<summary>⚠️ Outside diff range comments (1)</summary>

`src/config.py` (1)

Line 15: **設定値の検証が不足しています**

環境変数から読み込んだ設定値に対する検証処理が実装されていません。

</details>""",
        "submittedAt": "2025-08-27T17:25:00Z",
        "updatedAt": "2025-08-27T17:25:00Z"
    },
    {
        "id": "REV_2",
        "author": {
            "login": "coderabbitai[bot]"
        },
        "state": "COMMENTED",
        "body": """## Summary by CodeRabbit

## Summary
リファクタリングに関する包括的な改善が実装されました。

## New Features
- 新しいユーティリティ関数の追加
- エラーハンドリングの強化

## Bug Fixes
- データ検証ロジックの修正
- メモリリークの解消

## Documentation
- API仕様書の更新
- README.mdの改善

---
**Actionable comments posted: 26**""",
        "submittedAt": "2025-08-27T17:15:00Z",
        "updatedAt": "2025-08-27T17:15:00Z"
    }
]

# Mock GitHub CLI error responses
MOCK_GH_ERROR_RESPONSES = {
    "authentication_error": {
        "exit_code": 1,
        "stderr": "gh: To use GitHub CLI, please authenticate by running: gh auth login",
        "stdout": ""
    },
    "not_found_error": {
        "exit_code": 1,
        "stderr": "gh: could not find pull request #999 (HTTP 404)",
        "stdout": ""
    },
    "rate_limit_error": {
        "exit_code": 1,
        "stderr": "gh: API rate limit exceeded (HTTP 403)",
        "stdout": ""
    },
    "network_error": {
        "exit_code": 1,
        "stderr": "gh: failed to connect to github.com (network error)",
        "stdout": ""
    },
    "permission_error": {
        "exit_code": 1,
        "stderr": "gh: you do not have permission to access this repository (HTTP 403)",
        "stdout": ""
    },
    "invalid_url_error": {
        "exit_code": 1,
        "stderr": "gh: invalid repository URL format",
        "stdout": ""
    }
}

# Mock rate limit response
MOCK_RATE_LIMIT_RESPONSE = {
    "resources": {
        "core": {
            "limit": 5000,
            "remaining": 4999,
            "reset": 1640995200,
            "used": 1
        },
        "search": {
            "limit": 30,
            "remaining": 30,
            "reset": 1640995200,
            "used": 0
        }
    },
    "rate": {
        "limit": 5000,
        "remaining": 4999,
        "reset": 1640995200,
        "used": 1
    }
}

# Mock successful command responses
MOCK_SUCCESS_RESPONSES = {
    "gh_auth_status": {
        "exit_code": 0,
        "stdout": """github.com
  ✓ Logged in to github.com as username (/home/user/.config/gh/hosts.yml)
  ✓ Git operations for github.com configured to use ssh protocol.
  ✓ Token: gho_xxxxxxxxxxxxxxxxxxxx
  ✓ Token scopes: gist, read:org, repo""",
        "stderr": ""
    },
    "gh_version": {
        "exit_code": 0,
        "stdout": "gh version 2.40.1 (2023-12-13)",
        "stderr": ""
    },
    "gh_pr_view": {
        "exit_code": 0,
        "stdout": json.dumps(MOCK_GH_PR_RESPONSE, indent=2),
        "stderr": ""
    },
    "gh_pr_view_comments": {
        "exit_code": 0,
        "stdout": json.dumps(MOCK_GH_COMMENTS_RESPONSE, indent=2),
        "stderr": ""
    },
    "gh_api_rate_limit": {
        "exit_code": 0,
        "stdout": json.dumps(MOCK_RATE_LIMIT_RESPONSE, indent=2),
        "stderr": ""
    }
}

# Mock scenarios for different PR states
MOCK_PR_SCENARIOS = {
    "open_pr": {
        **MOCK_GH_PR_RESPONSE,
        "state": "open",
        "mergeable": True
    },
    "closed_pr": {
        **MOCK_GH_PR_RESPONSE,
        "state": "closed",
        "merged": False
    },
    "merged_pr": {
        **MOCK_GH_PR_RESPONSE,
        "state": "closed",
        "merged": True
    },
    "draft_pr": {
        **MOCK_GH_PR_RESPONSE,
        "isDraft": True
    }
}

# Mock large dataset response for performance testing
MOCK_LARGE_COMMENTS_RESPONSE = [
    {
        "id": 3000000000 + i,
        "author": {
            "login": "coderabbitai[bot]"
        },
        "body": f"""_{'🛠️ Refactor suggestion' if i % 3 == 0 else '⚠️ Potential issue' if i % 3 == 1 else '📝 Documentation suggestion'}_

Performance test comment #{i + 1}.

This is a longer comment body to simulate real-world scenarios where comments
can contain detailed explanations, code suggestions, and analysis results.

{'<details><summary>🤖 Prompt for AI Agents</summary>AI agent prompt content</details>' if i % 5 == 0 else ''}""",
        "createdAt": f"2025-08-27T{10 + (i % 14):02d}:00:00Z",
        "updatedAt": f"2025-08-27T{10 + (i % 14):02d}:00:05Z",
        "path": f"src/file_{(i % 20) + 1}.py",
        "line": (i % 100) + 1,
        "inReplyToId": None
    }
    for i in range(1000)  # 1000 comments for performance testing
]

# Mock command execution responses for different scenarios
COMMAND_RESPONSES = {
    "normal_execution": MOCK_SUCCESS_RESPONSES,
    "authentication_failure": {
        "gh_auth_status": MOCK_GH_ERROR_RESPONSES["authentication_error"]
    },
    "network_issues": {
        "gh_pr_view": MOCK_GH_ERROR_RESPONSES["network_error"]
    },
    "rate_limiting": {
        "gh_pr_view_comments": MOCK_GH_ERROR_RESPONSES["rate_limit_error"]
    },
    "permission_denied": {
        "gh_pr_view": MOCK_GH_ERROR_RESPONSES["permission_error"]
    },
    "invalid_repository": {
        "gh_pr_view": MOCK_GH_ERROR_RESPONSES["not_found_error"]
    }
}

# Mock responses for different comment types and edge cases
MOCK_EDGE_CASE_RESPONSES = {
    "empty_comments": {
        "exit_code": 0,
        "stdout": "[]",
        "stderr": ""
    },
    "malformed_json": {
        "exit_code": 0,
        "stdout": '{"incomplete": json',
        "stderr": ""
    },
    "mixed_comment_types": {
        "exit_code": 0,
        "stdout": json.dumps([
            {
                "id": 1,
                "author": {"login": "coderabbitai[bot]"},
                "body": "CodeRabbit comment",
                "createdAt": "2025-08-27T17:00:00Z"
            },
            {
                "id": 2,
                "author": {"login": "human-reviewer"},
                "body": "Human comment",
                "createdAt": "2025-08-27T17:01:00Z"
            },
            {
                "id": 3,
                "author": {"login": "other-bot[bot]"},
                "body": "Other bot comment",
                "createdAt": "2025-08-27T17:02:00Z"
            }
        ], indent=2),
        "stderr": ""
    }
}

# Helper function to get mock response based on command and scenario
def get_mock_response(command: str, scenario: str = "normal_execution") -> Dict[str, Any]:
    """Get mock response for a given command and scenario.
    
    Args:
        command: The GitHub CLI command (e.g., 'gh_pr_view')
        scenario: The scenario to simulate (e.g., 'normal_execution', 'authentication_failure')
        
    Returns:
        Dictionary containing exit_code, stdout, stderr
    """
    if scenario in COMMAND_RESPONSES:
        responses = COMMAND_RESPONSES[scenario]
        if command in responses:
            return responses[command]
    
    # Default to normal execution
    if command in MOCK_SUCCESS_RESPONSES:
        return MOCK_SUCCESS_RESPONSES[command]
    
    # Fallback for unknown commands
    return {
        "exit_code": 1,
        "stdout": "",
        "stderr": f"gh: unknown command '{command}'"
    }


# Function to generate dynamic mock data
def generate_mock_comments(count: int, comment_type: str = "mixed") -> List[Dict[str, Any]]:
    """Generate a list of mock comments for testing.
    
    Args:
        count: Number of comments to generate
        comment_type: Type of comments ('coderabbit', 'human', 'mixed')
        
    Returns:
        List of mock comment dictionaries
    """
    comments = []
    
    for i in range(count):
        if comment_type == "coderabbit" or (comment_type == "mixed" and i % 2 == 0):
            user = "coderabbitai[bot]"
            body_prefix = "_🛠️ Refactor suggestion_\n\n"
        else:
            user = f"user{i % 10}"
            body_prefix = ""
        
        comment = {
            "id": 5000000000 + i,
            "author": {"login": user},
            "body": f"{body_prefix}Generated comment #{i + 1} for testing purposes.",
            "createdAt": f"2025-08-27T{10 + (i % 14):02d}:{(i % 60):02d}:00Z",
            "updatedAt": f"2025-08-27T{10 + (i % 14):02d}:{(i % 60):02d}:05Z",
            "path": f"src/test_file_{(i % 10) + 1}.py",
            "line": (i % 100) + 1,
            "inReplyToId": None if i % 5 != 0 else (5000000000 + i - 1) if i > 0 else None
        }
        
        comments.append(comment)
    
    return comments
