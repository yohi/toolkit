"""AI integration module for CodeRabbit fetcher."""

from .llm_client import (
    LLMClient,
    LLMResponse,
    LLMConfig,
    OpenAIClient,
    AnthropicClient,
    LocalLLMClient
)

from .comment_classifier import (
    AICommentClassifier,
    CommentCategory,
    ClassificationResult,
    PriorityLevel
)

from .sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentScore,
    EmotionAnalysis
)

from .code_analyzer import (
    AICodeAnalyzer,
    CodeQualityScore,
    SecurityAnalysis,
    PerformanceAnalysis
)

from .prompt_templates import (
    PromptTemplate,
    ClassificationPrompt,
    AnalysisPrompt,
    SummaryPrompt
)

__all__ = [
    # LLM Client
    "LLMClient",
    "LLMResponse",
    "LLMConfig",
    "OpenAIClient",
    "AnthropicClient",
    "LocalLLMClient",

    # Comment Classification
    "AICommentClassifier",
    "CommentCategory",
    "ClassificationResult",
    "PriorityLevel",

    # Sentiment Analysis
    "SentimentAnalyzer",
    "SentimentScore",
    "EmotionAnalysis",

    # Code Analysis
    "AICodeAnalyzer",
    "CodeQualityScore",
    "SecurityAnalysis",
    "PerformanceAnalysis",

    # Prompt Templates
    "PromptTemplate",
    "ClassificationPrompt",
    "AnalysisPrompt",
    "SummaryPrompt"
]
