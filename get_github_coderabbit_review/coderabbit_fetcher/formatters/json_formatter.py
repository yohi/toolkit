"""
JSON formatter for CodeRabbit Comment Fetcher.
"""

import json
from typing import Any, Dict

from .base import Formatter


class JsonFormatter(Formatter):
    """JSON output formatter."""
    
    def format(self, persona: str, analyzed_comments: Dict[str, Any]) -> str:
        """Format the analyzed comments as JSON.
        
        Args:
            persona: The persona context for formatting
            analyzed_comments: The analyzed comments data
            
        Returns:
            Formatted JSON string
        """
        output_data = {
            "persona": persona if persona and persona.strip() else None,
            "analysis": analyzed_comments
        }
        
        return json.dumps(output_data, ensure_ascii=False, indent=2)