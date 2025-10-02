"""Sentiment analysis for CodeRabbit comments."""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..patterns.observer import EventType, publish_event
from .llm_client import LLMClient, get_llm_client
from .prompt_templates import SentimentPrompt

logger = logging.getLogger(__name__)


class SentimentLabel(Enum):
    """Sentiment label enumeration."""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class ToneType(Enum):
    """Tone type enumeration."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    CRITICAL = "critical"
    SUPPORTIVE = "supportive"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ENCOURAGING = "encouraging"


@dataclass
class EmotionAnalysis:
    """Emotion analysis result."""

    frustration: float = 0.0  # 0.0 to 1.0
    satisfaction: float = 0.0  # 0.0 to 1.0
    concern: float = 0.0  # 0.0 to 1.0
    approval: float = 0.0  # 0.0 to 1.0
    confusion: float = 0.0  # 0.0 to 1.0
    enthusiasm: float = 0.0  # 0.0 to 1.0
    impatience: float = 0.0  # 0.0 to 1.0

    def get_dominant_emotion(self) -> Tuple[str, float]:
        """Get the dominant emotion and its score."""
        emotions = {
            "frustration": self.frustration,
            "satisfaction": self.satisfaction,
            "concern": self.concern,
            "approval": self.approval,
            "confusion": self.confusion,
            "enthusiasm": self.enthusiasm,
            "impatience": self.impatience,
        }

        dominant = max(emotions.items(), key=lambda x: x[1])
        return dominant

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "frustration": self.frustration,
            "satisfaction": self.satisfaction,
            "concern": self.concern,
            "approval": self.approval,
            "confusion": self.confusion,
            "enthusiasm": self.enthusiasm,
            "impatience": self.impatience,
        }


@dataclass
class SentimentScore:
    """Sentiment analysis result."""

    sentiment_score: float  # -1.0 to 1.0 (negative to positive)
    sentiment_label: SentimentLabel
    confidence: float  # 0.0 to 1.0
    emotions: EmotionAnalysis = field(default_factory=EmotionAnalysis)
    tone: ToneType = ToneType.NEUTRAL
    constructiveness: float = 0.5  # 0.0 to 1.0
    politeness: float = 0.5  # 0.0 to 1.0
    clarity: float = 0.5  # 0.0 to 1.0
    reasoning: str = ""
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_positive(self) -> bool:
        """Check if sentiment is positive."""
        return self.sentiment_score > 0.1

    def is_negative(self) -> bool:
        """Check if sentiment is negative."""
        return self.sentiment_score < -0.1

    def is_neutral(self) -> bool:
        """Check if sentiment is neutral."""
        return abs(self.sentiment_score) <= 0.1

    def is_constructive(self) -> bool:
        """Check if comment is constructive."""
        return self.constructiveness > 0.6

    def get_overall_quality(self) -> float:
        """Get overall communication quality score."""
        # Combine constructiveness, politeness, and clarity
        quality_score = self.constructiveness * 0.4 + self.politeness * 0.3 + self.clarity * 0.3
        return round(quality_score, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label.value,
            "confidence": self.confidence,
            "emotions": self.emotions.to_dict(),
            "tone": self.tone.value,
            "constructiveness": self.constructiveness,
            "politeness": self.politeness,
            "clarity": self.clarity,
            "reasoning": self.reasoning,
            "keywords": self.keywords,
            "overall_quality": self.get_overall_quality(),
            "metadata": self.metadata,
        }


class SentimentAnalyzer:
    """Sentiment analyzer for code review comments."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        fallback_enabled: bool = True,
        cache_enabled: bool = True,
    ):
        """Initialize sentiment analyzer.

        Args:
            llm_client: LLM client for AI analysis
            fallback_enabled: Enable rule-based fallback
            cache_enabled: Enable result caching
        """
        self.llm_client = llm_client or get_llm_client()
        self.fallback_enabled = fallback_enabled
        self.cache_enabled = cache_enabled

        # Prompt template
        self.prompt_template = SentimentPrompt()

        # Rule-based patterns for fallback
        self._init_sentiment_patterns()

        # Statistics
        self.stats = {
            "analyses_performed": 0,
            "ai_analyses": 0,
            "fallback_analyses": 0,
            "average_sentiment": 0.0,
            "average_constructiveness": 0.0,
            "sentiment_distribution": {},
            "tone_distribution": {},
            "emotion_totals": EmotionAnalysis().to_dict(),
        }

    def _init_sentiment_patterns(self) -> None:
        """Initialize sentiment analysis patterns."""
        # Positive patterns
        self.positive_patterns = [
            r"(?i)\b(great|excellent|good|nice|well done|perfect|awesome|fantastic|brilliant)\b",
            r"(?i)\b(love|like|appreciate|thanks|thank you|impressed|solid)\b",
            r"(?i)\b(clean|elegant|efficient|smart|clever|neat|beautiful)\b",
        ]

        # Negative patterns
        self.negative_patterns = [
            r"(?i)\b(bad|terrible|awful|horrible|wrong|broken|failed|error)\b",
            r"(?i)\b(hate|dislike|disappointed|frustrated|confused|annoyed)\b",
            r"(?i)\b(messy|ugly|inefficient|slow|bloated|convoluted)\b",
        ]

        # Constructive patterns
        self.constructive_patterns = [
            r"(?i)\b(suggest|recommend|consider|perhaps|maybe|could|might)\b",
            r"(?i)\b(improve|optimize|refactor|enhance|better|alternative)\b",
            r"(?i)\bwould be (better|good|nice|helpful)\b",
        ]

        # Critical patterns (potentially destructive)
        self.critical_patterns = [
            r"(?i)\b(must|should|need to|have to|required|mandatory)\b",
            r"(?i)\b(always|never|every time|completely|totally|absolutely)\b",
            r"(?i)\b(obviously|clearly|simple|just|simply|merely)\b",
        ]

        # Emotion patterns
        self.emotion_patterns = {
            "frustration": [
                r"(?i)\b(frustrated|annoyed|irritated|tired|sick of)\b",
                r"(?i)\bwhy (would|do|did|is|are)\b",
                r"(?i)\b(again|still|yet another|keep)\b",
            ],
            "concern": [
                r"(?i)\b(worried|concerned|afraid|scared|risky|dangerous)\b",
                r"(?i)\b(problem|issue|trouble|difficult|challenging)\b",
            ],
            "approval": [
                r"(?i)\b(approve|agree|correct|right|yes|exactly)\b",
                r"(?i)\b(looks good|sounds good|makes sense)\b",
            ],
            "confusion": [
                r"(?i)\b(confused|unclear|unsure|not sure|don\'t understand)\b",
                r"(?i)\b(what|why|how|when|where)\b.*\?",
            ],
            "enthusiasm": [
                r"(?i)\b(excited|enthusiastic|eager|looking forward)\b",
                r"(?i)!+\s*$",  # Exclamation marks at end
            ],
        }

    async def analyze_sentiment_async(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> SentimentScore:
        """Analyze sentiment asynchronously.

        Args:
            text: Text to analyze
            context: Optional context information

        Returns:
            Sentiment analysis result
        """
        logger.debug(f"Analyzing sentiment for text: {text[:100]}...")

        try:
            # Try AI analysis first
            if self.llm_client:
                result = await self._analyze_with_ai(text, context)
                if result:
                    self.stats["ai_analyses"] += 1
                    self._update_stats(result)
                    return result

            # Fallback to rule-based analysis
            if self.fallback_enabled:
                result = self._analyze_with_rules(text, context)
                self.stats["fallback_analyses"] += 1
                self._update_stats(result)
                return result

            # Default neutral result
            result = SentimentScore(
                sentiment_score=0.0,
                sentiment_label=SentimentLabel.NEUTRAL,
                confidence=0.1,
                reasoning="No analysis method available",
            )
            self._update_stats(result)
            return result

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")

            # Return safe default
            return SentimentScore(
                sentiment_score=0.0,
                sentiment_label=SentimentLabel.NEUTRAL,
                confidence=0.0,
                reasoning=f"Analysis error: {e}",
            )

    def analyze_sentiment(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> SentimentScore:
        """Analyze sentiment synchronously.

        Args:
            text: Text to analyze
            context: Optional context

        Returns:
            Sentiment analysis result
        
        Raises:
            RuntimeError: If called from within a running event loop.
                         Use analyze_sentiment_async() instead.
        """
        try:
            loop = asyncio.get_running_loop()
            # イベントループ内からの同期呼び出しは禁止
            raise RuntimeError(
                "analyze_sentiment() cannot be called from within a running event loop. "
                "Use analyze_sentiment_async() instead."
            )
        except RuntimeError as e:
            if "cannot be called" in str(e):
                raise
            # イベントループが存在しない正常ケース
            return asyncio.run(self.analyze_sentiment_async(text, context))

    async def analyze_batch_async(
        self, texts: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> List[SentimentScore]:
        """Analyze multiple texts asynchronously.

        Args:
            texts: List of (text, context) tuples

        Returns:
            List of sentiment analysis results
        """
        if not texts:
            return []

        logger.info(f"Analyzing sentiment for {len(texts)} texts")

        # Process concurrently
        tasks = [self.analyze_sentiment_async(text, context) for text, context in texts]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing text {i}: {result}")
                final_results.append(
                    SentimentScore(
                        sentiment_score=0.0,
                        sentiment_label=SentimentLabel.NEUTRAL,
                        confidence=0.0,
                        reasoning=f"Error: {result}",
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def _analyze_with_ai(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[SentimentScore]:
        """Analyze sentiment using AI/LLM."""
        if not self.llm_client:
            return None

        try:
            # Generate sentiment analysis prompt
            prompt = self.prompt_template.create_prompt(text=text, context=context or {})

            system_prompt = self.prompt_template.get_system_prompt()

            # Get LLM response
            response = await self.llm_client.generate_async(
                prompt=prompt, system_prompt=system_prompt, temperature=0.1, max_tokens=400
            )

            # Parse response
            result = self._parse_ai_response(response, text)

            # Publish analysis event
            publish_event(
                EventType.PROCESSING_COMPLETED,
                source="SentimentAnalyzer",
                data={
                    "method": "ai",
                    "sentiment_score": result.sentiment_score,
                    "sentiment_label": result.sentiment_label.value,
                    "confidence": result.confidence,
                    "response_time_ms": response.response_time_ms,
                },
            )

            return result

        except Exception as e:
            logger.error(f"AI sentiment analysis error: {e}")

            # Publish error event
            publish_event(
                EventType.PROCESSING_FAILED,
                source="SentimentAnalyzer",
                data={"error": str(e), "method": "ai"},
                severity="error",
            )

            return None

    def _parse_ai_response(self, response, text: str) -> SentimentScore:
        """Parse AI response into sentiment score."""
        try:
            # Try to parse as JSON
            if response.content.strip().startswith("{"):
                data = json.loads(response.content)

                # Parse emotions
                emotions_data = data.get("emotions", {})
                emotions = EmotionAnalysis(
                    frustration=emotions_data.get("frustration", 0.0),
                    satisfaction=emotions_data.get("satisfaction", 0.0),
                    concern=emotions_data.get("concern", 0.0),
                    approval=emotions_data.get("approval", 0.0),
                    confusion=emotions_data.get("confusion", 0.0),
                    enthusiasm=emotions_data.get("enthusiasm", 0.0),
                    impatience=emotions_data.get("impatience", 0.0),
                )

                return SentimentScore(
                    sentiment_score=float(data.get("sentiment_score", 0.0)),
                    sentiment_label=SentimentLabel(data.get("sentiment_label", "neutral")),
                    confidence=float(data.get("confidence", 0.5)),
                    emotions=emotions,
                    tone=ToneType(data.get("tone", "neutral")),
                    constructiveness=float(data.get("constructiveness", 0.5)),
                    politeness=float(data.get("politeness", 0.5)),
                    clarity=float(data.get("clarity", 0.5)),
                    reasoning=data.get("reasoning", ""),
                    keywords=data.get("keywords", []),
                )

            # Fallback to text parsing
            return self._parse_text_response(response.content, text)

        except Exception as e:
            logger.error(f"Error parsing AI sentiment response: {e}")

            # Return rule-based analysis as fallback
            return self._analyze_with_rules(text)

    def _parse_text_response(self, text: str, original_text: str) -> SentimentScore:
        """Parse text response from AI."""
        # Extract sentiment score
        sentiment_score = 0.0
        score_match = re.search(r"sentiment.*?(-?\d+\.\d+)", text, re.IGNORECASE)
        if score_match:
            sentiment_score = float(score_match.group(1))

        # Determine sentiment label
        if sentiment_score > 0.6:
            sentiment_label = SentimentLabel.VERY_POSITIVE
        elif sentiment_score > 0.1:
            sentiment_label = SentimentLabel.POSITIVE
        elif sentiment_score < -0.5:
            sentiment_label = SentimentLabel.VERY_NEGATIVE
        elif sentiment_score < -0.1:
            sentiment_label = SentimentLabel.NEGATIVE
        else:
            sentiment_label = SentimentLabel.NEUTRAL

        # Extract confidence
        confidence = 0.5
        confidence_match = re.search(r"confidence.*?(\d+\.\d+)", text, re.IGNORECASE)
        if confidence_match:
            confidence = float(confidence_match.group(1))

        return SentimentScore(
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=confidence,
            reasoning=text[:200] + "..." if len(text) > 200 else text,
        )

    def _analyze_with_rules(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> SentimentScore:
        """Analyze sentiment using rule-based approach."""
        text_lower = text.lower()

        # Calculate sentiment score
        positive_count = sum(1 for pattern in self.positive_patterns if re.search(pattern, text))
        negative_count = sum(1 for pattern in self.negative_patterns if re.search(pattern, text))

        # Base sentiment score
        sentiment_score = (positive_count - negative_count) / max(
            positive_count + negative_count, 1
        )

        # Adjust for text length and intensity
        if len(text.split()) < 5:  # Very short text
            sentiment_score *= 0.7

        # Check for exclamation marks (intensity)
        exclamation_count = text.count("!")
        if exclamation_count > 0:
            sentiment_score *= 1 + exclamation_count * 0.1

        # Determine sentiment label
        if sentiment_score > 0.6:
            sentiment_label = SentimentLabel.VERY_POSITIVE
        elif sentiment_score > 0.2:
            sentiment_label = SentimentLabel.POSITIVE
        elif sentiment_score < -0.6:
            sentiment_label = SentimentLabel.VERY_NEGATIVE
        elif sentiment_score < -0.2:
            sentiment_label = SentimentLabel.NEGATIVE
        else:
            sentiment_label = SentimentLabel.NEUTRAL

        # Analyze constructiveness
        constructive_count = sum(
            1 for pattern in self.constructive_patterns if re.search(pattern, text)
        )
        critical_count = sum(1 for pattern in self.critical_patterns if re.search(pattern, text))

        constructiveness = max(0.1, min(0.9, 0.5 + (constructive_count - critical_count) * 0.2))

        # Analyze emotions
        emotions = EmotionAnalysis()
        for emotion, patterns in self.emotion_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, text))
            if score > 0:
                setattr(emotions, emotion, min(1.0, score * 0.3))

        # Determine tone
        tone = ToneType.NEUTRAL
        if any(re.search(pattern, text) for pattern in self.critical_patterns):
            tone = ToneType.CRITICAL
        elif constructiveness > 0.7:
            tone = ToneType.SUPPORTIVE
        elif sentiment_score > 0.3:
            tone = ToneType.ENCOURAGING
        elif sentiment_score < -0.3:
            tone = ToneType.FRUSTRATED

        # Calculate politeness (simple heuristic)
        polite_words = ["please", "thanks", "thank you", "appreciate", "kindly"]
        politeness = 0.5
        for word in polite_words:
            if word in text_lower:
                politeness += 0.2
        politeness = min(1.0, politeness)

        # Calculate clarity (inverse of complexity)
        word_count = len(text.split())
        sentence_count = text.count(".") + text.count("!") + text.count("?") + 1
        avg_words_per_sentence = word_count / sentence_count
        clarity = max(0.1, min(1.0, 1.0 - (avg_words_per_sentence - 10) * 0.05))

        return SentimentScore(
            sentiment_score=round(sentiment_score, 2),
            sentiment_label=sentiment_label,
            confidence=0.6,  # Rule-based confidence
            emotions=emotions,
            tone=tone,
            constructiveness=round(constructiveness, 2),
            politeness=round(politeness, 2),
            clarity=round(clarity, 2),
            reasoning="Rule-based analysis",
            keywords=self._extract_sentiment_keywords(text),
        )

    def _extract_sentiment_keywords(self, text: str) -> List[str]:
        """Extract sentiment-related keywords from text."""
        keywords = []

        # Extract positive words
        for pattern in self.positive_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)

        # Extract negative words
        for pattern in self.negative_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)

        # Extract constructive words
        for pattern in self.constructive_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)

        return list({kw.lower() for kw in keywords if len(kw) > 2})

    def _update_stats(self, result: SentimentScore) -> None:
        """Update analysis statistics."""
        self.stats["analyses_performed"] += 1

        # Update averages
        total_analyses = self.stats["analyses_performed"]
        self.stats["average_sentiment"] = (
            self.stats["average_sentiment"] * (total_analyses - 1) + result.sentiment_score
        ) / total_analyses
        self.stats["average_constructiveness"] = (
            self.stats["average_constructiveness"] * (total_analyses - 1) + result.constructiveness
        ) / total_analyses

        # Update distributions
        sentiment_label = result.sentiment_label.value
        self.stats["sentiment_distribution"][sentiment_label] = (
            self.stats["sentiment_distribution"].get(sentiment_label, 0) + 1
        )

        tone = result.tone.value
        self.stats["tone_distribution"][tone] = self.stats["tone_distribution"].get(tone, 0) + 1

        # Update emotion totals
        emotions_dict = result.emotions.to_dict()
        for emotion, score in emotions_dict.items():
            self.stats["emotion_totals"][emotion] = (
                self.stats["emotion_totals"].get(emotion, 0.0) + score
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get analysis statistics."""
        stats = self.stats.copy()

        # Calculate percentages
        if stats["analyses_performed"] > 0:
            stats["ai_percentage"] = (stats["ai_analyses"] / stats["analyses_performed"]) * 100
            stats["fallback_percentage"] = (
                stats["fallback_analyses"] / stats["analyses_performed"]
            ) * 100
        else:
            stats["ai_percentage"] = 0.0
            stats["fallback_percentage"] = 0.0

        return stats

    def get_team_sentiment_summary(self, results: List[SentimentScore]) -> Dict[str, Any]:
        """Generate team sentiment summary from multiple results.

        Args:
            results: List of sentiment analysis results

        Returns:
            Team sentiment summary
        """
        if not results:
            return {}

        # Calculate overall metrics
        avg_sentiment = sum(r.sentiment_score for r in results) / len(results)
        avg_constructiveness = sum(r.constructiveness for r in results) / len(results)
        avg_politeness = sum(r.politeness for r in results) / len(results)
        avg_clarity = sum(r.clarity for r in results) / len(results)

        # Count sentiment distributions
        sentiment_counts: dict[str, int] = {}
        tone_counts: dict[str, int] = {}

        for result in results:
            sentiment_counts[result.sentiment_label.value] = (
                sentiment_counts.get(result.sentiment_label.value, 0) + 1
            )
            tone_counts[result.tone.value] = tone_counts.get(result.tone.value, 0) + 1

        # Calculate team health indicators
        positive_ratio = sum(1 for r in results if r.is_positive()) / len(results)
        constructive_ratio = sum(1 for r in results if r.is_constructive()) / len(results)

        return {
            "total_comments": len(results),
            "overall_sentiment": round(avg_sentiment, 2),
            "constructiveness": round(avg_constructiveness, 2),
            "politeness": round(avg_politeness, 2),
            "clarity": round(avg_clarity, 2),
            "positive_ratio": round(positive_ratio, 2),
            "constructive_ratio": round(constructive_ratio, 2),
            "sentiment_distribution": sentiment_counts,
            "tone_distribution": tone_counts,
            "team_health_score": round(
                (avg_sentiment + avg_constructiveness + avg_politeness) / 3, 2
            ),
        }


# Global analyzer instance
_global_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> Optional[SentimentAnalyzer]:
    """Get global sentiment analyzer."""
    return _global_analyzer


def set_sentiment_analyzer(analyzer: SentimentAnalyzer) -> None:
    """Set global sentiment analyzer."""
    global _global_analyzer
    _global_analyzer = analyzer
    logger.info("Set global sentiment analyzer")


async def analyze_sentiment(
    text: str, context: Optional[Dict[str, Any]] = None
) -> Optional[SentimentScore]:
    """Analyze sentiment using global analyzer.

    Args:
        text: Text to analyze
        context: Optional context

    Returns:
        Sentiment analysis result or None if no global analyzer
    """
    analyzer = get_sentiment_analyzer()
    if analyzer:
        return await analyzer.analyze_sentiment_async(text, context)
    return None
