"""CodeRabbit Comment Fetcher - Professional GitHub PR comment analysis tool.

A comprehensive tool for fetching, analyzing, and formatting CodeRabbit comments
from GitHub Pull Requests with AI-agent optimization and Claude 4 best practices.

Features:
- GitHub CLI integration for secure API access
- CodeRabbit comment detection and filtering
- Multiple output formats (Markdown, JSON, Plain text)
- Resolved marker management
- Comment posting and resolution request
- Comprehensive validation and error handling
- Performance optimization for large datasets
- Multi-language support (English/Japanese)
- uvx compatibility for easy installation

Usage:
    # Install with uvx (recommended)
    uvx coderabbit-comment-fetcher https://github.com/owner/repo/pull/123

    # Or install with pip
    pip install coderabbit-comment-fetcher
    coderabbit-fetch https://github.com/owner/repo/pull/123

    # With custom options
    coderabbit-fetch https://github.com/owner/repo/pull/123 \\
        --persona-file my_persona.txt \\
        --output-format json \\
        --output-file results.json
"""

import importlib.metadata
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .cli.main import main

try:
    __version__ = importlib.metadata.version("coderabbit-comment-fetcher")
except importlib.metadata.PackageNotFoundError:
    # Development version
    __version__ = "1.0.0-dev"

__title__ = "CodeRabbit Comment Fetcher"
__description__ = "Professional tool to fetch, analyze, and format CodeRabbit comments from GitHub Pull Requests"
__author__ = "CodeRabbit Fetcher Team"
__email__ = "coderabbit-fetcher@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025 CodeRabbit Fetcher Team"

from .exceptions import CodeRabbitFetcherError
from .models import (
    AnalyzedComments, 
    SummaryComment, 
    ReviewComment,
    ActionableComment,
    AIAgentPrompt,
    ThreadContext,
    CommentMetadata,
)

# Package metadata
__all__ = [
    "__version__",
    "__title__",
    "__description__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
    "get_version_info",
    "get_package_info",
    "main",
    "CodeRabbitFetcherError",
    "AnalyzedComments",
    "SummaryComment",
    "ReviewComment",
    "ActionableComment",
    "AIAgentPrompt",
    "ThreadContext", 
    "CommentMetadata",
]


def get_version_info() -> Dict[str, str]:
    """Get detailed version information.
    
    Returns:
        Dictionary containing version details
    """
    import sys
    import platform
    
    return {
        "version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
    }


def get_package_info() -> Dict[str, Any]:
    """Get comprehensive package information.
    
    Returns:
        Dictionary containing package metadata
    """
    return {
        "title": __title__,
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "copyright": __copyright__,
        "version_info": get_version_info(),
    }


# Default configuration
DEFAULT_CONFIG = {
    "resolved_marker": "🔒 CODERABBIT_RESOLVED 🔒",
    "output_format": "markdown",
    "max_retries": 3,
    "timeout": 30,
    "retry_delay": 1.0,
    "claude_best_practices_url": "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices.md",
    "github_cli_required": True,
    "supported_python_versions": ["3.13"],
    "supported_output_formats": ["markdown", "json", "plain"],
}

# Export key components for programmatic usage
from .orchestrator import CodeRabbitOrchestrator, ExecutionConfig
from .github_client import GitHubClient
from .comment_analyzer import CommentAnalyzer

# Lazily expose CLI entry to avoid import-time side effects.
def __getattr__(name: str):
    if name == "main":
        from .cli.main import main as _main
        return _main
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Version check
import sys
if sys.version_info < (3, 13):
    import warnings
    warnings.warn(
        f"CodeRabbit Comment Fetcher requires Python 3.13+, "
        f"but you're using Python {sys.version_info.major}.{sys.version_info.minor}. "
        f"Some features may not work correctly.",
        RuntimeWarning,
        stacklevel=2
    )
