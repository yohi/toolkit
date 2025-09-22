"""Prompt templates for AI-powered analysis."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PromptTemplate(ABC):
    """Abstract base class for prompt templates."""

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt for the AI model."""
        pass

    @abstractmethod
    def create_prompt(self, **kwargs) -> str:
        """Create specific prompt from template."""
        pass


@dataclass
class CommentContext:
    """Context information for comment analysis."""

    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    language: Optional[str] = None
    diff_context: Optional[str] = None
    pr_title: Optional[str] = None
    pr_description: Optional[str] = None


class ClassificationPrompt(PromptTemplate):
    """Prompt template for comment classification."""

    def get_system_prompt(self) -> str:
        """Get system prompt for classification."""
        return """You are an expert code reviewer and AI assistant specialized in analyzing CodeRabbit review comments.

Your task is to classify review comments into categories and assign priority levels based on their content, technical impact, and urgency.

## Classification Categories:
- **security_critical**: Security vulnerabilities, injection risks, authentication issues
- **performance_issue**: Performance bottlenecks, memory leaks, inefficient algorithms
- **bug_potential**: Logic errors, null pointer risks, edge cases, incorrect implementations
- **code_quality**: Code structure, maintainability, design patterns, best practices
- **style_suggestion**: Formatting, naming conventions, code style preferences
- **documentation**: Missing or inadequate documentation, unclear comments
- **testing**: Test coverage, test quality, missing test cases
- **architecture**: System design, component structure, architectural concerns
- **nitpick**: Minor stylistic preferences, subjective improvements
- **positive_feedback**: Compliments, acknowledgments, positive observations
- **question**: Clarification requests, inquiries about implementation
- **unknown**: Unclear or ambiguous comments

## Priority Levels (1-5):
- **5 (CRITICAL)**: Security vulnerabilities, data loss risks, production failures
- **4 (HIGH)**: Performance issues, potential bugs, broken functionality
- **3 (MEDIUM)**: Code quality, architecture concerns, maintainability
- **2 (LOW)**: Style suggestions, documentation, minor improvements
- **1 (INFO)**: Positive feedback, questions, non-actionable comments

## Response Format:
Respond with a JSON object containing:
```json
{
  "category": "category_name",
  "priority": 1-5,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of classification decision",
  "keywords": ["key", "terms", "found"],
  "sentiment_score": -1.0 to 1.0 (optional),
  "actionable": true/false,
  "estimated_effort_hours": 0.5-8.0 (optional),
  "related_categories": ["other", "relevant", "categories"]
}
```

Be precise, consistent, and focus on technical impact and actionability."""

    def create_prompt(self, **kwargs) -> str:
        """Create classification prompt."""
        comment_text = kwargs.get("comment_text", "")
        context = kwargs.get("context", {})

        prompt = f"""Please classify the following CodeRabbit review comment:

**Comment Text:**
```
{comment_text}
```
"""

        # Add context if available
        if context:
            prompt += "\n**Context:**\n"
            if context.get("file_path"):
                prompt += f"- File: {context['file_path']}\n"
            if context.get("line_number"):
                prompt += f"- Line: {context['line_number']}\n"
            if context.get("function_name"):
                prompt += f"- Function: {context['function_name']}\n"
            if context.get("language"):
                prompt += f"- Language: {context['language']}\n"
            if context.get("diff_context"):
                prompt += f"- Diff Context:\n```\n{context['diff_context']}\n```\n"

        prompt += """
Analyze this comment and provide classification in the specified JSON format. Consider:
1. Technical impact and severity
2. Actionability and effort required
3. Context and code location
4. Urgency and business impact
"""

        return prompt

    def create_classification_prompt(self, comment_text: str, context: Dict[str, Any]) -> str:
        """Create classification prompt with context."""
        return self.create_prompt(comment_text=comment_text, context=context)

    def create_batch_classification_prompt(
        self, comments: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> str:
        """Create batch classification prompt."""
        prompt = """Please classify the following CodeRabbit review comments.
Return a JSON array with classification results for each comment in order.

**Comments to classify:**

"""

        for i, (comment_text, context) in enumerate(comments, 1):
            prompt += f"**Comment {i}:**\n```\n{comment_text}\n```\n"

            if context:
                prompt += "Context:\n"
                if context.get("file_path"):
                    prompt += f"- File: {context['file_path']}\n"
                if context.get("line_number"):
                    prompt += f"- Line: {context['line_number']}\n"

            prompt += "\n"

        prompt += """
Respond with a JSON array containing classification objects for each comment:
```json
[
  {
    "category": "category_name",
    "priority": 1-5,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "keywords": ["key", "terms"],
    "actionable": true/false
  },
  ...
]
```
"""

        return prompt


class AnalysisPrompt(PromptTemplate):
    """Prompt template for code analysis."""

    def get_system_prompt(self) -> str:
        """Get system prompt for code analysis."""
        return """You are an expert software engineer and security analyst.

Your task is to perform comprehensive code analysis including:
- Security vulnerability detection
- Performance bottleneck identification
- Code quality assessment
- Architecture and design evaluation
- Best practice compliance

Provide detailed, actionable feedback with specific recommendations for improvement."""

    def create_prompt(self, **kwargs) -> str:
        """Create analysis prompt."""
        code_snippet = kwargs.get("code_snippet", "")
        analysis_type = kwargs.get("analysis_type", "general")
        context = kwargs.get("context", {})

        prompt = f"""Please analyze the following code snippet:

**Code:**
```{context.get('language', '')}
{code_snippet}
```

**Analysis Type:** {analysis_type}
"""

        if context:
            prompt += "\n**Context:**\n"
            for key, value in context.items():
                if value:
                    prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

        if analysis_type == "security":
            prompt += """
Focus on security analysis:
1. Input validation and sanitization
2. Authentication and authorization
3. Data encryption and protection
4. Injection vulnerabilities (SQL, XSS, etc.)
5. Access control and permissions
6. Sensitive data handling
"""
        elif analysis_type == "performance":
            prompt += """
Focus on performance analysis:
1. Algorithm complexity and efficiency
2. Memory usage and leaks
3. Database query optimization
4. Caching opportunities
5. Resource utilization
6. Bottleneck identification
"""
        elif analysis_type == "quality":
            prompt += """
Focus on code quality analysis:
1. Code structure and organization
2. Design patterns and principles
3. Error handling and robustness
4. Maintainability and readability
5. Testing and testability
6. Documentation quality
"""

        prompt += """
Provide your analysis in JSON format:
```json
{
  "overall_score": 1-10,
  "issues": [
    {
      "type": "security|performance|quality|style",
      "severity": "critical|high|medium|low",
      "description": "Issue description",
      "line_number": 123,
      "recommendation": "Specific fix recommendation",
      "example": "Code example if helpful"
    }
  ],
  "strengths": ["Positive aspects found"],
  "recommendations": ["General improvement suggestions"],
  "estimated_fix_time": "Time estimate for all fixes"
}
```
"""

        return prompt


class SummaryPrompt(PromptTemplate):
    """Prompt template for generating summaries."""

    def get_system_prompt(self) -> str:
        """Get system prompt for summary generation."""
        return """You are an expert technical communicator specialized in creating clear, concise summaries of code reviews and analysis results.

Your summaries should be:
- Accurate and factual
- Well-structured and organized
- Actionable and prioritized
- Appropriate for the target audience (developers, managers, etc.)

Focus on key insights, critical issues, and clear next steps."""

    def create_prompt(self, **kwargs) -> str:
        """Create summary prompt."""
        content = kwargs.get("content", "")
        summary_type = kwargs.get("summary_type", "general")
        audience = kwargs.get("audience", "developers")
        max_length = kwargs.get("max_length", 500)

        prompt = f"""Please create a {summary_type} summary of the following content:

**Content to summarize:**
```
{content}
```

**Summary Requirements:**
- Target audience: {audience}
- Maximum length: {max_length} words
- Summary type: {summary_type}
"""

        if summary_type == "executive":
            prompt += """
- Focus on business impact and high-level outcomes
- Include metrics and quantifiable results
- Highlight critical issues and risks
- Provide clear recommendations
"""
        elif summary_type == "technical":
            prompt += """
- Focus on technical details and implementation
- Include specific code locations and files
- Explain technical concepts and solutions
- Provide actionable next steps
"""
        elif summary_type == "progress":
            prompt += """
- Focus on completed work and remaining tasks
- Include timeline and milestone updates
- Highlight blockers and dependencies
- Show progress metrics
"""

        prompt += """
Structure your summary with:
1. **Key Highlights** - Most important points
2. **Critical Issues** - Urgent items requiring attention
3. **Recommendations** - Specific action items
4. **Next Steps** - Clear follow-up actions

Provide the summary in markdown format."""

        return prompt


class SentimentPrompt(PromptTemplate):
    """Prompt template for sentiment analysis."""

    def get_system_prompt(self) -> str:
        """Get system prompt for sentiment analysis."""
        return """You are an expert in natural language processing and sentiment analysis, specialized in analyzing the emotional tone and sentiment of code review comments.

Your task is to analyze the sentiment, tone, and emotional context of review comments to help understand team dynamics and communication patterns.

Be objective and precise in your analysis."""

    def create_prompt(self, **kwargs) -> str:
        """Create sentiment analysis prompt."""
        text = kwargs.get("text", "")
        context = kwargs.get("context", {})

        prompt = f"""Please analyze the sentiment and emotional tone of this code review comment:

**Comment:**
```
{text}
```
"""

        if context:
            prompt += f"\n**Context:** {context}\n"

        prompt += """
Provide sentiment analysis in JSON format:
```json
{
  "sentiment_score": -1.0 to 1.0,
  "sentiment_label": "very_negative|negative|neutral|positive|very_positive",
  "confidence": 0.0 to 1.0,
  "emotions": {
    "frustration": 0.0-1.0,
    "satisfaction": 0.0-1.0,
    "concern": 0.0-1.0,
    "approval": 0.0-1.0,
    "confusion": 0.0-1.0
  },
  "tone": "professional|casual|critical|supportive|neutral",
  "constructiveness": 0.0-1.0,
  "reasoning": "Brief explanation of sentiment analysis"
}
```

Consider:
1. Word choice and phrasing
2. Constructiveness vs. criticism
3. Professional tone and language
4. Emotional indicators
5. Overall message intent
"""

        return prompt


class CodeSuggestionPrompt(PromptTemplate):
    """Prompt template for code suggestions."""

    def get_system_prompt(self) -> str:
        """Get system prompt for code suggestions."""
        return """You are an expert software engineer with deep knowledge across multiple programming languages, frameworks, and best practices.

Your task is to provide specific, actionable code suggestions and improvements based on review feedback and code analysis.

Your suggestions should be:
- Technically accurate and tested
- Following industry best practices
- Appropriate for the codebase context
- Well-documented with explanations"""

    def create_prompt(self, **kwargs) -> str:
        """Create code suggestion prompt."""
        original_code = kwargs.get("original_code", "")
        feedback = kwargs.get("feedback", "")
        language = kwargs.get("language", "")
        context = kwargs.get("context", {})

        prompt = f"""Please provide code suggestions based on the following:

**Original Code:**
```{language}
{original_code}
```

**Review Feedback:**
```
{feedback}
```
"""

        if context:
            prompt += "\n**Context:**\n"
            for key, value in context.items():
                if value:
                    prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

        prompt += """
Provide your suggestions in the following format:

```json
{
  "suggestions": [
    {
      "type": "fix|improvement|refactor|optimization",
      "description": "What this suggestion addresses",
      "original_lines": [1, 2, 3],
      "suggested_code": "New code implementation",
      "explanation": "Why this change is recommended",
      "benefits": ["List of benefits"],
      "potential_risks": ["Any potential issues"],
      "effort_estimate": "Time estimate for implementation"
    }
  ],
  "overall_assessment": "General evaluation of the code",
  "priority_order": [0, 1, 2],
  "additional_considerations": ["Other factors to consider"]
}
```

Focus on:
1. Addressing the specific feedback points
2. Following best practices for the language/framework
3. Maintaining code readability and maintainability
4. Ensuring performance and security considerations
5. Providing clear, implementable solutions
"""

        return prompt


# Factory function for creating prompt templates
def create_prompt_template(template_type: str) -> PromptTemplate:
    """Create prompt template based on type.

    Args:
        template_type: Type of prompt template

    Returns:
        Prompt template instance
    """
    template_map = {
        "classification": ClassificationPrompt,
        "analysis": AnalysisPrompt,
        "summary": SummaryPrompt,
        "sentiment": SentimentPrompt,
        "suggestion": CodeSuggestionPrompt,
    }

    template_class = template_map.get(template_type.lower())
    if not template_class:
        raise ValueError(f"Unknown template type: {template_type}")

    return template_class()


# Global template instances
_global_templates: Dict[str, PromptTemplate] = {}


def get_prompt_template(template_type: str) -> PromptTemplate:
    """Get or create prompt template.

    Args:
        template_type: Type of prompt template

    Returns:
        Prompt template instance
    """
    if template_type not in _global_templates:
        _global_templates[template_type] = create_prompt_template(template_type)

    return _global_templates[template_type]


def register_prompt_template(template_type: str, template: PromptTemplate) -> None:
    """Register custom prompt template.

    Args:
        template_type: Type identifier
        template: Template instance
    """
    _global_templates[template_type] = template
    logger.info(f"Registered custom prompt template: {template_type}")


# Template validation and testing utilities
def validate_prompt_template(template: PromptTemplate, test_data: Dict[str, Any]) -> bool:
    """Validate prompt template with test data.

    Args:
        template: Template to validate
        test_data: Test data for validation

    Returns:
        True if template is valid
    """
    try:
        # Test system prompt
        system_prompt = template.get_system_prompt()
        if not system_prompt or len(system_prompt.strip()) < 50:
            logger.warning("System prompt too short or empty")
            return False

        # Test prompt creation
        prompt = template.create_prompt(**test_data)
        if not prompt or len(prompt.strip()) < 10:
            logger.warning("Generated prompt too short or empty")
            return False

        # Check for template variables
        if "{" in prompt and "}" in prompt:
            logger.warning("Unresolved template variables found")
            return False

        return True

    except Exception as e:
        logger.error(f"Template validation failed: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    # Test classification template
    classifier = ClassificationPrompt()

    test_comment = "This function has a potential SQL injection vulnerability. The user input is not properly sanitized before being used in the database query."
    test_context = {"file_path": "src/auth/login.py", "line_number": 42, "language": "python"}

    prompt = classifier.create_classification_prompt(test_comment, test_context)
    print("Classification Prompt:")
    print(prompt)
    print("\n" + "=" * 50 + "\n")

    # Test analysis template
    analyzer = AnalysisPrompt()

    test_code = """
def login(username, password):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return db.execute(query)
"""

    analysis_prompt = analyzer.create_prompt(
        code_snippet=test_code,
        analysis_type="security",
        context={"language": "python", "function": "login"},
    )
    print("Analysis Prompt:")
    print(analysis_prompt)
