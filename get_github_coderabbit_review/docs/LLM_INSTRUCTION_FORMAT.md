# LLM指示プロンプト出力形式仕様

## 概要

CodeRabbit Comment FetcherのLLM指示プロンプト形式（`llm-instruction`）は、GitHub PRのCodeRabbitコメントを解析し、LLM（特にClaude 4）に最適化された構造化指示プロンプトを自動生成します。この形式は規則ベースの分類・優先度付けエンジンを使用して、実行可能なタスクリストとコンテキスト情報を提供します。

## 設計原則

- **Claude 4ベストプラクティス準拠**: Anthropic Claude 4の推奨プロンプト構造に従う
- **トークン効率**: LLM消費に最適化された簡潔で構造化された出力
- **実行指向**: 具体的なアクションアイテムとコード修正提案を重視
- **トレーサビリティ**: コメントIDによる追跡可能性
- **多言語対応**: CodeRabbitコンテンツは元言語保持、指示プロンプトは英語

## 出力構造

### XMLスキーマ

```xml
<?xml version="1.0" encoding="UTF-8"?>
<coderabbit_instructions generated="ISO8601_TIMESTAMP">
  <agent_context>
    <persona language="english">...</persona>
    <capabilities>...</capabilities>
  </agent_context>
  <task_overview>
    <objective>...</objective>
    <statistics>...</statistics>
    <execution_priority>...</execution_priority>
  </task_overview>
  <execution_instructions>
    <primary_tasks>...</primary_tasks>
    <guidance>...</guidance>
  </execution_instructions>
  <context_data>
    <summary_information>...</summary_information>
    <thread_contexts>...</thread_contexts>
  </context_data>
</coderabbit_instructions>
```

## 各セクション詳細

### 1. agent_context

AIエージェント向けのコンテキスト情報を提供します。

```xml
<agent_context>
  <persona language="english">
    # CodeRabbit Analysis Expert Persona
    ## Role Definition
    [専門的なソフトウェア開発者としての役割定義]
    ## Core Competencies
    [コード品質、セキュリティ、パフォーマンス等の専門領域]
    ## Task Instructions
    [具体的なタスク実行手順]
    ## Output Format
    [期待される出力形式の説明]
  </persona>
  <capabilities>
    <capability>Code analysis and review</capability>
    <capability>Issue identification and prioritization</capability>
    <capability>Code generation and modification</capability>
    <capability>Best practice recommendations</capability>
  </capabilities>
</agent_context>
```

**要素説明:**
- `persona`: 英語で記述されたAIエージェント用のペルソナ定義
- `capabilities`: エージェントが持つべき能力のリスト

### 2. task_overview

タスクの概要と統計情報を提供します。

```xml
<task_overview>
  <objective>Analyze CodeRabbit review comments and provide actionable recommendations</objective>
  <statistics>
    <total_comments>1</total_comments>
    <actionable_items>23</actionable_items>
    <high_priority>0</high_priority>
    <files_affected>6</files_affected>
  </statistics>
  <execution_priority>
    <priority_order>HIGH → MEDIUM → LOW</priority_order>
    <parallel_processing>Recommended for independent tasks</parallel_processing>
  </execution_priority>
</task_overview>
```

**統計情報:**
- `total_comments`: 処理されたコメント総数
- `actionable_items`: アクション可能なアイテム数
- `high_priority`: 高優先度アイテム数
- `files_affected`: 影響を受けるファイル数

### 3. execution_instructions

具体的な実行指示とタスクリストです。

```xml
<execution_instructions>
  <primary_tasks>
    <task priority='HIGH|MEDIUM|LOW' comment_id='actionable_N'>
      <description>具体的な問題の説明</description>
      <file>対象ファイルパス</file>
      <line>対象行番号（利用可能な場合）</line>
      <code_suggestion language='言語名'>
        提案されるコード修正
      </code_suggestion>
    </task>
  </primary_tasks>
  <guidance>
    <approach>Address issues systematically by priority level</approach>
    <verification>Test changes thoroughly before finalizing</verification>
    <best_practices>Follow language-specific conventions and patterns</best_practices>
  </guidance>
</execution_instructions>
```

**優先度分類ルール:**
- **HIGH**: セキュリティ、脆弱性、クリティカル、エラー関連
- **MEDIUM**: パフォーマンス、推奨事項、改善提案
- **LOW**: スタイル、フォーマット、軽微な提案、ドキュメント

