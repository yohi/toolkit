#!/usr/bin/env python3
"""
GitHub PR #104 コメント処理スクリプト
AIエージェント向けに構造化されたコメントデータを生成
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def process_pr_comments():
    """プルリクエストのコメントを処理してAIエージェント向け形式で出力"""

    # スクリプトファイル基準のベースディレクトリを設定
    base_dir = Path(__file__).resolve().parent

    # データファイルを読み込み
    try:
        pr_data_path = base_dir / "pr_104_raw_data.json"
        with open(pr_data_path, "r", encoding="utf-8") as f:
            pr_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ PR data file not found at {pr_data_path}: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in PR data file {pr_data_path}: {e}")
        return
    except OSError as e:
        print(f"❌ I/O error reading PR data file {pr_data_path}: {e}")
        return

    try:
        inline_comments_path = base_dir / "pr_104_inline_comments.json"
        with open(inline_comments_path, "r", encoding="utf-8") as f:
            inline_comments = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Inline comments file not found at {inline_comments_path}: {e}")
        inline_comments = []
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in inline comments file {inline_comments_path}: {e}")
        inline_comments = []
    except OSError as e:
        print(f"❌ I/O error reading inline comments file {inline_comments_path}: {e}")
        inline_comments = []

    try:
        reviews_path = base_dir / "pr_104_reviews.json"
        with open(reviews_path, "r", encoding="utf-8") as f:
            reviews = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ Reviews file not found at {reviews_path}: {e}")
        reviews = []
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in reviews file {reviews_path}: {e}")
        reviews = []
    except OSError as e:
        print(f"❌ I/O error reading reviews file {reviews_path}: {e}")
        reviews = []

    # AIエージェント向けの構造化データを作成
    structured_data = {
        "metadata": {
            "pull_request_number": pr_data.get("number"),
            "title": pr_data.get("title"),
            "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_inline_comments": len(inline_comments),
            "total_reviews": len(reviews),
            "data_sources": ["pr_data", "inline_comments", "reviews"],
            "processing_script": "process_pr_comments.py",
        },
        "pull_request_info": {
            "number": pr_data.get("number"),
            "title": pr_data.get("title"),
            "body": (lambda body: body[:500] + ("..." if len(body) > 500 else ""))(
                pr_data.get("body") or ""
            ),
        },
        "inline_comments": [],
        "review_comments": [],
        "actionable_items": [],
        "coderabbit_analysis": {
            "total_coderabbit_comments": 0,
            "actionable_count": 0,
            "file_coverage": [],
        },
    }

    # インラインコメントを処理
    coderabbit_count = 0
    files_mentioned = set()

    for comment in inline_comments:
        # Safe extraction of user login with None protection
        user_data = comment.get("user") or {}
        user_login = user_data.get("login") or ""

        # Safe extraction of body with None protection
        body_text = comment.get("body") or ""

        is_coderabbit = "coderabbit" in user_login.lower()

        if is_coderabbit:
            coderabbit_count += 1

        file_path = comment.get("path")
        if file_path:
            files_mentioned.add(file_path)

        structured_comment = {
            "id": comment.get("id"),
            "user": user_login,
            "created_at": comment.get("created_at"),
            "updated_at": comment.get("updated_at"),
            "body": body_text,
            "path": file_path,
            "line": comment.get("line"),
            "start_line": comment.get("start_line"),
            "side": comment.get("side"),
            "position": comment.get("position"),
            "commit_id": comment.get("commit_id"),
            "in_reply_to_id": comment.get("in_reply_to_id"),
            "is_coderabbit": is_coderabbit,
            "body_length": len(body_text),
            "has_suggestions": "```suggestion" in body_text.lower(),
        }
        structured_data["inline_comments"].append(structured_comment)

    # レビューコメントを処理
    for review in reviews:
        # Safe extraction with None protection
        user_data = review.get("user") or {}
        user_login = user_data.get("login") or ""
        body = review.get("body") or ""

        is_coderabbit = "coderabbit" in user_login.lower()

        structured_review = {
            "id": review.get("id"),
            "user": user_login,
            "state": review.get("state"),
            "body": body,
            "submitted_at": review.get("submitted_at"),
            "commit_id": review.get("commit_id"),
            "is_coderabbit": is_coderabbit,
            "body_length": len(body),
        }
        structured_data["review_comments"].append(structured_review)

    # レビューコメント由来のCodeRabbit件数も加算
    coderabbit_count += sum(
        1 for r in reviews if "coderabbit" in (r.get("user", {}).get("login") or "").lower()
    )

    # アクショナブルアイテムを抽出（CodeRabbitコメント中心）
    actionable_count = 0
    actionable_keywords = [
        "⚠️ Potential issue",
        "🛠️ Refactor suggestion",
        "📝 Committable suggestion",
        "🤖 Prompt for AI Agents",
        "Consider",
        "Suggestion:",
        "Issue:",
        "Problem:",
        "Warning:",
        "Error:",
    ]

    for comment in inline_comments:
        # Safe extraction with None protection
        user_data = comment.get("user") or {}
        user_login = user_data.get("login") or ""
        body = comment.get("body") or ""

        if "coderabbit" in user_login.lower():
            for keyword in actionable_keywords:
                if keyword.lower() in body.lower():
                    actionable_count += 1
                    structured_data["actionable_items"].append(
                        {
                            "comment_id": comment.get("id"),
                            "type": keyword,
                            "file": comment.get("path"),
                            "line": comment.get("line"),
                            "user": user_login,
                            "created_at": comment.get("created_at"),
                            "content_preview": body[:200] + ("..." if len(body) > 200 else ""),
                            "full_content": body,
                            "priority": (
                                "high"
                                if keyword in ["⚠️ Potential issue", "Error:", "Warning:"]
                                else "medium"
                            ),
                        }
                    )
                    break

    # CodeRabbit分析サマリーを更新
    structured_data["coderabbit_analysis"]["total_coderabbit_comments"] = coderabbit_count
    structured_data["coderabbit_analysis"]["actionable_count"] = actionable_count
    structured_data["coderabbit_analysis"]["file_coverage"] = list(files_mentioned)

    # ファイルに出力
    output_file = base_dir / "pr_104_ai_friendly_comments.json"

    # Create parent directory first
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"❌ Failed to create output directory {output_file.parent}: {e}")
        return

    # Write JSON output with specific error handling
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        print(f"✅ AI-friendly output generated: {output_file}")
    except TypeError as e:
        print(f"❌ JSON encoding error for {output_file}: {e}")
        return
    except OSError as e:
        print(f"❌ I/O error writing JSON file {output_file}: {e}")
        return

    # Print summary (no file I/O, should not fail)
    print("📊 Summary:")
    print(f"  - Total inline comments: {len(inline_comments)}")
    print(f"  - Total reviews: {len(reviews)}")
    print(f"  - CodeRabbit comments: {coderabbit_count}")
    print(f"  - Actionable items found: {actionable_count}")
    print(f"  - Files with comments: {len(files_mentioned)}")

    # Write markdown report with specific error handling
    report_file = base_dir / "pr_104_analysis_report.md"
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(
                f"""# PR #104 コメント分析レポート

