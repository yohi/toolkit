"""Thread processing and context analysis for CodeRabbit comments."""

import re
from typing import List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict

from ..models import ThreadContext
from ..models.thread_context import ResolutionStatus
from ..exceptions import CommentParsingError


class ThreadProcessor:
    """Processes comment threads to analyze structure and generate contextual summaries."""

    def __init__(self, resolved_marker: str = "🔒 CODERABBIT_RESOLVED 🔒"):
        """Initialize the thread processor.

        Args:
            resolved_marker: Marker text indicating a resolved comment thread
        """
        self.resolved_marker = resolved_marker
        self.coderabbit_author = "coderabbitai[bot]"

    def process_thread(self, thread_comments: List[Dict[str, Any]]) -> ThreadContext:
        """Process a comment thread to generate contextual information.

        Args:
            thread_comments: List of comments in chronological order

        Returns:
            ThreadContext object with analyzed thread information

        Raises:
            CommentParsingError: If thread cannot be processed
        """
        # Check for empty thread before entering try block
        if not thread_comments:
            raise CommentParsingError("Empty thread provided")
        
        try:
            # Sort comments chronologically
            sorted_comments = self._sort_comments_chronologically(thread_comments)
            # Extract thread metadata
            root_comment = sorted_comments[0]
            if not root_comment.get("id"):
                raise CommentParsingError("Missing root comment id")
            thread_id = str(root_comment["id"])
            file_context = root_comment.get("path", "")
            line_context = self._extract_line_context(root_comment)

            # Analyze thread participants
            participants = self._analyze_participants(sorted_comments)

            # Determine resolution status
            is_resolved = self._determine_resolution_status(sorted_comments)

            # Generate contextual summary
            context_summary = self._generate_context_summary(sorted_comments)

            # Extract CodeRabbit comments only
            coderabbit_comments = [
                c for c in sorted_comments
                if c.get("user", {}).get("login") == self.coderabbit_author
            ]

            # Generate AI-friendly structured format
            ai_summary = self._generate_ai_summary(sorted_comments, context_summary)

            # Prepare data for new ThreadContext structure
            replies = sorted_comments[1:] if len(sorted_comments) > 1 else []
            resolution_status = ResolutionStatus.RESOLVED if is_resolved else ResolutionStatus.UNRESOLVED

            return ThreadContext(
                thread_id=thread_id,
                main_comment=root_comment,
                replies=replies,
                resolution_status=resolution_status,
                contextual_summary=context_summary,
                chronological_order=sorted_comments
            )

        except Exception as e:
            raise CommentParsingError(f"Failed to process thread: {e!s}") from e
    def build_thread_context(self, comments: List[Dict[str, Any]]) -> List[ThreadContext]:
        """Build thread contexts from a list of comments by grouping them into threads.

        Args:
            comments: List of all comments

        Returns:
            List of ThreadContext objects, one for each thread
        """
        # Check for empty comments before processing
        if not comments:
            raise CommentParsingError("Empty comments list provided")

        try:
            # Group comments into threads
            threads = self._group_comments_into_threads(comments)

            # Process each thread
            thread_contexts = []
            for thread_comments in threads:
                if thread_comments:  # Only process non-empty threads
                    try:
                        context = self.process_thread(thread_comments)
                        thread_contexts.append(context)
                    except CommentParsingError:
                        # Skip problematic threads but continue processing others
                        continue

            return thread_contexts
        except Exception as e:
            raise CommentParsingError(f"Failed to build thread contexts: {e!s}") from e
    def _sort_comments_chronologically(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort comments in chronological order.

        Args:
            comments: List of comments to sort

        Returns:
            Comments sorted by creation time
        """
        def parse_datetime(dt_string: str) -> datetime:
            """Parse datetime string with fallback handling."""
            try:
                # Try parsing ISO format with Z suffix
                if dt_string.endswith('Z'):
                    dt = datetime.fromisoformat(dt_string[:-1] + '+00:00')
                else:
                    dt = datetime.fromisoformat(dt_string)
                # すべて UTC aware に正規化
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, TypeError):
                # Fallback to current time if parsing fails
                return datetime.now(timezone.utc)

        return sorted(
            comments,
            key=lambda c: parse_datetime(c.get("created_at", ""))
        )
    def _group_comments_into_threads(self, comments: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group comments into threads based on reply relationships.

        Args:
            comments: List of all comments

        Returns:
            List of comment threads
        """
        # Create mapping of comment ID to comment
        comment_map = {str(c.get("id", "")): c for c in comments if c.get("id")}

        # Group comments by thread
        threads = defaultdict(list)
        root_comments = []

        for comment in comments:
            comment_id = str(comment.get("id", ""))
            reply_to_id = comment.get("in_reply_to_id")

            if reply_to_id is None:
                # This is a root comment
                root_comments.append(comment)
                threads[comment_id].append(comment)
            else:
                # This is a reply - find the root comment
                root_id = self._find_thread_root(str(reply_to_id), comment_map)
                threads[root_id].append(comment)

        # Convert to list of thread lists
        return [thread for thread in threads.values() if thread]

    def _find_thread_root(self, comment_id: str, comment_map: Dict[str, Dict[str, Any]]) -> str:
        """Find the root comment ID for a given comment.

        Args:
            comment_id: ID of the comment to find root for
            comment_map: Mapping of comment IDs to comments

        Returns:
            Root comment ID
        """
        visited = set()
        current_id = comment_id

        while current_id and current_id not in visited:
            visited.add(current_id)

            if current_id not in comment_map:
                break

            comment = comment_map[current_id]
            reply_to_id = comment.get("in_reply_to_id")

            if reply_to_id is None:
                # Found root comment
                return current_id
            else:
                current_id = str(reply_to_id)

        # If we couldn't find root or hit a cycle, return the original ID
        return comment_id

    def _extract_line_context(self, comment: Dict[str, Any]) -> str:
        """Extract line context from a comment.

        Args:
            comment: Comment to extract line context from

        Returns:
            Line context string
        """
        line = comment.get("line")
        start_line = comment.get("start_line")

        if line is not None:
            return str(line)
        elif start_line is not None:
            end_line = comment.get("end_line", start_line)
            if end_line != start_line:
                return f"{start_line}-{end_line}"
            else:
                return str(start_line)
        else:
            return ""

    def _analyze_participants(self, comments: List[Dict[str, Any]]) -> List[str]:
        """Analyze thread participants.

        Args:
            comments: List of comments in the thread

        Returns:
            List of unique participant usernames
        """
        participants = set()

        for comment in comments:
            user = comment.get("user", {})
            username = user.get("login", "unknown")
            participants.add(username)

        return sorted(list(participants))

    def _determine_resolution_status(self, comments: List[Dict[str, Any]]) -> bool:
        """Determine if a thread is resolved based on resolved markers.

        Args:
            comments: List of comments in chronological order

        Returns:
            True if thread is resolved
        """
        # Check the last few comments for resolved markers
        for comment in reversed(comments[-3:]):  # Check last 3 comments
            body = comment.get("body", "")
            user = comment.get("user", {})

            # Only consider CodeRabbit comments for resolution status
            if user.get("login") == self.coderabbit_author:
                if self.resolved_marker in body:
                    return True

                # Also check for other resolution indicators
                resolution_patterns = [
                    r"\[CR_RESOLUTION_CONFIRMED[^\]]*\]",
                    r"✅.*resolved",
                    r"resolved.*✅",
                    r"issue.*fixed",
                    r"implemented.*suggestion"
                ]

                for pattern in resolution_patterns:
                    if re.search(pattern, body, re.IGNORECASE):
                        return True

        return False

    def _generate_context_summary(self, comments: List[Dict[str, Any]]) -> str:
        """Generate a contextual summary of the thread.

        Args:
            comments: List of comments in chronological order

        Returns:
            Contextual summary string
        """
        if not comments:
            return "Empty thread"

        root_comment = comments[0]
        user_count = len(set(c.get("user", {}).get("login") for c in comments))
        coderabbit_count = sum(
            1 for c in comments
            if c.get("user", {}).get("login") == self.coderabbit_author
        )

        # Extract key topics from CodeRabbit comments
        topics = self._extract_topics_from_coderabbit_comments(comments)

        summary_parts = []

        # Basic thread info
        if len(comments) == 1:
            summary_parts.append("Single comment thread")
        else:
            summary_parts.append(f"Thread with {len(comments)} comments from {user_count} participants")

        # CodeRabbit involvement
        if coderabbit_count > 0:
            summary_parts.append(f"CodeRabbit provided {coderabbit_count} comments")

        # File context
        file_path = root_comment.get("path")
        if file_path:
            summary_parts.append(f"Related to {file_path}")

        # Topics
        if topics:
            summary_parts.append(f"Topics: {', '.join(topics[:3])}")  # Top 3 topics

        return ". ".join(summary_parts) + "."

    def _extract_topics_from_coderabbit_comments(self, comments: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from CodeRabbit comments.

        Args:
            comments: List of comments

        Returns:
            List of topics found
        """
        topics = set()

        # Common patterns that indicate topics
        topic_patterns = [
            (r"security", "security"),
            (r"performance", "performance"),
            (r"refactor", "refactoring"),
            (r"test", "testing"),
            (r"documentation", "documentation"),
            (r"error handling", "error handling"),
            (r"validation", "validation"),
            (r"async|await", "async programming"),
            (r"database", "database"),
            (r"api", "API"),
            (r"ui|user interface", "UI"),
            (r"style|formatting", "code style"),
        ]

        for comment in comments:
            if comment.get("user", {}).get("login") == self.coderabbit_author:
                body = comment.get("body", "").lower()

                for pattern, topic in topic_patterns:
                    if re.search(pattern, body):
                        topics.add(topic)

        return sorted(list(topics))

    def _generate_ai_summary(self, comments: List[Dict[str, Any]], context_summary: str) -> str:
        """Generate AI-friendly structured summary following Claude 4 best practices.

        Args:
            comments: List of comments in chronological order
            context_summary: Basic context summary

        Returns:
            AI-optimized summary string
        """
        if not comments:
            return "No comments in thread"

        root_comment = comments[0]
        coderabbit_comments = [
            c for c in comments
            if c.get("user", {}).get("login") == self.coderabbit_author
        ]

        # Use existing method for participant analysis
        participants = self._analyze_participants(comments)
        # Structure following Claude 4 best practices
        ai_summary_parts = []

        # 1. Context (clear and specific)
        ai_summary_parts.append("## Thread Context")
        ai_summary_parts.append(f"- **File**: {root_comment.get('path', 'Unknown')}")
        ai_summary_parts.append(f"- **Line**: {self._extract_line_context(root_comment) or 'Unknown'}")
        ai_summary_parts.append(f"- **Participants**: {len(participants)}")
        ai_summary_parts.append(f"- **Total Comments**: {len(comments)}")
        ai_summary_parts.append(f"- **CodeRabbit Comments**: {len(coderabbit_comments)}")

        # Include the provided context summary
        if context_summary:
            ai_summary_parts.append(f"- **Summary**: {context_summary}")
        # 2. Resolution Status (clear outcome)
        resolution_status = "✅ Resolved" if self._determine_resolution_status(comments) else "⏳ Open"
        ai_summary_parts.append(f"- **Status**: {resolution_status}")

        # 3. Key Issues/Topics (actionable information)
        if coderabbit_comments:
            ai_summary_parts.append("\n## CodeRabbit Analysis")

            for i, comment in enumerate(coderabbit_comments[:3], 1):  # Limit to first 3
                body = comment.get("body", "")

                # Extract first meaningful line as summary
                lines = body.split('\n')
                summary_line = None

                for line in lines:
                    clean_line = line.strip()
                    if (clean_line and
                        not clean_line.startswith('_') and
                        not clean_line.startswith('<') and
                        not clean_line.startswith('```') and
                        len(clean_line) > 10):
                        summary_line = clean_line[:200]
                        break

                if summary_line:
                    ai_summary_parts.append(f"{i}. {summary_line}")

        # 4. Action Items (if any)
        action_items = self._extract_action_items_from_thread(comments)
        if action_items:
            ai_summary_parts.append("\n## Action Items")
            for item in action_items[:3]:  # Limit to 3 most important
                ai_summary_parts.append(f"- {item}")

        return "\n".join(ai_summary_parts)

    def _extract_action_items_from_thread(self, comments: List[Dict[str, Any]]) -> List[str]:
        """Extract action items from thread comments.

        Args:
            comments: List of comments

        Returns:
            List of action items
        """
        action_items = []

        action_patterns = [
            r"should\s+([^.]+)",
            r"need\s+to\s+([^.]+)",
            r"consider\s+([^.]+)",
            r"recommend\s+([^.]+)",
            r"suggest\s+([^.]+)",
        ]

        for comment in comments:
            if comment.get("user", {}).get("login") == self.coderabbit_author:
                body = comment.get("body", "")

                for pattern in action_patterns:
                    matches = re.finditer(pattern, body, re.IGNORECASE)
                    for match in matches:
                        action = match.group(1).strip()
                        if len(action) > 10 and len(action) < 100:  # Reasonable length
                            action_items.append(action)

        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in action_items:
            if item.lower() not in seen:
                seen.add(item.lower())
                unique_items.append(item)

        return unique_items[:5]  # Return top 5 action items

    def analyze_thread_complexity(self, thread_context: ThreadContext) -> Dict[str, Any]:
        """Analyze the complexity of a thread for prioritization.

        Args:
            thread_context: Thread context to analyze

        Returns:
            Dictionary with complexity metrics
        """
        complexity = {
            "score": 0,
            "factors": [],
            "priority": "low"
        }

        # Factor 1: Number of participants
        if len(thread_context.participants) > 2:
            complexity["score"] += 2
            complexity["factors"].append("multiple participants")

        # Factor 2: Number of comments
        if thread_context.comment_count > 5:
            complexity["score"] += 2
            complexity["factors"].append("long discussion")

        # Factor 3: CodeRabbit involvement
        if thread_context.coderabbit_comment_count > 1:
            complexity["score"] += 1
            complexity["factors"].append("multiple CodeRabbit comments")

        # Factor 4: Unresolved status
        if not thread_context.is_resolved:
            complexity["score"] += 3
            complexity["factors"].append("unresolved")

        # Factor 5: File type importance (heuristic)
        file_context = thread_context.file_context.lower()
        if any(ext in file_context for ext in ['.py', '.js', '.ts', '.java', '.cpp']):
            complexity["score"] += 1
            complexity["factors"].append("source code file")

        # Determine priority
        if complexity["score"] >= 6:
            complexity["priority"] = "high"
        elif complexity["score"] >= 3:
            complexity["priority"] = "medium"
        else:
            complexity["priority"] = "low"

        return complexity
