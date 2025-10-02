"""AI-powered comment classifier for CodeRabbit fetcher."""

import asyncio
import json
import logging
import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..patterns.observer import EventType, publish_event
from .llm_client import LLMClient, LLMResponse, get_llm_client
from .prompt_templates import ClassificationPrompt

logger = logging.getLogger(__name__)


class CommentCategory(Enum):
    """Comment category enumeration."""

    SECURITY_CRITICAL = "security_critical"
    PERFORMANCE_ISSUE = "performance_issue"
    BUG_POTENTIAL = "bug_potential"
    CODE_QUALITY = "code_quality"
    STYLE_SUGGESTION = "style_suggestion"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    NITPICK = "nitpick"
    POSITIVE_FEEDBACK = "positive_feedback"
    QUESTION = "question"
    UNKNOWN = "unknown"


class PriorityLevel(Enum):
    """Priority level enumeration."""

    CRITICAL = 5  # Security vulnerabilities, data loss risks
    HIGH = 4  # Performance issues, potential bugs
    MEDIUM = 3  # Code quality, architecture concerns
    LOW = 2  # Style, documentation
    INFO = 1  # Positive feedback, questions


@dataclass
class ClassificationResult:
    """Comment classification result."""

    category: CommentCategory
    priority: PriorityLevel
    confidence: float  # 0.0 to 1.0
    reasoning: str
    keywords: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    actionable: bool = True
    estimated_effort_hours: Optional[float] = None
    related_categories: List[CommentCategory] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "keywords": self.keywords,
            "sentiment_score": self.sentiment_score,
            "actionable": self.actionable,
            "estimated_effort_hours": self.estimated_effort_hours,
            "related_categories": [cat.value for cat in self.related_categories],
            "metadata": self.metadata,
        }


