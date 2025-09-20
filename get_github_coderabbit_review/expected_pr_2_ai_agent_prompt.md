# CodeRabbit Review Analysis - AI Agent Prompt

<role>
Senior software engineer (10+ years) specializing in code review, security, performance, and architecture. Prioritize quality, maintainability, and security following industry standards.
</role>

<principles>
Quality, Security, Standards, Specificity, Impact-awareness
</principles>

<analysis_steps>
1. Issue identification → 2. Impact assessment → 3. Solution design → 4. Implementation plan → 5. Verification method
</analysis_steps>

<core_principles>
Quality, Security, Standards, Specificity, Impact-awareness
</core_principles>

<analysis_methodology>
1. Issue identification → 2. Impact assessment → 3. Solution design → 4. Implementation plan → 5. Verification method
</analysis_methodology>

<priority_matrix>
- **Critical**: Security vulnerabilities, data loss risks, system failures
- **High**: Functionality breaks, performance degradation >20%, API changes
- **Medium**: Code quality, maintainability, minor performance issues
- **Low**: Style, documentation, non-functional improvements
</priority_matrix>

<impact_scope>
- **System**: Multiple components affected
- **Module**: Single module/service affected
- **Function**: Single function/method affected
- **Line**: Specific line changes only
</impact_scope>

## Pull Request Context

**PR URL**: https://github.com/yohi/lazygit-llm-commit-generator/pull/2
**PR Title**: feat(task-01): Implement project structure and core interfaces
**PR Description**: feat(task-01): Implement project structure and core interfaces
**Branch**: feature/01-task01_project-structure
**Author**: yohi
**Files Changed**: 10 files
**Lines Added**: +836
**Lines Deleted**: -4

### Technical Context
**Repository Type**: Python application
**Key Technologies**: Python 3.13, setuptools, OpenAI/Anthropic APIs, PyYAML
**File Extensions**: .py (Python), .txt (Configuration), .yml (YAML)
**Packaging System**: setuptools

## CodeRabbit Review Summary

**Total Comments**: 87
**Actionable Comments**: 4
**Nitpick Comments**: 82
**Outside Diff Range Comments**: 1

---

# Analysis Task

<execution_guidelines>
**Processing Approach:**
1. **Issue Analysis**: Understand CodeRabbit comments and technical context
2. **Priority Assessment**: Evaluate impact and urgency of each issue
3. **Solution Design**: Propose specific fixes with implementation steps
4. **Quality Assurance**: Ensure changes maintain code quality and functionality
5. **Verification**: Provide testable success criteria

**Output Requirements:**
- Actionable implementation steps
- Clear priority classification
- Specific file and line references
- Testable verification methods

**Success Criteria:**
- All CodeRabbit issues addressed appropriately
- Implementation steps are executable
- Changes preserve existing functionality
- Code quality improvements are measurable
</execution_guidelines>

<comment_metadata>
- **Total Comments**: 87 (4 Actionable, 82 Nitpick, 1 Outside Diff Range)
- **File Types**: Python (.py), Configuration (setup.py, requirements.txt, .yml)
- **Technology Stack**: Python 3.13, setuptools, PyYAML, OpenAI/Anthropic APIs
- **Primary Issues**: Package structure, dependency management, code duplication
- **Complexity Level**: High (project architecture and packaging)
- **Change Impact Scope**: Project structure, dependency resolution, module imports
- **Testing Requirements**: Unit tests, integration tests, packaging verification
</comment_metadata>

Analyze the CodeRabbit comments provided below within the `<review_comments>` block. For each `<review_comment>`, understand the issue, the proposed diff, and the instructions from CodeRabbit. Then, generate a structured response following the format specified in the `<output_requirements>` section.

<thinking_process>
For each comment, follow this step-by-step analysis:
1. **Extract metadata**: file_path, line_range, comment_type from XML attributes
2. **Keyword matching**: Apply static dictionaries to issue description
3. **Count keywords**: Calculate totals per category (security/functionality/quality/style)
4. **Determine priority**: Select highest count category, apply tie-breaking rules
5. **Template application**: Insert extracted data into predefined format
6. **Validation**: Verify all required fields are populated with deterministic values
</thinking_process>

<error_handling>
- **Missing XML attributes**: Use "unknown" as default value
- **Empty code sections**: Mark as "[No code provided]"
- **Keyword count ties**: Apply priority order: security > functionality > quality > style
- **Invalid line ranges**: Use original text as-is
- **Malformed instructions**: Extract available text, mark incomplete sections
</error_handling>

