# CodeRabbit Review Analysis - AI Agent Prompt

<role>
You are a senior software engineer with 10+ years of experience specializing in code review, quality improvement, security vulnerability identification, performance optimization, architecture design, and testing strategies. You follow industry best practices and prioritize code quality, maintainability, and security.
</role>

<core_principles>
Quality, Security, Standards, Specificity, Impact-awareness
</core_principles>

<analysis_steps>
1. Issue identification → 2. Impact assessment → 3. Solution design → 4. Implementation plan → 5. Verification method
</analysis_steps>

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

<pull_request_context>
  <pr_url>https://github.com/yohi/lazygit-llm-commit-generator/pull/2</pr_url>
  <title>feat(task-01): Implement project structure and core interfaces</title>
  <description>LazyGit LLM Commit Message Generator の基本プロジェクト構造を実装：

- LazyGit LLM専用ディレクトリ構造作成 (lazygit-llm/)
- ベースプロバイダーインターフェース定義 (base_provider.py)
- メインエントリーポイント作成 (main.py)
- API/CLIプロバイダーディレクトリとレジストリ作成
- 設定ファイル例・setup.py・requirements.txt作成
- 日本語コメント完備、Google Style Guide準拠
- デグレチェック完了: 既存ファイル保護確認済み
- タスクリスト更新: .specs/tasks.md L3-9

Task-01: Set up project structure and core interfaces
Requirements: 1.1, 2.1, 5.1
Design-ref: .specs/design.md
Affected: lazygit-llm/ (new), .specs/tasks.md
Test: 基本構造作成完了

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude &lt;noreply@anthropic.com&gt;</description>
  <branch>feature/01-task01_project-structure</branch>
  <author>yohi</author>
  <summary>
    <files_changed>10</files_changed>
    <lines_added>836</lines_added>
    <lines_deleted>4</lines_deleted>
  </summary>
  <technical_context>
    <repository_type>Python application</repository_type>
    <key_technologies>Python</key_technologies>
    <file_extensions>.example, .gitignore, .md, .py, .txt</file_extensions>
    <build_system>Unknown</build_system>
  </technical_context>
  <changed_files>
    <file path=".gitignore" additions="201" deletions="0" />
    <file path=".specs/tasks.md" additions="6" deletions="4" />
    <file path="lazygit-llm/config/config.yml.example" additions="49" deletions="0" />
    <file path="lazygit-llm/lazygit_llm/__init__.py" additions="10" deletions="0" />
    <file path="lazygit-llm/lazygit_llm/api_providers/__init__.py" additions="51" deletions="0" />
    <file path="lazygit-llm/lazygit_llm/base_provider.py" additions="170" deletions="0" />
    <file path="lazygit-llm/lazygit_llm/cli_providers/__init__.py" additions="51" deletions="0" />
    <file path="lazygit-llm/lazygit_llm/main.py" additions="204" deletions="0" />
    <file path="requirements.txt" additions="28" deletions="0" />
    <file path="setup.py" additions="66" deletions="0" />
  </changed_files>
</pull_request_context>

<coderabbit_review_summary>
  <total_comments>87</total_comments>
  <actionable_comments>4</actionable_comments>
  <nitpick_comments>82</nitpick_comments>
  <outside_diff_range_comments>1</outside_diff_range_comments>
</coderabbit_review_summary>

<comment_metadata>
  <primary_issues>command syntax, file existence checks</primary_issues>
  <complexity_level>Medium (build system configuration)</complexity_level>
  <change_impact_scope>build automation, configuration management, environment configuration, package installation, script execution</change_impact_scope>
  <testing_requirements>Manual execution verification, cross-platform compatibility</testing_requirements>
  <risk_assessment level="High" reason="Rule-based: Changes affect build system (Makefile) and package installation, which can impact all developers." />
  <estimated_resolution_time_hours description="This is a rule-based estimate">2-3</estimated_resolution_time_hours>
</comment_metadata>

# Analysis Task

<analysis_requirements>
Analyze each CodeRabbit comment below and provide structured responses following the specified format. For each comment type, apply different analysis depths:

## Actionable Comments Analysis
These are critical issues requiring immediate attention. Provide comprehensive analysis including:
- Root cause identification
- Impact assessment (High/Medium/Low)
- Specific code modifications
- Implementation checklist
- Testing requirements

## Outside Diff Range Comments Analysis
These comments reference code outside the current diff but are relevant to the changes. Focus on:
- Relationship to current changes
- Potential impact on the PR
- Recommendations for addressing (now vs. future)
- Documentation needs

## Nitpick Comments Analysis
These are minor improvements or style suggestions. Provide:
- Quick assessment of the suggestion value
- Implementation effort estimation
- Whether to address now or defer
- Consistency with codebase standards
</analysis_requirements>

<output_requirements>
For each comment, respond using this exact structure:

## [ファイル名:行番号] 問題のタイトル

