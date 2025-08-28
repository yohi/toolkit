"""Utility functions for exception handling and error reporting."""

import sys
import traceback
import logging
from typing import List, Dict, Any, Optional, Union, Type
from datetime import datetime

from .base import CodeRabbitFetcherError


logger = logging.getLogger(__name__)


def format_exception_for_user(exc: Exception) -> str:
    """Format any exception for user-friendly display.
    
    Args:
        exc: Exception to format
        
    Returns:
        User-friendly error message
    """
    if isinstance(exc, CodeRabbitFetcherError):
        return exc.get_user_message()
    
    # Handle standard Python exceptions
    exception_formatters = {
        FileNotFoundError: lambda e: f"❌ File not found: {getattr(e, 'filename', 'unknown')}\n💡 Check the file path and ensure it exists",
        PermissionError: lambda e: f"❌ Permission denied: {getattr(e, 'filename', 'unknown')}\n💡 Check file permissions and access rights",
        ConnectionError: lambda e: "❌ Network connection error\n💡 Check your internet connection and try again",
        TimeoutError: lambda e: "❌ Operation timed out\n💡 Try again or increase timeout value",
        KeyboardInterrupt: lambda e: "⚠️  Operation cancelled by user",
        ValueError: lambda e: f"❌ Invalid value: {e}\n💡 Check input parameters and format",
        TypeError: lambda e: f"❌ Type error: {e}\n💡 Check parameter types and usage",
        OSError: lambda e: f"❌ System error: {e}\n💡 Check system resources and permissions",
    }
    
    for exc_type, formatter in exception_formatters.items():
        if isinstance(exc, exc_type):
            return formatter(exc)
    
    # Generic exception
    return f"❌ Unexpected error: {exc}\n💡 Please report this issue if it persists"


def create_error_summary(exceptions: List[Exception]) -> Dict[str, Any]:
    """Create a summary of multiple exceptions for reporting.
    
    Args:
        exceptions: List of exceptions to summarize
        
    Returns:
        Dictionary with error summary information
    """
    if not exceptions:
        return {
            "total_errors": 0,
            "error_types": {},
            "recoverable_count": 0,
            "critical_count": 0,
            "suggestions": []
        }
    
    summary = {
        "total_errors": len(exceptions),
        "error_types": {},
        "recoverable_count": 0,
        "critical_count": 0,
        "suggestions": set(),
        "most_common_error": None,
        "first_error": None,
        "last_error": None,
        "error_timeline": []
    }
    
    for i, exc in enumerate(exceptions):
        error_type = type(exc).__name__
        summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1
        
        # Track timeline
        summary["error_timeline"].append({
            "index": i,
            "type": error_type,
            "message": str(exc),
            "timestamp": getattr(exc, 'timestamp', None)
        })
        
        if isinstance(exc, CodeRabbitFetcherError):
            if getattr(exc, 'recoverable', True):
                summary["recoverable_count"] += 1
            else:
                summary["critical_count"] += 1
            
            summary["suggestions"].update(getattr(exc, 'suggestions', []))
        else:
            # Assume non-CodeRabbit exceptions are recoverable unless known otherwise
            critical_types = {KeyboardInterrupt, SystemExit, MemoryError}
            if type(exc) in critical_types:
                summary["critical_count"] += 1
            else:
                summary["recoverable_count"] += 1
    
    # Find most common error type
    if summary["error_types"]:
        summary["most_common_error"] = max(
            summary["error_types"].items(), 
            key=lambda x: x[1]
        )[0]
    
    # First and last errors
    summary["first_error"] = {
        "type": type(exceptions[0]).__name__,
        "message": str(exceptions[0])
    }
    summary["last_error"] = {
        "type": type(exceptions[-1]).__name__,
        "message": str(exceptions[-1])
    }
    
    summary["suggestions"] = list(summary["suggestions"])
    return summary


def log_exception_details(exc: Exception, context: Optional[str] = None) -> None:
    """Log detailed exception information for debugging.
    
    Args:
        exc: Exception to log
        context: Optional context information
    """
    log_level = logging.ERROR
    
    # Use WARNING for recoverable errors
    if isinstance(exc, CodeRabbitFetcherError) and getattr(exc, 'recoverable', True):
        log_level = logging.WARNING
    
    context_str = f" (Context: {context})" if context else ""
    logger.log(log_level, f"Exception occurred{context_str}: {exc}")
    
    if isinstance(exc, CodeRabbitFetcherError):
        # Log detailed information for our custom exceptions
        debug_info = exc.get_debug_info()
        logger.debug(f"Exception details: {debug_info}")
    else:
        # Log traceback for unexpected exceptions
        logger.debug(f"Exception traceback: {traceback.format_exc()}")


def is_recoverable_error(exc: Exception) -> bool:
    """Determine if an exception is recoverable.
    
    Args:
        exc: Exception to check
        
    Returns:
        True if the error is recoverable
    """
    if isinstance(exc, CodeRabbitFetcherError):
        return getattr(exc, 'recoverable', True)
    
    # Standard Python exceptions classification
    recoverable_types = {
        ConnectionError,
        TimeoutError,
        OSError,  # Most OS errors are recoverable
        ValueError,  # Often user input issues
        FileNotFoundError,  # User can fix file paths
        PermissionError,  # User can fix permissions
    }
    
    non_recoverable_types = {
        KeyboardInterrupt,
        SystemExit,
        MemoryError,
        RecursionError,
        SyntaxError,  # Code issues
        ImportError,  # Environment issues
    }
    
    if type(exc) in non_recoverable_types:
        return False
    
    if type(exc) in recoverable_types:
        return True
    
    # Default to recoverable for unknown exceptions
    return True


