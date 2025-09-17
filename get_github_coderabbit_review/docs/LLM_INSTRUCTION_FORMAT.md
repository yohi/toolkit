# LLM指示フォーマット仕様書 - Claude 4最適化版

## 概要

CodeRabbit Comment FetcherのLLM指示フォーマット（`llm-instruction`）は、**GitHub CLIで取得したPRのCodeRabbitコメントデータを機械的に処理**してClaude 4最適化された構造化指示プロンプトを生成します。この処理は**LLMを一切使用せず**、GitHub APIレスポンスに対する**決定論的なルールベース変換**により、豊富なコンテキスト情報を持つ実行可能なタスクリストを提供し、AnthropicのClaude 4ベストプラクティスに準拠しています。

## 設計原則

### 🔧 機械的処理の制約
- **LLM非使用**: システム内部では一切LLMや機械学習を使用せず、純粋に決定論的処理
- **GitHub CLI依存**: GitHub APIレスポンスをGitHub CLIで取得し、Pythonで機械的に変換
- **ルールベース変換**: 正規表現、文字列操作、条件分岐のみによるデータ変換
- **予測可能性**: 同じ入力に対して常に同じ出力を生成する決定論的システム
- **デバッグ可能性**: 全処理ステップが機械的で追跡・検証が容易

### 🎯 Claude 4ベストプラクティス準拠（出力フォーマット）
- **XML構造化レスポンス**: Claude 4の望ましいレスポンス形式を示すXMLタグの活用
- **明示的な指示**: 動機的コンテキストを含む明確で具体的なタスク定義
- **思考プロセスの組み込み**: 構造化プロンプトによる反省と推論能力のサポート
- **並列処理**: 同時ツール呼び出しに最適化
- **解決志向**: テスト通過より堅牢で汎用的な解決策を重視

### 🚀 パフォーマンス最適化
- **トークン効率**: LLM消費に最適化されたストリームライン出力、不要な詳細の排除
- **実行指向**: 具体的なアクション項目とコード修正提案を優先、メタ分析の最小化
- **追跡可能性**: 説明責任のためのコメントIDベース追跡
- **多言語サポート**: 英語指示フレームワークで元のCodeRabbitコンテンツ言語を保持
- **コンテキスト明確性**: 理解向上のための明示的な動機と目標説明
- **簡潔性**: 要件に必要な最小限の情報のみ含める

## 出力構造（Claude 4最適化）

### Claude 4ベストプラクティスに準拠したXMLスキーマ

```xml
<?xml version="1.0" encoding="UTF-8"?>
<coderabbit_instructions generated="ISO8601_TIMESTAMP">
  <!-- Agent Context: Establishes clear role and capabilities -->
  <agent_context>
    <persona language="english">Your response should be composed of thoughtful, comprehensive analysis in <analysis_sections> tags</persona>
    <thinking_guidance>Leverage interleaved thinking - reflect after each analysis step</thinking_guidance>
    <capabilities>Code analysis, issue prioritization, solution generation</capabilities>
  </agent_context>

  <!-- Task Definition: Explicit instructions with motivational context -->
  <task_overview>
    <objective>Transform CodeRabbit feedback into actionable development improvements</objective>
    <motivation>Enhance code quality, security, and maintainability through systematic review implementation</motivation>
    <execution_approach>Address systematically by priority, invoke relevant tools simultaneously</execution_approach>
    <statistics>Quantified scope and impact metrics</statistics>
  </task_overview>

  <!-- Execution Framework: Structured for parallel processing -->
  <execution_instructions>
    <instruction_format>Tell Claude what to do, not what to avoid</instruction_format>
    <primary_tasks priority_based="true">Concrete, actionable items with context</primary_tasks>
    <solution_requirements>Focus on robust, general solutions for all valid inputs</solution_requirements>
  </execution_instructions>

  <!-- Rich Context: Supporting detailed reasoning -->
  <context_data>
    <coderabbit_analysis>Original CodeRabbit insights preserved</coderabbit_analysis>
    <thread_relationships>Inter-comment dependencies and resolution status</thread_relationships>
    <ai_agent_prompts>Specialized prompts for specific improvements</ai_agent_prompts>
  </context_data>
</coderabbit_instructions>
```

## 各セクション詳細

### 1. agent_context (Claude 4ペルソナフレームワーク)

Claude 4ベストプラクティスに従った明確な役割定義と応答期待値を確立します。

