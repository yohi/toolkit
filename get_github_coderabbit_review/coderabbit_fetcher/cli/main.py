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
from ..orchestrator import CodeRabbitOrchestrator, ExecutionConfig


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CLIError(CodeRabbitFetcherError):
    """CLI-specific errors."""

    pass


# Use orchestrator pattern - old CLI class removed and replaced with new architecture


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
        """,
    )

    # Optional positional argument (required only for fetch command)
    parser.add_argument(
        "pr_url",
        nargs="?",
        default=None,
        help="GitHub pull request URL (omit for --validate/--version/--examples/--validate-marker)",
    )

    # Optional arguments
    parser.add_argument(
        "--persona-file", "-p", type=str, help="Path to persona file for AI context"
    )

    parser.add_argument(
        "--output-format",
        "-f",
        choices=["markdown", "json", "plain"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    parser.add_argument("--output-file", "-o", type=str, help="Output file path (default: stdout)")

    parser.add_argument(
        "--resolved-marker",
        "-m",
        type=str,
        default="🔒 CODERABBIT_RESOLVED 🔒",
        help="Resolved marker string (default: 🔒 CODERABBIT_RESOLVED 🔒)",
    )

    parser.add_argument(
        "--post-resolution-request",
        "-r",
        action="store_true",
        help="Post resolution request comment to CodeRabbit",
    )

    parser.add_argument(
        "--show-stats", "-s", action="store_true", help="Show processing statistics"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    parser.add_argument("--validate", action="store_true", help="Validate GitHub CLI setup only")

    parser.add_argument("--validate-marker", type=str, help="Validate a resolved marker string")

    parser.add_argument("--version", action="store_true", help="Show version information")

    parser.add_argument("--examples", action="store_true", help="Show usage examples")

    return parser


def run_fetch_command(args) -> int:
    """Run the main fetch command using orchestrator."""
    try:
        # Create execution configuration
        config = ExecutionConfig(
            pr_url=args.pr_url,
            persona_file=args.persona_file,
            output_format=args.output_format,
            output_file=args.output_file,
            resolved_marker=args.resolved_marker,
            post_resolution_request=args.post_resolution_request,
            show_stats=args.show_stats,
            debug=args.debug,
        )

        # Validate configuration
        print("🔍 Validating configuration...")
        orchestrator = CodeRabbitOrchestrator(config)
        validation_result = orchestrator.validate_configuration()

        if not validation_result["valid"]:
            print("❌ Configuration validation failed:", file=sys.stderr)
            for issue in validation_result["issues"]:
                print(f"   • {issue}", file=sys.stderr)
            return 1

        if validation_result["warnings"]:
            print("⚠️  Configuration warnings:")
            for warning in validation_result["warnings"]:
                print(f"   • {warning}")

        # Execute main workflow
        print("🚀 Starting CodeRabbit Comment Fetcher...")
        results = orchestrator.execute()

        if results["success"]:
            print(f"\n✅ Processing completed successfully in {results['execution_time']:.2f}s!")

            # Show statistics if requested
            if args.show_stats:
                _display_execution_statistics(results["metrics"])

            return 0
        else:
            print(f"\n❌ Processing failed: {results['error']}", file=sys.stderr)

            # Show recovery recommendations
            if results.get("recovery_info", {}).get("recommendations"):
                print("\n💡 Recommended actions:", file=sys.stderr)
                for rec in results["recovery_info"]["recommendations"]:
                    print(f"   {rec}", file=sys.stderr)

            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        logger.exception("Unexpected error in fetch command")
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        return 1


def _display_execution_statistics(metrics: Dict[str, Any]) -> None:
    """Display detailed execution statistics."""
    print("\n📊 Execution Statistics:")
    print(f"   Total execution time: {metrics['execution_time']:.2f}s")
    print(f"   GitHub API calls: {metrics['github_api_calls']}")
    print(f"   GitHub API time: {metrics['github_api_time']:.2f}s")
    print(f"   Analysis time: {metrics['analysis_time']:.2f}s")
    print(f"   Formatting time: {metrics['formatting_time']:.2f}s")
    print(f"   Total comments processed: {metrics['total_comments_processed']}")
    print(f"   CodeRabbit comments found: {metrics['coderabbit_comments_found']}")
    print(f"   Resolved comments filtered: {metrics['resolved_comments_filtered']}")
    print(f"   Output size: {metrics['output_size_bytes']} bytes")
    print(f"   Success rate: {metrics['success_rate']*100:.1f}%")

    if metrics["errors_count"] > 0:
        print(f"   Errors encountered: {metrics['errors_count']}")

    if metrics["warnings_count"] > 0:
        print(f"   Warnings issued: {metrics['warnings_count']}")


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
            version = get_version("coderabbit-comment-fetcher")
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
