"""
CodeRabbit コメント解析モジュール

構造化コメント解析、解決状態検出、コメント分類の統合機能を提供
"""

from .comment_classifier import ClassifiedComments, CommentClassifier
from .metadata_enhancer import MetadataEnhancer
from .resolution_detector import (
    CommentResolution,
    ResolutionDetector,
    ResolutionMarker,
    ResolutionStatus,
)
from .structured_comment_parser import CommentSection, ParsedComment, StructuredCommentParser

__all__ = [
    # 構造化コメント解析
    "StructuredCommentParser",
    "ParsedComment",
    "CommentSection",
    # 解決状態検出
    "ResolutionDetector",
    "ResolutionStatus",
    "ResolutionMarker",
    "CommentResolution",
    # コメント分類統合
    "CommentClassifier",
    "ClassifiedComments",
    # メタデータ拡張
    "MetadataEnhancer",
]
