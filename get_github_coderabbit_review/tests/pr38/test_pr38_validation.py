#!/usr/bin/env python3
"""
PR38のGitHub CLIレスポンスをモックしてcoderabbit-fetchの出力を検証するテスト
"""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

try:
    from .test_pr38_mock_helpers import PR38MockHelper
except ImportError:
    from test_pr38_mock_helpers import PR38MockHelper


class TestPR38Validation:
    """PR38の出力が正しいことを検証するテストクラス"""

    @classmethod
    def setup_class(cls):
        """テストクラスの初期化"""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.expected_file = Path(__file__).parent / "expected" / "expected_pr_38_ai_agent_prompt.md"
        cls.mock_helper = PR38MockHelper(cls.repo_root)

    def test_pr38_output_validation(self):
        """PR38の実際の出力が期待値と一致することを検証"""

        # GitHub CLIコマンドをモックでパッチ
        with patch("subprocess.run") as mock_subprocess:
            # subprocess.run の戻り値をモック
            def mock_run(args, *_, **kwargs):
                # GitHub CLIコマンドの場合はモックデータを返す
                if "gh" in args:
                    result = Mock()
                    result.returncode = 0
                    result.stdout = self.mock_helper.mock_github_cli_command(args)
                    result.stderr = ""
                    return result

                # その他のコマンドは実際に実行
                return subprocess.run(args, capture_output=True, text=True, **kwargs)

            mock_subprocess.side_effect = mock_run

            # coderabbit-fetchを実行
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as temp_file:
                try:
                    # uvx でコマンドを実行（quietモード）
                    cmd = [
                        "uvx",
                        "--from",
                        ".",
                        "-n",
                        "crf",
                        "https://github.com/yohi/dots/pull/38",
                        "--quiet",
                        "--output",
                        temp_file.name,
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_root)

                    # コマンドが成功したか確認
                    assert result.returncode == 0, f"Command failed: {result.stderr}"

                    # 出力ファイルの内容を読み込み
                    with open(temp_file.name, encoding="utf-8") as f:
                        actual_output = f.read()

                    # 期待値ファイルの内容を読み込み
                    with open(self.expected_file, encoding="utf-8") as f:
                        expected_output = f.read()

                    # 出力の検証
                    self._validate_output_structure(actual_output)
                    self._validate_output_content(actual_output, expected_output)

                finally:
                    # 一時ファイルを削除
                    os.unlink(temp_file.name)

    def _validate_output_structure(self, output: str):
        """出力の基本構造を検証"""
        validation_results = self.mock_helper.validate_output_structure_detailed(output)

        # 全ての検証項目が True であることを確認
        failed_checks = [key for key, value in validation_results.items() if not value]

        if failed_checks:
            pytest.fail(f"Structure validation failed for: {', '.join(failed_checks)}")

    def _validate_output_content(self, actual: str, expected: str):
        """出力内容の詳細検証"""
        expected_context = self.mock_helper.get_expected_pr_context()
        expected_files = self.mock_helper.get_expected_files()
        expected_actionable = self.mock_helper.get_expected_actionable_items()
        expected_nitpick = self.mock_helper.get_expected_nitpick_items()

        # PR基本情報の検証
        assert f"PR #{expected_context['number']}" in actual
        assert expected_context["title"] in actual
        assert expected_context["url"] in actual

        # 変更ファイル数の検証
        assert f"{expected_context['files_changed']} files changed" in actual

        # ファイル名の存在確認
        for file_info in expected_files:
            assert (
                file_info["filename"] in actual
            ), f"Expected file not found: {file_info['filename']}"

        # actionable itemsの存在確認
        for item in expected_actionable[:3]:  # 主要なactionable items
            # タイトルの一部が含まれているかチェック
            title_parts = item["title"].split("—")[0].split("＋")[0]  # 最初の部分だけを使用
            assert any(
                part in actual for part in title_parts.split("を")
            ), f"Expected actionable item not found: {item['title'][:30]}..."

        # nitpick itemsの存在確認（一部）
        for item in expected_nitpick[:3]:  # 主要なnitpick items
            title_parts = item["title"].split("（")[0]  # カッコ前まで
            assert title_parts in actual or any(
                word in actual for word in title_parts.split()
            ), f"Expected nitpick item not found: {item['title'][:30]}..."

        # CodeRabbitコメント作成者の確認
        assert "coderabbitai[bot]" in actual or "CodeRabbit" in actual

    def test_dynamic_ordering_tolerance(self):
        """動的な順序変動に対する耐性テスト"""

        # primary_issuesフィールドなど、順序が動的に変わる可能性のある部分をテスト
        # 複数回実行して結果の一貫性を確認

        outputs = []
        for i in range(3):
            with patch("subprocess.run") as mock_subprocess:

                def mock_run(args, *_, **kwargs):
                    if "gh" in args:
                        result = Mock()
                        result.returncode = 0
                        result.stdout = self.mock_helper.mock_github_cli_command(args)
                        result.stderr = ""
                        return result
                    return subprocess.run(args, capture_output=True, text=True, **kwargs)

                mock_subprocess.side_effect = mock_run

                with tempfile.NamedTemporaryFile(
                    mode="w+", suffix=".md", delete=False
                ) as temp_file:
                    try:
                        cmd = [
                            "uvx",
                            "--from",
                            ".",
                            "-n",
                            "crf",
                            "https://github.com/yohi/dots/pull/38",
                            "--quiet",
                            "--output",
                            temp_file.name,
                        ]

                        result = subprocess.run(
                            cmd, capture_output=True, text=True, cwd=self.repo_root
                        )

                        assert result.returncode == 0

                        with open(temp_file.name, encoding="utf-8") as f:
                            outputs.append(f.read())

                    finally:
                        os.unlink(temp_file.name)

        # 基本構造は同じであることを確認
        for output in outputs:
            self._validate_output_structure(output)

        # 動的要素以外は一致することを確認
        # (primary_issues などの順序以外は同じ)
        stable_sections = []
        for output in outputs:
            # PR基本情報は一致するはず
            lines = output.split("\n")
            pr_context_lines = []
            in_pr_context = False

            for line in lines:
                if "<pr_context>" in line:
                    in_pr_context = True
                elif "</pr_context>" in line:
                    in_pr_context = False
                    pr_context_lines.append(line)
                    break
                elif in_pr_context:
                    pr_context_lines.append(line)

            stable_sections.append("\n".join(pr_context_lines))

        # PR context セクションは全て同じであることを確認
        for section in stable_sections[1:]:
            assert section == stable_sections[0], "PR context should be stable across runs"

    def test_actionable_items_extraction(self):
        """アクション可能なアイテムの抽出テスト"""
        with patch("subprocess.run") as mock_subprocess:

            def mock_run(args, *_, **kwargs):
                if "gh" in args:
                    result = Mock()
                    result.returncode = 0
                    result.stdout = self.mock_helper.mock_github_cli_command(args)
                    result.stderr = ""
                    return result
                return subprocess.run(args, capture_output=True, text=True, **kwargs)

            mock_subprocess.side_effect = mock_run

            with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as temp_file:
                try:
                    cmd = [
                        "uvx",
                        "--from",
                        ".",
                        "-n",
                        "crf",
                        "https://github.com/yohi/dots/pull/38",
                        "--quiet",
                        "--output",
                        temp_file.name,
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_root)

                    assert result.returncode == 0

                    with open(temp_file.name, encoding="utf-8") as f:
                        output = f.read()

                    # アクション可能なアイテムを抽出
                    actionable_items = self.mock_helper.extract_actionable_items_from_output(output)

                    # 最低限のアクション可能なアイテムが存在することを確認
                    assert (
                        len(actionable_items) >= 3
                    ), f"Expected at least 3 actionable items, got {len(actionable_items)}"

                    # 特定のキーワードが含まれていることを確認
                    output_text = " ".join(actionable_items)
                    expected_keywords = ["HOME", "bun", "date", "PATH"]

                    for keyword in expected_keywords:
                        assert (
                            keyword in output_text
                        ), f"Expected keyword '{keyword}' not found in actionable items"

                finally:
                    os.unlink(temp_file.name)

    def test_file_changes_extraction(self):
        """ファイル変更情報の抽出テスト"""
        with patch("subprocess.run") as mock_subprocess:

            def mock_run(args, *_, **kwargs):
                if "gh" in args:
                    result = Mock()
                    result.returncode = 0
                    result.stdout = self.mock_helper.mock_github_cli_command(args)
                    result.stderr = ""
                    return result
                return subprocess.run(args, capture_output=True, text=True, **kwargs)

            mock_subprocess.side_effect = mock_run

            with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as temp_file:
                try:
                    cmd = [
                        "uvx",
                        "--from",
                        ".",
                        "-n",
                        "crf",
                        "https://github.com/yohi/dots/pull/38",
                        "--quiet",
                        "--output",
                        temp_file.name,
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_root)

                    assert result.returncode == 0

                    with open(temp_file.name, encoding="utf-8") as f:
                        output = f.read()

                    # ファイル変更情報を抽出
                    file_changes = self.mock_helper.extract_file_changes_from_output(output)

                    # 期待されるファイルが含まれていることを確認
                    expected_files = self.mock_helper.get_expected_files()
                    file_changes_text = " ".join(file_changes)

                    for expected_file in expected_files:
                        assert (
                            expected_file["filename"] in file_changes_text
                        ), f"Expected file '{expected_file['filename']}' not found in file changes"

                finally:
                    os.unlink(temp_file.name)

    def test_error_handling(self):
        """エラーハンドリングのテスト"""

        # GitHub CLIが失敗する場合のテスト
        with patch("subprocess.run") as mock_subprocess:

            def mock_run_with_error(args, *_, **kwargs):
                if "gh" in args:
                    result = Mock()
                    result.returncode = 1
                    result.stdout = ""
                    result.stderr = "GitHub CLI error"
                    return result
                return subprocess.run(args, capture_output=True, text=True, **kwargs)

            mock_subprocess.side_effect = mock_run_with_error

            cmd = [
                "uvx",
                "--from",
                ".",
                "-n",
                "crf",
                "https://github.com/yohi/dots/pull/38",
                "--quiet",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_root)

            # エラーハンドリングが適切に動作することを確認
            # （具体的な動作はツールの実装による）
            assert (
                result.returncode != 0
                or "error" in result.stderr.lower()
                or "error" in result.stdout.lower()
            )


if __name__ == "__main__":
    # pytest として実行
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