```xml
<agent_context>
  <persona language="english">
    # Senior Software Development Consultant

    ## Role Definition
    You are a seasoned software development consultant specializing in code quality, security, and architectural excellence. Your expertise spans multiple programming languages, frameworks, and industry best practices.

    ## Core Competencies
    - **Code Quality Analysis**: Identify maintainability, readability, and performance issues
    - **Security Assessment**: Detect vulnerabilities and recommend secure coding practices
    - **Architecture Review**: Evaluate design patterns and structural improvements
    - **Best Practice Enforcement**: Ensure adherence to industry standards and conventions

    ## Task Execution Approach
    1. **Systematic Analysis**: Address issues by priority level (HIGH → MEDIUM → LOW)
    2. **Contextual Solutions**: Provide solutions that consider the broader codebase context
    3. **Actionable Recommendations**: Deliver specific, implementable improvements
    4. **Educational Value**: Explain the "why" behind each recommendation

    ## Output Requirements
    Your response should be structured in <analysis_sections> tags with:
    - Clear problem identification
    - Specific solution recommendations
    - Implementation guidance
    - Impact assessment
  </persona>

  <thinking_guidance>
    Use interleaved thinking throughout your analysis:
    - Reflect after examining each code issue
    - Consider relationships between different problems
    - Evaluate solution trade-offs before recommending
    - Think about long-term maintainability implications
  </thinking_guidance>

  <capabilities>
    <capability>Multi-language code analysis and review</capability>
    <capability>Security vulnerability identification</capability>
    <capability>Performance optimization recommendations</capability>
    <capability>Architecture and design pattern evaluation</capability>
    <capability>Best practice enforcement and education</capability>
  </capabilities>
</agent_context>
```

**Claude 4最適化要素:**
- **明確な役割設定**: 専門性と権限を定義
- **動機的コンテキスト**: コード品質改善の重要性を説明
- **明示的出力フォーマット**: レスポンス構造をガイドするXMLタグの使用
- **思考ガイダンス**: 反省と推論を促進
- **解決志向アプローチ**: 堅牢で実装可能な解決策を重視

### 2. task_overview (目標指向プランニング)

動機的コンテキストと実行戦略を含む明示的な目標を提供します。

```xml
<task_overview>
  <objective>Transform CodeRabbit feedback into systematic code quality improvements</objective>

  <motivation>
    Code review feedback represents critical insights for maintaining high-quality, secure, and maintainable software.
    Each recommendation addresses specific technical debt, security concerns, or performance opportunities that directly
    impact user experience and development velocity.
  </motivation>

  <scope_analysis>
    <total_comments>15</total_comments>
    <actionable_items>23</actionable_items>
    <priority_distribution>
      <high_priority>3</high_priority>      <!-- Security, critical errors -->
      <medium_priority>12</medium_priority>  <!-- Performance, best practices -->
      <low_priority>8</low_priority>         <!-- Style, documentation -->
    </priority_distribution>
    <impact_assessment>
      <files_affected>6</files_affected>
      <estimated_effort>2-4 hours</estimated_effort>
      <risk_level>Medium</risk_level>
    </impact_assessment>
  </scope_analysis>

  <execution_strategy>
    <approach>Systematic priority-based implementation with parallel processing for independent tasks</approach>
    <priority_order>HIGH (security/critical) → MEDIUM (performance/practices) → LOW (style/docs)</priority_order>
    <parallel_opportunities>Independent file modifications, documentation updates, test additions</parallel_opportunities>
    <verification_requirements>Test thoroughly, validate security improvements, check performance impact</verification_requirements>
  </execution_strategy>
</task_overview>
```

**強化されたメトリクスとプランニング:**
- **明確な動機**: なぜこれらの問題に対処する必要があるかを説明
- **詳細なスコープ**: 包括的な影響と労力の評価
- **戦略的実行**: 効率的な実装のためのガイダンス
- **並列処理**: Claude 4のマルチツール機能に最適化

### 3. execution_instructions (アクション指向実装)

明確な結果を伴う明示的で具体的な指示に対するClaude 4の選好に構造化されています。

