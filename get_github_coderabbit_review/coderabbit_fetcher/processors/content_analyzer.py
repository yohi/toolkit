"""Content analysis utilities for CodeRabbit comments."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes comment content for patterns, complexity, and relationships."""

    def __init__(self):
        """Initialize the content analyzer."""
        self.security_keywords = [
            'security', 'vulnerability', 'credential', 'token', 'password',
            'injection', 'xss', 'csrf', 'authentication', 'authorization',
            'leak', 'expose', 'sensitive'
        ]
        
        self.performance_keywords = [
            'performance', 'slow', 'optimization', 'memory', 'cpu',
            'bottleneck', 'cache', 'efficient', 'scale', 'latency'
        ]
        
        self.critical_keywords = [
            'critical', 'urgent', 'breaking', 'fails', 'error',
            'exception', 'crash', 'timeout', 'corrupt'
        ]

    def analyze_comment_priority(self, content: str, file_path: str = "") -> str:
        """Analyze comment content to determine priority level.

        Args:
            content: Comment content to analyze
            file_path: File path context for additional priority hints

        Returns:
            Priority level: "HIGH", "MEDIUM", or "LOW"
        """
        content_lower = content.lower()
        priority_score = 0

        # Security issues are always high priority
        if any(keyword in content_lower for keyword in self.security_keywords):
            priority_score += 10

        # Critical functionality issues
        if any(keyword in content_lower for keyword in self.critical_keywords):
            priority_score += 8

        # Performance issues
        if any(keyword in content_lower for keyword in self.performance_keywords):
            priority_score += 6

        # File type considerations
        if file_path:
            if any(ext in file_path.lower() for ext in ['.py', '.js', '.ts', '.java']):
                priority_score += 2  # Source code files are more important
            elif any(ext in file_path.lower() for ext in ['.md', '.txt', '.rst']):
                priority_score -= 1  # Documentation files are lower priority

        # Content indicators
        if any(indicator in content_lower for indicator in ['fix', 'change', 'update', 'remove']):
            priority_score += 3

        if any(indicator in content_lower for indicator in ['style', 'format', 'comment', 'typo']):
            priority_score -= 2

        # Determine final priority
        if priority_score >= 8:
            return "HIGH"
        elif priority_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"

    def analyze_comment_type(self, content: str) -> str:
        """Analyze comment content to determine comment type.

        Args:
            content: Comment content to analyze

        Returns:
            Comment type string
        """
        content_lower = content.lower()

        if "🧹" in content or "nitpick" in content_lower:
            return "nitpick"
        elif "⚠️" in content or "potential issue" in content_lower:
            return "potential_issue"
        elif "🛠️" in content or "refactor suggestion" in content_lower:
            return "refactor_suggestion"
        elif "outside diff" in content_lower:
            return "outside_diff"
        elif "🤖" in content or "ai agent" in content_lower:
            return "ai_agent_prompt"
        else:
            return "general"

    def extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from comment content.

        Args:
            content: Comment content

        Returns:
            List of code block dictionaries with language and content
        """
        code_blocks = []

        # Find fenced code blocks
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1) or 'text'
            code_content = match.group(2).strip()
            
            if code_content:
                code_blocks.append({
                    'language': language,
                    'content': code_content,
                    'lines': len(code_content.split('\n'))
                })

        # Find inline code
        inline_pattern = r'`([^`]+)`'
        inline_matches = re.finditer(inline_pattern, content)

        for match in inline_matches:
            code_content = match.group(1).strip()
            if code_content and len(code_content) > 10:  # Only longer inline code
                code_blocks.append({
                    'language': 'inline',
                    'content': code_content,
                    'lines': 1
                })

        return code_blocks

    def analyze_complexity_indicators(self, content: str) -> Dict[str, Any]:
        """Analyze content for complexity indicators.

        Args:
            content: Comment content to analyze

        Returns:
            Dictionary with complexity metrics
        """
        complexity = {
            'word_count': len(content.split()),
            'line_count': len(content.split('\n')),
            'code_blocks': len(self.extract_code_blocks(content)),
            'has_links': bool(re.search(r'https?://', content)),
            'has_lists': bool(re.search(r'^[*-]\s+', content, re.MULTILINE)),
            'has_tables': bool(re.search(r'\|.*\|', content)),
            'complexity_score': 0
        }

        # Calculate complexity score
        score = 0
        score += min(complexity['word_count'] // 50, 5)  # Cap at 5 points
        score += min(complexity['line_count'] // 10, 3)   # Cap at 3 points
        score += complexity['code_blocks'] * 2
        score += 1 if complexity['has_links'] else 0
        score += 1 if complexity['has_lists'] else 0
        score += 1 if complexity['has_tables'] else 0

        complexity['complexity_score'] = score
        
        return complexity

    def extract_file_references(self, content: str) -> List[Dict[str, Any]]:
        """Extract file references from comment content.

        Args:
            content: Comment content

        Returns:
            List of file reference dictionaries
        """
        file_refs = []

        # Pattern for file references with optional line numbers
        file_pattern = r'([^\s]+\.(py|js|ts|java|cpp|c|h|md|txt|json|yaml|yml|toml|ini|cfg))(?::(\d+))?'
        matches = re.finditer(file_pattern, content)

        for match in matches:
            file_path = match.group(1)
            extension = match.group(2)
            line_number = int(match.group(3)) if match.group(3) else None

            file_refs.append({
                'path': file_path,
                'extension': extension,
                'line_number': line_number,
                'is_source_code': extension in ['py', 'js', 'ts', 'java', 'cpp', 'c', 'h']
            })

        return file_refs

    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment and tone of comment content.

        Args:
            content: Comment content to analyze

        Returns:
            Dictionary with sentiment analysis
        """
        content_lower = content.lower()

        positive_words = [
            'good', 'great', 'excellent', 'nice', 'clean', 'clear',
            'improvement', 'better', 'optimize', 'enhance'
        ]

        negative_words = [
            'wrong', 'bad', 'poor', 'unclear', 'confusing', 'problematic',
            'issue', 'problem', 'error', 'broken', 'fail'
        ]

        neutral_words = [
            'consider', 'suggest', 'might', 'could', 'perhaps',
            'alternative', 'option', 'possible'
        ]

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        neutral_count = sum(1 for word in neutral_words if word in content_lower)

        total_words = positive_count + negative_count + neutral_count

        if total_words == 0:
            sentiment = "neutral"
            confidence = 0.5
        else:
            if positive_count > negative_count and positive_count > neutral_count:
                sentiment = "positive"
                confidence = positive_count / total_words
            elif negative_count > positive_count and negative_count > neutral_count:
                sentiment = "negative"
                confidence = negative_count / total_words
            else:
                sentiment = "neutral"
                confidence = max(neutral_count, max(positive_count, negative_count)) / total_words

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'neutral_indicators': neutral_count
        }

    def extract_action_words(self, content: str) -> List[str]:
        """Extract action words from comment content.

        Args:
            content: Comment content

        Returns:
            List of action words found
        """
        action_words = [
            'fix', 'change', 'update', 'modify', 'replace', 'remove',
            'add', 'implement', 'refactor', 'optimize', 'improve',
            'validate', 'check', 'verify', 'test', 'ensure'
        ]

        content_lower = content.lower()
        found_actions = []

        for action in action_words:
            if action in content_lower:
                found_actions.append(action)

        return found_actions

    def analyze_technical_depth(self, content: str) -> Dict[str, Any]:
        """Analyze technical depth and expertise level of comment.

        Args:
            content: Comment content

        Returns:
            Dictionary with technical depth analysis
        """
        content_lower = content.lower()

        technical_terms = [
            'algorithm', 'complexity', 'optimization', 'performance',
            'architecture', 'design pattern', 'inheritance', 'polymorphism',
            'async', 'thread', 'concurrency', 'memory', 'garbage collection',
            'database', 'sql', 'orm', 'api', 'rest', 'graphql',
            'security', 'encryption', 'authentication', 'authorization'
        ]

        advanced_terms = [
            'deadlock', 'race condition', 'mutex', 'semaphore',
            'microservices', 'event sourcing', 'cqrs', 'ddd',
            'functional programming', 'monad', 'closure',
            'dependency injection', 'inversion of control'
        ]

        technical_count = sum(1 for term in technical_terms if term in content_lower)
        advanced_count = sum(1 for term in advanced_terms if term in content_lower)

        depth_score = technical_count + (advanced_count * 2)

        if depth_score >= 8:
            depth_level = "expert"
        elif depth_score >= 4:
            depth_level = "intermediate"
        elif depth_score >= 1:
            depth_level = "basic"
        else:
            depth_level = "general"

        return {
            'depth_level': depth_level,
            'depth_score': depth_score,
            'technical_terms_count': technical_count,
            'advanced_terms_count': advanced_count,
            'has_code_examples': bool(self.extract_code_blocks(content))
        }
