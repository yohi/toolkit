"""Tests for CommentParser class."""

import unittest

from coderabbit_fetcher.models import ActionableComment, AIAgentPrompt
from coderabbit_fetcher.models.review_comment import NitpickComment, OutsideDiffComment
from coderabbit_fetcher.processors.comment_parser import CommentParser


class TestCommentParser(unittest.TestCase):
    """Test cases for CommentParser."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = CommentParser()

    def test_extract_actionable_comments_basic(self):
        """Test basic actionable comment extraction."""
        content = """
## 🛠️ Refactor Suggestions

**file.py:42** - Consider extracting this method
- Extract the validation logic into a separate method
- This would improve readability and testability
"""

        comments = self.parser.extract_actionable_comments(content)

        self.assertEqual(len(comments), 1)
        self.assertIsInstance(comments[0], ActionableComment)
        self.assertIn("Consider extracting", comments[0].description)

    def test_extract_actionable_comments_empty(self):
        """Test actionable comment extraction with empty content."""
        content = ""

        comments = self.parser.extract_actionable_comments(content)

        self.assertEqual(len(comments), 0)

    def test_extract_actionable_comments_multiple_sections(self):
        """Test extraction from multiple sections."""
        content = """
## 🛠️ Refactor Suggestions

**file1.py:10** - Refactor suggestion 1

## ⚠️ Potential Issues

**file2.py:20** - Potential issue found

## 📝 Committable Suggestions

**file3.py:30** - Committable suggestion
"""

        comments = self.parser.extract_actionable_comments(content)

        self.assertEqual(len(comments), 3)
        self.assertTrue(all(isinstance(c, ActionableComment) for c in comments))

    def test_extract_nitpick_comments_basic(self):
        """Test basic nitpick comment extraction."""
        content = """
## 🧹 Nitpick Comments

* Consider using more descriptive variable names
* Add type hints for better code clarity
"""

        comments = self.parser.extract_nitpick_comments(content)

        self.assertEqual(len(comments), 2)
        self.assertTrue(all(isinstance(c, NitpickComment) for c in comments))

    def test_extract_outside_diff_comments_basic(self):
        """Test outside diff comment extraction."""
        content = """
## ⚠️ Outside diff range comments

**config.py:1-10** - Configuration file needs update
* Update the database configuration
* Add new environment variables
"""

        comments = self.parser.extract_outside_diff_comments(content)

        self.assertEqual(len(comments), 2)
        self.assertTrue(all(isinstance(c, OutsideDiffComment) for c in comments))

    def test_extract_ai_agent_prompts_basic(self):
        """Test AI agent prompt extraction."""
        content = """
## 🤖 Prompt for AI Agents

```
Analyze the following code for security vulnerabilities:
- Check for SQL injection risks
- Validate input sanitization
```
"""

        prompts = self.parser.extract_ai_agent_prompts(content)

        self.assertEqual(len(prompts), 1)
        self.assertIsInstance(prompts[0], AIAgentPrompt)
        self.assertIn("security vulnerabilities", prompts[0].prompt_text)

    def test_extract_file_info_basic(self):
        """Test file information extraction."""
        content = "file.py:42 - Some comment about this line"

        file_info = self.parser._extract_file_info(content)

        self.assertEqual(file_info["path"], "file.py")
        self.assertEqual(file_info["line"], 42)

    def test_extract_file_info_with_range(self):
        """Test file information extraction with line range."""
        content = "config.yaml (lines 10-20) - Configuration update needed"

        file_info = self.parser._extract_file_info(content)

        self.assertEqual(file_info["path"], "config.yaml")
        self.assertEqual(file_info["line_range"], "10-20")

    def test_extract_description_basic(self):
        """Test description extraction."""
        content = (
            "**This is important** - Consider refactoring this method\nAdditional details here"
        )

        description = self.parser._extract_description(content)

        self.assertEqual(description, "This is important - Consider refactoring this method")

    def test_extract_suggestion_basic(self):
        """Test suggestion extraction."""
        content = """
