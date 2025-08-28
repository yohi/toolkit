"""Unit tests for formatter classes."""

import json
import pytest
from datetime import datetime

from coderabbit_fetcher.formatters import (
    BaseFormatter,
    MarkdownFormatter,
    JSONFormatter,
    PlainTextFormatter
)
from coderabbit_fetcher.models import (
    AnalyzedComments,
    SummaryComment,
    ReviewComment,
    ThreadContext,
    AIAgentPrompt,
    ActionableComment,
    NitpickComment,
    OutsideDiffComment,
    ResolutionStatus
)


class TestBaseFormatter:
    """Test cases for BaseFormatter abstract class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a concrete implementation for testing
        class ConcreteFormatter(BaseFormatter):
            def format(self, persona: str, analyzed_comments: AnalyzedComments) -> str:
                return f"Persona: {persona}\nComments: {len(analyzed_comments.summary_comments or [])}"
        
        self.formatter = ConcreteFormatter()
        
        # Sample data
        self.sample_prompt = AIAgentPrompt(
            description="Test AI prompt",
            file_path="test.py",
            line_range="10-15",
            code_block="def test():\n    pass"
        )
        
        self.sample_thread = ThreadContext(
            thread_id="test_thread_123",
            main_comment={"body": "Main comment"},
            replies=[{"body": "Reply 1"}],
            resolution_status=ResolutionStatus.UNRESOLVED,
            chronological_order=[{"body": "Comment 1"}],
            contextual_summary="Test thread summary",
            root_comment_id="123"
        )
    
    def test_format_ai_agent_prompt(self):
        """Test AI agent prompt formatting."""
        result = self.formatter.format_ai_agent_prompt(self.sample_prompt)
        
        assert "Test AI prompt" in result
        assert "test.py" in result
        assert "10-15" in result
        assert "def test():" in result
    
    def test_format_thread_context(self):
        """Test thread context formatting."""
        result = self.formatter.format_thread_context(self.sample_thread)
        
        assert "Thread Context" in result
        assert "UNRESOLVED" in result
        assert "Test thread summary" in result
    
    def test_format_actionable_comments(self):
        """Test actionable comments formatting."""
        comments = [
            ActionableComment(
                title="Fix security issue",
                description="Critical security vulnerability",
                file_path="security.py",
                line_number=42
            ),
            ActionableComment(
                title="Optimize performance",
                description="Improve algorithm efficiency",
                file_path="perf.py",
                line_number=100
            )
        ]
        
        result = self.formatter.format_actionable_comments(comments)
        
        assert "Fix security issue" in result
        assert "security.py" in result
        assert "Line 42" in result
        assert "Optimize performance" in result
    
    def test_format_nitpick_comments(self):
        """Test nitpick comments formatting."""
        comments = [
            NitpickComment(
                suggestion="Use consistent indentation",
                file_path="style.py",
                line_number=25
            )
        ]
        
        result = self.formatter.format_nitpick_comments(comments)
        
        assert "consistent indentation" in result
        assert "style.py" in result
        assert "Line 25" in result
    
    def test_format_outside_diff_comments(self):
        """Test outside diff comments formatting."""
        comments = [
            OutsideDiffComment(
                issue="Configuration issue",
                description="Invalid configuration detected",
                file_path="config.yaml",
                line_range="1-5"
            )
        ]
        
        result = self.formatter.format_outside_diff_comments(comments)
        
        assert "Configuration issue" in result
        assert "config.yaml" in result
        assert "Lines 1-5" in result
    
    def test_format_metadata(self):
        """Test metadata formatting."""
        analyzed_comments = AnalyzedComments(
            summary_comments=[SummaryComment(new_features=[], documentation_changes=[], test_changes=[], walkthrough="Test summary", changes_table=[], raw_content="Test summary")],
            review_comments=[],
            thread_contexts=[]
        )
        
        metadata = self.formatter.format_metadata(analyzed_comments)
        
        assert "timestamp" in metadata
        assert metadata["total_comments"] == 1
        assert metadata["summary_count"] == 1
        assert metadata["review_count"] == 0
        assert "ConcreteFormatter" in metadata["formatter_type"]
    
    def test_get_visual_markers(self):
        """Test visual markers retrieval."""
        markers = self.formatter.get_visual_markers()
        
        assert isinstance(markers, dict)
        assert "actionable" in markers
        assert "nitpick" in markers
        assert "ai_prompt" in markers
        assert markers["actionable"] == "🔥"
        assert markers["nitpick"] == "🧹"
    
    def test_sanitize_content(self):
        """Test content sanitization."""
        dirty_content = "Test\x00content\r\nwith\rbad\nchars"
        clean_content = self.formatter._sanitize_content(dirty_content)
        
        assert "\x00" not in clean_content
        assert "\r\n" not in clean_content
        assert "\r" not in clean_content
        assert clean_content == "Test\ncontent\nwith\nbad\nchars"
    
    def test_truncate_content(self):
        """Test content truncation."""
        long_content = "A" * 1000
        truncated = self.formatter._truncate_content(long_content, 50)
        
        assert len(truncated) == 50
        assert truncated.endswith("...")
        
        # Test no truncation needed
        short_content = "Short"
        not_truncated = self.formatter._truncate_content(short_content, 50)
        assert not_truncated == "Short"
    
    def test_extract_priority_level(self):
        """Test priority level extraction."""
        high_priority = self.formatter._extract_priority_level("Critical security vulnerability")
        assert high_priority == "High"
        
        medium_priority = self.formatter._extract_priority_level("Should improve performance")
        assert medium_priority == "Medium"
        
        low_priority = self.formatter._extract_priority_level("Minor style issue")
        assert low_priority == "Low"


class TestMarkdownFormatter:
    """Test cases for MarkdownFormatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = MarkdownFormatter()
        self.sample_persona = "You are a senior software engineer."
        
        self.sample_analyzed_comments = AnalyzedComments(
            summary_comments=[
                SummaryComment(
                    new_features=["Added new feature"],
                    documentation_changes=["Updated docs"],
                    test_changes=["Added tests"],
                    walkthrough="Test walkthrough",
                    changes_table=[],
                    raw_content="Test summary content"
                )
            ],
            review_comments=[
                ReviewComment(
                    actionable_comments=[
                        ActionableComment(
                            title="Fix bug",
                            description="Critical bug fix needed",
                            file_path="bug.py",
                            line_number=10
                        )
                    ],
                    nitpick_comments=[],
                    outside_diff_comments=[],
                    ai_agent_prompts=[],
                    raw_content="Raw comment content"
                )
            ],
            thread_contexts=[
                ThreadContext(thread_id="test_thread",
                    thread_id="test_thread_456",
                    main_comment={"body": "Main comment"},
                    replies=[],
                    resolution_status=ResolutionStatus.UNRESOLVED,
                    chronological_order=[{"body": "Thread comment"}],
                    contextual_summary="Thread summary",
                    root_comment_id="456"
                )
            ]
        )
    
    def test_format_complete_document(self):
        """Test complete markdown document formatting."""
        result = self.formatter.format(self.sample_persona, self.sample_analyzed_comments)
        
        # Check document structure
        assert "# CodeRabbit Analysis Report" in result
        assert "## AI Assistant Persona" in result
        assert "## 📋 Table of Contents" in result
        assert "## 📊 Summary Analysis" in result
        assert "## 🔍 Detailed Review Comments" in result
        assert "## 💬 Thread Discussions" in result
        assert "## 📈 Report Metadata" in result
        
        # Check persona inclusion
        assert self.sample_persona in result
    
    def test_format_without_toc(self):
        """Test formatting without table of contents."""
        formatter = MarkdownFormatter(include_toc=False)
        result = formatter.format(self.sample_persona, self.sample_analyzed_comments)
        
        assert "## 📋 Table of Contents" not in result
        assert "# CodeRabbit Analysis Report" in result
    
    def test_format_without_metadata(self):
        """Test formatting without metadata section."""
        formatter = MarkdownFormatter(include_metadata=False)
        result = formatter.format(self.sample_persona, self.sample_analyzed_comments)
        
        assert "## 📈 Report Metadata" not in result
        assert "# CodeRabbit Analysis Report" in result
    
    def test_format_summary_section(self):
        """Test summary section formatting."""
        summary = SummaryComment(
            new_features=["Feature 1", "Feature 2"],
            documentation_changes=["Improvement 1"],
            test_changes=[],
            walkthrough="Test summary",
            changes_table=[],
            raw_content="Test summary"
        )
        
        result = self.formatter.format_summary_section(summary)
        
        assert "### Summary Overview" in result
        assert "Test summary" in result
        assert "Feature 1" in result
        assert "Improvement 1" in result
    
    def test_format_review_section(self):
        """Test review section formatting."""
        review = ReviewComment(
            actionable_comments=[
                ActionableComment(
                    title="Security fix",
                    description="Fix security vulnerability",
                    file_path="security.py",
                    line_number=42
                )
            ],
            nitpick_comments=[],
            outside_diff_comments=[],
            ai_agent_prompts=[],
            raw_content="Raw content here"
        )
        
        result = self.formatter.format_review_section(review)
        
        assert "🔥 Actionable Items" in result
        assert "Security fix" in result
        assert "security.py" in result
        assert "📄 View Raw Comment Content" in result
    
    def test_format_ai_agent_prompt_markdown(self):
        """Test AI agent prompt formatting in Markdown."""
        prompt = AIAgentPrompt(
            description="Fix the function",
            file_path="test.py",
            line_range="1-5",
            code_block="def fixed_function():\n    return True"
        )
        
        result = self.formatter.format_ai_agent_prompt(prompt)
        
        assert "🤖 AI Agent Prompt" in result
        assert "Fix the function" in result
        assert "`test.py`" in result
        assert "```" in result
        assert "def fixed_function" in result
    
    def test_format_thread_section(self):
        """Test thread section formatting."""
        thread = ThreadContext(thread_id="test_thread",
            main_comment={"body": "Main comment"},
            replies=[{"body": "Reply"}],
            resolution_status=ResolutionStatus.RESOLVED,
            chronological_order=[
                {"body": "Comment 1"},
                {"body": "Comment 2"}
            ],
            contextual_summary="Thread about bug fix",
            root_comment_id="789"
        )
        
        result = self.formatter.format_thread_section(thread)
        
        assert "🧵 Thread:" in result
        assert "RESOLVED" in result
        assert "📝 Discussion Timeline" in result
        assert "Comment 1" in result
    
    def test_detect_language(self):
        """Test programming language detection."""
        # Python
        python_code = "def function():\n    import os"
        assert self.formatter._detect_language(python_code) == "python"
        
        # JavaScript
        js_code = "function test() {\n    const x = 1;"
        assert self.formatter._detect_language(js_code) == "javascript"
        
        # Java
        java_code = "public class Test {\n    private int x;"
        assert self.formatter._detect_language(java_code) == "java"
        
        # Unknown
        unknown_code = "some random text"
        assert self.formatter._detect_language(unknown_code) == ""
    
    def test_determine_comment_type(self):
        """Test comment type determination."""
        # AI prompt type
        ai_review = ReviewComment(
            actionable_comments=[],
            nitpick_comments=[],
            outside_diff_comments=[],
            ai_agent_prompts=[AIAgentPrompt(description="Test", file_path="", line_range="", code_block="")],
            raw_content=""
        )
        assert self.formatter._determine_comment_type(ai_review) == "ai_prompt"
        
        # Security type
        security_review = ReviewComment(
            actionable_comments=[ActionableComment(title="Security", description="security vulnerability", file_path="", line_number=1)],
            nitpick_comments=[],
            outside_diff_comments=[],
            ai_agent_prompts=[],
            raw_content=""
        )
        assert self.formatter._determine_comment_type(security_review) == "security"


