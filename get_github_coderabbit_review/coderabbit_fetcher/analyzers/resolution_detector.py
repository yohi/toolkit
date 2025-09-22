"""
コメント解決状態検出モジュール

Actionableコメントの解決状態を判定し、未解決コメントのフィルタリングを行う
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from .structured_comment_parser import CommentSection, ParsedComment

logger = logging.getLogger(__name__)


class ResolutionStatus(Enum):
    """解決状態"""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNKNOWN = "unknown"


@dataclass
class ResolutionMarker:
    """解決マーカー情報"""

    marker_text: str
    marker_type: str
    context: str
    review_index: int


@dataclass
class CommentResolution:
    """コメント解決情報"""

    comment: ParsedComment
    status: ResolutionStatus
    resolution_markers: List[ResolutionMarker]
    resolution_context: Optional[str] = None


class ResolutionDetector:
    """
    Actionableコメントの解決状態検出エンジン

    主な機能:
    - 解決マーカーの検出（configurable patterns）
    - レビュー間でのコメント追跡
    - 解決状態の判定ロジック
    - 未解決コメントのフィルタリング
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logger
        self.config = config or {}

        # デフォルト解決マーカーパターン
        self.default_resolution_patterns = [
            # 日本語パターン
            r"解決済み",
            r"解決しました",
            r"解決された",
            r"修正済み",
            r"修正しました",
            r"修正された",
            r"対応済み",
            r"対応しました",
            r"対応された",
            r"完了",
            r"完了しました",
            r"適切です",
            r"問題ありません",
            # 英語パターン
            r"resolved",
            r"fixed",
            r"addressed",
            r"completed",
            r"done",
            r"corrected",
            r"appropriate",
            r"good",
            r"ok",
            r"fine",
            # 肯定的なフィードバックパターン
            r"解決.*?[！!]",
            r"適切.*?改名",
            r"前回.*?解決",
            r"問題.*?解決",
            r"指摘.*?解決",
            r"衝突.*?解決",
            # CodeRabbit特有の解決表現
            r"前回のレビューで指摘した.*?修正",
            r"前回のレビューで指摘した.*?解決",
            r"素晴らしい対応です",
            r"適切に修正されています",
            r"適切です[！!]",
            r"適切な対応です",
            r"問題が解決されました",
            r"命名衝突が解決",
            r"適切に.*?修正",
            r"正しく.*?修正",
            r"適切な.*?変更",
            # 重複コメントセクション内のパターン
            r"♻️\s*Duplicate\s+comments",
            r"Duplicate\s+comments",
        ]

        # カスタムパターンを設定から取得
        custom_patterns = self.config.get("resolution_patterns", [])
        self.resolution_patterns = self.default_resolution_patterns + custom_patterns

        # コンパイル済み正規表現
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.resolution_patterns
        ]

        # 除外パターン（解決マーカーがあっても未解決と判定すべきケース）
        self.exclusion_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.config.get(
                "exclusion_patterns",
                [
                    r"まだ.*?解決.*?していません",
                    r"未だ.*?解決.*?していません",
                    r"まだ.*?修正.*?していません",
                    r"not.*?resolved",
                    r"not.*?fixed",
                    r"still.*?unresolved",
                ],
            )
        ]

    def detect_resolution_status(
        self, comments: List[ParsedComment], all_review_bodies: List[str]
    ) -> List[CommentResolution]:
        """
        コメントリストの解決状態を検出

        Args:
            comments: 解析済みコメントリスト
            all_review_bodies: 全レビューのボディテキストリスト（時系列順）

        Returns:
            解決状態情報付きコメントリスト
        """
        resolutions = []

        for comment in comments:
            if comment.section_type == CommentSection.ACTIONABLE:
                # Actionableコメントのみ解決状態を判定
                resolution = self._analyze_comment_resolution(comment, all_review_bodies)
            else:
                # その他のコメントは全て未解決扱い（フィルタリング条件なし）
                resolution = CommentResolution(
                    comment=comment, status=ResolutionStatus.UNRESOLVED, resolution_markers=[]
                )

            resolutions.append(resolution)

        self.logger.info(f"解決状態解析完了: {len(resolutions)}個のコメントを解析")
        return resolutions

    def _analyze_comment_resolution(
        self, comment: ParsedComment, all_review_bodies: List[str]
    ) -> CommentResolution:
        """
        個別コメントの解決状態を解析

        Args:
            comment: 解析対象コメント
            all_review_bodies: 全レビューボディリスト

        Returns:
            解決状態情報
        """
        resolution_markers = []

        # 全レビューから解決マーカーを検索
        for review_index, review_body in enumerate(all_review_bodies):
            markers = self._find_resolution_markers_in_review(comment, review_body, review_index)
            resolution_markers.extend(markers)

        # 解決状態を判定
        status = self._determine_resolution_status(comment, resolution_markers)

        # コンテキスト情報を構築
        context = self._build_resolution_context(resolution_markers)

        return CommentResolution(
            comment=comment,
            status=status,
            resolution_markers=resolution_markers,
            resolution_context=context,
        )

    def _find_resolution_markers_in_review(
        self, comment: ParsedComment, review_body: str, review_index: int
    ) -> List[ResolutionMarker]:
        """
        特定のレビュー内で解決マーカーを検索

        Args:
            comment: 対象コメント
            review_body: レビューボディ
            review_index: レビューインデックス

        Returns:
            発見された解決マーカーリスト
        """
        markers = []

        # コメントのファイル名と行番号で関連箇所を特定
        comment_context_patterns = [
            # ファイル名 + 行番号の組み合わせ
            rf"{re.escape(comment.file_path)}.*?{re.escape(comment.line_range)}",
            # 行番号のみ
            rf"`{re.escape(comment.line_range)}`",
            # タイトルの一部
            rf"{re.escape(comment.title[:20])}",  # タイトルの最初の20文字
        ]

        for context_pattern in comment_context_patterns:
            context_regex = re.compile(context_pattern, re.IGNORECASE | re.MULTILINE)
            context_match = context_regex.search(review_body)

            if context_match:
                # コンテキスト周辺で解決マーカーを検索
                context_start = max(0, context_match.start() - 500)
                context_end = min(len(review_body), context_match.end() + 500)
                context_text = review_body[context_start:context_end]

                # 解決マーカーパターンをチェック
                for pattern in self.compiled_patterns:
                    marker_matches = pattern.finditer(context_text)
                    for marker_match in marker_matches:
                        # 除外パターンをチェック
                        is_excluded = any(
                            exclusion.search(context_text) for exclusion in self.exclusion_patterns
                        )

                        if not is_excluded:
                            marker = ResolutionMarker(
                                marker_text=marker_match.group(0),
                                marker_type=pattern.pattern,
                                context=context_text,
                                review_index=review_index,
                            )
                            markers.append(marker)

        return markers

    def _determine_resolution_status(
        self, comment: ParsedComment, resolution_markers: List[ResolutionMarker]
    ) -> ResolutionStatus:
        """
        解決マーカーに基づいて解決状態を判定

        Args:
            comment: 対象コメント
            resolution_markers: 発見された解決マーカーリスト

        Returns:
            解決状態
        """
        if not resolution_markers:
            return ResolutionStatus.UNRESOLVED

        # 最新のマーカーを重視
        latest_marker = max(resolution_markers, key=lambda m: m.review_index)

        # 明確な解決マーカーがある場合
        definitive_patterns = [
            r"解決済み",
            r"修正済み",
            r"対応済み",
            r"resolved",
            r"fixed",
            r"addressed",
        ]

        for pattern in definitive_patterns:
            if re.search(pattern, latest_marker.marker_text, re.IGNORECASE):
                return ResolutionStatus.RESOLVED

        # 複数のマーカーがある場合は解決済みと判定
        if len(resolution_markers) >= 2:
            return ResolutionStatus.RESOLVED

        # 単一マーカーの場合は未解決として扱う（解決の証拠が不十分）
        return ResolutionStatus.UNRESOLVED

    def _build_resolution_context(
        self, resolution_markers: List[ResolutionMarker]
    ) -> Optional[str]:
        """
        解決状態のコンテキスト情報を構築

        Args:
            resolution_markers: 解決マーカーリスト

        Returns:
            コンテキスト文字列
        """
        if not resolution_markers:
            return None

        # 最新のマーカーのコンテキストを使用
        latest_marker = max(resolution_markers, key=lambda m: m.review_index)
        return f"Review {latest_marker.review_index + 1}: {latest_marker.marker_text}"

    def filter_unresolved_actionable(
        self, resolutions: List[CommentResolution]
    ) -> List[ParsedComment]:
        """
        未解決のActionableコメントのみをフィルタリング

        Args:
            resolutions: 解決状態情報付きコメントリスト

        Returns:
            未解決Actionableコメントリスト
        """
        unresolved_actionable = []

        for resolution in resolutions:
            # Actionableコメントで未解決のもののみ
            if (
                resolution.comment.section_type == CommentSection.ACTIONABLE
                and resolution.status == ResolutionStatus.UNRESOLVED
            ):
                unresolved_actionable.append(resolution.comment)

        self.logger.info(
            f"未解決Actionableコメントフィルタリング完了: "
            f"{len(unresolved_actionable)}個のコメントが未解決"
        )
        return unresolved_actionable

    def filter_all_non_actionable(
        self, resolutions: List[CommentResolution]
    ) -> List[ParsedComment]:
        """
        Actionable以外のコメントを全て取得（条件フィルタリングなし）

        Args:
            resolutions: 解決状態情報付きコメントリスト

        Returns:
            非Actionableコメントリスト
        """
        non_actionable = []

        for resolution in resolutions:
            if resolution.comment.section_type != CommentSection.ACTIONABLE:
                non_actionable.append(resolution.comment)

        return non_actionable

    def get_resolution_statistics(self, resolutions: List[CommentResolution]) -> Dict[str, Dict]:
        """
        解決状態統計情報を取得

        Args:
            resolutions: 解決状態情報付きコメントリスト

        Returns:
            統計情報辞書
        """
        stats = {
            "total": len(resolutions),
            "by_section": {},
            "by_status": {status.value: 0 for status in ResolutionStatus},
        }

        # セクション別統計
        for section in CommentSection:
            section_resolutions = [r for r in resolutions if r.comment.section_type == section]

            section_stats = {
                "total": len(section_resolutions),
                "by_status": {status.value: 0 for status in ResolutionStatus},
            }

            for resolution in section_resolutions:
                section_stats["by_status"][resolution.status.value] += 1

            stats["by_section"][section.value] = section_stats

        # 全体の状態別統計
        for resolution in resolutions:
            stats["by_status"][resolution.status.value] += 1

        return stats
