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
        pr_data_path = base_dir / 'pr_104_raw_data.json'
        with open(pr_data_path, 'r', encoding='utf-8') as f:
            pr_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading pr_data from {pr_data_path}: {e}")
        return

    try:
        inline_comments_path = base_dir / 'pr_104_inline_comments.json'
        with open(inline_comments_path, 'r', encoding='utf-8') as f:
            inline_comments = json.load(f)
    except Exception as e:
        print(f"❌ Error reading inline_comments from {inline_comments_path}: {e}")
        inline_comments = []

    try:
        reviews_path = base_dir / 'pr_104_reviews.json'
        with open(reviews_path, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
    except Exception as e:
        print(f"❌ Error reading reviews from {reviews_path}: {e}")
        reviews = []

    # AIエージェント向けの構造化データを作成
    structured_data = {
        'metadata': {
            'pull_request_number': pr_data.get('number'),
            'title': pr_data.get('title'),
            'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_inline_comments': len(inline_comments),
            'total_reviews': len(reviews),
            'data_sources': ['pr_data', 'inline_comments', 'reviews'],
            'processing_script': 'process_pr_comments.py'
        },
        'pull_request_info': {
            'number': pr_data.get('number'),
            'title': pr_data.get('title'),
            'body': pr_data.get('body', '')[:500] + ('...' if len(pr_data.get('body', '')) > 500 else '')
        },
        'inline_comments': [],
        'review_comments': [],
        'actionable_items': [],
        'coderabbit_analysis': {
            'total_coderabbit_comments': 0,
            'actionable_count': 0,
            'file_coverage': []
        }
    }

    # インラインコメントを処理
    coderabbit_count = 0
    files_mentioned = set()

    for comment in inline_comments:
        user_login = comment.get('user', {}).get('login', '')
        is_coderabbit = 'coderabbit' in user_login.lower()

        if is_coderabbit:
            coderabbit_count += 1

        file_path = comment.get('path')
        if file_path:
            files_mentioned.add(file_path)

        structured_comment = {
            'id': comment.get('id'),
            'user': user_login,
            'created_at': comment.get('created_at'),
            'updated_at': comment.get('updated_at'),
            'body': comment.get('body', ''),
            'path': file_path,
            'line': comment.get('line'),
            'start_line': comment.get('start_line'),
            'side': comment.get('side'),
            'position': comment.get('position'),
            'commit_id': comment.get('commit_id'),
            'in_reply_to_id': comment.get('in_reply_to_id'),
            'is_coderabbit': is_coderabbit,
            'body_length': len(comment.get('body', '')),
            'has_suggestions': '```suggestion' in comment.get('body', '').lower()
        }
        structured_data['inline_comments'].append(structured_comment)

    # レビューコメントを処理
    for review in reviews:
        user_login = review.get('user', {}).get('login', '')
        is_coderabbit = 'coderabbit' in user_login.lower()

        structured_review = {
            'id': review.get('id'),
            'user': user_login,
            'state': review.get('state'),
            'body': review.get('body', ''),
            'submitted_at': review.get('submitted_at'),
            'commit_id': review.get('commit_id'),
            'is_coderabbit': is_coderabbit,
            'body_length': len(review.get('body', ''))
        }
        structured_data['review_comments'].append(structured_review)

    # レビューコメント由来のCodeRabbit件数も加算
    coderabbit_count += sum(
        1
        for r in reviews
        if 'coderabbit' in r.get('user', {}).get('login', '').lower()
    )

    # アクショナブルアイテムを抽出（CodeRabbitコメント中心）
    actionable_count = 0
    actionable_keywords = [
        '⚠️ Potential issue',
        '🛠️ Refactor suggestion',
        '📝 Committable suggestion',
        '🤖 Prompt for AI Agents',
        'Consider',
        'Suggestion:',
        'Issue:',
        'Problem:',
        'Warning:',
        'Error:'
    ]

    for comment in inline_comments:
        user_login = comment.get('user', {}).get('login', '')
        if 'coderabbit' in user_login.lower():
            body = comment.get('body', '')

            for keyword in actionable_keywords:
                if keyword.lower() in body.lower():
                    actionable_count += 1
                    structured_data['actionable_items'].append({
                        'comment_id': comment.get('id'),
                        'type': keyword,
                        'file': comment.get('path'),
                        'line': comment.get('line'),
                        'user': user_login,
                        'created_at': comment.get('created_at'),
                        'content_preview': body[:200] + ('...' if len(body) > 200 else ''),
                        'full_content': body,
                        'priority': 'high' if keyword in ['⚠️ Potential issue', 'Error:', 'Warning:'] else 'medium'
                    })
                    break

    # CodeRabbit分析サマリーを更新
    structured_data['coderabbit_analysis']['total_coderabbit_comments'] = coderabbit_count
    structured_data['coderabbit_analysis']['actionable_count'] = actionable_count
    structured_data['coderabbit_analysis']['file_coverage'] = list(files_mentioned)

    # ファイルに出力
    output_file = base_dir / 'pr_104_ai_friendly_comments.json'
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)

        print(f'✅ AI-friendly output generated: {output_file}')
        print('📊 Summary:')
        print(f'  - Total inline comments: {len(inline_comments)}')
        print(f'  - Total reviews: {len(reviews)}')
        print(f'  - CodeRabbit comments: {coderabbit_count}')
        print(f'  - Actionable items found: {actionable_count}')
        print(f'  - Files with comments: {len(files_mentioned)}')

        # 簡易的な分析レポートも生成
        report_file = base_dir / 'pr_104_analysis_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"""# PR #104 コメント分析レポート

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
""")
            for file_path in sorted(files_mentioned):
                file_comment_count = sum(1 for c in inline_comments if c.get('path') == file_path)
                f.write(f"- `{file_path}`: {file_comment_count}件\n")

            f.write(f"""
## データファイル
- **構造化データ**: `{output_file}`
- **元データ**: `pr_104_raw_data.json`, `pr_104_inline_comments.json`, `pr_104_reviews.json`

## AIエージェント向け情報
このデータはAIエージェントが以下の用途で活用できます：
1. CodeRabbitコメントの自動分析
2. アクショナブルアイテムの優先度付け
3. ファイル別のレビュー密度分析
4. 修正提案の自動生成
""")

        print(f'📄 Analysis report generated: {report_file}')

    except Exception as e:
        print(f"❌ Error writing output files: {e}")

if __name__ == "__main__":
    process_pr_comments()