```xml
<execution_instructions>
  <instruction_philosophy>
    <!-- Claude 4 Best Practice: Tell what TO do, not what to avoid -->
    Focus on positive, constructive improvements rather than problem identification alone.
    Each task should provide clear implementation guidance with expected outcomes.
  </instruction_philosophy>

  <primary_tasks parallel_processing="recommended">
    <task priority='HIGH' comment_id='actionable_0' context_strength='0.85' file_impact='0.97'>
      <description>Replace str.format with Template.safe_substitute to prevent KeyError on diffs containing braces</description>
      <file>lazygit-llm/src/base_provider.py</file>
      <line>91-103</line>
      <impact_analysis>
        <problem>Current str.format breaks on JSON/template diffs with {} characters</problem>
        <solution_benefit>Safe handling of arbitrary diff content, backward compatibility maintained</solution_benefit>
        <effort_estimate>15 minutes</effort_estimate>
      </impact_analysis>
      <ai_agent_prompt>
        In lazygit-llm/src/base_provider.py around lines 91 to 103, _format_prompt
        currently uses str.format which breaks on raw `{}` in diffs; change it to use
        string.Template.safe_substitute with a `$diff` placeholder: update the method to
        accept the prompt_template, detect and replace any legacy `{diff}` occurrences
        with `$diff` before creating a string.Template, then call
        safe_substitute({'diff': diff}) to produce the formatted prompt.
      </ai_agent_prompt>
      <verification_steps>
        <step>Test with diffs containing JSON objects with braces</step>
        <step>Verify backward compatibility with existing {diff} templates</step>
        <step>Run unit tests to ensure no regressions</step>
      </verification_steps>
    </task>
  </primary_tasks>

  <implementation_guidance>
    <systematic_approach>
      1. **Priority Execution**: Address HIGH priority items first - they often block other improvements
      2. **Parallel Opportunities**: Independent file changes can be implemented simultaneously
      3. **Context Preservation**: Maintain existing code style and architectural patterns
      4. **Incremental Validation**: Test each change before proceeding to the next
    </systematic_approach>

    <solution_requirements>
      <!-- Claude 4 Best Practice: Focus on robust, general solutions -->
      - Implement solutions that work for all valid inputs, not just test cases
      - Consider edge cases and error handling in all modifications
      - Ensure solutions are maintainable and follow established patterns
      - Document any architectural decisions or trade-offs made
    </solution_requirements>

    <quality_standards>
      <code_quality>Follow existing conventions, maintain readability, add appropriate comments</code_quality>
      <security>Validate all inputs, avoid introduction of new vulnerabilities</security>
      <performance>Consider impact on execution speed and memory usage</performance>
      <maintainability>Write code that future developers can easily understand and modify</maintainability>
    </quality_standards>
  </implementation_guidance>
</execution_instructions>
```

**強化された優先度分類:**
- **HIGH**: セキュリティ脆弱性、重要なエラー、システム安定性の問題
- **MEDIUM**: パフォーマンス最適化、ベストプラクティス遵守、保守性の改善
- **LOW**: コードスタイル、ドキュメント、軽微な改善

**Claude 4最適化機能:**
- **ポジティブ指示フレーミング**: 達成すべきことを強調
- **明示的検証ステップ**: 徹底的なテストアプローチをガイド
- **コンテキスト対応ソリューション**: より広いアーキテクチャの影響を考慮
- **並列処理ガイダンス**: 同時タスク実行に最適化
- **AIエージェントプロンプト**: 複雑な修正のための専用指示

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

## XMLタグ詳細仕様

### 全体構造
```xml
<coderabbit_instructions generated="ISO8601_TIMESTAMP">
  <!-- 全体のコンテナタグ -->
  <!-- 生成日時がISO8601形式で記録される -->
</coderabbit_instructions>
```

### 1. agent_context（エージェントコンテキスト）
Claude 4のペルソナ設定と能力定義を行います。

**主な役割:**
- Claude 4の専門性と権限の明確化
- 分析タスクの実行方針の設定
- 期待される出力形式の指定
- 思考プロセスのガイダンス提供
- 利用可能な能力の一覧化

**構成要素:**
- `persona` (ペルソナ定義)
  - `language`: 出力言語の指定
  - 役割定義: 「Senior Software Development Consultant」としての専門性
  - コアコンピタンシー: コード品質分析、セキュリティ評価、アーキテクチャレビュー、ベストプラクティス管理
  - タスク実行アプローチ: 体系的分析、コンテキストソリューション、実行可能推奨、教育的価値
  - 出力要件: `<analysis_sections>`タグでの構造化レスポンス
- `thinking_guidance` (思考ガイダンス)
  - 交互思考の指示: 各コード問題の検証後の反省
  - 関係性考慮: 異なる問題間の関係性を思考
  - トレードオフ評価: 推奨前の解決策トレードオフを評価
  - 長期影響: 保守性への長期的影響を思考
- `capabilities` (能力一覧)
  - `capability`: 個別能力の列挙
  - 多言語コード分析とレビュー
  - セキュリティ脆弱性の特定
  - パフォーマンス最適化推奨
  - アーキテクチャと設計パターンの評価
  - ベストプラクティスの強制と教育