## 基本情報
- **PR番号**: {pr_data.get('number')}
- **タイトル**: {pr_data.get('title')}
- **処理日時**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}

## コメント統計
- **総インラインコメント数**: {len(inline_comments)}件
- **総レビュー数**: {len(reviews)}件
- **CodeRabbitコメント数**: {coderabbit_count}件
- **アクショナブルアイテム数**: {actionable_count}件
- **言及ファイル数**: {len(files_mentioned)}件

## ファイル別コメント分布
"""
            )
            for file_path in sorted(files_mentioned):
                file_comment_count = sum(1 for c in inline_comments if c.get("path") == file_path)
                f.write(f"- `{file_path}`: {file_comment_count}件\n")

            f.write(
                f"""
## データファイル
- **構造化データ**: `{output_file.name}`
- **元データ**: `pr_104_raw_data.json`, `pr_104_inline_comments.json`, `pr_104_reviews.json`

## AIエージェント向け情報
このデータはAIエージェントが以下の用途で活用できます：
1. CodeRabbitコメントの自動分析
2. アクショナブルアイテムの優先度付け
3. ファイル別のレビュー密度分析
4. 修正提案の自動生成
"""
            )
        print(f"📄 Analysis report generated: {report_file}")
    except OSError as e:
        print(f"❌ I/O error writing report file {report_file}: {e}")


if __name__ == "__main__":
    process_pr_comments()
