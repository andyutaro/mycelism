#!/bin/bash

# scribe起動用スクリプト（Automatorアプリから呼び出される）
#
# 役割:
# 1. scribeサーバー(ポート8765)がすでに起動しているか確認する
# 2. 起動していなければ、バックグラウンドで起動する
# 3. 少し待ってから、ブラウザでscribeのページを開く
#
# ターミナルウィンドウは一切表示されない（Automatorアプリ経由で実行されるため）。

PORT=8765
QUARTZ_DIR="$HOME/quartz"
LOG_FILE="$QUARTZ_DIR/logs/scribe_app.log"

mkdir -p "$QUARTZ_DIR/logs"

# すでにポート8765が使われているか確認する
if lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    # すでに起動中なら、サーバーは起動せず、ブラウザを開くだけにする
    echo "$(date): scribeは既に起動中です。ブラウザのみ開きます。" >> "$LOG_FILE"
else
    # 起動していない場合、バックグラウンドでサーバーを起動する
    echo "$(date): scribeサーバーを起動します。" >> "$LOG_FILE"
    cd "$QUARTZ_DIR" || exit 1
    nohup python3 scripts/scribe_server.py >> "$LOG_FILE" 2>&1 &
    disown 2>/dev/null || true

    # サーバーが起動するまで少し待つ（最大5秒、起動できたら即抜ける）
    for i in 1 2 3 4 5; do
        sleep 1
        if lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
            break
        fi
    done
fi

# ブラウザでscribeを開く
open "http://localhost:$PORT"
