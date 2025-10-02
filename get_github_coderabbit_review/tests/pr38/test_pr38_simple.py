#!/usr/bin/env python3
"""
PR38の出力検証テスト（pytest依存なし版）
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

try:
    from .test_pr38_mock_helpers import PR38MockHelper
except ImportError:
    from test_pr38_mock_helpers import PR38MockHelper


class SimplePR38Test:
    """PR38の出力が正しいことを検証するシンプルなテストクラス"""

    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.expected_file = (
            Path(__file__).parent / "expected" / "expected_pr_38_ai_agent_prompt.md"
        )
        self.mock_helper = PR38MockHelper(self.repo_root)
        self.python_executable = self._find_python_executable()

    def _find_python_executable(self) -> str:
        """環境に適したPython実行可能ファイルを検出"""
        # 1. python3を優先的に検索
        python3_path = shutil.which("python3")
        if python3_path:
            return python3_path

        # 2. pythonを検索
        python_path = shutil.which("python")
        if python_path:
            return python_path

        # 3. sys.executableをフォールバック（Cursor環境でも-mが使える場合）
        return sys.executable

    def run_crf_with_mock(self) -> str:
        """モックを使ってcrfコマンドを実行し、出力を返す"""

        # 元のsubprocess.runを保存
        original_run = subprocess.run

        with patch("subprocess.run") as mock_subprocess:

            def mock_run(args, **kwargs):
                # GitHub CLIコマンドの場合はモックデータを返す
                if isinstance(args, list) and len(args) > 0 and "gh" in args[0]:
                    result = Mock()
                    result.returncode = 0
                    result.stdout = self.mock_helper.mock_github_cli_command(args)
                    result.stderr = ""
                    return result
                elif (
                    isinstance(args, list)
                    and len(args) > 0
                    and any("gh" in str(arg) for arg in args)
                ):
                    result = Mock()
                    result.returncode = 0
                    result.stdout = self.mock_helper.mock_github_cli_command(args)
                    result.stderr = ""
                    return result
                else:
                    # その他のコマンドは実際に実行
                    return original_run(args, **kwargs)

            mock_subprocess.side_effect = mock_run

            # coderabbit-fetchを実行
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as temp_file:
                try:
                    cmd = [
                        self.python_executable,
                        "-m",
                        "coderabbit_fetcher.cli.main",
                        "https://github.com/yohi/dots/pull/38",
                        "--quiet",
                        "--output-file",
                        temp_file.name,
                    ]

                    env = os.environ.copy()
                    env["PYTHONPATH"] = str(self.repo_root)
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, cwd=self.repo_root, env=env
                    )

                    if result.returncode != 0:
                        raise Exception(
                            f"Command failed with return code {result.returncode}: {result.stderr}"
                        )

                    # 出力ファイルの内容を読み込み
                    with open(temp_file.name, encoding="utf-8") as f:
                        return f.read()

                finally:
                    # 一時ファイルを削除
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)

    def test_output_structure(self, output: str) -> bool:
        """出力構造の検証"""
        print("✅ 出力構造の検証...")

        validation_results = self.mock_helper.validate_output_structure_detailed(output)
        failed_checks = [key for key, value in validation_results.items() if not value]

        if failed_checks:
            print(f"❌ 構造検証失敗: {', '.join(failed_checks)}")
            return False
        else:
            print("✅ 構造検証成功")
            return True

    def test_output_content(self, output: str) -> bool:
        """出力内容の検証"""
        print("✅ 出力内容の検証...")

        try:
            expected_context = self.mock_helper.get_expected_pr_context()
            expected_files = self.mock_helper.get_expected_files()

            # PR基本情報の検証
            assert f"PR #{expected_context['number']}" in output
            assert expected_context["title"] in output
            assert expected_context["url"] in output
            print(f"  ✅ PR基本情報: PR #{expected_context['number']}, {expected_context['title']}")

            # 変更ファイル数の検証
            assert f"{expected_context['files_changed']} files changed" in output
            print(f"  ✅ ファイル変更数: {expected_context['files_changed']} files")

            # ファイル名の存在確認
            for file_info in expected_files:
                assert file_info["filename"] in output
            print(f"  ✅ 変更ファイル一覧: {len(expected_files)}個のファイルが確認されました")

            # CodeRabbitコメント作成者の確認
            assert "coderabbitai[bot]" in output or "CodeRabbit" in output
            print("  ✅ CodeRabbitコメント作成者が確認されました")

            print("✅ 内容検証成功")
            return True

        except AssertionError as e:
            print(f"❌ 内容検証失敗: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ 内容検証エラー: {str(e)}")
            return False

    def test_actionable_items(self, output: str) -> bool:
        """アクション可能なアイテムの検証"""
        print("✅ アクション可能なアイテムの検証...")

        try:
            actionable_items = self.mock_helper.extract_actionable_items_from_output(output)

            if len(actionable_items) < 3:
                print(f"❌ アクション可能なアイテムが不足: 期待3以上, 実際{len(actionable_items)}")
                return False

            # 特定のキーワードが含まれていることを確認
            output_text = " ".join(actionable_items)
            expected_keywords = ["HOME", "bun", "date"]

            found_keywords = []
            for keyword in expected_keywords:
                if keyword in output_text:
                    found_keywords.append(keyword)

            print(f"  ✅ アクション可能なアイテム数: {len(actionable_items)}")
            print(f"  ✅ 見つかったキーワード: {found_keywords}")

            if len(found_keywords) < 2:
                print(f"❌ 期待されるキーワードが不足: {expected_keywords}")
                return False

            print("✅ アクション可能なアイテム検証成功")
            return True

        except Exception as e:
            print(f"❌ アクション可能なアイテム検証エラー: {str(e)}")
            return False

    def run_all_tests(self):
        """全てのテストを実行"""
        print("🚀 PR38 出力検証テストを開始...")
        print(f"📁 作業ディレクトリ: {self.repo_root}")

        try:
            # crfコマンドを実行
            print("\n📦 coderabbit-fetch (crf) コマンドを実行中...")
            output = self.run_crf_with_mock()

            if not output:
                print("❌ 出力が空です")
                return False

            print(f"📝 出力サイズ: {len(output)} 文字")

            # 各種テストを実行
            structure_ok = self.test_output_structure(output)
            content_ok = self.test_output_content(output)
            actionable_ok = self.test_actionable_items(output)

            # 結果判定
            if structure_ok and content_ok and actionable_ok:
                print("\n🎉 全てのテストが成功しました！")
                print("✅ PR38の出力は期待値と一致しています")
                return True
            else:
                print("\n❌ 一部のテストが失敗しました")
                return False

        except Exception as e:
            print(f"\n💥 テスト実行中にエラーが発生しました: {str(e)}")
            return False


def main():
    """メイン関数"""
    test = SimplePR38Test()
    success = test.run_all_tests()

    if success:
        print("\n✅ テスト完了: 成功")
        exit(0)
    else:
        print("\n❌ テスト完了: 失敗")
        exit(1)


if __name__ == "__main__":
    main()
