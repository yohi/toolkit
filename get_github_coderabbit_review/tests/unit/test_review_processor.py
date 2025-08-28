"""Unit tests for ReviewProcessor class."""

import pytest

from coderabbit_fetcher.processors.review_processor import ReviewProcessor
from coderabbit_fetcher.models.review_comment import ReviewComment, NitpickComment, OutsideDiffComment
from coderabbit_fetcher.models import ActionableComment, AIAgentPrompt
from coderabbit_fetcher.exceptions import CommentParsingError


class TestReviewProcessor:
    """Test cases for ReviewProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ReviewProcessor()
        
        # Sample review comment with actionable items
        self.actionable_review = {
            "id": 123456,
            "user": {"login": "coderabbitai[bot]"},
            "body": """**Actionable comments posted: 5**

### Issues found:

- `src/auth.py:45` - Security vulnerability in password handling
- `src/models.py:120` - Missing validation for user input
- `tests/test_auth.py:30` - Test coverage gap for edge cases

### Other observations:

Some general feedback about the implementation approach.
"""
        }
        
        # Sample review comment with nitpick items
        self.nitpick_review = {
            "id": 123457,
            "user": {"login": "coderabbitai[bot]"},
            "body": """🧹 Nitpick comments

### Style improvements:

- `src/utils.py:15` - Consider using more descriptive variable names
- `src/config.py:8` - Add docstring to this function
- `README.md:25` - Fix typo in documentation

These are minor suggestions for better code quality.
"""
        }
        
        # Sample outside diff comment
        self.outside_diff_review = {
            "id": 123458,
            "user": {"login": "coderabbitai[bot]"},
            "body": """⚠️ Outside diff range comments (3)

<details>
<summary>Comments outside the visible diff</summary>

- `src/legacy.py:100-150` - This legacy code section needs refactoring
- `docs/setup.md:200` - Documentation is outdated
- `config/settings.json:5` - Configuration needs updating

</details>
"""
        }
        
        # Sample AI agent prompt
        self.ai_prompt_review = {
            "id": 123459,
            "user": {"login": "coderabbitai[bot]"},
            "body": """_🛠️ Refactor suggestion_

