"""Code quality improvement utilities."""

import logging
import re
import time
from functools import wraps
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


def complexity_reducer(max_lines: int = 50, max_params: int = 5) -> Callable:
    """Decorator to enforce complexity limits on functions.

    Args:
        max_lines: Maximum number of lines allowed in function
        max_params: Maximum number of parameters allowed

    Returns:
        Decorated function with complexity validation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check parameter count
            total_params = len(args) + len(kwargs)
            if total_params > max_params:
                logger.warning(
                    f"Function {func.__name__} has {total_params} parameters "
                    f"(max recommended: {max_params})"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_input_types(**type_hints):
    """Decorator to validate input types at runtime.

    Args:
        **type_hints: Type hints for validation

    Returns:
        Decorated function with type validation
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate kwargs types
            for param_name, expected_type in type_hints.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if value is not None and not isinstance(value, expected_type):
                        raise TypeError(
                            f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def safe_execute(default_return=None, log_errors: bool = True) -> Callable:
    """Decorator for safe execution with error handling.

    Args:
        default_return: Default value to return on error
        log_errors: Whether to log errors

    Returns:
        Decorated function with error handling
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                return default_return

        return wrapper

    return decorator


class CodeQualityAnalyzer:
    """Analyzes code quality metrics for functions and classes."""

    @staticmethod
    def calculate_complexity_score(content: str) -> Dict[str, Any]:
        """Calculate complexity score for code content.

        Args:
            content: Code content to analyze

        Returns:
            Dictionary with complexity metrics
        """
        lines = content.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # Count cyclomatic complexity indicators
        complexity_keywords = [
            "if",
            "elif",
            "else",
            "for",
            "while",
            "try",
            "except",
            "and",
            "or",
            "lambda",
            "with",
        ]

        complexity_count = 0
        for line in non_empty_lines:
            line_lower = line.lower().strip()
            for keyword in complexity_keywords:
                if f" {keyword} " in f" {line_lower} ":
                    complexity_count += 1

        # Calculate maintainability index (simplified)
        maintainability_score = max(0, 100 - complexity_count * 5 - len(non_empty_lines) * 0.5)

        return {
            "line_count": len(non_empty_lines),
            "complexity_count": complexity_count,
            "maintainability_score": maintainability_score,
            "complexity_level": (
                "low" if complexity_count < 5 else "medium" if complexity_count < 10 else "high"
            ),
        }

    @staticmethod
    def suggest_refactoring(content: str, function_name: str = "") -> List[str]:
        """Suggest refactoring opportunities.

        Args:
            content: Code content to analyze
            function_name: Name of the function being analyzed

        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        lines = content.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        # Long function suggestion
        if len(non_empty_lines) > 50:
            suggestions.append(
                f"Function {function_name} is {len(non_empty_lines)} lines long. "
                "Consider breaking it into smaller functions."
            )

        # High nesting level
        max_indent = 0
        for line in non_empty_lines:
            if line.strip():
                indent_level = (len(line) - len(line.lstrip())) // 4
                max_indent = max(max_indent, indent_level)

        if max_indent > 4:
            suggestions.append(
                f"High nesting level detected ({max_indent}). "
                "Consider extracting nested logic into separate functions."
            )

        # Duplicate code patterns
        line_patterns: dict[str, int] = {}
        for line in non_empty_lines:
            clean_line = re.sub(r"\s+", " ", line.strip())
            if len(clean_line) > 20:  # Only check substantial lines
                if clean_line in line_patterns:
                    line_patterns[clean_line] += 1
                else:
                    line_patterns[clean_line] = 1

        duplicates = {line: count for line, count in line_patterns.items() if count > 2}
        if duplicates:
            suggestions.append(
                "Duplicate code patterns detected. Consider extracting common logic."
            )

        # Too many parameters (for function definitions)
        param_matches = re.findall(r"def\s+\w+\s*\(([^)]*)\)", content)
        for params in param_matches:
            param_count = len([p.strip() for p in params.split(",") if p.strip()])
            if param_count > 5:
                suggestions.append(
                    f"Function has {param_count} parameters. "
                    "Consider using a configuration object or breaking into smaller functions."
                )

        return suggestions


class QualityGate:
    """Quality gate for code changes."""

    def __init__(self, max_complexity: int = 10, max_lines: int = 50):
        """Initialize quality gate.

        Args:
            max_complexity: Maximum complexity score allowed
            max_lines: Maximum lines per function allowed
        """
        self.max_complexity = max_complexity
        self.max_lines = max_lines

    def check_quality(self, content: str, function_name: str = "") -> Dict[str, Any]:
        """Check if code meets quality standards.

        Args:
            content: Code content to check
            function_name: Name of the function

        Returns:
            Quality check results
        """
        analyzer = CodeQualityAnalyzer()
        metrics = analyzer.calculate_complexity_score(content)
        suggestions = analyzer.suggest_refactoring(content, function_name)

        # Check quality gates
        passes_complexity = metrics["complexity_count"] <= self.max_complexity
        passes_length = metrics["line_count"] <= self.max_lines

        quality_score = 100
        if not passes_complexity:
            quality_score -= 30
        if not passes_length:
            quality_score -= 20
        if suggestions:
            quality_score -= len(suggestions) * 10

        quality_score = max(0, quality_score)

        return {
            "passes_quality_gate": passes_complexity and passes_length and len(suggestions) <= 2,
            "quality_score": quality_score,
            "metrics": metrics,
            "suggestions": suggestions,
            "gates_passed": {
                "complexity": passes_complexity,
                "length": passes_length,
                "suggestions": len(suggestions) <= 2,
            },
        }


def extract_method(large_function_content: str, method_name: str) -> Dict[str, str]:
    """Extract method refactoring helper.

    Args:
        large_function_content: Content of large function to refactor
        method_name: Name for the extracted method

    Returns:
        Dictionary with original and extracted method content
    """
    lines = large_function_content.split("\n")

    # Simple heuristic: extract middle section
    total_lines = len(lines)
    if total_lines <= 10:
        return {"original": large_function_content, "extracted": ""}

    # Extract middle third as a new method
    start_idx = total_lines // 3
    end_idx = 2 * total_lines // 3

    extracted_lines = lines[start_idx:end_idx]

    # Create method signature
    extracted_method = f"def {method_name}(self):\n"
    extracted_method += '    """Extracted method for improved readability."""\n'

    for line in extracted_lines:
        extracted_method += "    " + line + "\n"

    # Modify original function
    remaining_lines = lines[:start_idx] + [f"    self.{method_name}()"] + lines[end_idx:]
    modified_original = "\n".join(remaining_lines)

    return {"original": modified_original, "extracted": extracted_method}


def performance_monitor(
    log_slow_operations: bool = True, threshold_seconds: float = 1.0
) -> Callable:
    """Decorator to monitor function performance.

    Args:
        log_slow_operations: Whether to log slow operations
        threshold_seconds: Threshold for considering operation slow

    Returns:
        Decorated function with performance monitoring
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            if log_slow_operations and execution_time > threshold_seconds:
                logger.warning(
                    f"Slow operation detected: {func.__name__} took {execution_time:.2f}s "
                    f"(threshold: {threshold_seconds}s)"
                )

            return result

        return wrapper

    return decorator


def readable_code_formatter(content: str) -> str:
    """Format code for better readability.

    Args:
        content: Code content to format

    Returns:
        Formatted code content
    """
    lines = content.split("\n")
    formatted_lines = []

    for line in lines:
        # Remove excessive whitespace
        clean_line = re.sub(r" +", " ", line.rstrip())

        # Add spacing around operators for readability
        clean_line = re.sub(r"([=!<>]+)", r" \1 ", clean_line)
        clean_line = re.sub(r" +", " ", clean_line)  # Clean up multiple spaces

        formatted_lines.append(clean_line)

    return "\n".join(formatted_lines)


class CodeStyleChecker:
    """Checks code style and conventions."""

    @staticmethod
    def check_naming_conventions(content: str) -> List[str]:
        """Check naming conventions.

        Args:
            content: Code content to check

        Returns:
            List of naming convention violations
        """
        violations = []

        # Check function names (should be snake_case)
        function_names = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)", content)
        for name in function_names:
            if not re.match(r"^[a-z_][a-z0-9_]*$", name):
                violations.append(f"Function '{name}' should use snake_case")

        # Check class names (should be PascalCase)
        class_names = re.findall(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)", content)
        for name in class_names:
            if not re.match(r"^[A-Z][a-zA-Z0-9]*$", name):
                violations.append(f"Class '{name}' should use PascalCase")

        # Check constants (should be UPPER_CASE)
        constant_assignments = re.findall(r"^([A-Z_][A-Z0-9_]*)\s*=", content, re.MULTILINE)
        for name in constant_assignments:
            if not re.match(r"^[A-Z_][A-Z0-9_]*$", name):
                violations.append(f"Constant '{name}' should use UPPER_CASE")

        return violations

    @staticmethod
    def check_documentation(content: str) -> List[str]:
        """Check documentation completeness.

        Args:
            content: Code content to check

        Returns:
            List of documentation issues
        """
        issues = []

        # Check for docstrings on functions
        functions = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\):", content)
        for func_name in functions:
            if not re.search(rf'def\s+{func_name}.*?:\s*"""', content, re.DOTALL):
                issues.append(f"Function '{func_name}' missing docstring")

        # Check for docstrings on classes
        classes = re.findall(r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)", content)
        for class_name in classes:
            if not re.search(rf'class\s+{class_name}.*?:\s*"""', content, re.DOTALL):
                issues.append(f"Class '{class_name}' missing docstring")

        return issues
