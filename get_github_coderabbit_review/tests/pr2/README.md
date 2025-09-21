# PR2テスト

このディレクトリには、PR2（https://github.com/yohi/lazygit-llm-commit-generator/pull/2）に対するテストが含まれています。

## 概要

このテストは、現在の`uvx --from . -n crf https://github.com/yohi/lazygit-llm-commit-generator/pull/2 --quiet`の実行結果を正として、GitHub CLIレスポンスをモック化してテストします。

## ファイル構成

```
tests/pr2/
├── README.md                           # このファイル
├── test_pr2_quiet_mode.py             # メインテストファイル
├── expected_pr_2_ai_agent_prompt.md   # 期待値ファイル
└── mock_data/                         # モックデータディレクトリ
    ├── pr2_basic_info.json            # PR基本情報
    ├── pr2_files.json                 # 変更ファイル一覧
    ├── pr2_reviews.json               # レビューデータ
    └── pr2_comments.json              # コメントデータ
```

## テスト実行方法

### 単体実行
```bash
cd tests/pr2
python test_pr2_quiet_mode.py
```

### 統合テストランナーから実行
```bash
cd tests
python test_runner.py --type integration
```

## テスト内容

1. **test_pr2_quiet_mode_with_mocks**: GitHub CLIをモック化してquiet mode実行をテスト
2. **test_pr2_structure_validation**: 出力構造の検証（必須セクションの存在確認）
3. **test_mock_data_consistency**: モックデータの整合性確認

## モックデータについて

- `pr2_basic_info.json`: `gh pr view --json url,title,number,body,author,baseRefName,headRefName,additions,deletions,changedFiles`の結果
- `pr2_files.json`: `gh pr view --json files`の結果
- `pr2_reviews.json`: `gh api repos/yohi/lazygit-llm-commit-generator/pulls/2/reviews`の結果
- `pr2_comments.json`: `gh api repos/yohi/lazygit-llm-commit-generator/pulls/2/comments`の結果（サンプルのみ）

## 期待値について

`expected_pr_2_ai_agent_prompt.md`は、実際の実行結果をベースに作成された短縮版の期待値ファイルです。完全な出力との比較ではなく、重要な構造要素の存在確認に使用されます。

## 注意点

- このテストはGitHub CLIの実際の通信を行わず、すべてモック化されています
- PR2のデータは2025年9月時点のスナップショットです
- 将来的にツールの出力形式が変更された場合、期待値の更新が必要な場合があります

