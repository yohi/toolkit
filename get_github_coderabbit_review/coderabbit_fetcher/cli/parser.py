"""
Argument parser and main execution orchestrator.

This module handles parsing command line arguments and orchestrating the
main execution flow of the CodeRabbit Comment Fetcher.
"""

import re
from pathlib import Path
from typing import Optional

from rich.console import Console

from ..exceptions import InvalidPRUrlError
from ..github.client import GitHubClient
from ..analyzer.comment_analyzer import CommentAnalyzer
from ..persona.manager import PersonaManager
from ..formatters.factory import FormatterFactory

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
        self.persona_manager = PersonaManager()
        self.formatter_factory = FormatterFactory()
    
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
        if persona_file and not persona_file.is_file():
            from ..exceptions import PersonaFileError
            raise PersonaFileError(f"Persona file not found: {persona_file}")
        
        # Validate output format (expects normalized format)
        allowed_formats = {"markdown", "json", "plain"}
        if output_format not in allowed_formats:
            from ..exceptions import CodeRabbitFetcherError
            raise CodeRabbitFetcherError(f"Unsupported output_format: {output_format}")
        
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
        
        # Normalize output format early for consistent handling
        output_format = output_format.lower().strip()
        
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
        
        # Analyze comments
        if verbose:
            console.print("🔍 [blue]Analyzing CodeRabbit comments...[/blue]")
        
        analyzed_comments = self.comment_analyzer.analyze_comments(
            comments_data, resolved_marker
        )
        
        # Load persona
        if verbose:
            console.print("🤖 [blue]Loading persona...[/blue]")
        
        persona = self.persona_manager.load_persona(persona_file)
        
        # Format output
        if verbose:
            console.print(f"📝 [blue]Formatting output as {output_format}...[/blue]")
        
        formatter = self.formatter_factory.create_formatter(output_format)
        formatted_output = formatter.format(persona, analyzed_comments)
        
        # Write output
        if output_file:
            if verbose:
                console.print(f"💾 [blue]Writing to {output_file}...[/blue]")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(formatted_output, encoding="utf-8")
        else:
            console.print(formatted_output)
        
        # Post resolution request if requested
        if request_resolution and analyzed_comments.review_comments:
            if verbose:
                console.print("📤 [blue]Posting resolution request...[/blue]")
            
            from ..github.comment_poster import CommentPoster
            poster = CommentPoster(self.github_client)
            success = poster.post_resolution_request(pr_url, resolved_marker)
            
            if not success:
                console.print("⚠️ [yellow]Failed to post resolution request[/yellow]")
                return 1
        
        return 0