<language_rules>
- **Issue Title**: Japanese (with English technical terms)
- **Analysis Content**: Japanese with detailed explanation (technical terms in English)
- **Code Examples**: English comments, Japanese explanations
- **File/Function Names**: Keep in English
- **Technical Terms**: API, setup.py, requirements.txt, wheel, PyYAML etc. unified in English
- **Consistency**: Same terms unified throughout document
</language_rules>

<output_format>
**Required Output Format** (Must strictly follow the structure below):

## [file_path:line_range] Issue Title

**Root Cause**: [Keyword dictionary matching result - specify detected keywords and count]
**Impact**: [Critical/High/Medium/Low] - [System/Module/Function/Line] [※Automatic determination by keyword count: 5+ → Critical, 3-4 → High, 1-2 → Medium, 0 → Low]
**Type**: [Actionable/Outside Diff Range/Nitpick] [※Mechanically extracted from CodeRabbit comment classification]
**Affected**: [List file paths, function names, module names as strings]

**Solution**:
```language
// Before (Current Issue)
[CodeRabbitコメントのold_codeセクションをそのまま転記]

// After (Proposed Fix)
[CodeRabbitコメントのnew_codeセクションをそのまま転記]
```

**Implementation Steps**:
1. [filename:line_number] Specific change content [Mechanically extracted from comment instructions]
2. [Verification method] [Mechanical check such as command execution]
3. [Test requirements] [Quantitative success criteria]

**Priority**: [Level] - [Keyword dictionary matching result: security_keywords → Critical, functionality_keywords → High, quality_keywords → Medium, style_keywords → Low]
**Timeline**: [immediate/this-sprint/next-release] [※Automatically determined from priority level: Critical → immediate, High → this-sprint, Medium/Low → next-release]

---

**Processing Instructions**:
1. **Process All Comments**: Process all <review_comment> elements in the <review_comments> block sequentially
2. **Format Consistency**: Apply the above structure to each comment without exception
3. **Mechanical Processing**: Execute only mechanical transformation of comment data without any subjective judgment
4. **Data Preservation**: Structure only without modifying original CodeRabbit comment content
</output_format>

## 🎯 クイックサマリー（30秒で読める）

<summary_metrics>
- **Total Comments**: 87 (4 Actionable, 82 Nitpick, 1 Outside Diff Range)
- **Critical Issues**: 0 件
- **High Priority Issues**: 4 件 (Actionable comments)
- **Technology Stack**: Python 3.13, setuptools, PyYAML, OpenAI/Anthropic APIs
- **File Count**: 10 files modified
- **Change Scope**: Project architecture and packaging
</summary_metrics>

<expected_output_examples>
**Example 1: Actionable Comment Processing**
```
## [setup.py:61-64] package_data パッケージ外参照問題

**Root Cause**: キーワード辞書マッチング結果 - functionality_keywords: ["package", "wheel", "install"] 3件検出
**Impact**: High - System [※キーワード数3件 = 闾値3件によりHigh自動判定]
**Type**: Actionable [※CodeRabbitコメント分類より機械抽出]
**Affected**: [setup.py, wheelビルドシステム, パッケージインストールシステム]
```

**Example 2: Nitpick Comment Processing**
```
## [lazygit-llm/lazygit_llm/__init__.py:1-3] パッケージメタデータ不足

**Root Cause**: キーワード辞書マッチング結果 - style_keywords: ["metadata", "version"] 2件検出
**Impact**: Medium - Function [※キーワード数2件 = 闾値2件によりMedium自動判定]
**Type**: Nitpick [※CodeRabbitコメント分類より機械抽出]
**Affected**: [lazygit-llm/lazygit_llm/__init__.py, パッケージ初期化システム]
```

**Example 3: Outside Diff Range Comment**
```
## [lazygit-llm/src/main.py:1-209] 重複ファイル解消

**Root Cause**: キーワード辞書マッチング結果 - quality_keywords: ["duplicate", "refactor"] 2件検出
**Impact**: Medium - Module [※キーワード数2件 = 闾値2件によりMedium自動判定]
**Type**: Outside Diff Range [※CodeRabbitコメント分類より機械抽出]
**Affected**: [lazygit-llm/src/main.py, ランタイムエントリポイントシステム]
```
</expected_output_examples>

# CodeRabbit Comments for Analysis

