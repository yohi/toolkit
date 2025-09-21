#!/usr/bin/env python3
"""
PR2（yohi/lazygit-llm-commit-generator/pull/2）のquiet mode動作確認テスト

現在の実行結果を正として、uvxコマンドをサブプロセスで実行してテストします。
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TestPR2QuietMode(unittest.TestCase):
    """PR2のquiet mode動作テスト"""

    def setUp(self):
        """テストセットアップ"""
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent.parent
        self.pr_url = "https://github.com/yohi/lazygit-llm-commit-generator/pull/2"

        # 期待値ファイルを読み込み
        expected_file = self.test_dir / "expected_pr_2_ai_agent_prompt.md"
        if expected_file.exists():
            with open(expected_file, "r", encoding="utf-8") as f:
                self.expected_output = f.read()
        else:
            self.expected_output = None

    def test_pr2_quiet_mode_execution(self):
        """PR2のquiet mode実行テスト（実際のuvx実行）"""
        # uvxコマンドを実行
        cmd = ["uvx", "--from", str(self.project_root), "-n", "crf", self.pr_url, "--quiet"]

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=60
            )

            # 実行が成功することを確認
            if result.returncode != 0:
                print(f"Command failed with return code {result.returncode}")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                self.fail(f"uvx command failed: {result.stderr}")

            output = result.stdout

            # 基本的な構造要素を確認
            required_sections = [
                "# CodeRabbit Review Analysis - AI Agent Prompt",
                "<role>",
                "<core_principles>",
                "<analysis_steps>",
                "<priority_matrix>",
                "<pull_request_context>",
                "<coderabbit_review_summary>",
            ]

            for section in required_sections:
                with self.subTest(section=section):
                    self.assertIn(section, output, f"Required section missing: {section}")

            # PR情報の確認
            self.assertIn("feat(task-01): Implement project structure and core interfaces", output)
            self.assertIn("https://github.com/yohi/lazygit-llm-commit-generator/pull/2", output)
            self.assertIn("yohi", output)

            # ファイル数の確認
            self.assertIn("10", output)  # 変更ファイル数

            print("✅ PR2 quiet mode execution test passed")

        except subprocess.TimeoutExpired:
            self.fail("Command timed out after 60 seconds")
        except Exception as e:
            self.fail(f"Test execution failed: {e}")

    def test_pr2_output_structure(self):
        """PR2の出力構造テスト（ローカル期待値との比較）"""
        if not self.expected_output:
            self.skipTest("Expected output file not found")

        # uvxコマンドを実行
        cmd = ["uvx", "--from", str(self.project_root), "-n", "crf", self.pr_url, "--quiet"]

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                self.fail(f"uvx command failed: {result.stderr}")

            output = result.stdout

            # 期待値から重要なセクションを抽出して確認
            expected_sections = [
                "# CodeRabbit Review Analysis - AI Agent Prompt",
                "<role>",
                "<core_principles>",
                "<analysis_steps>",
                "<priority_matrix>",
                "<impact_scope>",
                "<pull_request_context>",
                "<coderabbit_review_summary>",
                "<comment_metadata>",
                "# Analysis Task",
            ]

            for section in expected_sections:
                if section in self.expected_output:
                    with self.subTest(section=section):
                        self.assertIn(section, output, f"Expected section missing: {section}")

            print("✅ PR2 output structure test passed")

        except subprocess.TimeoutExpired:
            self.fail("Command timed out after 60 seconds")
        except Exception as e:
            self.fail(f"Test execution failed: {e}")

    def test_mock_data_validation(self):
        """モックデータファイルの存在と構造確認"""
        mock_data_dir = self.test_dir / "mock_data"

        # 必要なモックファイルが存在することを確認
        required_files = [
            "pr2_basic_info.json",
            "pr2_files.json",
            "pr2_reviews.json",
            "pr2_comments.json",
        ]

        for filename in required_files:
            file_path = mock_data_dir / filename
            with self.subTest(file=filename):
                self.assertTrue(file_path.exists(), f"Mock file missing: {filename}")

                # JSONファイルの構造を確認
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                            self.assertIsNotNone(data, f"Invalid JSON in {filename}")
                        except json.JSONDecodeError as e:
                            self.fail(f"JSON decode error in {filename}: {e}")

        # 基本情報ファイルの構造確認
        basic_info_file = mock_data_dir / "pr2_basic_info.json"
        if basic_info_file.exists():
            with open(basic_info_file, "r", encoding="utf-8") as f:
                basic_info = json.load(f)

            required_keys = [
                "url",
                "title",
                "number",
                "author",
                "changedFiles",
                "additions",
                "deletions",
            ]
            for key in required_keys:
                with self.subTest(key=key):
                    self.assertIn(key, basic_info, f"Required key missing in basic_info: {key}")

        print("✅ Mock data validation passed")


def main():
    """テスト実行メイン関数"""
    print("🧪 Starting PR2 quiet mode tests...")

    # テストローダーでテストを発見・実行
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPR2QuietMode)

    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 結果サマリー
    if result.wasSuccessful():
        print("🎉 All PR2 tests passed!")
        return 0
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        for failure in result.failures:
            print(f"FAILURE: {failure[0]}")
            print(f"  {failure[1]}")
        for error in result.errors:
            print(f"ERROR: {error[0]}")
            print(f"  {error[1]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
