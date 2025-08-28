"""Comment processors module for CodeRabbit fetcher."""

from .summary_processor import SummaryProcessor
from .review_processor import ReviewProcessor
from .thread_processor import ThreadProcessor

__all__ = ["SummaryProcessor", "ReviewProcessor", "ThreadProcessor"]