class TestJSONFormatter:
    """Test cases for JSONFormatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = JSONFormatter(pretty_print=True)
        self.sample_persona = "You are a code reviewer."
        
        self.sample_analyzed_comments = AnalyzedComments(
            summary_comments=[
                SummaryComment(
                    new_features=["JSON feature"],
                    documentation_changes=["JSON improvement"],
                    test_changes=[],
                    walkthrough="JSON test summary",
                    changes_table=[],
                    raw_content="JSON test summary"
                )
            ],
            review_comments=[
                ReviewComment(
                    actionable_comments=[
                        ActionableComment(
                            title="JSON fix",
                            description="Fix JSON issue",
                            file_path="json.py",
                            line_number=5
                        )
                    ],
                    nitpick_comments=[],
                    outside_diff_comments=[],
                    ai_agent_prompts=[],
                    raw_content="JSON raw content"
                )
            ],
            thread_contexts=[]
        )
    
    def test_format_valid_json(self):
        """Test that formatter produces valid JSON."""
        result = self.formatter.format(self.sample_persona, self.sample_analyzed_comments)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        
        # Check top-level structure
        assert "metadata" in parsed
        assert "persona" in parsed
        assert "summary_comments" in parsed
        assert "review_comments" in parsed
        assert "thread_contexts" in parsed
    
    def test_format_pretty_vs_compact(self):
        """Test pretty print vs compact formatting."""
        pretty_formatter = JSONFormatter(pretty_print=True)
        compact_formatter = JSONFormatter(pretty_print=False)
        
        pretty_result = pretty_formatter.format(self.sample_persona, self.sample_analyzed_comments)
        compact_result = compact_formatter.format(self.sample_persona, self.sample_analyzed_comments)
        
        # Pretty should have indentation
        assert "  " in pretty_result
        
        # Compact should be shorter
        assert len(compact_result) < len(pretty_result)
        
        # Both should be valid JSON with same content
        assert json.loads(pretty_result) == json.loads(compact_result)
    
    def test_format_ai_agent_prompt_json(self):
        """Test AI agent prompt JSON formatting."""
        prompt = AIAgentPrompt(
            description="JSON test prompt",
            file_path="prompt.py",
            line_range="10-20",
            code_block="print('hello')"
        )
        
        result = self.formatter.format_ai_agent_prompt(prompt)
        
        assert result["type"] == "ai_agent_prompt"
        assert result["description"] == "JSON test prompt"
        assert result["file_path"] == "prompt.py"
        assert result["code_block"] == "print('hello')"
    
    def test_format_thread_context_json(self):
        """Test thread context JSON formatting."""
        thread = ThreadContext(thread_id="test_thread",
            main_comment={"body": "JSON thread main"},
            replies=[{"body": "JSON reply"}],
            resolution_status=ResolutionStatus.RESOLVED,
            chronological_order=[{"body": "JSON comment"}],
            contextual_summary="JSON thread summary",
            root_comment_id="json123"
        )
        
        result = self.formatter.format_thread_context(thread)
        
        assert result["root_comment_id"] == "json123"
        assert result["resolution_status"] == "RESOLVED"
        assert result["contextual_summary"] == "JSON thread summary"
        assert len(result["chronological_comments"]) == 1
    
    def test_include_raw_content_option(self):
        """Test include_raw_content option."""
        formatter_with_raw = JSONFormatter(include_raw_content=True)
        formatter_without_raw = JSONFormatter(include_raw_content=False)
        
        result_with = formatter_with_raw.format(self.sample_persona, self.sample_analyzed_comments)
        result_without = formatter_without_raw.format(self.sample_persona, self.sample_analyzed_comments)
        
        parsed_with = json.loads(result_with)
        parsed_without = json.loads(result_without)
        
        # With raw content should include it
        review_with = parsed_with["review_comments"][0]
        assert "raw_content" in review_with
        assert review_with["raw_content"] == "JSON raw content"
        
        # Without raw content should not include it
        review_without = parsed_without["review_comments"][0]
        assert "raw_content" not in review_without
    
    def test_metadata_structure(self):
        """Test metadata structure in JSON output."""
        result = self.formatter.format(self.sample_persona, self.sample_analyzed_comments)
        parsed = json.loads(result)
        
        metadata = parsed["metadata"]
        assert "generated_at" in metadata
        assert "formatter_type" in metadata
        assert "statistics" in metadata
        assert "configuration" in metadata
        
        stats = metadata["statistics"]
        assert "total_comments" in stats
        assert "summary_count" in stats
        assert "review_count" in stats
        assert "thread_count" in stats
    
    def test_comment_categorization(self):
        """Test comment categorization in JSON."""
        # Test nitpick categorization
        assert self.formatter._categorize_nitpick("Fix formatting style") == "formatting"
        assert self.formatter._categorize_nitpick("Rename variable to be clearer") == "naming"
        assert self.formatter._categorize_nitpick("Add documentation comment") == "documentation"
        assert self.formatter._categorize_nitpick("Remove unused import") == "cleanup"
        assert self.formatter._categorize_nitpick("General suggestion") == "general"
        
        # Test severity assessment
        assert self.formatter._assess_severity("Critical security issue") == "high"
        assert self.formatter._assess_severity("Warning about style") == "medium"
        assert self.formatter._assess_severity("Minor suggestion") == "low"


class TestPlainTextFormatter:
    """Test cases for PlainTextFormatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = PlainTextFormatter(line_width=60)
        self.sample_persona = "You are a plain text code reviewer."
        
        self.sample_analyzed_comments = AnalyzedComments(
            summary_comments=[
                SummaryComment(
                    new_features=["Text feature"],
                    documentation_changes=["Text improvement"],
                    test_changes=[],
                    walkthrough="Plain text summary",
                    changes_table=[],
                    raw_content="Plain text summary"
                )
            ],
            review_comments=[
                ReviewComment(
                    actionable_comments=[
                        ActionableComment(
                            title="Text fix",
                            description="Fix text issue",
                            file_path="text.py",
                            line_number=15
                        )
                    ],
                    nitpick_comments=[],
                    outside_diff_comments=[],
                    ai_agent_prompts=[],
                    raw_content="Text raw content"
                )
            ],
            thread_contexts=[]
        )
    
    def test_format_plain_text_structure(self):
        """Test plain text document structure."""
        result = self.formatter.format(self.sample_persona, self.sample_analyzed_comments)
        
        # Check main sections
        assert "CODERABBIT ANALYSIS REPORT" in result
        assert "AI ASSISTANT PERSONA" in result
        assert "SUMMARY ANALYSIS" in result
        assert "DETAILED REVIEW COMMENTS" in result
        assert "REPORT STATISTICS" in result
        
        # Check separators
        assert "=" * 60 in result  # Title separator
        assert "-" * 20 in result  # Section separators
    
    def test_format_without_separators(self):
        """Test formatting without separators."""
        formatter = PlainTextFormatter(include_separators=False)
        result = formatter.format(self.sample_persona, self.sample_analyzed_comments)
        
        # Should still have content but fewer separators
        assert "CODERABBIT ANALYSIS REPORT" in result
        assert "AI ASSISTANT PERSONA" in result
        # Main title separator should be reduced
        separator_count = result.count("=" * 60)
        assert separator_count <= 1  # At most the title separator
    
    def test_text_wrapping(self):
        """Test text wrapping functionality."""
        long_text = "This is a very long line that should be wrapped to fit within the specified line width for better readability."
        
        wrapped = self.formatter._wrap_text(long_text)
        lines = wrapped.split('\n')
        
        # Each line should be within the line width
        for line in lines:
            assert len(line) <= self.formatter.line_width
        
        # Should contain all original words
        original_words = long_text.split()
        wrapped_words = wrapped.replace('\n', ' ').split()
        assert original_words == wrapped_words
    
    def test_text_wrapping_with_indent(self):
        """Test text wrapping with indentation."""
        text = "Short text that should be indented properly when wrapped."
        
        wrapped = self.formatter._wrap_text(text, indent=4)
        lines = wrapped.split('\n')
        
        # Continuation lines should be indented
        if len(lines) > 1:
            for line in lines[1:]:
                assert line.startswith("    ")  # 4 spaces
    
    def test_format_persona_condensed(self):
        """Test condensed persona formatting."""
        # Long persona with role definition
        long_persona = """# Expert Persona
        
        You are an experienced software engineer with expertise in code review.
        Your role is to analyze CodeRabbit feedback and provide solutions.
        
        ## Instructions
        1. Analyze comments carefully
        2. Provide actionable feedback
        """
        
        condensed = self.formatter._format_persona_condensed(long_persona)
        
        # Should extract key role information
        assert "experienced software engineer" in condensed
        assert len(condensed) < len(long_persona)
    
    def test_format_actionable_comments_plain_text(self):
        """Test actionable comments in plain text format."""
        comments = [
            ActionableComment(
                title="High priority fix",
                description="Critical security vulnerability that needs immediate attention",
                file_path="security.py",
                line_number=42
            ),
            ActionableComment(
                title="Performance optimization", 
                description="Should improve algorithm efficiency",
                file_path="perf.py",
                line_number=100
            )
        ]
        
        result = self.formatter.format_actionable_comments(comments)
        
        # Check priority markers
        assert "[HIGH]" in result
        assert "[MED]" in result
        
        # Check content
        assert "High priority fix" in result
        assert "security.py" in result
        assert "Line 42" in result
    
    def test_extract_comment_content_safe(self):
        """Test safe comment content extraction."""
        # Test different comment formats
        comment_with_body = type('Comment', (), {'body': 'Test body'})()
        content = self.formatter._extract_comment_content_safe(comment_with_body)
        assert content == "Test body"
        
        comment_with_content = type('Comment', (), {'content': 'Test content'})()
        content = self.formatter._extract_comment_content_safe(comment_with_content)
        assert content == "Test content"
        
        string_comment = "String comment"
        content = self.formatter._extract_comment_content_safe(string_comment)
        assert content == "String comment"
        
        # Test error handling
        problematic_comment = type('Comment', (), {})()
        content = self.formatter._extract_comment_content_safe(problematic_comment)
        assert isinstance(content, str)  # Should return some string