```xml
<agent_context>
  <persona language="english">
    # Senior Software Development Consultant

    ## Role Definition
    経験豊富なソフトウェア開発コンサルタントとしての役割定義
    コード品質、セキュリティ、アーキテクチャの専門家

    ## Core Competencies
    - **Code Quality Analysis**: 保守性、可読性、パフォーマンス問題の特定
    - **Security Assessment**: 脆弱性の検出と安全なコーディング慣行の推奨
    - **Architecture Review**: 設計パターンと構造改善の評価
    - **Best Practice Enforcement**: 業界標準と規約の遵守確保

    ## Task Execution Approach
    1. **Systematic Analysis**: 優先度レベル別の問題対処（HIGH → MEDIUM → LOW）
    2. **Contextual Solutions**: より広いコードベースコンテキストを考慮した解決策
    3. **Actionable Recommendations**: 具体的で実装可能な改善策の提供
    4. **Educational Value**: 各推奨事項の「なぜ」を説明

    ## Output Requirements
    <analysis_sections>タグで構造化されたレスポンス:
    - 明確な問題特定
    - 具体的な解決策推奨
    - 実装ガイダンス
    - 影響評価
  </persona>

  <thinking_guidance>
    分析全体を通じて交互思考を使用:
    - 各コード問題を検証後の反省
    - 異なる問題間の関係性を考慮
    - 推奨前の解決策トレードオフを評価
    - 長期的な保守性への影響を思考
  </thinking_guidance>

  <capabilities>
    <capability>多言語コード分析とレビュー</capability>
    <capability>セキュリティ脆弱性の特定</capability>
    <capability>パフォーマンス最適化推奨</capability>
    <capability>アーキテクチャと設計パターンの評価</capability>
    <capability>ベストプラクティスの強制と教育</capability>
  </capabilities>
</agent_context>
```

### 2. task_overview（タスク概要）
明確な目標と実行戦略を定義します。

**主な役割:**
- プロジェクトの明確な目標設定
- 作業の動機と重要性の説明
- 定量的なスコープ分析の提供
- 効率的な実行戦略の策定
- リスクと工数の事前評価

**構成要素:**
- `objective` (目標定義)
  - 具体的で測定可能な目標設定
  - CodeRabbitフィードバックの体系的コード品質改善への変換
- `motivation` (動機説明)
  - 作業の重要性とビジネス価値の説明
  - 技術的負債、セキュリティ、パフォーマンスへの影響
  - ユーザーエクスペリエンスと開発速度への直接的影響
- `scope_analysis` (スコープ分析)
  - `total_comments`: 総コメント数
  - `actionable_items`: 実行可能なアイテム数
  - `priority_distribution`: 優先度別分布
    - `high_priority`: セキュリティ、重要なエラー
    - `medium_priority`: パフォーマンス、ベストプラクティス
    - `low_priority`: スタイル、ドキュメント
  - `impact_assessment`: 影響評価
    - `files_affected`: 影響を受けるファイル数
    - `estimated_effort`: 予想作業時間
    - `risk_level`: リスクレベル
- `execution_strategy` (実行戦略)
  - `approach`: 体系的アプローチ方法
  - `priority_order`: 優先度順序 (HIGH → MEDIUM → LOW)
  - `parallel_opportunities`: 並列処理可能なタスク群
  - `verification_requirements`: 検証要件と品質保証手順

```xml
<task_overview>
  <objective>CodeRabbitフィードバックを体系的なコード品質改善に変換</objective>

  <motivation>
    コードレビューフィードバックは、高品質で安全で保守可能なソフトウェアを
    維持するための重要な洞察を表します。各推奨事項は、ユーザーエクスペリエンス
    と開発速度に直接影響する特定の技術的負債、セキュリティ懸念、または
    パフォーマンス機会に対処します。
  </motivation>

  <scope_analysis>
    <total_comments>15</total_comments>
    <actionable_items>23</actionable_items>
    <priority_distribution>
      <high_priority>3</high_priority>      <!-- セキュリティ、重要なエラー -->
      <medium_priority>12</medium_priority>  <!-- パフォーマンス、ベストプラクティス -->
      <low_priority>8</low_priority>         <!-- スタイル、ドキュメント -->
    </priority_distribution>
    <impact_assessment>
      <files_affected>6</files_affected>
      <estimated_effort>2-4時間</estimated_effort>
      <risk_level>Medium</risk_level>
    </impact_assessment>
  </scope_analysis>

  <execution_strategy>
    <approach>独立タスクの並列処理による優先度ベースの体系的実装</approach>
    <priority_order>HIGH（セキュリティ/重要） → MEDIUM（パフォーマンス/慣行） → LOW（スタイル/ドキュメント）</priority_order>
    <parallel_opportunities>独立したファイル修正、ドキュメント更新、テスト追加</parallel_opportunities>
    <verification_requirements>徹底的なテスト、セキュリティ改善の検証、パフォーマンス影響の確認</verification_requirements>
  </execution_strategy>
</task_overview>
```

