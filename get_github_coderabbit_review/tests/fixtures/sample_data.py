"""Sample CodeRabbit comment data for testing."""

from typing import Dict, List, Any
from datetime import datetime, timezone


# Sample CodeRabbit comments based on real PR data
SAMPLE_CODERABBIT_COMMENTS = [
    {
        "id": 2304764272,
        "user": "coderabbitai[bot]",
        "created_at": "2025-08-27T17:20:22Z",
        "updated_at": "2025-08-27T17:20:25Z",
        "body": """_💡 Verification agent_

<details>
<summary>🧩 Analysis chain</summary>

**version と updated の情報を現状（2025-08-27）に同期してください。**

- PR 日付（2025-08-27）に対し、`updated: 2024-08-26` は古いです。
- 実装/設定のバージョン（gfp.js / claude_config.json）と `version: 4.2` の整合も確認を。

```diff
-version: 4.2
-created: 2024-08-26
-updated: 2024-08-26
+version: 4.2
+created: 2024-08-26
+updated: 2025-08-27
```

</details>

**.claude/commands/gfp.md の version と updated をコードに合わせて修正してください**

<details>
<summary>📝 Committable suggestion</summary>

```suggestion
version: 4.0
created: 2024-08-26
updated: 2025-08-27
```

</details>

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In .claude/commands/gfp.md around lines 5 to 7, update the frontmatter to match
the code: change version from 4.2 to 4.0 and set updated to 2025-08-27 so it
matches gfp.js / claude_config.json; save the file with those two fields
adjusted.
```

</details>""",
        "path": ".claude/commands/gfp.md",
        "line": None,
        "start_line": None,
        "side": "RIGHT",
        "position": 1,
        "commit_id": "6714ee424cba179d9289a955109f9e09bd98d42f",
        "in_reply_to_id": None,
        "is_coderabbit": True,
        "body_length": 1863,
        "has_suggestions": True
    },
    {
        "id": 2304764288,
        "user": "coderabbitai[bot]",
        "created_at": "2025-08-27T17:20:23Z",
        "updated_at": "2025-08-27T17:20:25Z",
        "body": """_🛠️ Refactor suggestion_

**「完全自動処理」表現を"原則自動（フォールバックあり）"へトーンダウン。**

本文末尾で手動返信フォールバックを明記しているため、冒頭の「完全自動」「ユーザー確認不要」は強すぎます。読者が誤解します。

```diff
-- **完全自動処理**: ユーザー確認不要、承認プロセス不要
+- **原則自動処理**: 通常はユーザー確認不要（API障害時は手動返信フォールバック）
```

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In .claude/commands/gfp.md around lines 48-57, the phrase "完全自動処理" and
"ユーザー確認不要、承認プロセス不要" is too strong given the manual fallback later; change the
wording to "原則自動（フォールバックあり）" and adjust the sub-bullet to something like
"原則自動処理：通常はユーザー確認不要、必要時は手動介入へフォールバック" to accurately reflect behavior.
```

</details>""",
        "path": ".claude/commands/gfp.md",
        "line": None,
        "start_line": None,
        "side": "RIGHT",
        "position": 1,
        "commit_id": "6714ee424cba179d9289a955109f9e09bd98d42f",
        "in_reply_to_id": None,
        "is_coderabbit": True,
        "body_length": 856,
        "has_suggestions": False
    },
    {
        "id": 2304764310,
        "user": "coderabbitai[bot]",
        "created_at": "2025-08-27T17:20:25Z",
        "updated_at": "2025-08-27T17:20:25Z",
        "body": """_⚠️ Potential issue_

**API失敗時の緊急代替手順セクションが重複・長すぎです。**

緊急代替手順（API失敗時の手動返信）が本文全体の25%（1600文字+）を占め、読みにくくなっています。

改善提案：
1. **重要度による並び替え**: 通常フロー → 緊急時対応
2. **簡潔化**: 代替手順を要点のみに
3. **別セクション化**: 詳細は「トラブルシューティング」セクションへ

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In .claude/commands/gfp.md around lines 320-380, the emergency fallback section
for API failures is too long and disrupts the flow; consider moving the detailed
fallback procedures to a separate "Troubleshooting" section at the end, keeping
only a brief mention in the main flow like "API失敗時は手動返信フォールバック（詳細は後述）"
```

</details>""",
        "path": ".claude/commands/gfp.md",
        "line": None,
        "start_line": None,
        "side": "RIGHT",
        "position": 1,
        "commit_id": "6714ee424cba179d9289a955109f9e09bd98d42f",
        "in_reply_to_id": None,
        "is_coderabbit": True,
        "body_length": 743,
        "has_suggestions": False
    }
]

