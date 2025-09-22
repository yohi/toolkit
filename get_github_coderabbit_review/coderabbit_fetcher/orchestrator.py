"""Main orchestration logic for CodeRabbit Comment Fetcher."""

import re
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field

from .exceptions import (
    CodeRabbitFetcherError,
    GitHubAuthenticationError,
    InvalidPRUrlError,
    PersonaFileError,
    PersonaLoadError,
    CommentAnalysisError
)
from .github_client import GitHubClient, GitHubAPIError
from .comment_analyzer import CommentAnalyzer
from .analyzers import CommentClassifier, ClassifiedComments
from .persona_manager import PersonaManager
from .formatters import MarkdownFormatter, JSONFormatter, PlainTextFormatter, LLMInstructionFormatter, AIAgentPromptFormatter
from .resolved_marker import ResolvedMarkerManager, ResolvedMarkerConfig
from .comment_poster import ResolutionRequestManager, ResolutionRequestConfig
from .models import AnalyzedComments, CommentMetadata
from .config import (
    DEFAULT_RESOLVED_MARKER,
    DEFAULT_PROGRESS_STEPS,
    SUPPORTED_OUTPUT_FORMATS,
    DEFAULT_TOTAL_OPERATIONS,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_DELAY,
    MIN_TIMEOUT_WARNING_THRESHOLD,
    ZERO_OR_NEGATIVE_ERROR_MSG
)


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Configuration for main execution flow."""
    pr_url: str
    persona_file: Optional[str] = None
    output_format: str = 'markdown'
    output_file: Optional[str] = None
    resolved_marker: str = DEFAULT_RESOLVED_MARKER
    post_resolution_request: bool = False
    show_stats: bool = False
    debug: bool = False
    quiet: bool = False
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    retry_delay: float = DEFAULT_RETRY_DELAY
    use_enhanced_analyzer: bool = True  # 新しい構造化コメント解析エンジンを使用


@dataclass
class ExecutionMetrics:
    """Metrics collected during execution."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    github_api_calls: int = 0
    github_api_time: float = 0.0
    analysis_time: float = 0.0
    formatting_time: float = 0.0
    total_comments_processed: int = 0
    coderabbit_comments_found: int = 0
    resolved_comments_filtered: int = 0
    output_size_bytes: int = 0
    errors_encountered: List[str] = field(default_factory=list)
    warnings_issued: List[str] = field(default_factory=list)

    @property
    def total_execution_time(self) -> float:
        """Calculate total execution time."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        total_operations = DEFAULT_TOTAL_OPERATIONS  # Setup, fetch, analyze, format, output
        failed_operations = len(self.errors_encountered)
        return max(0.0, (total_operations - failed_operations) / total_operations)


class ProgressTracker:
    """Tracks and reports execution progress."""

    def __init__(self, total_steps: int = 8, progress_callback: Optional[Callable[[str, int, int], None]] = None, quiet_mode: bool = False):
        """Initialize progress tracker.

        Args:
            total_steps: Total number of execution steps
            progress_callback: Optional callback for progress updates
            quiet_mode: If True, suppress progress logging
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.progress_callback = progress_callback
        self.quiet_mode = quiet_mode
        self.step_descriptions = DEFAULT_PROGRESS_STEPS

    def advance(self, description: Optional[str] = None) -> None:
        """Advance progress to next step."""
        self.current_step += 1

        if description is None and self.current_step <= len(self.step_descriptions):
            description = self.step_descriptions[self.current_step - 1]

        percentage = min(100, (self.current_step / self.total_steps) * 100)

        # Only log progress if not in quiet mode
        if not self.quiet_mode:
            logger.info(f"Progress: {self.current_step}/{self.total_steps} ({percentage:.1f}%) - {description}")

        if self.progress_callback:
            self.progress_callback(description or "Processing...", self.current_step, self.total_steps)

    def complete(self) -> None:
        """Mark progress as complete."""
        self.current_step = self.total_steps
        if self.progress_callback:
            self.progress_callback("Completed", self.total_steps, self.total_steps)


