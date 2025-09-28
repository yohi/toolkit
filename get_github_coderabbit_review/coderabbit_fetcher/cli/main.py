"""Main CLI interface for CodeRabbit Comment Fetcher."""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, TextIO
import json

from ..exceptions import CodeRabbitFetcherError, GitHubAuthenticationError, InvalidPRUrlError
from ..github_client import GitHubClient, GitHubAPIError
from ..comment_analyzer import CommentAnalyzer, CommentAnalysisError
from ..persona_manager import PersonaManager
from ..formatters import MarkdownFormatter, JSONFormatter, PlainTextFormatter
from ..resolved_marker import ResolvedMarkerManager, ResolvedMarkerConfig
from ..comment_poster import ResolutionRequestManager, ResolutionRequestConfig
from ..models import CommentMetadata


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLIError(CodeRabbitFetcherError):
    """CLI-specific errors."""
    pass


class CodeRabbitFetcherCLI:
    """Main CLI application class."""

    def __init__(self):
        """Initialize CLI application."""
        self.github_client = None
        self.persona_manager = None
        self.resolved_marker_manager = None
        self.resolution_request_manager = None
        self.comment_analyzer = None

    def setup_github_client(self) -> None:
        """Initialize and validate GitHub client."""
        try:
            self.github_client = GitHubClient()
            logger.info("GitHub CLI authentication verified")
        except GitHubAuthenticationError as e:
            print(f"❌ GitHub Authentication Error: {e}", file=sys.stderr)
            print("\n💡 To fix this issue:", file=sys.stderr)
            print("   1. Install GitHub CLI: https://cli.github.com/", file=sys.stderr)
            print("   2. Run: gh auth login", file=sys.stderr)
            print("   3. Follow the authentication prompts", file=sys.stderr)
            raise CLIError("GitHub CLI authentication required") from e

    def setup_managers(self, resolved_marker: str, post_resolution_request: bool) -> None:
        """Initialize manager components."""
        # Setup resolved marker manager
        marker_config = ResolvedMarkerConfig(default_marker=resolved_marker)
        self.resolved_marker_manager = ResolvedMarkerManager(marker_config)

        # Setup comment analyzer
        self.comment_analyzer = CommentAnalyzer(marker_config)

        # Setup persona manager
        self.persona_manager = PersonaManager()

        # Setup resolution request manager if needed
        if post_resolution_request:
            request_config = ResolutionRequestConfig(resolved_marker=resolved_marker)
            self.resolution_request_manager = ResolutionRequestManager(
                self.github_client, request_config
            )

    def validate_pr_url(self, pr_url: str) -> None:
        """Validate PR URL format."""
        try:
            self.github_client.parse_pr_url(pr_url)
        except InvalidPRUrlError as e:
            print(f"❌ Invalid PR URL: {e}", file=sys.stderr)
            print("\n💡 Expected format: https://github.com/owner/repo/pull/123", file=sys.stderr)
            raise CLIError("Invalid pull request URL") from e

    def load_persona(self, persona_file: Optional[str]) -> str:
        """Load persona content."""
        try:
            if persona_file:
                return self.persona_manager.load_persona_file(persona_file)
            else:
                return self.persona_manager.get_default_persona()
        except (FileNotFoundError, PermissionError, ValueError) as e:
            print(f"❌ Persona Error: {e}", file=sys.stderr)
            raise CLIError("Failed to load persona") from e

    def fetch_and_analyze_comments(self, pr_url: str) -> Any:  # Returns AnalyzedComments
        """Fetch and analyze PR comments."""
        try:
            # Show progress
            print("🔍 Fetching pull request data...")
            pr_data = self.github_client.fetch_pr_comments(pr_url)

            print("📊 Analyzing CodeRabbit comments...")
            analyzed_comments = self.comment_analyzer.analyze_comments(pr_data)

            # Apply resolved marker filtering
            if self.resolved_marker_manager:
                print("🔒 Filtering resolved comments...")
                result = self.resolved_marker_manager.process_threads_with_resolution(
                    analyzed_comments.unresolved_threads
                )
                analyzed_comments.unresolved_threads = result["unresolved_threads"]

                # Update metadata with resolution statistics
                if hasattr(analyzed_comments, 'metadata'):
                    analyzed_comments.metadata.resolved_comments = result["statistics"]["resolved_threads"]

            return analyzed_comments

        except GitHubAPIError as e:
            print(f"❌ GitHub API Error: {e}", file=sys.stderr)
            raise CLIError("Failed to fetch PR data") from e
        except CommentAnalysisError as e:
            print(f"❌ Comment Analysis Error: {e}", file=sys.stderr)
            raise CLIError("Failed to analyze comments") from e
        except (ValueError, KeyError, TypeError) as e:
            print(f"❌ Data Processing Error: {e}", file=sys.stderr)
            raise CLIError("Failed to process data") from e

    def format_output(self, persona: str, analyzed_comments: Any, output_format: str) -> str:
        """Format analyzed comments for output."""
        try:
            formatters = {
                'markdown': MarkdownFormatter(),
                'json': JSONFormatter(),
                'plain': PlainTextFormatter()
            }

            formatter = formatters.get(output_format)
            if not formatter:
                raise ValueError(f"Unsupported output format: {output_format}")

            return formatter.format(persona, analyzed_comments)

        except (ValueError, TypeError, AttributeError) as e:
            print(f"❌ Formatting Error: {e}", file=sys.stderr)
            raise CLIError("Failed to format output") from e

    def post_resolution_request(self, pr_url: str, analyzed_comments: Any) -> None:
        """Post resolution request if enabled."""
        if not self.resolution_request_manager:
            return

        try:
            print("📝 Posting resolution request to CodeRabbit...")

            # Generate context from analyzed comments
            context = self._generate_resolution_context(analyzed_comments)

            result = self.resolution_request_manager.validate_and_post(pr_url, context)

            if result["success"]:
                comment_url = result["posting"]["comment_url"]
                print(f"✅ Resolution request posted: {comment_url}")
            else:
                print(f"❌ Failed to post resolution request: {result['error']}", file=sys.stderr)

        except (ValueError, TypeError, AttributeError, GitHubAPIError) as e:
            print(f"❌ Resolution Request Error: {e}", file=sys.stderr)
            # Don't raise CLIError here - posting failure shouldn't stop the main output

    def _generate_resolution_context(self, analyzed_comments: Any) -> str:
        """Generate context for resolution request."""
        context_parts = []

        # Add summary of comments
        if hasattr(analyzed_comments, 'metadata'):
            metadata = analyzed_comments.metadata
            context_parts.append(f"Total comments analyzed: {metadata.total_comments}")
            context_parts.append(f"CodeRabbit comments: {metadata.coderabbit_comments}")
            context_parts.append(f"Actionable comments: {metadata.actionable_comments}")

        # Add thread information
        if hasattr(analyzed_comments, 'unresolved_threads'):
            thread_count = len(analyzed_comments.unresolved_threads)
            if thread_count > 0:
                context_parts.append(f"Unresolved threads: {thread_count}")

        return "; ".join(context_parts) if context_parts else "Comments processed for review"

    def write_output(self, content: str, output_file: Optional[str]) -> None:
        """Write formatted content to file or stdout."""
        try:
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"✅ Output written to: {output_path}")
            else:
                print(content)

        except (OSError, IOError, PermissionError) as e:
            print(f"❌ Output Error: {e}", file=sys.stderr)
            raise CLIError("Failed to write output") from e

    def display_statistics(self, analyzed_comments: Any) -> None:
        """Display processing statistics."""
        if not hasattr(analyzed_comments, 'metadata'):
            return

        metadata = analyzed_comments.metadata

        print("\n📊 Processing Statistics:")
        print(f"   Total comments: {metadata.total_comments}")
        print(f"   CodeRabbit comments: {metadata.coderabbit_comments}")
        print(f"   Actionable comments: {metadata.actionable_comments}")

        if hasattr(metadata, 'resolved_comments'):
            print(f"   Resolved comments: {metadata.resolved_comments}")

        if hasattr(analyzed_comments, 'unresolved_threads'):
            thread_count = len(analyzed_comments.unresolved_threads)
            print(f"   Unresolved threads: {thread_count}")

        if hasattr(metadata, 'processing_time_seconds'):
            print(f"   Processing time: {metadata.processing_time_seconds:.2f}s")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="CodeRabbit Comment Fetcher - Extract and format CodeRabbit comments from GitHub PRs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python -m coderabbit_fetcher https://github.com/owner/repo/pull/123

  # With custom persona and JSON output
  python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
      --persona-file my_persona.txt --output-format json

  # With resolution request posting
  python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
      --post-resolution-request --output-file results.md

  # Full featured command
  python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
      --persona-file ./personas/reviewer.txt \\
      --output-format markdown \\
      --output-file ./output/pr_123_analysis.md \\
      --resolved-marker "🔒 CUSTOM_RESOLVED 🔒" \\
      --post-resolution-request \\
      --show-stats \\
      --debug
        """
    )

    # Optional positional argument (required only for fetch command)
    parser.add_argument(
        'pr_url',
        nargs='?',
        default=None,
        help='GitHub pull request URL (omit for --validate/--version/--examples/--validate-marker)'
    )

    # Optional arguments
    parser.add_argument(
        '--persona-file', '-p',
        type=str,
        help='Path to persona file for AI context'
    )

    parser.add_argument(
        '--output-format', '-f',
        choices=['markdown', 'json', 'plain'],
        default='markdown',
        help='Output format (default: markdown)'
    )

    parser.add_argument(
        '--output-file', '-o',
        type=str,
        help='Output file path (default: stdout)'
    )

    parser.add_argument(
        '--resolved-marker', '-m',
        type=str,
        default='🔒 CODERABBIT_RESOLVED 🔒',
        help='Resolved marker string (default: 🔒 CODERABBIT_RESOLVED 🔒)'
    )

    parser.add_argument(
        '--post-resolution-request', '-r',
        action='store_true',
        help='Post resolution request comment to CodeRabbit'
    )

    parser.add_argument(
        '--show-stats', '-s',
        action='store_true',
        help='Show processing statistics'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate GitHub CLI setup only'
    )

    parser.add_argument(
        '--validate-marker',
        type=str,
        help='Validate a resolved marker string'
    )

    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information'
    )

    parser.add_argument(
        '--examples',
        action='store_true',
        help='Show usage examples'
    )

    return parser


def run_fetch_command(args) -> int:
    """Run the main fetch command."""
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    app = CodeRabbitFetcherCLI()

    try:
        # Setup components
        print("🔧 Setting up GitHub CLI...")
        app.setup_github_client()

        print("⚙️  Initializing components...")
        app.setup_managers(args.resolved_marker, args.post_resolution_request)

        # Validate inputs
        print("✅ Validating PR URL...")
        app.validate_pr_url(args.pr_url)

        # Load persona
        print("📝 Loading persona...")
        persona = app.load_persona(args.persona_file)

        # Fetch and analyze
        analyzed_comments = app.fetch_and_analyze_comments(args.pr_url)

        # Format output
        print(f"📋 Formatting output as {args.output_format}...")
        formatted_content = app.format_output(persona, analyzed_comments, args.output_format)

        # Write output
        app.write_output(formatted_content, args.output_file)

        # Show statistics
        if args.show_stats:
            app.display_statistics(analyzed_comments)

        # Post resolution request
        if args.post_resolution_request:
            app.post_resolution_request(args.pr_url, analyzed_comments)

        print("\n✅ Processing completed successfully!")
        return 0

    except CLIError:
        return 1
    except CommentAnalysisError as e:
        print(f"❌ Comment Analysis Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def run_validate_command() -> int:
    """Run the validate command."""
    print("🔍 Validating GitHub CLI setup...")

    try:
        client = GitHubClient()
        validation_result = client.validate_github_cli()

        # Display results
        if validation_result["gh_installed"]:
            print(f"✅ GitHub CLI installed: {validation_result['gh_version']}")
        else:
            print("❌ GitHub CLI not installed", file=sys.stderr)

        if validation_result["authenticated"]:
            user = validation_result.get("auth_user", "unknown")
            print(f"✅ Authenticated as: {user}")
        else:
            print("❌ Not authenticated", file=sys.stderr)

        # Show issues and recommendations
        if validation_result["issues"]:
            print("\n⚠️  Issues found:")
            for issue in validation_result["issues"]:
                print(f"   • {issue}")

        if validation_result["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in validation_result["recommendations"]:
                print(f"   • {rec}")

        # Check rate limit
        if validation_result["authenticated"]:
            try:
                rate_limit = client.check_rate_limit()
                core_limit = rate_limit.get("rate", {})
                remaining = core_limit.get("remaining", "unknown")
                limit = core_limit.get("limit", "unknown")
                print(f"\n📊 API Rate Limit: {remaining}/{limit} remaining")
            except (GitHubAPIError, ValueError, KeyError) as e:
                print(f"\n⚠️  Could not check rate limit: {e}")

        if validation_result["issues"]:
            return 1
        else:
            print("\n✅ GitHub CLI setup is valid!")
            return 0

    except Exception as e:
        print(f"❌ Validation failed: {e}", file=sys.stderr)
        return 1


def run_validate_marker_command(marker: str) -> int:
    """Run the validate marker command."""
    print(f"🔍 Validating marker: '{marker}'")

    try:
        from ..resolved_marker import ResolvedMarkerConfig, ResolvedMarkerManager

        # Use ResolvedMarkerManager's validate_marker method instead of config
        manager = ResolvedMarkerManager()
        validation = manager.validate_marker(marker)

        if validation["valid"]:
            print("✅ Marker is valid")
        else:
            print("❌ Marker validation failed:", file=sys.stderr)
            for issue in validation["issues"]:
                print(f"   • {issue}", file=sys.stderr)

        # Use public API to calculate uniqueness score
        score = manager.calculate_uniqueness_score(marker)

        print(f"\n📊 Uniqueness Score: {score:.2f}/1.0")
        if score < 0.3:
            print("   ⚠️  Low uniqueness - consider adding special characters")
        elif score < 0.7:
            print("   👍 Good uniqueness")
        else:
            print("   🎯 Excellent uniqueness")

        return 0 if validation["valid"] else 1

    except Exception as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        return 1


def run_version_command() -> int:
    """Run the version command."""
    version = "development"

    try:
        # First, try to import the required modules
        from importlib.metadata import version as get_version, PackageNotFoundError
    except ImportError:
        # If import fails, use development version
        version = "development"
    else:
        # If import succeeds, try to get the actual version
        try:
            version = get_version('coderabbit-comment-fetcher')
        except PackageNotFoundError:
            # If package is not found, use development version
            version = "development"

    print(f"CodeRabbit Comment Fetcher v{version}")
    print("Python script for extracting and formatting CodeRabbit comments")
    return 0


def run_examples_command() -> int:
    """Run the examples command."""
    examples_text = """
