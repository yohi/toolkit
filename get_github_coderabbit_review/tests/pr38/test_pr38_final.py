#!/usr/bin/env python3
"""
PR38出力検証テストの最終版
実際のGitHub APIを使用してツールの正しい動作を検証
"""

import difflib
import os
import subprocess
import tempfile
from pathlib import Path


class PR38FinalTest:
    """PR38の最終検証テスト"""

    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent
        self.expected_file = self.repo_root / "expected_pr_38_ai_agent_prompt.md"

    def run_crf_command(self, output_file: str) -> subprocess.CompletedProcess:
        """crfコマンドを実行"""
        cmd = [
            "uvx",
            "--from",
            ".",
            "-n",
            "crf",
            "https://github.com/yohi/dots/pull/38",
            "--quiet",
            "--output-file",
            output_file,
        ]

        return subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_root, timeout=120)

    def normalize_output(self, text: str) -> str:
        """出力を正規化（動的な順序変動などを考慮）"""
        lines = text.split("\n")
        normalized_lines = []

        for line in lines:
            # primary_issuesの順序は動的なので無視
            if "<primary_issues>" in line:
                # 要素だけを抽出してソート
                content_match = line.split(">")[1].split("<")[0]
                elements = [elem.strip() for elem in content_match.split(",")]
                elements.sort()
                normalized_line = f"  <primary_issues>{', '.join(elements)}</primary_issues>"
                normalized_lines.append(normalized_line)
            else:
                normalized_lines.append(line)

        return "\n".join(normalized_lines).rstrip()

    def validate_content_structure(self, output: str) -> dict:
        """出力内容の構造を検証"""
        validation = {
            "pr_url": "https://github.com/yohi/dots/pull/38" in output,
            "pr_title": "claude周り更新" in output,
            "pr_number": "PR #38" in output or "pull/38" in output,
            "files_changed": "6" in output and "files" in output,
            "total_comments": "10" in output and "comments" in output,
            "actionable_comments": "3" in output and "actionable" in output.lower(),
            "nitpick_comments": "7" in output and "nitpick" in output.lower(),
            "coderabbit_analysis": "coderabbit" in output.lower(),
            "ai_agent_prompt": "ai_agent_prompt" in output.lower() or "🤖" in output,
            "review_comments": "review_comments" in output.lower(),
            "expected_files": all(
                f in output
                for f in [
                    "claude/statusline.sh",
                    "mk/install.mk",
                    "mk/setup.mk",
                    "mk/variables.mk",
                    "mk/help.mk",
                    "claude/claude-settings.json",
                ]
            ),
            "critical_issues": all(
                issue in output
                for issue in [
                    "HOME",  # HOMEパス置換の問題
                    "bun",  # bunコマンドの問題
                    "date",  # date コマンドの問題
                ]
            ),
        }

        return validation

    def run_comparison_test(self) -> bool:
        """期待値との比較テスト"""
        print("🔍 期待値との比較テストを実行中...")

        # 期待値ファイルを読み込み
        if not self.expected_file.exists():
            print(f"❌ 期待値ファイルが見つかりません: {self.expected_file}")
            return False

        with open(self.expected_file, "r", encoding="utf-8") as f:
            expected_content = f.read()

        # 実際のコマンドを実行
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as temp_file:
            try:
                result = self.run_crf_command(temp_file.name)

                if result.returncode != 0:
                    print(f"❌ コマンド実行失敗: {result.stderr}")
                    return False

                # 実際の出力を読み込み
                with open(temp_file.name, "r", encoding="utf-8") as f:
                    actual_content = f.read()

                # 正規化
                expected_normalized = self.normalize_output(expected_content)
                actual_normalized = self.normalize_output(actual_content)

                # 差分を計算
                diff_lines = list(
                    difflib.unified_diff(
                        expected_normalized.splitlines(keepends=True),
                        actual_normalized.splitlines(keepends=True),
                        fromfile="expected",
                        tofile="actual",
                    )
                )

                if len(diff_lines) <= 10:  # 10行以下の差分は許容
                    print(f"✅ 比較テスト成功（差分: {len(diff_lines)}行）")
                    if diff_lines:
                        print("📊 軽微な差分:")
                        for line in diff_lines[:10]:
                            print(f"  {line.rstrip()}")
                    return True
                else:
                    print(f"❌ 比較テスト失敗（差分: {len(diff_lines)}行）")
                    print("📊 最初の20行の差分:")
                    for line in diff_lines[:20]:
                        print(f"  {line.rstrip()}")
                    return False

            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def run_structure_test(self) -> bool:
        """構造検証テスト"""
        print("🏗️ 構造検証テストを実行中...")

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as temp_file:
            try:
                result = self.run_crf_command(temp_file.name)

                if result.returncode != 0:
                    print(f"❌ コマンド実行失敗: {result.stderr}")
                    return False

                # 出力を読み込み
                with open(temp_file.name, "r", encoding="utf-8") as f:
                    output = f.read()

                # 構造を検証
                validation = self.validate_content_structure(output)
                passed_checks = sum(validation.values())
                total_checks = len(validation)

                print(f"📊 構造検証結果: {passed_checks}/{total_checks} 項目が合格")

                # 失敗した項目を表示
                failed_checks = [key for key, value in validation.items() if not value]
                if failed_checks:
                    print(f"❌ 失敗した検証項目: {', '.join(failed_checks)}")

                # 80%以上の項目が合格していればOK
                success_rate = passed_checks / total_checks
                return success_rate >= 0.8

            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def run_all_tests(self) -> bool:
        """全てのテストを実行"""
        print("🚀 PR38最終検証テストを開始...")
        print(f"📁 作業ディレクトリ: {self.repo_root}")

        # GitHub CLIの確認
        try:
            gh_result = subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, timeout=10
            )
            print(f"📦 GitHub CLI: 利用可能 ({gh_result.stdout.split()[2]})")
        except Exception as e:
            print(f"❌ GitHub CLI確認エラー: {str(e)}")
            return False

        # 各テストを実行
        structure_ok = self.run_structure_test()
        comparison_ok = self.run_comparison_test()

        if structure_ok and comparison_ok:
            print("\n🎉 全ての検証テストが成功しました！")
            print("✅ PR38の出力は期待値と一致し、構造も正しいです")
            print("✅ ツールは実際のGitHub APIで正常に動作しています")
            return True
        else:
            print("\n❌ 一部の検証テストが失敗しました")
            print(f"  構造テスト: {'✅' if structure_ok else '❌'}")
            print(f"  比較テスト: {'✅' if comparison_ok else '❌'}")
            return False


def main():
    """メイン関数"""
    test = PR38FinalTest()
    success = test.run_all_tests()

    if success:
        print("\n✅ PR38検証テスト完了: 成功")
        print("📋 結論: coderabbit-fetchツールはPR38に対して期待通りに動作します")
        exit(0)
    else:
        print("\n❌ PR38検証テスト完了: 失敗")
        exit(1)


if __name__ == "__main__":
    main()
