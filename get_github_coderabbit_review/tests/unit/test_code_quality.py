"""Tests for code quality utilities."""

import time
import unittest
from unittest.mock import patch

from coderabbit_fetcher.utils.code_quality import (
    CodeQualityAnalyzer,
    CodeStyleChecker,
    QualityGate,
    complexity_reducer,
    extract_method,
    performance_monitor,
    readable_code_formatter,
    safe_execute,
    validate_input_types,
)


class TestCodeQualityAnalyzer(unittest.TestCase):
    """Test cases for CodeQualityAnalyzer."""

    def test_calculate_complexity_score_simple(self):
        """Test complexity calculation for simple code."""
        content = """
def simple_function():
    x = 1
    return x
"""

        result = CodeQualityAnalyzer.calculate_complexity_score(content)

        self.assertEqual(result["line_count"], 3)
        self.assertEqual(result["complexity_count"], 0)
        self.assertEqual(result["complexity_level"], "low")
        self.assertGreater(result["maintainability_score"], 90)

    def test_calculate_complexity_score_complex(self):
        """Test complexity calculation for complex code."""
        content = """
def complex_function(x, y):
    if x > 0:
        if y > 0:
            for i in range(x):
                while i < y:
                    try:
                        if i % 2 == 0 and i > 5:
                            return i
                    except Exception:
                        pass
    elif x < 0:
        return -1
    else:
        return 0
"""

        result = CodeQualityAnalyzer.calculate_complexity_score(content)

        self.assertGreater(result["complexity_count"], 5)
        self.assertEqual(result["complexity_level"], "high")
        self.assertLess(result["maintainability_score"], 50)

    def test_suggest_refactoring_long_function(self):
        """Test refactoring suggestions for long functions."""
        # Create content with 60 lines
        lines = [f"    line_{i} = {i}" for i in range(60)]
        content = "def long_function():\n" + "\n".join(lines)

        suggestions = CodeQualityAnalyzer.suggest_refactoring(content, "long_function")

        self.assertTrue(any("60 lines long" in s for s in suggestions))
        self.assertTrue(any("breaking it into smaller functions" in s for s in suggestions))

    def test_suggest_refactoring_high_nesting(self):
        """Test refactoring suggestions for high nesting."""
        content = """
def nested_function():
    if condition1:
        if condition2:
            if condition3:
                if condition4:
                    if condition5:
                        return True
"""

        suggestions = CodeQualityAnalyzer.suggest_refactoring(content, "nested_function")

        self.assertTrue(any("High nesting level" in s for s in suggestions))

    def test_suggest_refactoring_many_parameters(self):
        """Test refactoring suggestions for many parameters."""
        content = "def many_params(a, b, c, d, e, f, g, h):\n    pass"

        suggestions = CodeQualityAnalyzer.suggest_refactoring(content)

        self.assertTrue(any("8 parameters" in s for s in suggestions))

    def test_suggest_refactoring_duplicate_code(self):
        """Test refactoring suggestions for duplicate code."""
        content = """
def function_with_duplicates():
    some_long_line_of_code_that_repeats = 1
    some_long_line_of_code_that_repeats = 2
    some_long_line_of_code_that_repeats = 3
    other_code = 4
"""

        suggestions = CodeQualityAnalyzer.suggest_refactoring(content)

        self.assertTrue(any("Duplicate code patterns" in s for s in suggestions))


class TestQualityGate(unittest.TestCase):
    """Test cases for QualityGate."""

    def setUp(self):
        """Set up test fixtures."""
        self.quality_gate = QualityGate(max_complexity=5, max_lines=25)

    def test_check_quality_passes(self):
        """Test quality check that passes all gates."""
        content = """
def simple_function():
    x = 1
    y = 2
    return x + y
"""

        result = self.quality_gate.check_quality(content, "simple_function")

        self.assertTrue(result["passes_quality_gate"])
        self.assertGreater(result["quality_score"], 80)
        self.assertTrue(result["gates_passed"]["complexity"])
        self.assertTrue(result["gates_passed"]["length"])

    def test_check_quality_fails_complexity(self):
        """Test quality check that fails complexity gate."""
        content = """
def complex_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        if True:
                            return True
"""

        result = self.quality_gate.check_quality(content, "complex_function")

        self.assertFalse(result["gates_passed"]["complexity"])
        self.assertLess(result["quality_score"], 80)

    def test_check_quality_fails_length(self):
        """Test quality check that fails length gate."""
        # Create content with 30 lines
        lines = [f"    line_{i} = {i}" for i in range(30)]
        content = "def long_function():\n" + "\n".join(lines)

        result = self.quality_gate.check_quality(content, "long_function")

        self.assertFalse(result["gates_passed"]["length"])


class TestExtractMethod(unittest.TestCase):
    """Test cases for extract_method function."""

    def test_extract_method_basic(self):
        """Test basic method extraction."""
        large_function = """
def large_function():
    # Setup
    x = 1
    y = 2
    # Main logic
    result = x + y
    result *= 2
    # Cleanup
    return result
"""

        result = extract_method(large_function, "extracted_method")

        self.assertIn("def extracted_method", result["extracted"])
        self.assertIn("self.extracted_method()", result["original"])

    def test_extract_method_small_function(self):
        """Test method extraction on small function."""
        small_function = "def small():\n    return 1"

        result = extract_method(small_function, "extracted_method")

        self.assertEqual(result["extracted"], "")
        self.assertEqual(result["original"], small_function)