# Sample resolved comments (with resolution markers)
SAMPLE_RESOLVED_COMMENTS = [
    {
        "id": 2304764400,
        "user": "coderabbitai[bot]",
        "created_at": "2025-08-27T17:21:00Z",
        "updated_at": "2025-08-27T17:21:05Z",
        "body": """_📝 Documentation suggestion_

このファイルにはドキュメントコメントがありません。

[CR_RESOLUTION_CONFIRMED:TECHNICAL_ISSUE_RESOLVED]
✅ エンジニアによる技術的検証完了 - CodeRabbitによる解決済みマーク実行可能
[/CR_RESOLUTION_CONFIRMED]""",
        "path": "src/utils/helper.py",
        "line": 1,
        "start_line": None,
        "side": "RIGHT",
        "position": 1,
        "commit_id": "6714ee424cba179d9289a955109f9e09bd98d42f",
        "in_reply_to_id": None,
        "is_coderabbit": True,
        "body_length": 298,
        "has_suggestions": False
    }
]

# Sample thread data (parent-child relationships)
SAMPLE_THREAD_DATA = [
    {
        "id": 2304764500,
        "user": "coderabbitai[bot]",
        "created_at": "2025-08-27T17:22:00Z",
        "updated_at": "2025-08-27T17:22:00Z",
        "body": """_🛠️ Refactor suggestion_

この関数は複雑すぎます。分割を検討してください。""",
        "path": "src/main.py",
        "line": 45,
        "in_reply_to_id": None,
        "is_coderabbit": True
    },
    {
        "id": 2304764501,
        "user": "developer",
        "created_at": "2025-08-27T17:23:00Z",
        "updated_at": "2025-08-27T17:23:00Z",
        "body": "@coderabbitai 具体的にどの部分を分割すべきでしょうか？",
        "path": "src/main.py",
        "line": 45,
        "in_reply_to_id": 2304764500,
        "is_coderabbit": False
    },
    {
        "id": 2304764502,
        "user": "coderabbitai[bot]",
        "created_at": "2025-08-27T17:24:00Z",
        "updated_at": "2025-08-27T17:24:00Z",
        "body": """@developer 以下の部分に分割することを推奨します：

1. データ検証ロジック（行45-60）
2. ビジネスロジック（行61-80）
3. レスポンス生成（行81-95）

各機能を独立した関数にすることで、テストしやすくなります。""",
        "path": "src/main.py",
        "line": 45,
        "in_reply_to_id": 2304764501,
        "is_coderabbit": True
    }
]

# Sample PR data structure
SAMPLE_PR_DATA = {
    "metadata": {
        "pull_request_number": 104,
        "title": "リファクタリング",
        "extraction_timestamp": "2025-08-28T12:14:08.427148",
        "total_inline_comments": 21,
        "total_reviews": 8,
        "data_sources": ["pr_data", "inline_comments", "reviews"],
        "processing_script": "process_pr_comments.py"
    },
    "pull_request_info": {
        "number": 104,
        "title": "リファクタリング",
        "body": "リファクタリング",
        "state": "open",
        "created_at": "2025-08-27T17:00:00Z",
        "updated_at": "2025-08-27T17:30:00Z",
        "author": "developer",
        "repository": "owner/repo"
    },
    "inline_comments": SAMPLE_CODERABBIT_COMMENTS,
    "resolved_comments": SAMPLE_RESOLVED_COMMENTS,
    "thread_data": SAMPLE_THREAD_DATA
}

# Large dataset for performance testing
SAMPLE_LARGE_DATASET = {
    "metadata": {
        "pull_request_number": 999,
        "title": "Large PR with many comments",
        "total_inline_comments": 500,
        "total_reviews": 50
    },
    "inline_comments": [
        {
            "id": 3000000000 + i,
            "user": "coderabbitai[bot]",
            "created_at": f"2025-08-27T{10 + (i % 14):02d}:00:00Z",
            "updated_at": f"2025-08-27T{10 + (i % 14):02d}:00:05Z",
            "body": f"""_{'🛠️ Refactor suggestion' if i % 3 == 0 else '⚠️ Potential issue' if i % 3 == 1 else '📝 Documentation suggestion'}_

Sample comment #{i + 1} for performance testing.

This is a longer comment body to simulate real-world scenarios where comments
can contain detailed explanations, code suggestions, and analysis results.

{'<details><summary>🤖 Prompt for AI Agents</summary>AI agent prompt content</details>' if i % 5 == 0 else ''}""",
            "path": f"src/file_{(i % 20) + 1}.py",
            "line": (i % 100) + 1,
            "in_reply_to_id": None,
            "is_coderabbit": True,
            "body_length": 200 + (i % 300)
        }
        for i in range(500)
    ]
}

