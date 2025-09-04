"""LLM Instruction Formatter for CodeRabbit comments.

This formatter creates XML-structured instruction prompts optimized for 
LLM consumption following Claude 4 best practices.
"""

import json
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
        
        # Primary tasks
        primary_tasks = self._extract_primary_tasks(analyzed_comments)
        if primary_tasks:
            instructions.append("  <primary_tasks>")
            for task in primary_tasks:
                instructions.append(f"    <task priority='{task['priority']}' comment_id='{task.get('comment_id', 'N/A')}'>")
                instructions.append(f"      <description>{escape(task['description'])}</description>")
                instructions.append(f"      <file>{escape(task['file'])}</file>")
                if task.get('line'):
                    instructions.append(f"      <line>{escape(str(task['line']))}</line>")
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
        """Extract primary tasks from analyzed comments.
        
        Args:
            analyzed_comments: Analyzed comments data
            
        Returns:
            List of primary task dictionaries
        """
        tasks = []
        
        # Extract from review comments (actionable comments)
        for review in analyzed_comments.review_comments:
            for comment in review.actionable_comments:
                task = {
                    'priority': comment.priority.value if hasattr(comment.priority, 'value') else str(comment.priority),
                    'comment_id': comment.comment_id,
                    'description': comment.issue_description,
                    'file': comment.file_path,
                    'line': comment.line_number,
                }
                
                # Add AI code suggestion if available
                if comment.ai_agent_prompt and comment.ai_agent_prompt.code_block:
                    task['code_suggestion'] = comment.ai_agent_prompt.code_block
                    task['language'] = comment.ai_agent_prompt.language or 'text'
                
                tasks.append(task)
            
            # Extract from nitpick comments
            for comment in review.nitpick_comments:
                task = {
                    'priority': 'LOW',  # Nitpicks are typically low priority
                    'comment_id': f"nitpick_{len(tasks)}",
                    'description': f"Nitpick: {comment.suggestion}",
                    'file': comment.file_path,
                    'line': comment.line_range,
                }
                
                tasks.append(task)
        
        # Sort by priority (HIGH → MEDIUM → LOW)
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        tasks.sort(key=lambda x: priority_order.get(x['priority'], 2))
        
        return tasks

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