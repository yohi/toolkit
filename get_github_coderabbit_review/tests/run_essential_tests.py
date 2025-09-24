#!/usr/bin/env python3
"""
PR2とPR38の出力結果テスト（モック使用）
GitHub認証不要で、モックを用いて期待通りの出力が生成されるかをテストします。
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str, working_dir: Path = None) -> bool:
    """コマンドを実行して結果を表示"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=working_dir or Path(__file__).parent
        )

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            # 成功の要約のみ表示
            lines = result.stdout.split("\n")
            for line in lines:
                if "✅" in line or "passed" in line.lower() or "success" in line.lower():
                    print(f"   {line}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Return code: {result.returncode}")
            if result.stderr:
                error_lines = result.stderr.split("\n")[:5]  # 最初の5行のみ
                for line in error_lines:
                    if line.strip():
                        print(f"   {line}")
            return False

    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    """メイン実行関数"""
    print("🚀 CodeRabbit Comment Fetcher - Essential Tests (モック化版)")
    print("   PR2とPR38の出力結果テストのみを実行します")

    tests = [
        # PR38モック化テスト（最も重要）
        (["python", "pr38/test_pr38_final.py"], "PR38モック化テスト（期待値との比較）"),
        # PR2モック化テスト
        (["python", "pr2/test_pr2_quiet_mode.py"], "PR2モック化テスト（出力生成確認）"),
    ]

    results = []
    for cmd, description in tests:
        success = run_command(cmd, description)
        results.append((description, success))

    # 結果サマリー
    print(f"\n{'='*60}")
    print("📊 Essential Tests 結果サマリー")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {description}")

    print(f"\n🎯 結果: {passed}/{total} essential tests passed")

    if passed == total:
        print("🎉 すべてのエッセンシャルテストが成功しました！")
        print("📝 PR2とPR38のモック化テストは正常に動作しています")
        return 0
    else:
        print(f"⚠️  {total - passed} essential tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
