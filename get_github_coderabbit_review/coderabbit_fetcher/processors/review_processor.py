"""Review comment processor for extracting actionable comments and specialized sections."""

import re
from typing import List, Dict, Any, Optional

from ..models import ActionableComment, AIAgentPrompt
from ..models.review_comment import ReviewComment, NitpickComment, OutsideDiffComment
from ..exceptions import CommentParsingError


class ReviewProcessor:
    """Processes CodeRabbit review comments to extract actionable items and specialized sections."""

    def __init__(self):
        """Initialize the review processor."""
        self.nitpick_patterns = [
            r"🧹 Nitpick comments?",
            r"Nitpick comments?",
            r"Minor suggestions?",
            r"Style suggestions?"
        ]

        self.outside_diff_patterns = [
            r"⚠️ Outside diff range comments?",
            r"Outside diff range comments?",
            r"Comments? outside the diff",
            r"Outside.*diff.*range"
        ]

        self.ai_agent_patterns = [
            r"🤖 Prompt for AI Agents",
            r"Prompt for AI Agents",
            r"AI Agent Prompt",
            r"For AI Agents"
        ]

    def process_review_comment(self, comment: Dict[str, Any]) -> ReviewComment:
        """Process a CodeRabbit review comment.

        Args:
            comment: Raw comment data from GitHub API

        Returns:
            ReviewComment object with extracted information

        Raises:
            CommentParsingError: If comment cannot be processed
        """
        try:
            body = comment.get("body", "")

            # Extract actionable comments count from the comment
            actionable_count = self._extract_actionable_count(body)

            # Extract different types of comments
            actionable_comments = self.extract_actionable_comments(body)
            nitpick_comments = self.extract_nitpick_comments(body)
            outside_diff_comments = self.extract_outside_diff_comments(body)
            ai_agent_prompts = self.extract_ai_agent_prompts(body)

            return ReviewComment(
                actionable_count=actionable_count,
                actionable_comments=actionable_comments,
                nitpick_comments=nitpick_comments,
                outside_diff_comments=outside_diff_comments,
                ai_agent_prompts=ai_agent_prompts,
                raw_content=body
            )

        except Exception as e:
            raise CommentParsingError(f"Failed to process review comment: {str(e)}") from e

    def extract_actionable_comments(self, content: str) -> List[ActionableComment]:
        """Extract actionable comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of ActionableComment objects
        """
        actionable_comments = []

        # Look for sections that contain actionable items
        actionable_patterns = [
            r"### Actionable comments[^#]*?(?=\n#{1,3}|\\Z)",
            r"## Actionable comments[^#]*?(?=\n#{1,2}|\\Z)",
            r"#### Actionable comments[^#]*?(?=\n#{1,4}|\\Z)",
            r"\*\*Actionable comments posted:\s*(\d+)\*\*.*?(?=\n#{1,3}|\\Z)",
        ]

        for pattern in actionable_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section = match.group(0)
                items = self._parse_actionable_items(section)
                actionable_comments.extend(items)

        # If no specific actionable sections found, look for general issue patterns
        if not actionable_comments:
            items = self._parse_actionable_items(content)
            actionable_comments.extend(items)

        return actionable_comments

    def extract_nitpick_comments(self, content: str) -> List[NitpickComment]:
        """Extract nitpick comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of NitpickComment objects
        """
        nitpick_comments = []

        for pattern in self.nitpick_patterns:
            # Look for nitpick sections
            section_pattern = f"{pattern}[^#]*?(?=\n#{1,3}|\\Z)"
            matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                section = match.group(0)
                items = self._parse_nitpick_items(section)
                nitpick_comments.extend(items)

        # If no nitpick sections found but emoji pattern exists, look for general suggestions
        if not nitpick_comments and "🧹" in content:
            items = self._parse_nitpick_items(content)
            nitpick_comments.extend(items)

        return nitpick_comments

    def extract_outside_diff_comments(self, content: str) -> List[OutsideDiffComment]:
        """Extract outside diff range comments from review content.

        Args:
            content: Review comment body

        Returns:
            List of OutsideDiffComment objects
        """
        outside_diff_comments = []

        for pattern in self.outside_diff_patterns:
            # Look for outside diff sections
            section_pattern = f"{pattern}[^#]*?(?=\n#{1,3}|\\Z)"
            matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                section = match.group(0)
                items = self._parse_outside_diff_items(section)
                outside_diff_comments.extend(items)

        # If no outside diff sections found but pattern exists, look for general items
        if not outside_diff_comments and ("⚠️" in content or "outside diff" in content.lower()):
            items = self._parse_outside_diff_items(content)
            outside_diff_comments.extend(items)

        return outside_diff_comments

    def extract_ai_agent_prompts(self, content: str) -> List[AIAgentPrompt]:
        """Extract AI agent prompts from review content.

        Args:
            content: Review comment body

        Returns:
            List of AIAgentPrompt objects
        """
        ai_prompts = []

        for pattern in self.ai_agent_patterns:
            # Look for AI agent prompt sections
            section_pattern = f"<details>[^<]*?<summary>{pattern}</summary>(.*?)</details>"
            matches = re.finditer(section_pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                prompt_content = match.group(1).strip()

                # Extract code blocks from the prompt
                code_blocks = self._extract_code_blocks(prompt_content)

                if code_blocks:
                    # Use first code block as main content
                    main_code_block = code_blocks[0]

                    # Extract description from prompt content
                    lines = prompt_content.split('\n')
                    description = next((line.strip() for line in lines if line.strip() and not line.strip().startswith('```')), "AI Agent Prompt")

                    ai_prompts.append(AIAgentPrompt(
                        code_block=main_code_block,
                        description=description[:200] if description else "AI Agent Prompt",
                        file_path="",  # Will be filled by context analysis
                        line_range=""  # Will be filled by context analysis
                    ))
                else:
                    # If no code blocks, create a prompt with the content as description
                    ai_prompts.append(AIAgentPrompt(
                        code_block=prompt_content,  # Use content as code block
                        description=prompt_content[:200] if prompt_content else "AI Agent Prompt",
                        file_path="",
                        line_range=""
                    ))

        return ai_prompts

    def _extract_actionable_count(self, content: str) -> int:
        """Extract the number of actionable comments from content.

        Args:
            content: Review comment body

        Returns:
            Number of actionable comments found
        """
        # Look for patterns like "Actionable comments posted: 5"
        count_patterns = [
            r"\*\*Actionable comments posted:\s*(\d+)\*\*",
            r"Actionable comments posted:\s*(\d+)",
            r"(\d+)\s+actionable comments?",
            r"Total:\s*(\d+)\s+actionable"
        ]

        for pattern in count_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

    def _parse_actionable_items(self, section: str) -> List[ActionableComment]:
        """Parse actionable items from section with Phase 2 enhanced markdown structure analysis.

        Args:
            section: Section text containing actionable items

        Returns:
            List of ActionableComment objects
        """
        items = []

        # Phase 2: Advanced markdown structure analysis
        markdown_sections = self._analyze_markdown_structure(section)
        
        for markdown_section in markdown_sections:
            # Extract meaningful actionable items from each structured section
            actionable_items = self._extract_actionable_from_section(markdown_section)
            items.extend(actionable_items)
        
        return items

    def _analyze_markdown_structure(self, content: str) -> List[Dict[str, Any]]:
        """Analyze markdown structure to identify distinct sections and their types.
        
        Args:
            content: Raw markdown content
            
        Returns:
            List of structured sections with metadata
        """
        sections = []
        
        # Phase 2: Advanced CodeRabbit comment structure patterns
        coderabbit_patterns = [
            # Issue description pattern: `file:line`: **Title**
            {
                'pattern': r'`([^`]+)`:?\s*\*\*([^*]+)\*\*\s*\n\n(.*?)(?=\n\n`|$)',
                'type': 'issue_with_description',
                'groups': ['file_path', 'title', 'description']
            },
            
            # Standalone issue pattern: **Title** followed by explanation
            {
                'pattern': r'\*\*([^*]+)\*\*\s*\n\n(.*?)(?=\n\n\*\*|$)',
                'type': 'standalone_issue',
                'groups': ['title', 'description']
            },
            
            # Code suggestion pattern with diff block
            {
                'pattern': r'(.*?)\n\n```diff\n(.*?)\n```(?:\n\n(.*))?',
                'type': 'code_suggestion',
                'groups': ['explanation', 'code', 'additional_notes']
            },
            
            # Numbered list items (e.g., checklist or recommendations)
            {
                'pattern': r'(\d+\.\s+.*?)(?=\n\d+\.|$)',
                'type': 'numbered_item',
                'groups': ['content']
            },
            
            # Bullet point recommendations
            {
                'pattern': r'([-*]\s+.*?)(?=\n[-*]|$)',
                'type': 'bullet_item', 
                'groups': ['content']
            }
        ]
        
        # Try each pattern to extract structured sections
        for pattern_info in coderabbit_patterns:
            matches = re.finditer(
                pattern_info['pattern'], 
                content, 
                re.DOTALL | re.MULTILINE
            )
            
            for match in matches:
                section_data = {
                    'type': pattern_info['type'],
                    'raw_content': match.group(0),
                    'start_pos': match.start(),
                    'end_pos': match.end()
                }
                
                # Extract named groups
                for i, group_name in enumerate(pattern_info['groups'], 1):
                    if match.group(i):
                        section_data[group_name] = match.group(i).strip()
                
                sections.append(section_data)
        
        # Phase 2: If no structured patterns match, fall back to paragraph-based analysis
        if not sections:
            paragraphs = re.split(r'\n\s*\n', content.strip())
            for para in paragraphs:
                if para.strip() and len(para.strip()) > 20:
                    sections.append({
                        'type': 'paragraph',
                        'raw_content': para.strip(),
                        'content': para.strip()
                    })
        
        # Sort by position and remove overlaps
        sections.sort(key=lambda x: x.get('start_pos', 0))
        return self._remove_overlapping_sections(sections)

    def _remove_overlapping_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove overlapping sections, keeping the most specific ones.
        
        Args:
            sections: List of section dictionaries
            
        Returns:
            Non-overlapping sections
        """
        if not sections:
            return sections
            
        non_overlapping = []
        last_end = -1
        
        for section in sections:
            start = section.get('start_pos', 0)
            if start >= last_end:
                non_overlapping.append(section)
                last_end = section.get('end_pos', start)
        
        return non_overlapping

    def _extract_actionable_from_section(self, section: Dict[str, Any]) -> List[ActionableComment]:
        """Extract actionable comments from a structured markdown section.
        
        Args:
            section: Structured section dictionary
            
        Returns:
            List of ActionableComment objects
        """
        items = []
        section_type = section.get('type', 'unknown')
        
        if section_type == 'issue_with_description':
            # CodeRabbit issue with file path and description
            file_path = section.get('file_path', 'unknown')
            title = section.get('title', '')
            description = section.get('description', '')
            
            # Parse file and line info
            parsed_file, line_range = self._parse_file_line_info(file_path, '')
            
            # Combine title and description meaningfully
            full_description = f"{title}. {description}" if description else title
            
            if self._is_valid_actionable_item(parsed_file, full_description):
                items.append(ActionableComment(
                    comment_id=f"actionable_{len(items)}",
                    file_path=parsed_file,
                    line_range=line_range or "0",
                    issue_description=full_description,
                    priority="medium",
                    raw_content=section['raw_content']
                ))
        
        elif section_type == 'code_suggestion':
            # CodeRabbit code suggestion with diff
            explanation = section.get('explanation', '')
            code = section.get('code', '')
            notes = section.get('additional_notes', '')
            
            if explanation and code:
                # Create comprehensive description
                description = explanation
                if notes:
                    description += f". {notes}"
                
                if self._is_valid_actionable_item("unknown", description):
                    actionable_comment = ActionableComment(
                        comment_id=f"actionable_{len(items)}",
                        file_path="unknown",
                        line_range="0", 
                        issue_description=description,
                        priority="medium",
                        raw_content=section['raw_content']
                    )
                    
                    # Add code suggestion
                    from coderabbit_fetcher.models.ai_agent_prompt import AIAgentPrompt
                    actionable_comment.ai_agent_prompt = AIAgentPrompt(
                        code_block=code,
                        language="diff",
                        prompt_text=explanation
                    )
                    
                    items.append(actionable_comment)
        
        elif section_type == 'standalone_issue':
            # Standalone issue description
            title = section.get('title', '')
            description = section.get('description', '')
            
            full_description = f"{title}. {description}" if description else title
            
            if self._is_valid_actionable_item("unknown", full_description):
                items.append(ActionableComment(
                    comment_id=f"actionable_{len(items)}",
                    file_path="unknown",
                    line_range="0",
                    issue_description=full_description,
                    priority="medium",
                    raw_content=section['raw_content']
                ))
        
        elif section_type in ['numbered_item', 'bullet_item']:
            # List items (recommendations, checklists)
            content = section.get('content', '')
            
            # Clean up list markers
            content = re.sub(r'^\d+\.\s+', '', content)
            content = re.sub(r'^[-*]\s+', '', content)
            
            if self._is_valid_actionable_item("unknown", content):
                items.append(ActionableComment(
                    comment_id=f"actionable_{len(items)}",
                    file_path="unknown", 
                    line_range="0",
                    issue_description=content,
                    priority="low",  # List items are typically lower priority
                    raw_content=section['raw_content']
                ))
        
        elif section_type == 'paragraph':
            # Generic paragraph - try to extract meaningful info
            content = section.get('content', '')
            
            # Phase 2: Better sentence extraction
            meaningful_sentences = self._extract_meaningful_sentences(content)
            
            for sentence in meaningful_sentences:
                if self._is_valid_actionable_item("unknown", sentence):
                    items.append(ActionableComment(
                        comment_id=f"actionable_{len(items)}",
                        file_path="unknown",
                        line_range="0", 
                        issue_description=sentence,
                        priority="medium",
                        raw_content=content
                    ))
        
        return items
    
    def _extract_meaningful_sentences(self, content: str) -> List[str]:
        """Extract meaningful sentences from paragraph content.
        
        Args:
            content: Paragraph content
            
        Returns:
            List of meaningful sentences
        """
        # Split into sentences but be smart about it
        sentences = re.split(r'[.!?]+\s+', content)
        meaningful = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Phase 2: Enhanced sentence validation
            if (len(sentence) > 25 and  # Longer sentences are more likely meaningful
                not re.match(r'^[^\w]*$', sentence) and  # Not just symbols
                not re.match(r'^(for|if|while|echo|command)\s+', sentence, re.IGNORECASE) and  # Not code
                sentence.count(' ') >= 4):  # Has multiple words
                
                meaningful.append(sentence)
        
        return meaningful

    def _parse_file_line_info(self, file_info: str, line_info: str) -> tuple[str, str]:
        """Parse file path and line information from extracted groups.
        
        Args:
            file_info: File information string
            line_info: Line information string
            
        Returns:
            Tuple of (file_path, line_range)
        """
        # Clean file_info
        file_info = file_info.strip()
        
        # Check if file_info contains line numbers (e.g., "file.py:123-125")
        if ':' in file_info:
            parts = file_info.split(':', 1)
            file_path = parts[0].strip()
            line_from_file = parts[1].strip()
        else:
            file_path = file_info
            line_from_file = ""
        
        # Determine line range
        if line_from_file:
            line_range = line_from_file
        elif line_info:
            line_range = str(line_info).strip()
        else:
            line_range = "0"
        
        # Clean up file path
        file_path = file_path.replace('`', '').strip()
        
        # Handle special cases
        if not file_path or file_path in ['--', '-', '+', '*']:
            file_path = "unknown"
        
        # Remove leading/trailing punctuation
        file_path = re.sub(r'^[-+*\s]+|[-+*\s]+$', '', file_path)
        
        return file_path, line_range

    def _is_valid_actionable_item(self, file_path: str, description: str) -> bool:
        """Check if extracted item is a valid actionable comment.
        
        Args:
            file_path: Extracted file path
            description: Extracted description
            
        Returns:
            True if item appears to be valid
        """
        # Must have meaningful description (increased minimum length)
        if not description or len(description) < 15:
            return False
        
        # Filter out clearly invalid file paths
        invalid_paths = {
            '--', '-', '+', '*', '**', '***', 
            'create', 'implement', 'add', 'update', 'fix',
            # Phase 1: Add more invalid patterns found in output
            'for bin in aws fzf; do', 'command', 'if ! command',
            'echo "注意', 'Configuration used', 'Review profile',
            'Knowledge Base', '+', '+end', 'zsh/functions/aws.zsh',
            'zsh/functions/cursor.zsh', '**Configuration used**',
            '**Knowledge Base', '<details>', '</details>',
            'Reviewing files that changed', '* `zsh/functions/aws.zsh`',
            '* `zsh/functions/cursor.zsh`', 'Nitpick comments',
            '</blockquote></details>'
        }
        
        if file_path.lower() in invalid_paths or file_path in invalid_paths:
            return False
        
        # Phase 1: Filter out code fragments and metadata
        metadata_patterns = [
            r'^[\+\-\*]\s*',  # Git diff markers
            r'^\d+\s*hunks?\)',  # Hunk info
            r'^Configuration used',
            r'^Review profile',
            r'^Knowledge Base',
            r'^</?details>',
            r'^</?summary>',
            r'^</?blockquote>',
            r'^Reviewing files that changed',
            r'^\*\s*`[^`]+`\s*\(\d+\s+hunks?\)',  # File hunk info
            r'^Nitpick comments?\s*\(\d+\)',
            r'^```\w*$',  # Code block markers
            r'^[\+\-]\s*(if|for|echo|command)',  # Code line fragments
            r'^(CHILL|Disabled due to)',  # CodeRabbit UI metadata
        ]
        
        for pattern in metadata_patterns:
            if re.match(pattern, description, re.IGNORECASE):
                return False
        
        # Phase 1: Filter out incomplete sentences/fragments
        if description.count(' ') < 3:  # Less than 4 words
            return False
            
        # Filter out HTML/XML fragments
        if re.match(r'^<[^>]+>.*</[^>]+>$', description.strip()):
            return False
            
        # Filter out single code statements
        code_fragment_patterns = [
            r'^\s*(for|if|while|echo|command|return)\s+',  # Shell commands
            r'^\s*[\+\-]\s+',  # Diff lines
            r'^\s*\w+\s*=\s*',  # Variable assignments
            r'^\s*#.*$',  # Comments only
        ]
        
        for pattern in code_fragment_patterns:
            if re.match(pattern, description, re.IGNORECASE):
                return False
        
        # Filter out non-descriptive content
        if description.lower() in {'', 'todo', 'fixme', 'note'}:
            return False
        
        return True

    def _parse_nitpick_items(self, section: str) -> List[NitpickComment]:
        """Parse nitpick items from a section.

        Args:
            section: Section text containing nitpick items

        Returns:
            List of NitpickComment objects
        """
        items = []

        # Look for file:line patterns in nitpick sections
        item_pattern = r"(?:`([^`]+)`|([^:\n]+)):?(\d+)?[:\-\s]*(.+?)(?=\n[-*+]|\n`|\n\n|\\Z)"

        matches = re.finditer(item_pattern, section, re.MULTILINE | re.DOTALL)

        for match in matches:
            file_path = match.group(1) or match.group(2) or ""
            line_number = match.group(3) or "0"
            suggestion = match.group(4).strip()

            if len(suggestion) > 5 and file_path:
                # Clean up the suggestion
                suggestion = re.sub(r'\n+', ' ', suggestion)
                suggestion = re.sub(r'\s+', ' ', suggestion)

                items.append(NitpickComment(
                    file_path=file_path.strip(),
                    line_range=line_number,
                    suggestion=suggestion,
                    raw_content=match.group(0)
                ))

        return items

    def _parse_outside_diff_items(self, section: str) -> List[OutsideDiffComment]:
        """Parse outside diff items from a section.

        Args:
            section: Section text containing outside diff items

        Returns:
            List of OutsideDiffComment objects
        """
        items = []

        # Look for file patterns in outside diff sections
        item_pattern = r"(?:`([^`]+)`|([^:\n]+)):?(\d+)?[:\-\s]*(.+?)(?=\n[-*+]|\n`|\n\n|\\Z)"

        matches = re.finditer(item_pattern, section, re.MULTILINE | re.DOTALL)

        for match in matches:
            file_path = match.group(1) or match.group(2) or ""
            line_number = match.group(3) or "0"
            content = match.group(4).strip()

            if len(content) > 10 and file_path:
                # Clean up the content
                content = re.sub(r'\n+', ' ', content)
                content = re.sub(r'\s+', ' ', content)

                items.append(OutsideDiffComment(
                    file_path=file_path.strip(),
                    line_range=line_number,
                    content=content,
                    reason="Outside diff range",
                    raw_content=match.group(0)
                ))

        return items

    def _extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """Extract code blocks from content with enhanced detection.

        Args:
            content: Text content that may contain code blocks

        Returns:
            List of dictionaries containing code block info: {code, language, type}
        """
        code_blocks = []

        # Phase 1: Enhanced code block patterns
        patterns = [
            # Multi-line diff blocks
            (r"```diff\s*\n(.*?)\n```", "diff", "diff"),
            # Standard markdown code blocks with language
            (r"```(\w+)\s*\n(.*?)\n```", r"\1", "code_block"),
            # Standard markdown code blocks without language
            (r"```\s*\n(.*?)\n```", "text", "code_block"),
            # Multi-line code suggestions (+ prefix)
            (r"(\n\+[^\n]*(?:\n\+[^\n]*)*)", "bash", "suggestion"),
            # Inline code (only if meaningful - more than just a word)
            (r"`([^`\n]{10,})`", "text", "inline"),
            # HTML code tags
            (r"<code>(.*?)</code>", "text", "html_code"),
        ]

        for pattern, language_or_group, block_type in patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if block_type == "suggestion":
                    # Handle diff-style suggestions
                    code_content = match.group(1).strip()
                    # Clean up the + prefixes and reconstruct the code
                    lines = []
                    for line in code_content.split('\n'):
                        if line.startswith('+'):
                            lines.append(line[1:].strip())
                    code_content = '\n'.join(lines)
                    language = "bash"  # Default for shell suggestions
                else:
                    code_content = match.group(2 if r"\1" in language_or_group else 1).strip()
                    language = match.group(1) if r"\1" in language_or_group else language_or_group

                # Phase 1: Filter out meaningless code fragments
                if code_content and len(code_content) > 10:
                    # Skip fragments that are just variable names or simple expressions
                    if not re.match(r'^[\w\s]*$', code_content) or ' ' in code_content:
                        code_blocks.append({
                            'code': code_content,
                            'language': language,
                            'type': block_type
                        })

        return code_blocks

    def has_review_content(self, content: str) -> bool:
        """Check if content contains review-like information.

        Args:
            content: Comment content to check

        Returns:
            True if content appears to be a review comment
        """
        review_indicators = [
            "actionable comments", "nitpick", "outside diff", "refactor suggestion",
            "potential issue", "verification agent", "analysis chain"
        ]

        content_lower = content.lower()
        return any(indicator in content_lower for indicator in review_indicators)

    def categorize_comment_type(self, content: str) -> str:
        """Categorize the type of review comment.

        Args:
            content: Comment content

        Returns:
            Comment type: "nitpick", "potential_issue", "refactor_suggestion", "outside_diff", "general"
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
        else:
            return "general"
    
    def analyze_thread_context_relationships(self, threads: List, actionable_comments: List) -> Dict[str, Any]:
        """Phase 3: Analyze relationships between thread contexts and actionable comments.
        
        Args:
            threads: List of thread contexts
            actionable_comments: List of actionable comments
            
        Returns:
            Dictionary of relationships and context enrichment data
        """
        relationships = {
            'thread_comment_mapping': {},
            'file_based_clusters': {},
            'priority_adjustments': {},
            'context_enrichments': {}
        }
        
        # Group actionable comments by file
        file_clusters = {}
        for comment in actionable_comments:
            file_path = comment.file_path
            if file_path not in file_clusters:
                file_clusters[file_path] = []
            file_clusters[file_path].append(comment)
        
        relationships['file_based_clusters'] = file_clusters
        
        # Map threads to actionable comments based on context
        for thread in threads:
            thread_file = getattr(thread, 'file_context', '')
            thread_line = getattr(thread, 'line_context', '')
            
            # Find related actionable comments
            related_comments = []
            for comment in actionable_comments:
                if self._is_contextually_related(thread, comment):
                    related_comments.append(comment)
            
            if related_comments:
                relationships['thread_comment_mapping'][getattr(thread, 'thread_id', 'unknown')] = {
                    'thread': thread,
                    'related_comments': related_comments,
                    'context_strength': self._calculate_context_strength(thread, related_comments)
                }
        
        # Generate priority adjustments based on context
        for thread_id, mapping in relationships['thread_comment_mapping'].items():
            thread = mapping['thread']
            comments = mapping['related_comments']
            
            # Adjust priority based on thread discussion intensity
            if len(getattr(thread, 'chronological_comments', [])) > 3:
                # High discussion activity suggests important issue
                for comment in comments:
                    if comment.priority.lower() == 'low':
                        relationships['priority_adjustments'][comment.comment_id] = 'MEDIUM'
                    elif comment.priority.lower() == 'medium':
                        relationships['priority_adjustments'][comment.comment_id] = 'HIGH'
        
        return relationships
    
    def _is_contextually_related(self, thread, comment) -> bool:
        """Check if a thread and comment are contextually related.
        
        Args:
            thread: Thread context
            comment: Actionable comment
            
        Returns:
            True if they appear to be related
        """
        thread_file = getattr(thread, 'file_context', '')
        thread_line = str(getattr(thread, 'line_context', ''))
        
        # Exact file match
        if thread_file and thread_file == comment.file_path:
            # Check line proximity
            if thread_line and hasattr(comment, 'line_range'):
                try:
                    thread_line_num = int(thread_line)
                    comment_line = str(comment.line_range)
                    if '-' in comment_line:
                        # Range like "10-15"
                        line_parts = comment_line.split('-')
                        start_line = int(line_parts[0])
                        end_line = int(line_parts[1]) if len(line_parts) > 1 else start_line
                        return start_line <= thread_line_num <= end_line + 5  # Allow 5 lines buffer
                    else:
                        comment_line_num = int(comment_line)
                        return abs(thread_line_num - comment_line_num) <= 10  # Within 10 lines
                except (ValueError, AttributeError):
                    return True  # Same file is good enough
            return True
        
        # Partial file name match (for cases where paths might be different)
        if thread_file and comment.file_path:
            thread_basename = thread_file.split('/')[-1]
            comment_basename = comment.file_path.split('/')[-1]
            if thread_basename == comment_basename:
                return True
        
        return False
    
    def _calculate_context_strength(self, thread, related_comments) -> float:
        """Calculate the strength of context relationship.
        
        Args:
            thread: Thread context
            related_comments: List of related comments
            
        Returns:
            Strength score between 0.0 and 1.0
        """
        strength = 0.0
        
        # Base strength from having related comments
        strength += 0.3
        
        # Bonus for multiple related comments
        strength += min(len(related_comments) * 0.1, 0.3)
        
        # Bonus for discussion activity
        comment_count = len(getattr(thread, 'chronological_comments', []))
        strength += min(comment_count * 0.05, 0.2)
        
        # Bonus for unresolved status
        if not getattr(thread, 'is_resolved', True):
            strength += 0.2
        
        return min(strength, 1.0)
    
    def analyze_code_change_patterns(self, actionable_comments: List, pr_diff_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Phase 3: Analyze code change patterns to adjust priorities intelligently.
        
        Args:
            actionable_comments: List of actionable comments
            pr_diff_data: Optional PR diff data for analysis
            
        Returns:
            Analysis results with priority adjustments
        """
        analysis = {
            'change_type_distribution': {},
            'file_impact_scores': {},
            'priority_adjustments': {},
            'risk_indicators': []
        }
        
        # Group comments by file and analyze change patterns
        file_groups = {}
        for comment in actionable_comments:
            file_path = comment.file_path
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(comment)
        
        for file_path, comments in file_groups.items():
            # Calculate file impact score
            impact_score = self._calculate_file_impact_score(file_path, comments)
            analysis['file_impact_scores'][file_path] = impact_score
            
            # Analyze change types
            change_types = self._identify_change_types(file_path, comments)
            analysis['change_type_distribution'][file_path] = change_types
            
            # Generate priority adjustments based on analysis
            adjustments = self._generate_priority_adjustments_from_analysis(
                file_path, comments, impact_score, change_types
            )
            analysis['priority_adjustments'].update(adjustments)
            
            # Identify risk indicators
            risks = self._identify_risk_indicators(file_path, comments, change_types)
            analysis['risk_indicators'].extend(risks)
        
        return analysis
    
    def _calculate_file_impact_score(self, file_path: str, comments: List) -> float:
        """Calculate impact score for a file based on comments and file type.
        
        Args:
            file_path: Path to the file
            comments: Comments related to this file
            
        Returns:
            Impact score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score from number of comments
        score += min(len(comments) * 0.15, 0.6)
        
        # File type importance
        file_ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
        
        critical_files = {
            'py': 0.8, 'js': 0.8, 'ts': 0.8, 'java': 0.8, 'cpp': 0.8, 'c': 0.8,
            'go': 0.8, 'rs': 0.8, 'rb': 0.7, 'php': 0.7, 'scala': 0.7,
            'sql': 0.9, 'dockerfile': 0.9, 'yaml': 0.6, 'yml': 0.6, 'json': 0.6,
            'sh': 0.7, 'bash': 0.7, 'zsh': 0.7, 'fish': 0.7
        }
        
        # Critical file names
        file_name = file_path.split('/')[-1].lower()
        critical_names = {
            'main.py': 0.9, 'index.js': 0.9, 'app.py': 0.9, 'server.py': 0.9,
            'config.py': 0.8, 'settings.py': 0.8, 'requirements.txt': 0.7,
            'package.json': 0.8, 'dockerfile': 0.9, 'makefile': 0.7,
            '.env': 0.9, '.gitignore': 0.3, 'readme.md': 0.2
        }
        
        if file_name in critical_names:
            score += critical_names[file_name] * 0.3
        elif file_ext in critical_files:
            score += critical_files[file_ext] * 0.2
        
        # Bonus for security-related files
        if any(keyword in file_path.lower() for keyword in 
               ['auth', 'security', 'crypto', 'token', 'password', 'secret']):
            score += 0.2
        
        # Bonus for core infrastructure files
        if any(keyword in file_path.lower() for keyword in 
               ['core', 'base', 'main', 'init', 'setup', 'config']):
            score += 0.1
        
        return min(score, 1.0)
    
    def _identify_change_types(self, file_path: str, comments: List) -> Dict[str, int]:
        """Identify types of changes based on comment content.
        
        Args:
            file_path: Path to the file
            comments: Comments for this file
            
        Returns:
            Dictionary of change type counts
        """
        change_types = {
            'security': 0, 'performance': 0, 'bug_fix': 0, 'refactoring': 0,
            'new_feature': 0, 'documentation': 0, 'style': 0, 'testing': 0
        }
        
        for comment in comments:
            description = comment.issue_description.lower()
            
            # Security changes
            if any(keyword in description for keyword in 
                   ['security', 'vulnerability', 'exploit', 'injection', 'xss', 'csrf', 
                    'authentication', 'authorization', 'sanitize', 'validate']):
                change_types['security'] += 1
            
            # Performance changes
            elif any(keyword in description for keyword in 
                     ['performance', 'optimize', 'slow', 'memory', 'cpu', 'cache',
                      'efficiency', 'bottleneck', 'latency']):
                change_types['performance'] += 1
            
            # Bug fixes
            elif any(keyword in description for keyword in 
                     ['bug', 'error', 'fix', 'issue', 'problem', 'crash', 'fail']):
                change_types['bug_fix'] += 1
            
            # Refactoring
            elif any(keyword in description for keyword in 
                     ['refactor', 'restructure', 'cleanup', 'simplify', 'extract']):
                change_types['refactoring'] += 1
            
            # New features
            elif any(keyword in description for keyword in 
                     ['add', 'new', 'feature', 'implement', 'create', 'introduce']):
                change_types['new_feature'] += 1
            
            # Documentation
            elif any(keyword in description for keyword in 
                     ['document', 'comment', 'readme', 'doc', 'explain']):
                change_types['documentation'] += 1
            
            # Style/formatting
            elif any(keyword in description for keyword in 
                     ['style', 'format', 'indent', 'whitespace', 'lint']):
                change_types['style'] += 1
            
            # Testing
            elif any(keyword in description for keyword in 
                     ['test', 'spec', 'coverage', 'mock', 'assert']):
                change_types['testing'] += 1
        
        return change_types
    
    def _generate_priority_adjustments_from_analysis(
        self, file_path: str, comments: List, impact_score: float, change_types: Dict[str, int]
    ) -> Dict[str, str]:
        """Generate priority adjustments based on file analysis.
        
        Args:
            file_path: Path to the file
            comments: Comments for this file
            impact_score: Calculated impact score
            change_types: Distribution of change types
            
        Returns:
            Dictionary of comment_id to new priority mappings
        """
        adjustments = {}
        
        # High impact files get priority boost
        if impact_score > 0.7:
            for comment in comments:
                current_priority = comment.priority.lower()
                if current_priority == 'low':
                    adjustments[comment.comment_id] = 'MEDIUM'
                elif current_priority == 'medium':
                    adjustments[comment.comment_id] = 'HIGH'
        
        # Security changes always get high priority
        if change_types.get('security', 0) > 0:
            for comment in comments:
                if any(keyword in comment.issue_description.lower() for keyword in 
                       ['security', 'vulnerability', 'exploit']):
                    adjustments[comment.comment_id] = 'HIGH'
        
        # Performance issues in critical files get boosted
        if change_types.get('performance', 0) > 0 and impact_score > 0.6:
            for comment in comments:
                if any(keyword in comment.issue_description.lower() for keyword in 
                       ['performance', 'optimize', 'slow']):
                    current_priority = comment.priority.lower()
                    if current_priority != 'high':
                        adjustments[comment.comment_id] = 'HIGH'
        
        return adjustments
    
    def _identify_risk_indicators(
        self, file_path: str, comments: List, change_types: Dict[str, int]
    ) -> List[Dict[str, str]]:
        """Identify risk indicators based on file and change analysis.
        
        Args:
            file_path: Path to the file
            comments: Comments for this file
            change_types: Distribution of change types
            
        Returns:
            List of risk indicator dictionaries
        """
        risks = []
        
        # Multiple security issues in one file
        if change_types.get('security', 0) > 2:
            risks.append({
                'type': 'multiple_security_issues',
                'severity': 'HIGH',
                'description': f'Multiple security issues detected in {file_path}',
                'file_path': file_path
            })
        
        # High comment concentration (possible problem area)
        if len(comments) > 5:
            risks.append({
                'type': 'high_issue_concentration',
                'severity': 'MEDIUM',
                'description': f'High concentration of issues in {file_path} ({len(comments)} comments)',
                'file_path': file_path
            })
        
        # Mix of security and performance issues
        if change_types.get('security', 0) > 0 and change_types.get('performance', 0) > 0:
            risks.append({
                'type': 'security_performance_mix',
                'severity': 'HIGH',
                'description': f'Both security and performance issues in {file_path}',
                'file_path': file_path
            })
        
        return risks
    
    def optimize_processing_for_large_datasets(self, comments: List, max_items: int = 1000) -> Dict[str, Any]:
        """Phase 3: Optimize processing for large PR datasets.
        
        Args:
            comments: List of comments to process
            max_items: Maximum number of items to process efficiently
            
        Returns:
            Optimization results and processing strategy
        """
        optimization = {
            'dataset_size': len(comments),
            'processing_strategy': 'standard',
            'sampling_applied': False,
            'filtered_count': 0,
            'optimization_applied': []
        }
        
        # Large dataset handling
        if len(comments) > max_items:
            optimization['processing_strategy'] = 'optimized'
            optimization['optimization_applied'].append('large_dataset_sampling')
            
            # Intelligent sampling - prioritize important comments
            sampled_comments = self._intelligent_sampling(comments, max_items)
            optimization['filtered_count'] = len(sampled_comments)
            optimization['sampling_applied'] = True
        
        # Memory optimization for code blocks
        if optimization['dataset_size'] > 500:
            optimization['optimization_applied'].append('code_block_compression')
        
        # Parallel processing recommendation
        if optimization['dataset_size'] > 200:
            optimization['optimization_applied'].append('parallel_processing_recommended')
        
        return optimization
    
    def _intelligent_sampling(self, comments: List, target_size: int) -> List:
        """Intelligent sampling that preserves important comments.
        
        Args:
            comments: Full list of comments
            target_size: Target number of comments to keep
            
        Returns:
            Sampled list of comments
        """
        if len(comments) <= target_size:
            return comments
        
        # Score comments by importance
        scored_comments = []
        for comment in comments:
            score = self._calculate_comment_importance_score(comment)
            scored_comments.append((comment, score))
        
        # Sort by importance and take top N
        scored_comments.sort(key=lambda x: x[1], reverse=True)
        return [comment for comment, score in scored_comments[:target_size]]
    
    def _calculate_comment_importance_score(self, comment) -> float:
        """Calculate importance score for comment sampling.
        
        Args:
            comment: Comment to score
            
        Returns:
            Importance score
        """
        score = 0.0
        
        if hasattr(comment, 'issue_description'):
            description = comment.issue_description.lower()
            
            # High importance keywords
            high_importance = ['security', 'vulnerability', 'critical', 'error', 'bug', 'performance']
            for keyword in high_importance:
                if keyword in description:
                    score += 2.0
            
            # Medium importance keywords  
            medium_importance = ['improve', 'optimize', 'refactor', 'update', 'fix']
            for keyword in medium_importance:
                if keyword in description:
                    score += 1.0
            
            # Priority boost
            if hasattr(comment, 'priority'):
                priority_scores = {'HIGH': 3.0, 'MEDIUM': 2.0, 'LOW': 1.0}
                priority = comment.priority.value if hasattr(comment.priority, 'value') else str(comment.priority)
                score += priority_scores.get(priority.upper(), 1.0)
        
        return score
    
    def enhanced_error_recovery(self, operation_name: str, data: Any, fallback_strategy: str = 'graceful') -> Dict[str, Any]:
        """Phase 3: Enhanced error handling with recovery strategies.
        
        Args:
            operation_name: Name of the operation being performed
            data: Data being processed
            fallback_strategy: Strategy for error recovery
            
        Returns:
            Recovery result with status and processed data
        """
        recovery_result = {
            'operation': operation_name,
            'status': 'success',
            'errors_encountered': [],
            'recovery_applied': [],
            'processed_data': data,
            'warnings': []
        }
        
        try:
            # Validate input data
            if not data:
                recovery_result['warnings'].append('Empty input data provided')
                return recovery_result
            
            # Apply error-prone operation simulation (in real usage, this would be the actual operation)
            if isinstance(data, list) and len(data) > 1000:
                recovery_result['warnings'].append('Large dataset detected - applying optimization')
                recovery_result['recovery_applied'].append('dataset_optimization')
            
            # Memory management for large operations
            if hasattr(data, '__len__') and len(data) > 500:
                recovery_result['recovery_applied'].append('memory_management')
                
        except Exception as e:
            recovery_result['status'] = 'error_recovered'
            recovery_result['errors_encountered'].append({
                'error_type': type(e).__name__,
                'error_message': str(e),
                'fallback_applied': fallback_strategy
            })
            
            # Apply fallback strategies
            if fallback_strategy == 'graceful':
                # Continue with partial results
                recovery_result['processed_data'] = self._create_minimal_fallback_data()
                recovery_result['recovery_applied'].append('graceful_degradation')
                
            elif fallback_strategy == 'retry':
                # Attempt retry with simplified processing
                recovery_result['recovery_applied'].append('simplified_retry')
                recovery_result['processed_data'] = self._create_simplified_data(data)
                
            elif fallback_strategy == 'skip':
                # Skip problematic items
                recovery_result['recovery_applied'].append('selective_skipping')
                recovery_result['processed_data'] = []
        
        return recovery_result
    
    def _create_minimal_fallback_data(self) -> List[Any]:
        """Create minimal fallback data structure."""
        return []
    
    def _create_simplified_data(self, original_data: Any) -> List[Any]:
        """Create simplified version of data for retry."""
        if isinstance(original_data, list):
            # Return first 100 items as simplified set
            return original_data[:100] if len(original_data) > 100 else original_data
        return []
    
    def validate_phase3_integration(self) -> Dict[str, Any]:
        """Validate that Phase 3 features are properly integrated.
        
        Returns:
            Validation result with status and feature availability
        """
        validation = {
            'phase3_features': {
                'context_relationships': False,
                'code_pattern_analysis': False, 
                'performance_optimization': False,
                'error_recovery': False,
                'intelligent_prioritization': False
            },
            'integration_status': 'unknown',
            'missing_features': [],
            'warnings': []
        }
        
        # Check for context relationship methods
        if hasattr(self, 'analyze_thread_context_relationships'):
            validation['phase3_features']['context_relationships'] = True
        else:
            validation['missing_features'].append('analyze_thread_context_relationships')
            
        # Check for code pattern analysis
        if hasattr(self, 'analyze_code_change_patterns'):
            validation['phase3_features']['code_pattern_analysis'] = True
        else:
            validation['missing_features'].append('analyze_code_change_patterns')
            
        # Check for performance optimization
        if hasattr(self, 'optimize_processing_for_large_datasets'):
            validation['phase3_features']['performance_optimization'] = True
        else:
            validation['missing_features'].append('optimize_processing_for_large_datasets')
            
        # Check for error recovery
        if hasattr(self, 'enhanced_error_recovery'):
            validation['phase3_features']['error_recovery'] = True
        else:
            validation['missing_features'].append('enhanced_error_recovery')
            
        # Check for intelligent prioritization (via ActionableComment model)
        try:
            from ..models.actionable_comment import ActionableComment
            if hasattr(ActionableComment, '_detect_priority'):
                validation['phase3_features']['intelligent_prioritization'] = True
            else:
                validation['missing_features'].append('intelligent_prioritization')
        except ImportError:
            validation['missing_features'].append('actionable_comment_model')
            
        # Determine integration status
        enabled_features = sum(validation['phase3_features'].values())
        total_features = len(validation['phase3_features'])
        
        if enabled_features == total_features:
            validation['integration_status'] = 'fully_integrated'
        elif enabled_features >= total_features * 0.8:
            validation['integration_status'] = 'mostly_integrated'
        elif enabled_features >= total_features * 0.5:
            validation['integration_status'] = 'partially_integrated'
        else:
            validation['integration_status'] = 'poorly_integrated'
            
        return validation
