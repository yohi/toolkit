# 要件定義書

## 概要

GitHubのプルリクエストURLからCodeRabbitのコメント内容を取得し、フォーマッティングするPythonスクリプトを開発する。このツールは、CodeRabbitによる自動レビューコメントを効率的に収集・整理し、開発者がレビュー内容を把握しやすくすることを目的とする。

## CodeRabbitコメントのサンプル構造

以下は実際のCodeRabbitコメントの構造例：

### サマリーコメント例
```
## Summary by CodeRabbit

• 新機能
  • AWS Secrets Manager をバックエンドとするキー保管を追加。

• ドキュメント
  • フック無効化に関するREADMEを追加。

• テスト
  • 単体/統合テストを追加し、CRUD、メタデータ、一覧、サイズ上限、未初期化時の動作を検証。

## Walkthrough

Rundeck向けAWS Secrets Managerバックエンドを新規追加。初期化・保存・取得・更新・削除・一覧・メタデータ取得・終了処理を実装。

## Changes

| Cohort / File(s) | Summary |
|------------------|---------|
| Docs aws-keystorage-plugin/README.md | 新規READMEを追加（1行: 「# pre-push hook disabled」）。 |
| Secrets Manager バックエンド実装 | 新規クラス SecretsManagerBackend を追加。 |
```

### レビューコメント例
```
Actionable comments posted: 8

🧹 Nitpick comments (2)
aws-keystorage-plugin/src/main/java/.../SecretsManagerBackend.java (2)

541-545 : 削除時のリカバリーウィンドウがハードコードされています

リカバリーウィンドウが7日にハードコードされています。設定可能にすべきです。

🤖 Prompt for AI Agents

+private static final int DEFAULT_RECOVERY_WINDOW_DAYS = 7;
+private int recoveryWindowDays;
+
+// In initialize method:
+this.recoveryWindowDays = configManager.getInteger("sm-recovery-window-days", DEFAULT_RECOVERY_WINDOW_DAYS);

⚠️ Outside diff range comments

aws-keystorage-plugin/src/main/java/.../SecretsManagerBackend.java (1)

823-824 : isDirectChild メソッドの実装が正確です

親パスの直接の子要素を正しく判定しています。エッジケースも適切に処理されています。
```

## 要件

### 要件1

**ユーザーストーリー:** 開発者として、GitHubプルリクエストのURLを指定してCodeRabbitのコメントを取得したい。そうすることで、レビュー内容を一覧で確認できる。

#### 受入基準

1. WHEN ユーザーがGitHubプルリクエストのURLを入力する THEN システムはそのURLからプルリクエスト情報を取得する SHALL
2. WHEN プルリクエストが存在する THEN システムはGitHub CLIを使用してコメント情報を取得する SHALL
3. WHEN 無効なURLが入力される THEN システムは適切なエラーメッセージを表示する SHALL

### 要件2

**ユーザーストーリー:** 開発者として、取得したコメントの中からCodeRabbitのコメントのみを抽出したい。そうすることで、AIレビューの内容に集中できる。

#### 受入基準

1. WHEN コメントリストを取得する THEN システムは"coderabbitai"ユーザーによるコメントを識別する SHALL
2. WHEN CodeRabbitコメントを識別する THEN システムは作成者名で正確にフィルタリングする SHALL
3. WHEN CodeRabbitコメント以外のコメントが存在する THEN システムはそれらを除外する SHALL
4. WHEN インラインコメントを処理する THEN システムは未解決のコメントのみを抽出する SHALL
5. WHEN 解決済みのインラインコメントが存在する THEN システムはそれらを除外する SHALL
6. WHEN スレッド化されたインラインコメントを処理する THEN システムはスレッド内のCodeRabbitコメントを付随情報として含める SHALL
7. WHEN スレッドの付随情報を表示する THEN システムは生成AIが理解しやすい構造でフォーマットする SHALL
8. WHEN スレッド情報をフォーマットする THEN システムはベストプラクティスに基づいた明確な階層構造と文脈情報を提供する SHALL
8. WHEN CodeRabbitの最後の返信に解決済みマーカーが含まれる THEN システムはそのコメントを解決済みとして扱う SHALL
9. WHEN 解決済みマーカーを検出する THEN システムはそのコメントを取得対象から除外する SHALL

### 要件3

**ユーザーストーリー:** 開発者として、CodeRabbitのサマリーコメントと個別のレビューコメントを区別して取得したい。そうすることで、概要と詳細を分けて確認できる。

#### 受入基準

1. WHEN CodeRabbitコメントを分析する THEN システムは"Summary by CodeRabbit"を含むサマリーコメントを識別する SHALL
2. WHEN サマリーコメントを処理する THEN システムは新機能、ドキュメント、テストの各セクションを抽出する SHALL
3. WHEN 個別レビューコメントを処理する THEN システムは"Actionable comments posted"の内容を抽出する SHALL