# Sample summary comment from CodeRabbit
SAMPLE_SUMMARY_COMMENT = {
    "id": 2304764000,
    "user": "coderabbitai[bot]",
    "created_at": "2025-08-27T17:15:00Z",
    "body": """## Summary by CodeRabbit

## Summary
リファクタリングに関する包括的な改善が実装されました。コードの可読性、保守性、および文書化が大幅に向上しています。

## New Features
- 新しいユーティリティ関数の追加
- エラーハンドリングの強化
- ログ機能の改善

## Bug Fixes
- データ検証ロジックの修正
- メモリリークの解消
- 並行処理の問題解決

## Documentation
- API仕様書の更新
- README.mdの改善
- コメントの追加と修正

## Tests
- 単体テストの追加
- 統合テストの強化
- カバレッジの向上

## Chores
- 依存関係の更新
- ビルド設定の最適化
- CI/CDパイプラインの改善

---
**Actionable comments posted: 26**

> [!TIP]
> 変更の詳細な分析結果を確認し、品質向上のための提案を確認してください。

<details>
<summary>📋 Walkthrough</summary>

| Files | Change Summary |
|-------|----------------|
| `.claude/commands/gfp.md` | バージョン情報と自動処理の表現を修正 |
| `src/main.py` | 関数の分割とリファクタリング |
| `src/utils/helper.py` | ユーティリティ関数の追加 |
| `tests/test_main.py` | テストケースの追加と改善 |

</details>

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Main
    participant Utils
    participant DB
    
    User->>Main: リクエスト送信
    Main->>Utils: データ検証
    Utils-->>Main: 検証結果
    Main->>DB: データ保存
    DB-->>Main: 保存結果
    Main-->>User: レスポンス返却
```""",
    "path": None,
    "in_reply_to_id": None,
    "is_coderabbit": True
}

# Sample review comment
SAMPLE_REVIEW_COMMENT = {
    "id": 2304765000,
    "user": "coderabbitai[bot]",
    "created_at": "2025-08-27T17:25:00Z",
    "body": """**Actionable comments posted: 26**

⚠️ Outside diff range comment (1)

<details>
<summary>⚠️ Outside diff range comments (1)</summary>

`src/config.py` (1)

Line 15: **設定値の検証が不足しています**

環境変数から読み込んだ設定値に対する検証処理が実装されていません。
無効な値が設定された場合、実行時エラーの原因となります。

```python
# 推奨される実装
def validate_config(config_dict):
    required_keys = ['API_KEY', 'BASE_URL', 'TIMEOUT']
    for key in required_keys:
        if not config_dict.get(key):
            raise ValueError(f"Required config key missing: {key}")
    return config_dict
```

</details>""",
    "path": None,
    "in_reply_to_id": None,
    "is_coderabbit": True
}

# Different comment types for testing
COMMENT_TYPES_SAMPLES = {
    "potential_issue": {
        "body": "_⚠️ Potential issue_\n\n**セキュリティ上の問題があります。**\n\nSQL インジェクションの脆弱性が検出されました。",
        "type": "potential_issue"
    },
    "refactor_suggestion": {
        "body": "_🛠️ Refactor suggestion_\n\n**コードの改善提案**\n\nこの関数は複雑すぎます。",
        "type": "refactor_suggestion"
    },
    "documentation": {
        "body": "_📝 Documentation suggestion_\n\n**ドキュメントの改善**\n\nこの関数にはドキュメントコメントがありません。",
        "type": "documentation"
    },
    "verification": {
        "body": "_💡 Verification agent_\n\n<details>\n<summary>🧩 Analysis chain</summary>\n\n検証結果の詳細\n\n</details>",
        "type": "verification"
    },
    "with_ai_prompt": {
        "body": """_🛠️ Refactor suggestion_

コードの改善が必要です。

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/main.py around line 45, refactor the function to improve readability
and maintainability by splitting into smaller functions.
```

</details>""",
        "type": "with_ai_prompt"
    }
}

# Edge cases and special scenarios
EDGE_CASE_SAMPLES = {
    "empty_body": {
        "id": 1000001,
        "user": "coderabbitai[bot]",
        "body": "",
        "is_coderabbit": True
    },
    "very_long_body": {
        "id": 1000002,
        "user": "coderabbitai[bot]",
        "body": "A" * 10000,  # 10KB comment
        "is_coderabbit": True
    },
    "special_characters": {
        "id": 1000003,
        "user": "coderabbitai[bot]",
        "body": "コメント with émojis 🚀 and special chars: <>&\"'",
        "is_coderabbit": True
    },
    "malformed_markdown": {
        "id": 1000004,
        "user": "coderabbitai[bot]",
        "body": "```python\nprint('unclosed code block'\n**bold without closing**\n[link without url]()",
        "is_coderabbit": True
    },
    "non_coderabbit": {
        "id": 1000005,
        "user": "human-reviewer",
        "body": "This is not a CodeRabbit comment",
        "is_coderabbit": False
    },
    "mixed_language": {
        "id": 1000006,
        "user": "coderabbitai[bot]",
        "body": """_🛠️ Refactor suggestion_

これは日本語と英語が混在したコメントです。

This comment contains both Japanese and English text for testing multilingual support.

```python
# Code example with mixed comments
def function_名前():  # 関数名
    return "mixed content"
```""",
        "is_coderabbit": True
    }
}

# Error scenarios for testing
ERROR_SCENARIOS = {
    "invalid_json": '{"incomplete": json',
    "missing_required_fields": {
        "id": 123,
        # missing user, body, etc.
    },
    "invalid_date_format": {
        "id": 123,
        "user": "coderabbitai[bot]",
        "created_at": "invalid-date",
        "body": "test"
    },
    "negative_id": {
        "id": -1,
        "user": "coderabbitai[bot]",
        "body": "test"
    }
}