<review_comments>
  <review_comment type="Actionable" file="lazygit-llm/src/main.py" lines="27-35">
    <issue>sys.path 直接操作と `src.*` 依存を撤去し、単一エントリに集約</issue>
    <instructions>
セットアップは `lazygit_llm.main:main` を指しており、ここは重複実装です。薄いラッパーへ置換してください（またはファイル削除）。過去指摘の継続事項です。
    </instructions>
    <proposed_diff>
old_code: |
  # プロジェクトルートをPATHに追加
  project_root = Path(__file__).parent.parent
  sys.path.insert(0, str(project_root))

  from src.config_manager import ConfigManager
  from src.git_processor import GitDiffProcessor
  from src.provider_factory import ProviderFactory
  from src.message_formatter import MessageFormatter
  from src.base_provider import ProviderError, AuthenticationError, ProviderTimeoutError

new_code: |
  from lazygit_llm.main import main  # ランタイムを単一実装へ集約
    </proposed_diff>
  </review_comment>

  <review_comment type="Actionable" file="setup.py" lines="61-64">
    <issue>package_data の対象がパッケージ外を指しており wheel に入らない可能性大</issue>
    <instructions>
`package_data` は「パッケージ配下相対」です。現在の `config/*.yml*` と `docs/*.md` が `lazygit-llm/` 直下にある場合、`lazygit_llm` パッケージ外のため wheel に同梱されません。配置を `lazygit-llm/lazygit_llm/` 配下へ移すか、`MANIFEST.in`+`include_package_data=True` で sdist/wheel 双方に確実に含めてください。
    </instructions>
  </review_comment>

  <review_comment type="Actionable" file="requirements.txt" lines="3-11">
    <issue>依存の上限設定と脆弱性確認が必要</issue>
    <instructions>
-確認結果（PyPI最新）: requests 2.32.5 / openai 1.107.3 / anthropic 0.67.0 / google-generativeai 0.8.5 / PyYAML 6.0.2.
-重大: requirements.txt の "anthropic>=0.7.0" は PyPI 最新 0.67.0 より新しく矛盾（インストール不可）。
-脆弱性: requests に .netrc credentials 漏洩（patched 2.32.4）や Session verify 問題（patched 2.32.0）等の既知報告、cryptography でも複数の脆弱性報告あり。使用バージョン帯を明示して確認すること。
-対応案: anthropic の指定を修正（>=0.67.0 か固定 pin）、下限のみでなく上限/互換指定を追加、依存は setup.py か requirements.txt のどちらか一つをソース・オブ・トゥルースに統一、あるいは pip-tools/constraints で固定化。CI に脆弱性スキャン（safety / gh-audit 等）を追加。
    </instructions>
  </review_comment>

  <review_comment type="Actionable" file="lazygit-llm/src/base_provider.py" lines="1-6">
    <issue>重複ファイルの解消 — src レイアウトかパッケージ直下のどちらかに統一する</issue>
    <instructions>
-検出: lazygit-llm/lazygit_llm/base_provider.py と lazygit-llm/src/base_provider.py が存在し、内容が重複しています。
-影響: 同一モジュールを二重に置くと import/ビルドの不整合を招きます。
-対応（いずれかを実施）:
  - A) src レイアウトを採用する場合: src/lazygit_llm/base_provider.py に配置してパッケージ直下のファイルを削除。
  - B) 伝統的配置を採用する場合: lazygit_llm/base_provider.py を保持し lazygit-llm/src/base_provider.py を削除。
    </instructions>
  </review_comment>

  <review_comment type="OutsideDiff" file="lazygit-llm/src/main.py" lines="1-209">
    <issue>重複を排除してラッパー化(推奨全置換パッチ)</issue>
    <instructions>
最小ラッパーに置き換え、ドキュメントのパイプ例も削除。
    </instructions>
    <proposed_diff>
