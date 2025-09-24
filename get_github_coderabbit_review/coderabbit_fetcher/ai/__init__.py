"""AI integration module for CodeRabbit fetcher."""

from .code_analyzer import AICodeAnalyzer, CodeQualityScore, PerformanceAnalysis, SecurityAnalysis
from .comment_classifier import (
    AICommentClassifier,
    ClassificationResult,
    CommentCategory,
    PriorityLevel,
)
from .llm_client import (
    AnthropicClient,
    LLMClient,
    LLMConfig,
    LLMResponse,
    LocalLLMClient,
    OpenAIClient,
)
from .prompt_templates import AnalysisPrompt, ClassificationPrompt, PromptTemplate, SummaryPrompt
from .sentiment_analyzer import EmotionAnalysis, SentimentAnalyzer, SentimentScore

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
    "SummaryPrompt",
]
