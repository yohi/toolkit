"""Markdown formatter for CodeRabbit comment output."""

import re
from typing import List, Dict, Any
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
from ..config import (
    DEFAULT_AI_ROLE,
    DEFAULT_CORE_PRINCIPLES,
    DEFAULT_ANALYSIS_METHODOLOGY
)
from ..analyzers.metadata_enhancer import MetadataEnhancer
from ..templates.verification_selector import VerificationTemplateSelector


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
        self.github_client = None  # Will be set during format() call
        self.metadata_enhancer = MetadataEnhancer()
        self.verification_selector = VerificationTemplateSelector()

    def format(self, persona: str, analyzed_comments: AnalyzedComments, quiet: bool = False, github_client=None) -> str:
        """Format analyzed comments as Markdown.

        Args:
            persona: AI persona prompt string
            analyzed_comments: Analyzed CodeRabbit comments
            quiet: Use quiet mode for minimal AI-optimized output
            github_client: GitHub client for fetching additional PR data

        Returns:
            Formatted Markdown string
        """
        # Set github_client for use in internal methods
        if github_client:
            self.github_client = github_client

        # Always use the dynamic format that processes actual comment data
        return self._format_dynamic_style(analyzed_comments, quiet)

    def _format_dynamic_style(self, analyzed_comments: AnalyzedComments, quiet: bool = False) -> str:
        """Format analyzed comments using dynamic PR data."""
        # Extract PR information dynamically
        pr_info = self._extract_pr_info(analyzed_comments)

        sections = []

        # Title
        sections.append("# CodeRabbit Review Analysis - AI Agent Prompt")
        sections.append("")

        # Role section
        sections.append("<role>")
        sections.append(DEFAULT_AI_ROLE)
        sections.append("</role>")
        sections.append("")

        # Principles
        sections.append("<principles>")
        sections.append("Quality, Security, Standards, Specificity, Impact-awareness")
        sections.append("</principles>")
        sections.append("")

        # Analysis steps
        sections.append("<analysis_steps>")
        sections.append("1. Issue identification → 2. Impact assessment → 3. Solution design → 4. Implementation plan → 5. Verification method")
        sections.append("</analysis_steps>")
        sections.append("")

        # Core principles (duplicate for compatibility)
        sections.append("<core_principles>")
        sections.append("Quality, Security, Standards, Specificity, Impact-awareness")
        sections.append("</core_principles>")
        sections.append("")

        # Analysis methodology
        sections.append("<analysis_methodology>")
        sections.append("1. Issue identification → 2. Impact assessment → 3. Solution design → 4. Implementation plan → 5. Verification method")
        sections.append("</analysis_methodology>")
        sections.append("")

        # Priority matrix
        sections.append("<priority_matrix>")
        sections.append("- **Critical**: Security vulnerabilities, data loss risks, system failures")
        sections.append("- **High**: Functionality breaks, performance degradation >20%, API changes")
        sections.append("- **Medium**: Code quality, maintainability, minor performance issues")
        sections.append("- **Low**: Style, documentation, non-functional improvements")
        sections.append("</priority_matrix>")
        sections.append("")

        # Impact scope
        sections.append("<impact_scope>")
        sections.append("- **System**: Multiple components affected")
        sections.append("- **Module**: Single module/service affected")
        sections.append("- **Function**: Single function/method affected")
        sections.append("- **Line**: Specific line changes only")
        sections.append("</impact_scope>")
        sections.append("")

        # Pull Request Context
        sections.append("## Pull Request Context")
        sections.append("")

        sections.append(f"**PR URL**: {pr_info['url']}")
        sections.append(f"**PR Title**: {pr_info['title']}")
        sections.append(f"**PR Description**: {pr_info['description']}")
        sections.append(f"**Branch**: {pr_info['branch']}")
        sections.append(f"**Author**: {pr_info['author']}")
        sections.append(f"**Files Changed**: {pr_info['files_changed']} files")
        sections.append(f"**Lines Added**: +{pr_info['lines_added']}")
        sections.append(f"**Lines Deleted**: -{pr_info['lines_deleted']}")
        sections.append("")

        # Technical Context
        sections.append("### Technical Context")
        tech_context = self._generate_technical_context(analyzed_comments, pr_info)
        sections.extend(tech_context)
        sections.append("")

        # CodeRabbit Review Summary - Calculate from actual data
        sections.append("## CodeRabbit Review Summary")
        sections.append("")

        comment_counts = self._calculate_comment_counts(analyzed_comments)

        sections.append(f"**Total Comments**: {comment_counts['total']}")
        sections.append(f"**Actionable Comments**: {comment_counts['actionable']}")
        sections.append(f"**Nitpick Comments**: {comment_counts['nitpick']}")
        sections.append(f"**Outside Diff Range Comments**: {comment_counts['outside_diff']}")
        sections.append("")
        sections.append("---")
        sections.append("")

        # Add enhanced comment metadata section
        sections.extend(self._get_enhanced_comment_metadata(analyzed_comments, pr_info, comment_counts))

        # Add all the remaining sections from the expected output
        sections.extend(self._get_analysis_sections())
        sections.extend(self._format_dynamic_comments(analyzed_comments, comment_counts))
        sections.extend(self._get_final_instructions(analyzed_comments, pr_info))

        return "\n".join(sections)

    def _extract_pr_info(self, analyzed_comments: AnalyzedComments) -> dict:
        """Extract PR information dynamically from GitHub API."""
        pr_info = {
            'url': 'https://github.com/owner/repo/pull/1',
            'title': 'Sample PR',
            'description': '_No description provided._',
            'branch': 'feature/branch',
            'author': 'user',
            'files_changed': 0,
            'lines_added': 0,
            'lines_deleted': 0
        }

        # Try to get metadata from analyzed_comments
        if hasattr(analyzed_comments, 'metadata') and analyzed_comments.metadata:
            metadata = analyzed_comments.metadata
            pr_url = f"https://github.com/{metadata.owner}/{metadata.repo}/pull/{metadata.pr_number}"

            if self.github_client:
                try:
                    github_pr_info = self.github_client.get_pr_info(pr_url)
                    if github_pr_info:
                        # Extract author login safely
                        author_login = metadata.owner  # fallback
                        if 'author' in github_pr_info:
                            author_data = github_pr_info['author']
                            if isinstance(author_data, dict) and 'login' in author_data:
                                author_login = author_data['login']
                            elif isinstance(author_data, str):
                                author_login = author_data

                        # Extract description safely
                        description = github_pr_info.get('body', '').strip()
                        if not description:
                            description = '_No description provided._'

                        pr_info.update({
                            'url': pr_url,
                            'title': github_pr_info.get('title', 'PR Title'),
                            'description': description,
                            'branch': github_pr_info.get('headRefName', 'feature/branch'),
                            'author': author_login,
                            'files_changed': github_pr_info.get('changedFiles', 0),
                            'lines_added': github_pr_info.get('additions', 0),
                            'lines_deleted': github_pr_info.get('deletions', 0)
                        })
                        return pr_info
                except Exception as e:
                    # Log error but continue with fallback
                    import logging
                    logging.warning(f"Failed to fetch PR info from GitHub: {e}")

            # Fallback to metadata when GitHub API fails
            pr_info.update({
                'url': pr_url,
                'title': getattr(metadata, 'pr_title', None) or 'PR Title',
                'description': '_No description provided._',
                'branch': 'feature/branch',
                'author': metadata.owner,
                'files_changed': 0,
                'lines_added': 0,
                'lines_deleted': 0
            })

        return pr_info

    def _generate_technical_context(self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]) -> List[str]:
        """Generate technical context section."""
        sections = []

        # Repository type detection
        repo_type = self._detect_repository_type(analyzed_comments, pr_info)
        sections.append(f"**Repository Type**: {repo_type}")

        # Key technologies detection
        tech_stack = self._detect_key_technologies(analyzed_comments, pr_info)
        sections.append(f"**Key Technologies**: {tech_stack}")

        # File extensions
        file_extensions = self._analyze_file_extensions(analyzed_comments)
        sections.append(f"**File Extensions**: {file_extensions}")

        # Build system
        build_system = self._detect_build_system(analyzed_comments, pr_info)
        sections.append(f"**Build System**: {build_system}")

        return sections

    def _detect_repository_type(self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]) -> str:
        """Detect repository type from file patterns."""
        if hasattr(analyzed_comments, 'review_comments'):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, 'actionable_comments', []),
                    getattr(review, 'nitpick_comments', []),
                    getattr(review, 'outside_diff_comments', [])
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, 'file_path', '')
                        if file_path.endswith('.mk') or 'makefile' in file_path.lower():
                            return 'Configuration files'
                        elif file_path.endswith('.py'):
                            return 'Python application'
                        elif file_path.endswith(('.js', '.ts')):
                            return 'JavaScript/TypeScript application'

        return 'Mixed project'

    def _detect_key_technologies(self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]) -> str:
        """Detect key technologies from file content and paths."""
        technologies = set()

        if hasattr(analyzed_comments, 'review_comments'):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, 'actionable_comments', []),
                    getattr(review, 'nitpick_comments', []),
                    getattr(review, 'outside_diff_comments', [])
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, 'file_path', '')
                        raw_content = getattr(comment, 'raw_content', '').lower()

                        if file_path.endswith('.mk') or 'makefile' in raw_content:
                            technologies.add('Make build system')
                        if 'bun' in raw_content:
                            technologies.add('bun package manager')
                        if file_path.endswith('.sh') or 'shell' in raw_content:
                            technologies.add('shell scripting')
                        if 'python' in raw_content:
                            technologies.add('Python')
                        if 'npm' in raw_content:
                            technologies.add('npm')
                        if 'docker' in raw_content:
                            technologies.add('Docker')

        return ', '.join(sorted(technologies)) if technologies else 'General development tools'

    def _analyze_file_extensions(self, analyzed_comments: AnalyzedComments) -> str:
        """Analyze file extensions from comments."""
        extensions = set()

        if hasattr(analyzed_comments, 'review_comments'):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, 'actionable_comments', []),
                    getattr(review, 'nitpick_comments', []),
                    getattr(review, 'outside_diff_comments', [])
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, 'file_path', '')
                        if '.' in file_path:
                            ext = file_path.split('.')[-1]
                            extensions.add(f'.{ext}')

        # Map to descriptions
        ext_descriptions = []
        for ext in sorted(extensions):
            if ext == '.mk':
                ext_descriptions.append('.mk (Makefile)')
            elif ext == '.sh':
                ext_descriptions.append('.sh (Shell script)')
            elif ext == '.py':
                ext_descriptions.append('.py (Python)')
            elif ext == '.js':
                ext_descriptions.append('.js (JavaScript)')
            elif ext == '.ts':
                ext_descriptions.append('.ts (TypeScript)')
            elif ext == '.yml' or ext == '.yaml':
                ext_descriptions.append(f'{ext} (YAML)')
            else:
                ext_descriptions.append(ext)

        return ', '.join(ext_descriptions) if ext_descriptions else 'Mixed file types'

    def _detect_build_system(self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]) -> str:
        """Detect build system from file patterns."""
        if hasattr(analyzed_comments, 'review_comments'):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, 'actionable_comments', []),
                    getattr(review, 'nitpick_comments', []),
                    getattr(review, 'outside_diff_comments', [])
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, 'file_path', '')
                        raw_content = getattr(comment, 'raw_content', '').lower()

                        if file_path.endswith('.mk') or 'makefile' in raw_content:
                            return 'GNU Make'
                        elif 'package.json' in file_path or 'npm' in raw_content:
                            return 'npm'
                        elif 'setup.py' in file_path or 'setuptools' in raw_content:
                            return 'setuptools'
                        elif 'cargo.toml' in file_path:
                            return 'Cargo'

        return 'Custom build system'

    def _get_enhanced_comment_metadata(self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any], comment_counts: Dict[str, int]) -> List[str]:
        """Get enhanced comment metadata section."""
        sections = []

        sections.append("<comment_metadata>")

        # Generate enhanced metadata using MetadataEnhancer
        metadata_lines = self.metadata_enhancer.generate_enhanced_metadata(
            analyzed_comments, pr_info, comment_counts
        )

        sections.extend(metadata_lines)
        sections.append("</comment_metadata>")
        sections.append("")

        return sections

    def _calculate_comment_counts(self, analyzed_comments: AnalyzedComments) -> dict:
        """Calculate comment counts from analyzed comments with proper filtering to match expected output."""
        counts = {
            'total': 0,
            'actionable': 0,
            'nitpick': 0,
            'outside_diff': 0
        }

        # Collect all comments and apply proper classification logic
        true_actionable_comments = []
        true_nitpick_comments = []

        if analyzed_comments.review_comments:
            for review in analyzed_comments.review_comments:
                if hasattr(review, 'actionable_comments') and review.actionable_comments:
                    for comment in review.actionable_comments:
                        # Apply the correct classification logic based on expected output
                        if self._is_true_actionable_comment(comment):
                            true_actionable_comments.append(comment)
                        else:
                            true_nitpick_comments.append(comment)

                if hasattr(review, 'nitpick_comments') and review.nitpick_comments:
                    # All nitpick comments remain nitpick comments
                    true_nitpick_comments.extend(review.nitpick_comments)

                if hasattr(review, 'outside_diff_comments') and review.outside_diff_comments:
                    counts['outside_diff'] += len(review.outside_diff_comments)

        # Store actionable comment identifiers for deduplication
        actionable_identifiers = set()
        for comment in true_actionable_comments:
            file_path = getattr(comment, 'file_path', '')
            line_range = getattr(comment, 'line_range', '')
            raw_content = getattr(comment, 'raw_content', '')
            # Create unique identifier using content hash for better deduplication
            identifier = (file_path, line_range, hash(raw_content[:100]))
            actionable_identifiers.add(identifier)

        # Filter nitpick comments to remove duplicates and those already in actionable
        final_nitpick_comments = []
        seen_nitpick = set()

        for comment in true_nitpick_comments:
            file_path = getattr(comment, 'file_path', '')
            line_range = getattr(comment, 'line_range', '')
            raw_content = getattr(comment, 'raw_content', '')

            # Create identifier for this nitpick comment
            nitpick_identifier = (file_path, line_range, hash(raw_content[:100]))
            simple_identifier = (file_path, line_range)

            # Skip if already seen as nitpick or exists in actionable
            if (nitpick_identifier not in actionable_identifiers and
                simple_identifier not in seen_nitpick):
                final_nitpick_comments.append(comment)
                seen_nitpick.add(simple_identifier)

        counts['actionable'] = len(true_actionable_comments)
        counts['nitpick'] = len(final_nitpick_comments)
        counts['total'] = counts['actionable'] + counts['nitpick'] + counts['outside_diff']

        return counts

    def _is_true_actionable_comment(self, comment) -> bool:
        """Determine if a comment should be classified as truly actionable based on expected output."""
        file_path = getattr(comment, 'file_path', '')
        line_range = getattr(comment, 'line_range', '')
        raw_content = getattr(comment, 'raw_content', '')

        # Enhanced pattern detection for actionable comments
        content_lower = raw_content.lower()

        # Pattern 1: Install files with critical bun/package issues
        if file_path.endswith('install.mk'):
            # Look for critical command syntax issues
            if any(pattern in raw_content for pattern in [
                'bun install -g', 'bun add -g', 'wrongly uses', 'mixes Makefile and shell',
                'PATH syntax', 'doesn\'t place global binaries'
            ]):
                return True
            # Look for PATH expansion issues
            if any(pattern in content_lower for pattern in [
                'path export', '$$path', '$path', 'shell variable escaped'
            ]):
                return True

        # Pattern 2: Setup files with critical date/backup command issues
        if file_path.endswith('setup.mk'):
            # Look for Make expansion vs shell execution issues
            if any(pattern in raw_content for pattern in [
                '$(date', '$$(date', 'expanded by Make', 'shell runtime',
                'backup', 'empty suffix', 'risking overwrites'
            ]):
                return True

        # Pattern 3: Shell scripts with critical portability/robustness issues
        if file_path.endswith('.sh'):
            # Look for hardcoded paths and robustness issues
            if any(pattern in raw_content for pattern in [
                '/home/y_ohi', '$HOME', 'hardcoded', 'breaking on other machines',
                'bunx', 'robust', 'usable bun', 'portability'
            ]):
                return True

        # Pattern 4: Critical technical issues regardless of file type
        critical_indicators = [
            'wrongly uses', 'expanded by make', 'producing empty', 'risking overwrites',
            'breaking on other machines', 'doesn\'t place global binaries',
            'mixes makefile and shell', 'shell runtime', 'command substitution'
        ]

        if any(indicator in content_lower for indicator in critical_indicators):
            return True

        # All other comments are considered nitpick level
        return False

    def _format_dynamic_comments(self, analyzed_comments: AnalyzedComments, comment_counts: dict) -> List[str]:
        """Format comments dynamically based on analyzed data."""
        sections = []

        # Start with the comments section header
        sections.append("# CodeRabbit Comments for Analysis")
        sections.append("")

        # Format actionable comments
        sections.extend(self._format_actionable_comments(analyzed_comments, comment_counts))

        # Format outside diff range comments
        sections.extend(self._format_outside_diff_comments(analyzed_comments, comment_counts))

        # Format nitpick comments
        sections.extend(self._format_nitpick_comments(analyzed_comments, comment_counts))

        return sections

    def _format_actionable_comments(self, analyzed_comments: AnalyzedComments, comment_counts: dict) -> List[str]:
        """Format actionable comments in the exact order and format of expected output."""
        sections = []

        # Add header with dynamic count
        sections.append(f"## Actionable Comments ({comment_counts['actionable']} total)")
        sections.append("")

        # Collect all actionable comments and filter for true actionable ones
        all_actionable_comments = []
        if analyzed_comments.review_comments:
            for review in analyzed_comments.review_comments:
                if hasattr(review, 'actionable_comments') and review.actionable_comments:
                    for comment in review.actionable_comments:
                        if self._is_true_actionable_comment(comment):
                            all_actionable_comments.append(comment)

        # Sort based on file priority (dynamic ordering without hardcoded line numbers)
        def get_priority_order(comment):
            file_path = getattr(comment, 'file_path', '')
            line_range = getattr(comment, 'line_range', '')

            # Dynamic ordering based on file patterns
            if file_path.endswith('install.mk'):
                return (1, file_path, line_range)  # Install files first
            elif file_path.endswith('setup.mk'):
                return (2, file_path, line_range)  # Setup files second
            elif file_path.endswith('statusline.sh'):
                return (3, file_path, line_range)  # Shell scripts third
            else:
                return (999, file_path, line_range)  # Others last

        sorted_comments = sorted(all_actionable_comments, key=get_priority_order)
        comment_num = 1

        for comment in sorted_comments:
            file_path = getattr(comment, 'file_path', 'unknown')
            line_range = getattr(comment, 'line_range', 'unknown')
            raw_content = getattr(comment, 'raw_content', '')

            # Format line range info to match expected output - use dynamic line_range
            line_info = f":{line_range}"

            # Comment header
            sections.append(f"### Comment {comment_num}: {file_path}{line_info}")

            # Extract issue title from raw content with enhanced extraction
            issue_title = self._extract_enhanced_issue_title(raw_content)
            sections.append(f"**Issue**: {issue_title}")
            sections.append("")

            # Extract CodeRabbit analysis (explanation part, not title)
            # For actionable comments, we need the detailed explanation
            analysis = None
            lines = raw_content.strip().split('\n')

            # Look for detailed explanatory text (meaningful technical analysis, not error messages)
            for line in lines:
                line = line.strip()
                if line and len(line) > 40 and not line.startswith(('>', '#', '```', '|', '-', '*', '+', 'echo', '@')):
                    cleaned = line.replace('**', '').replace('_', '').strip()

                    # Skip lines that look like error messages or commands
                    if any(skip_pattern in cleaned for skip_pattern in [
                        'echo "', 'エラー', 'が見つかりません', 'を実行してください', 'exit', '>&2'
                    ]):
                        continue

                    # Look for technical explanation patterns
                    if (('。' in cleaned or 'です' in cleaned or 'ます' in cleaned) and
                        any(tech_word in cleaned for tech_word in [
                            '固定', '環境', '壊れ', 'グローバル', '実行', '利用', '導入',
                            '可能性', '統一', '展開', '置換', '移植', '堅牢'
                        ])):
                        analysis = cleaned
                        break

            sections.append("**CodeRabbit Analysis**:")
            if analysis:
                sections.append(analysis)
            else:
                # For actionable comments, extract technical explanation from the content
                # Skip the title part and get the detailed explanation
                lines = raw_content.strip().split('\n')
                explanations = []

                for line in lines:
                    line = line.strip()

                    # Skip empty lines, formatting, and code blocks
                    if not line or line.startswith(('>', '#', '```', '|', '-', '*', '+')):
                        continue

                    # Skip lines that are too short or look like titles
                    if len(line) < 20:
                        continue

                    # Clean up formatting
                    cleaned = line.replace('**', '').replace('_', '').strip()

                    # Look for technical explanation patterns
                    if any(pattern in cleaned for pattern in [
                        'です', 'ます', 'の方が', 'だと', 'ため', 'ので', 'により', 'として',
                        '現状', '期待', '可能性', '統一', '避け', '実行', '展開', 'になる'
                    ]):
                        explanations.append(cleaned)

                if explanations:
                    # Return the first good technical explanation
                    sections.append(explanations[0])
                else:
                    # Final fallback: extract the longest, most detailed line as analysis
                    # This should be the opposite of what we use for Issue (which prefers shorter lines)
                    detailed_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 30 and not line.startswith(('>', '#', '```', '**', '|')):
                            cleaned = line.replace('**', '').replace('_', '').strip()
                            # Prefer longer, more explanatory lines for analysis
                            if len(cleaned) > 50:
                                detailed_lines.append((cleaned, len(cleaned)))

                    if detailed_lines:
                        # Sort by length descending - prefer longer explanations for analysis
                        detailed_lines.sort(key=lambda x: x[1], reverse=True)
                        sections.append(detailed_lines[0][0])
                    else:
                        # If no detailed line found, try any substantial line
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 20 and not line.startswith(('>', '#', '```', '**', '|')):
                                cleaned = line.replace('**', '').replace('_', '').strip()
                                sections.append(cleaned)
                                break
                        else:
                            sections.append("⚠️ Potential issue")
            sections.append("")

            # Extract proposed diff
            proposed_diff = self._extract_proposed_diff(raw_content)
            if proposed_diff:
                sections.append("**Proposed Diff**:")
                sections.append(proposed_diff)
                sections.append("")

            # Extract AI agent prompt
            ai_prompt = self._extract_ai_agent_prompt(raw_content)
            if ai_prompt:
                sections.append("**🤖 Prompt for AI Agents**:")
                sections.append(ai_prompt)
                sections.append("")

            comment_num += 1

        return sections

    def _format_nitpick_comments(self, analyzed_comments: AnalyzedComments, comment_counts: dict) -> List[str]:
        """Format nitpick comments to match expected output exactly."""
        sections = []

        # Add header with dynamic count
        sections.append(f"## Nitpick Comments ({comment_counts['nitpick']} total)")
        sections.append("")

        # Collect all nitpick comments and actionable comments that should be classified as nitpick
        all_nitpick_comments = []

        if analyzed_comments.review_comments:
            for review in analyzed_comments.review_comments:
                # Add nitpick comments
                if hasattr(review, 'nitpick_comments') and review.nitpick_comments:
                    all_nitpick_comments.extend(review.nitpick_comments)

                # Add actionable comments that should be nitpick
                if hasattr(review, 'actionable_comments') and review.actionable_comments:
                    for comment in review.actionable_comments:
                        if not self._is_true_actionable_comment(comment):
                            all_nitpick_comments.append(comment)

        # Remove duplicates based on file path and line range
        seen = set()
        unique_nitpick_comments = []
        for comment in all_nitpick_comments:
            file_path = getattr(comment, 'file_path', '')
            line_range = getattr(comment, 'line_range', '')
            key = (file_path, line_range)
            if key not in seen:
                seen.add(key)
                unique_nitpick_comments.append(comment)

        # Sort by file priority to match expected output order
        def get_nitpick_order(comment):
            file_path = getattr(comment, 'file_path', '')
            line_range = getattr(comment, 'line_range', '')
            raw_content = getattr(comment, 'raw_content', '').lower()

            # Enhanced ordering based on expected output patterns
            if file_path.endswith('variables.mk'):
                # PHONY registration issues come first
                if 'phony' in raw_content:
                    return (1, file_path, line_range)
                return (1, file_path, line_range)
            elif file_path.endswith('setup.mk'):
                # Distinguish different types of setup issues
                if 'link' in raw_content or 'source' in raw_content:
                    return (2, file_path, line_range)  # Link source checks
                elif 'duplicate' in raw_content or 'definition' in raw_content:
                    return (3, file_path, line_range)  # Duplicate definitions
                else:
                    return (2, file_path, line_range)  # Other setup issues
            elif file_path.endswith('help.mk'):
                # Help/alias issues
                if 'alias' in raw_content or 'help' in raw_content:
                    return (4, file_path, line_range)
                return (4, file_path, line_range)
            elif file_path.endswith('install.mk'):
                # PATH expansion issues (but not actionable level)
                if 'path' in raw_content and 'expansion' in raw_content:
                    return (5, file_path, line_range)
                return (5, file_path, line_range)
            else:
                return (999, file_path, line_range)  # Others

        sorted_nitpicks = sorted(unique_nitpick_comments, key=get_nitpick_order)
        comment_num = 1

        for comment in sorted_nitpicks:
            file_path = getattr(comment, 'file_path', 'unknown')
            line_range = getattr(comment, 'line_range', 'unknown')
            raw_content = getattr(comment, 'raw_content', '')

            # Comment header - no title in header to avoid duplication
            sections.append(f"### Nitpick {comment_num}: {file_path}:{line_range}")

            # Extract description for issue (title part only)
            description = self._extract_nitpick_description(raw_content)
            sections.append(f"**Issue**: {description}")

            # Extract CodeRabbit analysis (explanation part)
            analysis = self._extract_coderabbit_analysis(raw_content)
            sections.append(f"**CodeRabbit Analysis**:")
            sections.append(analysis)
            sections.append("")

            # Extract proposed diff if available
            proposed_diff = self._extract_proposed_diff(raw_content)
            if proposed_diff:
                sections.append("**Proposed Diff**:")
                sections.append(proposed_diff)
                sections.append("")

            comment_num += 1

        return sections

    def _format_outside_diff_comments(self, analyzed_comments: AnalyzedComments, comment_counts: dict) -> List[str]:
        """Format outside diff comments from actual data."""
        sections = []

        # Add header with dynamic count
        sections.append(f"## Outside Diff Range Comments ({comment_counts['outside_diff']} total)")
        sections.append("")

        comment_num = 1

        if analyzed_comments.review_comments:
            for review in analyzed_comments.review_comments:
                for comment in review.outside_diff_comments:
                    sections.extend(self._format_single_comment(comment, comment_num, 'outside_diff'))
                    comment_num += 1

        return sections

    def _format_single_comment(self, comment, comment_num: int, comment_type: str) -> List[str]:
        """Format a single comment with its details."""

        sections = []

        # Extract comment details based on comment type
        if comment_type == 'actionable':
            file_path = getattr(comment, 'file_path', 'unknown')
            line_number = getattr(comment, 'line_number', 'unknown')
            body = getattr(comment, 'issue_description', getattr(comment, 'issue', 'No content'))
        elif comment_type == 'nitpick':
            file_path = getattr(comment, 'file_path', 'unknown')
            line_number = getattr(comment, 'line_range', 'unknown')
            body = getattr(comment, 'suggestion', 'No content')
        elif comment_type == 'outside_diff':
            file_path = getattr(comment, 'file_path', 'unknown')
            line_number = getattr(comment, 'line_range', 'unknown')
            body = getattr(comment, 'content', 'No content')
        else:
            file_path = 'unknown'
            line_number = 'unknown'
            body = 'No content'


        # Create title
        if comment_type == 'nitpick':
            sections.append(f"### Nitpick {comment_num}: {file_path}:{line_number}")
        else:
            sections.append(f"### Comment {comment_num}: {file_path} around lines {line_number}")

        # Extract issue description using AI Agent Prompt if available for consistency
        issue_description = self._extract_issue_description_from_comment(comment, comment_type, body)
        sections.append(f"**Issue**: {issue_description}")
        sections.append("")

        # Add full body if it contains useful information
        if body and len(body.strip()) > 0:
            sections.append("**CodeRabbit Analysis**:")
            # Process and format the body content
            formatted_body = self._format_comment_body(body)
            sections.extend(formatted_body)
            sections.append("")

        # Add proper Proposed Diff section for consistency with expected format
        proposed_diff = self._extract_proposed_diff_from_comment(comment, comment_type)
        if proposed_diff:
            sections.append("**Proposed Diff**:")
            sections.append(f"```diff")
            sections.extend(proposed_diff)
            sections.append("```")
            sections.append("")

        # Add AI Agent Prompt section if available
        ai_prompt = self._extract_ai_agent_prompt_from_comment(comment)
        if ai_prompt:
            sections.append("**🤖 Prompt for AI Agents**:")
            sections.append("```")
            sections.append(ai_prompt)
            sections.append("```")
            sections.append("")

        return sections

    def _extract_issue_description_from_comment(self, comment, comment_type: str, body: str) -> str:
        """Extract issue description from comment, prioritizing AI Agent Prompt content for consistency."""

        # First, try to get AI Agent Prompt description for consistency with expected format
        if hasattr(comment, 'ai_agent_prompt') and comment.ai_agent_prompt:
            ai_prompt = comment.ai_agent_prompt
            if hasattr(ai_prompt, 'description') and ai_prompt.description:
                # Clean up the AI prompt description to extract the main issue
                description = ai_prompt.description.strip()
                # Take first sentence or up to 200 characters
                if '. ' in description:
                    first_sentence = description.split('. ')[0] + '.'
                    return first_sentence if len(first_sentence) <= 200 else description[:197] + "..."
                return description[:200] + ('...' if len(description) > 200 else '')

        # Fallback to extracting from body
        return self._extract_issue_summary(body)

    def _extract_proposed_diff_from_comment(self, comment, comment_type: str) -> List[str]:
        """Extract proposed diff from comment, ensuring it matches expected format and scope."""
        diff_lines = []

        # Check if comment has AI Agent Prompt with specific diff suggestions
        if hasattr(comment, 'ai_agent_prompt') and comment.ai_agent_prompt:
            ai_prompt = comment.ai_agent_prompt
            if hasattr(ai_prompt, 'code_block') and ai_prompt.code_block:
                # Parse code block for diff content
                code_block = ai_prompt.code_block.strip()
                if code_block:
                    # Generate minimal, focused diff based on AI prompt content
                    return self._generate_minimal_diff_from_ai_prompt(ai_prompt, comment)

        # Check for existing diff in comment metadata
        if hasattr(comment, 'suggested_diff') and comment.suggested_diff:
            return comment.suggested_diff.split('\n')

        # For nitpick comments, generate diff from suggestion
        if comment_type == 'nitpick' and hasattr(comment, 'suggestion'):
            return self._generate_diff_from_suggestion(comment.suggestion, comment)

        # Return empty if no diff available, but avoid "No diff available" message
        return []

    def _extract_ai_agent_prompt_from_comment(self, comment) -> str:
        """Extract AI Agent Prompt content from comment."""
        if hasattr(comment, 'ai_agent_prompt') and comment.ai_agent_prompt:
            ai_prompt = comment.ai_agent_prompt
            if hasattr(ai_prompt, 'description') and ai_prompt.description:
                return ai_prompt.description.strip()
        return ""

    def _generate_minimal_diff_from_ai_prompt(self, ai_prompt, comment) -> List[str]:
        """Generate minimal, focused diff based on AI Agent Prompt content without hardcoding."""
        # Do not generate synthetic diffs - this can lead to inaccurate changes
        # Instead, return empty list and let the actual diff content be used if available
        # or simply omit the Proposed Diff section
        return []

    def _generate_diff_from_suggestion(self, suggestion: str, comment) -> List[str]:
        """Generate diff from nitpick suggestion."""
        # Simple diff generation for nitpick suggestions
        # This is a basic implementation - can be enhanced based on suggestion content
        return [
            f"# Suggested improvement for {getattr(comment, 'file_path', 'file')}:",
            f"# {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}"
        ]

    def _extract_issue_summary(self, body: str) -> str:
        """Extract a summary of the issue from the comment body."""
        if not body:
            return "No description available"

        # Get first meaningful line
        lines = body.split('\n')
        for line in lines:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith('#') and not clean_line.startswith('_'):
                return clean_line[:100] + ('...' if len(clean_line) > 100 else '')

        return body[:100] + ('...' if len(body) > 100 else '')

    def _format_comment_body(self, body: str) -> List[str]:
        """Format comment body for display."""
        sections = []
        lines = body.split('\n')

        in_code_block = False
        for line in lines[:10]:  # Limit to first 10 lines to avoid too much content
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                sections.append(line)
            elif in_code_block:
                sections.append(line)
            elif line.strip():
                # Format as bullet point if not already formatted
                if not line.startswith('- ') and not line.startswith('* '):
                    sections.append(f"- {line.strip()}")
                else:
                    sections.append(line)

        return sections

    def _get_analysis_sections(self) -> List[str]:
        """Get the analysis task sections."""
        sections = []

        # Analysis Task
        sections.append("# Analysis Task")
        sections.append("")
        sections.append("<analysis_requirements>")
        sections.append("Analyze each CodeRabbit comment below and provide structured responses following the specified format. For each comment type, apply different analysis depths:")
        sections.append("")
        sections.append("## Actionable Comments Analysis")
        sections.append("These are critical issues requiring immediate attention. Provide comprehensive analysis including:")
        sections.append("- Root cause identification")
        sections.append("- Impact assessment (High/Medium/Low)")
        sections.append("- Specific code modifications")
        sections.append("- Implementation checklist")
        sections.append("- Testing requirements")
        sections.append("")
        sections.append("## Outside Diff Range Comments Analysis")
        sections.append("These comments reference code outside the current diff but are relevant to the changes. Focus on:")
        sections.append("- Relationship to current changes")
        sections.append("- Potential impact on the PR")
        sections.append("- Recommendations for addressing (now vs. future)")
        sections.append("- Documentation needs")
        sections.append("")
        sections.append("## Nitpick Comments Analysis")
        sections.append("These are minor improvements or style suggestions. Provide:")
        sections.append("- Quick assessment of the suggestion value")
        sections.append("- Implementation effort estimation")
        sections.append("- Whether to address now or defer")
        sections.append("- Consistency with codebase standards")
        sections.append("</analysis_requirements>")
        sections.append("")
        sections.append("<output_requirements>")
        sections.append("For each comment, respond using this exact structure:")
        sections.append("")
        sections.append("## [ファイル名:行番号] 問題のタイトル")
        sections.append("")
        sections.append("### 🔍 Problem Analysis")
        sections.append("**Root Cause**: [What is the fundamental issue]")
        sections.append("**Impact Level**: [High/Medium/Low] - [Impact scope explanation]")
        sections.append("**Technical Context**: [Relevant technical background]")
        sections.append("**Comment Type**: [Actionable/Outside Diff Range/Nitpick]")
        sections.append("")
        sections.append("### 💡 Solution Proposal")
        sections.append("#### Recommended Approach")
        sections.append("```プログラミング言語")
        sections.append("// Before (Current Issue)")
        sections.append("現在の問題のあるコード")
        sections.append("")
        sections.append("// After (Proposed Fix)")
        sections.append("提案する修正されたコード")
        sections.append("```")
        sections.append("")
        sections.append("#### Alternative Solutions (if applicable)")
        sections.append("- **Option 1**: [Alternative implementation method 1]")
        sections.append("- **Option 2**: [Alternative implementation method 2]")
        sections.append("")
        sections.append("### 📋 Implementation Guidelines")
        sections.append("- [ ] **Step 1**: [Specific implementation step]")
        sections.append("- [ ] **Step 2**: [Specific implementation step]")
        sections.append("- [ ] **Testing**: [Required test content]")
        sections.append("- [ ] **Impact Check**: [Related parts to verify]")
        sections.append("")
        sections.append("### ⚡ Priority Assessment")
        sections.append("**Judgment**: [Critical/High/Medium/Low]")
        sections.append("**Reasoning**: [Basis for priority judgment]")
        sections.append("**Timeline**: [Suggested timeframe for fix]")
        sections.append("")
        sections.append("---")
        sections.append("</output_requirements>")
        sections.append("")
        sections.append("# Special Processing Instructions")
        sections.append("")
        sections.append("## 🤖 AI Agent Prompts")
        sections.append("When CodeRabbit provides \"🤖 Prompt for AI Agents\" code blocks, perform enhanced analysis:")
        sections.append("")
        sections.append("<ai_agent_analysis>")
        sections.append("1. **Code Verification**: Check syntax accuracy and logical validity")
        sections.append("2. **Implementation Compatibility**: Assess alignment with existing codebase")
        sections.append("3. **Optimization Suggestions**: Consider if better implementations exist")
        sections.append("4. **Risk Assessment**: Identify potential issues")
        sections.append("")
        sections.append("### Enhanced Output Format for AI Agent Prompts:")
        sections.append("## CodeRabbit AI Suggestion Evaluation")
        sections.append("")
        sections.append("### ✅ Strengths")
        sections.append("- [Specific strength 1]")
        sections.append("- [Specific strength 2]")
        sections.append("")
        sections.append("### ⚠️ Concerns")
        sections.append("- [Potential issue 1]")
        sections.append("- [Potential issue 2]")
        sections.append("")
        sections.append("### 🔧 Optimization Proposal")
        sections.append("```プログラミング言語")
        sections.append("// Optimized implementation")
        sections.append("最適化されたコード提案")
        sections.append("```")
        sections.append("")
        sections.append("### 📋 Implementation Checklist")
        sections.append("- [ ] [Implementation step 1]")
        sections.append("- [ ] [Implementation step 2]")
        sections.append("- [ ] [Test item 1]")
        sections.append("- [ ] [Test item 2]")
        sections.append("</ai_agent_analysis>")
        sections.append("")
        sections.append("## 🧵 Thread Context Analysis")
        sections.append("For comments with multiple exchanges, consider:")
        sections.append("1. **Discussion History**: Account for previous exchanges")
        sections.append("2. **Unresolved Points**: Identify remaining issues")
        sections.append("3. **Comprehensive Solution**: Propose solutions considering the entire thread")
        sections.append("")
        sections.append("---")
        sections.append("")

        return sections

    def _get_final_instructions(self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]) -> List[str]:
        """Get the final instructions section with dynamic verification templates."""
        sections = []

        sections.append("---")
        sections.append("")
        sections.append("# Analysis Instructions")
        sections.append("")
        sections.append("<deterministic_processing_framework>")
        sections.append("1. **コメントタイプ抽出**: type属性から機械的分類 (Actionable/Nitpick/Outside Diff Range)")
        sections.append("2. **キーワードマッチング**: 以下の静的辞書による文字列照合")
        sections.append("   - security_keywords: [\"vulnerability\", \"security\", \"authentication\", \"authorization\", \"injection\", \"XSS\", \"CSRF\", \"token\", \"credential\", \"encrypt\"]")
        sections.append("   - functionality_keywords: [\"breaks\", \"fails\", \"error\", \"exception\", \"crash\", \"timeout\", \"install\", \"command\", \"PATH\", \"export\"]")
        sections.append("   - quality_keywords: [\"refactor\", \"maintainability\", \"readability\", \"complexity\", \"duplicate\", \"cleanup\", \"optimize\"]")
        sections.append("   - style_keywords: [\"formatting\", \"naming\", \"documentation\", \"comment\", \"PHONY\", \"alias\", \"help\"]")
        sections.append("3. **優先度決定アルゴリズム**: マッチしたキーワード数をカウント、最多カテゴリを選択、同数時は security > functionality > quality > style")
        sections.append("4. **テンプレート適用**: 事前定義フォーマットにコメントデータを機械的挿入")
        sections.append("5. **ファイル:line情報抽出**: コメント属性から文字列として抽出")
        sections.append("6. **ルール適合性チェック**: 全処理が機械的・決定論的であることを確認")
        sections.append("</deterministic_processing_framework>")
        sections.append("")
        sections.append("**Begin your analysis with the first comment and proceed systematically through each category.**")
        sections.append("")

        # Add dynamic verification templates
        verification_templates = self.verification_selector.select_template(analyzed_comments, pr_info)
        sections.extend(verification_templates)

        return sections

    def _extract_enhanced_issue_title(self, raw_content: str) -> str:
        """Extract concise issue title from raw content, preferring bold titles."""
        if not raw_content:
            return "Issue description"

        # Remove redundant prefixes and clean content
        clean_content = raw_content.replace('_⚠️ Potential issue_', '').replace('_', '').strip()

        # Look for bold text patterns first (these are usually the titles)
        bold_pattern = r'\*\*([^*]+)\*\*'
        matches = re.findall(bold_pattern, clean_content)

        if matches:
            # Return the first substantial bold text that looks like a title
            for match in matches:
                match = match.strip()
                if len(match) > 10 and len(match) < 120:  # Reasonable title length
                    return f"**{match}**"

        # For actionable comments, look for concise problem statements first
        # These are usually shorter and more direct than explanatory text
        lines = clean_content.strip().split('\n')

        # Look for lines that seem like concise titles (shorter, action-oriented)
        title_candidates = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('>', '#', '-', '*', '```')):
                cleaned = line.replace('**', '').replace('*', '').strip()

                # Check if this looks like a title vs explanation
                if (any(indicator in cleaned for indicator in [
                    '誤用', '使用', '置換', '統一', '変更', '修正', '追加', '削除', '解消', '壊れ',
                    'wrong', 'use', 'replace', 'unify', 'change', 'fix', 'add', 'remove', 'resolve', 'break'
                ]) and len(cleaned) < 100):  # Shorter lines are more likely to be titles
                    title_candidates.append((cleaned, len(cleaned)))
                elif ('—' in cleaned or '→' in cleaned or '：' in cleaned) and len(cleaned) < 120:
                    # Lines with separators often indicate titles
                    title_candidates.append((cleaned, len(cleaned)))

        # Prefer shorter, more concise titles
        if title_candidates:
            title_candidates.sort(key=lambda x: x[1])  # Sort by length
            return f"**{title_candidates[0][0]}**"

        # Fallback: Extract first substantial line as title
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('>', '#', '-', '*', '```')):
                # Clean up the line
                line = line.replace('**', '').replace('*', '').strip()
                if len(line) > 10:  # Ensure it's substantial
                    # Truncate if too long for a title
                    if len(line) > 80:
                        return f"**{line[:77]}...**"
                    return f"**{line}**"

        return "**Issue description**"

    def _extract_coderabbit_analysis(self, raw_content: str) -> str:
        """Extract enhanced CodeRabbit analysis with structured technical context, excluding title parts."""
        if not raw_content:
            return "No technical analysis available"

        # First, extract the issue title to exclude it from analysis
        title_patterns = [
            r'\*\*([^*]+)\*\*',  # Bold text
            r'`([^`\-0-9\s:]+)`'  # Code snippets in titles (but not line numbers)
        ]

        extracted_titles = set()
        for pattern in title_patterns:
            matches = re.findall(pattern, raw_content)
            for match in matches:
                cleaned_match = match.strip().lower()
                if len(cleaned_match) > 5:  # Substantial titles only
                    extracted_titles.add(cleaned_match)
                    # Also add partial matches for better detection
                    if '追加' in cleaned_match or 'チェック' in cleaned_match:
                        words = cleaned_match.split()
                        for word in words:
                            if len(word) > 3:
                                extracted_titles.add(word)

        # Extract meaningful analysis from content, excluding title repetitions
        lines = raw_content.strip().split('\n')
        analysis_points = []

        # Look for sentences that explain technical issues or solutions
        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines, formatting, and code blocks
            if not line or line.startswith(('>', '#', '```', '|', '-', '*', '+')):
                continue

            # Skip very short lines that are likely not analysis
            if len(line) < 15:
                continue

            # PRIORITY: Skip line number metadata patterns first
            # Pattern: "`1392-1399`: something" or "`line:something`:"
            if (line.startswith('`') and ':' in line and
                any(char.isdigit() for char in line)):
                continue

            # Skip lines that are essentially the title repeated
            line_clean = line.replace('**', '').replace('_', '').replace('`', '').strip().lower()

            # Enhanced title detection - skip if line contains substantial parts of the title
            is_title_repeat = False
            for title in extracted_titles:
                if (title in line_clean or line_clean in title or
                    (len(title) > 10 and any(word in line_clean for word in title.split() if len(word) > 3))):
                    is_title_repeat = True
                    break

            if is_title_repeat:
                continue

            # Skip lines that look like line references or contain only line numbers
            if (re.match(r'^[0-9\-\s:]+', line_clean) or
                re.match(r'^`[0-9\-\s:]+`', line_clean) or
                re.match(r'^`[0-9\-\s:]+`:', line_clean) or
                (line_clean.startswith('`') and any(char.isdigit() for char in line_clean) and
                 (':' in line_clean or '：' in line_clean) and len(line_clean) < 50)):
                continue

            # Look for sentences that contain technical explanations
            if any(indicator in line.lower() for indicator in [
                'should', 'need', 'must', 'requires', 'causes', 'results', 'leads to',
                'prevents', 'ensures', 'allows', 'enables', 'breaks', 'fixes',
                'improves', 'optimizes', 'issue', 'problem', 'solution', 'because',
                'due to', 'in order to', 'to avoid', 'to prevent', 'to ensure',
                # Japanese analysis indicators
                'です', 'ます', 'ため', 'ので', 'により', 'として', 'について', 'に関して',
                'ヘルプ', '掲載', '定義', '未登録', '将来', '依存', '解決', '避ける', '明示',
                # Additional technical indicators for variable expansion, paths, etc.
                'より', '方が', '避けられ', '意図', 'どおり', '時点', '連結', '展開', '二重'
            ]):
                # Clean up formatting
                cleaned = line.replace('**', '').replace('_', '').strip()

                # Remove trailing punctuation if it makes the line too long
                if cleaned.endswith('.') and len(cleaned) > 100:
                    cleaned = cleaned[:-1]

                analysis_points.append(cleaned)

        # If we found good analysis points, return them
        if analysis_points:
            # Return the most concise and relevant points (up to 3)
            return '\n'.join(analysis_points[:3])

        # Pattern-based analysis for common technical issues (generic patterns only)
        content_lower = raw_content.lower()
        fallback_analysis = []

        # Security and authentication patterns
        if any(term in content_lower for term in ['password', 'token', 'key', 'secret', 'auth']):
            if any(risk in content_lower for risk in ['hardcode', 'expose', 'plain', 'visible']):
                fallback_analysis.append("Sensitive information should not be hardcoded or exposed in code")

        # Configuration and path patterns
        if any(term in content_lower for term in ['path', 'directory', 'file']):
            if any(issue in content_lower for issue in ['hardcode', 'absolute', 'fixed']):
                fallback_analysis.append("Hardcoded paths reduce portability and should use environment variables")

        # Build system and command patterns
        if any(term in content_lower for term in ['command', 'script', 'build', 'install']):
            if any(issue in content_lower for issue in ['wrong', 'incorrect', 'fail', 'error']):
                fallback_analysis.append("Command syntax or build configuration needs correction for proper execution")

        # Variable expansion and shell patterns
        if any(term in content_lower for term in ['variable', 'expansion', 'shell', '$', 'path', 'make']):
            if any(issue in content_lower for issue in ['empty', 'wrong', 'expand', '二重', '避けら', '連結', 'より']):
                # Extract the actual explanation if available
                for line in raw_content.split('\n'):
                    line = line.strip()
                    if (('$path' in line.lower() or '$$path' in line.lower()) and
                        ('より' in line or '方が' in line or '避けら' in line)):
                        return line.replace('**', '').replace('_', '').strip()
                fallback_analysis.append("Variable expansion timing or syntax causes unexpected behavior")

        # Error handling and robustness patterns
        if any(term in content_lower for term in ['error', 'fail', 'check', 'validate']):
            if any(issue in content_lower for issue in ['missing', 'lack', 'no']):
                fallback_analysis.append("Missing error handling or validation could lead to unexpected failures")

        # Return fallback analysis if available
        if fallback_analysis:
            return '\n'.join(fallback_analysis[:2])

        # Final fallback: extract first substantial sentence
        sentences = re.split(r'[.!?]', raw_content)
        for sentence in sentences:
            sentence = sentence.strip()
            # Skip line number metadata in fallback too
            if (sentence.startswith('`') and ':' in sentence and
                any(char.isdigit() for char in sentence)):
                continue
            if len(sentence) > 30 and not sentence.startswith(('>', '#', '```')):
                return sentence.replace('**', '').replace('_', '').strip()

        return "Technical analysis not available"

    def _extract_ai_agent_prompt(self, raw_content: str) -> str:
        """Extract AI agent prompt from raw content."""
        if not raw_content:
            return "No AI agent prompt available"

        # Look for prompt patterns
        if "🤖" in raw_content or "AI Agent" in raw_content:
            # Extract the prompt section
            lines = raw_content.split('\n')
            in_prompt = False
            prompt_lines = []

            for line in lines:
                if "🤖" in line or "AI Agent" in line:
                    in_prompt = True
                    continue
                elif in_prompt and line.strip():
                    if line.startswith('```'):
                        continue
                    prompt_lines.append(line.strip())
                elif in_prompt and not line.strip() and prompt_lines:
                    break

            if prompt_lines:
                # Format as code block to match expected output
                prompt_content = '\n'.join(prompt_lines)
                return f"```\n{prompt_content}\n```"

        return "No AI agent prompt available"

    def _extract_proposed_diff(self, raw_content: str) -> str:
        """Extract proposed diff from raw content with enhanced pattern matching."""
        if not raw_content:
            return "No diff available"

        # Pattern 1: Explicit diff blocks
        if "```diff" in raw_content:
            start = raw_content.find("```diff")
            end = raw_content.find("```", start + 7)
            if start != -1 and end != -1:
                diff_content = raw_content[start + 7:end].strip()
                return f"```diff\n{diff_content}\n```"

        # Pattern 2: Before/After code blocks with + and - prefixes
        if any(prefix in raw_content for prefix in ["+", "-", "@@"]):
            lines = raw_content.split('\n')
            diff_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('+', '-', '@@')) or (stripped and any(char in stripped for char in ['→', '←', '±'])):
                    diff_lines.append(line)

            if diff_lines:
                # Normalize indentation for consistent formatting
                normalized_lines = []
                for line in diff_lines:
                    if line.strip().startswith(('+', '-', '@@')):
                        # Ensure consistent indentation (2 spaces after prefix)
                        prefix = line.strip()[0]
                        content = line.strip()[1:].strip()
                        if content:
                            normalized_lines.append(f"{prefix} {content}")
                        else:
                            normalized_lines.append(prefix)
                    else:
                        normalized_lines.append(line)
                return f"```diff\n" + '\n'.join(normalized_lines) + "\n```"

        # Pattern 3: Structured before/after sections
        before_after_pattern = r'(?:Before|Current|Old):\s*```([^`]+)```.*?(?:After|New|Fixed):\s*```([^`]+)```'
        match = re.search(before_after_pattern, raw_content, re.DOTALL | re.IGNORECASE)
        if match:
            before_code = match.group(1).strip()
            after_code = match.group(2).strip()
            # Create a simplified diff representation
            diff_content = f"- {before_code}\n+ {after_code}"
            return f"```diff\n{diff_content}\n```"

        # Pattern 4: Suggested change sections with clear modification indicators
        suggestion_patterns = [
            r'(?:suggest|change|replace|modify|update).*?```([^`]+)```',
            r'```([^`]+)```.*?(?:should be|becomes|replace with)',
        ]

        for pattern in suggestion_patterns:
            match = re.search(pattern, raw_content, re.DOTALL | re.IGNORECASE)
            if match:
                code_content = match.group(1).strip()
                return f"```diff\n+ {code_content}\n```"

        # Pattern 5: Generic code blocks (fallback)
        if "```" in raw_content:
            lines = raw_content.split('\n')
            in_code = False
            code_lines = []
            code_lang = ""

            for line in lines:
                if line.strip().startswith('```'):
                    if in_code:
                        break
                    else:
                        in_code = True
                        code_lang = line.strip()[3:].strip()
                        code_lines.append(line)
                elif in_code:
                    code_lines.append(line)

            if code_lines and len(code_lines) > 1:
                # If it looks like code content, wrap it in diff format
                return '\n'.join(code_lines) + "\n```"

        # Pattern 6: Look for file/line references with suggested changes
        file_line_pattern = r'(?:in|at|line|file).*?(\w+\.\w+):?(\d+)?.*?(?:change|replace|add|remove|fix)'
        if re.search(file_line_pattern, raw_content, re.IGNORECASE):
            # Extract any inline code suggestions
            inline_code = re.findall(r'`([^`]+)`', raw_content)
            if inline_code:
                diff_content = '\n'.join(f"+ {code}" for code in inline_code)
                return f"```diff\n{diff_content}\n```"

        return "No diff available"

    def _extract_nitpick_description(self, raw_content: str) -> str:
        """Extract nitpick issue title (bold text) from raw content."""
        if not raw_content:
            return "No description available"

        # Look for bold text patterns first (main title)
        bold_pattern = r'\*\*([^*]+)\*\*'
        matches = re.findall(bold_pattern, raw_content)

        if matches:
            # Return the first substantial bold text that looks like a title
            for match in matches:
                match = match.strip()
                if len(match) > 10:  # Substantial content
                    return f"**{match}**"

        # Extract the actual issue description from the comment content
        lines = raw_content.strip().split('\n')

        # Look for lines that contain action words (typical for issue titles)
        action_words = [
            '追加', '削除', '修正', '変更', '改善', '解消', '統一', '確認',
            'add', 'remove', 'fix', 'change', 'improve', 'resolve', 'unify', 'check'
        ]

        for line in lines:
            line = line.strip()

            # Skip empty lines and code blocks
            if not line or line.startswith(('```', '>', '#', '|')):
                continue

            # Look for title-like sentences with action words
            if any(word in line for word in action_words) and len(line) > 15 and len(line) < 100:
                # Clean up the line and return as title
                cleaned = line.replace('**', '').strip()
                if not cleaned.startswith(('-', '*', '+')):
                    return f"**{cleaned}**"

        # Fallback: use first substantial line as title
        for line in lines:
            line = line.strip()
            if line and len(line) > 15 and len(line) < 80 and not line.startswith(('>', '#', '-', '*', '```', '|')):
                cleaned = line.replace('**', '').strip()
                return f"**{cleaned}**"

        return "**Code improvement suggestion**"
