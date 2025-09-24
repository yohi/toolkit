# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このプロジェクトは、GitHubのプルリクエストからCodeRabbitのコメントを取得・分析し、複数の形式で出力するプロフェッショナルなツールです。AIエージェント最適化とClaude 4のベストプラクティスに準拠しています。

## 開発コマンド

### インストール・セットアップ
```bash
# 開発環境のセットアップ
make setup-dev

# 開発依存関係を含むインストール
make install-dev

# すべての依存関係を含むインストール
make install-full
```

### テスト実行
```bash
# 全テスト実行
make test
python tests/test_runner.py --type all

# テストタイプ別実行
make test-unit                              # 単体テスト
make test-integration                       # 統合テスト
make test-performance                       # パフォーマンステスト
python tests/test_runner.py --type unit    # カスタムランナーで単体テスト

# カバレッジ付きテスト
make coverage
python tests/test_runner.py --coverage
```

### コード品質チェック
```bash
# リント・型チェック
make lint          # ruff + mypy
make type-check    # mypy のみ

# コードフォーマット
make format        # black + isort
make lint-fix      # 自動修正可能な問題を修正
```

### ビルド・パッケージ管理
```bash
# パッケージビルド
make build         # ホイール + ソース配布物
make build-wheel   # ホイールのみ
make build-sdist   # ソース配布物のみ

# uvx互換性テスト（重要）
make uvx-test
make uvx-install-test
```

### デバッグ・開発時の実行
```bash
# デバッグモードでの実行
uvx --from . -n crf https://github.com/owner/repo/pull/123 --debug

# quietモード（AI最適化出力）
uvx --from . -n crf https://github.com/owner/repo/pull/123 --quiet

# 統計情報付き実行
uvx --from . -n crf https://github.com/owner/repo/pull/123 --show-stats
```

### その他開発コマンド
```bash
# プリコミットフック
make pre-commit-install
make pre-commit

# クリーンアップ
make clean

# プロジェクト統計
make stats
```

## アーキテクチャ構造

### コアコンポーネント

1. **Orchestrator (`orchestrator.py`)**
   - メインワークフローの制御
   - `ExecutionConfig`でパラメータ管理
   - `ExecutionMetrics`でパフォーマンス測定

2. **GitHub統合 (`github_client.py`)**
   - GitHub CLIを使用した安全なAPI アクセス
   - プルリクエストとコメントデータの取得
   - 認証はGitHub CLIに依存（トークン保存なし）

3. **コメント分析 (`comment_analyzer.py`)**
   - CodeRabbitコメントの検出・フィルタリング
   - スレッド処理と時系列解析
   - 解決済みマーカーの管理

4. **パーソナ管理 (`persona_manager.py`)**
   - AIエージェント用のカスタムペルソナファイル
   - Claude 4最適化されたプロンプト生成

5. **フォーマッター (`formatters/`)**
   - Markdown、JSON、PlainTextの出力形式
   - `base_formatter.py`で共通インターフェース定義
   - `markdown_formatter.py`にquietモード（AI最適化出力）機能
   - thread contextsからのactionable item抽出機能

### モデル層 (`models/`)

- `AnalyzedComments`: 分析済みコメントデータ
- `CommentMetadata`: コメントメタデータ
- `ReviewComment`: レビューコメント
- `SummaryComment`: サマリーコメント
- `ThreadContext`: スレッドコンテキスト
- `ActionableComment`: アクション可能コメント

### 例外階層 (`exceptions/`)

包括的な例外ハンドリングシステム：
- `CodeRabbitFetcherError`: ベース例外
- `GitHubAuthenticationError`: 認証関連
- `InvalidPRUrlError`: URL検証関連
- `PersonaFileError`: ペルソナファイル関連
- `CommentAnalysisError`: コメント分析関連

### 処理器 (`processors/`)

- `ReviewProcessor`: レビューコメント処理
- `SummaryProcessor`: サマリー処理
- `ThreadProcessor`: スレッド処理

## 重要な技術仕様

### セキュリティ
- GitHub CLIベースの認証（トークン保存なし）
- コマンドインジェクション防止
- 包括的な入力検証

### パフォーマンス
- 大規模データセット対応（数百コメント）
- ストリーミング処理でメモリ最適化
- 並列処理による高速化
- 指数バックオフ付きリトライ機能

### 多言語対応
- Unicode文字とemoji完全サポート
- 日本語ネイティブサポート
- 混合言語コンテンツ対応

## CLI エントリーポイント

メインエントリーポイントは2つ：
- `coderabbit-fetch` (フルコマンド)
- `crf` (短縮版)

両方とも `coderabbit_fetcher.cli.main:main` を呼び出します。

### 実行方法
```bash
# uvxでの実行（推奨）
uvx --from . -n crf https://github.com/owner/repo/pull/123
uvx --from . -n crf https://github.com/owner/repo/pull/123 --quiet

# インストール後の直接実行
coderabbit-fetch https://github.com/owner/repo/pull/123
crf https://github.com/owner/repo/pull/123 --output-format json
```

## テスト構造

カスタムテストランナー（`tests/test_runner.py`）を使用：
- `tests/unit/`: 単体テスト
- `tests/integration/`: 統合テスト
- `tests/performance/`: パフォーマンステスト
- `tests/fixtures/`: テスト用フィクスチャ

## uvx互換性

このプロジェクトはuvx（uv実行ツール）との互換性が重要な要件です：
- `pyproject.toml`でuvx互換性を明示
- `scripts/test_uvx_installation.py`で互換性テスト
- `make uvx-test`でCI/CDパイプラインに統合

## 品質保証

- Python 3.13+ 専用
- 型ヒントによる型安全性
- 90%以上のテストカバレッジ目標
- black + isort + ruff によるコードフォーマット
- mypy による厳密な型チェック
- pre-commit フックによる品質ゲート

## AI エージェント最適化

Claude 4のベストプラクティスに準拠：
- ペルソナファイルによるカスタマイズ
- "Prompt for AI Agents" セクション抽出
- コンテキスト豊富な分析出力
- 構造化されたJSON出力オプション

### Quietモード機能
- `--quiet`フラグでAI最適化された簡潔な出力
- review_commentsとunresolved_threadsの両方からactionable itemsを抽出
- 優先度ベースの構造化（Critical/Important/Minor）
- 重複排除とノイズフィルタリング機能
- thread contextsからのインライン コメント抽出対応

### 重要な実装詳細
- `MarkdownFormatter._format_quiet_mode()`: quietモードの主要ロジック
- `_extract_actionable_from_thread()`: thread contextsからのitem抽出
- `_clean_file_path()`, `_clean_title()`: データクリーニング機能
- `_is_valid_item()`: アイテム有効性検証とフィルタリング