### 🔍 Problem Analysis
**Root Cause**: [What is the fundamental issue]
**Impact Level**: [High/Medium/Low] - [Impact scope explanation]
**Technical Context**: [Relevant technical background]
**Comment Type**: [Actionable/Outside Diff Range/Nitpick]

### 💡 Solution Proposal
#### Recommended Approach
```プログラミング言語
// Before (Current Issue)
現在の問題のあるコード

// After (Proposed Fix)
提案する修正されたコード
```

#### Alternative Solutions (if applicable)
- **Option 1**: [Alternative implementation method 1]
- **Option 2**: [Alternative implementation method 2]

### 📋 Implementation Guidelines
- [ ] **Step 1**: [Specific implementation step]
- [ ] **Step 2**: [Specific implementation step]
- [ ] **Testing**: [Required test content]
- [ ] **Impact Check**: [Related parts to verify]

### ⚡ Priority Assessment
**Judgment**: [Critical/High/Medium/Low]
**Reasoning**: [Basis for priority judgment]
**Timeline**: [Suggested timeframe for fix]

---
</output_requirements>

# Special Processing Instructions

## 🤖 AI Agent Prompts
When CodeRabbit provides "🤖 Prompt for AI Agents" code blocks, perform enhanced analysis:

<ai_agent_analysis>
1. **Code Verification**: Check syntax accuracy and logical validity
2. **Implementation Compatibility**: Assess alignment with existing codebase
3. **Optimization Suggestions**: Consider if better implementations exist
4. **Risk Assessment**: Identify potential issues

### Enhanced Output Format for AI Agent Prompts:
## CodeRabbit AI Suggestion Evaluation

### ✅ Strengths
- [Specific strength 1]
- [Specific strength 2]

### ⚠️ Concerns
- [Potential issue 1]
- [Potential issue 2]

### 🔧 Optimization Proposal
```プログラミング言語
// Optimized implementation
最適化されたコード提案
```

### 📋 Implementation Checklist
- [ ] [Implementation step 1]
- [ ] [Implementation step 2]
- [ ] [Test item 1]
- [ ] [Test item 2]
</ai_agent_analysis>

## 🧵 Thread Context Analysis
For comments with multiple exchanges, consider:
1. **Discussion History**: Account for previous exchanges
2. **Unresolved Points**: Identify remaining issues
3. **Comprehensive Solution**: Propose solutions considering the entire thread

---

# CodeRabbit Comments for Analysis

<review_comments>
  <review_comment type="Actionable" file="lazygit-llm/lazygit_llm/base_provider.py" lines="6">
    <issue_summary>
      &lt;summary&gt;🧩 Analysis chain&lt;/summary&gt;
    </issue_summary>
    <coderabbit_analysis>
      - 要修正箇所（例）: lazygit-llm/src/main.py（現: from src.base_provider ...）、lazygit-llm/lazygit_llm/main.py（現: from lazygit_llm.base_provider ...）、および lazygit-llm/lazygit_llm/api_providers/__init__.py、lazygit-llm/lazygit_llm/cli_providers/__init__.py を更新すること。
    </coderabbit_analysis>
    <ai_agent_prompt>
      <code_block>
        In lazygit-llm/lazygit_llm/base_provider.py (lines 1-6) there is a duplicate of src/base_provider.py (MD5 match); choose a canonical path (recommend src/lazygit_llm/base_provider.py), move the single authoritative file there, delete the duplicate lazygit-llm/lazygit_llm/base_provider.py, and update all imports to the canonical path (e.g. change from src.base_provider and lazygit_llm.base_provider to src.lazygit_llm.base_provider) including lazygit-llm/src/main.py, lazygit-llm/lazygit_llm/main.py, lazygit-llm/lazygit_llm/api_providers/__init__.py, and lazygit-llm/lazygit_llm/cli_providers/__init__.py; ensure package __init__.py files and setup/pyproject import paths reflect the new location and run tests/linters to catch any remaining broken imports.
      </code_block>
      <language>python</language>
    </ai_agent_prompt>
    <proposed_diff>
      <![CDATA[
---
---
---
---
- 確認: 以下の重複ファイルを検出（内容一致、MD5=06243edb1911b71561dd2a03ca59473b）: lazygit-llm/lazygit_llm/base_provider.py、lazygit-llm/src/base_provider.py。
- 対応: 単一の正本を src/lazygit_llm/base_provider.py に配置するか、プロジェクトで採用しているパッケージ構成に合わせて canonical な場所を決定して移動・統一する。重複ファイルを削除し、全ての import を canonical パスに揃えること。
- 要修正箇所（例）: lazygit-llm/src/main.py（現: from src.base_provider ...）、lazygit-llm/lazygit_llm/main.py（現: from lazygit_llm.base_provider ...）、および lazygit-llm/lazygit_llm/api_providers/__init__.py、lazygit-llm/lazygit_llm/cli_providers/__init__.py を更新すること。
]]>
    </proposed_diff>
  </review_comment>
</review_comments>