### 3. execution_instructions（実行指示）
具体的な実装タスクと品質基準を定義します。

**主な役割:**
- Claude 4ベストプラクティスに沿った指示方針の設定
- 優先度付きの具体的タスクの定義
- 実装ガイダンスと品質基準の提示
- 検証手順の明確化
- 並列処理機会の特定

**構成要素:**
- `instruction_philosophy` (指示哲学)
  - Claude 4ベストプラクティス: 「すべきこと」を指示、「避けるべきこと」ではない
  - ポジティブで建設的な改善に焦点
  - 期待される結果と明確な実装ガイダンスの提供
- `primary_tasks` (メインタスク)
  - `parallel_processing`: 並列処理の推奨フラグ
  - `task` (個別タスク)
    - `priority`: 優先度レベル (HIGH/MEDIUM/LOW)
    - `comment_id`: コメント識別子
    - `context_strength`: コンテキストの強度指数 (0.0-1.0)
    - `file_impact`: ファイルへの影響度 (0.0-1.0)
    - `description`: タスクの簡潔な説明
    - `file`: 対象ファイルパス
    - `line`: 対象行番号または範囲
    - `ai_agent_prompt` (AIエージェントプロンプト)
      - 具体的な実装指示とコード修正手順
      - ファイル、行番号、修正内容の詳細
      - 簡潔で実行可能な指示
- `implementation_guidance` (実装ガイダンス)
  - `systematic_approach`: 体系的アプローチ
    - 優先度実行: HIGH優先度項目を最初に対処
    - 並列機会: 独立したファイル変更の同時実装
    - コンテキスト保持: 既存コードスタイルとパターンの維持
    - 段階的検証: 各変更の逐次テスト
  - `solution_requirements`: 解決策要件
    - 全有効入力への対応、テストケースのみではない
    - エッジケースとエラーハンドリングの考慮
    - 保守可能で確立されたパターンへの準拠
    - アーキテクチャ上の決定やトレードオフの文書化
- `quality_standards` (品質基準)
  - `code_quality`: コード品質基準
    - 既存の規約遵守、可読性維持、適切なコメント追加
  - `security`: セキュリティ基準
    - 入力検証、新しい脆弱性の導入回避
  - `performance`: パフォーマンス基準
    - 実行速度とメモリ使用量への影響考慮
  - `maintainability`: 保守性基準
    - 将来の開発者が容易に理解し修正できるコード

```xml
<execution_instructions>
  <instruction_philosophy>
    <!-- Claude 4ベストプラクティス: 避けるべきことではなく、すべきことを指示 -->
    問題特定のみでなく、ポジティブで建設的な改善に焦点を当てる。
    各タスクは期待される結果と明確な実装ガイダンスを提供すべき。
  </instruction_philosophy>

  <primary_tasks parallel_processing="recommended">
      <task comment_id='actionable_0' category='actionable'>
        <description>例外処理でのカスタム例外クラス使用</description>
        <file>lazygit-llm/lazygit_llm/api_providers/__init__.py</file>
        <line>30</line>
        <ai_agent_prompt>
          lazygit-llm/lazygit_llm/api_providers/__init__.pyの30行で、長い例外メッセージを
          カスタム例外クラスに移動する。ProviderNotFoundErrorクラスを定義し、
          ValueErrorの代わりに使用する。
        </ai_agent_prompt>
      </task>
  </primary_tasks>

  <implementation_guidance>
    <systematic_approach>
      1. **優先度実行**: HIGH優先度項目を最初に対処 - 多くの場合他の改善をブロックする
      2. **並列機会**: 独立したファイル変更は同時に実装可能
      3. **コンテキスト保持**: 既存のコードスタイルとアーキテクチャパターンを維持
      4. **段階的検証**: 次に進む前に各変更をテスト
    </systematic_approach>

    <solution_requirements>
      <!-- Claude 4ベストプラクティス: 堅牢で汎用的な解決策に焦点 -->
      - テストケースだけでなく、すべての有効な入力に対して動作する解決策を実装
      - すべての修正でエッジケースとエラーハンドリングを考慮
      - 解決策が保守可能で確立されたパターンに従うことを確保
      - アーキテクチャ上の決定やトレードオフを文書化
    </solution_requirements>

    <quality_standards>
      <code_quality>既存の規約に従い、可読性を維持し、適切なコメントを追加</code_quality>
      <security>すべての入力を検証し、新しい脆弱性の導入を避ける</security>
      <performance>実行速度とメモリ使用量への影響を考慮</performance>
      <maintainability>将来の開発者が容易に理解し修正できるコードを記述</maintainability>
    </quality_standards>
  </implementation_guidance>
</execution_instructions>
```