def get_error_category(exc: Exception) -> str:
    """Categorize an exception for reporting purposes.
    
    Args:
        exc: Exception to categorize
        
    Returns:
        Error category string
    """
    if isinstance(exc, CodeRabbitFetcherError):
        # Use the module name as category
        module_name = exc.__class__.__module__
        if '.' in module_name:
            return module_name.split('.')[-1]  # e.g., 'auth', 'network', 'validation'
        return 'application'
    
    # Standard Python exception categories
    category_map = {
        # Network and I/O
        ConnectionError: 'network',
        TimeoutError: 'network',
        OSError: 'system',
        FileNotFoundError: 'file_system',
        PermissionError: 'file_system',
        
        # Input and validation
        ValueError: 'validation',
        TypeError: 'validation',
        
        # System and runtime
        MemoryError: 'system',
        RecursionError: 'system',
        KeyboardInterrupt: 'user_action',
        SystemExit: 'user_action',
        
        # Code and import issues
        SyntaxError: 'code',
        ImportError: 'environment',
        AttributeError: 'code',
        NameError: 'code',
    }
    
    return category_map.get(type(exc), 'unknown')


def create_error_report(
    exceptions: List[Exception],
    context: Optional[Dict[str, Any]] = None,
    include_traceback: bool = False
) -> str:
    """Create a comprehensive error report.
    
    Args:
        exceptions: List of exceptions to include in report
        context: Optional context information
        include_traceback: Whether to include traceback information
        
    Returns:
        Formatted error report string
    """
    if not exceptions:
        return "No errors to report."
    
    report_lines = [
        "🔍 Error Report",
        "=" * 50,
        f"Generated: {datetime.now().isoformat()}",
        f"Total Errors: {len(exceptions)}",
        ""
    ]
    
    # Add context if provided
    if context:
        report_lines.extend([
            "📋 Context:",
            *[f"   {k}: {v}" for k, v in context.items()],
            ""
        ])
    
    # Error summary
    summary = create_error_summary(exceptions)
    report_lines.extend([
        "📊 Error Summary:",
        f"   Recoverable: {summary['recoverable_count']}",
        f"   Critical: {summary['critical_count']}",
        f"   Most Common: {summary['most_common_error']}",
        ""
    ])
    
    # Error types breakdown
    if summary["error_types"]:
        report_lines.extend([
            "📈 Error Types:",
            *[f"   {error_type}: {count}" for error_type, count in 
              sorted(summary["error_types"].items(), key=lambda x: x[1], reverse=True)],
            ""
        ])
    
    # Individual errors
    report_lines.append("📝 Individual Errors:")
    for i, exc in enumerate(exceptions, 1):
        report_lines.extend([
            f"   {i}. {type(exc).__name__}: {exc}",
            f"      Category: {get_error_category(exc)}",
            f"      Recoverable: {is_recoverable_error(exc)}"
        ])
        
        if isinstance(exc, CodeRabbitFetcherError) and exc.suggestions:
            report_lines.extend([
                "      Suggestions:",
                *[f"        • {suggestion}" for suggestion in exc.suggestions]
            ])
        
        if include_traceback:
            tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
            report_lines.extend([
                "      Traceback:",
                *[f"        {line.rstrip()}" for line in tb]
            ])
        
        report_lines.append("")
    
    # Recommendations
    if summary["suggestions"]:
        report_lines.extend([
            "💡 Recommendations:",
            *[f"   • {suggestion}" for suggestion in summary["suggestions"][:10]],  # Limit to top 10
            ""
        ])
    
    return "\n".join(report_lines)


def chain_exceptions(*exceptions: Exception) -> Exception:
    """Chain multiple exceptions together for comprehensive error reporting.
    
    Args:
        exceptions: Exceptions to chain
        
    Returns:
        Chained exception with context from all input exceptions
    """
    if not exceptions:
        return CodeRabbitFetcherError("No exceptions provided")
    
    if len(exceptions) == 1:
        return exceptions[0]
    
    # Use the last exception as the main one
    main_exc = exceptions[-1]
    
    # Create a detailed message with all exception information
    messages = []
    for i, exc in enumerate(exceptions):
        messages.append(f"{i+1}. {type(exc).__name__}: {exc}")
    
    chained_message = f"Multiple errors occurred:\n" + "\n".join(messages)
    
    # If main exception is a CodeRabbitFetcherError, preserve its structure
    if isinstance(main_exc, CodeRabbitFetcherError):
        details = getattr(main_exc, 'details', {})
        details['chained_exceptions'] = [str(exc) for exc in exceptions[:-1]]
        
        return type(main_exc)(
            chained_message,
            details=details,
            suggestions=getattr(main_exc, 'suggestions', []),
            error_code=getattr(main_exc, 'error_code', None),
            recoverable=getattr(main_exc, 'recoverable', True)
        )
    
    # For non-CodeRabbit exceptions, wrap in a generic error
    return CodeRabbitFetcherError(
        chained_message,
        details={'chained_exceptions': [str(exc) for exc in exceptions]},
        suggestions=["Review all error messages above", "Address issues in order"]
    )
