# Toolkit Repository

このリポジトリには各種開発ツールとプロジェクトが含まれています。

## プロジェクト一覧

### get_github_coderabbit_review

GitHubのプルリクエストからCodeRabbitのコメントを取得・分析し、AIエージェント向けのプロンプトを生成するツール。

**特徴:**
- GitHub CLI統合によるセキュアなAPI アクセス
- CodeRabbitコメントの自動分析・分類
- AI最適化されたプロンプト出力
- 包括的なテストスイート

**詳細:** [get_github_coderabbit_review/README.md](get_github_coderabbit_review/README.md)

## Git フックの設定

このリポジトリではpre-pushフックが設定されており、`get_github_coderabbit_review`に変更があった場合に自動的にテストが実行されます。

### セットアップ

```bash
# フックを有効にする
./setup-hooks.sh
```

### 使用方法

```bash
# 通常のpush（完全テスト実行）
git push origin branch-name

# クイックテスト付きpush
QUICK_TEST=true git push origin branch-name

# フックをスキップ
git push --no-verify origin branch-name
```

### フック動作

- `get_github_coderabbit_review/` 配下のファイルに変更がある場合のみテスト実行
- 変更がない場合はテストをスキップして高速化
- テスト失敗時はpushを自動的に阻止

**詳細:** [.githooks/README.md](.githooks/README.md)
