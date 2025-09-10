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
        
        # Primary tasks with Phase 3 enhancements
        primary_tasks = self._extract_primary_tasks(analyzed_comments)
        if primary_tasks:
            instructions.append("  <primary_tasks>")
            for task in primary_tasks:
                # Phase 3: Enhanced task attributes
                task_attrs = f"priority='{task['priority']}' comment_id='{task.get('comment_id', 'N/A')}'"
                
                # Add context information
                if task.get('context_strength', 0.0) > 0:
                    task_attrs += f" context_strength='{task['context_strength']:.2f}'"
                
                if task.get('file_impact_score', 0.0) > 0:
                    task_attrs += f" file_impact='{task['file_impact_score']:.2f}'"
                
                instructions.append(f"    <task {task_attrs}>")
                instructions.append(f"      <description>{escape(task['description'])}</description>")
                instructions.append(f"      <file>{escape(task['file'])}</file>")
                if task.get('line'):
                    instructions.append(f"      <line>{escape(str(task['line']))}</line>")
                
                # Phase 3: Risk indicators
                if task.get('risk_indicators'):
                    instructions.append("      <risk_indicators>")
                    for risk in task['risk_indicators']:
                        instructions.append(f"        <risk_type>{escape(risk)}</risk_type>")
                    instructions.append("      </risk_indicators>")
                
                if task.get('code_suggestion'):
                    instructions.append(f"      <code_suggestion language='{task.get('language', 'text')}'>")
                    instructions.append(f"{self._indent_text(escape(task['code_suggestion']), 8)}")
                    instructions.append("      </code_suggestion>")
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
        """Extract primary tasks from analyzed comments with Phase 3 intelligent enhancements.
        
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
        
        # Phase 3: Perform intelligent context analysis
        context_relationships = self._analyze_context_relationships(
            analyzed_comments.unresolved_threads, all_actionable_comments
        )
        
        # Phase 3: Analyze code change patterns
        change_analysis = self._analyze_code_patterns(all_actionable_comments)
        
        # Extract from review comments (actionable comments)
        for review in analyzed_comments.review_comments:
            for comment in review.actionable_comments:
                if self._is_meaningful_task(comment.issue_description, comment.file_path):
                    # Phase 3: Apply intelligent priority adjustments
                    adjusted_priority = self._calculate_intelligent_priority(
                        comment, context_relationships, change_analysis
                    )
                    
                    task = {
                        'priority': adjusted_priority,
                        'comment_id': comment.comment_id,
                        'description': self._enhance_description_with_context(comment, context_relationships),
                        'file': comment.file_path,
                        'line': comment.line_number,
                        'context_strength': context_relationships.get('context_strengths', {}).get(comment.comment_id, 0.0),
                        'file_impact_score': change_analysis.get('file_impact_scores', {}).get(comment.file_path, 0.0)
                    }
                    
                    # Add AI code suggestion if available
                    if comment.ai_agent_prompt and comment.ai_agent_prompt.code_block:
                        task['code_suggestion'] = comment.ai_agent_prompt.code_block
                        task['language'] = comment.ai_agent_prompt.language or 'text'
                    
                    # Phase 3: Add risk indicators
                    task['risk_indicators'] = self._get_task_risk_indicators(
                        comment, change_analysis.get('risk_indicators', [])
                    )
                    
                    tasks.append(task)
            
            # Extract from nitpick comments (with enhanced filtering)
            for comment in review.nitpick_comments:
                if self._is_meaningful_task(comment.suggestion, comment.file_path):
                    # Phase 3: Nitpicks can be upgraded based on context
                    file_impact = change_analysis.get('file_impact_scores', {}).get(comment.file_path, 0.0)
                    priority = 'MEDIUM' if file_impact > 0.7 else 'LOW'
                    
                    task = {
                        'priority': priority,
                        'comment_id': f"nitpick_{len(tasks)}",
                        'description': f"Nitpick: {comment.suggestion}",
                        'file': comment.file_path,
                        'line': comment.line_range,
                        'context_strength': 0.0,
                        'file_impact_score': file_impact
                    }
                    
                    tasks.append(task)
        
        # Phase 3: Enhanced deduplication with context awareness
        tasks = self._deduplicate_tasks_with_context(tasks)
        
        # Phase 3: Intelligent sorting with multiple criteria
        tasks = self._sort_tasks_intelligently(tasks)
        
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
        """Phase 3: Enhance description with context information.
        
        Args:
            comment: Actionable comment
            context_relationships: Context relationship data
            
        Returns:
            Enhanced description
        """
        description = comment.issue_description
        
        # Find related threads
        related_threads = []
        for thread_id, mapping in context_relationships.get('thread_comment_mapping', {}).items():
            if comment in mapping.get('related_comments', []):
                related_threads.append(thread_id)
        
        if related_threads:
            thread_count = len(related_threads)
            description += f" (Related to {thread_count} discussion thread{'s' if thread_count > 1 else ''})"
        
        return description
    
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
            len(review.actionable_comments)
            for review in analyzed_comments.review_comments
        )
        
        high_priority = sum(
            1 for review in analyzed_comments.review_comments
            for comment in review.actionable_comments
            if comment.is_high_priority
        )
        
        files_affected = len(set(
            comment.file_path
            for review in analyzed_comments.review_comments
            for comment in review.actionable_comments
        ))
        
        return {
            'total_comments': total_comments,
            'actionable_items': actionable_items,
            'high_priority': high_priority,
            'files_affected': files_affected,
        }

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