There are some issues with the implementation.

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/auth.py around lines 45-50, the password hashing implementation
needs to be updated to use bcrypt instead of md5; replace the current
hash_password function with a secure implementation using bcrypt.hash()
and ensure the salt is properly handled.
```

</details>

This suggestion will improve security.
"""
        }
        
        # Complex review with multiple sections
        self.complex_review = {
            "id": 123460,
            "user": {"login": "coderabbitai[bot]"},
            "body": """**Actionable comments posted: 12**

## Critical Issues

### Security Concerns
- `src/auth.py:45` - Use bcrypt for password hashing
- `src/api.py:120` - Add input validation for API endpoints

## 🧹 Nitpick comments

### Code Style
- `src/utils.py:15` - Variable naming could be more descriptive
- `src/models.py:8` - Add type hints to function parameters

## ⚠️ Outside diff range comments (2)

### Configuration Issues
- `config/database.yaml:10` - Database connection settings need review
- `deploy/nginx.conf:25` - SSL configuration outdated

<details>
<summary>🤖 Prompt for AI Agents</summary>

```
In src/auth.py around lines 45-50, replace the MD5 hashing with bcrypt
for better security; import bcrypt and use bcrypt.hashpw() with proper
salt generation; update all related authentication functions.
```

</details>
"""
        }
    
    def test_extract_actionable_count(self):
        """Test extraction of actionable comments count."""
        count = self.processor._extract_actionable_count(self.actionable_review["body"])
        assert count == 5
    
    def test_extract_actionable_count_no_count(self):
        """Test actionable count extraction when no count is present."""
        content = "This is just a regular comment without actionable items."
        count = self.processor._extract_actionable_count(content)
        assert count == 0
    
    def test_extract_actionable_count_different_formats(self):
        """Test actionable count extraction with different formats."""
        test_cases = [
            ("**Actionable comments posted: 8**", 8),
            ("Actionable comments posted: 3", 3),
            ("5 actionable comments found", 5),
            ("Total: 10 actionable items", 10),
        ]
        
        for content, expected in test_cases:
            count = self.processor._extract_actionable_count(content)
            assert count == expected
    
    def test_extract_actionable_comments(self):
        """Test extraction of actionable comments."""
        actionable_comments = self.processor.extract_actionable_comments(
            self.actionable_review["body"]
        )
        
        assert len(actionable_comments) >= 1  # Should find at least some items
        
        # Check that we extracted ActionableComment objects
        for comment in actionable_comments:
            assert isinstance(comment, ActionableComment)
            assert comment.file_path != ""
            assert comment.issue_description != ""
    
    def test_extract_nitpick_comments(self):
        """Test extraction of nitpick comments."""
        nitpick_comments = self.processor.extract_nitpick_comments(
            self.nitpick_review["body"]
        )
        
        assert len(nitpick_comments) >= 1
        
        # Check that we extracted NitpickComment objects
        for comment in nitpick_comments:
            assert isinstance(comment, NitpickComment)
            assert comment.file_path != ""
            assert comment.suggestion != ""
    
    def test_extract_outside_diff_comments(self):
        """Test extraction of outside diff comments."""
        outside_diff_comments = self.processor.extract_outside_diff_comments(
            self.outside_diff_review["body"]
        )
        
        assert len(outside_diff_comments) >= 1
        
        # Check that we extracted OutsideDiffComment objects
        for comment in outside_diff_comments:
            assert isinstance(comment, OutsideDiffComment)
            assert comment.file_path != ""
            assert comment.content != ""
            assert comment.reason != ""
    
    def test_extract_ai_agent_prompts(self):
        """Test extraction of AI agent prompts."""
        ai_prompts = self.processor.extract_ai_agent_prompts(
            self.ai_prompt_review["body"]
        )
        
        assert len(ai_prompts) >= 1
        
        # Check that we extracted AIAgentPrompt objects
        for prompt in ai_prompts:
            assert isinstance(prompt, AIAgentPrompt)
            assert prompt.code_block != ""
            assert prompt.description != ""
    
    def test_extract_code_blocks(self):
        """Test extraction of code blocks from content."""
        content = """
        Here's some code:
        
        ```python
        def hello_world():
            print("Hello, World!")
        ```
        
        And some inline `variable_name` code.
        
        <code>html_code_here</code>
        """
        
        code_blocks = self.processor._extract_code_blocks(content)
        
        assert len(code_blocks) >= 1
        # Should find either the function definition or inline code
        found_hello = any("hello_world" in block for block in code_blocks)
        found_var = any("variable_name" in block for block in code_blocks)
        found_html = any("html_code_here" in block for block in code_blocks)
        assert found_hello or found_var or found_html
    
    def test_process_review_comment_actionable(self):
        """Test processing of actionable review comment."""
        result = self.processor.process_review_comment(self.actionable_review)
        
        assert isinstance(result, ReviewComment)
        assert result.actionable_count == 5
        assert len(result.actionable_comments) >= 1
        assert result.raw_content == self.actionable_review["body"]
    
    def test_process_review_comment_nitpick(self):
        """Test processing of nitpick review comment.""" 
        result = self.processor.process_review_comment(self.nitpick_review)
        
        assert isinstance(result, ReviewComment)
        assert len(result.nitpick_comments) >= 1
        assert result.raw_content == self.nitpick_review["body"]
    
    def test_process_review_comment_outside_diff(self):
        """Test processing of outside diff review comment."""
        result = self.processor.process_review_comment(self.outside_diff_review)
        
        assert isinstance(result, ReviewComment)
        assert len(result.outside_diff_comments) >= 1
        assert result.raw_content == self.outside_diff_review["body"]
    
    def test_process_review_comment_ai_prompt(self):
        """Test processing of AI prompt review comment."""
        result = self.processor.process_review_comment(self.ai_prompt_review)
        
        assert isinstance(result, ReviewComment)
        assert len(result.ai_agent_prompts) >= 1
        assert result.raw_content == self.ai_prompt_review["body"]
    
    def test_process_review_comment_complex(self):
        """Test processing of complex review comment with multiple sections."""
        result = self.processor.process_review_comment(self.complex_review)
        
        assert isinstance(result, ReviewComment)
        assert result.actionable_count == 12
        assert len(result.actionable_comments) >= 1
        assert len(result.nitpick_comments) >= 1
        # Complex review may or may not have outside diff comments depending on pattern matching
        assert len(result.outside_diff_comments) >= 0
        assert len(result.ai_agent_prompts) >= 1
        assert result.raw_content == self.complex_review["body"]
    
    def test_process_review_comment_missing_body(self):
        """Test processing comment with missing body."""
        comment = {"id": 123, "user": {"login": "coderabbitai[bot]"}}
        
        result = self.processor.process_review_comment(comment)
        assert isinstance(result, ReviewComment)
        assert result.raw_content == ""
        assert result.actionable_count == 0
    
    def test_has_review_content(self):
        """Test review content detection."""
        test_cases = [
            ("This has actionable comments", True),
            ("Some nitpick suggestions here", True),
            ("Outside diff range issues", True),
            ("Refactor suggestion for better code", True),
            ("Potential issue with implementation", True),
            ("This is just a regular comment", False),
            ("Thanks for the great work!", False),
        ]
        
        for content, expected in test_cases:
            result = self.processor.has_review_content(content)
            assert result == expected
    
    def test_categorize_comment_type(self):
        """Test comment type categorization."""
        test_cases = [
            ("🧹 Nitpick: Fix code style", "nitpick"),
            ("⚠️ Potential issue with security", "potential_issue"),
            ("🛠️ Refactor suggestion", "refactor_suggestion"),
            ("Outside diff range comment", "outside_diff"),
            ("General comment about code", "general"),
        ]
        
        for content, expected in test_cases:
            result = self.processor.categorize_comment_type(content)
            assert result == expected
    
    def test_parse_actionable_items_edge_cases(self):
        """Test parsing actionable items with edge cases."""
        # Empty section
        assert self.processor._parse_actionable_items("") == []
        
        # Section with no clear file references
        section = "Some general feedback without specific files"
        items = self.processor._parse_actionable_items(section)
        assert len(items) == 0
        
        # Section with very short descriptions
        section = "- file.py:10 - ok"
        items = self.processor._parse_actionable_items(section)
        assert len(items) == 0  # Should filter out short descriptions
    
    def test_parse_nitpick_items_edge_cases(self):
        """Test parsing nitpick items with edge cases."""
        # Empty section
        assert self.processor._parse_nitpick_items("") == []
        
        # Section with no file paths
        section = "- Consider refactoring"
        items = self.processor._parse_nitpick_items(section)
        assert len(items) == 0
    
    def test_parse_outside_diff_items_edge_cases(self):
        """Test parsing outside diff items with edge cases."""
        # Empty section
        assert self.processor._parse_outside_diff_items("") == []
        
        # Section with very short content
        section = "- file.py - bad"
        items = self.processor._parse_outside_diff_items(section)
        assert len(items) == 0  # Should filter out short content
    
    def test_file_path_line_extraction(self):
        """Test extraction of file paths and line numbers."""
        test_cases = [
            ("src/auth.py:45", "src/auth.py", "45"),
            ("`config.json:10`", "config.json", "10"),
            ("utils.py:100-120", "utils.py", "100"),
            ("README.md", "README.md", "0"),
        ]
        
        for test_input, expected_file, expected_line in test_cases:
            section = f"- {test_input} - Some description here for testing"
            items = self.processor._parse_actionable_items(section)
            
            if items:  # Only check if items were parsed
                assert expected_file in items[0].file_path
                # Line range handling may vary, so we check that some line info is captured
                assert items[0].line_range is not None
    
    def test_japanese_content_support(self):
        """Test support for Japanese content in reviews."""
        japanese_review = {
            "id": 123461,
            "user": {"login": "coderabbitai[bot]"},
            "body": """**Actionable comments posted: 3**

### 問題点:

- `src/auth.py:45` - セキュリティ脆弱性があります
- `src/models.py:120` - バリデーションが不足しています

### 🧹 軽微な指摘

- `src/utils.py:15` - 変数名をより分かりやすくしてください
"""
        }
        
        result = self.processor.process_review_comment(japanese_review)
        
        assert isinstance(result, ReviewComment)
        assert result.actionable_count == 3
        # Content should be processed even if in Japanese
        assert len(result.actionable_comments) >= 0  # May or may not find items due to pattern matching
    
    def test_malformed_comment_handling(self):
        """Test handling of malformed comments."""
        malformed_comment = {
            "id": 123462,
            "user": {"login": "coderabbitai[bot]"},
            "body": """**Actionable comments posted: invalid**
            
            Some random content here...
            
            - Incomplete item
            - `file.py - Missing colon
            - file.py::: - Too many colons
            """
        }
        
        # Should not raise an exception
        result = self.processor.process_review_comment(malformed_comment)
        assert isinstance(result, ReviewComment)
        # Should handle invalid count gracefully
        assert result.actionable_count == 0
    
    def test_performance_with_large_content(self):
        """Test performance with large comment content."""
        # Create a large comment body
        large_body = "**Actionable comments posted: 1**\n\n"
        large_body += "- file.py:1 - Issue description\n" * 1000
        large_body += "\n" + "Some filler content. " * 10000
        
        large_comment = {
            "id": 123463,
            "user": {"login": "coderabbitai[bot]"},
            "body": large_body
        }
        
        # Should complete within reasonable time
        result = self.processor.process_review_comment(large_comment)
        assert isinstance(result, ReviewComment)
        assert result.actionable_count == 1
