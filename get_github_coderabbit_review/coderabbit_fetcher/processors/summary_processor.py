"""Summary comment processor for extracting CodeRabbit summaries."""

import re
from typing import List, Optional, Dict, Any

from ..models import SummaryComment, ChangeEntry
from ..exceptions import CommentParsingError


class SummaryProcessor:
    """Processes CodeRabbit summary comments to extract structured information."""
    
    def __init__(self):
        """Initialize the summary processor."""
        self.summary_patterns = [
            r"#+\s*Summary\s+by\s+CodeRabbit",
            r"## Summary",
            r"# Summary",
            r"Summary by CodeRabbit",
            r"## 📋 Summary",
            r"🤖 Summary by CodeRabbit",
            r"#+\s*サマリー\s+by\s+CodeRabbit",
            r"## サマリー",
            r"# サマリー",
            r"サマリー by CodeRabbit",
            r"## 📋 サマリー",
            r"🤖 サマリー by CodeRabbit"
        ]
    
    def process_summary_comment(self, comment: Dict[str, Any]) -> SummaryComment:
        """Process a CodeRabbit summary comment.
        
        Args:
            comment: Raw comment data from GitHub API
            
        Returns:
            SummaryComment object with extracted information
            
        Raises:
            CommentParsingError: If comment cannot be processed
        """
        try:
            body = comment.get("body", "")
            
            if not self.is_summary_comment(body):
                raise CommentParsingError(
                    "Comment does not appear to be a CodeRabbit summary"
                )
            
            # Extract different sections from the summary
            new_features = self._extract_new_features(body)
            documentation_changes = self._extract_documentation_changes(body)
            test_changes = self._extract_test_changes(body)
            walkthrough = self._extract_walkthrough(body)
            changes_table = self._extract_changes_table(body)
            sequence_diagram = self._extract_sequence_diagram(body)
            
            return SummaryComment(
                new_features=new_features,
                documentation_changes=documentation_changes,
                test_changes=test_changes,
                walkthrough=walkthrough,
                changes_table=changes_table,
                sequence_diagram=sequence_diagram,
                raw_content=body
            )
            
        except Exception as e:
            raise CommentParsingError(f"Failed to process summary comment: {str(e)}") from e
    
    def _is_summary_comment(self, body: str) -> bool:
        """Check if the comment body contains a CodeRabbit summary.
        
        Args:
            body: Comment body text
            
        Returns:
            True if this is a summary comment
        """
        body_lines = body.lower()
        return any(
            re.search(pattern, body_lines, re.IGNORECASE)
            for pattern in self.summary_patterns
        )

    def is_summary_comment(self, body: str) -> bool:
        """Public API to check if the comment body contains a CodeRabbit summary.
        
        Args:
            body: Comment body text
            
        Returns:
            True if this is a summary comment
        """
        return self._is_summary_comment(body)
    
    def _extract_new_features(self, content: str) -> List[str]:
        """Extract new features from summary content.
        
        Args:
            content: Summary comment body
            
        Returns:
            List of new features mentioned
        """
        features = []
        
        # Common patterns for new features
        feature_patterns = [
            r"### New features?\s*\n(.*?)(?=\n###|\n##|\n---|\Z)",
            r"## New features?\s*\n(.*?)(?=\n##|\n---|\Z)",
            r"#### New features?\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
            r"#### ✨ New features?\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
            r"- \*\*New features?\*\*:?\s*(.*?)(?=\n-|\n##|\Z)"
        ]
        
        for pattern in feature_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section = match.group(1).strip()
                features.extend(self._parse_bullet_points(section))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_features = []
        for feature in features:
            if feature not in seen:
                seen.add(feature)
                unique_features.append(feature)
        
        return unique_features
    
    def _extract_documentation_changes(self, content: str) -> List[str]:
        """Extract documentation changes from summary content.
        
        Args:
            content: Summary comment body
            
        Returns:
            List of documentation changes mentioned
        """
        doc_changes = []
        
        # Common patterns for documentation changes
        doc_patterns = [
            r"### Documentation\s*\n(.*?)(?=\n###|\n##|\n---|\Z)",
            r"## Documentation\s*\n(.*?)(?=\n##|\n---|\Z)",
            r"#### Documentation\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
            r"#### 📚 Documentation\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
            r"- \*\*Documentation\*\*:?\s*(.*?)(?=\n-|\n##|\Z)"
        ]
        
        for pattern in doc_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section = match.group(1).strip()
                doc_changes.extend(self._parse_bullet_points(section))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_changes = []
        for change in doc_changes:
            if change not in seen:
                seen.add(change)
                unique_changes.append(change)
        
        return unique_changes
    
    def _extract_test_changes(self, content: str) -> List[str]:
        """Extract test changes from summary content.
        
        Args:
            content: Summary comment body
            
        Returns:
            List of test changes mentioned
        """
        test_changes = []
        
        # Common patterns for test changes
        test_patterns = [
            r"### Tests?\s*\n(.*?)(?=\n###|\n##|\n---|\Z)",
            r"## Tests?\s*\n(.*?)(?=\n##|\n---|\Z)",
            r"#### Tests?\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
            r"#### 🧪 Tests?\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
            r"- \*\*Tests?\*\*:?\s*(.*?)(?=\n-|\n##|\Z)"
        ]
        
        for pattern in test_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                section = match.group(1).strip()
                test_changes.extend(self._parse_bullet_points(section))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_changes = []
        for change in test_changes:
            if change not in seen:
                seen.add(change)
                unique_changes.append(change)
        
        return unique_changes
    
    def _extract_walkthrough(self, content: str) -> str:
        """Extract walkthrough section from summary content.
        
        Args:
            content: Summary comment body
            
        Returns:
            Walkthrough text or empty string if not found
        """
        # Common patterns for walkthrough
        walkthrough_patterns = [
            r"### Walkthrough\s*\n(.*?)(?=\n###|\n##|\n---|\Z)",
            r"## Walkthrough\s*\n(.*?)(?=\n##|\n---|\Z)",
            r"#### Walkthrough\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
            r"#### 🚶 Walkthrough\s*\n(.*?)(?=\n####|\n###|\n##|\Z)",
        ]
        
        for pattern in walkthrough_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_changes_table(self, content: str) -> List[ChangeEntry]:
        """Extract changes table from summary content.
        
        Args:
            content: Summary comment body
            
        Returns:
            List of ChangeEntry objects
        """
        changes = []
        
        # Look for markdown tables - simpler approach
        # Find lines that look like table rows
        lines = content.split('\n')
        table_lines = []
        current_table = []
        in_code_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check for fenced code block markers
            if line_stripped.startswith("```"):
                in_code_block = not in_code_block
                # If we're entering a code block and have an open table, close it
                if in_code_block and len(current_table) >= 2:
                    table_lines.append(current_table)
                    current_table = []
                continue
            
            # Skip table detection inside code blocks
            if in_code_block:
                continue
                
            if line_stripped and '|' in line_stripped and line_stripped.count('|') >= 2:
                current_table.append(line_stripped)
            else:
                if len(current_table) >= 2:  # At least header + one data row
                    table_lines.append(current_table)
                current_table = []
        
        # Don't forget the last table (if not in code block)
        if not in_code_block and len(current_table) >= 2:
            table_lines.append(current_table)
        
        # Process each table
        for table_rows in table_lines:
            self._process_table_rows(table_rows, changes)
        
        return changes
    
    def _process_table_rows(self, rows: List[str], changes: List[ChangeEntry]) -> None:
        """Process table rows to extract change entries.
        
        Args:
            rows: List of table row strings
            changes: List to append ChangeEntry objects to
        """
        if len(rows) < 2:
            return
            
        # Skip header row and potential separator row
        data_start = 1
        if len(rows) > 1:
            # Check if any row looks like a separator (contains mostly dashes, pipes, spaces, colons)
            for i in range(1, min(3, len(rows))):  # Check first few rows after header
                if re.match(r'^\s*\|[\s\-:|]+\|\s*$', rows[i]):
                    data_start = i + 1
                    break
        
        for row in rows[data_start:]:
            cells = [cell.strip() for cell in row.split('|')]
            # Remove empty cells from start/end
            while cells and not cells[0]:
                cells.pop(0)
            while cells and not cells[-1]:
                cells.pop()
            
            if len(cells) >= 2:
                cohort_or_files = self._clean_table_cell(cells[0])
                summary = self._clean_table_cell(cells[1])
                
                # Skip separator rows (containing only dashes, colons, spaces)
                if (cohort_or_files and summary and 
                    not re.match(r'^[\s\-:]+$', cohort_or_files) and 
                    not re.match(r'^[\s\-:]+$', summary)):
                    changes.append(ChangeEntry(
                        cohort_or_files=cohort_or_files,
                        summary=summary
                    ))
    
    def _extract_sequence_diagram(self, content: str) -> Optional[str]:
        """Extract sequence diagram from summary content.
        
        Args:
            content: Summary comment body
            
        Returns:
            Sequence diagram text or None if not found
        """
        # Look for mermaid sequence diagrams
        mermaid_patterns = [
            r"```mermaid\s*\n(sequenceDiagram.*?)```",
            r"```\s*mermaid\s*\n(sequenceDiagram.*?)```",
            r"```sequence\s*\n(.*?)```"
        ]
        
        for pattern in mermaid_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Look for other diagram formats
        diagram_patterns = [
            r"```\s*diagram\s*\n(.*?)```",
            r"```\s*flow\s*\n(.*?)```",
            r"```\s*graph\s*\n(.*?)```"
        ]
        
        for pattern in diagram_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                diagram_content = match.group(1).strip()
                # Check if it looks like a sequence diagram
                if any(keyword in diagram_content.lower() for keyword in 
                       ['sequence', 'participant', 'actor', '->', 'activate', 'deactivate']):
                    return diagram_content
        
        return None
    
    def _parse_bullet_points(self, section: str) -> List[str]:
        """Parse bullet points from a section of text.
        
        Args:
            section: Text section containing bullet points
            
        Returns:
            List of bullet point items
        """
        if not section:
            return []
        
        items = []
        
        # Match different bullet point formats
        bullet_patterns = [
            r"^[-*+]\s+(.+)$",  # - item, * item, + item
            r"^\d+\.\s+(.+)$",  # 1. item, 2. item
            r"^[•·]\s+(.+)$",   # • item, · item
        ]
        
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match:
                    item = match.group(1).strip()
                    # Remove markdown formatting
                    item = re.sub(r'\*\*(.*?)\*\*', r'\1', item)  # **bold**
                    item = re.sub(r'\*(.*?)\*', r'\1', item)      # *italic*
                    item = re.sub(r'`(.*?)`', r'\1', item)        # `code`
                    
                    if item:
                        items.append(item)
                    break
            else:
                # If it's not a bullet point but looks like content, add it
                if len(line) > 10 and not line.startswith('#'):
                    items.append(line)
        
        return items
    
    def _clean_table_cell(self, cell: str) -> str:
        """Clean table cell content.
        
        Args:
            cell: Raw table cell content
            
        Returns:
            Cleaned cell content
        """
        # Remove markdown formatting
        cell = re.sub(r'\*\*(.*?)\*\*', r'\1', cell)  # **bold**
        cell = re.sub(r'\*(.*?)\*', r'\1', cell)      # *italic*
        cell = re.sub(r'`(.*?)`', r'\1', cell)        # `code`
        cell = re.sub(r'\[(.*?)\]\([^)]*\)', r'\1', cell)  # [text](link)
        
        return cell.strip()
    
    def has_summary_content(self, content: str) -> bool:
        """Check if content contains any summary-like information.
        
        Args:
            content: Comment content to check
            
        Returns:
            True if content appears to be a summary
        """
        summary_indicators = [
            "summary", "walkthrough", "changes", "new features",
            "documentation", "tests", "overview", "highlights"
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in summary_indicators)
