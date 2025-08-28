"""Comprehensive input validation and error handling utilities."""

import re
import os
import sys
import time
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from functools import wraps

from .exceptions import (
    CodeRabbitFetcherError,
    InvalidPRUrlError,
    PersonaFileError,
    GitHubAuthenticationError
)


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operation."""
    valid: bool
    issues: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.details is None:
            self.details = {}
    
    def add_issue(self, message: str) -> None:
        """Add a validation issue."""
        self.issues.append(message)
        self.valid = False
    
    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)
    
    def add_suggestion(self, message: str) -> None:
        """Add a validation suggestion."""
        self.suggestions.append(message)
    
    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        if not other.valid:
            self.valid = False
        self.issues.extend(other.issues)
        self.warnings.extend(other.warnings)
        self.suggestions.extend(other.suggestions)
        self.details.update(other.details)


class URLValidator:
    """Comprehensive URL validation for GitHub pull requests."""
    
    # GitHub URL patterns
    GITHUB_PR_PATTERN = re.compile(
        r'^https://github\.com/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)/pull/(\d+)(?:/.*)?$'
    )
    
    GITHUB_DOMAIN_PATTERN = re.compile(
        r'^(https?://)?(www\.)?github\.com$'
    )
    
    def __init__(self):
        self.timeout = 10  # seconds for connectivity checks
    
    def validate_pr_url(self, url: str) -> ValidationResult:
        """Validate GitHub pull request URL comprehensively.
        
        Args:
            url: The URL to validate
            
        Returns:
            ValidationResult with detailed validation information
        """
        result = ValidationResult(valid=True)
        
        if not url:
            result.add_issue("PR URL cannot be empty")
            return result
        
        if not isinstance(url, str):
            result.add_issue("PR URL must be a string")
            return result
        
        # Basic format validation
        url = url.strip()
        
        # Protocol validation
        if not url.startswith(('http://', 'https://')):
            result.add_issue("URL must start with http:// or https://")
            result.add_suggestion("Use: https://github.com/owner/repo/pull/123")
            return result
        
        # Recommend HTTPS
        if url.startswith('http://'):
            result.add_warning("HTTP URLs are not recommended, use HTTPS")
            # Auto-correct to HTTPS
            url = url.replace('http://', 'https://', 1)
            result.add_suggestion(f"Corrected URL: {url}")
        
        # Parse URL components
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as e:
            result.add_issue(f"Invalid URL format: {e}")
            return result
        
        # Domain validation
        if not self._is_github_domain(parsed.netloc):
            result.add_issue(f"URL must be from github.com domain, got: {parsed.netloc}")
            result.add_suggestion("Use format: https://github.com/owner/repo/pull/123")
            return result
        
        # GitHub PR pattern validation
        match = self.GITHUB_PR_PATTERN.match(url)
        if not match:
            result.add_issue("URL does not match GitHub pull request format")
            result.add_suggestion("Expected format: https://github.com/owner/repo/pull/123")
            return result
        
        # Extract components
        owner, repo, pr_number = match.groups()
        
        # Validate components
        owner_validation = self._validate_github_identifier(owner, "owner")
        repo_validation = self._validate_github_identifier(repo, "repository")
        pr_validation = self._validate_pr_number(pr_number)
        
        result.merge(owner_validation)
        result.merge(repo_validation)
        result.merge(pr_validation)
        
        # Store parsed components
        result.details.update({
            "owner": owner,
            "repo": repo,
            "pr_number": int(pr_number),
            "normalized_url": url
        })
        
        return result
    
    def _is_github_domain(self, domain: str) -> bool:
        """Check if domain is a valid GitHub domain."""
        valid_domains = [
            'github.com',
            'www.github.com'
        ]
        return domain.lower() in valid_domains
    
    def _validate_github_identifier(self, identifier: str, type_name: str) -> ValidationResult:
        """Validate GitHub owner/repository identifier."""
        result = ValidationResult(valid=True)
        
        if not identifier:
            result.add_issue(f"GitHub {type_name} cannot be empty")
            return result
        
        # Length validation
        if len(identifier) > 39:
            result.add_issue(f"GitHub {type_name} cannot exceed 39 characters")
        
        # Character validation
        if not re.match(r'^[a-zA-Z0-9._-]+$', identifier):
            result.add_issue(f"GitHub {type_name} contains invalid characters")
            result.add_suggestion("Only letters, numbers, dots, hyphens, and underscores are allowed")
        
        # Cannot start/end with special characters
        if identifier.startswith(('.', '-')) or identifier.endswith(('.', '-')):
            result.add_issue(f"GitHub {type_name} cannot start or end with dots or hyphens")
        
        # Reserved names
        reserved_names = ['api', 'www', 'github', 'help', 'status', 'blog']
        if identifier.lower() in reserved_names:
            result.add_warning(f"'{identifier}' is a reserved GitHub name")
        
        return result
    
    def _validate_pr_number(self, pr_number: str) -> ValidationResult:
        """Validate pull request number."""
        result = ValidationResult(valid=True)
        
        try:
            num = int(pr_number)
            if num <= 0:
                result.add_issue("Pull request number must be positive")
            elif num > 999999:  # Reasonable upper bound
                result.add_warning("Pull request number seems unusually high")
        except ValueError:
            result.add_issue(f"Pull request number must be a valid integer, got: {pr_number}")
        
        return result


class FileValidator:
    """Comprehensive file and path validation."""
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_persona_extensions = {'.txt', '.md', '.text'}
    
    def validate_persona_file(self, file_path: str) -> ValidationResult:
        """Validate persona file comprehensively.
        
        Args:
            file_path: Path to the persona file
            
        Returns:
            ValidationResult with detailed validation information
        """
        result = ValidationResult(valid=True)
        
        if not file_path:
            result.add_issue("Persona file path cannot be empty")
            return result
        
        # Convert to Path object
        try:
            path = Path(file_path).resolve()
        except Exception as e:
            result.add_issue(f"Invalid file path: {e}")
            return result
        
        # Existence check
        if not path.exists():
            result.add_issue(f"Persona file does not exist: {path}")
            result.add_suggestion("Check the file path and ensure the file exists")
            return result
        
        # File type check
        if not path.is_file():
            result.add_issue(f"Path is not a file: {path}")
            return result
        
        # Extension validation
        if path.suffix.lower() not in self.allowed_persona_extensions:
            result.add_warning(f"Unusual file extension: {path.suffix}")
            result.add_suggestion(f"Recommended extensions: {', '.join(self.allowed_persona_extensions)}")
        
        # Permissions check
        if not os.access(path, os.R_OK):
            result.add_issue(f"File is not readable: {path}")
            result.add_suggestion("Check file permissions")
            return result
        
        # Size validation
        try:
            file_size = path.stat().st_size
            if file_size == 0:
                result.add_warning("Persona file is empty")
            elif file_size > self.max_file_size:
                result.add_issue(f"Persona file too large: {file_size} bytes (max: {self.max_file_size})")
            
            result.details['file_size'] = file_size
        except Exception as e:
            result.add_warning(f"Could not check file size: {e}")
        
        # Content validation
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Read first 1KB for validation
                
                # Check for binary content
                if '\x00' in content:
                    result.add_issue("File appears to be binary, not text")
                    return result
                
                # Check encoding
                try:
                    content.encode('utf-8')
                except UnicodeEncodeError:
                    result.add_warning("File contains non-UTF-8 characters")
                
                result.details['preview'] = content[:200]  # Store preview
                
        except UnicodeDecodeError:
            result.add_issue("File is not valid UTF-8 text")
        except Exception as e:
            result.add_warning(f"Could not read file content: {e}")
        
        return result
    
    def validate_output_path(self, output_path: str) -> ValidationResult:
        """Validate output file path.
        
        Args:
            output_path: Path for output file
            
        Returns:
            ValidationResult with detailed validation information
        """
        result = ValidationResult(valid=True)
        
        if not output_path:
            result.add_issue("Output path cannot be empty")
            return result
        
        try:
            path = Path(output_path).resolve()
        except Exception as e:
            result.add_issue(f"Invalid output path: {e}")
            return result
        
        # Parent directory validation
        parent_dir = path.parent
        
        # Check if parent directory exists or can be created
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
                result.add_suggestion(f"Created output directory: {parent_dir}")
            except Exception as e:
                result.add_issue(f"Cannot create output directory: {e}")
                return result
        
        # Check write permissions on parent directory
        if not os.access(parent_dir, os.W_OK):
            result.add_issue(f"No write permission for directory: {parent_dir}")
            return result
        
        # Check if file already exists
        if path.exists():
            if not path.is_file():
                result.add_issue(f"Output path exists but is not a file: {path}")
                return result
            
            if not os.access(path, os.W_OK):
                result.add_issue(f"No write permission for existing file: {path}")
                return result
            
            result.add_warning(f"Output file already exists and will be overwritten: {path}")
        
        # File extension validation
        if path.suffix:
            common_extensions = {'.md', '.json', '.txt', '.html'}
            if path.suffix.lower() not in common_extensions:
                result.add_warning(f"Unusual output file extension: {path.suffix}")
        
        result.details['resolved_path'] = str(path)
        return result


class OptionsValidator:
    """Validate command-line options and configuration."""
    
    def __init__(self):
        self.valid_formats = {'markdown', 'json', 'plain'}
        self.valid_log_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR'}
    
    def validate_output_format(self, format_name: str) -> ValidationResult:
        """Validate output format option."""
        result = ValidationResult(valid=True)
        
        if not format_name:
            result.add_issue("Output format cannot be empty")
            return result
        
        if format_name not in self.valid_formats:
            result.add_issue(f"Invalid output format: {format_name}")
            result.add_suggestion(f"Valid formats: {', '.join(sorted(self.valid_formats))}")
        
        return result
    
    def validate_timeout(self, timeout: Union[int, float, str]) -> ValidationResult:
        """Validate timeout value."""
        result = ValidationResult(valid=True)
        
        try:
            timeout_val = float(timeout)
        except (ValueError, TypeError):
            result.add_issue(f"Timeout must be a number, got: {timeout}")
            return result
        
        if timeout_val <= 0:
            result.add_issue("Timeout must be positive")
        elif timeout_val < 5:
            result.add_warning("Very short timeout may cause failures")
            result.add_suggestion("Consider using at least 10 seconds")
        elif timeout_val > 600:  # 10 minutes
            result.add_warning("Very long timeout specified")
        
        result.details['timeout_seconds'] = timeout_val
        return result
    
    def validate_retry_settings(self, attempts: Union[int, str], delay: Union[int, float, str]) -> ValidationResult:
        """Validate retry configuration."""
        result = ValidationResult(valid=True)
        
        # Validate attempts
        try:
            attempts_val = int(attempts)
        except (ValueError, TypeError):
            result.add_issue(f"Retry attempts must be an integer, got: {attempts}")
            return result
        
        if attempts_val < 0:
            result.add_issue("Retry attempts cannot be negative")
        elif attempts_val > 10:
            result.add_warning("High number of retry attempts may cause long delays")
        
        # Validate delay
        try:
            delay_val = float(delay)
        except (ValueError, TypeError):
            result.add_issue(f"Retry delay must be a number, got: {delay}")
            return result
        
        if delay_val < 0:
            result.add_issue("Retry delay cannot be negative")
        elif delay_val > 60:  # 1 minute
            result.add_warning("Very long retry delay specified")
        
        result.details.update({
            'retry_attempts': attempts_val,
            'retry_delay': delay_val
        })
        
        return result
    
    def validate_resolved_marker(self, marker: str) -> ValidationResult:
        """Validate resolved marker string."""
        result = ValidationResult(valid=True)
        
        if not marker:
            result.add_issue("Resolved marker cannot be empty")
            return result
        
        if len(marker) < 3:
            result.add_warning("Very short resolved marker may cause false positives")
            result.add_suggestion("Use at least 3 characters for better uniqueness")
        
        if len(marker) > 100:
            result.add_warning("Very long resolved marker may be unwieldy")
        
        # Check for special characters (good for uniqueness)
        special_chars = set('🔒🎯✅❌⚠️💡🔧📝📊🚀')
        marker_chars = set(marker)
        
        if not marker_chars.intersection(special_chars):
            result.add_suggestion("Consider adding special characters (🔒, ✅, etc.) for better uniqueness")
        
        # Check for common words that might cause false positives
        common_words = ['resolved', 'done', 'fixed', 'complete', 'finished']
        marker_lower = marker.lower()
        
        conflicting_words = [word for word in common_words if word in marker_lower]
        if conflicting_words:
            result.add_warning(f"Marker contains common words that may cause false positives: {', '.join(conflicting_words)}")
        
        result.details['marker_length'] = len(marker)
        result.details['special_char_count'] = len(marker_chars.intersection(special_chars))
        
        return result


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator for adding retry logic to functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by for each retry
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed, re-raise
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    current_delay = delay * (backoff_factor ** attempt)
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                                 f"Retrying in {current_delay:.1f}s...")
                    
                    time.sleep(current_delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def timeout_handler(timeout_seconds: float) -> Callable:
    """Decorator for adding timeout handling to functions.
    
    Args:
        timeout_seconds: Timeout in seconds
        
    Returns:
        Decorated function with timeout handling
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if sys.platform == "win32":
                # Windows doesn't support signal-based timeouts
                # Use a simpler approach or skip timeout on Windows
                logger.warning("Timeout handling not fully supported on Windows")
                return func(*args, **kwargs)
            
            import signal
            
            def timeout_handler_func(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")
            
            # Set up the timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler_func)
            signal.alarm(int(timeout_seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel the alarm
                return result
            except TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s")
                raise
            finally:
                signal.alarm(0)  # Ensure alarm is cancelled
                signal.signal(signal.SIGALRM, old_handler)  # Restore old handler
        
        return wrapper
    return decorator


class ValidationSuite:
    """Comprehensive validation suite for all inputs."""
    
    def __init__(self):
        self.url_validator = URLValidator()
        self.file_validator = FileValidator()
        self.options_validator = OptionsValidator()
    
    def validate_all_inputs(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate all configuration inputs comprehensively.
        
        Args:
            config: Dictionary of configuration values
            
        Returns:
            ValidationResult with combined validation results
        """
        result = ValidationResult(valid=True)
        
        # Validate PR URL
        if 'pr_url' in config:
            url_result = self.url_validator.validate_pr_url(config['pr_url'])
            result.merge(url_result)
        
        # Validate persona file
        if config.get('persona_file'):
            file_result = self.file_validator.validate_persona_file(config['persona_file'])
            result.merge(file_result)
        
        # Validate output file
        if config.get('output_file'):
            output_result = self.file_validator.validate_output_path(config['output_file'])
            result.merge(output_result)
        
        # Validate output format
        if 'output_format' in config:
            format_result = self.options_validator.validate_output_format(config['output_format'])
            result.merge(format_result)
        
        # Validate timeout
        if 'timeout_seconds' in config:
            timeout_result = self.options_validator.validate_timeout(config['timeout_seconds'])
            result.merge(timeout_result)
        
        # Validate retry settings
        if 'retry_attempts' in config and 'retry_delay' in config:
            retry_result = self.options_validator.validate_retry_settings(
                config['retry_attempts'], config['retry_delay']
            )
            result.merge(retry_result)
        
        # Validate resolved marker
        if 'resolved_marker' in config:
            marker_result = self.options_validator.validate_resolved_marker(config['resolved_marker'])
            result.merge(marker_result)
        
        return result
    
    def generate_validation_report(self, result: ValidationResult) -> str:
        """Generate a user-friendly validation report.
        
        Args:
            result: ValidationResult to generate report for
            
        Returns:
            Formatted validation report string
        """
        report_lines = []
        
        if result.valid:
            report_lines.append("✅ Configuration validation passed")
        else:
            report_lines.append("❌ Configuration validation failed")
        
        if result.issues:
            report_lines.append("\n🔴 Issues found:")
            for issue in result.issues:
                report_lines.append(f"   • {issue}")
        
        if result.warnings:
            report_lines.append("\n⚠️  Warnings:")
            for warning in result.warnings:
                report_lines.append(f"   • {warning}")
        
        if result.suggestions:
            report_lines.append("\n💡 Suggestions:")
            for suggestion in result.suggestions:
                report_lines.append(f"   • {suggestion}")
        
        if result.details:
            report_lines.append("\n📊 Validation details:")
            for key, value in result.details.items():
                if isinstance(value, (int, float)):
                    report_lines.append(f"   • {key}: {value}")
                elif isinstance(value, str) and len(value) < 100:
                    report_lines.append(f"   • {key}: {value}")
        
        return "\n".join(report_lines)
