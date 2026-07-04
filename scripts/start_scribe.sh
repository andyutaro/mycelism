#!/bin/bash

# 旧scribeは2026-07-04に引退しました(REDEフェーズ2でクラウド化)。
# 新しい放送卓: https://rede-web-chi.vercel.app/desk
#
# このスクリプトはもうローカルサーバー(scribe_server.py)を起動しません。
# 旧Automatorアプリ(/Applications/scribe.app)から呼ばれた場合も、
# 新しいdeskを開くだけの誘導として振る舞います。
# 旧実装を復元したい場合はこのリポジトリのgit履歴から戻せます。

echo "$(date): 旧scribeは引退済み。新しいdeskへ誘導します。" >> "$HOME/quartz/logs/scribe_app.log"
open "https://rede-web-chi.vercel.app/desk"
