#!/bin/bash
# ClaudeCode 開発環境 自動セットアップスクリプト

# 色付け用
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}ClaudeCode 開発環境のセットアップを開始します...${NC}"

# --- 1. ディレクトリの作成 ---
PROJECT_DIR="my-claude-dev"
if [ -d "$PROJECT_DIR" ]; then
  echo -e "${YELLOW}警告: ディレクトリ '$PROJECT_DIR' は既に存在します。${NC}"
else
  mkdir "$PROJECT_DIR"
  echo "作業ディレクトリを作成しました: $PROJECT_DIR"
fi
cd "$PROJECT_DIR"

# --- 2. ファイルの生成 ---
echo "Dockerfile を作成中..."
cat << 'EOF' > Dockerfile
# ベースイメージ
FROM ubuntu:25.10

# pipxでインストールしたコマンドがどこからでも使えるようにPATHを事前に設定
ENV PATH="/root/.local/bin:${PATH}"

# パッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nodejs \
    npm \
    pipx \
    && rm -rf /var/lib/apt/lists/*

# SuperClaudeとClaudeCodeのインストール
RUN npm install -g @anthropic-ai/claude-code \
    && pipx install SuperClaude \
    && pipx upgrade SuperClaude \
    && SuperClaude install -y \
    && pipx ensurepath

# 認証/設定ファイルのマウント先として、コンテナ内にディレクトリを作成
RUN mkdir -p /root/.claude

# 作業ディレクトリの設定
WORKDIR /workspace

# コンテナ起動時のデフォルトコマンド
CMD ["bash"]
EOF

echo "起動スクリプト (start-dev.sh) を作成中..."
cat << 'EOF' > start-dev.sh
#!/bin/bash
# 開発環境コンテナ起動スクリプト

IMAGE_NAME="ghcr.io/yohi/sandbox:latest"
CLAUDE_CONFIG_DIR="$HOME/.claude"

if ! command -v docker &> /dev/null; then
    echo "エラー: Dockerがインストールされていません。"
    exit 1
fi
if [ ! -f "$CLAUDE_CONFIG_DIR/credentials.json" ] || [ ! -f "$CLAUDE_CONFIG_DIR/config.json" ]; then
  echo "エラー: ClaudeCodeの認証ファイルまたは設定ファイルが見つかりません。"
  echo "パスを確認してください: $CLAUDE_CONFIG_DIR"
  echo "事前にブラウザで一度ログインを済ませてください。"
  exit 1
fi

if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Dockerイメージが見つかりません。ビルドを開始します..."
  docker build -t "$IMAGE_NAME" .
  if [ $? -ne 0 ]; then
    echo "エラー: Dockerイメージのビルドに失敗しました。"
    exit 1
  fi
fi

echo "認証情報をマウントしてコンテナを起動します..."
echo "コンテナを終了するには 'exit' と入力してください。"

docker run -it --rm \
  -v "$CLAUDE_CONFIG_DIR/credentials.json:/root/.claude/credentials.json:ro" \
  -v "$CLAUDE_CONFIG_DIR/config.json:/root/.claude/config.json:ro" \
  -v "$(pwd):/workspace" \
  "$IMAGE_NAME"

echo "コンテナを終了しました。"
EOF

chmod +x start-dev.sh

# --- 3. 完了メッセージ ---
echo -e "${GREEN}--------------------------------------------------${NC}"
echo -e "${GREEN}セットアップが完了しました！${NC}"
echo ""
echo "次のステップ:"
echo "1. 新しく作成されたディレクトリに移動してください:"
echo -e "   ${YELLOW}cd $PROJECT_DIR${NC}"
echo "2. 起動スクリプトを実行して、開発環境を開始します:"
echo -e "   ${YELLOW}./start-dev.sh${NC}"
echo -e "${GREEN}--------------------------------------------------${NC}"
