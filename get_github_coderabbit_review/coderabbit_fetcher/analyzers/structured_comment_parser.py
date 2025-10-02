"""
CodeRabbit構造化コメント解析モジュール

CodeRabbitのマークダウン形式レビューサマリーから個別コメントを抽出・解析する
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CommentSection(Enum):
    """コメントセクションタイプ"""

    ACTIONABLE = "actionable"
    NITPICK = "nitpick"
    OUTSIDE_DIFF_RANGE = "outside_diff_range"
    ADDITIONAL = "additional"
    DUPLICATE = "duplicate"


@dataclass
class ParsedComment:
    """解析済みコメント情報"""

    file_path: str
    line_range: str
    title: str
    content: str
    section_type: CommentSection
    raw_text: str
    is_duplicate: bool = False  # "Also applies to:" による重複
    applies_to_lines: Optional[List[str]] = None  # 重複適用行番号


class StructuredCommentParser:
    """
    CodeRabbitの構造化マークダウンからコメントを抽出する解析エンジン

    主な機能:
    - レビューサマリー内の個別コメント抽出
    - セクション別分類（Actionable/Nitpick/Outside Diff Range）
    - ファイル名とコメント内容の正確な抽出
    - ネストした<details>構造の処理
    - "Also applies to:" 重複コメントの処理
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = logger

        # パターン定義
        self.section_patterns = {
            CommentSection.ACTIONABLE: re.compile(
                r"\*\*Actionable comments posted:\s*(\d+)\*\*", re.MULTILINE
            ),
            CommentSection.NITPICK: re.compile(
                r"<summary>🧹 Nitpick comments \((\d+)\)</summary>", re.MULTILINE
            ),
            CommentSection.OUTSIDE_DIFF_RANGE: re.compile(
                r"<summary>⚠️ Outside diff range comments \((\d+)\)</summary>", re.MULTILINE
            ),
            CommentSection.ADDITIONAL: re.compile(
                r"<summary>🔇 Additional comments \((\d+)\)</summary>", re.MULTILINE
            ),
            CommentSection.DUPLICATE: re.compile(
                r"<summary>♻️ Duplicate comments \((\d+)\)</summary>", re.MULTILINE
            ),
        }

        # コメント行番号パターン（例: `3-8`:, `20-20`:, `1-1`:）
        self.line_comment_pattern = re.compile(r"`(\d+(?:-\d+)?)`: \*\*(.*?)\*\*", re.MULTILINE)

        # ファイル名パターン（例: <summary>setup.py (1)</summary>）
        self.file_pattern = re.compile(r"<summary>(.*?)(?: \((\d+)\))?</summary>", re.MULTILINE)

        # "Also applies to:" パターン
        self.also_applies_pattern = re.compile(r"Also applies to:\s*([0-9,\s-]+)", re.MULTILINE)

    def parse_review_summary(self, review_body: str) -> List[ParsedComment]:
        """
        レビューサマリーから構造化コメントを抽出

        Args:
            review_body: CodeRabbitレビューサマリーのマークダウンテキスト

        Returns:
            抽出されたコメントのリスト
        """
        comments = []

        # セクション別に解析
        for section_type in CommentSection:
            section_comments = self._parse_section(review_body, section_type)

            comments.extend(section_comments)

        self.logger.info(f"構造化コメント解析完了: {len(comments)}個のコメントを抽出")
        return comments

    def _parse_section(self, review_body: str, section_type: CommentSection) -> List[ParsedComment]:
        """
        特定セクションのコメントを解析

        Args:
            review_body: レビューサマリーテキスト
            section_type: 解析対象のセクションタイプ

        Returns:
            該当セクションのコメントリスト
        """
        pattern = self.section_patterns[section_type]
        section_match = pattern.search(review_body)

        if not section_match:
            self.logger.debug(f"セクション {section_type.value} が見つかりませんでした")
            if section_type == CommentSection.ADDITIONAL:
                # Additional Commentsの検索パターンを詳細ログで確認
                self.logger.debug(f"Additional Comments検索パターン: {pattern.pattern}")
                self.logger.debug(f"レビューボディの一部: {review_body[:1000]}...")
            return []

        # セクション宣言から数値を抽出
        declared_count = self._extract_declared_count(section_match, section_type)

        # セクション開始位置を特定
        section_start = section_match.end()
        self.logger.debug(
            f"セクション {section_type.value} を発見: 開始位置 {section_match.start()}, 終了位置 {section_start}"
        )

        # セクション終了位置を特定（次のセクションまたは終端）
        section_end = self._find_section_end(review_body, section_start)
        section_content = review_body[section_start:section_end]

        # デバッグ用にセクション内容をログ出力
        if section_type == CommentSection.OUTSIDE_DIFF_RANGE:
            self.logger.debug(f"Outside Diff Range セクション内容: {section_content[:500]}...")

        # セクション内のコメントを抽出
        extracted_comments = self._extract_comments_from_section(
            section_content, section_type, review_body[section_match.start() : section_end]
        )

        # CodeRabbitの宣言数値に従って結果を調整
        return self._align_with_declared_count(extracted_comments, declared_count, section_type)

    def _find_section_end(self, text: str, start_pos: int) -> int:
        """
        セクションの終了位置を特定

        Args:
            text: 全体テキスト
            start_pos: セクション開始位置

        Returns:
            セクション終了位置
        """
        # 次のセクションの開始を探す
        next_sections = []
        for pattern in self.section_patterns.values():
            match = pattern.search(text, start_pos)
            if match:
                next_sections.append(match.start())

        if next_sections:
            return min(next_sections)
        else:
            return len(text)

    def _extract_comments_from_section(
        self, section_content: str, section_type: CommentSection, full_section: str
    ) -> List[ParsedComment]:
        """
        セクション内容から個別コメントを抽出

        Args:
            section_content: セクション内容テキスト
            section_type: セクションタイプ
            full_section: フルセクションテキスト（デバッグ用）

        Returns:
            抽出されたコメントリスト
        """
        comments = []

        # Outside Diff Rangeセクションの場合、直接パターンマッチング
        if section_type == CommentSection.OUTSIDE_DIFF_RANGE:
            # Find all <summary> tags and their positions to map comments to correct files
            summary_pattern = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)
            summaries = [(m.start(), m.group(1).strip()) for m in summary_pattern.finditer(section_content)]
            
            # 直接section_content全体から`行番号`: **タイトル** パターンを検索
            direct_matches = self.line_comment_pattern.finditer(section_content)
            for match in direct_matches:
                line_range = match.group(1)
                title = match.group(2)
                match_pos = match.start()

                # ファイル名を抽出（マッチ位置より前で最も近い<summary>から）
                file_path = "unknown_file"
                for sum_pos, sum_text in reversed(summaries):
                    if sum_pos < match_pos:
                        # "ファイル名 (1)" のようなパターンからファイル名を抽出
                        file_name_match = re.match(r"(.+?)\s*\(\d+\)", sum_text)
                        if file_name_match:
                            file_path = file_name_match.group(1).strip()
                        else:
                            file_path = sum_text
                        break

                # コメント内容を抽出
                content_start = match.end()
                content_end = self._find_comment_end(section_content, content_start)
                content = section_content[content_start:content_end].strip()

                comment = ParsedComment(
                    file_path=file_path,
                    line_range=line_range,
                    title=title,
                    content=content,
                    section_type=section_type,
                    raw_text=match.group(0),
                    applies_to_lines=[],
                )
                comments.append(comment)
                self.logger.debug(
                    f"Outside Diff Range コメント検出: {file_path}:{line_range} - {title}"
                )

        # その他のセクションは従来通り
        else:
            # <details>タグでファイル別に分割
            file_blocks = self._split_by_file_blocks(section_content)

            for file_path, file_content in file_blocks.items():
                file_comments = self._extract_file_comments(file_path, file_content, section_type)
                comments.extend(file_comments)

        self.logger.debug(f"セクション {section_type.value}: {len(comments)}個のコメントを抽出")
        return comments

    def _split_by_file_blocks(self, content: str) -> Dict[str, str]:
        """
        <details>タグでファイル別にコンテンツを分割

        Args:
            content: セクション内容

        Returns:
            ファイル名をキーとしたコンテンツ辞書
        """
        file_blocks = {}

        # <details><summary>ファイル名</summary>パターンで分割（blockquote内も対応）
        details_pattern = re.compile(
            r"<details>\s*<summary>(.*?)</summary><blockquote>(.*?)</blockquote></details>",
            re.DOTALL | re.MULTILINE,
        )

        # blockquote内のdetailsパターンも検索（> 記号を含む形式に対応）
        blockquote_details_pattern = re.compile(
            r"<blockquote>\s*>\s*\s*<details>\s*<summary>(.*?)</summary><blockquote>\s*>\s*(.*?)</blockquote>",
            re.DOTALL | re.MULTILINE,
        )

        # 通常のdetailsパターンを検索
        matches = details_pattern.finditer(content)
        for match in matches:
            file_header = match.group(1).strip()
            file_content = match.group(2).strip()

            # ファイル名を抽出（例: "setup.py (1)" -> "setup.py"）
            file_name = re.sub(r"\s*\(\d+\)\s*$", "", file_header)
            file_blocks[file_name] = file_content

        # blockquote内のdetailsパターンも検索
        blockquote_matches = blockquote_details_pattern.finditer(content)
        for match in blockquote_matches:
            file_header = match.group(1).strip()
            file_content = match.group(2).strip()

            # ファイル名を抽出（例: "setup.py (1)" -> "setup.py"）
            file_name = re.sub(r"\s*\(\d+\)\s*$", "", file_header)
            file_blocks[file_name] = file_content

        # Outside Diff Rangeの場合、file_blocksの結果をログ出力
        if len(file_blocks) == 0:
            # デバッグ用にパターンマッチング詳細を確認
            self.logger.debug(
                f"通常のdetailsパターンマッチ数: {len(list(details_pattern.finditer(content)))}"
            )
            self.logger.debug(
                f"blockquoteパターンマッチ数: {len(list(blockquote_details_pattern.finditer(content)))}"
            )

        return file_blocks

    def _extract_file_comments(
        self, file_path: str, file_content: str, section_type: CommentSection
    ) -> List[ParsedComment]:
        """
        特定ファイルのコメントを抽出

        Args:
            file_path: ファイルパス
            file_content: ファイルのコメント内容
            section_type: セクションタイプ

        Returns:
            該当ファイルのコメントリスト
        """
        comments = []

        # 行番号コメントを検索
        if section_type == CommentSection.OUTSIDE_DIFF_RANGE:
            self.logger.debug(
                f"Outside Diff Range パターン検索: {self.line_comment_pattern.pattern}"
            )
            self.logger.debug(f"検索対象コンテンツ: {file_content}")
            matches = list(self.line_comment_pattern.finditer(file_content))
            self.logger.debug(f"マッチした数: {len(matches)}")
            for i, match in enumerate(matches):
                self.logger.debug(f"マッチ {i+1}: {match.group(0)}")

        for match in self.line_comment_pattern.finditer(file_content):
            line_range = match.group(1)
            title = match.group(2)

            # コメント内容を抽出（次のコメントまたは区切りまで）
            content_start = match.end()
            content_end = self._find_comment_end(file_content, content_start)
            content = file_content[content_start:content_end].strip()

            # "Also applies to:" の処理
            also_applies_lines = self._extract_also_applies_to(content)

            # Debug: log the extracted content for lib/ comments
            if "lib/" in title:
                self.logger.info("DEBUG: lib/ comment extraction:")
                self.logger.info(f"  title: {repr(title)}")
                self.logger.info(f"  content: {repr(content)}")
                self.logger.info(f"  raw match: {repr(match.group(0))}")
                self.logger.info(f"  content_start: {content_start}, content_end: {content_end}")
                self.logger.info(
                    f"  file_content[content_start:content_end]: {repr(file_content[content_start:content_end])}"
                )

            comment = ParsedComment(
                file_path=file_path,
                line_range=line_range,
                title=title,
                content=content,
                section_type=section_type,
                raw_text=match.group(0),
                applies_to_lines=also_applies_lines,
            )

            comments.append(comment)

            # "Also applies to:" がある場合は重複コメントも作成
            for also_line in also_applies_lines:
                duplicate_comment = ParsedComment(
                    file_path=file_path,
                    line_range=also_line,
                    title=title,
                    content=content,
                    section_type=section_type,
                    raw_text=match.group(0),
                    is_duplicate=True,
                )
                comments.append(duplicate_comment)

        return comments

    def _find_comment_end(self, text: str, start_pos: int) -> int:
        """
        コメントの終了位置を特定

        Args:
            text: テキスト
            start_pos: コメント開始位置

        Returns:
            コメント終了位置
        """
        # 次の行番号コメントを探す
        next_comment = self.line_comment_pattern.search(text, start_pos)
        if next_comment:
            return next_comment.start()

        # "---" 区切りを探す
        divider_match = re.search(r"\n---\n", text[start_pos:])
        if divider_match:
            return start_pos + divider_match.start()

        # セクション終了まで
        return len(text)

    def _extract_also_applies_to(self, content: str) -> List[str]:
        """
        "Also applies to:" から適用行番号を抽出

        Args:
            content: コメント内容

        Returns:
            適用対象の行番号リスト
        """
        match = self.also_applies_pattern.search(content)
        if not match:
            return []

        lines_text = match.group(1)
        # "123-456, 789-800" のような形式をパース
        line_ranges = []
        for line_range in lines_text.split(","):
            line_range = line_range.strip()
            if line_range:
                line_ranges.append(line_range)

        return line_ranges

    def get_section_statistics(self, comments: List[ParsedComment]) -> Dict[str, Dict]:
        """
        セクション別統計情報を取得

        Args:
            comments: 解析済みコメントリスト

        Returns:
            セクション別統計辞書
        """
        stats = {}

        for section_type in CommentSection:
            section_comments = [c for c in comments if c.section_type == section_type]
            unique_comments = [c for c in section_comments if not c.is_duplicate]
            duplicate_comments = [c for c in section_comments if c.is_duplicate]

            stats[section_type.value] = {
                "total": len(section_comments),
                "unique": len(unique_comments),
                "duplicates": len(duplicate_comments),
                "files": len(set(c.file_path for c in section_comments)),
            }

        return stats

    def _extract_declared_count(
        self, section_match: re.Match, section_type: CommentSection
    ) -> Optional[int]:
        """
        セクション宣言から数値を抽出

        Args:
            section_match: セクションパターンのマッチオブジェクト
            section_type: セクションタイプ

        Returns:
            宣言された数値、見つからない場合はNone
        """
        try:
            # グループ1に数値が含まれているはず
            if section_match.groups():
                declared_count = int(section_match.group(1))
                self.logger.debug(f"セクション {section_type.value} 宣言数値: {declared_count}")
                return declared_count
        except (ValueError, IndexError) as e:
            self.logger.warning(f"セクション {section_type.value} 数値抽出失敗: {e}")

        return None

    def _align_with_declared_count(
        self,
        extracted_comments: List[ParsedComment],
        declared_count: Optional[int],
        section_type: CommentSection,
    ) -> List[ParsedComment]:
        """
        抽出されたコメントをCodeRabbitの宣言数値に合わせて調整

        Args:
            extracted_comments: 抽出されたコメントリスト
            declared_count: CodeRabbitが宣言した数値
            section_type: セクションタイプ

        Returns:
            宣言数値に調整されたコメントリスト
        """
        extracted_count = len(extracted_comments)

        # 宣言数値が取得できない場合は、抽出されたものをそのまま返す
        if declared_count is None:
            self.logger.debug(
                f"セクション {section_type.value}: 宣言数値なし、抽出結果 {extracted_count}件をそのまま使用"
            )
            return extracted_comments

        # 抽出数と宣言数が一致する場合
        if extracted_count == declared_count:
            self.logger.debug(f"セクション {section_type.value}: {extracted_count}件 (一致)")
            return extracted_comments

        # 抽出数が宣言数より多い場合は制限
        if extracted_count > declared_count:
            limited_comments = extracted_comments[:declared_count]
            self.logger.info(
                f"セクション {section_type.value}: {extracted_count}件 → {declared_count}件に調整 "
                f"(CodeRabbit宣言数値に合わせて-{extracted_count - declared_count}件)"
            )
            return limited_comments

        # 抽出数が宣言数より少ない場合
        if extracted_count < declared_count:
            # Actionableコメントは別途inline comments APIから取得されるため、summary解析では抽出漏れが正常
            if section_type == CommentSection.ACTIONABLE:
                self.logger.debug(
                    f"セクション {section_type.value}: 抽出 {extracted_count}件 < 宣言 {declared_count}件 "
                    f"(Actionableコメントは別APIから取得済み)"
                )
            else:
                self.logger.warning(
                    f"セクション {section_type.value}: 抽出 {extracted_count}件 < 宣言 {declared_count}件 "
                    f"(抽出漏れの可能性、そのまま返します)"
                )
            return extracted_comments

        return extracted_comments
