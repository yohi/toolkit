"""
CodeRabbit コメント解析モジュール

構造化コメント解析、解決状態検出、コメント分類の統合機能を提供
"""

from .structured_comment_parser import (
    StructuredCommentParser,
    ParsedComment,
    CommentSection
)
from .resolution_detector import (
    ResolutionDetector,
    ResolutionStatus,
    ResolutionMarker,
    CommentResolution
)
from .comment_classifier import (
    CommentClassifier,
    ClassifiedComments
)
from .metadata_enhancer import MetadataEnhancer

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