### 4. context_data（コンテキストデータ）
追加のコンテキスト情報とスレッドデータを提供します。

**主な役割:**
- 元のCodeRabbitデータの完全保持
- スレッド構造と時系列情報の維持
- コメント間の関係性の明示
- 解決状況の追跡
- 元言語でのコンテンツ保存

**構成要素:**
- `summary_information` (サマリー情報)
  - `summary` (サマリーコメント)
    - `content`: CodeRabbitサマリーコメントの完全な内容
    - `walkthrough`: 変更の詳細な概要説明とプルリクエストの目的
- `thread_contexts` (スレッドコンテキスト)
  - `thread` (個別スレッド)
    - `id`: 一意のスレッド識別子
    - `resolved`: 解決状況フラグ (true/false)
    - `file_context`: 対象ファイルパス
    - `line_context`: 対象行番号または範囲
    - `inline_comments` (インラインコメント)
      - `comment` (個別コメント)
        - `id`: コメント識別子 (GitHub API由来)
        - `author`: コメント作成者 (通常は"coderabbitai[bot]")
        - `content`: コメント内容（元言語保持）
        - `timestamp`: 作成日時 (ISO8601形式)
    - `structured_data` (構造化データ)
      - JSON形式でのスレッド詳細情報
      - `thread_id`: スレッド識別子
      - `participants`: 参加者リスト配列
      - `context_summary`: スレッドの要約と関連情報
      - `resolution_status`: 解決状況 ("resolved"/"unresolved")
      - `last_activity`: 最終活動日時

```xml
<context_data>
  <summary_information>
    <summary>
      <content>CodeRabbitサマリーコメントの完全な内容</content>
      <walkthrough>変更の詳細な概要説明とプルリクエストの目的</walkthrough>
    </summary>
  </summary_information>

  <thread_contexts>
    <thread id='unique_thread_identifier' resolved='true|false'>
      <file_context>src/main.py</file_context>
      <line_context>42-58</line_context>

      <inline_comments>
        <comment id='issue_comment_123456789'>
          <author>coderabbitai[bot]</author>
          <content>Consider using typing.Protocol for better type safety</content>
          <timestamp>2024-01-15T10:30:00Z</timestamp>
        </comment>
      </inline_comments>

      <structured_data>
        {
          "thread_id": "thread_abc123",
          "participants": ["coderabbitai[bot]", "developer_username"],
          "context_summary": "型安全性に関する議論とProtocolの使用提案",
          "resolution_status": "unresolved",
          "last_activity": "2024-01-15T10:30:00Z"
        }
      </structured_data>
    </thread>
  </thread_contexts>
</context_data>
```

### 5. Claude 4レスポンス用タグ（期待される出力構造）
Claude 4が生成すべきレスポンスの構造を定義します。

**主な役割:**
- Claude 4の出力形式の統一
- 分析結果の体系化
- 実装可能な推奨事項の提供
- 影響評価の明確化
- 検証計画の具体化

**構成要素:**
- `priority_assessment` (優先度評価)
  - HIGH優先度の確認: セキュリティ脆弱性、重要なエラーの特定
  - MEDIUM優先度の評価: 例外名の競合、インポート組織等
  - LOW優先度の確認: ドキュメントフォーマット、スタイル一貫性
  - 優先度再評価と確認の理由説明
- `implementation_strategy` (実装戦略)
  - 重要なセキュリティ修正の優先対処
  - 独立したファイル変更の並列実装計画
  - 各修正グループ後の体系的テスト方針
  - リスク管理とロールバック計画
- `code_solutions` (コード解決策)
  - 説明付きの詳細なコード修正内容
  - 具体的な実装手順とコード例
  - 変更の理由と期待される効果の説明
  - エッジケースや例外ケースへの対処方法
- `verification_plan` (検証計画)
  - 包括的なテストアプローチの詳細
  - 単体テスト、統合テスト、手動検証手順
  - リグレッション防止策と品質ゲート
  - パフォーマンスとセキュリティの検証方法
- `impact_summary` (影響要約)
  - セキュリティ: 脆弱性の排除とリスク軽減
  - 保守性: エラーハンドリングとコード組織の改善
  - 開発速度: クリーンなコードベース、技術的負債の削減
  - パフォーマンス: 実行速度やメモリ使用量への影響
  - リスク評価: 潜在的な影響や副作用の明示