🚀 CodeRabbit Comment Fetcher - Usage Examples

1. Basic usage:
   python -m coderabbit_fetcher https://github.com/owner/repo/pull/123

2. Custom persona file:
   python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
       --persona-file ./my_persona.txt

3. JSON output to file:
   python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
       --output-format json --output-file results.json

4. With resolution request posting:
   python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
       --post-resolution-request

5. Custom resolved marker:
   python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
       --resolved-marker "✅ VERIFIED ✅"

6. Full featured command:
   python -m coderabbit_fetcher https://github.com/owner/repo/pull/123 \\
       --persona-file ./personas/reviewer.txt \\
       --output-format markdown \\
       --output-file ./output/pr_123_analysis.md \\
       --resolved-marker "🔒 CUSTOM_RESOLVED 🔒" \\
       --post-resolution-request \\
       --show-stats \\
       --debug

🔧 Setup Commands:

1. Validate GitHub CLI setup:
   python -m coderabbit_fetcher --validate

2. Validate a custom marker:
   python -m coderabbit_fetcher --validate-marker "🔒 MY_MARKER 🔒"

3. Show version:
   python -m coderabbit_fetcher --version

💡 Tips:

• Use --show-stats to see processing statistics
• Use --debug to enable detailed logging
• Use --help for more information
• Persona files should contain plain text for AI context
• Resolution requests are posted as comments to CodeRabbit
• Custom markers help avoid conflicts with existing resolved comments
    """
    print(examples_text)
    return 0


def main():
    """Main entry point for the CLI."""
    try:
        parser = create_argument_parser()

        # Handle special case when no arguments provided
        if len(sys.argv) == 1:
            parser.print_help()
            return 0

        args = parser.parse_args()

        # Handle utility commands first
        if args.version:
            return run_version_command()

        if args.examples:
            return run_examples_command()

        if args.validate:
            return run_validate_command()

        if args.validate_marker:
            return run_validate_marker_command(args.validate_marker)

        # Main fetch command (requires pr_url)
        if not args.pr_url:
            print("❌ PR URL is required for fetch command", file=sys.stderr)
            parser.print_help()
            return 1

        return run_fetch_command(args)

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        logger.exception("CLI startup error")
        print(f"❌ Failed to start CLI: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()
