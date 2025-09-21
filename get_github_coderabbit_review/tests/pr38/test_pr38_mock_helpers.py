#!/usr/bin/env python3
"""
PR38テスト用のモックヘルパー関数
GitHub CLIコマンドの応答を詳細に制御する
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class PR38MockHelper:
    """PR38のモックデータを管理するヘルパークラス"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self._load_all_mock_data()

    def _load_all_mock_data(self):
        """全てのモックデータを読み込む"""
        self.pr_data = self._load_json("pr38_mock_data.json")
        self.inline_comments = self._load_json("pr38_inline_comments.json")
        self.reviews = self._load_json("pr38_reviews.json")
        self.files = self._load_json("pr38_files.json")

    def _load_json(self, filename: str) -> Any:
        """JSONファイルを読み込む"""
        # tests/pr38/mock_dataディレクトリ内のファイルを参照
        file_path = self.repo_root / "tests" / "pr38" / "mock_data" / filename
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def mock_github_cli_command(self, command_args: List[str]) -> str:
        """GitHub CLIコマンドをモックして適切なレスポンスを返す"""
        cmd_str = " ".join(command_args)

        # gh pr view コマンド
        if self._is_pr_view_command(cmd_str):
            return self._handle_pr_view_command(cmd_str)

        # gh api コマンド（各種エンドポイント）
        elif self._is_api_command(cmd_str):
            return self._handle_api_command(cmd_str)

        # その他のコマンド
        else:
            return ""

    def _is_pr_view_command(self, cmd: str) -> bool:
        """pr viewコマンドかどうか判定"""
        return "pr view" in cmd and "--json" in cmd

    def _is_api_command(self, cmd: str) -> bool:
        """API コマンドかどうか判定"""
        return "gh api" in cmd or "api repos/" in cmd

    def _handle_pr_view_command(self, cmd: str) -> str:
        """pr view コマンドの処理"""
        # PR番号とリポジトリを確認
        if "38" in cmd and "yohi/dots" in cmd:
            return json.dumps(self.pr_data, ensure_ascii=False)

        return json.dumps({"error": "PR not found"})

    def _handle_api_command(self, cmd: str) -> str:
        """API コマンドの処理"""
        # インラインコメントAPI
        if "pulls/38/comments" in cmd:
            return json.dumps(self.inline_comments, ensure_ascii=False)

        # レビューAPI
        elif "pulls/38/reviews" in cmd:
            return json.dumps(self.reviews, ensure_ascii=False)

        # ファイル一覧API
        elif "pulls/38/files" in cmd:
            return json.dumps(self.files, ensure_ascii=False)

        # その他のAPI
        else:
            return json.dumps([])

    def get_expected_pr_context(self) -> Dict[str, Any]:
        """期待されるPRコンテキストデータを返す"""
        return {
            "number": 38,
            "title": "claude周り更新",
            "url": "https://github.com/yohi/dots/pull/38",
            "state": "OPEN",
            "files_changed": 6,
            "total_comments": 8,  # 3 actionable + 5 nitpick
            "actionable_comments": 3,
            "nitpick_comments": 5,
        }

    def get_expected_files(self) -> List[Dict[str, Any]]:
        """期待される変更ファイル一覧を返す"""
        return [
            {
                "filename": "claude/claude-settings.json",
                "status": "modified",
                "additions": 5,
                "deletions": 1,
                "changes": 6,
            },
            {
                "filename": "claude/statusline.sh",
                "status": "added",
                "additions": 7,
                "deletions": 0,
                "changes": 7,
            },
            {
                "filename": "mk/help.mk",
                "status": "modified",
                "additions": 2,
                "deletions": 0,
                "changes": 2,
            },
            {
                "filename": "mk/install.mk",
                "status": "modified",
                "additions": 26,
                "deletions": 6,
                "changes": 32,
            },
            {
                "filename": "mk/setup.mk",
                "status": "modified",
                "additions": 28,
                "deletions": 64,
                "changes": 92,
            },
            {
                "filename": "mk/variables.mk",
                "status": "modified",
                "additions": 2,
                "deletions": 1,
                "changes": 3,
            },
        ]

    def get_expected_actionable_items(self) -> List[Dict[str, str]]:
        """期待されるアクション可能なアイテム一覧を返す"""
        return [
            {
                "title": "ユーザー固定パスを$HOMEに置換＋失敗時の扱いを追加（移植性/堅牢性）",
                "file": "claude/statusline.sh",
                "lines": "4-7",
                "description": "/home/y_ohi固定は他環境で壊れます。bunx利用でグローバル未導入でも実行可に。",
            },
            {
                "title": "`bun install -g ccusage`は誤用—`bun add -g`または`bunx`を使用",
                "file": "mk/install.mk",
                "lines": "1390-1403",
                "description": "Bunのグローバル導入は`bun add -g <pkg>`です。現状だと期待通りにバイナリが配置されない可能性があります。",
            },
            {
                "title": "`$(date ...)`がMake展開で空になる—バックアップファイル名が壊れます",
                "file": "mk/setup.mk",
                "lines": "539-545",
                "description": "シェル実行時のコマンド置換は`$$(...)`が必要です。現状だと`.backup.`のような固定名になり上書き事故のリスクがあります。",
            },
        ]

    def get_expected_nitpick_items(self) -> List[Dict[str, str]]:
        """期待されるnitpickアイテム一覧を返す"""
        return [
            {
                "title": "PHONYに`install-packages-gemini-cli`も追加してください",
                "file": "mk/variables.mk",
                "lines": "19-20",
                "description": "ヘルプに掲載され、エイリアスも定義されていますが、PHONY未登録です。",
            },
            {
                "title": "リンク元の存在チェックを追加してください（壊れたシンボリックリンク防止）",
                "file": "mk/setup.mk",
                "lines": "543-545",
                "description": "ln -sfn前にソース有無を検証し、欠如時は警告してスキップすると運用が安定します。",
            },
            {
                "title": "`setup-config-claude`と`setup-config-lazygit`の二重定義を解消",
                "file": "mk/setup.mk",
                "lines": "599-602",
                "description": "上部(行 513–528)にも同名エイリアスがあります。重複は混乱の元なので片方へ集約を。",
            },
            {
                "title": "ヘルプにエイリアス`install-ccusage`も載せると発見性が上がります",
                "file": "mk/help.mk",
                "lines": "27-28",
                "description": "直接ターゲットを案内したい場合に便利です。",
            },
            {
                "title": "PATH拡張の変数展開を統一（可搬性）",
                "file": "mk/install.mk",
                "lines": "1392-1399",
                "description": "$PATHより$$PATHの方がMakeの二重展開を避けられ、意図どおりにシェル時点で連結されます。",
            },
            {
                "title": "完了メッセージに新配置(~/.claude)の注意を一言追記",
                "file": "mk/setup.mk",
                "lines": "565-569",
                "description": "利用者が旧パス(~/.config/claude)を探さないよう明示しておくと親切です。",
            },
            {
                "title": "LGTM（エイリアス定義）およびインデント修正のみで挙動は不変—OK",
                "file": "mk/install.mk",
                "lines": "1387-1388, 1831-1836",
                "description": "install-packages-gemini-cli: install-gemini-cliの橋渡しは妥当です。視認性が向上しています。",
            },
        ]

    def validate_output_structure_detailed(self, output: str) -> Dict[str, bool]:
        """出力構造の詳細検証を行い、結果を辞書で返す"""
        results = {}

        # 必須セクションの検証
        required_sections = [
            "# PR Context",
            "## Summary",
            "## File Changes",
            "## Review Comments",
            "## Actionable Items",
            "## Prompt for AI Agents",
        ]

        for section in required_sections:
            results[
                f"section_{section.replace('# ', '').replace('## ', '').replace(' ', '_').lower()}"
            ] = (section in output)

        # XMLタグの検証
        xml_tags = [
            ("<pr_context>", "</pr_context>"),
            ("<changed_files>", "</changed_files>"),
            ("<review_comments>", "</review_comments>"),
        ]

        for open_tag, close_tag in xml_tags:
            tag_name = open_tag.strip("<>")
            results[f"xml_{tag_name}"] = open_tag in output and close_tag in output

        # PR基本情報の検証
        results["pr_number"] = "PR #38" in output
        results["pr_title"] = "claude周り更新" in output
        results["pr_url"] = "https://github.com/yohi/dots/pull/38" in output

        # ファイル数の検証
        results["files_count"] = "6 files changed" in output

        # コメント数の検証（概算）
        results["has_actionable_items"] = "actionable" in output.lower()
        results["has_nitpick_items"] = "nitpick" in output.lower()

        return results

    def extract_actionable_items_from_output(self, output: str) -> List[str]:
        """出力からアクション可能なアイテムを抽出"""
        actionable_items = []

        # Actionable Itemsセクションを探す
        lines = output.split("\n")
        in_actionable_section = False

        for line in lines:
            if "## Actionable Items" in line:
                in_actionable_section = True
                continue
            elif line.startswith("## ") and in_actionable_section:
                break
            elif in_actionable_section and line.strip() and not line.startswith("#"):
                actionable_items.append(line.strip())

        return actionable_items

    def extract_file_changes_from_output(self, output: str) -> List[str]:
        """出力からファイル変更情報を抽出"""
        file_changes = []

        # changed_filesタグの内容を抽出
        start_tag = "<changed_files>"
        end_tag = "</changed_files>"

        start_idx = output.find(start_tag)
        end_idx = output.find(end_tag)

        if start_idx != -1 and end_idx != -1:
            files_section = output[start_idx + len(start_tag) : end_idx]
            lines = files_section.strip().split("\n")

            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    file_changes.append(line)

        return file_changes