class TestFormatterIntegration:
    """Integration tests for all formatters."""
    
    def setup_method(self):
        """Set up test fixtures for integration tests."""
        self.persona = "You are an integration test expert."
        
        # Comprehensive test data
        self.analyzed_comments = AnalyzedComments(
            summary_comments=[
                SummaryComment(
                    new_features=["Added new API endpoint", "Enhanced error handling"],
                    documentation_changes=["Optimized database queries", "Improved logging"],
                    test_changes=[],
                    walkthrough="Integration test summary with comprehensive data",
                    changes_table=[],
                    raw_content="Integration test summary with comprehensive data"
                )
            ],
            review_comments=[
                ReviewComment(
                    actionable_comments=[
                        ActionableComment(
                            title="Security vulnerability",
                            description="Critical SQL injection vulnerability",
                            file_path="api/users.py",
                            line_number=127
                        )
                    ],
                    nitpick_comments=[
                        NitpickComment(
                            suggestion="Use consistent naming convention",
                            file_path="models/user.py",
                            line_number=45
                        )
                    ],
                    outside_diff_comments=[
                        OutsideDiffComment(
                            issue="Configuration mismatch",
                            description="Database configuration inconsistent with environment",
                            file_path="config/database.yaml",
                            line_range="15-20"
                        )
                    ],
                    ai_agent_prompts=[
                        AIAgentPrompt(
                            description="Fix validation function",
                            file_path="utils/validators.py",
                            line_range="30-35",
                            code_block="def validate_email(email: str) -> bool:\n    import re\n    pattern = r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$'\n    return bool(re.match(pattern, email))"
                        )
                    ],
                    raw_content="This is the raw content of the review comment with all original formatting."
                )
            ],
            thread_contexts=[
                ThreadContext(thread_id="test_thread",
                    main_comment={"body": "Initial discussion about the security issue"},
                    replies=[
                        {"body": "I agree this needs immediate attention"},
                        {"body": "Let me fix this right away"}
                    ],
                    resolution_status=ResolutionStatus.IN_PROGRESS,
                    chronological_order=[
                        {"body": "Found a security vulnerability"},
                        {"body": "This looks serious"},
                        {"body": "Working on a fix now"}
                    ],
                    contextual_summary="Discussion thread about security vulnerability requiring immediate attention",
                    root_comment_id="integration_test_123"
                )
            ]
        )
    
    def test_all_formatters_produce_output(self):
        """Test that all formatters produce non-empty output."""
        formatters = [
            MarkdownFormatter(),
            JSONFormatter(),
            PlainTextFormatter()
        ]
        
        for formatter in formatters:
            result = formatter.format(self.persona, self.analyzed_comments)
            
            assert isinstance(result, str)
            assert len(result) > 100  # Should be substantial
            assert self.persona in result or "integration test expert" in result.lower()
    
    def test_cross_formatter_content_consistency(self):
        """Test that all formatters include essential content."""
        markdown_result = MarkdownFormatter().format(self.persona, self.analyzed_comments)
        json_result = JSONFormatter().format(self.persona, self.analyzed_comments)
        plain_result = PlainTextFormatter().format(self.persona, self.analyzed_comments)
        
        # Common content that should appear in all formats
        essential_content = [
            "Security vulnerability",
            "api/users.py",
            "Configuration mismatch",
            "validate_email",
            "IN_PROGRESS"
        ]
        
        for content in essential_content:
            assert content in markdown_result
            assert content in json_result
            assert content in plain_result
    
    def test_json_formatter_data_integrity(self):
        """Test JSON formatter preserves all data accurately."""
        result = JSONFormatter(include_raw_content=True).format(self.persona, self.analyzed_comments)
        parsed = json.loads(result)
        
        # Verify summary data
        summary = parsed["summary_comments"][0]
        assert summary["walkthrough"] == "Integration test summary with comprehensive data"
        assert len(summary["new_features"]) == 2
        assert len(summary["documentation_changes"]) == 2
        
        # Verify review data
        review = parsed["review_comments"][0]
        assert len(review["actionable_comments"]) == 1
        assert len(review["nitpick_comments"]) == 1
        assert len(review["outside_diff_comments"]) == 1
        assert len(review["ai_agent_prompts"]) == 1
        assert review["raw_content"] is not None
        
        # Verify AI prompt data
        ai_prompt = review["ai_agent_prompts"][0]
        assert ai_prompt["description"] == "Fix validation function"
        assert "validate_email" in ai_prompt["code_block"]
        
        # Verify thread data
        thread = parsed["thread_contexts"][0]
        assert thread["resolution_status"] == "IN_PROGRESS"
        assert len(thread["chronological_comments"]) == 3
    
    def test_formatter_performance(self):
        """Test formatter performance with reasonable execution time."""
        import time
        
        formatters = [
            MarkdownFormatter(),
            JSONFormatter(),
            PlainTextFormatter()
        ]
        
        for formatter in formatters:
            start_time = time.time()
            result = formatter.format(self.persona, self.analyzed_comments)
            end_time = time.time()
            
            # Should complete within reasonable time (1 second)
            execution_time = end_time - start_time
            assert execution_time < 1.0
            assert len(result) > 0
    
    def test_special_character_handling(self):
        """Test handling of special characters across all formatters."""
        # Create test data with special characters
        special_persona = "You are a reviewer with émojis 🔥 and spéciál cháracters"
        
        special_comments = AnalyzedComments(
            summary_comments=[
                SummaryComment(
                    new_features=["Féature with ñ"],
                    documentation_changes=["Improvement with émoji 💡"],
                    test_changes=[],
                    walkthrough="Tëst with spëcial characers: áéíóú ñ ü 中文 日本語 🚀",
                    changes_table=[],
                    raw_content="Tëst with spëcial characers: áéíóú ñ ü 中文 日本語 🚀"
                )
            ],
            review_comments=[],
            thread_contexts=[]
        )
        
        formatters = [
            MarkdownFormatter(),
            JSONFormatter(),
            PlainTextFormatter()
        ]
        
        for formatter in formatters:
            result = formatter.format(special_persona, special_comments)
            
            # Should handle special characters without errors
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Some special characters should be preserved
            if isinstance(formatter, JSONFormatter):
                # JSON should properly escape/encode
                parsed = json.loads(result)
                assert isinstance(parsed, dict)
            else:
                # Text formats should preserve readable characters
                assert "spëcial" in result or "special" in result