### 要件4

**ユーザーストーリー:** 開発者として、CodeRabbitコメントの構造化された情報を読みやすい形式で出力したい。そうすることで、レビュー内容を効率的に確認できる。

#### 受入基準

1. WHEN サマリーコメントをフォーマットする THEN システムは新機能、ドキュメント、テストの変更点を整理して表示する SHALL
2. WHEN Walkthroughセクションを処理する THEN システムは変更の概要を構造化して表示する SHALL
3. WHEN Actionable commentsを処理する THEN システムはファイル名、行番号、コメント内容を明確に区別して表示する SHALL
4. WHEN 個別の指摘事項を処理する THEN システムは各コメントを独立したセクションとしてフォーマットする SHALL
5. WHEN "🤖 Prompt for AI Agents"が含まれるコメントを処理する THEN システムはそのコードブロックをそのまま採用して表示する SHALL
6. WHEN Sequence Diagramが含まれる THEN システムはMermaid図を適切にフォーマットする SHALL

### 要件5

**ユーザーストーリー:** 開発者として、Nitpickコメント、Actionableコメント、Outside diff range commentsを区別して表示したい。そうすることで、優先度と種類に応じてレビュー対応ができる。

#### 受入基準

1. WHEN Nitpickコメントを識別する THEN システムは"🧹 Nitpick comments"セクションを抽出する SHALL
2. WHEN 重要なコメントを識別する THEN システムは"Actionable comments posted"の数値と内容を表示する SHALL
3. WHEN Outside diff range commentsを識別する THEN システムは"⚠️ Outside diff range comments"セクションを抽出する SHALL
4. WHEN Outside diff range commentsを処理する THEN システムは各指摘事項をファイル名、行番号、コメント内容に分けてフォーマットする SHALL
5. WHEN コメントの種類を表示する THEN システムは視覚的に区別できる形式で出力する SHALL

### 要件6

**ユーザーストーリー:** 開発者として、Python 3.13とuvを使用した環境で動作するスクリプトを使いたい。そうすることで、最新のPython環境で効率的に実行できる。

#### 受入基準

1. WHEN スクリプトを実行する THEN システムはPython 3.13で動作する SHALL
2. WHEN 依存関係を管理する THEN システムはuvを使用して仮想環境を構築する SHALL
3. WHEN uvxで実行する THEN システムは追加のセットアップなしで動作する SHALL

### 要件7

**ユーザーストーリー:** 開発者として、GitHub CLIを使用してプルリクエスト情報を取得したい。そうすることで、認証済みのGitHub APIアクセスを活用できる。

#### 受入基準

1. WHEN GitHub APIにアクセスする THEN システムはGitHub CLIを使用する SHALL
2. WHEN GitHub CLIが未認証の場合 THEN システムは認証が必要である旨を通知する SHALL
3. WHEN API制限に達した場合 THEN システムは適切なエラーハンドリングを行う SHALL

### 要件8

**ユーザーストーリー:** 開発者として、コマンドライン引数でプルリクエストURLを指定したい。そうすることで、スクリプトを柔軟に使用できる。

#### 受入基準

1. WHEN コマンドライン引数を解析する THEN システムはプルリクエストURLを受け取る SHALL
2. WHEN 引数が不足している THEN システムは使用方法を表示する SHALL
3. WHEN ヘルプオプションが指定される THEN システムは詳細な使用方法を表示する SHALL
4. WHEN ペルソナファイルが引数で指定される THEN システムはそのテキストファイルを読み込む SHALL
5. WHEN ペルソナファイルが存在しない THEN システムは適切なエラーメッセージを表示する SHALL

### 要件8.1

**ユーザーストーリー:** 開発者として、ペルソナや参考情報を含むテキストファイルを出力の先頭に追加したい。そうすることで、生成AIに対して適切なコンテキストを提供できる。

#### 受入基準

1. WHEN ペルソナファイルを読み込む THEN システムはファイル内容をそのまま保持する SHALL
2. WHEN 出力を生成する THEN システムはペルソナ情報を最初に配置する SHALL
3. WHEN ペルソナ情報とCodeRabbitコメントを結合する THEN システムは明確な区切りを設ける SHALL
4. WHEN ペルソナファイルが指定されない THEN システムはデフォルトペルソナを自動的に付与する SHALL
5. WHEN デフォルトペルソナを生成する THEN システムはレビュー指摘対応に最適化されたペルソナ情報を使用する SHALL
6. WHEN デフォルトペルソナを適用する THEN システムは「あなたは経験豊富なソフトウェア開発者です。CodeRabbitからのレビュー指摘を分析し、適切なコード修正を提案してください。」のような内容を含める SHALL
7. WHEN デフォルトペルソナを設計する THEN システムはAnthropic Claude 4のベストプラクティス（https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices.md）を参考にする SHALL
8. WHEN プロンプト構造を最適化する THEN システムは明確な役割定義、具体的なタスク指示、期待する出力形式を含める SHALL

