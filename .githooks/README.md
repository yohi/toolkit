# Git Hooks

このディレクトリには、プロジェクト用のGitフックが含まれています。

## セットアップ

フックを有効にするには、gitルートディレクトリで以下のコマンドを実行してください：

```bash
git config core.hooksPath .githooks
```

## フック一覧

### pre-push

`get_github_coderabbit_review` ディレクトリに変更があった場合に、PR38検証テストを自動実行します。

#### 機能
- 変更ファイルの検出
- PR38検証テストの自動実行
- テスト失敗時のpush阻止

#### 実行モード

**通常モード（デフォルト）**
```bash
git push origin branch-name
```
- 完全なPR38検証テストを実行
- より詳細な検証を行う

**クイックモード**
```bash
QUICK_TEST=true git push origin branch-name
```
- 高速な構造チェックのみ実行
- 短時間で基本的な検証を行う

#### 出力例

**変更検出時**
```
🔍 Pre-push hook: Checking for changes in get_github_coderabbit_review...
🔄 Checking refs: refs/heads/feature -> refs/heads/feature
📋 Checking range: abc123..def456
✅ Changes detected in get_github_coderabbit_review/
  get_github_coderabbit_review/coderabbit_fetcher/orchestrator.py
  get_github_coderabbit_review/tests/pr38/test_pr38_final.py

🧪 Changes detected - running validation tests...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 Running PR38 validation tests...
📦 Executing PR38 final validation test...
🎉 全ての検証テストが成功しました！
✅ PR38の出力は期待値と一致し、構造も正しいです
✅ ツールは実際のGitHub APIで正常に動作しています
✅ PR38 validation tests passed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 All validation tests passed! Push proceeding...
✅ Pre-push hook completed successfully
```

**変更なしの場合**
```
🔍 Pre-push hook: Checking for changes in get_github_coderabbit_review...
🔄 Checking refs: refs/heads/feature -> refs/heads/feature
📋 Checking range: abc123..def456
ℹ️  No changes detected in get_github_coderabbit_review/
ℹ️  No changes in get_github_coderabbit_review - skipping tests
✅ Pre-push hook completed successfully
```

**テスト失敗時**
```
❌ PR38 validation tests failed!
❌ Validation tests failed. Push aborted.
💡 Hint: Run 'cd get_github_coderabbit_review && python tests/pr38/test_pr38_final.py' to debug
💡 Or set QUICK_TEST=true for faster validation
```

#### トラブルシューティング

**テストをスキップしたい場合**
```bash
git push --no-verify origin branch-name
```

**フックを無効にしたい場合**
```bash
git config --unset core.hooksPath
```

**フックを再有効化**
```bash
git config core.hooksPath .githooks
```

#### 対象ファイル

以下のパターンのファイルに変更があった場合にテストが実行されます：
- `get_github_coderabbit_review/` 配下のすべてのファイル

#### 前提条件

- Python 3.13+ がインストールされている
- GitHub CLI (`gh`) がインストール・認証済み
- インターネット接続（実際のGitHub APIアクセス用）
- uvx実行環境が利用可能

#### 設定ファイル

フックの動作は以下の環境変数で制御できます：

- `QUICK_TEST=true`: クイックモードで実行
- `FULL_TEST=true`: 詳細モードで実行（デフォルト）

## メンテナンス

### フックの更新

フックスクリプトを更新した場合：

1. ファイルの実行権限を確認
   ```bash
   chmod +x .githooks/pre-push
   ```

2. フック設定の確認
   ```bash
   git config core.hooksPath
   ```

3. テスト実行
   ```bash
   .githooks/pre-push origin https://github.com/example/repo.git <<< "refs/heads/test abc123 refs/heads/test def456"
   ```

### ログ確認

フックの実行ログは標準出力に表示されます。詳細なデバッグが必要な場合は、スクリプト内の `set -x` を有効にしてください。