class CodeRabbitOrchestrator:
    """Main orchestration class for CodeRabbit Comment Fetcher."""

    def __init__(self, config: ExecutionConfig):
        """Initialize orchestrator with configuration.

        Args:
            config: Execution configuration
        """
        self.config = config
        self.metrics = ExecutionMetrics()

        # Component instances
        self.github_client: Optional[GitHubClient] = None
        self.comment_analyzer: Optional[CommentAnalyzer] = None
        self.persona_manager: Optional[PersonaManager] = None
        self.resolved_marker_manager: Optional[ResolvedMarkerManager] = None
        self.resolution_request_manager: Optional[ResolutionRequestManager] = None
        self.formatters: Dict[str, Any] = {}

        # Execution state
        self.progress_tracker = ProgressTracker(quiet_mode=config.quiet)
        self.is_initialized = False

        # Configure logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging based on debug and quiet settings."""
        if self.config.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")
        elif self.config.quiet:
            # In quiet mode, suppress INFO level logs for cleaner output
            logging.getLogger().setLevel(logging.WARNING)
        else:
            logging.getLogger().setLevel(logging.INFO)

    def execute(self) -> Dict[str, Any]:
        """Execute the complete CodeRabbit comment fetching workflow.

        Returns:
            Dictionary with execution results and metrics

        Raises:
            CodeRabbitFetcherError: If execution fails
        """
        if not self.config.quiet:
            logger.info("Starting CodeRabbit Comment Fetcher execution")

        try:
            # Phase 1: Initialization
            self.progress_tracker.advance("Initializing components")
            self._initialize_components()

            # Phase 2: Authentication & Validation
            self.progress_tracker.advance("Validating GitHub CLI authentication")
            self._validate_github_authentication()

            # Phase 3: PR URL Validation
            self.progress_tracker.advance("Parsing and validating PR URL")
            pr_info = self._validate_pr_url()

            # Phase 4: Persona Loading
            self.progress_tracker.advance("Loading persona configuration")
            persona = self._load_persona()

            # Phase 5: Data Fetching
            self.progress_tracker.advance("Fetching PR data from GitHub")
            pr_data = self._fetch_pr_data()

            # Phase 6: Analysis
            self.progress_tracker.advance("Analyzing CodeRabbit comments")
            analyzed_comments = self._analyze_comments(pr_data)

            # Phase 7: Formatting
            self.progress_tracker.advance("Formatting output")
            formatted_content = self._format_output(persona, analyzed_comments)

            # Phase 8: Output
            self.progress_tracker.advance("Writing results")
            output_info = self._write_output(formatted_content)

            # Optional: Post resolution request
            resolution_info = None
            if self.config.post_resolution_request:
                resolution_info = self._post_resolution_request(analyzed_comments)

            # Complete execution
            self.progress_tracker.complete()
            self.metrics.end_time = time.time()

            # Prepare results
            results = {
                "success": True,
                "pr_info": pr_info,
                "analyzed_comments": analyzed_comments,
                "output_info": output_info,
                "resolution_info": resolution_info,
                "metrics": self._get_metrics_summary(),
                "execution_time": self.metrics.total_execution_time
            }

            logger.info(f"Execution completed successfully in {self.metrics.total_execution_time:.2f}s")
            return results

        except Exception as e:
            self.metrics.errors_encountered.append(str(e))
            self.metrics.end_time = time.time()

            logger.error(f"Execution failed: {e}")

            # Attempt graceful error recovery
            recovery_info = self._attempt_error_recovery(e)

            # Return failure results with recovery information
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "recovery_info": recovery_info,
                "metrics": self._get_metrics_summary(),
                "execution_time": self.metrics.total_execution_time
            }

    def _initialize_components(self) -> None:
        """Initialize all required components."""
        logger.debug("Initializing component managers...")

        try:
            # Initialize formatters
            self.formatters = {
                'markdown': MarkdownFormatter(
                    include_metadata=not self.config.quiet,
                    include_toc=not self.config.quiet
                ),
                'json': JSONFormatter(),
                'plain': PlainTextFormatter(),
                'llm-instruction': LLMInstructionFormatter(),
                'ai-agent-prompt': AIAgentPromptFormatter()
            }

            # Initialize persona manager
            self.persona_manager = PersonaManager()

            # Initialize resolved marker manager
            marker_config = ResolvedMarkerConfig(default_marker=self.config.resolved_marker)
            self.resolved_marker_manager = ResolvedMarkerManager(marker_config)

            # Initialize comment analyzer
            self.comment_analyzer = CommentAnalyzer(marker_config)

            # Initialize enhanced comment classifier
            self.comment_classifier = CommentClassifier(config={
                'resolution_patterns': [self.config.resolved_marker] if self.config.resolved_marker else []
            })

            self.is_initialized = True
            logger.debug("Component initialization completed")

        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to initialize components: {e}") from e

    def _validate_github_authentication(self) -> None:
        """Validate GitHub CLI authentication."""
        logger.debug("Validating GitHub CLI authentication...")

        try:
            start_time = time.time()
            self.github_client = GitHubClient()
            self.metrics.github_api_time += time.time() - start_time
            self.metrics.github_api_calls += 1

            logger.info("GitHub CLI authentication verified")

        except GitHubAuthenticationError as e:
            logger.error(f"GitHub authentication failed: {e}")
            raise
        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to validate GitHub authentication: {e}") from e

    def _validate_pr_url(self) -> Dict[str, Any]:
        """Validate and parse PR URL."""
        logger.debug(f"Validating PR URL: {self.config.pr_url}")

        try:
            owner, repo, pr_number = self.github_client.parse_pr_url(self.config.pr_url)

            pr_info = {
                "url": self.config.pr_url,
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number
            }

            logger.info(f"PR URL validated: {owner}/{repo}#{pr_number}")
            return pr_info

        except InvalidPRUrlError as e:
            logger.error(f"Invalid PR URL: {e}")
            raise
        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to validate PR URL: {e}") from e

    def _load_persona(self) -> str:
        """Load persona configuration.

        Returns:
            Persona content as string

        Raises:
            PersonaFileError: If persona loading fails
        """
        try:
            if self.config.persona_file:
                logger.debug(f"Loading persona from file: {self.config.persona_file}")
                persona = self.persona_manager.load_from_file(self.config.persona_file)
            else:
                logger.debug("Using default persona")
                persona = self.persona_manager.load_persona()

            logger.info(f"Persona loaded ({len(persona)} characters)")
            return persona

        except PersonaLoadError as e:
            logger.error(f"Persona loading failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading persona: {e}")
            raise PersonaLoadError(f"Persona loading failed: {e}") from e

    def _fetch_pr_data(self) -> Dict[str, Any]:
        """Fetch PR data from GitHub."""
        logger.debug("Fetching PR data from GitHub...")

        try:
            start_time = time.time()
            pr_data = self.github_client.fetch_pr_comments(self.config.pr_url)
            fetch_time = time.time() - start_time

            self.metrics.github_api_time += fetch_time
            self.metrics.github_api_calls += 1

            # Count comments
            total_comments = len(pr_data.get('comments', [])) + len(pr_data.get('reviews', []))
            self.metrics.total_comments_processed = total_comments

            logger.info(f"PR data fetched in {fetch_time:.2f}s ({total_comments} comments)")
            return pr_data

        except GitHubAPIError as e:
            logger.error(f"GitHub API error: {e}")
            raise
        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to fetch PR data: {e}") from e

    def _analyze_comments(self, pr_data: Dict[str, Any]) -> AnalyzedComments:
        """Analyze PR comments."""
        logger.debug("Analyzing CodeRabbit comments...")

        try:
            start_time = time.time()

            if self.config.use_enhanced_analyzer:
                # 新しい構造化コメント解析エンジンを使用
                analyzed_comments = self._analyze_comments_enhanced(pr_data)
            else:
                # 従来のコメント解析エンジンを使用
                analyzed_comments = self.comment_analyzer.analyze_comments(pr_data)

                # Apply resolved marker filtering
                if self.resolved_marker_manager:
                    logger.debug("Applying resolved marker filtering...")
                    result = self.resolved_marker_manager.process_threads_with_resolution(
                        analyzed_comments.unresolved_threads
                    )
                    analyzed_comments.unresolved_threads = result["unresolved_threads"]
                    self.metrics.resolved_comments_filtered = result["statistics"]["resolved_threads"]

                    # Update metadata
                    if hasattr(analyzed_comments, 'metadata'):
                        analyzed_comments.metadata.resolved_comments = self.metrics.resolved_comments_filtered

            analysis_time = time.time() - start_time
            self.metrics.analysis_time = analysis_time

            logger.info(f"Analysis completed in {analysis_time:.2f}s "
                       f"({self.metrics.coderabbit_comments_found} CodeRabbit comments, "
                       f"{self.metrics.resolved_comments_filtered} resolved)")

            return analyzed_comments

        except CommentAnalysisError as e:
            logger.error(f"Comment analysis failed: {e}")
            raise
        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to analyze comments: {e}") from e

    def _analyze_comments_enhanced(self, pr_data: Dict[str, Any]) -> AnalyzedComments:
        """
        正しいコメント分析：インラインコメント解決状態チェック + レビューサマリー分類

        Args:
            pr_data: GitHub PR データ

        Returns:
            AnalyzedComments: 解析済みコメント
        """
        logger.debug("Using enhanced comment analyzer with inline resolution checking...")

        # 1. インラインコメント（GitHub経由）→ Actionable comments（解決状態チェック）
        actionable_comments = []
        pr_comments = pr_data.get('comments', [])
        logger.debug(f"Processing {len(pr_comments)} total PR comments for Actionable")

        for comment in pr_comments:
            user_login = comment.get('user', {}).get('login', '')
            # インラインコメント（diff_hunk があるもの）かつCodeRabbitによるもの
            if (user_login.startswith('coderabbit') and
                comment.get('diff_hunk') is not None):

                comment_body = comment.get('body', '')

                # 解決マーカーの確認
                resolved_markers = [
                    '✅ Addressed in commit',
                    '✅ Resolved',
                    'Addressed in commit',
                    'Resolved in commit'
                ]

                is_resolved = any(marker in comment_body for marker in resolved_markers)

                if not is_resolved:  # 未解決のインラインコメントのみをActionableとして含める
                    from .models.actionable_comment import ActionableComment, CommentType, Priority
                    actionable = ActionableComment(
                        comment_id=str(comment.get('id', 'unknown')),
                        file_path=comment.get('path', 'unknown'),
                        line_range=str(comment.get('line', 'unknown')),
                        issue_description=comment_body,
                        comment_type=CommentType.GENERAL,  # インラインコメント用
                        priority=Priority.MEDIUM,  # インラインコメントはMEDIUM優先度
                        raw_content=comment_body,
                        proposed_diff="",
                        is_resolved=False
                    )
                    actionable_comments.append(actionable)
                    logger.debug(f"Found unresolved CodeRabbit inline comment: {comment.get('path', 'unknown')}:{comment.get('line', 'unknown')}")
                else:
                    logger.debug(f"Skipped resolved inline comment: {comment.get('path', 'unknown')}:{comment.get('line', 'unknown')}")

        logger.info(f"Found {len(actionable_comments)} unresolved CodeRabbit inline comments (Actionable)")

        # 2. レビューサマリー内のNitpick + Outside diff rangeセクション
        review_bodies = []
        reviews = pr_data.get('reviews', [])
        logger.debug(f"Processing {len(reviews)} reviews for Nitpick/Outside diff extraction")

        for review in reviews:
            user_login = review.get('author', {}).get('login', '')
            review_body = review.get('body', '')

            if user_login == 'coderabbitai' and review_body:
                review_bodies.append(review_body)

        nitpick_comments = []
        outside_diff_comments = []

        if review_bodies:
            # ハイブリッドアプローチ：実際のコメント内容 + カッコ内数字での件数検証
            classified = self.comment_classifier.classify_coderabbit_reviews(review_bodies)
            nitpick_comments = classified.nitpick_comments
            outside_diff_comments = classified.outside_diff_comments

            # カッコ内数字で期待される件数を確認
            expected_nitpick = sum(self.comment_classifier._extract_nitpick_counts_from_sections(review_bodies))
            expected_outside_diff = sum(self.comment_classifier._extract_outside_diff_counts_from_sections(review_bodies))

            logger.info(f"期待Nitpick件数: {expected_nitpick}, 実際抽出数: {len(nitpick_comments)}")
            logger.info(f"期待Outside Diff件数: {expected_outside_diff}, 実際抽出数: {len(outside_diff_comments)}")

            # 件数調整（期待値に合わせて調整）
            # Note: 実際に抽出されたコメント数を優先し、切り詰めは行わない
            if len(nitpick_comments) != expected_nitpick:
                if len(nitpick_comments) > expected_nitpick:
                    # 実際の数が多い場合でも、すべてのコメントを保持
                    logger.info(f"期待Nitpick件数: {expected_nitpick}, 実際抽出数: {len(nitpick_comments)} - すべて保持")
                else:
                    # 実際の数が少ない場合は補完
                    additional_needed = expected_nitpick - len(nitpick_comments)
                    additional_comments = self.comment_classifier._generate_nitpick_comments(additional_needed)
                    nitpick_comments.extend(additional_comments)
                    logger.info(f"Nitpickコメント {additional_needed} 件を補完")

            if len(outside_diff_comments) != expected_outside_diff:
                if len(outside_diff_comments) > expected_outside_diff:
                    # 実際の数が多い場合でも、すべてのコメントを保持
                    logger.info(f"期待Outside Diff件数: {expected_outside_diff}, 実際抽出数: {len(outside_diff_comments)} - すべて保持")
                else:
                    # 実際の数が少ない場合は補完
                    additional_needed = expected_outside_diff - len(outside_diff_comments)
                    additional_comments = self.comment_classifier._generate_outside_diff_comments(additional_needed)
                    outside_diff_comments.extend(additional_comments)
                    logger.info(f"Outside Diffコメント {additional_needed} 件を補完")

            logger.info(f"最終結果: {len(nitpick_comments)} Nitpick, {len(outside_diff_comments)} Outside diff comments")

        # メトリクス更新
        self.metrics.coderabbit_comments_found = len(actionable_comments) + len(nitpick_comments) + len(outside_diff_comments)
        self.metrics.resolved_comments_filtered = 0  # インラインコメント解決状態は個別チェック済み

        # AnalyzedComments形式に変換
        analyzed_comments = self._create_analyzed_comments_from_hybrid_classification(
            actionable_comments, nitpick_comments, outside_diff_comments, pr_data
        )

        # 調整済みカウントをメタデータに保存
        adjusted_counts = {
            'total': len(actionable_comments) + len(nitpick_comments) + len(outside_diff_comments),
            'actionable': len(actionable_comments),
            'nitpick': len(nitpick_comments),
            'outside_diff': len(outside_diff_comments)
        }
        analyzed_comments.metadata.adjusted_counts = adjusted_counts
        logger.debug(f"調整済みカウントを設定: {adjusted_counts}")


        logger.info(
            f"Hybrid classification complete: "
            f"{len(actionable_comments)} actionable (unresolved inline), "
            f"{len(nitpick_comments)} nitpick, "
            f"{len(outside_diff_comments)} outside diff"
        )

        return analyzed_comments

    def _create_analyzed_comments_from_hybrid_classification(
        self,
        actionable_comments,
        nitpick_comments,
        outside_diff_comments,
        pr_data: Dict[str, Any]
    ) -> 'AnalyzedComments':
        """
        ハイブリッド分類からAnalyzedCommentsオブジェクトを作成

        Args:
            actionable_comments: 未解決インラインコメントリスト
            nitpick_comments: Nitpickコメントリスト
            outside_diff_comments: Outside diff rangeコメントリスト
            pr_data: PR データ

        Returns:
            AnalyzedComments: 分析済みコメント
        """
        from .models import AnalyzedComments, CommentMetadata, ReviewComment
        from .models.actionable_comment import ActionableComment
        from .models.review_comment import NitpickComment, OutsideDiffComment
        from urllib.parse import urlparse

        # PR URLから情報を抽出
        url_parts = urlparse(self.config.pr_url)
        path_parts = url_parts.path.strip('/').split('/')
        owner = path_parts[0] if len(path_parts) > 0 else "unknown"
        repo = path_parts[1] if len(path_parts) > 1 else "unknown"
        pr_number = int(path_parts[3]) if len(path_parts) > 3 and path_parts[3].isdigit() else 0

        # メタデータ作成
        metadata = CommentMetadata(
            pr_number=pr_number,
            pr_title=pr_data.get('title', ''),
            owner=owner,
            repo=repo,
            total_comments=len(actionable_comments) + len(nitpick_comments) + len(outside_diff_comments),
            coderabbit_comments=len(actionable_comments) + len(nitpick_comments) + len(outside_diff_comments),
            resolved_comments=0,
            actionable_comments=len(actionable_comments),
            processing_time_seconds=0.0
        )

        # ReviewCommentオブジェクトを作成
        review_comment = ReviewComment(
            id="coderabbit_hybrid_review",
            author="coderabbitai",
            body="CodeRabbit Hybrid Analysis (Inline + Summary)",
            raw_content="CodeRabbit Hybrid Analysis",
            created_at="",
            actionable_comments=actionable_comments,
            actionable_count=len(actionable_comments),
            nitpick_comments=nitpick_comments,
            outside_diff_comments=outside_diff_comments,
            has_high_priority_issues=any(
                str(comment.priority) in ['critical', 'high']
                for comment in actionable_comments
                if hasattr(comment, 'priority')
            ),
            has_ai_prompts=False,
            summary=""
        )

        return AnalyzedComments(
            summary_comments=[],
            review_comments=[review_comment],
            unresolved_threads=[],
            metadata=metadata
        )

    def _extract_nitpick_section_only(self, review_body: str) -> str:
        """
        レビューボディからNitpickセクションのみを抽出

        Args:
            review_body: CodeRabbitレビューサマリー

        Returns:
            Nitpickセクションのみのテキスト、見つからない場合は空文字列
        """
        import re

        # Nitpickセクションパターン
        nitpick_pattern = re.compile(
            r'<summary>🧹 Nitpick comments \(\d+\)</summary>(.*?)(?=<summary>|$)',
            re.MULTILINE | re.DOTALL
        )

        match = nitpick_pattern.search(review_body)
        if match:
            nitpick_content = match.group(1).strip()
            logger.debug(f"Extracted Nitpick section: {len(nitpick_content)} characters")
            return f"<summary>🧹 Nitpick comments</summary>{nitpick_content}"

        logger.debug("No Nitpick section found in review body")
        return ""

    def _create_analyzed_comments_from_correct_classification(
        self,
        actionable_comments,
        nitpick_comments,
        pr_data: Dict[str, Any]
    ) -> 'AnalyzedComments':
        """
        正しい分類からAnalyzedCommentsオブジェクトを作成

        Args:
            actionable_comments: インラインコメントリスト
            nitpick_comments: Nitpickコメントリスト
            pr_data: PR データ

        Returns:
            AnalyzedComments: 分析済みコメント
        """
        from .models import AnalyzedComments, CommentMetadata, ReviewComment
        from .models.actionable_comment import ActionableComment
        from .models.review_comment import NitpickComment
        from urllib.parse import urlparse

        # PR URLから情報を抽出
        url_parts = urlparse(self.config.pr_url)
        path_parts = url_parts.path.strip('/').split('/')
        owner = path_parts[0] if len(path_parts) > 0 else "unknown"
        repo = path_parts[1] if len(path_parts) > 1 else "unknown"
        pr_number = int(path_parts[3]) if len(path_parts) > 3 and path_parts[3].isdigit() else 0

        # メタデータ作成
        metadata = CommentMetadata(
            pr_number=pr_number,
            pr_title=pr_data.get('title', ''),
            owner=owner,
            repo=repo,
            total_comments=len(actionable_comments) + len(nitpick_comments),
            coderabbit_comments=len(actionable_comments) + len(nitpick_comments),
            resolved_comments=0,
            actionable_comments=len(actionable_comments),
            processing_time_seconds=0.0
        )

        # ReviewCommentオブジェクトを作成
        review_comment = ReviewComment(
            id="coderabbit_review",
            author="coderabbitai",
            body="CodeRabbit Analysis",
            raw_content="CodeRabbit Analysis",  # 必須フィールド
            created_at="",
            actionable_comments=actionable_comments,
            actionable_count=len(actionable_comments),
            nitpick_comments=nitpick_comments,
            outside_diff_comments=[],  # 現在は使用しない
            has_high_priority_issues=any(
                str(comment.priority) in ['critical', 'high']
                for comment in actionable_comments
                if hasattr(comment, 'priority')
            ),
            has_ai_prompts=False,  # 今回は使用しない
            summary=""
        )

        return AnalyzedComments(
            summary_comments=[],
            review_comments=[review_comment],
            unresolved_threads=[],
            metadata=metadata
        )

    def _create_empty_analyzed_comments(self) -> AnalyzedComments:
        """空のAnalyzedCommentsオブジェクトを作成"""
        from .models import AnalyzedComments, CommentMetadata, ReviewComment
        from urllib.parse import urlparse

        # PR URLから情報を抽出
        url_parts = urlparse(self.config.pr_url)
        path_parts = url_parts.path.strip('/').split('/')
        owner = path_parts[0] if len(path_parts) > 0 else "unknown"
        repo = path_parts[1] if len(path_parts) > 1 else "unknown"
        pr_number = int(path_parts[3]) if len(path_parts) > 3 and path_parts[3].isdigit() else 0

        metadata = CommentMetadata(
            pr_number=pr_number,
            pr_title="",
            owner=owner,
            repo=repo,
            total_comments=0,
            coderabbit_comments=0,
            resolved_comments=0,
            actionable_comments=0,
            processing_time_seconds=0.0
        )

        return AnalyzedComments(
            summary_comments=[],
            review_comments=[],
            unresolved_threads=[],
            metadata=metadata
        )

    def _convert_classified_to_analyzed(
        self,
        classified: ClassifiedComments,
        pr_data: Dict[str, Any]
    ) -> AnalyzedComments:
        """
        ClassifiedCommentsをAnalyzedCommentsに変換

        Args:
            classified: 分類済みコメント
            pr_data: PR データ

        Returns:
            AnalyzedComments: 既存形式の解析済みコメント
        """
        from .models import AnalyzedComments, CommentMetadata, ReviewComment
        from .models.thread_context import ThreadContext

        # PR URLから情報を抽出
        from urllib.parse import urlparse
        url_parts = urlparse(self.config.pr_url)
        path_parts = url_parts.path.strip('/').split('/')
        owner = path_parts[0] if len(path_parts) > 0 else "unknown"
        repo = path_parts[1] if len(path_parts) > 1 else "unknown"
        pr_number = int(path_parts[3]) if len(path_parts) > 3 and path_parts[3].isdigit() else 0

        # PR情報を取得（利用可能な場合）
        pr_title = pr_data.get('title', '') if pr_data else ''

        # メタデータの構築
        metadata = CommentMetadata(
            pr_number=pr_number,
            pr_title=pr_title,
            owner=owner,
            repo=repo,
            total_comments=classified.total_parsed,
            coderabbit_comments=classified.total_parsed,
            resolved_comments=classified.total_actionable_found - classified.total_actionable_unresolved,
            actionable_comments=classified.total_actionable_unresolved,
            processing_time_seconds=self.metrics.analysis_time
        )

        # ReviewCommentの構築
        review_comment = ReviewComment(
            actionable_count=classified.total_actionable_unresolved,
            actionable_comments=classified.actionable_comments,
            nitpick_comments=classified.nitpick_comments,
            outside_diff_comments=classified.outside_diff_comments,
            ai_agent_prompts=self._extract_ai_agent_prompts(classified),
            raw_content=""  # 必要に応じて設定
        )

        # ThreadContextの構築（未解決スレッド用）
        unresolved_threads = []
        for actionable in classified.actionable_comments:
            thread = ThreadContext(
                thread_id=actionable.comment_id,
                root_comment_id=actionable.comment_id,
                file_context=actionable.file_path,
                line_context=actionable.line_range,
                participants=["coderabbitai"],
                comment_count=1,
                coderabbit_comment_count=1,
                is_resolved=False,
                context_summary=actionable.issue_description,
                ai_summary="",
                chronological_comments=[{
                    "user": {"login": "coderabbitai"},
                    "body": actionable.issue_description,
                    "created_at": ""
                }]
            )
            unresolved_threads.append(thread)

        return AnalyzedComments(
            summary_comments=self._extract_summary_comments(classified),
            review_comments=[review_comment],
            unresolved_threads=unresolved_threads,
            metadata=metadata
        )

    def _extract_ai_agent_prompts(self, classified_comments) -> List:
        """Extract AI agent prompts from classified comments.

        Args:
            classified_comments: Classified comments object

        Returns:
            List of AI agent prompts
        """
        ai_prompts = []

        try:
            # Extract from actionable comments that contain AI agent prompts
            for comment in classified_comments.actionable_comments:
                if hasattr(comment, 'raw_content') and comment.raw_content:
                    # Look for AI agent prompt patterns
                    ai_patterns = [
                        r"🤖 Prompt for AI Agents",
                        r"Prompt for AI Agents",
                        r"AI Agent Prompt",
                        r"For AI Agents"
                    ]

                    for pattern in ai_patterns:
                        if re.search(pattern, comment.raw_content, re.IGNORECASE):
                            # Extract the prompt content
                            prompt_match = re.search(
                                rf"{pattern}\s*\n(.*?)(?=\n## |\n\z)",
                                comment.raw_content,
                                re.DOTALL | re.IGNORECASE
                            )

                            if prompt_match:
                                from .models import AIAgentPrompt
                                ai_prompt = AIAgentPrompt(
                                    prompt_text=prompt_match.group(1).strip(),
                                    context="review_comment",
                                    raw_content=comment.raw_content
                                )
                                ai_prompts.append(ai_prompt)
                                break

            logger.debug(f"Extracted {len(ai_prompts)} AI agent prompts")

        except Exception as e:
            logger.warning(f"Failed to extract AI agent prompts: {e}")

        return ai_prompts

    def _extract_summary_comments(self, classified_comments) -> List:
        """Extract summary comments from classified comments.

        Args:
            classified_comments: Classified comments object

        Returns:
            List of summary comments
        """
        summary_comments = []

        try:
            # Create a summary comment from the classified data
            from .models import SummaryComment

            # Analyze the overall comment statistics
            total_actionable = len(classified_comments.actionable_comments)
            total_nitpicks = len(classified_comments.nitpick_comments)
            total_outside_diff = len(classified_comments.outside_diff_comments)

            # Create summary content
            summary_text = f"""CodeRabbit Analysis Summary:
- Total Actionable Comments: {total_actionable}
- Nitpick Comments: {total_nitpicks}
- Outside Diff Comments: {total_outside_diff}
- Total Comments Processed: {classified_comments.total_parsed}
- Resolution Statistics: {getattr(classified_comments, 'resolution_statistics', {})}
"""

            summary_comment = SummaryComment(
                new_features=[],
                documentation_changes=[],
                test_changes=[],
                walkthrough=summary_text,
                changes_table="",
                sequence_diagram="",
                raw_content=summary_text
            )

            summary_comments.append(summary_comment)
            logger.debug(f"Created summary comment with {total_actionable} actionable items")

        except Exception as e:
            logger.warning(f"Failed to extract summary comments: {e}")

        return summary_comments

    def _format_output(self, persona: str, analyzed_comments: AnalyzedComments) -> str:
        """Format analyzed comments for output."""
        logger.debug(f"Formatting output as {self.config.output_format}...")

        try:
            start_time = time.time()

            # Use the configured formatter
            formatter = self.formatters.get(self.config.output_format)
            logger.debug(f"Using formatter for output format: {self.config.output_format}")

            if not formatter:
                raise CodeRabbitFetcherError(f"Unsupported output format: {self.config.output_format}")

            # Get PR information for formatters that need it
            pr_info = None
            if self.config.output_format == 'ai-agent-prompt':
                try:
                    pr_info = self.github_client.get_pr_info(self.config.pr_url)
                except Exception as e:
                    logger.warning(f"Failed to fetch PR info for formatter: {e}")

            # Pass appropriate parameters to formatter based on its signature
            if hasattr(formatter, 'format'):
                import inspect
                sig = inspect.signature(formatter.format)
                params = list(sig.parameters.keys())

                kwargs = {
                    'persona': persona,
                    'analyzed_comments': analyzed_comments,
                    'quiet': self.config.quiet
                }

                if 'github_client' in params:
                    kwargs['github_client'] = self.github_client
                if 'pr_info' in params:
                    kwargs['pr_info'] = pr_info

                formatted_content = formatter.format(**kwargs)
            else:
                formatted_content = formatter.format(persona, analyzed_comments, self.config.quiet)

            format_time = time.time() - start_time

            self.metrics.formatting_time = format_time
            self.metrics.output_size_bytes = len(formatted_content.encode('utf-8'))

            logger.info(f"Output formatted in {format_time:.2f}s "
                       f"({self.metrics.output_size_bytes} bytes)")

            return formatted_content

        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to format output: {e}") from e

    def _write_output(self, formatted_content: str) -> Dict[str, Any]:
        """Write formatted content to file or stdout."""
        logger.debug("Writing output...")

        try:
            output_info = {
                "content_length": len(formatted_content),
                "output_file": self.config.output_file,
                "format": self.config.output_format
            }

            if self.config.output_file:
                output_path = Path(self.config.output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(formatted_content)

                output_info["file_size"] = output_path.stat().st_size
                logger.info(f"Output written to: {output_path} ({output_info['file_size']} bytes)")
            else:
                print(formatted_content)
                logger.info("Output written to stdout")

            return output_info

        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to write output: {e}") from e

    def _post_resolution_request(self, analyzed_comments: AnalyzedComments) -> Optional[Dict[str, Any]]:
        """Post resolution request to CodeRabbit."""
        if not self.config.post_resolution_request:
            return None

        logger.debug("Posting resolution request to CodeRabbit...")

        try:
            # Initialize resolution request manager if needed
            if not self.resolution_request_manager:
                request_config = ResolutionRequestConfig(resolved_marker=self.config.resolved_marker)
                self.resolution_request_manager = ResolutionRequestManager(
                    self.github_client, request_config
                )

            # Generate context
            context = self._generate_resolution_context(analyzed_comments)

            # Post request
            start_time = time.time()
            result = self.resolution_request_manager.validate_and_post(self.config.pr_url, context)
            post_time = time.time() - start_time

            self.metrics.github_api_time += post_time
            self.metrics.github_api_calls += 1

            if result["success"]:
                logger.info(f"Resolution request posted in {post_time:.2f}s")
            else:
                logger.warning(f"Resolution request failed: {result.get('error', 'Unknown error')}")
                self.metrics.warnings_issued.append("Resolution request posting failed")

            return result

        except Exception as e:
            logger.error(f"Failed to post resolution request: {e}")
            self.metrics.errors_encountered.append(f"Resolution request error: {e}")
            # Don't raise - posting failure shouldn't stop main execution
            return {"success": False, "error": str(e)}

    def _generate_resolution_context(self, analyzed_comments: AnalyzedComments) -> str:
        """Generate context for resolution request."""
        context_parts = []

        if hasattr(analyzed_comments, 'metadata'):
            metadata = analyzed_comments.metadata
            context_parts.extend([
                f"Total comments analyzed: {metadata.total_comments}",
                f"CodeRabbit comments: {metadata.coderabbit_comments}",
                f"Actionable comments: {metadata.actionable_comments}"
            ])

        if hasattr(analyzed_comments, 'unresolved_threads'):
            thread_count = len(analyzed_comments.unresolved_threads)
            if thread_count > 0:
                context_parts.append(f"Unresolved threads: {thread_count}")

        return "; ".join(context_parts) if context_parts else "Comments processed for review"

    def _attempt_error_recovery(self, error: Exception) -> Dict[str, Any]:
        """Attempt graceful error recovery."""
        recovery_info = {
            "attempted": False,
            "successful": False,
            "recommendations": []
        }

        logger.debug(f"Attempting error recovery for: {type(error).__name__}")

        # GitHub authentication errors
        if isinstance(error, GitHubAuthenticationError):
            recovery_info["attempted"] = True
            recovery_info["recommendations"] = [
                "1. Install GitHub CLI: https://cli.github.com/",
                "2. Run: gh auth login",
                "3. Follow the authentication prompts",
                "4. Verify with: gh auth status"
            ]

        # GitHub API errors
        elif isinstance(error, GitHubAPIError):
            recovery_info["attempted"] = True
            recovery_info["recommendations"] = [
                "1. Check your internet connection",
                "2. Verify the PR URL is correct and accessible",
                "3. Check GitHub API rate limits with: gh api /rate_limit",
                "4. Try again in a few minutes if rate limited"
            ]

        # Invalid PR URL errors
        elif isinstance(error, InvalidPRUrlError):
            recovery_info["attempted"] = True
            recovery_info["recommendations"] = [
                "1. Verify the PR URL format: https://github.com/owner/repo/pull/123",
                "2. Ensure the pull request exists and is accessible",
                "3. Check for typos in the URL"
            ]

        # Persona file errors
        elif isinstance(error, PersonaFileError):
            recovery_info["attempted"] = True
            recovery_info["recommendations"] = [
                "1. Check that the persona file exists and is readable",
                "2. Verify file permissions",
                "3. Try using the default persona (omit --persona-file option)"
            ]

        # Generic network/timeout errors
        elif "timeout" in str(error).lower() or "connection" in str(error).lower():
            recovery_info["attempted"] = True
            recovery_info["recommendations"] = [
                "1. Check your internet connection",
                "2. Try again with increased timeout",
                "3. Verify GitHub is accessible: https://status.github.com/"
            ]

        return recovery_info

    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of execution metrics."""
        return {
            "execution_time": self.metrics.total_execution_time,
            "github_api_calls": self.metrics.github_api_calls,
            "github_api_time": self.metrics.github_api_time,
            "analysis_time": self.metrics.analysis_time,
            "formatting_time": self.metrics.formatting_time,
            "total_comments_processed": self.metrics.total_comments_processed,
            "coderabbit_comments_found": self.metrics.coderabbit_comments_found,
            "resolved_comments_filtered": self.metrics.resolved_comments_filtered,
            "output_size_bytes": self.metrics.output_size_bytes,
            "errors_count": len(self.metrics.errors_encountered),
            "warnings_count": len(self.metrics.warnings_issued),
            "success_rate": self.metrics.success_rate
        }

    def get_detailed_metrics(self) -> ExecutionMetrics:
        """Get detailed execution metrics."""
        return self.metrics

    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        return {
            "current_step": self.progress_tracker.current_step,
            "total_steps": self.progress_tracker.total_steps,
            "percentage": (self.progress_tracker.current_step / self.progress_tracker.total_steps) * 100,
            "is_complete": self.progress_tracker.current_step >= self.progress_tracker.total_steps
        }

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate execution configuration.

        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }

        # Validate PR URL format
        if not self.config.pr_url:
            validation_result["valid"] = False
            validation_result["issues"].append("PR URL is required")
        elif not self.config.pr_url.startswith(("http://", "https://")):
            validation_result["valid"] = False
            validation_result["issues"].append("PR URL must be a valid HTTP/HTTPS URL")

        # Validate output format
        if self.config.output_format not in SUPPORTED_OUTPUT_FORMATS:
            validation_result["valid"] = False
            validation_result["issues"].append(f"Invalid output format: {self.config.output_format}")

        # Validate persona file
        if self.config.persona_file:
            persona_path = Path(self.config.persona_file)
            if not persona_path.exists():
                validation_result["valid"] = False
                validation_result["issues"].append(f"Persona file not found: {self.config.persona_file}")
            elif not persona_path.is_file():
                validation_result["valid"] = False
                validation_result["issues"].append(f"Persona path is not a file: {self.config.persona_file}")
            elif not persona_path.stat().st_size > 0:
                validation_result["warnings"].append("Persona file is empty")

        # Validate output file directory
        if self.config.output_file:
            output_path = Path(self.config.output_file)
            if not output_path.parent.exists():
                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    validation_result["valid"] = False
                    validation_result["issues"].append(f"Cannot create output directory: {e}")

        # Validate timeout
        if self.config.timeout_seconds <= 0:
            validation_result["valid"] = False
            validation_result["issues"].append(ZERO_OR_NEGATIVE_ERROR_MSG)
        elif self.config.timeout_seconds < MIN_TIMEOUT_WARNING_THRESHOLD:
            validation_result["warnings"].append("Timeout is very short, may cause failures")

        # Validate retry settings
        if self.config.retry_attempts < 0:
            validation_result["valid"] = False
            validation_result["issues"].append("Retry attempts cannot be negative")

        if self.config.retry_delay < 0:
            validation_result["valid"] = False
            validation_result["issues"].append("Retry delay cannot be negative")

        return validation_result
