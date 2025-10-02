# LLM指示フォーマット仕様

## 1. 概要

このドキュメントは、CodeRabbitコメントフェッチャーによって生成されるAIエージェント指示プロンプトの最終的な出力フォーマットを定義します。このフォーマットは、GitHub PRデータを、構造化され、機械可読で、AIフレンドリーなプロンプトに決定論的かつルールベースで変換した結果です。

このフォーマットの重要な特徴は、**いかなるLLMも使用せずに**生成されることです。これは、GitHub CLIを介して取得された生データを直接的かつ機械的に構造化したものであり、体系的な分析のためにLLMエージェントによって消費されるように設計されています。

## 2. 設計思想

- **LLMフリーの生成**: このフォーマットは、AIによる要約や分析を生成プロセス自体に介在させず、取得したデータをAIが消費しやすいように構造化した生の表現です。
- **構造による明確さ**: Claudeのベストプラクティスを採用し、XML形式のタグを使用してGitHubからの生のテキストデータに構造を与え、受け取るAIが各情報の役割を容易に解析・理解できるようにします。
- **単一の信頼できる情報源**: プロンプトの動的セクション内のすべてのコンテンツは、GitHub CLIの出力に直接追跡可能であり、データの完全性を保証します。
- **決定論的処理**: ルールベースの分析と検証のための組み込みフレームワークを含みます。

## 3. フォーマット仕様

出力は、XML形式のタグが埋め込まれた単一のMarkdownファイルです。構造は以下の通りです。

```markdown
# CodeRabbit Review Analysis - AI Agent Prompt

<role>
あなたは、コードレビュー、品質改善、セキュリティ脆弱性の特定、パフォーマンス最適化、アーキテクチャ設計、テスト戦略を専門とする10年以上の経験を持つシニアソフトウェアエンジニアです。業界のベストプラクティスに従い、コードの品質、保守性、セキュリティを最優先します。
</role>

<core_principles>
品質、セキュリティ、標準、具体性、影響認識
</core_principles>

<analysis_steps>
1. 問題特定 → 2. 影響評価 → 3. 解決策設計 → 4. 実装計画 → 5. 検証方法
</analysis_steps>

<priority_matrix>
- **Critical**: セキュリティ脆弱性、データ損失リスク、システム障害
- **High**: 機能不全、20%以上のパフォーマンス低下、API変更
- **Medium**: コード品質、保守性、軽微なパフォーマンス問題
- **Low**: スタイル、ドキュメント、非機能的な改善
</priority_matrix>

<impact_scope>
- **System**: 複数のコンポーネントに影響
- **Module**: 単一のモジュール/サービスに影響
- **Function**: 単一の関数/メソッドに影響
- **Line**: 特定の行の変更のみ
</impact_scope>

<pull_request_context>
  <pr_url>{dynamic: PR URL}</pr_url>
  <title>{dynamic: PRタイトル}</title>
  <description>{dynamic: PR説明}</description>
  <branch>{dynamic: ブランチ名}</branch>
  <author>{dynamic: 作成者}</author>
  <summary>
    <files_changed>{dynamic: ファイル数}</files_changed>
    <lines_added>{dynamic: 追加行数}</lines_added>
    <lines_deleted>{dynamic: 削除行数}</lines_deleted>
  </summary>
  <technical_context>
    <repository_type>{dynamic: リポジトリ分類}</repository_type>
    <key_technologies>{dynamic: 技術スタック}</key_technologies>
    <file_extensions>{dynamic: ファイル拡張子}</file_extensions>
    <build_system>{dynamic: ビルドツール}</build_system>
  </technical_context>
  <changed_files>
    <file path="{dynamic: ファイルパス}" additions="{dynamic}" deletions="{dynamic}" />
    ...
  </changed_files>
</pull_request_context>

<coderabbit_review_summary>
  <total_comments>{dynamic: 総コメント数}</total_comments>
  <actionable_comments>{dynamic: Actionableコメント数}</actionable_comments>
  <nitpick_comments>{dynamic: Nitpickコメント数}</nitpick_comments>
  <outside_diff_range_comments>{dynamic: 範囲外コメント数}</outside_diff_range_comments>
</coderabbit_review_summary>

<comment_metadata>
  <primary_issues>{dynamic: 主要な問題カテゴリ}</primary_issues>
  <complexity_level>{dynamic: 複雑度評価}</complexity_level>
  <change_impact_scope>{dynamic: 変更影響範囲}</change_impact_scope>
  <testing_requirements>{dynamic: テスト要件}</testing_requirements>
  <risk_assessment level="{dynamic}" reason="{dynamic}" />
  <estimated_resolution_time_hours description="{dynamic}">{dynamic: 推定解決時間}</estimated_resolution_time_hours>
</comment_metadata>

# Analysis Task

<analysis_requirements>
... (異なるコメントタイプを分析する方法に関する静的な指示) ...
</analysis_requirements>

<output_requirements>
... (AIに要求される出力形式を定義する静的な指示) ...
</output_requirements>

# Special Processing Instructions

<ai_agent_analysis>
... (CodeRabbitのAIプロンプトを評価する方法に関する静的な指示) ...
</ai_agent_analysis>

... (その他の特別な指示) ...

---

# CodeRabbit Comments for Analysis

<review_comments>
  <review_comment type="{string}" file="{string}" lines="{string}">
    <issue_summary>
      {string: コメントの要約}
    </issue_summary>
    <coderabbit_analysis>
      {string: コメント分析の本文}
    </coderabbit_analysis>
    <ai_agent_prompt>
      {string: CodeRabbitからの生のAIプロンプト}
    </ai_agent_prompt>
    <proposed_diff>
      <![CDATA[
{string: diffの内容}
]]>
    </proposed_diff>
  </review_comment>

  <!-- ... さらなるreview_commentブロック ... -->

</review_comments>

---

# Analysis Instructions

<deterministic_processing_framework>
... (キーワード辞書を含む、処理のための静的なルール) ...
</deterministic_processing_framework>

<verification_templates>
... (提案された修正を検証するための静的なテンプレート) ...
</verification_templates>
```

