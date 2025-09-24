# 🤖 AI エージェント用クイックスタートガイド

CodeRabbit Comment Fetcherを他のAIエージェント（Claude、ChatGPT、Geminiなど）にコピー＆ペーストして利用する際の簡単ガイドです。

## 📋 1分で始める - 基本の使い方

### AIエージェントに送る基本プロンプト

```
以下のコマンドを実行して、GitHubプルリクエストのCodeRabbitコメントを分析してください：

coderabbit-fetch https://github.com/[owner]/[repo]/pull/[number]

例：
coderabbit-fetch https://github.com/microsoft/vscode/pull/12345
```

### 出力形式を指定する場合

```
以下のコマンドでJSON形式で出力してください：

coderabbit-fetch https://github.com/[owner]/[repo]/pull/[number] --output-format json
```

## 🎯 すぐ使えるコマンド例

### 1. 基本分析（マークダウン出力）
```bash
coderabbit-fetch https://github.com/facebook/react/pull/12345
```

### 2. JSON出力（プログラム処理用）
```bash
coderabbit-fetch https://github.com/microsoft/vscode/pull/67890 \
    --output-format json \
    --output-file analysis.json
```

### 3. セキュリティ専門レビュー
```bash
coderabbit-fetch https://github.com/django/django/pull/54321 \
    --persona-file examples/personas/security_expert.txt \
    --output-file security_review.md
```

### 4. 日本語レビュー
```bash
coderabbit-fetch https://github.com/owner/japanese-project/pull/123 \
    --persona-file examples/personas/japanese_reviewer.txt
```

### 5. 大規模PRの分析（タイムアウト延長）
```bash
coderabbit-fetch https://github.com/kubernetes/kubernetes/pull/98765 \
    --timeout 120 \
    --show-stats \
    --output-format json
```

### 6. 簡潔な出力（quietモード）
```bash
coderabbit-fetch https://github.com/owner/repo/pull/123 --quiet
```

## 📁 コピー＆ペースト用ファイル

### AIエージェントに渡すペルソナファイル内容

**デフォルトレビューアー**（`examples/personas/default_reviewer.txt`）:
```
You are an experienced software developer and technical reviewer with deep expertise in code quality, security, and maintainability.

## Expertise Areas
- Full-stack web development with modern frameworks
- Code quality and best practices
- Security considerations and vulnerability assessment
- Performance optimization and scalability
- Database design and optimization
- API design and documentation
- Testing strategies and automation

## Review Philosophy
Your code reviews focus on:
1. **Functionality**: Does the code solve the intended problem correctly?
2. **Security**: Are there potential security vulnerabilities or risks?
3. **Performance**: Could this code impact application performance?
4. **Maintainability**: Will this code be easy to understand and modify?
5. **Best Practices**: Does the code follow established conventions?

## Communication Style
- Provide constructive, specific feedback with clear examples
- Suggest concrete improvements with code snippets when helpful
- Explain the reasoning behind your recommendations
- Prioritize critical issues (security, functionality) over style preferences
- Offer alternative approaches when applicable
- Be encouraging while maintaining high standards
```

**セキュリティ専門家**（`examples/personas/security_expert.txt`）をAIに渡す場合:
```
You are a cybersecurity expert and senior security engineer with extensive experience in application security, vulnerability assessment, and secure coding practices.

## Core Security Focus Areas
- Authentication and authorization vulnerabilities
- Input validation and injection attacks (SQL, XSS, CSRF)
- Data encryption and secure storage
- API security and rate limiting
- Dependency vulnerabilities and supply chain security
- Secure configuration and deployment practices

## Security Review Priorities
1. **Critical Security Flaws** - Immediate security risks
2. **Data Protection** - Sensitive data handling and privacy
3. **Access Control** - Authentication and authorization mechanisms
4. **Input Validation** - All user inputs and external data
5. **Cryptographic Implementation** - Encryption, hashing, tokens
6. **Third-party Dependencies** - Security of external libraries
```

## 🚀 プロンプト例文集

### 基本分析依頼
```
このGitHubプルリクエストのCodeRabbitコメントを分析して、重要な指摘事項をまとめてください。

PR URL: https://github.com/[owner]/[repo]/pull/[number]

使用コマンド：
coderabbit-fetch [上記URL] --output-format markdown
```

### セキュリティ重点分析
```
セキュリティの観点から、このプルリクエストのCodeRabbitコメントを詳細に分析してください。
特に以下の点に注目して報告してください：
- 脆弱性に関する指摘
- データ保護の問題
- 認証・認可の問題

使用コマンド：
coderabbit-fetch [PR_URL] --persona-file examples/personas/security_expert.txt
```

### 日本語での分析依頼
```
このプルリクエストのCodeRabbitコメントを日本語で分析して、開発チームに分かりやすく報告してください。

使用コマンド：
coderabbit-fetch [PR_URL] --persona-file examples/personas/japanese_reviewer.txt
```

### 大規模PR分析（統計情報付き）
```
この大規模なプルリクエストのCodeRabbitコメントを分析し、統計情報も含めて報告してください。
処理時間が長くなる可能性があるため、タイムアウトを延長して実行してください。

使用コマンド：
coderabbit-fetch [PR_URL] --timeout 180 --show-stats --output-format json
```

## 💡 AIエージェント活用のヒント

### 1. **段階的分析のすすめ**
1. まず基本コマンドで全体を把握
2. 必要に応じて特定の観点（セキュリティ、パフォーマンスなど）で再分析
3. 結果をもとに改善提案を作成

### 2. **出力形式の選択**
- **Markdown**: 人間が読みやすい、レポート作成に適している
- **JSON**: プログラム処理、データ分析に適している
- **Plain**: シンプルなテキスト、軽量処理に適している

### 3. **エラーハンドリング**
コマンド実行時にエラーが出た場合の対処法：
```bash
# GitHub認証の確認
gh auth status

# GitHub CLIでの再認証
gh auth login

# タイムアウト延長
coderabbit-fetch [PR_URL] --timeout 120

# デバッグ情報付きで実行
coderabbit-fetch [PR_URL] --debug
```

## 📋 チェックリスト - AIエージェント用

AIエージェントがこのツールを使用する際の確認事項：

- [ ] PRのURLが正しいか確認
- [ ] GitHub CLIが認証済みか確認（`gh auth status`）
- [ ] 適切な出力形式を選択（markdown/json/plain）
- [ ] 大規模PRの場合はタイムアウトを延長
- [ ] 特定の観点が必要な場合は適切なペルソナファイルを選択
- [ ] 必要に応じて`--show-stats`でパフォーマンス情報を取得

## 🆘 トラブルシューティング

### よくある問題と解決方法

1. **「GitHub CLI not found」エラー**
   ```bash
   # GitHub CLIのインストール（Mac）
   brew install gh

   # GitHub CLIのインストール（Linux）
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   sudo apt update && sudo apt install gh
   ```

2. **「Authentication required」エラー**
   ```bash
   gh auth login
   ```

3. **「PR not found」エラー**
   - PRのURLが正しいか確認
   - プライベートリポジトリへのアクセス権限を確認

4. **タイムアウトエラー**
   ```bash
   coderabbit-fetch [PR_URL] --timeout 180
   ```

このガイドを使って、AIエージェントでCodeRabbit Comment Fetcherを効果的に活用してください！
