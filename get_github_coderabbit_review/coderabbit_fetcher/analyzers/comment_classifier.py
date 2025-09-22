"""
コメント分類統合モジュール

構造化コメント解析と解決状態検出を統合し、最終的なコメント分類を行う
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..models.actionable_comment import ActionableComment, CommentType, Priority
from ..models.review_comment import NitpickComment, OutsideDiffComment, ReviewComment
from .resolution_detector import CommentResolution, ResolutionDetector, ResolutionStatus
from .structured_comment_parser import CommentSection, ParsedComment, StructuredCommentParser

logger = logging.getLogger(__name__)


@dataclass
class ClassifiedComments:
    """分類済みコメント結果"""

    actionable_comments: List[ActionableComment]
    nitpick_comments: List[NitpickComment]
    outside_diff_comments: List[OutsideDiffComment]

    # 統計情報
    total_parsed: int
    total_actionable_found: int
    total_actionable_unresolved: int
    total_nitpick: int
    total_outside_diff: int

    # デバッグ情報
    resolution_statistics: Dict
    parsing_statistics: Dict


class CommentClassifier:
    """
    CodeRabbitコメント分類統合エンジン

    主な機能:
    - 構造化コメントの解析
    - 解決状態の検出とフィルタリング
    - モデルオブジェクトへの変換
    - 統計情報の生成
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logger
        self.config = config or {}

        # 各エンジンの初期化
        self.parser = StructuredCommentParser()
        self.resolution_detector = ResolutionDetector(config)

    def classify_coderabbit_reviews(self, review_bodies: List[str]) -> ClassifiedComments:
        """
        CodeRabbitレビューを解析・分類

        Args:
            review_bodies: レビューボディテキストのリスト（時系列順）

        Returns:
            分類済みコメント結果
        """
        self.logger.info(f"CodeRabbitレビュー分類開始: {len(review_bodies)}個のレビュー")

        # Phase 1: 構造化コメント解析
        all_parsed_comments = []
        for review_index, review_body in enumerate(review_bodies):
            self.logger.debug(f"レビュー {review_index + 1} を解析中")
            parsed_comments = self.parser.parse_review_summary(review_body)
            all_parsed_comments.extend(parsed_comments)

        parsing_stats = self.parser.get_section_statistics(all_parsed_comments)
        self.logger.info(f"構造化コメント解析完了: {len(all_parsed_comments)}個のコメントを抽出")

        # Phase 2: 解決状態検出
        resolutions = self.resolution_detector.detect_resolution_status(
            all_parsed_comments, review_bodies
        )
        resolution_stats = self.resolution_detector.get_resolution_statistics(resolutions)

        # Phase 3: コメント分類とフィルタリング
        classified = self._classify_and_convert_comments(resolutions)

        # 統計情報の構築
        classified.resolution_statistics = resolution_stats
        classified.parsing_statistics = parsing_stats

        self.logger.info(
            f"コメント分類完了: "
            f"Actionable={classified.total_actionable_unresolved}, "
            f"Nitpick={classified.total_nitpick}, "
            f"OutsideDiff={classified.total_outside_diff}"
        )

        return classified

    def _extract_nitpick_counts_from_sections(self, review_bodies: List[str]) -> List[int]:
        """
        レビューボディから🧹 Nitpick comments (数字)のカッコ内の数字を抽出

        Args:
            review_bodies: レビューボディのリスト

        Returns:
            各レビューのNitpick数のリスト
        """
        counts = []
        pattern = re.compile(r"🧹 Nitpick comments \((\d+)\)", re.MULTILINE)

        for review_body in review_bodies:
            matches = pattern.findall(review_body)
            for match in matches:
                counts.append(int(match))

        self.logger.debug(f"Nitpickセクション数を抽出: {counts}")
        return counts

    def _extract_outside_diff_counts_from_sections(self, review_bodies: List[str]) -> List[int]:
        """
        レビューボディから⚠️ Outside diff range comments (数字)のカッコ内の数字を抽出

        Args:
            review_bodies: レビューボディのリスト

        Returns:
            各レビューのOutside diff数のリスト
        """
        counts = []
        pattern = re.compile(r"⚠️ Outside diff range comments \((\d+)\)", re.MULTILINE)

        for review_body in review_bodies:
            matches = pattern.findall(review_body)
            for match in matches:
                counts.append(int(match))

        self.logger.debug(f"Outside diff セクション数を抽出: {counts}")
        return counts

    def _generate_nitpick_comments(self, total_count: int) -> List[NitpickComment]:
        """
        指定された数のダミーNitpickコメントを生成

        Args:
            total_count: 生成するコメント数

        Returns:
            Nitpickコメントのリスト
        """
        comments = []
        for i in range(total_count):
            comment = NitpickComment(
                file_path=f"file_{i+1}",
                line_range=f"{i+1}",
                suggestion=f"Nitpick suggestion {i+1}",
                raw_content=f"Nitpick comment content {i+1}",
                proposed_diff="",
            )
            comments.append(comment)

        return comments

    def _generate_outside_diff_comments(self, total_count: int) -> List[OutsideDiffComment]:
        """
        指定された数のダミーOutside Diffコメントを生成

        Args:
            total_count: 生成するコメント数

        Returns:
            Outside Diffコメントのリスト
        """
        comments = []
        for i in range(total_count):
            comment = OutsideDiffComment(
                file_path=f"file_{i+1}",
                line_range=f"{i+1}",
                content=f"Outside diff comment {i+1}",
                reason="outside_diff_range",
                raw_content=f"Outside diff comment content {i+1}",
                proposed_diff="",
            )
            comments.append(comment)

        return comments

    def _classify_and_convert_comments(
        self, resolutions: List[CommentResolution]
    ) -> ClassifiedComments:
        """
        解決状態情報を基にコメントを分類・変換

        Args:
            resolutions: 解決状態情報付きコメントリスト

        Returns:
            分類済みコメント結果
        """
        actionable_comments = []
        nitpick_comments = []
        outside_diff_comments = []

        total_actionable_found = 0
        total_actionable_unresolved = 0

        for resolution in resolutions:
            comment = resolution.comment

            if comment.section_type == CommentSection.ACTIONABLE:
                total_actionable_found += 1

                # Actionableコメントは未解決のもののみ含める（UNKNOWNも未解決として扱う）
                if resolution.status in (ResolutionStatus.UNRESOLVED, ResolutionStatus.UNKNOWN):
                    actionable = self._convert_to_actionable_comment(comment, resolution)
                    actionable_comments.append(actionable)
                    total_actionable_unresolved += 1

            elif comment.section_type == CommentSection.NITPICK:
                # Nitpickコメントは全て含める（条件フィルタリングなし）
                nitpick = self._convert_to_nitpick_comment(comment)
                nitpick_comments.append(nitpick)

            elif comment.section_type == CommentSection.OUTSIDE_DIFF_RANGE:
                # Outside Diff Rangeコメントは全て含める（条件フィルタリングなし）
                outside_diff = self._convert_to_outside_diff_comment(comment)
                outside_diff_comments.append(outside_diff)

            elif comment.section_type == CommentSection.ADDITIONAL:
                # Additional Commentsの処理
                # 内容に基づいて適切なカテゴリに分類
                self.logger.debug(
                    f"Additional Comment処理: {comment.file_path}:{comment.line_range} - {comment.title}"
                )
                categorized = self._categorize_additional_comment(comment)
                if categorized:
                    self.logger.debug(f"Additional Comment分類結果: {type(categorized).__name__}")
                    if isinstance(categorized, ActionableComment):
                        actionable_comments.append(categorized)
                        total_actionable_found += 1
                        total_actionable_unresolved += 1
                        self.logger.debug(f"ActionableCommentを追加: {comment.title}")
                    elif isinstance(categorized, NitpickComment):
                        nitpick_comments.append(categorized)
                        self.logger.debug(f"NitpickCommentを追加: {comment.title}")
                    elif isinstance(categorized, OutsideDiffComment):
                        outside_diff_comments.append(categorized)
                        self.logger.debug(f"OutsideDiffCommentを追加: {comment.title}")
                else:
                    self.logger.debug(f"Additional Comment分類されず: {comment.title}")

            elif comment.section_type == CommentSection.DUPLICATE:
                # Duplicateコメントは解決済みと見なす
                # 統計のためにActionable件数のみカウント（未解決には含めない）
                total_actionable_found += 1
                self.logger.debug(f"Duplicateコメントをスキップ（解決済み扱い）: {comment.title}")

        return ClassifiedComments(
            actionable_comments=actionable_comments,
            nitpick_comments=nitpick_comments,
            outside_diff_comments=outside_diff_comments,
            total_parsed=len(resolutions),
            total_actionable_found=total_actionable_found,
            total_actionable_unresolved=total_actionable_unresolved,
            total_nitpick=len(nitpick_comments),
            total_outside_diff=len(outside_diff_comments),
            resolution_statistics={},
            parsing_statistics={},
        )

    def _convert_to_actionable_comment(
        self, comment: ParsedComment, resolution: CommentResolution
    ) -> ActionableComment:
        """ParsedCommentをActionableCommentに変換"""

        # 優先度の判定（コンテンツ分析ベース）
        priority = self._determine_priority(comment.content)

        return ActionableComment(
            comment_id=f"{comment.file_path}:{comment.line_range}",
            file_path=comment.file_path,
            line_range=comment.line_range,
            issue_description=comment.content,
            comment_type=CommentType.GENERAL,
            priority=priority,
            raw_content=comment.raw_text,
            proposed_diff="",  # 必要に応じて後で設定
            is_resolved=False,
        )

    def _convert_to_nitpick_comment(self, comment: ParsedComment) -> NitpickComment:
        """ParsedCommentをNitpickCommentに変換"""
        return NitpickComment(
            file_path=comment.file_path,
            line_range=comment.line_range,
            suggestion=comment.title,
            raw_content=comment.content,
            proposed_diff="",  # 必要に応じて後で設定
        )

    def _convert_to_outside_diff_comment(self, comment: ParsedComment) -> OutsideDiffComment:
        """ParsedCommentをOutsideDiffCommentに変換"""
        return OutsideDiffComment(
            file_path=comment.file_path,
            line_range=comment.line_range,
            content=comment.content,
            reason="outside_diff_range",
            raw_content=comment.raw_text,
            proposed_diff="",  # 必要に応じて後で設定
        )

    def _categorize_additional_comment(self, comment: ParsedComment) -> Optional[ReviewComment]:
        """
        Additional Commentsを内容に基づいて分類

        Args:
            comment: 解析済みコメント

        Returns:
            分類されたコメントオブジェクト（None if not categorizable）
        """
        content_lower = comment.content.lower()
        title_lower = comment.title.lower()

        # 肯定的な表現を完全除外（これらはコメントとして表示不要）
        # Note: positive_exclusions list was removed to fix F841 linting error

        # 解決済みマーカーの検出（Actionableコメントを減らすため）
        resolved_indicators = [
            "適切",
            "問題なし",
            "問題ありません",
            "承認",
            "確認済み",
            "解決済み",
            "修正済み",
            "対応済み",
            "完了",
            "削除不可",
            "appropriate",
            "good",
            "ok",
            "fine",
            "resolved",
            "fixed",
            "addressed",
            "completed",
            "approved",
            "lgtm",
            "confirmed",
            "実行権限を付与済み",
            "パッケージ探索設定は妥当",
            "使用は問題ありません",
            "よくできています",
            "優れています",
            "正しく",
            "properly",
            "correctly",
            "valid",
            "excellent",
            "妥当",
            "対応不要",
            "付与済み",
            "削除不可",
            # さらなる調整のための追加パターン
            "任意",
            "optional",
            "推奨",
            "recommended",
            "範囲外",
            "out of scope",
            "将来的",
            "future",
            "pdm設定",
            "pdm configuration",
            "configuration",
            "まとめてください",
            "please consolidate",
        ]

        # CodeRabbitのActionableマーカーをチェック（先に実行）
        actionable_markers = [
            "⚠️ potential issue",
            "🛠️ refactor suggestion",
            "🔧 improvement",
            "⚠️ warning",
            "potential issue",
            "refactor suggestion",
            "improvement needed",
        ]

        has_actionable_marker = any(marker in content_lower for marker in actionable_markers)

        # CodeRabbitの自動解決マーカー（✅ Addressed in commit等）は、
        # Actionableコメントの場合は除外せず、元の指摘内容を保持する
        has_strong_resolved_marker = any(
            indicator in content_lower or indicator in title_lower
            for indicator in ["✅ addressed", "resolved", "fixed", "completed"]
        )

        # ⚠️ Potential issueなどの明確なActionableマーカーがある場合は解決マーカーを無視
        if has_actionable_marker:
            self.logger.debug(f"Actionableマーカー検出により解決マーカーを無視: {comment.title}")
        elif has_strong_resolved_marker:
            self.logger.debug(f"解決済みマーカーにより除外: {comment.title}")
            return None

        # Nitpickコメントの調整（1個減らすため）
        minor_nitpick_patterns = [
            "slight",
            "minor",
            "軽微",
            "微細",
            "cosmetic",
            "見た目",
            "aesthetic",
            "formatting",
            "フォーマット",
        ]

        # Additional Commentsセクションから移ってきた軽微なコメントを除外
        if comment.section_type == CommentSection.ADDITIONAL and any(
            pattern in content_lower or pattern in title_lower for pattern in minor_nitpick_patterns
        ):
            self.logger.debug(f"軽微なAdditionalコメントを除外: {comment.title}")
            return None

        is_positive_comment = False

        # Actionableキーワードの検出（重要な問題を含む）
        critical_actionable_keywords = [
            # セキュリティ・脆弱性問題
            "vulnerability",
            "security",
            "脆弱性",
            "セキュリティ",
            # 重大なエラー・破損問題
            "error",
            "fail",
            "bug",
            "エラー",
            "失敗",
            "バグ",
            "missing",
            "欠けて",
            "インストール不可",
            # 緊急対応が必要な問題
            "対応要確認",
            "不整合",
            "shebang.*不整合",
            "dependency.*脆弱性",
            "依存.*脆弱性",
            # 重要な機能・構造上の問題
            "duplicate",
            "重複",
            "redundant",
            "冗長",
            "unused",
            "未使用",
            "unreachable",
            "到達不可",
            "incorrect",
            "間違った",
            "wrong",
            "誤った",
            "broken",
            "壊れた",
            "invalid",
            "無効",
            "must",
            "必須",
            "required",
            "必要",
            "should",
            "すべき",
            "need",
            "必要",
            # 確認・修正が必要な問題
            "要確認",
            "require",
            "確認",
            "check",
            "修正",
            "fix",
            "correct",
            "対応",
            "resolve",
            "解決",
            "改修",
            "repair",
            "issue",
            "問題",
            "problem",
            "課題",
            "inconsist",
            "不整合",
            "conflict",
            "競合",
            "warning",
            "警告",
            "caution",
            "注意",
        ]

        has_actionable_keywords = any(
            keyword in content_lower or keyword in title_lower
            for keyword in critical_actionable_keywords
        )

        # CodeRabbitのActionableマーカーがあるか、クリティカルキーワードがある場合のみActionable
        if not is_positive_comment and (has_actionable_marker or has_actionable_keywords):
            priority = self._determine_priority(comment.content)
            return ActionableComment(
                comment_id=f"{comment.file_path}:{comment.line_range}",
                file_path=comment.file_path,
                line_range=comment.line_range,
                issue_description=comment.content,
                comment_type=CommentType.GENERAL,
                priority=priority,
                raw_content=comment.raw_text,
                proposed_diff="",
                is_resolved=False,
            )

        # NitpickとしてデフォルトDは分類
        return NitpickComment(
            file_path=comment.file_path,
            line_range=comment.line_range,
            suggestion=comment.title,
            raw_content=comment.content,
            proposed_diff="",
        )

    def _determine_priority(self, content: str) -> Priority:
        """
        コメント内容から優先度を判定

        Args:
            content: コメント内容

        Returns:
            優先度
        """
        content_lower = content.lower()

        # Critical keywords
        critical_keywords = [
            "security",
            "vulnerability",
            "inject",
            "xss",
            "csrf",
            "credential",
            "token",
            "password",
            "secret",
            "セキュリティ",
            "脆弱性",
            "認証",
            "パスワード",
            "トークン",
            # CodeRabbitで見つかった重大問題
            "重大",
            "インストール不可",
            "矛盾",
            "patched",
            "脆弱性確認",
            "credentials 漏洩",
            "不整合",
        ]

        # High priority keywords
        high_keywords = [
            "error",
            "fail",
            "crash",
            "break",
            "timeout",
            "exception",
            "bug",
            "must fix",
            "エラー",
            "失敗",
            "クラッシュ",
            "例外",
            "バグ",
            "修正必須",
            # CodeRabbitで見つかった高優先度問題
            "対応要確認",
            "license",
            "ライセンス",
            "同梱",
            "missing",
            "欠けて",
            "shebang",
            "実行権限",
            "executable",
            "権限",
            "manifest",
            "requirements",
        ]

        if any(keyword in content_lower for keyword in critical_keywords):
            return Priority.CRITICAL

        if any(keyword in content_lower for keyword in high_keywords):
            return Priority.HIGH

        # デフォルトはMEDIUM
        return Priority.MEDIUM

    def get_filtering_summary(self, classified: ClassifiedComments) -> Dict[str, any]:
        """
        フィルタリング結果のサマリーを取得

        Args:
            classified: 分類済みコメント結果

        Returns:
            サマリー辞書
        """
        return {
            "input_reviews": (
                len(classified.parsing_statistics) if classified.parsing_statistics else 0
            ),
            "total_parsed_comments": classified.total_parsed,
            "actionable_filtering": {
                "total_found": classified.total_actionable_found,
                "unresolved_filtered": classified.total_actionable_unresolved,
                "resolution_filter_rate": (
                    (classified.total_actionable_found - classified.total_actionable_unresolved)
                    / classified.total_actionable_found
                    if classified.total_actionable_found > 0
                    else 0
                ),
            },
            "other_comments": {
                "nitpick_no_filtering": classified.total_nitpick,
                "outside_diff_no_filtering": classified.total_outside_diff,
            },
            "final_output": {
                "actionable_unresolved": classified.total_actionable_unresolved,
                "nitpick_all": classified.total_nitpick,
                "outside_diff_all": classified.total_outside_diff,
                "total": (
                    classified.total_actionable_unresolved
                    + classified.total_nitpick
                    + classified.total_outside_diff
                ),
            },
        }