Consider: Using a factory pattern here
Try: Implementing dependency injection
```python
class Factory:
    def create(self):
        return Product()
```
"""

        suggestion = self.parser._extract_suggestion(content)

        self.assertIn("Using a factory pattern", suggestion)

    def test_create_actionable_comment_success(self):
        """Test successful actionable comment creation."""
        content = "file.py:42 - **Security Issue** - Validate user input here"

        comment = self.parser._create_actionable_comment(content)

        self.assertIsNotNone(comment)
        self.assertIsInstance(comment, ActionableComment)
        self.assertEqual(comment.file_path, "file.py")
        self.assertEqual(comment.line_number, 42)

    def test_create_actionable_comment_no_description(self):
        """Test actionable comment creation with no description."""
        content = ""

        comment = self.parser._create_actionable_comment(content)

        self.assertIsNone(comment)

    def test_create_nitpick_comment_success(self):
        """Test successful nitpick comment creation."""
        content = "file.py:10 - Consider using better variable names"

        comment = self.parser._create_nitpick_comment(content)

        self.assertIsNotNone(comment)
        self.assertIsInstance(comment, NitpickComment)
        self.assertEqual(comment.file_path, "file.py")
        self.assertEqual(comment.line_number, 10)

    def test_create_outside_diff_comment_success(self):
        """Test successful outside diff comment creation."""
        content = "config.py (lines 1-5) - Update configuration settings"

        comment = self.parser._create_outside_diff_comment(content)

        self.assertIsNotNone(comment)
        self.assertIsInstance(comment, OutsideDiffComment)
        self.assertEqual(comment.file_path, "config.py")
        self.assertEqual(comment.line_range, "1-5")

    def test_create_ai_agent_prompt_success(self):
        """Test successful AI agent prompt creation."""
        content = """
```
Analyze this code for performance issues:
- Check for inefficient loops
- Identify memory leaks
```
"""

        prompt = self.parser._create_ai_agent_prompt(content)

        self.assertIsNotNone(prompt)
        self.assertIsInstance(prompt, AIAgentPrompt)
        self.assertIn("performance issues", prompt.prompt_text)

    def test_create_ai_agent_prompt_empty(self):
        """Test AI agent prompt creation with empty content."""
        content = "```\n\n```"

        prompt = self.parser._create_ai_agent_prompt(content)

        self.assertIsNone(prompt)

    def test_parse_actionable_section_multiple_comments(self):
        """Test parsing actionable section with multiple comments."""
        section_content = """
**file1.py:10** - First issue here
- Description of first issue

**file2.py:20** - Second issue here
- Description of second issue
"""

        comments = self.parser._parse_actionable_section(section_content)

        self.assertEqual(len(comments), 2)
        self.assertTrue(all(isinstance(c, ActionableComment) for c in comments))

    def test_parse_nitpick_section_bullet_points(self):
        """Test parsing nitpick section with bullet points."""
        section_content = """
* First nitpick comment
* Second nitpick comment
- Third nitpick comment
"""

        comments = self.parser._parse_nitpick_section(section_content)

        self.assertEqual(len(comments), 3)
        self.assertTrue(all(isinstance(c, NitpickComment) for c in comments))

    def test_parse_outside_diff_section_file_refs(self):
        """Test parsing outside diff section with file references."""
        section_content = """
config.py:1 - Configuration issue
database.sql:10-20 - Database schema update
"""

        comments = self.parser._parse_outside_diff_section(section_content)

        self.assertEqual(len(comments), 2)
        self.assertTrue(all(isinstance(c, OutsideDiffComment) for c in comments))

    def test_error_handling_in_extraction(self):
        """Test error handling during extraction."""
        # Test with malformed content
        malformed_content = "## 🛠️ Refactor Suggestions\n**unclosed markdown"

        # Should not raise exception and return empty list
        comments = self.parser.extract_actionable_comments(malformed_content)
        self.assertIsInstance(comments, list)

    def test_pattern_matching_case_insensitive(self):
        """Test that pattern matching is case insensitive."""
        content = """
## 🤖 prompt for ai agents

```
Test prompt content
```
"""

        prompts = self.parser.extract_ai_agent_prompts(content)

        self.assertEqual(len(prompts), 1)


if __name__ == "__main__":
    unittest.main()
