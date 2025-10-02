"""Feature extraction for machine learning comment classification."""

import hashlib
import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TextFeatures:
    """Text-based features extracted from comments."""

    # Basic text metrics
    word_count: int = 0
    sentence_count: int = 0
    avg_word_length: float = 0.0
    char_count: int = 0
    line_count: int = 0

    # Linguistic features
    question_marks: int = 0
    exclamation_marks: int = 0
    capital_ratio: float = 0.0
    punctuation_ratio: float = 0.0

    # Code-related features
    code_snippets: int = 0
    code_blocks: int = 0
    inline_code: int = 0
    file_paths: int = 0
    urls: int = 0

    # Sentiment indicators
    positive_words: int = 0
    negative_words: int = 0
    technical_terms: int = 0

    # Readability metrics
    flesch_reading_ease: float = 0.0
    lexical_diversity: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to feature dictionary."""
        return {
            "word_count": float(self.word_count),
            "sentence_count": float(self.sentence_count),
            "avg_word_length": self.avg_word_length,
            "char_count": float(self.char_count),
            "line_count": float(self.line_count),
            "question_marks": float(self.question_marks),
            "exclamation_marks": float(self.exclamation_marks),
            "capital_ratio": self.capital_ratio,
            "punctuation_ratio": self.punctuation_ratio,
            "code_snippets": float(self.code_snippets),
            "code_blocks": float(self.code_blocks),
            "inline_code": float(self.inline_code),
            "file_paths": float(self.file_paths),
            "urls": float(self.urls),
            "positive_words": float(self.positive_words),
            "negative_words": float(self.negative_words),
            "technical_terms": float(self.technical_terms),
            "flesch_reading_ease": self.flesch_reading_ease,
            "lexical_diversity": self.lexical_diversity,
        }


@dataclass
class ContextFeatures:
    """Context-based features from comment metadata."""

    # File context
    is_in_test_file: bool = False
    is_in_config_file: bool = False
    is_in_documentation: bool = False
    file_extension: str = ""

    # Location context
    line_number: int = 0
    is_in_function: bool = False
    is_in_class: bool = False
    nesting_level: int = 0

    # PR context
    pr_size: int = 0  # lines changed
    files_changed: int = 0
    is_first_review: bool = True

    # Temporal features
    comment_position: int = 0  # position in review sequence
    time_since_pr: float = 0.0  # hours since PR creation

    def to_dict(self) -> Dict[str, float]:
        """Convert to feature dictionary."""
        return {
            "is_in_test_file": float(self.is_in_test_file),
            "is_in_config_file": float(self.is_in_config_file),
            "is_in_documentation": float(self.is_in_documentation),
            "file_extension_hash": float(
                int.from_bytes(
                    hashlib.blake2b(self.file_extension.encode("utf-8"), digest_size=2).digest(),
                    "big",
                )
                % 1000
            ),
            "line_number": float(self.line_number),
            "is_in_function": float(self.is_in_function),
            "is_in_class": float(self.is_in_class),
            "nesting_level": float(self.nesting_level),
            "pr_size": float(self.pr_size),
            "files_changed": float(self.files_changed),
            "is_first_review": float(self.is_first_review),
            "comment_position": float(self.comment_position),
            "time_since_pr": self.time_since_pr,
        }


@dataclass
class CommentFeatureSet:
    """Complete feature set for a comment."""

    text_features: TextFeatures
    context_features: ContextFeatures
    keyword_features: Dict[str, float] = field(default_factory=dict)
    pattern_features: Dict[str, float] = field(default_factory=dict)

    def to_vector(self) -> Dict[str, float]:
        """Convert to feature vector for ML models."""
        features = {}
        features.update(self.text_features.to_dict())
        features.update(self.context_features.to_dict())
        features.update(self.keyword_features)
        features.update(self.pattern_features)
        return features

    def get_feature_names(self) -> List[str]:
        """Get list of feature names."""
        return list(self.to_vector().keys())


class FeatureExtractor:
    """Feature extractor for comment classification."""

    def __init__(self) -> None:
        """Initialize feature extractor."""
        self._init_word_lists()
        self._init_patterns()

    def _init_word_lists(self) -> None:
        """Initialize word lists for feature extraction."""
        # Positive sentiment words
        self.positive_words = {
            "good",
            "great",
            "excellent",
            "nice",
            "perfect",
            "awesome",
            "fantastic",
            "brilliant",
            "clean",
            "elegant",
            "efficient",
            "smart",
            "clever",
            "neat",
            "beautiful",
            "love",
            "like",
            "appreciate",
            "thanks",
            "thank",
            "impressed",
            "solid",
        }

        # Negative sentiment words
        self.negative_words = {
            "bad",
            "terrible",
            "awful",
            "horrible",
            "wrong",
            "broken",
            "failed",
            "error",
            "hate",
            "dislike",
            "disappointed",
            "frustrated",
            "confused",
            "annoyed",
            "messy",
            "ugly",
            "inefficient",
            "slow",
            "bloated",
            "convoluted",
        }

        # Technical terms
        self.technical_terms = {
            "algorithm",
            "complexity",
            "performance",
            "optimization",
            "refactor",
            "architecture",
            "design",
            "pattern",
            "security",
            "vulnerability",
            "authentication",
            "authorization",
            "encryption",
            "database",
            "query",
            "api",
            "endpoint",
            "interface",
            "class",
            "method",
            "function",
            "variable",
            "parameter",
            "return",
            "exception",
            "error",
            "handling",
            "validation",
            "sanitization",
            "testing",
            "coverage",
            "mock",
            "stub",
            "integration",
            "deployment",
            "ci",
            "cd",
            "build",
            "compile",
            "debug",
        }

        # Severity indicators
        self.critical_words = {
            "critical",
            "urgent",
            "severe",
            "major",
            "blocker",
            "security",
            "vulnerability",
            "breach",
            "exploit",
        }

        self.minor_words = {
            "minor",
            "nitpick",
            "suggestion",
            "consider",
            "maybe",
            "optional",
            "style",
            "formatting",
            "cosmetic",
        }

    def _init_patterns(self) -> None:
        """Initialize regex patterns for feature extraction."""
        # Code patterns
        self.code_block_pattern = r"```[\s\S]*?```"
        self.inline_code_pattern = r"`[^`]+`"
        self.file_path_pattern = r"[a-zA-Z0-9_\-\.\/]+\.[a-zA-Z]{1,4}"
        self.url_pattern = r"https?://[^\s]+"

        # Sentiment patterns
        self.question_pattern = r"\?"
        self.exclamation_pattern = r"!"
        self.capital_letters_pattern = r"[A-Z]"
        self.punctuation_pattern = r"[^\w\s]"

        # Code review specific patterns
        self.suggestion_pattern = r"(?i)\b(suggest|recommend|consider|perhaps|maybe|could|might)\b"
        self.requirement_pattern = r"(?i)\b(must|should|need to|have to|required|mandatory)\b"
        self.issue_pattern = r"(?i)\b(issue|problem|bug|error|wrong|incorrect|broken)\b"
        self.improvement_pattern = r"(?i)\b(improve|optimize|enhance|better|refactor)\b"

        # Security patterns
        self.security_pattern = (
            r"(?i)\b(security|vulnerability|exploit|attack|injection|xss|csrf|auth)\b"
        )

        # Performance patterns
        self.performance_pattern = (
            r"(?i)\b(performance|slow|fast|optimization|bottleneck|memory|cpu|cache)\b"
        )

    def extract_features(
        self, comment_text: str, context: Optional[Dict[str, Any]] = None
    ) -> CommentFeatureSet:
        """Extract features from comment text and context.

        Args:
            comment_text: Comment text to analyze
            context: Optional context information

        Returns:
            Complete feature set
        """
        # Extract text features
        text_features = self._extract_text_features(comment_text)

        # Extract context features
        context_features = self._extract_context_features(context or {})

        # Extract keyword features
        keyword_features = self._extract_keyword_features(comment_text)

        # Extract pattern features
        pattern_features = self._extract_pattern_features(comment_text)

        return CommentFeatureSet(
            text_features=text_features,
            context_features=context_features,
            keyword_features=keyword_features,
            pattern_features=pattern_features,
        )

    def _extract_text_features(self, text: str) -> TextFeatures:
        """Extract text-based features."""
        # Basic text metrics
        words = text.split()
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        word_count = len(words)
        sentence_count = len(sentences)
        avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
        char_count = len(text)
        line_count = len(text.splitlines())

        # Punctuation features
        question_marks = len(re.findall(self.question_pattern, text))
        exclamation_marks = len(re.findall(self.exclamation_pattern, text))
        capital_letters = len(re.findall(self.capital_letters_pattern, text))
        punctuation = len(re.findall(self.punctuation_pattern, text))

        capital_ratio = capital_letters / max(char_count, 1)
        punctuation_ratio = punctuation / max(char_count, 1)

        # Code-related features
        code_blocks = len(re.findall(self.code_block_pattern, text))
        inline_code = len(re.findall(self.inline_code_pattern, text))
        code_snippets = code_blocks + inline_code
        file_paths = len(re.findall(self.file_path_pattern, text))
        urls = len(re.findall(self.url_pattern, text))

        # Sentiment features
        words_lower = [word.lower().strip(".,!?;:") for word in words]

        positive_words = sum(1 for word in words_lower if word in self.positive_words)
        negative_words = sum(1 for word in words_lower if word in self.negative_words)
        technical_terms = sum(1 for word in words_lower if word in self.technical_terms)

        # Readability metrics
        flesch_reading_ease = self._calculate_flesch_reading_ease(text, words, sentences)
        lexical_diversity = len(set(words_lower)) / max(word_count, 1)

        return TextFeatures(
            word_count=word_count,
            sentence_count=sentence_count,
            avg_word_length=avg_word_length,
            char_count=char_count,
            line_count=line_count,
            question_marks=question_marks,
            exclamation_marks=exclamation_marks,
            capital_ratio=capital_ratio,
            punctuation_ratio=punctuation_ratio,
            code_snippets=code_snippets,
            code_blocks=code_blocks,
            inline_code=inline_code,
            file_paths=file_paths,
            urls=urls,
            positive_words=positive_words,
            negative_words=negative_words,
            technical_terms=technical_terms,
            flesch_reading_ease=flesch_reading_ease,
            lexical_diversity=lexical_diversity,
        )

    def _extract_context_features(self, context: Dict[str, Any]) -> ContextFeatures:
        """Extract context-based features."""
        file_path = context.get("file_path", "")

        # File type detection
        is_test_file = any(marker in file_path.lower() for marker in ["test", "spec", "__test__"])
        is_config_file = any(
            ext in file_path.lower() for ext in [".json", ".yaml", ".yml", ".toml", ".ini"]
        )
        is_documentation = any(
            marker in file_path.lower() for marker in ["readme", "doc", ".md", "docs/"]
        )

        file_extension = file_path.split(".")[-1] if "." in file_path else ""

        # Location context
        line_number = context.get("line_number", 0)
        function_name = context.get("function_name", "")
        class_name = context.get("class_name", "")

        is_in_function = bool(function_name)
        is_in_class = bool(class_name)

        # Estimate nesting level from line indentation if available
        diff_context = context.get("diff_context", "")
        nesting_level = self._estimate_nesting_level(diff_context, line_number)

        # PR context
        pr_size = context.get("pr_size", 0)
        files_changed = context.get("files_changed", 0)
        is_first_review = context.get("is_first_review", True)

        # Temporal features
        comment_position = context.get("comment_position", 0)
        time_since_pr = context.get("time_since_pr", 0.0)

        return ContextFeatures(
            is_in_test_file=is_test_file,
            is_in_config_file=is_config_file,
            is_in_documentation=is_documentation,
            file_extension=file_extension,
            line_number=line_number,
            is_in_function=is_in_function,
            is_in_class=is_in_class,
            nesting_level=nesting_level,
            pr_size=pr_size,
            files_changed=files_changed,
            is_first_review=is_first_review,
            comment_position=comment_position,
            time_since_pr=time_since_pr,
        )

    def _extract_keyword_features(self, text: str) -> Dict[str, float]:
        """Extract keyword-based features."""
        text_lower = text.lower()
        features = {}

        # Severity keywords
        features["has_critical_words"] = float(
            any(word in text_lower for word in self.critical_words)
        )
        features["has_minor_words"] = float(any(word in text_lower for word in self.minor_words))

        # Category keywords
        features["has_security_words"] = float(bool(re.search(self.security_pattern, text)))
        features["has_performance_words"] = float(bool(re.search(self.performance_pattern, text)))

        # Action keywords
        features["has_suggestion_words"] = float(bool(re.search(self.suggestion_pattern, text)))
        features["has_requirement_words"] = float(bool(re.search(self.requirement_pattern, text)))
        features["has_issue_words"] = float(bool(re.search(self.issue_pattern, text)))
        features["has_improvement_words"] = float(bool(re.search(self.improvement_pattern, text)))

        # Specific keyword counts
        features["critical_word_count"] = float(
            sum(1 for word in self.critical_words if word in text_lower)
        )
        features["technical_density"] = float(
            len([word for word in text.split() if word.lower() in self.technical_terms])
        ) / max(len(text.split()), 1)

        return features

    def _extract_pattern_features(self, text: str) -> Dict[str, float]:
        """Extract pattern-based features."""
        features = {}

        # Communication patterns
        features["starts_with_question"] = float(
            text.strip().startswith(("What", "Why", "How", "When", "Where", "Who"))
        )
        features["ends_with_question"] = float(text.strip().endswith("?"))
        features["has_multiple_sentences"] = float(len(re.split(r"[.!?]+", text)) > 2)

        # Review patterns
        features["mentions_alternatives"] = float(
            bool(re.search(r"(?i)\b(alternative|instead|rather|consider|option)\b", text))
        )
        features["references_external"] = float(
            bool(re.search(r"(?i)\b(documentation|docs|spec|standard|best practice)\b", text))
        )
        features["suggests_testing"] = float(
            bool(re.search(r"(?i)\b(test|testing|unit test|integration test|coverage)\b", text))
        )

        # Formatting patterns
        features["has_code_example"] = float(bool(re.search(self.code_block_pattern, text)))
        features["has_bullet_points"] = float(bool(re.search(r"^\s*[-*•]\s", text, re.MULTILINE)))
        features["has_numbered_list"] = float(bool(re.search(r"^\s*\d+\.\s", text, re.MULTILINE)))

        # Emphasis patterns
        features["has_bold_text"] = float(bool(re.search(r"\*\*[^*]+\*\*|__[^_]+__", text)))
        features["has_italic_text"] = float(bool(re.search(r"\*[^*]+\*|_[^_]+_", text)))
        features["has_all_caps_words"] = float(bool(re.search(r"\b[A-Z]{3,}\b", text)))

        return features

    def _calculate_flesch_reading_ease(
        self, text: str, words: List[str], sentences: List[str]
    ) -> float:
        """Calculate Flesch Reading Ease score."""
        if not words or not sentences:
            return 0.0

        # Count syllables (simplified)
        syllable_count = 0
        for word in words:
            word_clean = re.sub(r"[^a-zA-Z]", "", word.lower())
            if word_clean:
                # Simple syllable counting heuristic
                vowels = "aeiouy"
                syllables = 0
                prev_was_vowel = False
                for char in word_clean:
                    is_vowel = char in vowels
                    if is_vowel and not prev_was_vowel:
                        syllables += 1
                    prev_was_vowel = is_vowel

                # Ensure at least one syllable per word
                syllable_count += max(1, syllables)

        # Flesch Reading Ease formula
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = syllable_count / len(words)

        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

        # Clamp to reasonable range
        return max(0.0, min(100.0, flesch_score))

    def _estimate_nesting_level(self, diff_context: str, line_number: int) -> int:
        """Estimate nesting level from diff context."""
        if not diff_context:
            return 0

        lines = diff_context.split("\n")
        target_line_idx = -1

        # Find the target line in diff context
        for i, line in enumerate(lines):
            if str(line_number) in line:
                target_line_idx = i
                break

        if target_line_idx == -1:
            return 0

        # Look at surrounding lines to estimate indentation
        context_lines = lines[max(0, target_line_idx - 2) : target_line_idx + 3]

        max_indentation = 0
        for line in context_lines:
            # Remove diff markers
            cleaned_line = re.sub(r"^[+-\s]*", "", line)
            if cleaned_line.strip():
                leading_spaces = len(line) - len(line.lstrip())
                indentation_level = leading_spaces // 4  # Assuming 4-space indentation
                max_indentation = max(max_indentation, indentation_level)

        return min(max_indentation, 10)  # Cap at reasonable level

    def extract_batch_features(
        self, comments_with_context: List[Tuple[str, Optional[Dict[str, Any]]]]
    ) -> List[CommentFeatureSet]:
        """Extract features for multiple comments.

        Args:
            comments_with_context: List of (comment_text, context) tuples

        Returns:
            List of feature sets
        """
        feature_sets = []

        for comment_text, context in comments_with_context:
            try:
                features = self.extract_features(comment_text, context)
                feature_sets.append(features)
            except Exception as e:
                logger.error(f"Error extracting features for comment: {e}")

                # Return default feature set on error
                feature_sets.append(
                    CommentFeatureSet(
                        text_features=TextFeatures(),
                        context_features=ContextFeatures(),
                        keyword_features={},
                        pattern_features={},
                    )
                )

        return feature_sets

    def get_feature_importance(
        self, feature_sets: List[CommentFeatureSet], labels: List[str]
    ) -> Dict[str, float]:
        """Calculate feature importance using simple correlation.

        Args:
            feature_sets: List of feature sets
            labels: Corresponding labels

        Returns:
            Feature importance scores
        """
        if not feature_sets or not labels:
            return {}

        # Convert to feature vectors
        feature_vectors = [fs.to_vector() for fs in feature_sets]
        if not feature_vectors:
            return {}

        feature_names = feature_vectors[0].keys()
        importance_scores = {}

        # Create label encoding
        unique_labels = list(set(labels))
        label_map = {label: i for i, label in enumerate(unique_labels)}
        numeric_labels = [label_map[label] for label in labels]

        # Calculate correlation for each feature
        for feature_name in feature_names:
            feature_values = [fv.get(feature_name, 0.0) for fv in feature_vectors]

            # Simple correlation calculation
            correlation = self._calculate_correlation(feature_values, numeric_labels)
            importance_scores[feature_name] = abs(correlation)

        return importance_scores

    def _calculate_correlation(self, x: List[float], y: List[int]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))

        if denominator == 0:
            return 0.0

        return numerator / denominator


# Global feature extractor instance
_global_extractor: Optional[FeatureExtractor] = None


def get_feature_extractor() -> FeatureExtractor:
    """Get global feature extractor."""
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = FeatureExtractor()
    return _global_extractor


def extract_comment_features(
    comment_text: str, context: Optional[Dict[str, Any]] = None
) -> CommentFeatureSet:
    """Extract features using global extractor.

    Args:
        comment_text: Comment text to analyze
        context: Optional context information

    Returns:
        Complete feature set
    """
    extractor = get_feature_extractor()
    return extractor.extract_features(comment_text, context)