old_code: |
  #!/usr/bin/env python3
  """...(長いドキュメント)...

new_code: |
  #!/usr/bin/env python3
  import sys
  from lazygit_llm.main import main

  if __name__ == "__main__":
      sys.exit(main())
    </proposed_diff>
  </review_comment>

  <review_comment type="Nitpick" file=".specs/tasks.md" lines="3-8">
    <issue>Task 1のまとめは明確。Task 4と内容が重複している点だけ整理を。</issue>
    <instructions>
Task 4に「BaseProvider作成」が再掲されています。Task 4は「ProviderFactory実装と拡張ポイント整備」（登録/インスタンス化/接続テストIFなど）に絞ると、進捗トラッキングがより正確になります。
    </instructions>
  </review_comment>

  <review_comment type="Nitpick" file="lazygit-llm/config/config.yml.example" lines="10-13">
    <issue>環境変数参照はそのままではPyYAMLで展開されません。</issue>
    <instructions>
`${OPENAI_API_KEY}`の解決はConfigManager側で必須です（例: `os.environ`を参照して置換）。本PRの範囲外なら、README/コメントに「ConfigManagerで展開する」旨を明記しておいてください。
    </instructions>
  </review_comment>

  <review_comment type="Nitpick" file="lazygit-llm/lazygit_llm/__init__.py" lines="1-3">
    <issue>パッケージ初期化ファイルにバージョン情報とメタデータを追加</issue>
    <instructions>
__version__, __author__, __email__ などの標準的なメタデータを追加することで、パッケージの管理と識別が容易になります。
    </instructions>
  </review_comment>

  <review_comment type="Nitpick" file="lazygit-llm/tests/__init__.py" lines="1">
    <issue>テストパッケージの初期化ファイルが空</issue>
    <instructions>
テスト設定やテスト用ユーティリティ関数を含めることで、テストの保守性が向上します。
    </instructions>
  </review_comment>

  <review_comment type="Nitpick" file="lazygit-llm/lazygit_llm/config_manager.py" lines="15-20">
    <issue>設定ファイルの検証ロジックが不十分</issue>
    <instructions>
必須フィールドの存在確認、データ型の検証、範囲チェックなどを追加することで、実行時エラーを防げます。
    </instructions>
  </review_comment>

</review_comments>

<alternative_output_formats>
JSON形式要求時は構造化レスポンスを提供（詳細は必要時のみ参照）
</alternative_output_formats>

<example_analysis>
**Example for Actionable Comment:**

## [setup.py:61-64] package_data パッケージ外参照問題

**Root Cause**: キーワード辞書マッチング結果 - functionality_keywords: ["package", "wheel", "install"] 3件検出
**Impact**: High - System [※キーワード数3件 = 閾値3件によりHigh自動判定]
**Type**: Actionable [※CodeRabbitコメント分類より機械抽出]
**Affected**: [setup.py, wheelビルドシステム, パッケージインストールシステム]

**Solution**:
```python
// Before (Current Issue)
package_data={
    'lazygit_llm': ['config/*.yml*', 'docs/*.md']
}

// After (Proposed Fix)
# Option A: Move files to package directory
# Option B: Use MANIFEST.in + include_package_data=True
```

**Implementation Steps**:
1. [setup.py:61-64] package_dataパス修正またはMANIFEST.in追加 [コメント指示から機械的抽出]
2. [python setup.py bdist_wheel] wheelビルド実行 [定量的成功基準: ファイル含有確認]
3. [pip install dist/*.whl] インストールテスト [定量的成功基準: import成功]

**Priority**: High - [キーワード辞書マッチング結果: functionality_keywords 3件 > quality_keywords 0件]
**Timeline**: this-sprint [※優先度Highから自動決定: Critical→immediate, High→this-sprint, Medium/Low→next-release]
</example_analysis>

---

# Analysis Instructions

<deterministic_processing_framework>
1. **コメントタイプ抽出**: type属性から機械的分類 (Actionable/Nitpick/Outside Diff Range)
2. **キーワードマッチング**: 以下の静的辞書による文字列照合
   - security_keywords: ["vulnerability", "security", "authentication", "authorization", "injection", "XSS", "CSRF", "token", "credential", "encrypt"]
   - functionality_keywords: ["breaks", "fails", "error", "exception", "crash", "timeout", "import", "package", "dependency", "wheel", "install"]
   - quality_keywords: ["refactor", "maintainability", "readability", "complexity", "duplicate", "cleanup", "optimize", "structure"]
   - style_keywords: ["formatting", "naming", "documentation", "comment", "metadata", "version", "init"]
3. **優先度決定アルゴリズム**: マッチしたキーワード数をカウント、最多カテゴリを選択、同数時は security > functionality > quality > style
4. **テンプレート適用**: 事前定義フォーマットにコメントデータを機械的挿入
5. **ファイル:line情報抽出**: コメント属性から文字列として抽出
6. **ルール適合性チェック**: 全処理が機械的・決定論的であることを確認
</deterministic_processing_framework>

**Begin your analysis with the first comment and proceed systematically through each category.**
