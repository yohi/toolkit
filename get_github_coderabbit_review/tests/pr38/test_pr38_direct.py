#!/usr/bin/env python3
"""
PR38の出力検証テスト（直接実行版）
まず実際の動作を確認してからモック戦略を決定する
"""

import os
import subprocess
import tempfile
from pathlib import Path


def test_direct_execution():
    """実際にcrfコマンドを実行してエラーを確認"""
    repo_root = Path(__file__).parent.parent.parent
    print("🚀 直接実行テストを開始...")
    print(f"📁 作業ディレクトリ: {repo_root}")

    # まず、GitHub CLIが利用できるかチェック
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True, timeout=10)
        print(f"📦 GitHub CLI: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ GitHub CLI確認エラー: {str(e)}")

    # coderabbit-fetchを実行（モックなし）
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
                "--output-file",
                temp_file.name,
            ]

            print(f"🔧 実行コマンド: {' '.join(cmd)}")

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=repo_root, timeout=120  # 2分のタイムアウト
            )

            print(f"📊 終了コード: {result.returncode}")
            if result.stdout:
                print(f"📤 標準出力:\n{result.stdout}")
            if result.stderr:
                print(f"📥 標準エラー:\n{result.stderr}")

            if result.returncode == 0:
                # 出力ファイルの内容を確認
                if os.path.exists(temp_file.name):
                    with open(temp_file.name, "r", encoding="utf-8") as f:
                        output = f.read()

                    print(f"📝 出力ファイルサイズ: {len(output)} 文字")
                    print("📄 出力ファイルの最初の1000文字:")
                    print("-" * 50)
                    print(output[:1000])
                    print("-" * 50)

                    # 期待される内容があるか簡単にチェック
                    if "PR #38" in output:
                        print("✅ PR番号が見つかりました")
                    if "claude周り更新" in output:
                        print("✅ PRタイトルが見つかりました")
                    if "actionable" in output.lower():
                        print("✅ actionableアイテムが見つかりました")

                    return True
                else:
                    print("❌ 出力ファイルが作成されませんでした")
                    return False
            else:
                print("❌ コマンド実行失敗")
                return False

        except subprocess.TimeoutExpired:
            print("⏰ コマンド実行がタイムアウトしました")
            return False
        except Exception as e:
            print(f"💥 実行エラー: {str(e)}")
            return False
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def main():
    """メイン関数"""
    success = test_direct_execution()

    if success:
        print("\n✅ 直接実行テスト成功")
        print("ℹ️  実際のGitHub APIを使用して正常に動作しました")
        exit(0)
    else:
        print("\n❌ 直接実行テスト失敗")
        print("ℹ️  モック実装が必要です")
        exit(1)


if __name__ == "__main__":
    main()
