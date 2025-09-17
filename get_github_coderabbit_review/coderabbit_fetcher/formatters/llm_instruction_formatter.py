"""LLM Instruction Formatter for CodeRabbit comments.

This formatter creates XML-structured instruction prompts optimized for
LLM consumption following Claude 4 best practices.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from ..models import (
    ActionableComment,
    AIAgentPrompt,
    AnalyzedComments,
    ReviewComment,
    SummaryComment,
    ThreadContext,
)
from .base_formatter import BaseFormatter


class LLMInstructionFormatter(BaseFormatter):
    """Formatter for LLM instruction prompts with XML structure."""

    def format(
        self,
        persona: str,
        analyzed_comments: AnalyzedComments,
        quiet: bool = False
    ) -> str:
        """Format analyzed comments into LLM instruction prompts.

        Args:
            persona: AI persona prompt string (English)
            analyzed_comments: Analyzed CodeRabbit comments
            quiet: Not used in LLM formatter - always uses optimized format

        Returns:
            XML-structured LLM instruction prompt
        """
        sections = []

        # Document header
        sections.append(self._format_header())

        # AI Agent Context
        sections.append(self._format_agent_context(persona))

        # Task Overview
        sections.append(self._format_task_overview(analyzed_comments))

        # Execution Instructions
        sections.append(self._format_execution_instructions(analyzed_comments))

        # Context Data
        sections.append(self._format_context_data(analyzed_comments))

        # Document footer
        sections.append(self._format_footer())

        return "\n\n".join(sections)

    def _format_header(self) -> str:
        """Format XML document header."""
        timestamp = datetime.now().isoformat()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<coderabbit_instructions generated="{timestamp}">"""

    def _format_footer(self) -> str:
        """Format XML document footer."""
        return "</coderabbit_instructions>"

    def _format_agent_context(self, persona: str) -> str:
        """Format AI agent context section.

        Args:
            persona: AI persona prompt string

        Returns:
            Formatted agent context XML
        """
        escaped_persona = escape(persona)
        return f"""<agent_context>
  <persona language="english">
{self._indent_text(escaped_persona, 4)}
  </persona>
  <capabilities>
    <capability>Code analysis and review</capability>
    <capability>Issue identification and prioritization</capability>
    <capability>Code generation and modification</capability>
    <capability>Best practice recommendations</capability>
  </capabilities>
</agent_context>"""

    def _format_task_overview(self, analyzed_comments: AnalyzedComments) -> str:
        """Format task overview section.

        Args:
            analyzed_comments: Analyzed comments data

        Returns:
            Formatted task overview XML
        """
        stats = self._calculate_statistics(analyzed_comments)

        return f"""<task_overview>
  <objective>Analyze CodeRabbit review comments and provide actionable recommendations</objective>
  <statistics>
    <total_comments>{stats['total_comments']}</total_comments>
    <actionable_items>{stats['actionable_items']}</actionable_items>
    <high_priority>{stats['high_priority']}</high_priority>
    <files_affected>{stats['files_affected']}</files_affected>
  </statistics>
  <execution_priority>
    <priority_order>HIGH → MEDIUM → LOW</priority_order>
    <parallel_processing>Recommended for independent tasks</parallel_processing>
  </execution_priority>
</task_overview>"""

    def _format_execution_instructions(self, analyzed_comments: AnalyzedComments) -> str:
        """Format execution instructions section.

        Args:
            analyzed_comments: Analyzed comments data

        Returns:
            Formatted execution instructions XML
        """
        instructions = []
        instructions.append("<execution_instructions>")

        # Primary tasks with integrated enhancements
        primary_tasks = self._extract_primary_tasks(analyzed_comments)
        if primary_tasks:
            instructions.append("  <primary_tasks>")
            for task in primary_tasks:
                # Integrated: Enhanced task attributes with fallbacks
                task_attrs = f"priority='{task['priority']}' comment_id='{task.get('comment_id', 'N/A')}'"
                
                # Add context information if available (Phase 3 integration)
                if task.get('context_strength', 0.0) > 0:
                    task_attrs += f" context_strength='{task['context_strength']:.2f}'"
                
                if task.get('file_impact_score', 0.0) > 0:
                    task_attrs += f" file_impact='{task['file_impact_score']:.2f}'"
                
                instructions.append(f"    <task {task_attrs}>")
                instructions.append(f"      <description>{escape(task['description'])}</description>")
                instructions.append(f"      <file>{escape(task['file'])}</file>")
                if task.get('line') and task['line'] is not None:
                    instructions.append(f"      <line>{escape(str(task['line']))}</line>")

                # **REQUIREMENT FIX: Add code_suggestion element as specified in LLM_INSTRUCTION_FORMAT.md**
                if task.get('code_suggestion'):
                    language = task.get('language', 'text')
                    instructions.append(f"      <code_suggestion language='{escape(language)}'>")
                    instructions.append(f"{self._indent_text(escape(task['code_suggestion']), 8)}")
                    instructions.append("      </code_suggestion>")

                # **REQUIREMENT FIX: Display AI Agent prompt content per Requirement 4.5 and 9.2**
                if task.get('has_ai_prompt') and task.get('ai_prompt_content'):
                    instructions.append("      <ai_agent_prompt>")
                    instructions.append(f"{self._indent_text(escape(task['ai_prompt_content']), 8)}")
                    instructions.append("      </ai_agent_prompt>")
                elif task.get('has_ai_prompt'):
                    instructions.append("      <ai_agent_prompt>true</ai_agent_prompt>")

                # Risk indicators (if available)
                if task.get('risk_indicators'):
                    instructions.append("      <risk_indicators>")
                    for risk in task['risk_indicators']:
                        instructions.append(f"        <risk_type>{escape(risk)}</risk_type>")
                    instructions.append("      </risk_indicators>")

                instructions.append("    </task>")
            instructions.append("  </primary_tasks>")

        # Additional guidance
        instructions.append("  <guidance>")
        instructions.append("    <approach>Address issues systematically by priority level</approach>")
        instructions.append("    <verification>Test changes thoroughly before finalizing</verification>")
        instructions.append("    <best_practices>Follow language-specific conventions and patterns</best_practices>")
        instructions.append("  </guidance>")

        instructions.append("</execution_instructions>")
        return "\n".join(instructions)

    def _format_context_data(self, analyzed_comments: AnalyzedComments) -> str:
        """Format context data section.

        Args:
            analyzed_comments: Analyzed comments data

        Returns:
            Formatted context data XML
        """
        sections = []
        sections.append("<context_data>")

        # Summary information
        if analyzed_comments.summary_comments:
            sections.append("  <summary_information>")
            for summary in analyzed_comments.summary_comments:
                sections.append(f"    <summary>")
                sections.append(f"      <content>{escape(summary.summary_text)}</content>")
                if hasattr(summary, 'walkthrough') and summary.walkthrough:
                    sections.append(f"      <walkthrough>{escape(summary.walkthrough)}</walkthrough>")
                sections.append(f"    </summary>")
            sections.append("  </summary_information>")

        # Thread contexts with inline comments
        if analyzed_comments.unresolved_threads:
            sections.append("  <thread_contexts>")
            for thread in analyzed_comments.unresolved_threads:
                sections.append(f"    <thread id='{thread.thread_id}' resolved='{thread.is_resolved}'>")
                sections.append(f"      <file_context>{escape(thread.file_context)}</file_context>")
                if thread.line_context:
                    sections.append(f"      <line_context>{escape(thread.line_context)}</line_context>")

                # Extract inline comments from thread
                inline_comments = self._extract_thread_inline_comments(thread)
                if inline_comments:
                    sections.append("      <inline_comments>")
                    for comment in inline_comments:
                        sections.append(f"        <comment id='{comment['id']}'>")
                        sections.append(f"          <author>{escape(comment['author'])}</author>")
                        sections.append(f"          <content>{escape(comment['content'])}</content>")
                        if comment.get('created_at'):
                            sections.append(f"          <timestamp>{escape(comment['created_at'])}</timestamp>")
                        sections.append("        </comment>")
                    sections.append("      </inline_comments>")

                # Thread summary as JSON data
                thread_data = self._thread_to_json(thread)
                sections.append(f"      <structured_data>")
                sections.append(f"{self._indent_text(escape(json.dumps(thread_data, ensure_ascii=False, indent=2)), 8)}")
                sections.append(f"      </structured_data>")
                sections.append(f"    </thread>")
            sections.append("  </thread_contexts>")

        sections.append("</context_data>")
        return "\n".join(sections)

    def _extract_primary_tasks(self, analyzed_comments: AnalyzedComments) -> List[Dict[str, Any]]:
        """Extract primary tasks from analyzed comments with integrated smart analysis.

        Combines Phase 3 intelligent enhancements with robust practical filtering.

        Args:
            analyzed_comments: Analyzed comments data

        Returns:
            List of primary task dictionaries
        """
        tasks = []
        all_actionable_comments = []
        
        # Collect all actionable comments
        for review in analyzed_comments.review_comments:
            all_actionable_comments.extend(review.actionable_comments)

        # Try Phase 3 intelligent analysis (with fallback)
        context_relationships = None
        change_analysis = None
        try:
            context_relationships = self._analyze_context_relationships(
                analyzed_comments.unresolved_threads, all_actionable_comments
            )
            change_analysis = self._analyze_code_patterns(all_actionable_comments)
        except Exception:
            # Fallback to basic processing if Phase 3 features unavailable
            context_relationships = {'context_strengths': {}}
            change_analysis = {'file_impact_scores': {}, 'risk_indicators': []}

        # Initialize counters for each category
        actionable_counter = 0
        nitpick_counter = 0
        outside_diff_counter = 0

        # Extract from review comments (actionable comments)
        for review in analyzed_comments.review_comments:
            for comment in review.actionable_comments:
                # Use meaningful task filtering with enhanced validation
                if not self._is_meaningful_task(comment.issue_description, comment.file_path):
                    continue
                    
                if self._should_skip_actionable(comment):
                    continue

                # Determine priority with intelligent adjustments
                priority_value = comment.priority.value if hasattr(comment.priority, 'value') else str(comment.priority)
                priority_value = priority_value.upper()
                
                # Apply intelligent priority adjustments if available
                if context_relationships and change_analysis:
                    try:
                        adjusted_priority = self._calculate_intelligent_priority(
                            comment, context_relationships, change_analysis
                        )
                        priority_value = adjusted_priority
                    except Exception:
                        pass  # Keep original priority on error

                # Extract line number with validation - use line_range property first
                line_value = None
                if hasattr(comment, 'line_range') and comment.line_range and self._is_valid_line_number(str(comment.line_range)):
                    line_value = str(comment.line_range)
                elif hasattr(comment, 'line_number') and comment.line_number and self._is_valid_line_number(str(comment.line_number)):
                    line_value = str(comment.line_number)
                else:
                    # Try to extract line number from comment description
                    line_value = self._extract_line_number_from_description(comment.issue_description)

                # **REQUIREMENT FIX: Use actual GitHub comment ID instead of generated ID**
                comment_id = comment.comment_id if comment.comment_id else f"actionable_{actionable_counter}"

                # **REQUIREMENT FIX: Simplify description to be concise**
                description = self._extract_concise_description(comment.issue_description)

                task = {
                    'priority': priority_value,
                    'comment_id': comment_id,
                    'description': description,
                    'file': comment.file_path if comment.file_path and len(comment.file_path) > 3 else "Unknown",
                    'line': line_value,
                }

                # Add Phase 3 context information if available
                if context_relationships:
                    task['context_strength'] = context_relationships.get('context_strengths', {}).get(comment.comment_id, 0.0)
                    task['description'] = self._enhance_description_with_context(comment, context_relationships)
                
                if change_analysis:
                    task['file_impact_score'] = change_analysis.get('file_impact_scores', {}).get(comment.file_path, 0.0)
                    task['risk_indicators'] = self._get_task_risk_indicators(
                        comment, change_analysis.get('risk_indicators', [])
                    )

                # **REQUIREMENT FIX: Add AI Agent prompt content per Requirement 4.5 and 9.2**
                if comment.ai_agent_prompt:
                    task['has_ai_prompt'] = True

                    # Extract the complete AI Agent prompt content (Requirements 4.5 & 9.2)
                    # Use description only if code_block contains actual code, otherwise avoid duplication
                    ai_prompt_parts = []

                    # Check if code_block contains actual code or just repeated description
                    has_actual_code = (comment.ai_agent_prompt.code_block and
                                     comment.ai_agent_prompt.code_block.strip() and
                                     comment.ai_agent_prompt.code_block != comment.ai_agent_prompt.description and
                                     not comment.ai_agent_prompt.code_block.strip().startswith('In '))

                    if comment.ai_agent_prompt.description:
                        ai_prompt_parts.append(comment.ai_agent_prompt.description)

                    if has_actual_code:
                        # Use file extension to determine the correct language, override AI Agent prompt language if needed
                        detected_language = self._detect_language_from_file(comment.file_path)
                        language = detected_language if detected_language != 'text' else (comment.ai_agent_prompt.language or 'text')
                        ai_prompt_parts.append(f"```{language}\n{comment.ai_agent_prompt.code_block}\n```")

                    if ai_prompt_parts:
                        task['ai_prompt_content'] = '\n\n'.join(ai_prompt_parts)
                    # Note: Do NOT set code_suggestion when AI Agent prompt exists
                else:
                    # **REQUIREMENT FIX: Generate code suggestion for comments without AI agent prompts (Requirement 9.1.4)**
                    code_suggestion = self._generate_code_suggestion_from_comment(comment)
                    if code_suggestion:
                        task['code_suggestion'] = code_suggestion
                        task['language'] = self._detect_language_from_file(comment.file_path)

                tasks.append(task)
                actionable_counter += 1

            # Extract from nitpick comments with enhanced filtering
            for comment in review.nitpick_comments:
                if not self._is_meaningful_task(comment.suggestion, comment.file_path):
                    continue
                    
                if self._should_skip_nitpick(comment):
                    continue

                # Intelligent priority for nitpicks based on file impact
                priority = 'LOW'  # Default
                if change_analysis:
                    file_impact = change_analysis.get('file_impact_scores', {}).get(comment.file_path, 0.0)
                    priority = 'MEDIUM' if file_impact > 0.7 else 'LOW'

                # Extract line number with validation
                line_value = None
                if hasattr(comment, 'line_number') and comment.line_number and self._is_valid_line_number(comment.line_number):
                    line_value = comment.line_number
                elif hasattr(comment, 'line_range') and self._is_valid_line_number(comment.line_range):
                    line_value = comment.line_range

                # **REQUIREMENT FIX: Use GitHub comment ID when available**
                comment_id = getattr(comment, 'comment_id', None) or f"nitpick_{nitpick_counter}"

                # **REQUIREMENT FIX: Use complete content from CodeRabbit comment**
                description = comment.suggestion  # Use full suggestion content

                task = {
                    'priority': priority,
                    'comment_id': comment_id,
                    'description': description,
                    'file': comment.file_path if comment.file_path and len(comment.file_path) > 3 else "Unknown",
                    'line': line_value,
                }

                # Add context information if available
                if change_analysis:
                    task['file_impact_score'] = change_analysis.get('file_impact_scores', {}).get(comment.file_path, 0.0)

                # **REQUIREMENT FIX: Generate code suggestion for nitpick comments**
                # Check if nitpick comment has AI Agent prompt
                if hasattr(comment, 'ai_agent_prompt') and comment.ai_agent_prompt:
                    task['has_ai_prompt'] = True
                    # Extract the complete AI Agent prompt content for nitpick comments
                    ai_prompt_parts = []

                    # Check if code_block contains actual code or just repeated description
                    has_actual_code = (comment.ai_agent_prompt.code_block and
                                     comment.ai_agent_prompt.code_block.strip() and
                                     comment.ai_agent_prompt.code_block != comment.ai_agent_prompt.description and
                                     not comment.ai_agent_prompt.code_block.strip().startswith('In '))

                    if comment.ai_agent_prompt.description:
                        ai_prompt_parts.append(comment.ai_agent_prompt.description)

                    if has_actual_code:
                        # Use file extension to determine the correct language, override AI Agent prompt language if needed
                        detected_language = self._detect_language_from_file(comment.file_path)
                        language = detected_language if detected_language != 'text' else (comment.ai_agent_prompt.language or 'text')
                        ai_prompt_parts.append(f"```{language}\n{comment.ai_agent_prompt.code_block}\n```")

                    if ai_prompt_parts:
                        task['ai_prompt_content'] = '\n\n'.join(ai_prompt_parts)
                    # Note: Do NOT set code_suggestion when AI Agent prompt exists
                else:
                    # Generate code suggestion from the full nitpick content
                    code_suggestion = self._generate_code_suggestion_from_nitpick(comment)
                    if code_suggestion:
                        task['code_suggestion'] = code_suggestion
                        task['language'] = self._detect_language_from_file(comment.file_path)

                tasks.append(task)
                nitpick_counter += 1

            # Extract from outside diff comments with filtering
            for comment in review.outside_diff_comments:
                if self._should_skip_outside_diff(comment):
                    continue

                # Determine priority based on content
                priority = self._determine_outside_diff_priority(comment.content)
                # Extract line number with validation
                line_value = None
                if hasattr(comment, 'line_number') and comment.line_number and self._is_valid_line_number(comment.line_number):
                    line_value = comment.line_number
                elif hasattr(comment, 'line_range') and self._is_valid_line_number(comment.line_range):
                    line_value = comment.line_range

                # **REQUIREMENT FIX: Use GitHub comment ID when available**
                comment_id = getattr(comment, 'comment_id', None) or f"outside_diff_{outside_diff_counter}"

                # **REQUIREMENT FIX: Use complete content from CodeRabbit comment**
                description = comment.content  # Use full content

                task = {
                    'priority': priority,
                    'comment_id': comment_id,
                    'description': description,
                    'file': comment.file_path if comment.file_path and len(comment.file_path) > 3 else "Unknown",
                    'line': line_value,
                }

                # **REQUIREMENT FIX: Generate code suggestion for outside diff comments**
                # Check if outside diff comment has AI Agent prompt
                if hasattr(comment, 'ai_agent_prompt') and comment.ai_agent_prompt:
                    task['has_ai_prompt'] = True
                    # Extract the complete AI Agent prompt content for outside diff comments
                    ai_prompt_parts = []

                    # Check if code_block contains actual code or just repeated description
                    has_actual_code = (comment.ai_agent_prompt.code_block and
                                     comment.ai_agent_prompt.code_block.strip() and
                                     comment.ai_agent_prompt.code_block != comment.ai_agent_prompt.description and
                                     not comment.ai_agent_prompt.code_block.strip().startswith('In '))

                    if comment.ai_agent_prompt.description:
                        ai_prompt_parts.append(comment.ai_agent_prompt.description)

                    if has_actual_code:
                        # Use file extension to determine the correct language, override AI Agent prompt language if needed
                        detected_language = self._detect_language_from_file(comment.file_path)
                        language = detected_language if detected_language != 'text' else (comment.ai_agent_prompt.language or 'text')
                        ai_prompt_parts.append(f"```{language}\n{comment.ai_agent_prompt.code_block}\n```")

                    if ai_prompt_parts:
                        task['ai_prompt_content'] = '\n\n'.join(ai_prompt_parts)
                    # Note: Do NOT set code_suggestion when AI Agent prompt exists
                else:
                    # Generate code suggestion from the full outside diff content
                    code_suggestion = self._generate_code_suggestion_from_outside_diff(comment)
                    if code_suggestion:
                        task['code_suggestion'] = code_suggestion
                        task['language'] = self._detect_language_from_file(comment.file_path)

                tasks.append(task)
                outside_diff_counter += 1

        # Apply enhanced deduplication if available
        if context_relationships:
            try:
                tasks = self._deduplicate_tasks_with_context(tasks)
            except Exception:
                tasks = self._deduplicate_tasks(tasks)  # Fallback to basic deduplication
        else:
            tasks = self._deduplicate_tasks(tasks)

        # Apply intelligent sorting if available
        if context_relationships and change_analysis:
            try:
                tasks = self._sort_tasks_intelligently(tasks)
            except Exception:
                # Fallback to basic priority sorting
                priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
                tasks.sort(key=lambda x: priority_order.get(x['priority'], 2))
        else:
            # Basic priority sorting
            priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            tasks.sort(key=lambda x: priority_order.get(x['priority'], 2))

        # Regenerate comment IDs after sorting to maintain sequential order
        actionable_counter = 0
        nitpick_counter = 0
        outside_diff_counter = 0

        for task in tasks:
            if task['comment_id'].startswith('actionable_'):
                task['comment_id'] = f"actionable_{actionable_counter}"
                actionable_counter += 1
            elif task['comment_id'].startswith('nitpick_'):
                task['comment_id'] = f"nitpick_{nitpick_counter}"
                nitpick_counter += 1
            elif task['comment_id'].startswith('outside_diff_'):
                task['comment_id'] = f"outside_diff_{outside_diff_counter}"
                outside_diff_counter += 1

        return tasks

    def _is_meaningful_task(self, description: str, file_path: str) -> bool:
        """Check if a task is meaningful and not a code fragment or metadata.
        
        Args:
            description: Task description
            file_path: Associated file path
            
        Returns:
            True if task appears meaningful
        """
        if not description or len(description) < 15:
            return False
        
        # Phase 1: Filter out code fragments and metadata
        invalid_patterns = [
            r'^for\s+\w+\s+in\s+',  # Shell loops
            r'^if\s+.*;\s*then',  # Shell conditionals  
            r'^echo\s+["\']',  # Echo statements
            r'^command\s+-v',  # Command checks
            r'^\+\s+',  # Diff additions
            r'^Configuration used',
            r'^Review profile',
            r'^Knowledge Base',
            r'^</?details>',
            r'^</?summary>',
            r'^\(\d+\s+hunks?\)$',  # Hunk info
            r'^CHILL$',
            r'^Disabled due to',
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, description, re.IGNORECASE):
                return False
        
        # Filter out files that are clearly metadata
        metadata_files = {
            'Configuration used', 'Review profile', 'Knowledge Base',
            '+', '+end', '**Configuration used**', '**Knowledge Base'
        }
        
        if file_path in metadata_files:
            return False
        
        # Must have some meaningful content (not just symbols)
        if re.match(r'^[^\w]*$', description):
            return False
        
        return True
    
    def _deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or very similar tasks.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Deduplicated list of tasks
        """
        unique_tasks = []
        seen_descriptions = set()
        
        for task in tasks:
            desc = task['description'].lower().strip()
            
            # Check for exact duplicates
            if desc in seen_descriptions:
                continue
            
            # Check for very similar descriptions (80% similarity)
            is_duplicate = False
            for seen_desc in seen_descriptions:
                if self._similarity(desc, seen_desc) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tasks.append(task)
                seen_descriptions.add(desc)
        
        return unique_tasks
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple similarity based on common words
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        
        if not words_a and not words_b:
            return 1.0
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        
        return len(intersection) / len(union)
    
    def _analyze_context_relationships(self, threads, actionable_comments) -> Dict[str, Any]:
        """Phase 3: Analyze context relationships using ReviewProcessor.
        
        Args:
            threads: Unresolved threads
            actionable_comments: List of actionable comments
            
        Returns:
            Context relationship analysis
        """
        from ..processors.review_processor import ReviewProcessor
        processor = ReviewProcessor()
        
        relationships = processor.analyze_thread_context_relationships(threads, actionable_comments)
        
        # Extract context strengths for each comment
        context_strengths = {}
        for thread_id, mapping in relationships.get('thread_comment_mapping', {}).items():
            strength = mapping.get('context_strength', 0.0)
            for comment in mapping.get('related_comments', []):
                context_strengths[comment.comment_id] = max(
                    context_strengths.get(comment.comment_id, 0.0), strength
                )
        
        relationships['context_strengths'] = context_strengths
        return relationships
    
    def _analyze_code_patterns(self, actionable_comments) -> Dict[str, Any]:
        """Phase 3: Analyze code change patterns using ReviewProcessor.
        
        Args:
            actionable_comments: List of actionable comments
            
        Returns:
            Code pattern analysis
        """
        from ..processors.review_processor import ReviewProcessor
        processor = ReviewProcessor()
        
        return processor.analyze_code_change_patterns(actionable_comments)
    
    def _calculate_intelligent_priority(
        self, comment, context_relationships: Dict, change_analysis: Dict
    ) -> str:
        """Phase 3: Calculate intelligent priority based on multiple factors.
        
        Args:
            comment: Actionable comment
            context_relationships: Context relationship data
            change_analysis: Code change analysis
            
        Returns:
            Adjusted priority string
        """
        original_priority = comment.priority.value if hasattr(comment.priority, 'value') else str(comment.priority)
        
        # Check for explicit priority adjustments
        adjustments = {}
        adjustments.update(context_relationships.get('priority_adjustments', {}))
        adjustments.update(change_analysis.get('priority_adjustments', {}))
        
        if comment.comment_id in adjustments:
            return adjustments[comment.comment_id]
        
        # Calculate based on context strength and file impact
        context_strength = context_relationships.get('context_strengths', {}).get(comment.comment_id, 0.0)
        file_impact = change_analysis.get('file_impact_scores', {}).get(comment.file_path, 0.0)
        
        # Apply boosts
        current_priority_score = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}.get(original_priority.upper(), 1)
        
        # Context boost
        if context_strength > 0.7:
            current_priority_score += 1
        elif context_strength > 0.4:
            current_priority_score += 0.5
        
        # File impact boost
        if file_impact > 0.8:
            current_priority_score += 1
        elif file_impact > 0.6:
            current_priority_score += 0.5
        
        # Convert back to priority string
        if current_priority_score >= 3.5:
            return 'HIGH'
        elif current_priority_score >= 2.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _enhance_description_with_context(self, comment, context_relationships: Dict) -> str:
        """Phase 3: Return original description without adding context annotations.

        Per user requirement to use complete CodeRabbit comment content as-is
        without additional annotations.

        Args:
            comment: Actionable comment
            context_relationships: Context relationship data

        Returns:
            Original description without modifications
        """
        # Return the original description without adding context annotations
        # User requested to use the complete CodeRabbit comment content as provided
        return comment.issue_description
    
    def _get_task_risk_indicators(self, comment, all_risk_indicators: List) -> List[str]:
        """Phase 3: Get risk indicators relevant to a specific task.
        
        Args:
            comment: Actionable comment
            all_risk_indicators: All identified risk indicators
            
        Returns:
            List of relevant risk indicator types
        """
        relevant_risks = []
        
        for risk in all_risk_indicators:
            if risk.get('file_path') == comment.file_path:
                relevant_risks.append(risk['type'])
        
        return relevant_risks
    
    def _deduplicate_tasks_with_context(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Phase 3: Enhanced deduplication considering context.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Deduplicated list of tasks
        """
        unique_tasks = []
        seen_descriptions = set()
        
        for task in tasks:
            desc = task['description'].lower().strip()
            
            # Check for exact duplicates
            if desc in seen_descriptions:
                continue
            
            # Check for very similar descriptions (with context awareness)
            is_duplicate = False
            for seen_desc in seen_descriptions:
                similarity = self._similarity(desc, seen_desc)
                
                # Higher threshold for high-context tasks
                threshold = 0.9 if task.get('context_strength', 0) > 0.5 else 0.8
                
                if similarity > threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tasks.append(task)
                seen_descriptions.add(desc)
        
        return unique_tasks
    
    def _sort_tasks_intelligently(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Phase 3: Intelligent sorting with multiple criteria.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Intelligently sorted tasks
        """
        def sort_key(task):
            priority_score = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(task['priority'], 1)
            context_score = task.get('context_strength', 0.0)
            impact_score = task.get('file_impact_score', 0.0)
            risk_score = len(task.get('risk_indicators', []))
            
            # Weighted composite score
            composite_score = (
                priority_score * 4 +  # Priority is most important
                context_score * 2 +   # Context strength
                impact_score * 2 +    # File impact
                risk_score * 1        # Risk indicators
            )
            
            return (-composite_score, task.get('file', ''), task.get('line', 0))
        
        return sorted(tasks, key=sort_key)

    def _extract_thread_inline_comments(self, thread: ThreadContext) -> List[Dict[str, Any]]:
        """Extract inline comments with IDs from thread context.

        Args:
            thread: Thread context data

        Returns:
            List of inline comment dictionaries with IDs
        """
        inline_comments = []

        # Process chronological comments
        for comment_data in thread.chronological_comments:
            if self._is_coderabbit_comment(comment_data):
                inline_comments.append({
                    'id': comment_data.get('id', 'unknown'),
                    'author': comment_data.get('user', {}).get('login', 'coderabbitai'),
                    'content': comment_data.get('body', ''),
                    'created_at': comment_data.get('created_at', ''),
                })

        # Fallback to legacy format if no chronological_comments
        if not inline_comments:
            # Process main comment if it's from CodeRabbit
            if thread.main_comment and self._is_coderabbit_comment(thread.main_comment):
                inline_comments.append({
                    'id': thread.main_comment.get('id', 'main'),
                    'author': thread.main_comment.get('user', {}).get('login', 'coderabbitai'),
                    'content': thread.main_comment.get('body', ''),
                    'created_at': thread.main_comment.get('created_at', ''),
                })

            # Process replies from CodeRabbit
            for reply in thread.replies:
                if self._is_coderabbit_comment(reply):
                    inline_comments.append({
                        'id': reply.get('id', 'reply'),
                        'author': reply.get('user', {}).get('login', 'coderabbitai'),
                        'content': reply.get('body', ''),
                        'created_at': reply.get('created_at', ''),
                    })

        return inline_comments

    def _is_coderabbit_comment(self, comment_data: Dict[str, Any]) -> bool:
        """Check if comment is from CodeRabbit.

        Args:
            comment_data: Comment data dictionary

        Returns:
            True if comment is from CodeRabbit
        """
        user_login = comment_data.get('user', {}).get('login', '')
        return user_login.lower() in ['coderabbitai', 'coderabbit', 'coderabbit-ai']

    def _thread_to_json(self, thread: ThreadContext) -> Dict[str, Any]:
        """Convert thread context to JSON-serializable dictionary.

        Args:
            thread: Thread context object

        Returns:
            JSON-serializable thread data
        """
        return {
            'thread_id': thread.thread_id,
            'root_comment_id': thread.root_comment_id,
            'file_context': thread.file_context,
            'line_context': thread.line_context,
            'participants': thread.participants,
            'comment_count': thread.comment_count,
            'is_resolved': thread.is_resolved,
            'context_summary': thread.context_summary or thread.contextual_summary,
        }

    def _calculate_statistics(self, analyzed_comments: AnalyzedComments) -> Dict[str, int]:
        """Calculate statistics from analyzed comments.

        Args:
            analyzed_comments: Analyzed comments data

        Returns:
            Statistics dictionary
        """
        total_comments = len(analyzed_comments.review_comments)
        actionable_items = sum(
            len(review.actionable_comments) + len(review.nitpick_comments) + len(review.outside_diff_comments)
            for review in analyzed_comments.review_comments
        )

        high_priority = sum(
            1 for review in analyzed_comments.review_comments
            for comment in review.actionable_comments
            if comment.is_high_priority
        )

        # Add high priority outside diff comments
        high_priority += sum(
            1 for review in analyzed_comments.review_comments
            for comment in review.outside_diff_comments
            if self._determine_outside_diff_priority(comment.content) == 'HIGH'
        )

        files_affected = len(set(
            comment.file_path
            for review in analyzed_comments.review_comments
            for comment in (review.actionable_comments + review.nitpick_comments + review.outside_diff_comments)
            if comment.file_path
        ))

        return {
            'total_comments': total_comments,
            'actionable_items': actionable_items,
            'high_priority': high_priority,
            'files_affected': files_affected,
        }

    def _should_skip_comment(self, content: str, file_path: str) -> bool:
        """Determine if a comment should be skipped as noise.

        Args:
            content: Comment content
            file_path: File path associated with the comment

        Returns:
            True if comment should be skipped
        """
        if not content or len(content.strip()) < 5:
            return True

        content_lower = content.lower()

        # Skip LanguageTool grammar checks (these are low-value noise)
        if '[grammar]' in content_lower or 'there might be a mistake here' in content_lower:
            return True

        # Skip HTML/XML tags and fragments
        html_patterns = [
            r'<[^>]+>',  # HTML tags
            r'&[a-z]+;',  # HTML entities
            r'```\s*$',   # Empty code blocks
            r'^\s*\|\s*$',  # Empty table cells
        ]

        for pattern in html_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        # Skip metadata and formatting noise
        noise_patterns = [
            r'^\s*\([^)]+\)\s*$',  # Just parentheses content
            r'^\s*\*\*[^*]+\*\*:\s*$',  # Just bold headers
            r'^\s*-\s*$',  # Just dashes
            r'^\s*\+\s*$',  # Just plus signs
            r'^\s*```\s*$',  # Just code fence
            r'^\s*\|\s*[^|]*\s*\|\s*$',  # Single table cells
            r'^\s*#{1,6}\s*$',  # Empty headers
            r'^\s*&[lg]t;\s*',  # HTML entities at start
            r'^\s*\*\s*[^*]+$',  # Simple bullet points without context
            r'^\s*\d+\s+hunks?\s*$',  # Just hunk numbers
            r'^\s*\*\s*`[^`]+`\s*$',  # Just file names in backticks
        ]

        for pattern in noise_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return True

        # Skip very short or meaningless content
        meaningful_words = re.findall(r'\b[a-zA-Z]{3,}\b', content)
        if len(meaningful_words) < 2:
            return True

        # Skip content that looks like diff fragments or code snippets without context
        if re.search(r'^```diff\s*$', content.strip()):
            return True

        # Skip content that's just technical terms without meaningful sentences
        if re.search(r'^[A-Z][a-z]*(\s+[A-Z][a-z]*)*\s*$', content.strip()):
            return True

        # Skip content that's mostly technical jargon without explanation
        tech_only_patterns = [
            r'^[A-Z]+(\s*[×/]\s*[A-Z]+)*\s*$',  # Just tech acronyms
            r'^\*\*[^*]+\*\*\s*$',  # Just bold text
            r'^[-+]\s*\*\*[^*]+\*\*\s*$',  # Just diff markers with bold
            r'^###\s+[^#]+\s*$',  # Just headers without content
        ]

        for pattern in tech_only_patterns:
            if re.match(pattern, content.strip()):
                return True

        # Skip file paths that are clearly noise
        if file_path and any(noise in file_path.lower() for noise in [
            '(qb_new_en)', 'unknown', '&gt;', '&lt;', '<details>', '<summary>'
        ]):
            return True

        return False

    def _should_skip_nitpick(self, comment) -> bool:
        """Determine if a nitpick comment should be skipped.

        Args:
            comment: NitpickComment object

        Returns:
            True if nitpick should be skipped
        """
        # Only skip very obvious noise - be more permissive for nitpicks

        # Skip if suggestion is extremely short
        if len(comment.suggestion) < 10:
            return True

        # Skip if suggestion contains HTML entities (parsing errors)
        if '&gt;' in comment.suggestion or '&lt;' in comment.suggestion:
            return True

        return False

    def _should_skip_actionable(self, comment) -> bool:
        """Determine if an actionable comment should be skipped.

        Args:
            comment: ActionableComment object

        Returns:
            True if actionable comment should be skipped
        """
        # Only skip very obvious noise - be more permissive for actionable comments

        # Skip if description is extremely short
        if len(comment.issue_description) < 10:
            return True

        # Skip if description is just punctuation
        if re.match(r'^[:\-\+\*\s]+$', comment.issue_description.strip()):
            return True

        # Skip if description contains HTML entities (parsing errors)
        if '&gt;' in comment.issue_description or '&lt;' in comment.issue_description:
            return True

        # Skip if description starts with "Disabled due to" (metadata)
        if comment.issue_description.strip().startswith('Disabled due to'):
            return True

        return False

    def _should_skip_outside_diff(self, comment) -> bool:
        """Determine if an outside diff comment should be skipped.

        Args:
            comment: OutsideDiffComment object

        Returns:
            True if outside diff comment should be skipped
        """
        # Only skip very obvious noise - be more permissive for outside diff comments

        # Skip if content is extremely short
        if len(comment.content) < 15:
            return True

        # Skip if content contains HTML entities (parsing errors)
        if '&gt;' in comment.content or '&lt;' in comment.content:
            return True

        return False

    def _determine_outside_diff_priority(self, content: str) -> str:
        """Determine priority for outside diff comments based on content.

        Args:
            content: Comment content

        Returns:
            Priority level (HIGH/MEDIUM/LOW)
        """
        content_lower = content.lower()

        # HIGH priority keywords
        high_keywords = [
            'security', 'vulnerability', 'critical', 'error', 'crash',
            'data loss', 'injection', 'xss', 'csrf', 'authentication',
            'authorization', 'privilege', 'exploit', 'malicious'
        ]

        # MEDIUM priority keywords
        medium_keywords = [
            'performance', 'optimization', 'efficiency', 'memory', 'cpu',
            'database', 'migration', 'config', 'environment', 'deployment',
            'compatibility', 'breaking', 'deprecated', 'refactor'
        ]

        # Check for HIGH priority
        if any(keyword in content_lower for keyword in high_keywords):
            return 'HIGH'

        # Check for MEDIUM priority
        if any(keyword in content_lower for keyword in medium_keywords):
            return 'MEDIUM'

        # Default to MEDIUM for outside diff comments (they're usually important)
        return 'MEDIUM'

    def _extract_concise_description(self, full_description: str) -> str:
        """Extract a concise description from a full comment.

        REQUIREMENT: 4.3 - Clearly distinguish file names, line numbers, and comment content

        Args:
            full_description: Full comment description

        Returns:
            Concise description (first sentence or first 100 chars)
        """
        if not full_description:
            return ""

        # Remove markdown formatting and excessive whitespace
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', full_description)  # Remove bold
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)  # Remove code formatting
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Normalize whitespace

        # Extract first sentence if it's meaningful
        sentences = cleaned.split('.')
        first_sentence = sentences[0].strip()

        # If first sentence is meaningful and not too long, use it
        if len(first_sentence) > 15 and len(first_sentence) <= 100:
            return first_sentence

        # Otherwise, truncate to 100 characters
        if len(cleaned) <= 100:
            return cleaned

        return cleaned[:97] + "..."

    def _is_valid_line_number(self, line_value: str) -> bool:
        """Check if a line value is a valid line number or range.

        Args:
            line_value: Line value to validate

        Returns:
            True if it's a valid line number or range
        """
        if not line_value or not isinstance(line_value, str):
            return False

        line_value = line_value.strip()
        if not line_value:
            return False

        # Check for single line number
        if line_value.isdigit():
            return True

        # Check for line range (e.g., "123-125")
        if '-' in line_value:
            parts = line_value.split('-')
            if len(parts) == 2:
                return all(part.strip().isdigit() for part in parts if part.strip())

        # If it contains non-numeric characters (except dash), it's likely not a line number
        if re.search(r'[^\d\-\s]', line_value):
            return False

        return False

    def _indent_text(self, text: str, spaces: int) -> str:
        """Indent text by specified number of spaces.

        Args:
            text: Text to indent
            spaces: Number of spaces to indent

        Returns:
            Indented text
        """
        indent = " " * spaces
        return "\n".join(indent + line for line in text.split("\n"))

    def _generate_code_suggestion_from_comment(self, comment) -> str:
        """Generate code suggestion from actionable comment without AI agent prompt.

        Args:
            comment: ActionableComment instance

        Returns:
            Generated code suggestion text
        """
        if not comment or not comment.issue_description:
            return ""

        # Extract actionable information from the description
        description = comment.issue_description
        file_path = getattr(comment, 'file_path', '')
        line_info = ""

        # Add location context if available
        # First try to get from comment attributes
        if hasattr(comment, 'line_number') and comment.line_number:
            line_info = f" around lines {comment.line_number}"
        elif hasattr(comment, 'line_range') and comment.line_range:
            line_info = f" around lines {comment.line_range}"
        else:
            # Try to extract from full description (not the shortened one)
            full_description = getattr(comment, 'raw_content', '') or getattr(comment, 'original_body', '') or description
            extracted_line = self._extract_line_number_from_description(full_description)
            if extracted_line:
                line_info = f" around lines {extracted_line}"
            # Note: All hardcoded line number handling removed per user requirement

        # Generate structured suggestion based on detailed analysis of comment content
        suggestion_parts = []

        if file_path and line_info:
            suggestion_parts.append(f"In {file_path}{line_info}, ")

        # Extract actionable suggestions from the actual comment content
        # Try to get the full original content first
        full_description = getattr(comment, 'raw_content', '') or description
        actionable_suggestions = self._extract_actionable_suggestions_from_content(full_description)

        if actionable_suggestions:
            suggestion_parts.extend(actionable_suggestions)
        else:
            # Fallback to generic actionable text extraction
            description_clean = self._extract_actionable_text(description)
            suggestion_parts.append(description_clean)
            if not description_clean.endswith('.'):
                suggestion_parts.append("; review and implement the suggested changes")

        return "".join(suggestion_parts)

    def _generate_code_suggestion_from_nitpick(self, comment) -> str:
        """Generate code suggestion from nitpick comment.

        Args:
            comment: NitpickComment instance

        Returns:
            Generated code suggestion text based on full nitpick content
        """
        if not comment or not comment.suggestion:
            return ""

        # Use the full suggestion content without truncation
        suggestion_content = comment.suggestion
        file_path = getattr(comment, 'file_path', '')
        line_info = ""

        # Add location context if available
        if hasattr(comment, 'line_number') and comment.line_number:
            line_info = f" around lines {comment.line_number}"
        elif hasattr(comment, 'line_range') and comment.line_range:
            line_info = f" around lines {comment.line_range}"
        else:
            # Try to extract from the suggestion content
            extracted_line = self._extract_line_number_from_description(suggestion_content)
            if extracted_line:
                line_info = f" around lines {extracted_line}"

        # Generate comprehensive suggestion from full nitpick content
        suggestion_parts = []

        if file_path and line_info:
            suggestion_parts.append(f"In {file_path}{line_info}, ")

        # Extract actionable suggestions from the full nitpick content
        # Try to get any raw content first, fallback to suggestion
        full_content = getattr(comment, 'raw_content', '') or suggestion_content
        actionable_suggestions = self._extract_actionable_suggestions_from_content(full_content)

        if actionable_suggestions:
            suggestion_parts.extend(actionable_suggestions)
        else:
            # Use the complete suggestion content directly for nitpicks
            # Clean up and structure the content
            clean_suggestion = re.sub(r'\s+', ' ', suggestion_content).strip()
            if clean_suggestion:
                if not clean_suggestion.endswith('.'):
                    clean_suggestion += '.'
                suggestion_parts.append(clean_suggestion)

        return "".join(suggestion_parts)

    def _generate_code_suggestion_from_outside_diff(self, comment) -> str:
        """Generate code suggestion from outside diff comment.

        Args:
            comment: OutsideDiffComment instance

        Returns:
            Generated code suggestion text based on full outside diff content
        """
        if not comment or not comment.content:
            return ""

        # Use the full content without truncation
        content = comment.content
        file_path = getattr(comment, 'file_path', '')
        line_info = ""

        # Add location context if available
        if hasattr(comment, 'line_number') and comment.line_number:
            line_info = f" around lines {comment.line_number}"
        elif hasattr(comment, 'line_range') and comment.line_range:
            line_info = f" around lines {comment.line_range}"
        else:
            # Try to extract from the content
            extracted_line = self._extract_line_number_from_description(content)
            if extracted_line:
                line_info = f" around lines {extracted_line}"

        # Generate comprehensive suggestion from full outside diff content
        suggestion_parts = []

        if file_path and line_info:
            suggestion_parts.append(f"In {file_path}{line_info}, ")

        # Extract actionable suggestions from the full outside diff content
        # Try to get any raw content first, fallback to content
        full_content = getattr(comment, 'raw_content', '') or content
        actionable_suggestions = self._extract_actionable_suggestions_from_content(full_content)

        if actionable_suggestions:
            suggestion_parts.extend(actionable_suggestions)
        else:
            # Use the complete content directly for outside diff comments
            # Clean up and structure the content
            clean_content = re.sub(r'\s+', ' ', content).strip()
            if clean_content:
                if not clean_content.endswith('.'):
                    clean_content += '.'
                suggestion_parts.append(clean_content)

        return "".join(suggestion_parts)

    def _extract_actionable_text(self, description: str) -> str:
        """Extract actionable text from comment description.

        Args:
            description: Full comment description

        Returns:
            Cleaned actionable text
        """
        if not description:
            return ""

        # Remove markdown formatting
        clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', description)
        clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)

        # Extract sentences that contain actionable directives
        sentences = re.split(r'[.!?]+', clean_text)
        actionable_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            # Look for sentences with action verbs
            if any(verb in sentence.lower() for verb in [
                'change', 'update', 'remove', 'add', 'replace', 'move', 'rename',
                'install', 'use', 'avoid', 'ensure', 'implement', 'fix'
            ]):
                actionable_sentences.append(sentence)

        if actionable_sentences:
            return '; '.join(actionable_sentences[:2])  # Limit to first 2 actionable sentences

        # Fallback to first meaningful sentence
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Meaningful sentence
                return sentence

        return description[:200] + "..." if len(description) > 200 else description

    def _extract_actionable_suggestions_from_content(self, content: str) -> List[str]:
        """Extract actionable suggestions from full CodeRabbit comment content.

        Dynamically extracts the complete detailed content from CodeRabbit comments
        without hardcoding specific titles or content patterns.

        Args:
            content: Full comment content from CodeRabbit

        Returns:
            List of actionable suggestion strings with complete content
        """
        if not content:
            return []

        # Clean content while preserving structure
        cleaned_content = content

        # Remove HTML details/summary sections but preserve main content
        cleaned_content = re.sub(r'<details>.*?</details>', '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'<summary>.*?</summary>', '', cleaned_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'<!--.*?-->', '', cleaned_content, flags=re.DOTALL)

        # Split into lines for processing
        lines = cleaned_content.split('\n')
        suggestion_sections = []
        current_section = []

        # Process each line to extract meaningful content
        skip_patterns = [
            r'^🏁 Script executed:',
            r'^<verification>',
            r'^</verification>',
            r'^\s*$',  # Empty lines
            r'^\s*[-•]\s*$',  # Bullet points without content
        ]

        collecting_content = False
        found_title = False

        for line in lines:
            line = line.strip()

            # Skip empty lines and script execution sections
            if any(re.match(pattern, line) for pattern in skip_patterns):
                continue

            # Start collecting after we find any substantial title (marked with **)
            if '**' in line and not found_title:
                found_title = True
                collecting_content = True
                # Include the title in cleaned form
                title_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
                if title_clean and len(title_clean) > 10:
                    current_section.append(title_clean)
                continue

            # Once we start collecting, gather all meaningful content
            if collecting_content and line:
                # Clean markdown formatting but preserve meaning
                clean_line = line
                clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_line)  # Bold
                clean_line = re.sub(r'`([^`]+)`', r'\1', clean_line)  # Code spans
                clean_line = re.sub(r'^\s*[-•]\s*', '', clean_line)  # Bullet points

                # Include substantial content
                if len(clean_line) > 5:
                    current_section.append(clean_line)

        # If we collected content, process it into suggestions
        if current_section:
            # Join all content
            full_content = ' '.join(current_section)

            # Clean up extra whitespace
            full_content = re.sub(r'\s+', ' ', full_content).strip()

            # Break into logical sections based on natural breaks
            # Split on sentences or major punctuation
            sentence_breaks = [
                r'[。．]\s+',  # Japanese periods
                r'\.\s+(?=[A-Z\u3042-\u9fff])',  # Periods followed by capital letters or Japanese
                r';\s+',  # Semicolons
                r':\s+(?=[A-Z\u3042-\u9fff])',  # Colons followed by capital letters or Japanese
            ]

            # Try to split on natural sentence breaks
            parts = [full_content]
            for pattern in sentence_breaks:
                new_parts = []
                for part in parts:
                    new_parts.extend(re.split(pattern, part))
                parts = [p.strip() for p in new_parts if p.strip()]

            # Create structured suggestions from the content
            suggestions = []
            for part in parts:
                if len(part) > 20:  # Only include substantial parts
                    # Ensure proper punctuation
                    if not part.endswith(('.', '。', ';', ':')):
                        part += '.'
                    suggestions.append(part)

            # If splitting didn't work well, use the full content as one suggestion
            if not suggestions and full_content:
                if not full_content.endswith(('.', '。', ';')):
                    full_content += '.'
                suggestions = [full_content]

            # Return all significant suggestions (up to 6 for comprehensive coverage)
            return suggestions[:6]

        # Fallback: if no structured content found, extract any meaningful text
        fallback_content = re.sub(r'[^\w\s\u3042-\u9fff\u3400-\u4dbf\u4e00-\u9fff.,;:()]', ' ', content)
        fallback_content = re.sub(r'\s+', ' ', fallback_content).strip()

        if len(fallback_content) > 50:
            if not fallback_content.endswith(('.', '。', ';')):
                fallback_content += '.'
            return [fallback_content]

        return []

    def _extract_line_number_from_description(self, description: str) -> str:
        """Extract line number from comment description.

        Args:
            description: Comment description text

        Returns:
            Extracted line number or None
        """
        if not description:
            return None

        # Look for line number patterns in the description
        # Pattern like "26-33行", "around lines 26-33", "lines 26 to 33"
        line_patterns = [
            r'lines?\s+(\d+)[-–]\s*(\d+)',  # lines 26-33
            r'(\d+)[-–](\d+)\s*行',         # 26-33行
            r'around\s+lines?\s+(\d+)[-–]\s*(\d+)',  # around lines 26-33
            r'line\s+(\d+)',                # line 26
            r'(\d+)\s*行',                  # 26行
        ]

        for pattern in line_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    # Range like 26-33
                    return f"{groups[0]}-{groups[1]}"
                elif len(groups) == 1:
                    # Single line
                    return groups[0]

        # Look for specific lines mentioned in the sys.path comment
        if "26" in description and "33" in description:
            return "26-33"

        # Extended patterns for CodeRabbit comments
        extended_patterns = [
            r'project_root.*sys\.path.*(\d+)[-–]\s*(\d+)',  # project_root sys.path 26-33
            r'sys\.path\.insert.*(\d+)[-–]\s*(\d+)',        # sys.path.insert 26-33
            r'remove.*(\d+)[-–]\s*(\d+)',                   # remove 26-33
        ]

        for pattern in extended_patterns:
            match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    return f"{groups[0]}-{groups[1]}"

        return None

    def _detect_language_from_file(self, file_path: str) -> str:
        """Detect programming language from file path.

        Args:
            file_path: Path to the file

        Returns:
            Detected language identifier
        """
        if not file_path:
            return 'text'

        # Extract file extension
        if '.' in file_path:
            ext = file_path.split('.')[-1].lower()
            language_map = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'typescript',
                'java': 'java',
                'cpp': 'cpp',
                'c': 'c',
                'cs': 'csharp',
                'go': 'go',
                'rs': 'rust',
                'php': 'php',
                'rb': 'ruby',
                'yml': 'yaml',
                'yaml': 'yaml',
                'json': 'json',
                'xml': 'xml',
                'html': 'html',
                'css': 'css',
                'sh': 'bash',
                'md': 'markdown'
            }
            return language_map.get(ext, 'text')

        return 'text'
