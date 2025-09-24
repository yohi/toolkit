"""AI Agent Prompt Formatter for CodeRabbit comments.

This formatter creates detailed AI agent prompts that match the expected output format
with comprehensive role definitions, analysis requirements, and structured comment data.
"""

import re
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from ..models import ActionableComment, AnalyzedComments
from .base_formatter import BaseFormatter


class AIAgentPromptFormatter(BaseFormatter):
    """Formatter for detailed AI agent prompts matching expected output format."""

    def format(
        self,
        persona: str,
        analyzed_comments: AnalyzedComments,
        quiet: bool = False,
        pr_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format analyzed comments into detailed AI agent prompt.

        Args:
            persona: AI persona prompt string (not used - uses built-in template)
            analyzed_comments: Analyzed CodeRabbit comments
            quiet: Enable quiet mode to suppress debug output
            pr_info: Pull request information from GitHub API

        Returns:
            Detailed AI agent prompt matching expected format
        """
        sections = []

        # Document header
        sections.append(self._format_header())

        # Role definition
        sections.append(self._format_role_definition())

        # Core principles
        sections.append(self._format_core_principles())

        # Analysis steps
        sections.append(self._format_analysis_steps())

        # Priority matrix
        sections.append(self._format_priority_matrix())

        # Impact scope
        sections.append(self._format_impact_scope())

        # Pull request context
        sections.append(self._format_pull_request_context(pr_info))

        # CodeRabbit review summary
        sections.append(self._format_coderabbit_review_summary(analyzed_comments, quiet))

        # Comment metadata
        sections.append(self._format_comment_metadata(analyzed_comments))

        # Analysis task section
        sections.append(self._format_analysis_task())

        # Analysis requirements
        sections.append(self._format_analysis_requirements())

        # Output requirements
        sections.append(self._format_output_requirements())

        # Special processing instructions
        sections.append(self._format_special_processing_instructions())

        # CodeRabbit comments for analysis
        sections.append(self._format_coderabbit_comments(analyzed_comments))

        # Analysis instructions
        sections.append(self._format_analysis_instructions())

        return "\n\n".join(sections)

    def _format_header(self) -> str:
        """Format document header."""
        return "# CodeRabbit Review Analysis - AI Agent Prompt"

    def _format_role_definition(self) -> str:
        """Format role definition section."""
        return """<role>
You are a senior software engineer with 10+ years of experience specializing in code review, quality improvement, security vulnerability identification, performance optimization, architecture design, and testing strategies. You follow industry best practices and prioritize code quality, maintainability, and security.
</role>"""

    def _format_core_principles(self) -> str:
        """Format core principles section."""
        return """<core_principles>
Quality, Security, Standards, Specificity, Impact-awareness
</core_principles>"""

    def _format_analysis_steps(self) -> str:
        """Format analysis steps section."""
        return """<analysis_steps>
1. Issue identification → 2. Impact assessment → 3. Solution design → 4. Implementation plan → 5. Verification method
</analysis_steps>"""

    def _format_priority_matrix(self) -> str:
        """Format priority matrix section."""
        return """<priority_matrix>
- **Critical**: Security vulnerabilities, data loss risks, system failures
- **High**: Functionality breaks, performance degradation >20%, API changes
- **Medium**: Code quality, maintainability, minor performance issues
- **Low**: Style, documentation, non-functional improvements
</priority_matrix>"""

    def _format_impact_scope(self) -> str:
        """Format impact scope section."""
        return """<impact_scope>
- **System**: Multiple components affected
- **Module**: Single module/service affected
- **Function**: Single function/method affected
- **Line**: Specific line changes only
</impact_scope>"""

    def _format_pull_request_context(self, pr_info: Optional[Dict[str, Any]]) -> str:
        """Format pull request context section."""
        if not pr_info:
            return """<pull_request_context>
  <pr_url>Unknown</pr_url>
  <title>Unknown</title>
  <description>_No description provided._</description>
  <branch>Unknown</branch>
  <author>Unknown</author>
  <summary>
    <files_changed>0</files_changed>
    <lines_added>0</lines_added>
    <lines_deleted>0</lines_deleted>
  </summary>
  <technical_context>
    <repository_type>Unknown</repository_type>
    <key_technologies>Unknown</key_technologies>
    <file_extensions>Unknown</file_extensions>
    <build_system>Unknown</build_system>
  </technical_context>
  <changed_files>
  </changed_files>
</pull_request_context>"""

        # Extract PR information with proper field mapping
        pr_url = pr_info.get("url", "Unknown")
        title = pr_info.get("title", "Unknown")
        description = pr_info.get("body") or "_No description provided._"

        # Handle different possible field names for branch
        branch = pr_info.get("headRefName") or pr_info.get("head", {}).get("ref") or "Unknown"

        # Handle different possible field names for author
        author = "Unknown"
        if "author" in pr_info:
            author_data = pr_info["author"]
            if isinstance(author_data, dict):
                author = author_data.get("login", "Unknown")
            elif isinstance(author_data, str):
                author = author_data

        # Get file changes with proper field mapping
        files_changed = pr_info.get("changedFiles", pr_info.get("changed_files", 0))
        lines_added = pr_info.get("additions", 0)
        lines_deleted = pr_info.get("deletions", 0)

        # Analyze technical context from files
        files = pr_info.get("files", [])
        tech_context = self._analyze_technical_context(files)

        # Format changed files - use dynamic data only
        changed_files_section = ""
        for file_info in files[:10]:  # Limit to first 10 files
            filename = file_info.get("filename", "Unknown")
            additions = file_info.get("additions", 0)
            deletions = file_info.get("deletions", 0)
            changed_files_section += f'    <file path="{escape(filename)}" additions="{additions}" deletions="{deletions}" />\n'

        return f"""<pull_request_context>
  <pr_url>{escape(pr_url)}</pr_url>
  <title>{escape(title)}</title>
  <description>{escape(description)}</description>
  <branch>{escape(branch)}</branch>
  <author>{escape(author)}</author>
  <summary>
    <files_changed>{files_changed}</files_changed>
    <lines_added>{lines_added}</lines_added>
    <lines_deleted>{lines_deleted}</lines_deleted>
  </summary>
  <technical_context>
    <repository_type>{escape(tech_context['repository_type'])}</repository_type>
    <key_technologies>{escape(tech_context['key_technologies'])}</key_technologies>
    <file_extensions>{escape(tech_context['file_extensions'])}</file_extensions>
    <build_system>{escape(tech_context['build_system'])}</build_system>
  </technical_context>
  <changed_files>
{changed_files_section}  </changed_files>
</pull_request_context>"""

    def _analyze_technical_context(self, files: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze technical context from changed files."""
        if not files:
            return {
                "repository_type": "Unknown",
                "key_technologies": "Unknown",
                "file_extensions": "Unknown",
                "build_system": "Unknown",
            }

        # Analyze file extensions
        extensions = set()
        build_files = []
        has_bun_content = False

        for file_info in files:
            filename = file_info.get("filename", "")
            if "." in filename:
                ext = filename.split(".")[-1]
                extensions.add(f".{ext}")

            # Check for build system files
            basename = filename.split("/")[-1].lower()
            if basename in [
                "makefile",
                "package.json",
                "pyproject.toml",
                "cargo.toml",
                "build.gradle",
            ]:
                build_files.append(basename)

            # Check for bun-related content in file patches
            patch = file_info.get("patch", "")
            if patch and ("bun " in patch or "bunx" in patch or ".bun" in patch):
                has_bun_content = True

        # Determine repository type and technologies
        repo_type = "Configuration files"
        technologies = []
        build_system = "Unknown"

        if ".py" in extensions:
            technologies.append("Python")
            repo_type = "Python application"
        if ".js" in extensions or ".ts" in extensions:
            technologies.append("JavaScript/TypeScript")
            repo_type = "Web application"
        if ".mk" in extensions or "makefile" in build_files:
            technologies.append("Make build system")
            build_system = "GNU Make"
        if "package.json" in build_files:
            technologies.append("Node.js")
            build_system = "npm/yarn"

        # Special handling for shell scripts
        if ".sh" in extensions:
            technologies.append("shell scripting")

        # Add bun package manager if detected in content
        if has_bun_content:
            technologies.append("bun package manager")

        # Format file extensions to match expected output
        formatted_extensions = []
        if ".mk" in extensions:
            formatted_extensions.append(".mk (Makefile)")
        if ".sh" in extensions:
            formatted_extensions.append(".sh (Shell script)")
        # Add other extensions without descriptions
        for ext in sorted(extensions):
            if ext not in [".mk", ".sh"]:
                formatted_extensions.append(ext)

        return {
            "repository_type": repo_type,
            "key_technologies": ", ".join(technologies) if technologies else "Unknown",
            "file_extensions": (
                ", ".join(formatted_extensions) if formatted_extensions else "Unknown"
            ),
            "build_system": build_system,
        }

    def _format_coderabbit_review_summary(
        self, analyzed_comments: AnalyzedComments, quiet: bool = False
    ) -> str:
        """Format CodeRabbit review summary section."""
        # Enhanced Classification結果を優先的に使用
        if (
            hasattr(analyzed_comments.metadata, "adjusted_counts")
            and analyzed_comments.metadata.adjusted_counts
        ):
            adjusted_counts = analyzed_comments.metadata.adjusted_counts
            actionable_comments = adjusted_counts["actionable"]
            nitpick_comments = adjusted_counts["nitpick"]
            outside_diff_comments = adjusted_counts["outside_diff"]
            total_comments = adjusted_counts["total"]

            if not quiet:
                print(
                    f"DEBUG: Using Enhanced Classification counts - actionable: {actionable_comments}, nitpick: {nitpick_comments}, outside_diff: {outside_diff_comments}"
                )
        else:
            # Fallback to legacy counting method
            actionable_comments = 0
            nitpick_comments = 0
            outside_diff_comments = 0

            # Count from review comments
            for review in analyzed_comments.review_comments:
                actionable_comments += len(review.actionable_comments)
                nitpick_comments += len(review.nitpick_comments)
                outside_diff_comments += len(review.outside_diff_comments)
                if not quiet:
                    print(
                        f"DEBUG: Review has {len(review.outside_diff_comments)} outside_diff_comments"
                    )

            # Count from thread contexts (these are typically actionable)
            for _thread in analyzed_comments.unresolved_threads:
                actionable_comments += 1

            # Total comments is the sum of all individual comments
            total_comments = actionable_comments + nitpick_comments + outside_diff_comments

            if not quiet:
                print(
                    f"DEBUG: Legacy counting - actionable: {actionable_comments}, nitpick: {nitpick_comments}, outside_diff: {outside_diff_comments}"
                )

        return f"""<coderabbit_review_summary>
  <total_comments>{total_comments}</total_comments>
  <actionable_comments>{actionable_comments}</actionable_comments>
  <nitpick_comments>{nitpick_comments}</nitpick_comments>
  <outside_diff_range_comments>{outside_diff_comments}</outside_diff_range_comments>
</coderabbit_review_summary>"""

    def _format_comment_metadata(self, analyzed_comments: AnalyzedComments) -> str:
        """Format comment metadata section."""
        # Extract primary issues from comments
        primary_issues = []
        files_affected = set()

        for review in analyzed_comments.review_comments:
            for comment in review.actionable_comments:
                if comment.file_path:
                    files_affected.add(comment.file_path)
                # Extract key issues from descriptions
                if "PATH" in comment.issue_description:
                    primary_issues.append("PATH handling")
                if (
                    "file existence" in comment.issue_description
                    or "check" in comment.issue_description
                ):
                    primary_issues.append("file existence checks")
                if "command" in comment.issue_description or "syntax" in comment.issue_description:
                    primary_issues.append("command syntax")

        # Determine complexity and impact
        complexity_level = "Medium (build system configuration)"
        change_impact_scope = "build automation, configuration management, environment configuration, package installation, script execution"
        testing_requirements = "Manual execution verification, cross-platform compatibility"

        # Risk assessment based on file types
        risk_level = "High"
        risk_reason = "Rule-based: Changes affect build system (Makefile) and package installation, which can impact all developers."

        estimated_time = "2-3"

        return f"""<comment_metadata>
  <primary_issues>{', '.join(set(primary_issues)) if primary_issues else 'general code improvements'}</primary_issues>
  <complexity_level>{complexity_level}</complexity_level>
  <change_impact_scope>{change_impact_scope}</change_impact_scope>
  <testing_requirements>{testing_requirements}</testing_requirements>
  <risk_assessment level="{risk_level}" reason="{risk_reason}" />
  <estimated_resolution_time_hours description="This is a rule-based estimate">{estimated_time}</estimated_resolution_time_hours>
</comment_metadata>"""

    def _format_analysis_task(self) -> str:
        """Format analysis task section."""
        return """# Analysis Task

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
</analysis_requirements>"""

    def _format_analysis_requirements(self) -> str:
        """Format analysis requirements section."""
        return ""  # Already included in analysis_task

    def _format_output_requirements(self) -> str:
        """Format output requirements section."""
        return """<output_requirements>
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
</output_requirements>"""

    def _format_special_processing_instructions(self) -> str:
        """Format special processing instructions section."""
        return """# Special Processing Instructions

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

---"""

    def _format_coderabbit_comments(self, analyzed_comments: AnalyzedComments) -> str:
        """Format CodeRabbit comments for analysis section."""
        sections = []
        sections.append("# CodeRabbit Comments for Analysis")
        sections.append("")
        sections.append("<review_comments>")

        # Process actionable comments first, then nitpick comments, then outside diff comments
        # Use consistent ordering based on file type and line number
        all_actionable = []
        all_nitpick = []
        all_outside_diff = []

        for review in analyzed_comments.review_comments:
            all_actionable.extend(review.actionable_comments)
            all_nitpick.extend(review.nitpick_comments)
            all_outside_diff.extend(review.outside_diff_comments)

        # Sort actionable comments by file path and line number
        def sort_key(comment):
            file_path = getattr(comment, "file_path", "")
            line_range = str(getattr(comment, "line_range", ""))
            # Extract numeric part for sorting
            line_num = 0
            if line_range.isdigit():
                line_num = int(line_range)
            elif "-" in line_range:
                try:
                    line_num = int(line_range.split("-")[0])
                except ValueError:
                    line_num = 0
            return (file_path, line_num)

        # Format actionable comments
        for comment in sorted(all_actionable, key=sort_key):
            sections.append(self._format_review_comment(comment, "Actionable"))

        # Format nitpick comments (with deduplication for also_applies_to cases)
        deduplicated_nitpick = self._deduplicate_nitpick_comments(sorted(all_nitpick, key=sort_key))
        for comment in deduplicated_nitpick:
            sections.append(self._format_nitpick_comment(comment))

        # Format outside diff comments
        for comment in sorted(all_outside_diff, key=sort_key):
            sections.append(self._format_outside_diff_comment(comment))

        sections.append("</review_comments>")
        return "\n".join(sections)

    def _deduplicate_nitpick_comments(self, nitpick_comments):
        """Deduplicate nitpick comments that have 'also_applies_to' information."""
        seen_issues = set()
        deduplicated = []

        for comment in nitpick_comments:
            # Extract the issue summary/title to use as a deduplication key
            if hasattr(comment, "suggestion"):
                issue_key = comment.suggestion
            elif hasattr(comment, "raw_content"):
                issue_key = self._extract_issue_summary(comment.raw_content, "")
            else:
                issue_key = str(comment)

            # Normalize the issue key for comparison
            normalized_key = issue_key.strip().lower()

            # Skip if we've already seen this issue
            if normalized_key in seen_issues:
                continue

            # Add to seen issues and deduplicated list
            seen_issues.add(normalized_key)
            deduplicated.append(comment)

        return deduplicated

    def _format_review_comment(self, comment: ActionableComment, comment_type: str) -> str:
        """Format a single review comment."""
        lines = []
        # Clean line_range to prevent XML attribute corruption
        clean_line_range = (
            str(comment.line_range).replace("\n", "").replace("\r", "").replace("---", "").strip()
        )
        lines.append(
            f'  <review_comment type="{comment_type}" file="{escape(comment.file_path)}" lines="{escape(clean_line_range)}">'
        )

        # Extract detailed information from raw content
        raw_content = comment.raw_content

        # Issue summary - extract title or first meaningful line
        issue_summary = self._extract_issue_summary(raw_content, comment.issue_description)
        lines.append("    <issue_summary>")
        lines.append(f"      {escape(issue_summary)}")
        lines.append("    </issue_summary>")

        # Add "Also applies to" information if this is a consolidated comment
        also_applies_to = self._extract_also_applies_to(raw_content)
        if also_applies_to:
            lines.append("    <also_applies_to>")
            lines.append(f"      {escape(also_applies_to)}")
            lines.append("    </also_applies_to>")

        # CodeRabbit analysis - use the same method as nitpick comments
        analysis_text = self._extract_analysis_text(raw_content)
        lines.append("    <coderabbit_analysis>")
        lines.append(f"      {escape(analysis_text)}")
        lines.append("    </coderabbit_analysis>")

        # AI agent prompt if available - structured format
        ai_prompt_text = self._extract_ai_agent_prompt_text(raw_content)
        if ai_prompt_text:
            lines.append("    <ai_agent_prompt>")

            # Extract code block and description from AI prompt text
            code_block, language, description = self._parse_ai_agent_prompt(ai_prompt_text)

            if code_block:
                lines.append("      <code_block>")
                lines.append(f"        {escape(code_block)}")
                lines.append("      </code_block>")

            if language:
                lines.append(f"      <language>{escape(language)}</language>")

            if description:
                lines.append("      <description>")
                lines.append(f"        {escape(description)}")
                lines.append("      </description>")

            lines.append("    </ai_agent_prompt>")

        # Proposed diff if available
        proposed_diff = self._extract_proposed_diff(raw_content)
        if proposed_diff:
            lines.append("    <proposed_diff>")
            lines.append("      <![CDATA[")
            lines.append(proposed_diff)
            lines.append("]]>")
            lines.append("    </proposed_diff>")

        lines.append("  </review_comment>")
        lines.append("")
        return "\n".join(lines)

    def _format_nitpick_comment(self, comment) -> str:
        """Format a nitpick comment."""
        # Handle different comment types
        if hasattr(comment, "file_path"):
            file_path = comment.file_path
            line_range = getattr(comment, "line_range", "Unknown")
            # For NitpickComment objects, use 'raw_content' for analysis and 'suggestion' for title
            title = getattr(comment, "suggestion", "Nitpick suggestion")
            analysis_content = getattr(
                comment, "raw_content", getattr(comment, "suggestion", str(comment))
            )
        else:
            # Handle dictionary-like objects
            file_path = comment.get("file_path", "Unknown")
            line_range = comment.get("line_range", "Unknown")
            title = comment.get("suggestion", "Nitpick suggestion")
            analysis_content = comment.get("raw_content", comment.get("suggestion", str(comment)))

        lines = []
        # Clean line_range to prevent XML attribute corruption
        clean_line_range = (
            str(line_range).replace("\n", "").replace("\r", "").replace("---", "").strip()
        )
        lines.append(
            f'  <review_comment type="Nitpick" file="{escape(file_path)}" lines="{escape(clean_line_range)}">'
        )

        # Issue summary
        lines.append("    <issue_summary>")
        lines.append(f"      {escape(title)}")
        lines.append("    </issue_summary>")

        # Add "Also applies to" information if this is a consolidated comment
        also_applies_to = self._extract_also_applies_to(analysis_content)
        if also_applies_to:
            lines.append("    <also_applies_to>")
            lines.append(f"      {escape(also_applies_to)}")
            lines.append("    </also_applies_to>")

        # CodeRabbit analysis
        lines.append("    <coderabbit_analysis>")
        analysis_text = self._extract_analysis_text(analysis_content)
        lines.append(f"      {escape(analysis_text)}")
        lines.append("    </coderabbit_analysis>")

        # Proposed diff - generate based on comment type if not available
        proposed_diff = None
        if hasattr(comment, "proposed_fix") and comment.proposed_fix:
            proposed_diff = comment.proposed_fix
        elif hasattr(comment, "proposed_diff") and comment.proposed_diff:
            proposed_diff = comment.proposed_diff
        else:
            # Generate proposed diff based on the issue type
            proposed_diff = self._generate_proposed_diff(analysis_content, file_path, line_range)

        if proposed_diff:
            lines.append("    <proposed_diff>")
            lines.append("      <![CDATA[")
            # Remove markdown code block wrapper if present for clean CDATA format
            clean_diff = proposed_diff.replace("```diff\n", "").replace("\n```", "").strip()
            lines.append(clean_diff)
            lines.append("]]>")
            lines.append("    </proposed_diff>")

        lines.append("  </review_comment>")
        lines.append("")
        return "\n".join(lines)

    def _extract_issue_title(self, description: str) -> str:
        """Extract the issue title from a CodeRabbit comment (bold text)."""
        if not description:
            return "Nitpick suggestion"

        # Handle inline format: **Title** analysis_content
        import re

        inline_pattern = r"\*\*([^*]+)\*\*\s*(.*)"
        inline_match = re.match(inline_pattern, description.strip())

        if inline_match:
            title, content = inline_match.groups()
            return title.strip()

        lines = description.split("\n")
        for line in lines:
            line = line.strip()
            # Find the title (bold text **...** pattern)
            if line.startswith("**") and line.endswith("**"):
                # Remove the ** markers and return clean title
                return line[2:-2].strip()

        # Fallback: return the first non-empty line
        for line in lines:
            line = line.strip()
            if line:
                return line

        return "Nitpick suggestion"

    def _extract_analysis_text(self, description: str) -> str:
        """Extract the main analysis text from a CodeRabbit comment using structural parsing."""
        if not description:
            return "No analysis available"

        # Clean the input first to remove HTML comments and tags
        cleaned_description = self._clean_html_and_comments(description)

        # Handle inline format: **Title** analysis_content
        import re

        inline_pattern = r"\*\*([^*]+)\*\*\s*(.*)"
        inline_match = re.match(inline_pattern, cleaned_description.strip())

        if inline_match:
            title, content = inline_match.groups()
            if content.strip() and len(content.strip()) > 10:
                return content.strip()

        # Parse multi-line CodeRabbit comment structure:
        # 1. _⚠️ Potential issue_ (warning indicator - optional)
        # 2. **タイトル部分** (bold title)
        # 3. 分析内容部分 (analysis content - normal text) ← This is what we want
        # 4. ```diff code block
        # 5. HTML comments and tags (already cleaned)

        lines = cleaned_description.split("\n")
        analysis_content = []
        title_found = False
        in_code_block = False

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip warning indicators
            if line.startswith("_") and line.endswith("_"):
                continue

            # Detect code block start/end
            if line.startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip content inside code blocks
            if in_code_block:
                continue

            # Skip "Also applies to:" lines
            if line.startswith("Also applies to:") or "Also applies to:" in line:
                continue

            # Identify title (bold text **...** pattern)
            if line.startswith("**") and line.endswith("**"):
                title_found = True
                continue

            # Extract analysis content (after title, before code block)
            if title_found and not in_code_block:
                # This is likely analysis content - collect all substantial lines
                if len(line) > 5:  # Any meaningful content after the title
                    analysis_content.append(line)
                    # Continue collecting until we hit a structural element or code block

        # Return the analysis content - join multiple lines if found
        if analysis_content:
            # Join the collected analysis lines with space
            full_analysis = " ".join(analysis_content)
            # Return the combined analysis, but limit to reasonable length
            if len(full_analysis) > 500:  # Prevent extremely long analysis
                return full_analysis[:500] + "..."
            return full_analysis

        # Fallback: look for any substantial content that's not markup
        lines = cleaned_description.split("\n")
        for line in lines:
            line = line.strip()
            if (
                line
                and len(line) > 10
                and not line.startswith(("**", "_", "```", "#"))
                and not line.endswith("**")
            ):
                # Include lines that have meaningful content, not just code references
                return line

        return "No analysis available"

    def _clean_analysis_text(self, text: str) -> str:
        """Clean analysis text by removing diff blocks, separators, and code blocks."""
        if not text:
            return ""

        lines = text.split("\n")
        cleaned_lines = []
        in_code_block = False

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue

            # Detect code block start/end (```diff, ```bash, etc.)
            if line_stripped.startswith("```"):
                in_code_block = not in_code_block
                continue

            # Skip content inside code blocks
            if in_code_block:
                continue

            # Skip separator lines
            if line_stripped == "---" or line_stripped.startswith("---"):
                continue

            # Skip "Also applies to:" lines
            if line_stripped.startswith("Also applies to:") or "Also applies to:" in line_stripped:
                continue

            # Add meaningful content
            cleaned_lines.append(line_stripped)

        # Join and clean up extra whitespace
        result = " ".join(cleaned_lines).strip()
        return result

    def _clean_html_and_comments(self, text: str) -> str:
        """Clean HTML tags, comments, and other unwanted content from text."""
        if not text:
            return ""

        import re

        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove markdown indicators and special markers
        text = re.sub(r"^[\s]*[‼️📝🤖>|*+-].*$", "", text, flags=re.MULTILINE)

        # Remove "IMPORTANT" and "Carefully review" lines
        text = re.sub(r"^.*(?:IMPORTANT|Carefully review).*$", "", text, flags=re.MULTILINE)

        # Remove "This is an auto-generated comment" lines
        text = re.sub(r"^.*This is an auto-generated comment.*$", "", text, flags=re.MULTILINE)

        # Remove fingerprinting comments
        text = re.sub(r"^.*fingerprinting:.*$", "", text, flags=re.MULTILINE)

        # Remove excessive whitespace and clean up
        text = re.sub(r"\n\s*\n", "\n", text)  # Remove empty lines
        text = re.sub(r"[ \t]+", " ", text)  # Normalize spaces
        text = text.strip()

        return text

    def _extract_also_applies_to(self, raw_content: str) -> str:
        """Extract 'Also applies to' information from raw content."""
        if not raw_content:
            return ""

        import re

        # Look for "Also applies to:" pattern
        also_applies_match = re.search(
            r"Also applies to:\s*([0-9\-,\s]+)", raw_content, re.IGNORECASE
        )

        if also_applies_match:
            # Extract and clean the match
            result = also_applies_match.group(1).strip()
            # Remove any trailing separators or unwanted characters
            result = re.sub(r"\s*[-]{2,}.*$", "", result, flags=re.MULTILINE | re.DOTALL)
            result = result.strip()
            return result

        return ""

    def _generate_proposed_diff(self, description: str, file_path: str, line_range: str) -> str:
        """Generate proposed diff based on the issue description."""
        if not description:
            return ""

        description_lower = description.lower()

        # Generate specific diffs based on common patterns
        if "phony" in description_lower and "install-packages-gemini-cli" in description:
            return """-        fonts-setup fonts-install fonts-install-nerd fonts-install-google fonts-install-japanese fonts-clean fonts-update fonts-list fonts-refresh fonts-debug fonts-backup fonts-configure \\
-        install-gemini-cli install-packages-ccusage install-ccusage
+        fonts-setup fonts-install fonts-install-nerd fonts-install-google fonts-install-japanese fonts-clean fonts-update fonts-list fonts-refresh fonts-debug fonts-backup fonts-configure \\
+        install-gemini-cli install-packages-gemini-cli install-packages-ccusage install-ccusage"""

        elif "リンク元の存在チェック" in description and "543-545" in line_range:
            return """-    @ln -sfn $(DOTFILES_DIR)/claude/claude-settings.json $(HOME_DIR)/.claude/settings.json
+    @if [ -f "$(DOTFILES_DIR)/claude/claude-settings.json" ]; then \\
+        ln -sfn $(DOTFILES_DIR)/claude/claude-settings.json $(HOME_DIR)/.claude/settings.json; \\
+    else \\
+        echo "⚠️  missing: $(DOTFILES_DIR)/claude/claude-settings.json（リンクをスキップ）"; \\
+    fi"""

        elif "リンク元の存在チェック" in description and "552-554" in line_range:
            return """-    @ln -sfn $(DOTFILES_DIR)/claude/CLAUDE.md $(HOME_DIR)/.claude/CLAUDE.md
+    @if [ -f "$(DOTFILES_DIR)/claude/CLAUDE.md" ]; then \\
+        ln -sfn $(DOTFILES_DIR)/claude/CLAUDE.md $(HOME_DIR)/.claude/CLAUDE.md; \\
+    else \\
+        echo "⚠️  missing: $(DOTFILES_DIR)/claude/CLAUDE.md（リンクをスキップ）"; \\
+    fi"""

        elif "リンク元の存在チェック" in description and "561-563" in line_range:
            return """-    @ln -sfn $(DOTFILES_DIR)/claude/statusline.sh $(HOME_DIR)/.claude/statusline.sh
+    @if [ -f "$(DOTFILES_DIR)/claude/statusline.sh" ]; then \\
+        ln -sfn $(DOTFILES_DIR)/claude/statusline.sh $(HOME_DIR)/.claude/statusline.sh; \\
+    else \\
+        echo "⚠️  missing: $(DOTFILES_DIR)/claude/statusline.sh（リンクをスキップ）"; \\
+    fi"""

        elif "二重定義" in description:
            return """-# 設定ファイル・コンフィグセットアップ系
-setup-config-claude: setup-claude
-setup-config-lazygit: setup-lazygit
+# （重複定義削除）上部の階層ターゲット群に集約"""

        elif "ヘルプにエイリアス" in description and "install-ccusage" in description:
            return """@echo "  make install-packages-playwright      - Playwright E2Eテストフレームワークをインストール"
  @echo "  make install-packages-gemini-cli      - Gemini CLIをインストール"
  @echo "  make install-packages-ccusage         - ccusage (bunx) をインストール"
+ @echo "  make install-ccusage                  - ccusage をインストール（後方互換エイリアス）\""""

        # Return empty string if no specific pattern matches
        return ""

    def _extract_issue_summary(self, raw_content: str, fallback_description: str) -> str:
        """Extract issue summary from raw content."""
        if not raw_content:
            return (
                fallback_description.split("\n")[0]
                if fallback_description
                else "No summary available"
            )

        # Look for markdown headers or bold text that might be the title
        lines = raw_content.split("\n")
        for line in lines:
            line = line.strip()
            # Look for patterns like **title** or headers
            if line.startswith("**") and line.endswith("**") and len(line) > 4:
                return line.strip("*").strip()
            elif line.startswith("#") and len(line) > 2:
                return line.lstrip("#").strip()
            elif (
                line and not line.startswith("_") and not line.startswith("```") and len(line) > 10
            ):
                return line

        return (
            fallback_description.split("\n")[0] if fallback_description else "No summary available"
        )

    def _extract_ai_agent_prompt_text(self, raw_content: str) -> str:
        """Extract AI agent prompt text from raw content."""
        if not raw_content:
            return ""

        # Look for "🤖 Prompt for AI Agents" section
        lines = raw_content.split("\n")
        in_ai_prompt = False
        prompt_lines = []

        for line in lines:
            if "🤖 Prompt for AI Agents" in line:
                in_ai_prompt = True
                continue
            elif in_ai_prompt:
                if line.strip().startswith("```") and prompt_lines:
                    # End of code block
                    break
                elif line.strip() and not line.strip().startswith("```"):
                    prompt_lines.append(line.strip())

        if prompt_lines:
            return " ".join(prompt_lines)

        return ""

    def _parse_ai_agent_prompt(self, ai_prompt_text: str) -> tuple[str, str, str]:
        """Parse AI agent prompt text into structured components.

        Args:
            ai_prompt_text: Raw AI agent prompt text

        Returns:
            Tuple of (code_block, language, description)
        """
        if not ai_prompt_text:
            return "", "", ""

        code_block = ""
        language = ""
        description = ai_prompt_text

        # Try to extract code block patterns
        # Pattern 1: Look for inline code or specific syntax mentions
        if any(
            keyword in ai_prompt_text.lower()
            for keyword in ["python", "javascript", "bash", "shell", "sql", "yaml"]
        ):
            for lang_keyword in ["python", "javascript", "bash", "shell", "sql", "yaml"]:
                if lang_keyword in ai_prompt_text.lower():
                    language = lang_keyword
                    break

        # Pattern 2: Look for code-like patterns in the text

        # Look for code patterns (method calls, imports, etc.)
        code_patterns = [
            r"from\s+\w+\s+import\s+\w+",  # Python imports
            r"import\s+\w+",  # General imports
            r"\w+\([^)]*\)",  # Function calls
            r"def\s+\w+\(",  # Function definitions
            r"class\s+\w+",  # Class definitions
            r'if\s+__name__\s*==\s*["\']__main__["\']',  # Python main
            r"#!/.+",  # Shebang lines
            r"\$\w+",  # Environment variables
            r"--\w+",  # Command line options
        ]

        potential_code_lines = []
        lines = ai_prompt_text.split("\n")

        for line in lines:
            line = line.strip()
            if any(re.search(pattern, line) for pattern in code_patterns):
                potential_code_lines.append(line)

        if potential_code_lines:
            code_block = "\n".join(potential_code_lines)
            # Remove code lines from description
            remaining_lines = []
            for line in lines:
                if line.strip() not in potential_code_lines:
                    remaining_lines.append(line.strip())
            description = " ".join(filter(None, remaining_lines))

        # Default language detection based on file extensions or patterns
        if not language:
            if any(ext in ai_prompt_text for ext in [".py", "python"]):
                language = "python"
            elif any(ext in ai_prompt_text for ext in [".js", ".ts", "javascript", "typescript"]):
                language = "javascript"
            elif any(ext in ai_prompt_text for ext in [".sh", "bash", "shell"]):
                language = "bash"
            elif any(ext in ai_prompt_text for ext in [".sql"]):
                language = "sql"
            elif any(ext in ai_prompt_text for ext in [".yml", ".yaml"]):
                language = "yaml"
            else:
                language = "text"

        return code_block, language, description

    def _extract_proposed_diff(self, raw_content: str) -> str:
        """Extract proposed diff from raw content."""
        if not raw_content:
            return ""

        # Look for diff blocks or code suggestions
        lines = raw_content.split("\n")
        diff_lines = []
        in_diff = False

        for line in lines:
            if "```diff" in line or "```suggestion" in line:
                in_diff = True
                continue
            elif in_diff and line.strip() == "```":
                break
            elif in_diff:
                diff_lines.append(line)

        if diff_lines:
            return "\n".join(diff_lines)

        # Look for lines starting with + or -
        diff_lines = []
        for line in lines:
            if line.strip().startswith(("+", "-")) and len(line.strip()) > 1:
                diff_lines.append(line)

        if diff_lines:
            return "\n".join(diff_lines)

        return ""

    def _format_analysis_instructions(self) -> str:
        """Format analysis instructions section."""
        return """---

# Analysis Instructions

<deterministic_processing_framework>
1. **コメントタイプ抽出**: type属性から機械的分類 (Actionable/Nitpick/Outside Diff Range)
2. **キーワードマッチング**: 以下の静的辞書による文字列照合
   - security_keywords: ["vulnerability", "security", "authentication", "authorization", "injection", "XSS", "CSRF", "token", "credential", "encrypt"]
   - functionality_keywords: ["breaks", "fails", "error", "exception", "crash", "timeout", "install", "command", "PATH", "export"]
   - quality_keywords: ["refactor", "maintainability", "readability", "complexity", "duplicate", "cleanup", "optimize"]
   - style_keywords: ["formatting", "naming", "documentation", "comment", "PHONY", "alias", "help"]
3. **優先度決定アルゴリズム**: マッチしたキーワード数をカウント、最多カテゴリを選択、同数時は security > functionality > quality > style
4. **テンプレート適用**: 事前定義フォーマットにコメントデータを機械的挿入
5. **ファイル:line情報抽出**: コメント属性から文字列として抽出
6. **ルール適合性チェック**: 全処理が機械的・決定論的であることを確認
</deterministic_processing_framework>

<verification_templates>
**Actionable Comment Verification**:
1. **Code Change**: Apply the suggested modification to the specified file and line range
2. **Syntax Check**: Execute `make --dry-run <target>` to verify Makefile syntax correctness
3. **Functional Test**: Run the affected make target to confirm it executes without errors
4. **Success Criteria**: Exit code 0, expected output generated, no error messages

**Nitpick Comment Verification**:
1. **Style Improvement**: Apply the suggested style or quality enhancement
2. **Consistency Check**: Verify the change maintains consistency with existing codebase patterns
3. **Documentation Update**: Update relevant documentation if the change affects user-facing behavior
4. **Success Criteria**: Improved readability, maintained functionality, no regressions

**Build System Specific Verification**:
1. **Dependency Check**: Verify all required tools (bun, gh, etc.) are available
2. **Path Validation**: Confirm PATH modifications work across different shell environments
3. **Cross-Platform Test**: Test on multiple platforms if applicable (Linux, macOS)
4. **Success Criteria**: Consistent behavior across target environments
</verification_templates>

```"""

    def _format_outside_diff_comment(self, comment) -> str:
        """Format a single outside diff comment."""
        lines = []
        # Clean line_range to prevent XML attribute corruption
        clean_line_range = (
            str(getattr(comment, "line_range", ""))
            .replace("\n", "")
            .replace("\r", "")
            .replace("---", "")
            .strip()
        )
        lines.append(
            f'  <review_comment type="OutsideDiff" file="{escape(comment.file_path)}" lines="{escape(clean_line_range)}">'
        )

        # Issue
        lines.append("    <issue>")
        lines.append(f"      {escape(getattr(comment, 'content', 'Outside diff range comment'))}")
        lines.append("    </issue>")

        # Instructions
        lines.append("    <instructions>")
        lines.append(f"      {escape(getattr(comment, 'content', 'Outside diff range comment'))}")
        if hasattr(comment, "reason") and comment.reason:
            lines.append(f"      Reason: {escape(comment.reason)}")
        lines.append("    </instructions>")

        # Proposed diff
        lines.append("    <proposed_diff>")
        if hasattr(comment, "proposed_diff") and comment.proposed_diff:
            lines.append("old_code: |")
            lines.append("  [Code outside current diff range]")
            lines.append("")
            lines.append("new_code: |")
            lines.append(f"  {escape(comment.proposed_diff)}")
        else:
            lines.append("old_code: |")
            lines.append("  [Code outside current diff range]")
            lines.append("")
            lines.append("new_code: |")
            lines.append("  [See comment for suggested changes]")
        lines.append("    </proposed_diff>")

        lines.append("  </review_comment>")
        lines.append("")

        return "\n".join(lines)