```xml
<analysis_sections>
  <priority_assessment>
    確認されたHIGH優先度: _format_promptでのセキュリティテンプレートインジェクション脆弱性
    MEDIUM優先度: 例外名の競合、インポート組織
    LOW優先度: ドキュメントフォーマット、スタイル一貫性
  </priority_assessment>

  <implementation_strategy>
    1. テンプレートインジェクションを最初に対処 - 重要なセキュリティ修正
    2. 独立したファイル変更の並列実装
    3. 各修正グループ後の体系的テスト
  </implementation_strategy>

  <code_solutions>
    [説明付きの詳細なコード修正]
    具体的な実装手順とコード例
    変更の理由と期待される効果
  </code_solutions>

  <verification_plan>
    [包括的なテストアプローチ]
    単体テスト、統合テスト、手動検証手順
    リグレッション防止策
  </verification_plan>

  <impact_summary>
    セキュリティ: テンプレートインジェクション脆弱性の排除
    保守性: エラーハンドリングとコード組織の改善
    開発速度: よりクリーンなコードベース、技術的負債の削減
  </impact_summary>
</analysis_sections>
```

### タグの役割と相互関係

**情報フロー:**
1. **agent_context** → Claude 4の専門性と分析手法を確立
2. **task_overview** → 全体目標と戦略的アプローチを設定
3. **execution_instructions** → 具体的な実装タスクと品質基準を提供
4. **context_data** → 元データと関係性情報を保持
5. **analysis_sections** → 構造化された出力形式を指定

**相互連携の特徴:**
- **一貫性**: 全タグでClaude 4ベストプラクティスを適用
- **階層性**: 抽象的な目標から具体的な実装まで段階的に詳細化
- **完全性**: CodeRabbitデータの情報損失なし
- **実行性**: 並列処理と検証を考慮した実装指針
- **追跡性**: コメントIDと優先度による明確な管理

**最適化のポイント:**
- **トークン効率**: 冗長性を排除した簡潔な表現
- **処理速度**: Claude 4の並列ツール実行能力を活用
- **品質保証**: 体系的な検証プロセスの組み込み
- **保守性**: 将来の機能拡張に対応する柔軟な構造

これらのタグは相互に連携し、CodeRabbitのフィードバックをClaude 4が効率的に処理できる包括的な指示システムを形成します。

## Claude 4統合での使用例

### 基本的な使用方法

```bash
# Generate Claude 4-optimized instruction format (default)
crf https://github.com/yohi/lazygit-llm-commit-generator/pull/2

# Explicit format specification
crf https://github.com/owner/repo/pull/123 --output-format llm-instruction

# Save to file for Claude 4 analysis
crf https://github.com/owner/repo/pull/123 --output-file claude_instructions.xml

# Quiet mode for AI-optimized output
crf https://github.com/owner/repo/pull/123 --quiet
```

### Claude 4統合ワークフロー

**ステップ1: 指示プロンプトの生成**
```bash
crf https://github.com/yohi/lazygit-llm-commit-generator/pull/2 --output-file pr_analysis.xml
```

**ステップ2: Claude 4分析**
生成されたXMLを以下のメタプロンプトと共にClaude 4に送信します:

```
以下のXMLで提供されるCodeRabbitフィードバックを分析してください。構造化された
指示とペルソナガイダンスに従って、包括的なコード改善推奨事項を提供してください。

<analysis_sections>タグを使用してレスポンスを以下のように構造化してください:
1. <priority_assessment> - タスクの優先度を評価・確認
2. <implementation_strategy> - 問題への対処の詳細なアプローチ
3. <code_solutions> - 説明付きの具体的なコード修正
4. <verification_plan> - テストと検証のステップ
5. <impact_summary> - 期待される利益と潜在的リスク

[生成されたXMLをここに貼り付け]
```

**ステップ3: 期待されるClaude 4レスポンス構造**

```xml
<analysis_sections>
  <priority_assessment>
    Confirmed HIGH priority: Security template injection vulnerability in _format_prompt
    MEDIUM priorities: Exception naming conflicts, import organization
    LOW priorities: Documentation formatting, style consistency
  </priority_assessment>

  <implementation_strategy>
    1. Address template injection first - critical security fix
    2. Parallel implementation of independent file changes
    3. Systematic testing after each modification group
  </implementation_strategy>

  <code_solutions>
    [Detailed code modifications with explanations]
  </code_solutions>

  <verification_plan>
    [Comprehensive testing approach]
  </verification_plan>

  <impact_summary>
    Security: Eliminates template injection vulnerability
    Maintainability: Improved error handling and code organization
    Development velocity: Cleaner codebase, reduced technical debt
  </impact_summary>
</analysis_sections>
```

### 実際の例分析