### 要件8.2

**ユーザーストーリー:** 開発者として、解決済みマーカーを使用してCodeRabbitコメントのステータスを管理したい。そうすることで、対応済みのコメントを自動的に除外できる。

#### 受入基準

1. WHEN 解決済みマーカーを定義する THEN システムは設定可能なマーカー文字列を使用する SHALL
2. WHEN CodeRabbitの最後の返信を分析する THEN システムは解決済みマーカーの存在を確認する SHALL
3. WHEN 解決済みマーカーが検出される THEN システムはそのコメントスレッドを解決済みとしてマークする SHALL
4. WHEN 解決済みコメントを処理する THEN システムはそれらを取得対象から除外する SHALL
5. WHEN 解決済みマーカーのデフォルト値を設定する THEN システムは"🔒 CODERABBIT_RESOLVED 🔒"のような識別しやすい形式を使用する SHALL
6. WHEN 解決済みマーカーを設計する THEN システムは誤検出を防ぐため特殊な文字列パターンを使用する SHALL

### 要件8.3

**ユーザーストーリー:** 開発者として、CodeRabbitに対してHEADの確認と解決済みマーカーの追加を依頼したい。そうすることで、対応済みコメントの自動管理を促進できる。

#### 受入基準

1. WHEN 解決確認オプションが指定される THEN システムはCodeRabbitに確認依頼コメントを投稿する SHALL
2. WHEN 確認依頼コメントを生成する THEN システムは"@coderabbitai HEADを確認して問題がなければ解決済みマーカー🔒 CODERABBIT_RESOLVED 🔒を付けてください"形式のメッセージを作成する SHALL
3. WHEN GitHub CLIを使用してコメント投稿する THEN システムは適切なプルリクエストにコメントを追加する SHALL
4. WHEN コメント投稿が失敗する THEN システムは適切なエラーメッセージを表示する SHALL
5. WHEN 解決確認オプションが無効の場合 THEN システムはコメント投稿を行わない SHALL

### 要件9

**ユーザーストーリー:** 開発者として、CodeRabbitが提供するAI Agent用のプロンプトコードを特別に扱いたい。そうすることで、提案されたコード修正を直接活用できる。

#### 受入基準

1. WHEN "🤖 Prompt for AI Agents"セクションを検出する THEN システムはそのセクションを特別にマークする SHALL
2. WHEN AI Agent用のコードブロックを抽出する THEN システムはコードブロック内容をそのまま保持する SHALL
3. WHEN AI Agent用プロンプトを表示する THEN システムは他のコメントと視覚的に区別して表示する SHALL
4. WHEN "🤖 Prompt for AI Agents"がないインラインコメントを処理する THEN システムは指摘内容をAIエージェントが理解しやすい形式でフォーマットする SHALL
5. WHEN 通常のインラインコメントをフォーマットする THEN システムは問題の説明と推奨される修正方法をAIエージェントが処理しやすい構造で表示する SHALL
6. WHEN AIエージェント向けフォーマットを設計する THEN システムはClaude 4ベストプラクティスに基づいた構造化された形式を使用する SHALL

### 要件10

**ユーザーストーリー:** 開発者として、スレッド化されたコメントの文脈を理解したい。そうすることで、コメントの背景と関連する議論を把握できる。

#### 受入基準

1. WHEN スレッド化されたコメントを検出する THEN システムはスレッド全体の構造を分析する SHALL
2. WHEN スレッド内のCodeRabbitコメントを抽出する THEN システムは時系列順に整理する SHALL
3. WHEN スレッドの付随情報を生成する THEN システムは主要コメント、返信、解決状況を明確に区別する SHALL
4. WHEN 生成AI向けにフォーマットする THEN システムはスレッドの文脈と関係性を構造化データとして表現する SHALL
5. WHEN 構造化データを設計する THEN システムはClaude 4ベストプラクティスに従った明確で一貫性のある形式を使用する SHALL

### 要件11

**ユーザーストーリー:** 開発者として、出力形式を選択できるようにしたい。そうすることで、用途に応じて最適な形式でレビュー内容を確認できる。

#### 受入基準

1. WHEN 出力形式オプションが指定される THEN システムはMarkdown、JSON、プレーンテキストから選択できる SHALL
2. WHEN Markdown形式で出力する THEN システムは見出し、リスト、コードブロックを適切にフォーマットする SHALL
3. WHEN JSON形式で出力する THEN システムは構造化されたデータとして出力する SHALL