class TestReadableCodeFormatter(unittest.TestCase):
    """Test cases for readable_code_formatter function."""

    def test_format_spacing_around_operators(self):
        """Test formatting spacing around operators."""
        content = "x=1+2*3"

        formatted = readable_code_formatter(content)

        self.assertIn(" = ", formatted)
        self.assertIn(" + ", formatted)

    def test_format_remove_excessive_whitespace(self):
        """Test removing excessive whitespace."""
        content = "x   =    1     +    2"

        formatted = readable_code_formatter(content)

        self.assertNotIn("   ", formatted)  # No triple spaces
        self.assertIn(" = ", formatted)


class TestCodeStyleChecker(unittest.TestCase):
    """Test cases for CodeStyleChecker."""

    def test_check_naming_conventions_functions(self):
        """Test function naming convention checks."""
        content = """
def goodFunction():
    pass

def bad_function():
    pass

def BadFunction():
    pass
"""

        violations = CodeStyleChecker.check_naming_conventions(content)

        # Should flag goodFunction and BadFunction
        self.assertTrue(any("goodFunction" in v for v in violations))
        self.assertTrue(any("BadFunction" in v for v in violations))
        self.assertFalse(any("bad_function" in v for v in violations))

    def test_check_naming_conventions_classes(self):
        """Test class naming convention checks."""
        content = """
class GoodClass:
    pass

class badClass:
    pass

class bad_class:
    pass
"""

        violations = CodeStyleChecker.check_naming_conventions(content)

        # Should flag badClass and bad_class
        self.assertTrue(any("badClass" in v for v in violations))
        self.assertTrue(any("bad_class" in v for v in violations))
        self.assertFalse(any("GoodClass" in v for v in violations))

    def test_check_naming_conventions_constants(self):
        """Test constant naming convention checks."""
        content = """
GOOD_CONSTANT = 1
badConstant = 2
Bad_Constant = 3
"""

        violations = CodeStyleChecker.check_naming_conventions(content)

        # Should flag badConstant and Bad_Constant
        self.assertTrue(any("badConstant" in v for v in violations))
        self.assertTrue(any("Bad_Constant" in v for v in violations))

    def test_check_documentation_functions(self):
        """Test function documentation checks."""
        content = '''
def documented_function():
    """This function has documentation."""
    pass

def undocumented_function():
    pass
'''

        issues = CodeStyleChecker.check_documentation(content)

        self.assertTrue(any("undocumented_function" in i for i in issues))
        self.assertFalse(any("documented_function" in i for i in issues))

    def test_check_documentation_classes(self):
        """Test class documentation checks."""
        content = '''
class DocumentedClass:
    """This class has documentation."""
    pass

class UndocumentedClass:
    pass
'''

        issues = CodeStyleChecker.check_documentation(content)

        self.assertTrue(any("UndocumentedClass" in i for i in issues))
        self.assertFalse(any("DocumentedClass" in i for i in issues))


class TestDecorators(unittest.TestCase):
    """Test cases for quality decorators."""

    def test_complexity_reducer_decorator(self):
        """Test complexity reducer decorator."""

        @complexity_reducer(max_lines=10, max_params=3)
        def test_function(a, b, c, d):
            return a + b + c + d

        # Should work normally but log warning
        with patch("coderabbit_fetcher.utils.code_quality.logger") as mock_logger:
            result = test_function(1, 2, 3, 4)

            self.assertEqual(result, 10)
            mock_logger.warning.assert_called()

    def test_validate_input_types_decorator(self):
        """Test input type validation decorator."""

        @validate_input_types(name=str, age=int)
        def test_function(name=None, age=None):
            return f"{name} is {age} years old"

        # Valid types should work
        result = test_function(name="Alice", age=30)
        self.assertEqual(result, "Alice is 30 years old")

        # Invalid types should raise TypeError
        with self.assertRaises(TypeError):
            test_function(name=123, age=30)

    def test_safe_execute_decorator(self):
        """Test safe execute decorator."""

        @safe_execute(default_return="error", log_errors=True)
        def failing_function():
            raise ValueError("Test error")

        with patch("coderabbit_fetcher.utils.code_quality.logger") as mock_logger:
            result = failing_function()

            self.assertEqual(result, "error")
            mock_logger.error.assert_called()

    def test_performance_monitor_decorator(self):
        """Test performance monitor decorator."""

        @performance_monitor(threshold_seconds=0.1)
        def slow_function():
            time.sleep(0.2)
            return "done"

        with patch("coderabbit_fetcher.utils.code_quality.logger") as mock_logger:
            result = slow_function()

            self.assertEqual(result, "done")
            mock_logger.warning.assert_called()

    def test_performance_monitor_fast_function(self):
        """Test performance monitor with fast function."""

        @performance_monitor(threshold_seconds=1.0)
        def fast_function():
            return "done"

        with patch("coderabbit_fetcher.utils.code_quality.logger") as mock_logger:
            result = fast_function()

            self.assertEqual(result, "done")
            mock_logger.warning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
