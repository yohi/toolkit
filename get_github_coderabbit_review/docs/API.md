# 🔌 CodeRabbit Comment Fetcher - API Documentation

This document provides comprehensive API documentation for programmatic usage of CodeRabbit Comment Fetcher.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
- [Configuration](#configuration)
- [Data Models](#data-models)
- [Formatters](#formatters)
- [Exception Handling](#exception-handling)
- [Advanced Usage](#advanced-usage)
- [Examples](#examples)

## 🚀 Quick Start

### Basic Programmatic Usage

```python
from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig

# Create configuration
config = ExecutionConfig(
    pr_url="https://github.com/owner/repo/pull/123",
    output_format="json",
    show_stats=True
)

# Execute analysis
orchestrator = CodeRabbitOrchestrator(config)
results = orchestrator.execute()

if results["success"]:
    print(f"Analysis completed successfully")
    print(f"Processed {results['metrics']['comments_processed']} comments")
    print(f"Output: {results['output']}")
else:
    print(f"Analysis failed: {results['error']}")
```

### Advanced Configuration

```python
from coderabbit_fetcher import (
    CodeRabbitOrchestrator,
    ExecutionConfig,
    GitHubClient,
    CommentAnalyzer
)

# Advanced configuration
config = ExecutionConfig(
    pr_url="https://github.com/owner/repo/pull/123",
    persona_file="custom_persona.txt",
    output_format="markdown",
    output_file="analysis.md",
    resolved_marker="✅ RESOLVED",
    post_resolution_request=True,
    timeout=120,
    retry_attempts=5,
    retry_delay=2.0,
    show_stats=True,
    debug=True
)

# Execute with error handling
try:
    orchestrator = CodeRabbitOrchestrator(config)
    results = orchestrator.execute()

    if results["success"]:
        print("✅ Analysis completed successfully")

        # Access detailed metrics
        metrics = results["metrics"]
        print(f"Execution time: {metrics['execution_time']:.2f}s")
        print(f"Comments processed: {metrics['comments_processed']}")
        print(f"Resolved comments: {metrics['resolved_comments']}")

    else:
        print(f"❌ Analysis failed: {results['error']}")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

## 🏗️ Core Classes

### CodeRabbitOrchestrator

Main orchestration class that manages the entire workflow.

```python
class CodeRabbitOrchestrator:
    """Main orchestrator for CodeRabbit comment analysis workflow."""

    def __init__(self, config: ExecutionConfig):
        """Initialize orchestrator with configuration."""

    def execute(self) -> Dict[str, Any]:
        """Execute the complete analysis workflow.

        Returns:
            Dict containing:
            - success: bool - Whether execution succeeded
            - output: str - Formatted output (if successful)
            - metrics: ExecutionMetrics - Execution statistics
            - error: str - Error message (if failed)
        """

    def validate_configuration(self) -> ValidationResult:
        """Validate configuration before execution."""

    def get_progress_tracker(self) -> ProgressTracker:
        """Get current progress tracker."""
```

#### Usage Example

```python
from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig

config = ExecutionConfig(pr_url="https://github.com/owner/repo/pull/123")
orchestrator = CodeRabbitOrchestrator(config)

# Validate configuration
validation = orchestrator.validate_configuration()
if not validation.valid:
    print(f"Configuration errors: {validation.issues}")
    exit(1)

# Execute analysis
results = orchestrator.execute()

# Monitor progress (in another thread)
tracker = orchestrator.get_progress_tracker()
print(f"Current step: {tracker.current_step}")
print(f"Progress: {tracker.progress_percentage}%")
```

### ExecutionConfig

Configuration class for orchestrator execution.

```python
@dataclass
class ExecutionConfig:
    """Configuration for CodeRabbit analysis execution."""

    # Required parameters
    pr_url: str

    # Optional parameters with defaults
    persona_file: Optional[str] = None
    output_format: str = "markdown"  # markdown, json, plain
    output_file: Optional[str] = None
    resolved_marker: str = "🔒 CODERABBIT_RESOLVED 🔒"
    post_resolution_request: bool = False
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    show_stats: bool = False
    debug: bool = False

    def validate(self) -> ValidationResult:
        """Validate configuration parameters."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionConfig':
        """Create configuration from dictionary."""
```

#### Usage Example

```python
from coderabbit_fetcher import ExecutionConfig

# Create configuration
config = ExecutionConfig(
    pr_url="https://github.com/owner/repo/pull/123",
    output_format="json",
    timeout=60,
    show_stats=True
)

# Validate configuration
validation = config.validate()
if not validation.valid:
    for issue in validation.issues:
        print(f"❌ {issue}")

# Convert to/from dictionary
config_dict = config.to_dict()
restored_config = ExecutionConfig.from_dict(config_dict)
```

### GitHubClient

GitHub CLI integration for secure API access.

```python
class GitHubClient:
    """GitHub CLI client for secure API access."""

    def __init__(self, timeout: int = 30):
        """Initialize GitHub client."""

    def check_authentication(self) -> bool:
        """Check if GitHub CLI is authenticated."""

    def validate(self) -> Dict[str, Any]:
        """Validate GitHub CLI setup and authentication.

        Returns:
            Dictionary containing:
            - valid: bool - Whether validation passed
            - issues: List[str] - List of validation issues found
            - warnings: List[str] - List of warnings (if any)

        Raises:
            No exceptions raised directly - errors are returned in the result dictionary
        """

    def fetch_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch pull request comments using GitHub CLI.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            List of comment dictionaries

        Raises:
            GitHubAuthenticationError: If not authenticated
            APIRateLimitError: If rate limit exceeded
            InvalidPRUrlError: If PR not found
            NetworkError: If a network-related issue occurs while fetching PR comments
        """

    def post_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Post a comment to pull request."""
```

#### Usage Example

```python
from coderabbit_fetcher import GitHubClient
from coderabbit_fetcher.exceptions import GitHubAuthenticationError, NetworkError

client = GitHubClient(timeout=60)

# Validate GitHub CLI setup (recommended before use)
validation = client.validate()
if not validation["valid"]:
    print("❌ GitHub CLI validation failed:")
    for issue in validation["issues"]:
        print(f"  - {issue}")
    exit(1)

print("✅ GitHub CLI validated successfully")

# Check authentication
if not client.check_authentication():
    print("❌ GitHub CLI not authenticated. Run: gh auth login")
    exit(1)

# Fetch comments
try:
    comments = client.fetch_pr_comments("owner", "repo", 123)
    print(f"Fetched {len(comments)} comments")

    for comment in comments:
        print(f"Comment {comment['id']}: {comment['body'][:100]}...")

except GitHubAuthenticationError:
    print("❌ Authentication required")
except NetworkError as e:
    print(f"❌ Network error: {e}")
except Exception as e:
    print(f"❌ Error fetching comments: {e}")
```

### CommentAnalyzer

Analyzes and filters CodeRabbit comments.

```python
class CommentAnalyzer:
    """Analyzes and filters CodeRabbit comments."""

    def __init__(self, resolved_marker: str = "🔒 CODERABBIT_RESOLVED 🔒"):
        """Initialize comment analyzer."""

    def filter_coderabbit_comments(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter comments to only include CodeRabbit comments.

        Args:
            comments: List of raw comment dictionaries

        Returns:
            List of filtered CodeRabbit comments
        """

    def classify_comment_type(self, comment: Dict[str, Any]) -> CommentType:
        """Classify comment type based on content."""

    def extract_ai_agent_prompts(self, comments: List[Dict[str, Any]]) -> List[str]:
        """Extract 'Prompt for AI Agents' sections."""

    def group_by_thread(self, comments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group comments by thread/conversation."""

    def analyze_resolution_status(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze resolution status of comments."""
```

#### Usage Example

```python
from coderabbit_fetcher import CommentAnalyzer, CommentType

analyzer = CommentAnalyzer(resolved_marker="✅ RESOLVED")

# Filter CodeRabbit comments
coderabbit_comments = analyzer.filter_coderabbit_comments(all_comments)
print(f"Found {len(coderabbit_comments)} CodeRabbit comments")

# Classify comments
for comment in coderabbit_comments:
    comment_type = analyzer.classify_comment_type(comment)
    print(f"Comment {comment['id']}: {comment_type.value}")

# Extract AI prompts
ai_prompts = analyzer.extract_ai_agent_prompts(coderabbit_comments)
print(f"Found {len(ai_prompts)} AI agent prompts")

# Group by thread
threads = analyzer.group_by_thread(coderabbit_comments)
print(f"Organized into {len(threads)} conversation threads")

# Analyze resolution status
status = analyzer.analyze_resolution_status(coderabbit_comments)
print(f"Resolved: {status['resolved_count']}, Unresolved: {status['unresolved_count']}")
```

## ⚙️ Configuration

### Environment Variables

```python
import os
from coderabbit_fetcher import ExecutionConfig

# Configuration from environment
config = ExecutionConfig(
    pr_url=os.getenv("CODERABBIT_PR_URL"),
    timeout=int(os.getenv("CODERABBIT_TIMEOUT", "30")),
    output_format=os.getenv("CODERABBIT_OUTPUT_FORMAT", "markdown"),
    resolved_marker=os.getenv("CODERABBIT_RESOLVED_MARKER", "🔒 CODERABBIT_RESOLVED 🔒"),
    debug=os.getenv("CODERABBIT_DEBUG", "false").lower() == "true",
)
```

### Configuration File Support

```python
import toml
from coderabbit_fetcher import ExecutionConfig

# Load from TOML file
def load_config_from_file(config_path: str) -> ExecutionConfig:
    """Load configuration from TOML file."""
    with open(config_path, 'r') as f:
        config_data = toml.load(f)

    return ExecutionConfig(**config_data.get('coderabbit', {}))

# Example config.toml:
"""
[coderabbit]
output_format = "json"
timeout = 60
retry_attempts = 5
show_stats = true
resolved_marker = "✅ RESOLVED"
"""

config = load_config_from_file("config.toml")
```

## 📊 Data Models

### Comment Data Model

```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class CommentType(Enum):
    """Types of CodeRabbit comments."""
    NITPICK = "nitpick"
    POTENTIAL_ISSUE = "potential_issue"
    REFACTOR_SUGGESTION = "refactor_suggestion"
    OUTSIDE_DIFF = "outside_diff"
    GENERAL = "general"

class Priority(Enum):
    """Comment priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class AnalyzedComment:
    """Analyzed CodeRabbit comment with metadata."""
    id: int
    body: str
    user: str
    created_at: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    comment_type: CommentType = CommentType.GENERAL
    priority: Priority = Priority.MEDIUM
    resolved: bool = False
    ai_agent_prompt: Optional[str] = None
    thread_id: Optional[str] = None
    suggestions: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyzedComment':
        """Create from dictionary."""
```

### Execution Metrics

```python
@dataclass
class ExecutionMetrics:
    """Metrics from execution."""
    execution_time: float
    comments_fetched: int
    comments_processed: int
    coderabbit_comments: int
    resolved_comments: int
    unresolved_comments: int
    ai_agent_prompts: int
    threads_processed: int
    api_calls_made: int
    errors_encountered: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""

    def get_summary(self) -> str:
        """Get human-readable summary."""
```

## 🎨 Formatters

### Using Built-in Formatters

```python
from coderabbit_fetcher.formatters import (
    MarkdownFormatter,
    JsonFormatter,
    PlainFormatter
)

# Markdown formatting
markdown_formatter = MarkdownFormatter()
markdown_output = markdown_formatter.format(analyzed_comments, metadata)

# JSON formatting
json_formatter = JsonFormatter(indent=2)
json_output = json_formatter.format(analyzed_comments, metadata)

# Plain text formatting
plain_formatter = PlainFormatter()
plain_output = plain_formatter.format(analyzed_comments, metadata)
```

### Custom Formatter

```python
from coderabbit_fetcher.formatters.base import BaseFormatter
from typing import List, Dict, Any

class CustomFormatter(BaseFormatter):
    """Custom output formatter."""

    def format(self, comments: List[AnalyzedComment], metadata: Dict[str, Any]) -> str:
        """Format comments with custom logic."""
        output = []

        # Custom header
        output.append(f"=== Custom Analysis Report ===")
        output.append(f"PR: {metadata.get('pr_number')}")
        output.append(f"Comments: {len(comments)}")
        output.append("")

        # Group by priority
        high_priority = [c for c in comments if c.priority == Priority.HIGH]
        medium_priority = [c for c in comments if c.priority == Priority.MEDIUM]
        low_priority = [c for c in comments if c.priority == Priority.LOW]

        for priority_group, title in [
            (high_priority, "🔴 HIGH PRIORITY"),
            (medium_priority, "🟡 MEDIUM PRIORITY"),
            (low_priority, "🟢 LOW PRIORITY")
        ]:
            if priority_group:
                output.append(f"## {title}")
                for comment in priority_group:
                    output.append(f"- {comment.file_path}:{comment.line_number}")
                    output.append(f"  {comment.body[:100]}...")
                output.append("")

        return "\n".join(output)

# Usage
formatter = CustomFormatter()
custom_output = formatter.format(comments, metadata)
```

## 🚨 Exception Handling

### Exception Hierarchy

```python
from coderabbit_fetcher.exceptions import (
    CodeRabbitFetcherError,           # Base exception
    NetworkError,                     # Network-related errors
    GitHubAuthenticationError,        # Authentication issues
    APIRateLimitError,               # Rate limiting
    InvalidPRUrlError,               # Invalid PR URL
    CommentParsingError,             # Comment parsing issues
    ValidationError,                 # Input validation
    TimeoutError,                    # Network timeouts
    RetryExhaustedError             # Retry attempts exhausted
)

# Comprehensive error handling
try:
    orchestrator = CodeRabbitOrchestrator(config)
    results = orchestrator.execute()

except GitHubAuthenticationError:
    print("❌ GitHub authentication required. Run: gh auth login")

except InvalidPRUrlError as e:
    print(f"❌ Invalid PR URL: {e}")

except APIRateLimitError as e:
    print(f"❌ API rate limit exceeded. Try again later: {e}")

except TimeoutError as e:
    print(f"❌ Request timed out: {e}")

except ValidationError as e:
    print(f"❌ Configuration error: {e}")

except CodeRabbitFetcherError as e:
    print(f"❌ CodeRabbit Fetcher error: {e}")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

#### NetworkError

Base exception class for network-related errors during GitHub API operations.

**Base Class:** `CodeRabbitFetcherError`

**Constructor Signature:**
```python
def __init__(self, message: str, details: str | None = None) -> None:
    """Initialize network error.

    Args:
        message: Human-readable error message
        details: Optional additional details about the error
    """
```

**Typical Use Cases:**
- Network connectivity issues
- DNS resolution failures
- Connection timeouts
- SSL/TLS errors
- API endpoint unreachable

**When It's Thrown:**
This is a base class for network-related exceptions. It's typically not raised directly but through its subclasses:
- `APIRateLimitError` - When GitHub API rate limit is exceeded
- Other network-specific errors during API operations

**Example:**
```python
from coderabbit_fetcher import GitHubClient
from coderabbit_fetcher.exceptions import NetworkError, APIRateLimitError

client = GitHubClient()

try:
    # fetch_pr_comments expects three arguments: owner, repo, pr_number
    comments = client.fetch_pr_comments("owner", "repo", 123)
except APIRateLimitError as e:
    # Handle rate limiting (subclass of NetworkError)
    print(f"⏱️ Rate limit exceeded: {e}")
    if e.details:
        print(f"Details: {e.details}")
except NetworkError as e:
    # Handle other network errors
    print(f"🌐 Network error: {e.message}")
    if e.details:
        print(f"Additional info: {e.details}")
```

### Error Recovery

```python
from coderabbit_fetcher.exceptions import RetryableError, is_recoverable_error

def robust_analysis(config: ExecutionConfig, max_retries: int = 3) -> Dict[str, Any]:
    """Robust analysis with error recovery."""
    for attempt in range(max_retries):
        try:
            orchestrator = CodeRabbitOrchestrator(config)
            return orchestrator.execute()

        except RetryableError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"⚠️  Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f"❌ Max retries exceeded: {e}")
                raise

        except Exception as e:
            if is_recoverable_error(e) and attempt < max_retries - 1:
                print(f"⚠️  Recoverable error, retrying: {e}")
                continue
            else:
                raise

# Usage
try:
    results = robust_analysis(config, max_retries=5)
    print("✅ Analysis completed with error recovery")
except Exception as e:
    print(f"❌ Analysis failed after all retries: {e}")
```

## 🔬 Advanced Usage

### Batch Processing

```python
from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def analyze_pr(pr_url: str, persona_file: str = None) -> Dict[str, Any]:
    """Analyze a single PR."""
    config = ExecutionConfig(
        pr_url=pr_url,
        persona_file=persona_file,
        output_format="json",
        timeout=120
    )

    orchestrator = CodeRabbitOrchestrator(config)
    return orchestrator.execute()

def batch_analyze(pr_urls: List[str], max_workers: int = 3) -> List[Dict[str, Any]]:
    """Analyze multiple PRs in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(analyze_pr, url): url
            for url in pr_urls
        }

        # Collect results
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                result['pr_url'] = url
                results.append(result)
                print(f"✅ Completed: {url}")
            except Exception as e:
                results.append({
                    'pr_url': url,
                    'success': False,
                    'error': str(e)
                })
                print(f"❌ Failed: {url} - {e}")

    return results

# Usage
pr_urls = [
    "https://github.com/owner/repo/pull/101",
    "https://github.com/owner/repo/pull/102",
    "https://github.com/owner/repo/pull/103"
]

batch_results = batch_analyze(pr_urls, max_workers=2)

# Process results
successful = [r for r in batch_results if r.get('success', False)]
failed = [r for r in batch_results if not r.get('success', False)]

print(f"Batch complete: {len(successful)}/{len(batch_results)} successful")
```

### Custom Workflow Integration

```python
from coderabbit_fetcher import GitHubClient, CommentAnalyzer
from coderabbit_fetcher.formatters import JsonFormatter

class CustomWorkflow:
    """Custom workflow with fine-grained control."""

    def __init__(self):
        self.client = GitHubClient()
        self.analyzer = CommentAnalyzer()
        self.formatter = JsonFormatter()

    def analyze_with_custom_logic(self, pr_url: str) -> Dict[str, Any]:
        """Custom analysis workflow."""
        # Parse PR URL
        parts = pr_url.split('/')
        owner, repo, pr_number = parts[-4], parts[-3], int(parts[-1])

        # Fetch comments
        raw_comments = self.client.fetch_pr_comments(owner, repo, pr_number)

        # Custom filtering logic
        filtered_comments = []
        for comment in raw_comments:
            # Custom criteria
            if (comment.get('user', {}).get('login') == 'coderabbitai[bot]' and
                len(comment.get('body', '')) > 50 and
                'potential issue' in comment.get('body', '').lower()):
                filtered_comments.append(comment)

        # Custom analysis
        analysis_results = {
            'pr_url': pr_url,
            'total_comments': len(raw_comments),
            'filtered_comments': len(filtered_comments),
            'high_priority_issues': [],
            'security_concerns': [],
            'performance_issues': []
        }

        for comment in filtered_comments:
            body = comment.get('body', '').lower()

            if any(keyword in body for keyword in ['security', 'vulnerability', 'xss', 'sql injection']):
                analysis_results['security_concerns'].append(comment)
            elif any(keyword in body for keyword in ['performance', 'slow', 'memory', 'cpu']):
                analysis_results['performance_issues'].append(comment)
            elif any(keyword in body for keyword in ['critical', 'important', 'must fix']):
                analysis_results['high_priority_issues'].append(comment)

        return analysis_results

    def generate_custom_report(self, analysis: Dict[str, Any]) -> str:
        """Generate custom report format."""
        report = []
        report.append("# Custom CodeRabbit Analysis Report")
        report.append(f"**PR URL:** {analysis['pr_url']}")
        report.append(f"**Total Comments:** {analysis['total_comments']}")
        report.append(f"**Filtered Comments:** {analysis['filtered_comments']}")
        report.append("")

        if analysis['security_concerns']:
            report.append("## 🔒 Security Concerns")
            for comment in analysis['security_concerns']:
                report.append(f"- {comment['body'][:100]}...")
            report.append("")

        if analysis['performance_issues']:
            report.append("## ⚡ Performance Issues")
            for comment in analysis['performance_issues']:
                report.append(f"- {comment['body'][:100]}...")
            report.append("")

        if analysis['high_priority_issues']:
            report.append("## 🔴 High Priority Issues")
            for comment in analysis['high_priority_issues']:
                report.append(f"- {comment['body'][:100]}...")

        return "\n".join(report)

# Usage
workflow = CustomWorkflow()
analysis = workflow.analyze_with_custom_logic("https://github.com/owner/repo/pull/123")
report = workflow.generate_custom_report(analysis)
print(report)
```

### Progress Monitoring

```python
from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig
import threading
import time

def monitor_progress(orchestrator: CodeRabbitOrchestrator, interval: float = 1.0):
    """Monitor progress in separate thread."""
    while True:
        tracker = orchestrator.get_progress_tracker()
        if tracker:
            print(f"\r🔄 {tracker.current_step}: {tracker.progress_percentage:.1f}% complete", end="")

            if tracker.is_complete:
                print("\n✅ Analysis complete!")
                break

        time.sleep(interval)

# Usage with progress monitoring
config = ExecutionConfig(
    pr_url="https://github.com/large-project/repo/pull/999",
    timeout=300,  # 5 minutes for large PR
    show_stats=True
)

orchestrator = CodeRabbitOrchestrator(config)

# Start progress monitoring in background
progress_thread = threading.Thread(
    target=monitor_progress,
    args=(orchestrator, 0.5)
)
progress_thread.daemon = True
progress_thread.start()

# Execute analysis
results = orchestrator.execute()

# Wait for progress thread to complete
progress_thread.join()

if results["success"]:
    print(f"📊 Metrics: {results['metrics']}")
```

## 📝 Examples

### Complete Example: Enterprise Integration

```python
#!/usr/bin/env python3
"""Enterprise integration example for CodeRabbit Comment Fetcher."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from coderabbit_fetcher import (
    CodeRabbitOrchestrator,
    ExecutionConfig,
    AnalyzedComment,
    Priority
)
from coderabbit_fetcher.exceptions import CodeRabbitFetcherError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('coderabbit_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class EnterpriseAnalyzer:
    """Enterprise-grade CodeRabbit analysis integration."""

    def __init__(self, config_file: str = "enterprise_config.json"):
        """Initialize with enterprise configuration."""
        self.config_file = Path(config_file)
        self.load_configuration()

    def load_configuration(self):
        """Load enterprise configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.enterprise_config = json.load(f)
        else:
            self.enterprise_config = {
                "default_timeout": 120,
                "max_retries": 5,
                "priority_thresholds": {
                    "high_keywords": ["security", "critical", "vulnerability"],
                    "medium_keywords": ["performance", "important", "refactor"],
                    "low_keywords": ["style", "minor", "suggestion"]
                },
                "notification_settings": {
                    "email_on_high_priority": True,
                    "slack_webhook": None
                },
                "output_settings": {
                    "include_ai_prompts": True,
                    "include_statistics": True,
                    "format_for_jira": False
                }
            }

    def analyze_pr(self, pr_url: str, persona_type: str = "default") -> Dict[str, Any]:
        """Analyze PR with enterprise settings."""
        logger.info(f"Starting enterprise analysis for PR: {pr_url}")

        # Select persona file based on type
        persona_files = {
            "security": "examples/personas/security_expert.txt",
            "architecture": "examples/personas/senior_architect.txt",
            "japanese": "examples/personas/japanese_reviewer.txt",
            "default": "examples/personas/default_reviewer.txt"
        }

        persona_file = persona_files.get(persona_type, persona_files["default"])

        # Create configuration
        config = ExecutionConfig(
            pr_url=pr_url,
            persona_file=persona_file,
            output_format="json",
            timeout=self.enterprise_config["default_timeout"],
            retry_attempts=self.enterprise_config["max_retries"],
            show_stats=True,
            debug=False
        )

        # Execute analysis
        try:
            orchestrator = CodeRabbitOrchestrator(config)
            results = orchestrator.execute()

            if results["success"]:
                # Parse JSON output
                analysis_data = json.loads(results["output"])

                # Apply enterprise processing
                enhanced_results = self.enhance_analysis(analysis_data)

                # Generate enterprise report
                report = self.generate_enterprise_report(enhanced_results)

                # Send notifications if configured
                self.send_notifications(enhanced_results)

                logger.info(f"Enterprise analysis completed successfully")
                return {
                    "success": True,
                    "analysis": enhanced_results,
                    "report": report,
                    "metrics": results["metrics"]
                }
            else:
                logger.error(f"Analysis failed: {results['error']}")
                return {
                    "success": False,
                    "error": results["error"]
                }

        except CodeRabbitFetcherError as e:
            logger.error(f"CodeRabbit Fetcher error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    def enhance_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance analysis with enterprise logic."""
        enhanced = analysis_data.copy()

        # Categorize comments by enterprise priorities
        high_priority = []
        medium_priority = []
        low_priority = []

        for comment in enhanced.get("comments", []):
            body = comment.get("body", "").lower()

            # Apply priority rules
            if any(keyword in body for keyword in self.enterprise_config["priority_thresholds"]["high_keywords"]):
                comment["enterprise_priority"] = "high"
                high_priority.append(comment)
            elif any(keyword in body for keyword in self.enterprise_config["priority_thresholds"]["medium_keywords"]):
                comment["enterprise_priority"] = "medium"
                medium_priority.append(comment)
            else:
                comment["enterprise_priority"] = "low"
                low_priority.append(comment)

        # Add enterprise statistics
        enhanced["enterprise_statistics"] = {
            "high_priority_count": len(high_priority),
            "medium_priority_count": len(medium_priority),
            "low_priority_count": len(low_priority),
            "security_issues": len([c for c in enhanced.get("comments", []) if "security" in c.get("body", "").lower()]),
            "performance_issues": len([c for c in enhanced.get("comments", []) if "performance" in c.get("body", "").lower()]),
            "analysis_timestamp": datetime.now().isoformat(),
            "risk_score": self.calculate_risk_score(enhanced.get("comments", []))
        }

        return enhanced

    def calculate_risk_score(self, comments: List[Dict[str, Any]]) -> int:
        """Calculate enterprise risk score (0-100)."""
        if not comments:
            return 0

        risk_score = 0

        for comment in comments:
            body = comment.get("body", "").lower()

            # High risk indicators
            if any(keyword in body for keyword in ["security", "vulnerability", "critical"]):
                risk_score += 20
            elif any(keyword in body for keyword in ["performance", "memory leak", "bottleneck"]):
                risk_score += 10
            elif any(keyword in body for keyword in ["bug", "error", "exception"]):
                risk_score += 5
            else:
                risk_score += 1

        # Normalize to 0-100 scale
        return min(100, risk_score)

    def generate_enterprise_report(self, analysis: Dict[str, Any]) -> str:
        """Generate enterprise-formatted report."""
        metadata = analysis.get("metadata", {})
        stats = analysis.get("enterprise_statistics", {})

        report = []
        report.append("# 🏢 Enterprise CodeRabbit Analysis Report")
        report.append(f"**Generated:** {stats.get('analysis_timestamp', 'N/A')}")
        report.append(f"**PR:** #{metadata.get('pr_number')} - {metadata.get('title', 'N/A')}")
        report.append(f"**Risk Score:** {stats.get('risk_score', 0)}/100")
        report.append("")

        # Executive Summary
        report.append("## 📊 Executive Summary")
        report.append(f"- **Total Issues:** {len(analysis.get('comments', []))}")
        report.append(f"- **High Priority:** {stats.get('high_priority_count', 0)}")
        report.append(f"- **Medium Priority:** {stats.get('medium_priority_count', 0)}")
        report.append(f"- **Low Priority:** {stats.get('low_priority_count', 0)}")
        report.append(f"- **Security Issues:** {stats.get('security_issues', 0)}")
        report.append(f"- **Performance Issues:** {stats.get('performance_issues', 0)}")
        report.append("")

        # Risk Assessment
        risk_score = stats.get('risk_score', 0)
        if risk_score >= 70:
            risk_level = "🔴 HIGH"
            risk_action = "Immediate attention required"
        elif risk_score >= 40:
            risk_level = "🟡 MEDIUM"
            risk_action = "Review and plan fixes"
        else:
            risk_level = "🟢 LOW"
            risk_action = "Monitor and address as capacity allows"

        report.append("## 🎯 Risk Assessment")
        report.append(f"**Risk Level:** {risk_level}")
        report.append(f"**Recommended Action:** {risk_action}")
        report.append("")

        # Detailed Issues
        high_priority_comments = [c for c in analysis.get("comments", []) if c.get("enterprise_priority") == "high"]
        if high_priority_comments:
            report.append("## 🔴 High Priority Issues")
            for comment in high_priority_comments[:10]:  # Limit to top 10
                file_info = f"{comment.get('file', 'N/A')}:{comment.get('line', 'N/A')}"
                report.append(f"### {file_info}")
                report.append(f"{comment.get('body', '')[:200]}...")
                report.append("")

        return "\n".join(report)

    def send_notifications(self, analysis: Dict[str, Any]):
        """Send enterprise notifications."""
        stats = analysis.get("enterprise_statistics", {})

        # Email notification for high priority issues
        if (self.enterprise_config["notification_settings"]["email_on_high_priority"] and
            stats.get("high_priority_count", 0) > 0):
            logger.info(f"Would send email notification for {stats['high_priority_count']} high priority issues")

        # Slack notification
        slack_webhook = self.enterprise_config["notification_settings"]["slack_webhook"]
        if slack_webhook and stats.get("risk_score", 0) >= 50:
            logger.info(f"Would send Slack notification for risk score {stats['risk_score']}")

def main():
    """Main enterprise integration example."""
    if len(sys.argv) < 2:
        print("Usage: python enterprise_example.py <pr_url> [persona_type]")
        sys.exit(1)

    pr_url = sys.argv[1]
    persona_type = sys.argv[2] if len(sys.argv) > 2 else "default"

    # Initialize enterprise analyzer
    analyzer = EnterpriseAnalyzer()

    # Run analysis
    results = analyzer.analyze_pr(pr_url, persona_type)

    if results["success"]:
        print("✅ Enterprise analysis completed successfully")

        # Save results
        output_file = f"enterprise_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results["analysis"], f, indent=2)

        # Save report
        report_file = f"enterprise_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(results["report"])

        print(f"📄 Analysis saved to: {output_file}")
        print(f"📄 Report saved to: {report_file}")

        # Print summary
        stats = results["analysis"].get("enterprise_statistics", {})
        print(f"📊 Risk Score: {stats.get('risk_score', 0)}/100")
        print(f"🔴 High Priority: {stats.get('high_priority_count', 0)}")
        print(f"🟡 Medium Priority: {stats.get('medium_priority_count', 0)}")
        print(f"🟢 Low Priority: {stats.get('low_priority_count', 0)}")

    else:
        print(f"❌ Enterprise analysis failed: {results['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

This comprehensive API documentation provides developers with everything they need to integrate CodeRabbit Comment Fetcher into their applications, from basic usage to enterprise-grade implementations.