class AICommentClassifier:
    """AI-powered comment classifier using LLM."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        fallback_enabled: bool = True,
        batch_size: int = 5,
    ):
        """Initialize AI comment classifier.

        Args:
            llm_client: LLM client for AI classification
            fallback_enabled: Enable rule-based fallback
            batch_size: Batch size for processing multiple comments
        """
        self.llm_client = llm_client or get_llm_client()
        self.fallback_enabled = fallback_enabled
        self.batch_size = batch_size

        # Classification prompt template
        self.prompt_template = ClassificationPrompt()

        # Rule-based patterns for fallback
        self.security_patterns = [
            r"(?i)\b(security|vulnerability|exploit|attack|injection|xss|csrf|auth|password|secret|token)\b",
            r"(?i)\b(unsafe|dangerous|risk|threat|malicious)\b",
        ]

        self.performance_patterns = [
            r"(?i)\b(performance|slow|optimization|bottleneck|memory|cpu|cache|efficiency)\b",
            r"(?i)\b(n\+1|query|database|algorithm|complexity|timeout)\b",
        ]

        self.bug_patterns = [
            r"(?i)\b(bug|error|exception|crash|failure|broken|incorrect|wrong)\b",
            r"(?i)\b(null|undefined|missing|invalid|edge case)\b",
        ]

        # Statistics
        self._stats_lock = threading.Lock()
        self.stats = {
            "comments_classified": 0,
            "ai_classifications": 0,
            "fallback_classifications": 0,
            "batch_classifications": 0,
            "average_confidence": 0.0,
            "category_distribution": {},
            "priority_distribution": {},
        }

    async def classify_comment_async(
        self, comment_text: str, context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Classify a single comment asynchronously.

        Args:
            comment_text: Comment text to classify
            context: Optional context (file path, line number, etc.)

        Returns:
            Classification result
        """
        logger.debug(f"Classifying comment: {comment_text[:100]}...")

        try:
            # Try AI classification first
            if self.llm_client:
                result = await self._classify_with_ai(comment_text, context)
                if result:
                    with self._stats_lock:
                        self.stats["ai_classifications"] += 1
                    self._update_stats(result)
                    return result

            # Fallback to rule-based classification
            if self.fallback_enabled:
                result = self._classify_with_rules(comment_text, context)
                with self._stats_lock:
                    self.stats["fallback_classifications"] += 1
                self._update_stats(result)
                return result

            # Default classification
            result = ClassificationResult(
                category=CommentCategory.UNKNOWN,
                priority=PriorityLevel.MEDIUM,
                confidence=0.1,
                reasoning="No classification method available",
            )
            self._update_stats(result)
            return result

        except Exception:
            # 軽量だが追跡可能なログ
            logger.debug("Classification failed", exc_info=True)

            # Return safe default (error details from reasoning for debugging)
            return ClassificationResult(
                category=CommentCategory.UNKNOWN,
                priority=PriorityLevel.MEDIUM,
                confidence=0.0,
                reasoning=f"Classification error: {type(e).__name__}",
            )

    def classify_comment(
        self, comment_text: str, context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Classify a single comment synchronously.

        Args:
            comment_text: Comment text to classify
            context: Optional context

        Returns:
            Classification result
        """
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures

            # Run in executor to avoid creating new event loop
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = loop.run_in_executor(
                    ex,
                    lambda: asyncio.new_event_loop().run_until_complete(
                        self.classify_comment_async(comment_text, context)
                    ),
                )
                return loop.run_until_complete(fut)
        except RuntimeError:
            return asyncio.run(self.classify_comment_async(comment_text, context))

    async def classify_comments_batch_async(
        self, comments: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> List[ClassificationResult]:
        """Classify multiple comments in batches.

        Args:
            comments: List of (comment_text, context) tuples

        Returns:
            List of classification results
        """
        if not comments:
            return []

        logger.info(f"Classifying {len(comments)} comments in batches")

        results = []

        # Process in batches
        for i in range(0, len(comments), self.batch_size):
            batch = comments[i : i + self.batch_size]

            try:
                # Try batch AI classification
                if self.llm_client:
                    batch_results = await self._classify_batch_with_ai(batch)
                    if batch_results:
                        results.extend(batch_results)
                        with self._stats_lock:
                            self.stats["batch_classifications"] += 1
                        continue

                # Fallback to individual classification
                for comment_text, context in batch:
                    result = await self.classify_comment_async(comment_text, context)
                    results.append(result)

            except Exception:
                logger.exception("Error in batch classification")

                # Fallback to individual classification
                for comment_text, context in batch:
                    try:
                        result = await self.classify_comment_async(comment_text, context)
                        results.append(result)
                    except Exception:
                        logger.exception("Individual classification error")
                        results.append(
                            ClassificationResult(
                                category=CommentCategory.UNKNOWN,
                                priority=PriorityLevel.MEDIUM,
                                confidence=0.0,
                                reasoning=f"Error: {individual_error}",
                            )
                        )

        logger.info(f"Classified {len(results)} comments")
        return results

    async def _classify_with_ai(
        self, comment_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[ClassificationResult]:
        """Classify comment using AI/LLM."""
        if not self.llm_client:
            return None

        try:
            # Generate classification prompt
            prompt = self.prompt_template.create_classification_prompt(
                comment_text=comment_text, context=context or {}
            )

            system_prompt = self.prompt_template.get_system_prompt()

            # Get LLM response
            response = await self.llm_client.generate_async(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=500,
            )

            # Parse response
            result = self._parse_ai_response(response, comment_text)

            # Publish classification event
            publish_event(
                EventType.PROCESSING_COMPLETED,
                source="AICommentClassifier",
                data={
                    "method": "ai",
                    "category": result.category.value,
                    "priority": result.priority.value,
                    "confidence": result.confidence,
                    "response_time_ms": response.response_time_ms,
                },
            )

            return result

        except Exception as e:
            logger.error(f"AI classification error: {e}")

            # Publish error event
            publish_event(
                EventType.PROCESSING_FAILED,
                source="AICommentClassifier",
                data={"error": str(e), "method": "ai"},
                severity="error",
            )

            return None

    async def _classify_batch_with_ai(
        self, comments: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> Optional[List[ClassificationResult]]:
        """Classify multiple comments with AI in a single request."""
        if not self.llm_client or len(comments) > self.batch_size:
            return None

        try:
            # Generate batch classification prompt
            prompt = self.prompt_template.create_batch_classification_prompt(comments)
            system_prompt = self.prompt_template.get_system_prompt()

            # Get LLM response
            response = await self.llm_client.generate_async(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=1500,  # More tokens for batch processing
            )

            # Parse batch response
            results = self._parse_batch_ai_response(response, comments)

            return results

        except Exception:
            logger.exception("Batch AI classification error")
            return None

    def _parse_ai_response(self, response: LLMResponse, comment_text: str) -> ClassificationResult:
        """Parse AI response into classification result."""
        try:
            # Try to parse as JSON first
            if response.content.strip().startswith("{"):
                data = json.loads(response.content)

                return ClassificationResult(
                    category=CommentCategory(data.get("category", "unknown")),
                    priority=PriorityLevel(data.get("priority", 3)),
                    confidence=float(data.get("confidence", 0.5)),
                    reasoning=data.get("reasoning", ""),
                    keywords=data.get("keywords", []),
                    sentiment_score=data.get("sentiment_score"),
                    actionable=data.get("actionable", True),
                    estimated_effort_hours=data.get("estimated_effort_hours"),
                    related_categories=[
                        CommentCategory(cat) for cat in data.get("related_categories", [])
                    ],
                )

            # Fallback to text parsing
            return self._parse_text_response(response.content, comment_text)

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")

            # Return basic classification based on keywords
            return self._classify_with_rules(comment_text)

    def _parse_batch_ai_response(
        self, response: LLMResponse, comments: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> List[ClassificationResult]:
        """Parse batch AI response."""
        try:
            # Try to parse as JSON array
            if response.content.strip().startswith("["):
                data_list = json.loads(response.content)

                results = []
                for i, data in enumerate(data_list):
                    if i < len(comments):
                        result = ClassificationResult(
                            category=CommentCategory(data.get("category", "unknown")),
                            priority=PriorityLevel(data.get("priority", 3)),
                            confidence=float(data.get("confidence", 0.5)),
                            reasoning=data.get("reasoning", ""),
                            keywords=data.get("keywords", []),
                            sentiment_score=data.get("sentiment_score"),
                            actionable=data.get("actionable", True),
                            estimated_effort_hours=data.get("estimated_effort_hours"),
                        )
                        results.append(result)

                return results

            # Fallback to individual parsing
            return []

        except Exception:
            logger.exception("Error parsing batch AI response")
            return []

    def _parse_text_response(self, text: str, comment_text: str) -> ClassificationResult:
        """Parse text response from AI."""
        # Extract category
        category = CommentCategory.UNKNOWN
        for cat in CommentCategory:
            if cat.value.lower() in text.lower():
                category = cat
                break

        # Extract priority
        priority = PriorityLevel.MEDIUM
        if any(word in text.lower() for word in ["critical", "urgent", "severe"]):
            priority = PriorityLevel.CRITICAL
        elif any(word in text.lower() for word in ["high", "important"]):
            priority = PriorityLevel.HIGH
        elif any(word in text.lower() for word in ["low", "minor", "nitpick"]):
            priority = PriorityLevel.LOW

        # Extract confidence (look for percentages or confidence words)
        confidence = 0.5
        confidence_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if confidence_match:
            confidence = float(confidence_match.group(1)) / 100
        elif "high confidence" in text.lower():
            confidence = 0.8
        elif "low confidence" in text.lower():
            confidence = 0.3

        return ClassificationResult(
            category=category,
            priority=priority,
            confidence=confidence,
            reasoning=text[:200] + "..." if len(text) > 200 else text,
        )

    def _classify_with_rules(
        self, comment_text: str, context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """Classify comment using rule-based approach."""
        text_lower = comment_text.lower()

        # Check security patterns
        for pattern in self.security_patterns:
            if re.search(pattern, comment_text):
                return ClassificationResult(
                    category=CommentCategory.SECURITY_CRITICAL,
                    priority=PriorityLevel.CRITICAL,
                    confidence=0.7,
                    reasoning="Matched security-related keywords",
                    keywords=self._extract_keywords(comment_text, pattern),
                )

        # Check performance patterns
        for pattern in self.performance_patterns:
            if re.search(pattern, comment_text):
                return ClassificationResult(
                    category=CommentCategory.PERFORMANCE_ISSUE,
                    priority=PriorityLevel.HIGH,
                    confidence=0.6,
                    reasoning="Matched performance-related keywords",
                    keywords=self._extract_keywords(comment_text, pattern),
                )

        # Check bug patterns
        for pattern in self.bug_patterns:
            if re.search(pattern, comment_text):
                return ClassificationResult(
                    category=CommentCategory.BUG_POTENTIAL,
                    priority=PriorityLevel.HIGH,
                    confidence=0.6,
                    reasoning="Matched bug-related keywords",
                    keywords=self._extract_keywords(comment_text, pattern),
                )

        # Check for positive feedback
        if any(word in text_lower for word in ["good", "great", "excellent", "nice", "well done"]):
            return ClassificationResult(
                category=CommentCategory.POSITIVE_FEEDBACK,
                priority=PriorityLevel.INFO,
                confidence=0.5,
                reasoning="Contains positive feedback",
            )

        # Check for questions
        if "?" in comment_text or any(
            word in text_lower for word in ["why", "how", "what", "when", "where"]
        ):
            return ClassificationResult(
                category=CommentCategory.QUESTION,
                priority=PriorityLevel.LOW,
                confidence=0.5,
                reasoning="Contains question",
            )

        # Default to code quality
        return ClassificationResult(
            category=CommentCategory.CODE_QUALITY,
            priority=PriorityLevel.MEDIUM,
            confidence=0.3,
            reasoning="Default classification based on rules",
        )

    def _extract_keywords(self, text: str, pattern: str) -> List[str]:
        """Extract keywords matching the pattern."""
        matches = re.findall(pattern, text, re.IGNORECASE)
        return sorted(set(matches)) if matches else []

    def _update_stats(self, result: ClassificationResult) -> None:
        """Update classification statistics."""
        with self._stats_lock:
            self.stats["comments_classified"] += 1

            # Update confidence average
            total_confidence = (
                self.stats["average_confidence"] * (self.stats["comments_classified"] - 1)
                + result.confidence
            ) / self.stats["comments_classified"]
            self.stats["average_confidence"] = total_confidence

            # Update category distribution
            category = result.category.value
            self.stats["category_distribution"][category] = (
                self.stats["category_distribution"].get(category, 0) + 1
            )

            # Update priority distribution
            priority = result.priority.value
            self.stats["priority_distribution"][priority] = (
                self.stats["priority_distribution"].get(priority, 0) + 1
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        with self._stats_lock:
            stats = self.stats.copy()

        # Calculate percentages
        if stats["comments_classified"] > 0:
            stats["ai_percentage"] = (
                stats["ai_classifications"] / stats["comments_classified"]
            ) * 100
            stats["fallback_percentage"] = (
                stats["fallback_classifications"] / stats["comments_classified"]
            ) * 100
        else:
            stats["ai_percentage"] = 0.0
            stats["fallback_percentage"] = 0.0

        return stats


# Global classifier instance
_global_classifier: Optional[AICommentClassifier] = None


def get_comment_classifier() -> Optional[AICommentClassifier]:
    """Get global comment classifier."""
    return _global_classifier


def set_comment_classifier(classifier: AICommentClassifier) -> None:
    """Set global comment classifier."""
    global _global_classifier
    _global_classifier = classifier
    logger.info("Set global AI comment classifier")


async def classify_comment(
    comment_text: str, context: Optional[Dict[str, Any]] = None
) -> Optional[ClassificationResult]:
    """Classify comment using global classifier.

    Args:
        comment_text: Comment text to classify
        context: Optional context

    Returns:
        Classification result or None if no global classifier
    """
    classifier = get_comment_classifier()
    if classifier:
        return await classifier.classify_comment_async(comment_text, context)
    return None