`https://github.com/yohi/lazygit-llm-commit-generator/pull/2`からの実際のCodeRabbitフィードバックに基づいて、生成される指示には以下が含まれます:

- **7つのアクション可能コメント** - 具体的なセキュリティとパフォーマンス改善
- **18のニットピックコメント** - コード品質向上のため
- **AIエージェントプロンプト** - 詳細な実装ガイダンス付き
- **ファイル影響分析** - 9つの修正ファイル全体
- **優先度ベースタスク組織** - 体系的な実装のため

## 技術仕様

### 機械的処理アルゴリズム

**データ取得フロー:**
1. `gh pr view <url> --json comments,reviews` でRAWデータ取得
2. JSON解析によるCodeRabbitコメント抽出（`author.login == "coderabbitai"`）
3. 正規表現による構造化データ抽出（Summary、Actionable、Nitpick等）
4. 条件分岐による優先度分類（HIGH/MEDIUM/LOW）
5. テンプレートベースXML生成

**ルールベース優先度分類:**
- **HIGH**: `security|vulnerability|critical|urgent|breaking` パターンマッチ
- **MEDIUM**: `error|bug|issue|problem|failure|fix` パターンマッチ
- **LOW**: `style|formatting|convention|documentation` パターンマッチ

**決定論的処理:**
- 同一PRに対して常に同一XML出力を生成
- ランダム性や学習による変動は一切なし

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
- **処理速度**: 大規模PRでも数秒で処理完了（GitHub CLI呼び出し時間除く）
- **並列化**: 独立タスクの並列実行推奨（出力XML内での指示）

## 専門用途向けカスタマイズ

### ドメイン固有ペルソナファイル

特定のドメイン、フレームワーク、または組織要件に合わせて生成される指示をカスタマイズします:

```bash
# Security-focused analysis
crf https://github.com/owner/repo/pull/123 --persona-file security_expert.txt

# Performance optimization specialist
crf https://github.com/owner/repo/pull/123 --persona-file performance_tuner.txt

# Architecture review focus
crf https://github.com/owner/repo/pull/123 --persona-file architect.txt
```

**カスタムペルソナの例 (security_expert.txt):**
```
# Security-First Development Consultant

## Specialized Focus
Your analysis should prioritize security implications above all other concerns.
Every recommendation must consider potential attack vectors and defense strategies.

## Security Assessment Framework
1. Input validation and sanitization
2. Authentication and authorization mechanisms
3. Data encryption and secure storage
4. API security and rate limiting
5. Dependency vulnerability assessment

## Output Requirements
Structure your response in <security_analysis> tags with explicit threat modeling.
```

### 高度なフィルタリングオプション

```bash
# Exclude resolved items (supports multiple markers)
crf https://github.com/owner/repo/pull/123 --resolved-marker "✅ Addressed in commit"

# Focus on specific priority levels
crf https://github.com/owner/repo/pull/123 --priority-filter HIGH,MEDIUM

# Include only specific file types
crf https://github.com/owner/repo/pull/123 --file-pattern "*.py,*.js"

# Custom output template
crf https://github.com/owner/repo/pull/123 --template claude4_enhanced.xml
```

### 開発ワークフローとの統合

**プリコミットフック統合:**
```bash
#!/bin/bash
# .git/hooks/pre-commit
if [[ -n "$PR_NUMBER" ]]; then
  crf https://github.com/owner/repo/pull/$PR_NUMBER --quiet > /tmp/coderabbit_analysis.xml
  # Send to Claude 4 for automated analysis
fi
```

**CI/CDパイプライン統合:**
```yaml
# .github/workflows/code-review.yml
name: Automated Code Review Analysis
on: [pull_request]
jobs:
  coderabbit-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate Claude 4 Instructions
        run: |
          crf ${{ github.event.pull_request.html_url }} \
            --output-file claude_instructions.xml \
            --persona-file .github/personas/team_standards.txt
      - name: Archive Analysis
        uses: actions/upload-artifact@v3
        with:
          name: claude-analysis-instructions
          path: claude_instructions.xml
```

## 制限事項

1. **GitHub CLI依存**: GitHub CLIの認証と設定が必要
2. **CodeRabbitコメント**: CodeRabbitによるコメントのみ処理対象
3. **XMLサイズ**: 非常に大きなPRの場合、出力サイズが大きくなる可能性
4. **言語サポート**: コード提案の言語検出は基本的なヒューリスティクス
5. **機械的処理の限界**:
   - 複雑なコンテキスト理解や推論は不可能
   - 正規表現とキーワードマッチのみによる分類
   - CodeRabbitコメントの構造変更に脆弱
   - LLMのような柔軟な解釈は一切不可

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
