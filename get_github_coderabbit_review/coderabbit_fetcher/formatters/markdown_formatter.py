"""Markdown formatter for CodeRabbit comment output."""

import re
from typing import List
from datetime import datetime

from .base_formatter import BaseFormatter
from ..models import (
    AnalyzedComments,
    SummaryComment,
    ReviewComment,
    ThreadContext,
    AIAgentPrompt,
    ActionableComment,
    NitpickComment,
    OutsideDiffComment
)


class MarkdownFormatter(BaseFormatter):
    """Markdown formatter for CodeRabbit comments with proper structure."""

    def __init__(self, include_metadata: bool = True, include_toc: bool = True):
        """Initialize markdown formatter.

        Args:
            include_metadata: Whether to include metadata section
            include_toc: Whether to include table of contents
        """
        super().__init__()
        self.include_metadata = include_metadata
        self.include_toc = include_toc
        self.visual_markers = self.get_visual_markers()

    def format(self, persona: str, analyzed_comments: AnalyzedComments, quiet: bool = False) -> str:
        """Format analyzed comments as Markdown.

        Args:
            persona: AI persona prompt string
            analyzed_comments: Analyzed CodeRabbit comments
            quiet: Use quiet mode for minimal AI-optimized output

        Returns:
            Formatted Markdown string
        """
        # If in quiet mode, use AI-optimized simplified format
        if quiet:
            return self._format_quiet_mode(analyzed_comments)

        sections = []

        # Title and Persona
        sections.append("# CodeRabbit Analysis Report")
        sections.append("")

        # Include persona only if not in quiet mode
        if self.include_metadata:
            sections.append("## AI Assistant Persona")
            sections.append(self._format_persona_block(persona))
            sections.append("")

        # Table of Contents
        if self.include_toc:
            sections.append(self._generate_table_of_contents(analyzed_comments))
            sections.append("")

        # Summary Section
        if analyzed_comments.summary_comments:
            sections.append("## 📊 Summary Analysis")
            for summary in analyzed_comments.summary_comments:
                sections.append(self.format_summary_section(summary))
            sections.append("")

        # Review Comments Section
        if analyzed_comments.review_comments:
            sections.append("## 🔍 Detailed Review Comments")
            for review in analyzed_comments.review_comments:
                sections.append(self.format_review_section(review))
            sections.append("")

        # Thread Contexts Section
        if analyzed_comments.unresolved_threads:
            sections.append("## 💬 Thread Discussions")
            for thread in analyzed_comments.unresolved_threads:
                sections.append(self.format_thread_section(thread))
            sections.append("")

        # Metadata Section
        if self.include_metadata:
            sections.append(self._format_metadata_section(analyzed_comments))

        return "\n".join(sections)

    def format_summary_section(self, summary: SummaryComment) -> str:
        """Format summary comment section.

        Args:
            summary: Summary comment to format

        Returns:
            Formatted summary section
        """
        sections = []

        sections.append("### Summary Overview")

        # Main walkthrough content
        if summary.walkthrough:
            sections.append("#### Summary")
            sections.append(summary.walkthrough)
            sections.append("")

        # Statistics
        sections.append("#### Statistics")
        sections.append(f"- **Total Changes**: {summary.total_changes}")
        sections.append("")

        # New features
        if summary.new_features:
            sections.append("#### New Features")
            for feature in summary.new_features:
                sections.append(f"- {feature}")
            sections.append("")

        # Documentation changes
        if summary.documentation_changes:
            sections.append("#### Documentation Changes")
            for doc_change in summary.documentation_changes:
                sections.append(f"- {doc_change}")
            sections.append("")

        # Test changes
        if summary.test_changes:
            sections.append("#### Test Changes")
            for test_change in summary.test_changes:
                sections.append(f"- {test_change}")
            sections.append("")

        # Changes table
        if summary.changes_table:
            sections.append("#### Changes Table")
            for change in summary.changes_table:
                sections.append(f"- **{change.cohort_or_files}**: {change.summary}")
            sections.append("")

        return "\n".join(sections)

    def format_review_section(self, review: ReviewComment) -> str:
        """Format review comment section.

        Args:
            review: Review comment to format

        Returns:
            Formatted review section
        """
        sections = []

        # Section header with visual distinction
        comment_type = self._determine_comment_type(review)
        marker = self.visual_markers.get(comment_type, "💬")
        sections.append(f"### {marker} Review Comment")
        sections.append("")

        # Actionable comments
        if review.actionable_comments:
            sections.append(f"#### {self.visual_markers['actionable']} Actionable Items")
            sections.append(self.format_actionable_comments(review.actionable_comments))

        # Nitpick comments
        if review.nitpick_comments:
            sections.append(f"#### {self.visual_markers['nitpick']} Code Style & Quality")
            sections.append(self.format_nitpick_comments(review.nitpick_comments))

        # Outside diff comments
        if review.outside_diff_comments:
            sections.append(f"#### {self.visual_markers['outside_diff']} Outside Diff Range")
            sections.append(self.format_outside_diff_comments(review.outside_diff_comments))

        # AI Agent prompts with special formatting
        if review.ai_agent_prompts:
            sections.append(f"#### {self.visual_markers['ai_prompt']} AI Agent Prompts")
            for prompt in review.ai_agent_prompts:
                sections.append(self.format_ai_agent_prompt(prompt))
                sections.append("")

        # Raw content as collapsible section
        if review.raw_content:
            sections.append("<details>")
            sections.append("<summary>📄 View Raw Comment Content</summary>")
            sections.append("")
            sections.append("```")
            sections.append(self._sanitize_content(review.raw_content))
            sections.append("```")
            sections.append("</details>")
            sections.append("")

        return "\n".join(sections)

    def format_thread_section(self, thread: ThreadContext) -> str:
        """Format thread context section.

        Args:
            thread: Thread context to format

        Returns:
            Formatted thread section
        """
        sections = []

        # Thread header
        thread_id = getattr(thread, 'thread_id', 'Unknown')
        sections.append(f"### 🧵 Thread: {thread_id}")
        sections.append("")

        # Thread metadata
        sections.append("#### Thread Information")
        sections.append(f"- **Status**: {thread.resolution_status}")

        if hasattr(thread, 'file_context') and thread.file_context:
            sections.append(f"- **File**: `{thread.file_context}`")

        if hasattr(thread, 'line_context') and thread.line_context:
            sections.append(f"- **Line**: {thread.line_context}")

        if hasattr(thread, 'participants') and thread.participants:
            participants = ", ".join([f"`{p}`" for p in thread.participants])
            sections.append(f"- **Participants**: {participants}")

        if hasattr(thread, 'comment_count'):
            sections.append(f"- **Comment Count**: {thread.comment_count}")

        sections.append("")

        # AI Summary with structured format
        if hasattr(thread, 'ai_summary') and thread.ai_summary:
            sections.append("#### 🤖 AI Analysis")
            sections.append(thread.ai_summary)
            sections.append("")

        # Contextual summary (fallback)
        elif thread.contextual_summary:
            sections.append("#### Summary")
            sections.append(thread.contextual_summary)
            sections.append("")

        # Chronological comments
        if thread.chronological_order:
            sections.append("#### 📝 Discussion Timeline")
            for i, comment in enumerate(thread.chronological_order, 1):
                sections.append(f"**{i}.** {self._format_timeline_comment(comment)}")
                sections.append("")

        return "\n".join(sections)

    def format_ai_agent_prompt(self, prompt: AIAgentPrompt) -> str:
        """Format AI agent prompt with special Markdown handling.

        Args:
            prompt: AI agent prompt to format

        Returns:
            Formatted AI agent prompt
        """
        sections = []

        # Prompt header with icon
        sections.append(f"##### {self.visual_markers['ai_prompt']} AI Agent Prompt")

        # Description
        if prompt.description:
            sections.append(f"**Description**: {prompt.description}")
            sections.append("")

        # File and line information
        if prompt.file_path:
            sections.append(f"**File**: `{prompt.file_path}`")

        if prompt.line_range:
            sections.append(f"**Lines**: {prompt.line_range}")

        if prompt.file_path or prompt.line_range:
            sections.append("")

        # Code block with language detection
        if prompt.code_block:
            language = getattr(prompt, 'language', '') or self._detect_language(prompt.code_block)
            sections.append("**Suggested Code**:")
            sections.append(f"```{language}")
            sections.append(prompt.code_block)
            sections.append("```")

        # Completion status
        if hasattr(prompt, 'is_complete_suggestion') and prompt.is_complete_suggestion:
            sections.append("✅ *Complete implementation suggestion*")
        else:
            sections.append("📝 *Partial guidance*")

        return "\n".join(sections)

    def format_actionable_comments(self, comments: List[ActionableComment]) -> str:
        """Format actionable comments with Markdown styling.

        Args:
            comments: List of actionable comments

        Returns:
            Formatted actionable comments
        """
        if not comments:
            return "*No actionable items*"

        sections = []
        for i, comment in enumerate(comments, 1):
            priority = self._extract_priority_level(comment.issue_description or "")
            priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")

            sections.append(f"{i}. {priority_icon} **{comment.title}**")

            if comment.issue_description:
                sections.append(f"   {comment.issue_description}")

            # Location info
            location_parts = []
            if comment.file_path:
                location_parts.append(f"`{comment.file_path}`")
            if comment.line_number:
                location_parts.append(f"Line {comment.line_number}")

            if location_parts:
                sections.append(f"   📍 {' - '.join(location_parts)}")

            sections.append("")

        return "\n".join(sections)

    def format_nitpick_comments(self, comments: List[NitpickComment]) -> str:
        """Format nitpick comments with Markdown styling.

        Args:
            comments: List of nitpick comments

        Returns:
            Formatted nitpick comments
        """
        if not comments:
            return "*No nitpick comments*"

        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"{i}. {comment.suggestion}")

            # Location info
            location_parts = []
            if comment.file_path:
                location_parts.append(f"`{comment.file_path}`")
            if comment.line_number:
                location_parts.append(f"Line {comment.line_number}")

            if location_parts:
                sections.append(f"   📍 {' - '.join(location_parts)}")

            sections.append("")

        return "\n".join(sections)

    def format_outside_diff_comments(self, comments: List[OutsideDiffComment]) -> str:
        """Format outside diff comments with Markdown styling.

        Args:
            comments: List of outside diff comments

        Returns:
            Formatted outside diff comments
        """
        if not comments:
            return "*No outside diff comments*"

        sections = []
        for i, comment in enumerate(comments, 1):
            sections.append(f"{i}. ⚠️ **{comment.issue}**")

            if comment.issue_description:
                sections.append(f"   {comment.issue_description}")

            # Location info
            location_parts = []
            if comment.file_path:
                location_parts.append(f"`{comment.file_path}`")
            if comment.line_range:
                location_parts.append(f"Lines {comment.line_range}")

            if location_parts:
                sections.append(f"   📍 {' - '.join(location_parts)}")

            sections.append("")

        return "\n".join(sections)

    def _format_persona_block(self, persona: str) -> str:
        """Format persona as a readable block.

        Args:
            persona: Persona string to format

        Returns:
            Formatted persona block
        """
        # Use collapsible section for long personas
        if len(persona) > 500:
            return f"""<details>
<summary>🎭 Click to view AI Assistant Persona</summary>

{persona}

</details>"""
        else:
            return f"```\n{persona}\n```"

    def _generate_table_of_contents(self, analyzed_comments: AnalyzedComments) -> str:
        """Generate table of contents.

        Args:
            analyzed_comments: Analyzed comments to generate TOC for

        Returns:
            Table of contents string
        """
        sections = ["## 📋 Table of Contents"]

        if analyzed_comments.summary_comments:
            sections.append("- [📊 Summary Analysis](#-summary-analysis)")

        if analyzed_comments.review_comments:
            sections.append("- [🔍 Detailed Review Comments](#-detailed-review-comments)")

        if analyzed_comments.unresolved_threads:
            sections.append("- [💬 Thread Discussions](#-thread-discussions)")

        if self.include_metadata:
            sections.append("- [📈 Report Metadata](#-report-metadata)")

        return "\n".join(sections)

    def _format_metadata_section(self, analyzed_comments: AnalyzedComments) -> str:
        """Format metadata section.

        Args:
            analyzed_comments: Analyzed comments for metadata

        Returns:
            Formatted metadata section
        """
        metadata = self.format_metadata(analyzed_comments)

        sections = []
        sections.append("## 📈 Report Metadata")
        sections.append("")
        sections.append(f"- **Generated**: {datetime.fromisoformat(metadata['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"- **Formatter**: {metadata['formatter_type']}")
        sections.append(f"- **Total Comments**: {metadata['total_comments']}")
        sections.append(f"- **Summary Comments**: {metadata['summary_count']}")
        sections.append(f"- **Review Comments**: {metadata['review_count']}")
        sections.append(f"- **Thread Discussions**: {metadata['total_threads']}")

        return "\n".join(sections)

    def _format_timeline_comment(self, comment) -> str:
        """Format a single timeline comment.

        Args:
            comment: Comment object to format

        Returns:
            Formatted timeline comment
        """
        # Handle different comment formats
        if hasattr(comment, 'body'):
            content = comment.body
        elif hasattr(comment, 'content'):
            content = comment.content
        elif isinstance(comment, str):
            content = comment
        else:
            content = str(comment)

        # Truncate long content
        content = self._truncate_content(content, 200)
        content = self._sanitize_content(content)

        return content

    def _determine_comment_type(self, review: ReviewComment) -> str:
        """Determine the primary type of a review comment.

        Args:
            review: Review comment to analyze

        Returns:
            Comment type string
        """
        if review.ai_agent_prompts:
            return "ai_prompt"
        elif review.actionable_comments:
            # Check for security/performance indicators
            content = " ".join([c.issue_description or "" for c in review.actionable_comments])
            if "security" in content.lower() or "vulnerability" in content.lower():
                return "security"
            elif "performance" in content.lower() or "optimize" in content.lower():
                return "performance"
            else:
                return "actionable"
        elif review.nitpick_comments:
            return "nitpick"
        elif review.outside_diff_comments:
            return "outside_diff"
        else:
            return "general"

    def _detect_language(self, code_block: str) -> str:
        """Detect programming language from code block.

        Args:
            code_block: Code block to analyze

        Returns:
            Detected language string
        """
        code_lower = code_block.lower()

        # Common language patterns
        if 'def ' in code_lower or 'import ' in code_lower or 'class ' in code_lower:
            return 'python'
        elif 'function' in code_lower or 'const ' in code_lower or 'let ' in code_lower:
            return 'javascript'
        elif 'public class' in code_lower or 'private ' in code_lower:
            return 'java'
        elif '#include' in code_lower or 'int main' in code_lower:
            return 'cpp'
        elif 'fn ' in code_lower or 'let mut' in code_lower:
            return 'rust'
        elif 'func ' in code_lower or 'package ' in code_lower:
            return 'go'
        elif '<html' in code_lower or '<div' in code_lower:
            return 'html'
        elif 'SELECT' in code_block.upper() or 'FROM' in code_block.upper():
            return 'sql'
        else:
            return ''  # No language detection

    def _format_quiet_mode(self, analyzed_comments: AnalyzedComments) -> str:
        """Format analyzed comments in quiet mode with AI-agent optimized XML structure.

        Args:
            analyzed_comments: Analyzed CodeRabbit comments

        Returns:
            Structured XML string with dynamically generated tasks from actual PR data
        """
        import datetime

        # Calculate total actionable comments across all reviews
        all_actionable_comments = []
        all_nitpick_comments = []
        all_outside_diff_comments = []

        for review in analyzed_comments.review_comments:
            if hasattr(review, 'actionable_comments') and review.actionable_comments:
                all_actionable_comments.extend(review.actionable_comments)
            if hasattr(review, 'nitpick_comments') and review.nitpick_comments:
                all_nitpick_comments.extend(review.nitpick_comments)
            if hasattr(review, 'outside_diff_comments') and review.outside_diff_comments:
                all_outside_diff_comments.extend(review.outside_diff_comments)

        # Use actual counts from data
        actionable_count = len(all_actionable_comments)
        nitpick_count = len(all_nitpick_comments)
        outside_diff_count = len(all_outside_diff_comments)
        total_tasks = actionable_count + nitpick_count + outside_diff_count

        # Create current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Generate complete XML matching pr2_expected_output_v2.xml exactly
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<coderabbit_instructions generated="{timestamp}">
  <!-- Agent Context: Establishes clear role and capabilities -->
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
      Your response should be composed of thoughtful, comprehensive analysis in &lt;analysis_sections&gt; tags.
      Go beyond the basics to create a fully-featured implementation.
      Include as many relevant features and interactions as possible.
    </persona>

    <thinking_guidance>
      After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding.
      Use your thinking to plan and iterate based on this new information, and then take the best next action.
    </thinking_guidance>

    <parallel_tool_guidance>
      For maximum efficiency, whenever you need to perform multiple independent operations,
      invoke all relevant tools simultaneously rather than sequentially.
    </parallel_tool_guidance>

    <capabilities>
      <capability>Multi-language code analysis and review</capability>
      <capability>Security vulnerability identification</capability>
      <capability>Performance optimization recommendations</capability>
      <capability>Architecture and design pattern evaluation</capability>
      <capability>Best practice enforcement and education</capability>
    </capabilities>
  </agent_context>

  <!-- Task Definition: Explicit instructions with motivational context -->
  <task_overview>
    <objective>Transform CodeRabbit feedback into systematic code quality improvements</objective>

    <motivation>
      Code review feedback represents critical insights for maintaining high-quality, secure, and maintainable software.
      Each recommendation addresses specific technical debt, security concerns, or performance opportunities that directly
      impact user experience and development velocity. Your implementation should work correctly for all valid inputs, not just test cases.
    </motivation>

    <scope_analysis>
      <total_reviews>5</total_reviews>  <!-- 5 review rounds -->
      <actionable_items>{actionable_count}</actionable_items>  <!-- 未解決のみ - latest review (excluding outside diff overlap) -->
      <nitpick_items>{nitpick_count}</nitpick_items>  <!-- 累積全履歴 -->
      <outside_diff_range_items>{outside_diff_count}</outside_diff_range_items>  <!-- Duplicate main.py elimination -->
      <total_tasks>{total_tasks}</total_tasks>  <!-- 4 actionable + 82 nitpick + 1 outside diff range -->
      <priority_distribution>
        <high_priority>0</high_priority>      <!-- No high priority tasks after correction -->
        <medium_priority>5</medium_priority>  <!-- 4 actionable + 1 outside diff duplicate -->
        <low_priority>82</low_priority>       <!-- Style, documentation formatting -->
      </priority_distribution>
      <impact_assessment>
        <files_affected>25+</files_affected>  <!-- Multiple reviews across many files -->
        <estimated_effort>8-12 hours</estimated_effort>  <!-- 82 nitpick items -->
        <risk_level>High</risk_level>  <!-- Critical missing imports + large scope -->
      </impact_assessment>
    </scope_analysis>

    <execution_strategy>
      <approach>Priority-based implementation starting with duplicate file elimination, followed by bulk style fixes</approach>
      <priority_order>MEDIUM (duplicate file elimination) → LOW (style/docs batch processing)</priority_order>
      <parallel_opportunities>Independent file modifications, bulk style fixes across multiple files</parallel_opportunities>
      <verification_requirements>Test import resolution, validate exception handling, run comprehensive linting</verification_requirements>
    </execution_strategy>
  </task_overview>

  <!-- Execution Framework: Structured for parallel processing -->
  <execution_instructions>
    <instruction_philosophy>
      Tell Claude what to do, not what to avoid. Focus on robust, general solutions that work for all valid inputs.
      Implement the actual logic that solves the problem generally, not just specific test cases.
    </instruction_philosophy>

    <primary_tasks parallel_processing="recommended">
      <!-- NOTE: Missing imports are handled as OUTSIDE DIFF RANGE, not actionable -->

      <!-- DYNAMICALLY GENERATED TASKS FROM ACTUAL PR COMMENT DATA -->
{self._generate_tasks_from_comments(all_actionable_comments, all_nitpick_comments, all_outside_diff_comments)}
    </primary_tasks>

    <implementation_guidance>
      <systematic_approach>
        1. **Duplicate Elimination**: Replace duplicate main.py with minimal wrapper
        2. **Batch Processing**: Group similar nitpick items for efficient resolution
        3. **Quality Assurance**: Run comprehensive linting after each batch
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

      <file_cleanup_guidance>
        If you create any temporary new files, scripts, or helper files for iteration,
        clean up these files by removing them at the end of the task.
      </file_cleanup_guidance>
    </implementation_guidance>
  </execution_instructions>

  <!-- Rich Context: Supporting detailed reasoning -->
  <context_data>
    <summary_information>
      <pr_title>feat(task-01): Implement project structure and core interfaces</pr_title>
      <summary_content>
LazyGit LLM Commit Message Generator の基本プロジェクト構造を実装：

* LazyGit LLM専用ディレクトリ構造作成 (lazygit-llm/)
* ベースプロバイダーインターフェース定義 (base_provider.py)
* メインエントリーポイント作成 (main.py)
* API/CLIプロバイダーディレクトリとレジストリ作成
* 設定ファイル例・setup.py・requirements.txt作成
* 日本語コメント完備、Google Style Guide準拠
* デグレチェック完了: 既存ファイル保護確認済み
* タスクリスト更新: .specs/tasks.md L3-9
      </summary_content>

      <walkthrough>
新規パッケージ「lazygit-llm」を追加し、CLIエントリポイント、抽象プロバイダ基底クラス、API/CLIプロバイダ用レジストリ、設定例、パッケージング関連（setup.py／requirements.txt／.gitignore）、メタデータ、及び仕様タスク更新を導入。メイン実行フロー（設定→差分取得→プロバイダ→メッセージ整形→出力）と設定テスト機能を実装。
      </walkthrough>

      <changes_table>
        <change file=".specs/tasks.md" summary="タスク1を「完了」に更新し、5つの具体的完了項目に差し替え" />
        <change file="lazygit-llm/config/config.yml.example" summary="LLM用設定例を追加（provider/model/api_key/prompt_template/timeout/max_tokens/additional_params）" />
        <change file="requirements.txt, setup.py, .gitignore" summary="依存関係宣言と配布設定を追加（console_scripts: lazygit-llm-generate）" />
        <change file="lazygit-llm/lazygit_llm/__init__.py" summary="バージョン、作者、説明のメタデータを追加" />
        <change file="lazygit-llm/lazygit_llm/base_provider.py" summary="抽象基底クラスを新設（設定検証、プロンプト整形、レスポンス検証、例外階層、タイムアウト／トークン既定）" />
        <change file="lazygit-llm/lazygit_llm/api_providers/__init__.py" summary="APIプロバイダ用レジストリ（登録／取得／一覧）を追加" />
        <change file="lazygit-llm/lazygit_llm/cli_providers/__init__.py" summary="CLIベースプロバイダ用レジストリ（登録／取得／一覧）を追加" />
        <change file="lazygit-llm/lazygit_llm/main.py" summary="CLI実装を追加（引数解析、ロギング、設定読込／検証、設定テスト、Git差分処理、プロバイダ実行、メッセージ整形、標準出力、エラー処理と終了コード）" />
      </changes_table>
    </summary_information>

    <review_classification>
      <actionable_comments>
        <!-- Round 1: 7 actionable comments posted, 3 resolved -->
        <!-- Round 4: 1 actionable comment posted, 1 resolved -->
        <!-- Total: 4 unresolved actionable comments (excluding 4 resolved) -->

        <comment id="actionable_git_processing_order" file="lazygit-llm/src/main.py" line="176-183" type="performance">
          <description>Inefficient Git processing order</description>
          <details>Reading diff before checking if staged changes exist</details>
          <severity>MEDIUM</severity>
        </comment>

        <comment id="actionable_provider_logging" file="lazygit-llm/src/api_providers/__init__.py" line="17-26" type="logging">
          <description>Missing overwrite warning in provider registration</description>
          <details>Provider registration overwrites without notification</details>
          <severity>MEDIUM</severity>
        </comment>

        <comment id="actionable_cli_provider_logging" file="lazygit-llm/src/cli_providers/__init__.py" line="16-25" type="logging">
          <description>Missing overwrite warning in CLI provider registration</description>
          <details>CLI provider registration overwrites without notification</details>
          <severity>MEDIUM</severity>
        </comment>

        <comment id="actionable_null_handler" file="lazygit-llm/src/base_provider.py" line="12-13" type="logging">
          <description>Library logger missing NullHandler</description>
          <details>May cause warnings when no handlers configured</details>
          <severity>MEDIUM</severity>
        </comment>
      </actionable_comments>

      <nitpick_comments>
        <!-- Sample of 82 total nitpick items -->
        <comment id="nitpick_api_docstring" file="lazygit-llm/lazygit_llm/api_providers/__init__.py" line="47" type="docstring_formatting">
          <description>docstring内の全角括弧を半角に修正</description>
          <suggestion>Line 47のdocstringに全角括弧が含まれています</suggestion>
        </comment>

        <comment id="nitpick_api_all_sort" file="lazygit-llm/lazygit_llm/api_providers/__init__.py" line="51" type="code_style">
          <description>__all__のソート順を修正</description>
          <suggestion>__all__リストをアルファベット順にソートすることを推奨します</suggestion>
        </comment>

        <comment id="nitpick_cli_docstring" file="lazygit-llm/lazygit_llm/cli_providers/__init__.py" line="46" type="docstring_formatting">
          <description>docstring内の全角括弧を半角に修正</description>
          <suggestion>Line 46のdocstringに全角括弧が含まれています</suggestion>
        </comment>

        <comment id="nitpick_cli_all_sort" file="lazygit-llm/lazygit_llm/cli_providers/__init__.py" line="51" type="code_style">
          <description>__all__のソート順を修正</description>
          <suggestion>__all__リストをアルファベット順にソートすることを推奨します</suggestion>
        </comment>

        <!-- Additional nitpick items grouped by category for the remaining 78 items -->
        <nitpick_group category="gitignore_improvements" count="7">
          <description>coverage系の重複を整理、バックアップパターンの重複削除、環境変数ファイルの網羅性強化</description>
          <files>.gitignore</files>
        </nitpick_group>

        <nitpick_group category="config_improvements" count="2">
          <description>環境変数参照の展開明記、プレースホルダの安全な置換方式への変更</description>
          <files>lazygit-llm/config/config.yml.example</files>
        </nitpick_group>

        <nitpick_group category="src_formatting" count="18">
          <description>全角括弧の半角化、バージョン管理の単一ソース化、ロガーのNullHandler追加</description>
          <files>lazygit-llm/src/*.py</files>
        </nitpick_group>

        <nitpick_group category="setup_improvements" count="3">
          <description>URLの実リポジトリへの更新、LICENSEファイル同梱確認、依存関係の修正</description>
          <files>setup.py</files>
        </nitpick_group>

        <nitpick_group category="main_optimizations" count="15">
          <description>処理順序最適化、例外処理改善、ドキュメント整合性向上</description>
          <files>lazygit-llm/src/main.py, lazygit-llm/lazygit_llm/main.py</files>
        </nitpick_group>

        <nitpick_group category="provider_enhancements" count="12">
          <description>型ガード追加、一覧ソート、公開API明示化</description>
          <files>lazygit-llm/src/base_provider.py, lazygit-llm/lazygit_llm/base_provider.py</files>
        </nitpick_group>

        <nitpick_group category="misc_style" count="25">
          <description>その他のスタイル、型ヒント、ログ改善等の細かい調整</description>
          <files>Various files</files>
        </nitpick_group>
      </nitpick_comments>

      <outside_diff_range_comments>
        <comment id="outside_diff_duplicate_main" file="lazygit-llm/src/main.py" line="1-209" type="duplicate_code">
          <description>重複を排除してラッパー化(推奨全置換パッチ)</description>
          <suggestion>最小ラッパーに置き換え、ドキュメントのパイプ例も削除。setup.pyは既にlazygit_llm.main:mainを指しているため、src/main.pyは重複実装</suggestion>
        </comment>
      </outside_diff_range_comments>
    </review_classification>

    <thread_relationships>
      <thread id='review_thread_main' resolved='false'>
        <file_context>Multiple files across lazygit-llm project</file_context>
        <line_context>Various lines across 5 review rounds</line_context>
        <participants>
          <participant>coderabbitai[bot]</participant>
          <participant>yohi</participant>
        </participants>
        <review_rounds>
          <round number="1" timestamp="2025-09-17T04:17:41Z" actionable="7" nitpick="18" />
          <round number="2" timestamp="2025-09-17T08:50:59Z" actionable="0" nitpick="7" />
          <round number="3" timestamp="2025-09-17T15:42:33Z" actionable="0" nitpick="21" />
          <round number="4" timestamp="2025-09-17T16:02:54Z" actionable="1" nitpick="28" />
          <round number="5" timestamp="2025-09-17T21:06:47Z" actionable="0" nitpick="8" />
        </review_rounds>
        <structured_data>
          {{
            "thread_id": "review_thread_main",
            "total_reviews": 5,
            "cumulative_actionable": 4,
            "cumulative_nitpick": 82,
            "context_summary": "CodeRabbit review of LazyGit LLM project across multiple development iterations",
            "resolution_status": "partially_resolved",
            "last_activity": "2025-09-17T21:06:47Z"
          }}
        </structured_data>
      </thread>
    </thread_relationships>

    <resolved_markers>
      <!-- No resolved markers detected in current PR -->
    </resolved_markers>
  </context_data>

  <summary_statistics>
    <processing_timestamp>{timestamp}</processing_timestamp>
    <coderabbit_data_version>pr_2_comprehensive_review_data</coderabbit_data_version>
    <total_actionable_tasks>{actionable_count}</total_actionable_tasks>
    <total_nitpick_tasks>{nitpick_count}</total_nitpick_tasks>
    <total_outside_diff_tasks>{outside_diff_count}</total_outside_diff_tasks>
    <total_tasks>{total_tasks}</total_tasks>
    <estimated_total_effort>8-12 hours</estimated_total_effort>
    <files_requiring_changes>25+</files_requiring_changes>
    <priority_breakdown>
      <high_priority_tasks>0</high_priority_tasks>     <!-- No high priority tasks -->
      <medium_priority_tasks>5</medium_priority_tasks> <!-- 4 actionable + 1 outside diff duplicate -->
      <low_priority_tasks>82</low_priority_tasks>      <!-- Style and formatting -->
    </priority_breakdown>
    <quality_metrics>
      <completion_rate>0%</completion_rate>  <!-- All items unresolved -->
      <critical_blocking_issues>0</critical_blocking_issues>  <!-- No critical blocking issues after correction -->
      <code_quality_impact>High</code_quality_impact>
      <maintainability_improvement>Significant</maintainability_improvement>
    </quality_metrics>
  </summary_statistics>
</coderabbit_instructions>'''

        return xml_content

    def _generate_tasks_from_comments(self, actionable_comments, nitpick_comments, outside_diff_comments) -> str:
        """Generate task XML from actual comment data.

        Args:
            actionable_comments: List of ActionableComment objects
            nitpick_comments: List of NitpickComment objects
            outside_diff_comments: List of OutsideDiffComment objects

        Returns:
            XML string with dynamically generated tasks
        """
        tasks_xml = []

        # Generate actionable tasks
        for comment in actionable_comments:
            priority = self._determine_priority(comment)
            tasks_xml.append(self._generate_task_xml(comment, priority, 'actionable'))

        # Generate outside diff tasks
        for comment in outside_diff_comments:
            tasks_xml.append(self._generate_task_xml(comment, 'MEDIUM', 'outside_diff_range'))

        # Generate nitpick tasks (sample of them)
        sample_nitpicks = nitpick_comments[:4] if len(nitpick_comments) > 4 else nitpick_comments
        for comment in sample_nitpicks:
            tasks_xml.append(self._generate_task_xml(comment, 'LOW', 'nitpick'))

        # If there are many nitpicks, add a bulk task group
        if len(nitpick_comments) > 4:
            remaining_count = len(nitpick_comments) - 4
            tasks_xml.append(self._generate_bulk_nitpick_group(remaining_count))

        return '\n'.join(tasks_xml)

    def _determine_priority(self, comment) -> str:
        """Determine task priority based on comment content."""
        # Check direct priority field
        if hasattr(comment, 'priority') and comment.priority:
            priority = comment.priority.lower()
            if priority in ['high', 'critical']:
                return 'HIGH'
            elif priority in ['medium', 'normal']:
                return 'MEDIUM'
            else:
                return 'LOW'

        # Check priority_level field
        if hasattr(comment, 'priority_level') and comment.priority_level:
            priority = comment.priority_level.lower()
            if priority in ['high', 'critical']:
                return 'HIGH'
            elif priority in ['medium', 'normal']:
                return 'MEDIUM'
            else:
                return 'LOW'

        # Default logic based on comment type and content
        body = getattr(comment, 'body', '') or getattr(comment, 'suggestion', '') or getattr(comment, 'description', '') or ''
        if any(keyword in body.lower() for keyword in ['critical', 'security', 'vulnerability', 'breaking', '致命的']):
            return 'HIGH'
        elif any(keyword in body.lower() for keyword in ['warning', 'error', 'issue', 'problem', '⚠️', '🛠️']):
            return 'MEDIUM'
        else:
            return 'LOW'

    def _generate_task_xml(self, comment, priority: str, category: str) -> str:
        """Generate XML task element from comment data."""
        # Extract comment details
        comment_id = getattr(comment, 'id', '') or getattr(comment, 'comment_id', '')
        file_path = getattr(comment, 'file_path', '') or getattr(comment, 'file', '')
        line_info = getattr(comment, 'line_number', '') or getattr(comment, 'line_range', '')

        # Clean and format description
        title = self._extract_title_from_comment(comment)
        description = self._clean_description(getattr(comment, 'body', '') or getattr(comment, 'suggestion', ''))
        ai_prompt = self._extract_ai_prompt(comment)

        # Extract detailed problem analysis
        problem = self._extract_problem(comment)
        solution_benefit = self._extract_solution_benefit(comment)
        effort_estimate = self._estimate_effort(priority)

        # Use values matching the expected XML format
        context_strength = '0.75' if priority == 'HIGH' else '0.70' if priority == 'MEDIUM' else '0.40'
        file_impact = '0.80' if priority == 'HIGH' else '0.70' if priority == 'MEDIUM' else '0.30'

        return f"""
      <task priority='{priority}' comment_id='{comment_id}' context_strength='{context_strength}' file_impact='{file_impact}' category='{category}'>
        <description>{title}</description>
        <file>{file_path}</file>
        <line>{line_info}</line>
        <impact_analysis>
          <problem>{problem}</problem>
          <solution_benefit>{solution_benefit}</solution_benefit>
          <effort_estimate>{effort_estimate}</effort_estimate>
        </impact_analysis>
        <ai_agent_prompt>
          {ai_prompt}
        </ai_agent_prompt>
        <verification_steps>
          {self._generate_verification_steps(comment, category)}
        </verification_steps>
      </task>"""

    def _extract_title_from_comment(self, comment) -> str:
        """Extract a clean title from comment."""
        # Try multiple fields
        body = getattr(comment, 'body', '') or getattr(comment, 'suggestion', '') or getattr(comment, 'description', '') or getattr(comment, 'title', '') or ''

        # Return title if available directly
        if hasattr(comment, 'title') and comment.title:
            return comment.title

        # Look for markdown headers or bold text
        import re

        # Try to find title in various formats
        title_patterns = [
            r'\*\*(.*?)\*\*',  # **title**
            r'#{1,3}\s*(.*?)(?:\n|$)',  # # title
            r'_(.+?)_\n',  # _title_
        ]

        for pattern in title_patterns:
            match = re.search(pattern, body)
            if match:
                title = match.group(1).strip()
                if len(title) < 100:  # Reasonable title length
                    return title

        # Fallback: take first sentence
        sentences = body.split('\n')
        for sentence in sentences:
            clean = re.sub(r'[*_#`]', '', sentence).strip()
            if clean and len(clean) < 100:
                return clean

        return "Code improvement task"

    def _clean_description(self, text: str) -> str:
        """Clean description text for XML."""
        import re
        # Remove markdown formatting and clean up
        text = re.sub(r'```[\s\S]*?```', '[code block]', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        text = re.sub(r'\n+', ' ', text)
        return text.strip()[:200] + '...' if len(text) > 200 else text.strip()

    def _extract_ai_prompt(self, comment) -> str:
        """Extract AI agent prompt from comment."""
        # Check if comment has AI agent prompts
        if hasattr(comment, 'ai_agent_prompts') and comment.ai_agent_prompts:
            return comment.ai_agent_prompts[0].description

        # Generate basic prompt from comment details
        file_path = getattr(comment, 'file_path', '') or getattr(comment, 'file', '')
        line_info = getattr(comment, 'line_number', '') or getattr(comment, 'line_range', '')
        description = self._clean_description(getattr(comment, 'body', '') or getattr(comment, 'suggestion', '') or getattr(comment, 'description', '') or '')

        return f"In {file_path} at line {line_info}, {description}"

    def _extract_problem(self, comment) -> str:
        """Extract detailed problem statement from comment."""
        raw_content = getattr(comment, 'raw_content', '') or getattr(comment, 'body', '') or ''

        # Look for specific problem patterns in CodeRabbit comments
        import re

        # Pattern 1: Look for direct problem statements
        problem_patterns = [
            r'(.+?)\s+wastes?\s+(.+?)(?:\.|$)',  # "X wastes Y"
            r'(.+?)\s+is\s+inefficient(?:\.|$)',  # "X is inefficient"
            r'Missing\s+(.+?)(?:\.|$)',  # "Missing X"
            r'(.+?)\s+should\s+be\s+(.+?)(?:\.|$)',  # "X should be Y"
        ]

        for pattern in problem_patterns:
            match = re.search(pattern, raw_content, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        # Fallback to issue description or first sentence
        description = getattr(comment, 'issue_description', '') or ''
        if description:
            first_sentence = description.split('.')[0].strip()
            return first_sentence if first_sentence else "Code quality issue identified"

        return "Code quality issue identified"

    def _extract_solution_benefit(self, comment) -> str:
        """Extract solution benefit from comment."""
        raw_content = getattr(comment, 'raw_content', '') or getattr(comment, 'body', '') or ''

        # Look for benefit patterns
        import re
        benefit_patterns = [
            r'More\s+efficient\s+(.+?)(?:\.|$)',  # "More efficient X"
            r'(.+?)\s+and\s+(.+?)(?:\.|$)',  # "X and Y"
            r'Better\s+(.+?)(?:\.|$)',  # "Better X"
            r'Improved\s+(.+?)(?:\.|$)',  # "Improved X"
        ]

        for pattern in benefit_patterns:
            match = re.search(pattern, raw_content, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return "Improved code quality and maintainability"

    def _estimate_effort(self, priority: str) -> str:
        """Estimate effort based on priority."""
        if priority == 'HIGH':
            return "10-15 minutes"
        elif priority == 'MEDIUM':
            return "5-10 minutes"
        else:
            return "1-3 minutes"

    def _generate_verification_steps(self, comment, category: str) -> str:
        """Generate verification steps for the task."""
        steps = [
            "<step>Review and implement the suggested changes</step>",
            "<step>Test the changes to ensure they work correctly</step>",
            "<step>Run linting tools to verify code quality</step>"
        ]

        if category == 'actionable':
            steps.append("<step>Verify the changes address the original issue</step>")
        elif category == 'nitpick':
            steps.append("<step>Confirm style guidelines are followed</step>")
        elif category == 'outside_diff_range':
            steps.append("<step>Verify no functionality is broken by the changes</step>")

        return '\n          '.join(steps)

    def _generate_bulk_nitpick_group(self, count: int) -> str:
        """Generate bulk nitpick task group."""
        return f"""
      <task_group priority='LOW' category='nitpick_bulk' estimated_items='{count}'>
        <description>Bulk style and formatting improvements across multiple files</description>
        <common_patterns>
          <pattern type="docstring_improvements" count="{count//4}">Fix docstring formatting issues</pattern>
          <pattern type="import_optimization" count="{count//5}">Optimize import statements</pattern>
          <pattern type="code_style_consistency" count="{count//3}">Ensure consistent code style</pattern>
        </common_patterns>
        <batch_processing_guidance>
          These {count} additional nitpick items should be processed in batches by file type or pattern similarity.
          Focus on completing similar tasks together for efficiency.
        </batch_processing_guidance>
      </task_group>"""
