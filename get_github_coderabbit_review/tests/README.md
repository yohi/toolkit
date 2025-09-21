# テストファイル

このディレクトリには、coderabbit-fetchツールのテストが含まれています。

## ディレクトリ構成

```
tests/
├── pr38/                    # PR38専用テスト
│   ├── mock_data/          # モックデータファイル
│   ├── test_pr38_*.py      # テストファイル
│   └── README.md           # PR38テストガイド
├── unit/                   # 単体テスト
├── integration/            # 統合テスト
├── performance/            # パフォーマンステスト
└── fixtures/               # テスト用フィクスチャ
```

## PR38検証テスト

PR38に対するツールの出力が期待値と一致することを検証するテストセットです。

### テストファイル構成

| ファイル | 説明 | 推奨度 |
|---------|-----|--------|
| `pr38/test_pr38_final.py` | 実際のGitHub APIを使用した最終検証テスト | ⭐ **推奨** |
| `pr38/test_pr38_direct.py` | 直接実行による動作確認テスト | 🔧 開発用 |
| `pr38/test_pr38_validation.py` | pytestベースの包括的テストスイート | 🧪 詳細検証 |
| `pr38/test_pr38_simple.py` | pytest依存なしのシンプルテスト | 🚀 軽量 |
| `pr38/test_pr38_mock_helpers.py` | モック管理とテスト支援機能 | 📦 ヘルパー |

### モックデータファイル

| ファイル | 内容 |
|---------|-----|
| `pr38/mock_data/pr38_mock_data.json` | PR基本情報（タイトル、説明、コメント、レビュー） |
| `pr38/mock_data/pr38_inline_comments.json` | インラインコメント（3個のアクション可能コメント） |
| `pr38/mock_data/pr38_reviews.json` | レビューデータ（CodeRabbitレビュー本体） |
| `pr38/mock_data/pr38_files.json` | 変更ファイル一覧（6ファイルの詳細情報） |

## テストの実行方法

### 1. 推奨テスト（最終検証）

```bash
cd tests
python pr38/test_pr38_final.py
```

このテストは：
- 実際のGitHub APIを使用
- 期待値ファイルとの厳密な比較
- 12項目の構造検証
- 差分分析と成功率評価

### 2. 直接実行テスト

```bash
cd tests
python pr38/test_pr38_direct.py
```

このテストは：
- モックなしの実際の動作確認
- コマンドライン引数の検証
- 実際の出力内容の確認

### 3. pytestベーステスト（pytest環境が必要）

```bash
cd tests
python pr38/test_pr38_validation.py
# または
pytest pr38/test_pr38_validation.py -v
```

### 4. 軽量テスト

```bash
cd tests
python pr38/test_pr38_simple.py
```

## 期待値ファイル

期待値ファイル `expected_pr_38_ai_agent_prompt.md` はプロジェクトルートに配置されています。

## 検証項目

### 構造検証（12項目）
1. PR基本情報（URL、タイトル、番号）
2. ファイル変更数（6ファイル）
3. コメント数（10コメント: 3 actionable + 7 nitpick）
4. CodeRabbit分析の存在
5. AIエージェントプロンプトの存在
6. レビューコメント構造
7. 期待ファイル一覧（全6ファイル）
8. 重要な問題（HOME、bun、date関連）

### 内容検証
- 期待値ファイルとの完全一致（動的順序考慮）
- アクション可能なアイテムの抽出
- ファイル変更情報の抽出
- エラーハンドリング

## 実行環境要件

- Python 3.13+
- GitHub CLI (`gh`) がインストール済み
- インターネット接続（実際のGitHub APIアクセス用）
- uvx実行環境

## トラブルシューティング

### コマンドライン引数エラー
```
error: ambiguous option: --output could match --output-format, --output-file
```
**解決**: `--output-file` を使用してください（`--output` は曖昧）

### インポートエラー
```
ModuleNotFoundError: No module named 'test_pr38_mock_helpers'
```
**解決**: testsディレクトリ内で実行してください

### GitHub CLI認証エラー
```
GitHub CLI error
```
**解決**: `gh auth login` でGitHub CLIの認証を設定してください

## 結果の解釈

### 成功例
```
🎉 全ての検証テストが成功しました！
✅ PR38の出力は期待値と一致し、構造も正しいです
✅ ツールは実際のGitHub APIで正常に動作しています
```

### 部分的成功例
```
📊 構造検証結果: 10/12 項目が合格
✅ 比較テスト成功（差分: 3行）
```

### 失敗例
```
❌ 構造検証失敗: pr_url, actionable_comments
❌ 比較テスト失敗（差分: 50行）
```

## 注意事項

- テストは実際のGitHub APIを使用するため、ネットワーク接続が必要です
- PR38のデータは安定していますが、将来的にGitHubの仕様変更により影響を受ける可能性があります
- モックデータは2025年9月21日時点の実際のレスポンスに基づいています
