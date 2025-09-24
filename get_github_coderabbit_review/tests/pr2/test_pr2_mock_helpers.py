#!/usr/bin/env python3
"""
PR2テスト用のモックヘルパー関数
GitHub CLIコマンドの応答を詳細に制御する
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class PR2MockHelper:
    """PR2のモックデータを管理するヘルパークラス"""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self._load_all_mock_data()

    def _load_all_mock_data(self):
        """全てのモックデータを読み込む"""
        self.pr_basic_info = self._load_json("pr2_basic_info.json")
        self.pr_files = self._load_json("pr2_files.json")
        self.pr_reviews = self._load_json("pr2_reviews.json")
        self.pr_comments = self._load_json("pr2_comments.json")

    def _load_json(self, filename: str) -> Any:
        """JSONファイルを読み込む"""
        # tests/pr2/mock_dataディレクトリ内のファイルを参照
        file_path = self.repo_root / "tests" / "pr2" / "mock_data" / filename
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def mock_github_cli_command(self, command_args: List[str]) -> str:
        """GitHub CLIコマンドをモックして適切なレスポンスを返す"""
        cmd_str = " ".join(command_args)
        print(f"DEBUG: Mocking command: {cmd_str}")

        # gh pr view コマンド
        if self._is_pr_view_command(cmd_str):
            response = self._handle_pr_view_command(cmd_str)
            print(f"DEBUG: PR view response length: {len(response)}")
            return response

        # gh api コマンド（各種エンドポイント）
        elif self._is_api_command(cmd_str):
            response = self._handle_api_command(cmd_str)
            print(f"DEBUG: API response length: {len(response)}")
            return response

        # その他のコマンド
        else:
            print(f"DEBUG: Command not matched: {cmd_str}")
            return ""

    def _is_pr_view_command(self, cmd: str) -> bool:
        """pr viewコマンドかどうか判定"""
        return "gh pr view" in cmd and ("pull/2" in cmd or "lazygit-llm-commit-generator" in cmd)

    def _is_api_command(self, cmd: str) -> bool:
        """apiコマンドかどうか判定"""
        return "gh api" in cmd and (
            "yohi/lazygit-llm-commit-generator" in cmd or "repos/yohi" in cmd
        )

    def _handle_pr_view_command(self, cmd: str) -> str:
        """gh pr viewコマンドのレスポンスを処理"""
        # 基本情報を取得
        if "--json" in cmd and "files" not in cmd:
            return json.dumps(self.pr_basic_info, ensure_ascii=False, indent=2)

        # ファイル情報を取得
        elif "--json files" in cmd:
            return json.dumps(self.pr_files, ensure_ascii=False, indent=2)

        else:
            return ""

    def _handle_api_command(self, cmd: str) -> str:
        """gh apiコマンドのレスポンスを処理"""
        # レビューを取得
        if "/pulls/2/reviews" in cmd:
            return json.dumps(self.pr_reviews, ensure_ascii=False, indent=2)

        # コメントを取得
        elif "/pulls/2/comments" in cmd:
            return json.dumps(self.pr_comments, ensure_ascii=False, indent=2)

        else:
            return ""

    def get_mock_data_summary(self) -> Dict[str, Any]:
        """モックデータのサマリーを返す"""
        return {
            "pr_number": self.pr_basic_info.get("number", 2),
            "pr_title": self.pr_basic_info.get("title", ""),
            "changed_files": self.pr_basic_info.get("changedFiles", 0),
            "additions": self.pr_basic_info.get("additions", 0),
            "deletions": self.pr_basic_info.get("deletions", 0),
            "total_reviews": len(self.pr_reviews) if isinstance(self.pr_reviews, list) else 0,
            "total_comments": len(self.pr_comments) if isinstance(self.pr_comments, list) else 0,
        }
