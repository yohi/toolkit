"""
Argument parser and main execution orchestrator.

This module handles parsing command line arguments and orchestrating the
main execution flow of the CodeRabbit Comment Fetcher.
"""

import json
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from rich.console import Console

from ..exceptions import InvalidPRUrlError, GitHubAuthenticationError
from ..github.client import GitHubClient
from ..github.comment_poster import CommentPoster
from ..analyzer import CommentAnalyzer

console = Console()


class ArgumentParser:
    """Handles argument parsing and main execution orchestration."""

    PR_URL_PATTERN = re.compile(
        r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)$"
    )

    def __init__(self) -> None:
        """Initialize the argument parser."""
        self.github_client = GitHubClient()
        self.comment_analyzer = CommentAnalyzer()

    def parse_pr_url(self, pr_url: str) -> tuple[str, str, int]:
        """Parse GitHub pull request URL to extract owner, repo, and PR number.

        Args:
            pr_url: GitHub pull request URL

        Returns:
            Tuple of (owner, repo, pr_number)

        Raises:
            InvalidPRUrlError: If URL format is invalid
        """
        match = self.PR_URL_PATTERN.match(pr_url.strip())
        if not match:
            raise InvalidPRUrlError(
                f"Invalid GitHub pull request URL: {pr_url}\n"
                "Expected format: https://github.com/owner/repo/pull/123"
            )

        owner, repo, pr_number_str = match.groups()
        return owner, repo, int(pr_number_str)

    def validate_inputs(
        self,
        pr_url: str,
        persona_file: Optional[Path],
        output_format: str,
        resolved_marker: str,
    ) -> None:
        """Validate input parameters.

        Args:
            pr_url: GitHub pull request URL
            persona_file: Optional path to persona file
            output_format: Output format choice
            resolved_marker: Resolved marker string

        Raises:
            InvalidPRUrlError: If PR URL is invalid
            PersonaFileError: If persona file is invalid
        """
        # Validate PR URL
        self.parse_pr_url(pr_url)

        # Validate persona file if provided
        if persona_file and not persona_file.exists():
            from ..exceptions import PersonaFileError
            raise PersonaFileError(f"Persona file not found: {persona_file}")

        # Validate resolved marker
        if not resolved_marker.strip():
            from ..exceptions import CodeRabbitFetcherError
            raise CodeRabbitFetcherError("Resolved marker cannot be empty")

    def parse_and_execute(
        self,
        pr_url: str,
        persona_file: Optional[Path],
        output_format: str,
        resolved_marker: str,
        request_resolution: bool,
        output_file: Optional[Path],
        verbose: bool,
    ) -> int:
        """Parse arguments and execute the main workflow.

        Args:
            pr_url: GitHub pull request URL
            persona_file: Optional path to persona file
            output_format: Output format choice
            resolved_marker: Resolved marker string
            request_resolution: Whether to post resolution requests
            output_file: Optional output file path
            verbose: Enable verbose output

        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        if verbose:
            console.print("🔍 [blue]Validating inputs...[/blue]")

        # Validate inputs
        self.validate_inputs(pr_url, persona_file, output_format, resolved_marker)

        # Parse PR URL
        owner, repo, pr_number = self.parse_pr_url(pr_url)

        if verbose:
            console.print(f"📋 [blue]Processing PR: {owner}/{repo}#{pr_number}[/blue]")

        # Check GitHub CLI authentication
        if not self.github_client.check_authentication():
            from ..exceptions import GitHubAuthenticationError
            raise GitHubAuthenticationError(
                "GitHub CLI is not authenticated. Please run 'gh auth login' first."
            )

        # Fetch PR comments
        if verbose:
            console.print("📥 [blue]Fetching PR comments...[/blue]")

        comments_data = self.github_client.fetch_pr_comments(pr_url)

        if verbose:
            console.print(f"✅ [green]Successfully fetched PR data[/green]")
            console.print(f"📊 [blue]Found {len(comments_data.get('comments', []))} comments[/blue]")

        # Analyze comments using CommentAnalyzer
        if verbose:
            console.print("🔍 [blue]Analyzing CodeRabbit comments...[/blue]")

        # Update the analyzer with the custom resolved marker
        self.comment_analyzer.resolved_marker = resolved_marker

        # Analyze the comments
        analyzed_comments = self.comment_analyzer.analyze_comments(comments_data)

        if verbose:
            console.print(f"📊 [green]Analysis complete:[/green]")
            console.print(f"   - Total comments: {analyzed_comments.metadata.total_comments}")
            console.print(f"   - Summary comments: {len(analyzed_comments.summary_comments)}")
            console.print(f"   - Review comments: {len(analyzed_comments.review_comments)}")
            console.print(f"   - Actionable items: {analyzed_comments.metadata.actionable_comments}")
            console.print(f"   - Resolved comments: {analyzed_comments.metadata.resolved_comments}")

        # Prepare output data
        output_data = {
            "metadata": {
                "pr_url": pr_url,
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "resolved_marker": resolved_marker,
                "analysis_timestamp": analyzed_comments.metadata.processed_at.isoformat()
            },
            "raw_data": comments_data,
            "analysis": {
                "total_comments": analyzed_comments.metadata.total_comments,
                "resolved_count": analyzed_comments.metadata.resolved_comments,
                "summary_comments": [comment.model_dump() for comment in analyzed_comments.summary_comments],
                "review_comments": [comment.model_dump() for comment in analyzed_comments.review_comments],
                "metadata": analyzed_comments.metadata.model_dump()
            }
        }

        # Output the analyzed data
        if output_file:
            if verbose:
                console.print(f"💾 [blue]Writing analyzed data to {output_file}...[/blue]")
            output_file.write_text(
                json.dumps(output_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        else:
            console.print(json.dumps(output_data, indent=2, ensure_ascii=False))

        # Post resolution request if requested (basic implementation)
        if request_resolution:
            if verbose:
                console.print("📤 [blue]Posting resolution request...[/blue]")

            from ..github.comment_poster import CommentPoster
            poster = CommentPoster(self.github_client)
            success = poster.post_resolution_request(pr_url, resolved_marker)

            if not success:
                console.print("⚠️ [yellow]Failed to post resolution request[/yellow]")
                return 1

        return 0