**task要素:**
- `priority`: 自動分類された優先度
- `comment_id`: 元のCodeRabbitコメント追跡用ID
- `description`: 問題の詳細説明
- `file`: 対象ファイルパス
- `line`: 対象行番号（利用可能な場合）
- `code_suggestion`: AIエージェントからの具体的なコード提案

### 4. context_data

追加のコンテキスト情報とスレッドデータです。

```xml
<context_data>
  <summary_information>
    <summary>
      <content>CodeRabbitサマリーコメント内容</content>
      <walkthrough>変更の概要説明</walkthrough>
    </summary>
  </summary_information>
  <thread_contexts>
    <thread id='THREAD_ID' resolved='true|false'>
      <file_context>対象ファイル</file_context>
      <line_context>対象行</line_context>
      <inline_comments>
        <comment id='COMMENT_ID'>
          <author>コメント作成者</author>
          <content>コメント内容（元言語保持）</content>
          <timestamp>作成日時</timestamp>
        </comment>
      </inline_comments>
      <structured_data>
        {
          "thread_id": "スレッドID",
          "participants": ["参加者リスト"],
          "context_summary": "スレッドの要約"
        }
      </structured_data>
    </thread>
  </thread_contexts>
</context_data>
```

**スレッドコンテキスト:**
- `inline_comments`: CodeRabbitからのインラインコメント（コメントID付き）
- `structured_data`: JSON形式でのスレッド詳細情報

## 使用例

### 基本的な使用方法

```bash
# デフォルト（LLM指示プロンプト形式）
crf https://github.com/owner/repo/pull/123

# 明示的に指定
crf https://github.com/owner/repo/pull/123 --output-format llm-instruction

# ファイルに出力
crf https://github.com/owner/repo/pull/123 --output-file instructions.xml
```

### LLMでの利用例

生成されたXMLプロンプトをClaude等のLLMに入力して、構造化された分析と修正提案を得ることができます：

```
[生成されたXMLプロンプトをLLMに送信]

LLMは以下のような構造化された応答を生成します：
- 🔍 Analysis Summary
- 📋 Detailed Recommendations  
- ⚡ Quick Wins
- 🎯 Next Steps
```

## 技術仕様

### コメントID生成

- **レビューコメント**: `actionable_N` (Nは連番)
- **インラインコメント**: GitHub APIから提供される実際のコメントID
- **スレッド**: GitHub APIから提供される実際のスレッドID

### 文字エンコーディング

- **出力**: UTF-8エンコーディング
- **XML**: XML 1.0標準準拠
- **特殊文字**: XMLエスケープ処理済み

### パフォーマンス特性

- **メモリ効率**: ストリーミング処理でメモリ使用量を最小化
- **処理速度**: 大規模PRでも数秒で処理完了
- **並列化**: 独立タスクの並列実行推奨

## カスタマイズ

### ペルソナファイル

カスタムペルソナファイルを指定して、特定のドメインや要件に特化した指示プロンプトを生成できます：

```bash
crf https://github.com/owner/repo/pull/123 --persona-file custom_persona.txt
```

### 解決済みマーカー

特定の解決済みマーカーを設定して、対応済みコメントを除外できます：

```bash
crf https://github.com/owner/repo/pull/123 --resolved-marker "✅ RESOLVED ✅"
```

## 制限事項

1. **GitHub CLI依存**: GitHub CLIの認証と設定が必要
2. **CodeRabbitコメント**: CodeRabbitによるコメントのみ処理対象
3. **XMLサイズ**: 非常に大きなPRの場合、出力サイズが大きくなる可能性
4. **言語サポート**: コード提案の言語検出は基本的なヒューリスティクス

## トラブルシューティング

### 一般的な問題

1. **空の出力**: PRにCodeRabbitコメントが存在しない
2. **認証エラー**: GitHub CLI認証の確認が必要
3. **大きなファイルサイズ**: `--quiet`オプションで冗長な情報を削減

### デバッグ

```bash
# デバッグモードで実行
crf https://github.com/owner/repo/pull/123 --debug

# 統計情報を表示
crf https://github.com/owner/repo/pull/123 --show-stats
```

## バージョン情報

- **現在のバージョン**: 1.0.0
- **対応Claude版**: Claude 4最適化
- **XML仕様**: XML 1.0
- **文字セット**: UTF-8

---

*このドキュメントは、CodeRabbit Comment Fetcher v1.0.0のLLM指示プロンプト機能について記述しています。*