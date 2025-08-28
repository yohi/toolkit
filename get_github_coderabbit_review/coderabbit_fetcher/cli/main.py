"""
Main CLI entry point for CodeRabbit Comment Fetcher.

This module provides the command-line interface for fetching and formatting
CodeRabbit comments from GitHub pull requests.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.traceback import install

from ..exceptions import CodeRabbitFetcherError
from .parser import ArgumentParser

# Install rich traceback handler for better error display
install(show_locals=True)

console = Console()


@click.command()
@click.argument("pr_url", type=str)
@click.option(
    "--persona-file",
    "-p",
    type=click.Path(exists=True, path_type=Path),
    help="Path to persona file for AI context",
)
@click.option(
    "--output-format",
    "-f",
    type=click.Choice(["markdown", "json", "plain"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option(
    "--resolved-marker",
    "-m",
    default="🔒 CODERABBIT_RESOLVED 🔒",
    help="Marker string for resolved comments",
)
@click.option(
    "--request-resolution",
    "-r",
    is_flag=True,
    help="Post resolution request to CodeRabbit",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: stdout)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.version_option(version="1.0.0")
@click.help_option("--help", "-h")
def cli(
    pr_url: str,
    persona_file: Optional[Path],
    output_format: str,
    resolved_marker: str,
    request_resolution: bool,
    output_file: Optional[Path],
    verbose: bool,
) -> None:
    """Fetch and format CodeRabbit comments from GitHub pull requests.

    PR_URL should be a GitHub pull request URL like:
    https://github.com/owner/repo/pull/123

    Examples:
        coderabbit-fetch https://github.com/owner/repo/pull/123
        coderabbit-fetch https://github.com/owner/repo/pull/123 --format json
        coderabbit-fetch https://github.com/owner/repo/pull/123 --persona-file persona.txt
    """
    try:
        parser = ArgumentParser()
        result = parser.parse_and_execute(
            pr_url=pr_url,
            persona_file=persona_file,
            output_format=output_format,
            resolved_marker=resolved_marker,
            request_resolution=request_resolution,
            output_file=output_file,
            verbose=verbose,
        )

        if result == 0:
            console.print("✅ [green]Successfully processed CodeRabbit comments[/green]")
        else:
            console.print("⚠️ [yellow]Processing completed with warnings[/yellow]")

    except CodeRabbitFetcherError as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n⏹️ [yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"💥 [red]Unexpected error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI application."""
    cli()


if __name__ == "__main__":
    main()