### 3.1. ヘッダーセクション（静的）

- **`<role>`, `<core_principles>`, `<analysis_steps>`, `<priority_matrix>`, `<impact_scope>`**: これらはAIエージェントのペルソナと分析フレームワークを定義する静的なテキストブロックです。すべての生成プロンプトで一貫しています。

### 3.2. コンテキストセクション（動的）

- **`<pull_request_context>`**: 包括的で動的に入力されるPRメタデータを含みます。
- **`<coderabbit_review_summary>`**: コメントタイプに関する機械的にカウントされた統計を提供します。
- **`<comment_metadata>`**: 主要な問題、複雑さ、リスク、時間見積もりなど、レビューのより深いルールベースの分析を提供します。

### 3.3. タスクセクション（静的）

- **`# Analysis Task`**: AI向けの静的な指示を含みます。
  - **`<analysis_requirements>`**: 各コメントタイプに対する分析の深さを定義します。
  - **`<output_requirements>`**: AIから要求される正確な応答形式を指定します。
- **`# Special Processing Instructions`**: ネストされたAIプロンプトやコメントスレッドのような複雑なケースのためのガイダンスを提供します。

### 3.4. コアデータセクション: `<review_comments>`（動的）

これは、構造化されたCodeRabbitレビューコメントを含む主要なデータペイロードです。

- **`<review_comments>`**: ルートコンテナ。
- **`<review_comment>`**: 個別のフィードバックを表します。
    - **`type`属性**: コメントカテゴリ（`Actionable`, `Nitpick`など）。
    - **`file`属性**: 関連するファイルパス。
    - **`lines`属性**: 関連する行番号。
- **`<issue_summary>`**: コメントのタイトル。
- **`<coderabbit_analysis>`**: コメントの詳細な本文。
- **`<ai_agent_prompt>`**: 存在する場合、「Prompt for AI Agents」ブロックの生のテキスト。
- **`<proposed_diff>`**: 提案された変更の差分を含むCDATAブロック。

### 3.5. フッターセクション（静的）

- **`# Analysis Instructions`**: 決定論的な処理のためのフレームワークを含みます。
  - **`<deterministic_processing_framework>`**: 分類のためのキーワード辞書を含む、ルールベースのアルゴリズム。
  - **`<verification_templates>`**: 修正を検証するための特定の手順。

## 4. 結論

このフォーマットは、データ収集/構造化とデータ分析を分離する原則に厳密に従っています。`coderabbit-fetcher`ツールは決定論的なデータ前処理器として機能し、クリーンで構造化され、予測可能な入力を生成します。その後の分析と解釈は、提供された包括的な分析フレームワークに導かれ、このプロンプトを消費するAIエージェントの責任となります。
