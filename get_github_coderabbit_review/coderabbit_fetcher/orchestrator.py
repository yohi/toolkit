"""Main orchestration logic for CodeRabbit Comment Fetcher."""

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
from .persona_manager import PersonaManager
from .formatters import MarkdownFormatter, JSONFormatter, PlainTextFormatter, LLMInstructionFormatter
from .resolved_marker import ResolvedMarkerManager, ResolvedMarkerConfig
from .comment_poster import ResolutionRequestManager, ResolutionRequestConfig
from .models import AnalyzedComments, CommentMetadata


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Configuration for main execution flow."""
    pr_url: str
    persona_file: Optional[str] = None
    output_format: str = 'llm-instruction'
    output_file: Optional[str] = None
    resolved_marker: str = '🔒 CODERABBIT_RESOLVED 🔒'
    post_resolution_request: bool = False
    show_stats: bool = False
    debug: bool = False
    quiet: bool = False
    timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay: float = 1.0


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
        total_operations = 5  # Setup, fetch, analyze, format, output
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
        self.step_descriptions = [
            "Initializing components",
            "Validating GitHub CLI authentication",
            "Parsing and validating PR URL",
            "Loading persona configuration",
            "Fetching PR data from GitHub",
            "Analyzing CodeRabbit comments",
            "Formatting output",
            "Writing results"
        ]

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
                'llm-instruction': LLMInstructionFormatter()
            }

            # Initialize persona manager
            self.persona_manager = PersonaManager()

            # Initialize resolved marker manager
            marker_config = ResolvedMarkerConfig(default_marker=self.config.resolved_marker)
            self.resolved_marker_manager = ResolvedMarkerManager(marker_config)

            # Initialize comment analyzer
            self.comment_analyzer = CommentAnalyzer(marker_config)

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
            analyzed_comments = self.comment_analyzer.analyze_comments(pr_data)
            analysis_time = time.time() - start_time

            self.metrics.analysis_time = analysis_time
            self.metrics.coderabbit_comments_found = analyzed_comments.metadata.coderabbit_comments

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

            logger.info(f"Analysis completed in {analysis_time:.2f}s "
                       f"({self.metrics.coderabbit_comments_found} CodeRabbit comments, "
                       f"{self.metrics.resolved_comments_filtered} resolved)")

            return analyzed_comments

        except CommentAnalysisError as e:
            logger.error(f"Comment analysis failed: {e}")
            raise
        except Exception as e:
            raise CodeRabbitFetcherError(f"Failed to analyze comments: {e}") from e

    def _format_output(self, persona: str, analyzed_comments: AnalyzedComments) -> str:
        """Format analyzed comments for output."""
        logger.debug(f"Formatting output as {self.config.output_format}...")

        try:
            start_time = time.time()

            # In quiet mode, force use of MarkdownFormatter for simplified XML output
            if self.config.quiet:
                formatter = self.formatters.get('markdown')
                logger.debug("Using MarkdownFormatter for quiet mode")
            else:
                formatter = self.formatters.get(self.config.output_format)
            
            if not formatter:
                raise CodeRabbitFetcherError(f"Unsupported output format: {self.config.output_format}")

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
        if self.config.output_format not in ['markdown', 'json', 'plain', 'llm-instruction']:
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
            validation_result["issues"].append("Timeout must be positive")
        elif self.config.timeout_seconds < 30:
            validation_result["warnings"].append("Timeout is very short, may cause failures")

        # Validate retry settings
        if self.config.retry_attempts < 0:
            validation_result["valid"] = False
            validation_result["issues"].append("Retry attempts cannot be negative")

        if self.config.retry_delay < 0:
            validation_result["valid"] = False
            validation_result["issues"].append("Retry delay cannot be negative")

        return validation_result
