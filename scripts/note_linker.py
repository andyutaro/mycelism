"""
note_linker.py

content/notes/memo/ 以下の走り書きメモ同士の意味的な関連を見つけ、
本文中の既存の語句をそのまま [[ ]] で囲んでリンク化するスクリプト。

設計方針（重要・変更しないこと）:
- AIは本文の言葉を一切リライトしない。既存の語句をそのまま [[ ]] で囲むだけ。
- 関連が見つからない場合は何もしない（無理にリンクを作らない）。
- ポッドキャスト由来の concepts/ とのリンクは対象外。あくまでnotes同士。
- 処理済みのメモは processed_notes.json に記録し、本文に変更がない限り再処理しない。
- 1回のAI呼び出しで「新しいメモ1件」 vs 「既存メモ全件」を比較する設計
  （現状ノート総量が小さい=21KB程度のため、全件をコンテキストに含めて問題ない）
"""

import os
import re
import json
import glob
import hashlib
import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

VAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content')
NOTES_DIR = os.path.join(VAULT_PATH, 'notes')  # memo/diary/article等、notes以下を再帰的に全て対象にする
PROCESSED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'processed_notes.json')


class ParseError(Exception):
    """AIの返答形式が想定外だった場合に投げる。'本当に関連なし'(None)とは明確に区別する。
    main側でこの例外を捕まえた場合は processed に記録せず、次回また再試行させる。"""
    pass


def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_processed(data):
    with open(PROCESSED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def content_hash(text):
    """本文のハッシュ値。次回以降、内容が変わっていなければ再処理をスキップするための判定に使う"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]


def load_all_notes():
    """
    全ノートのタイトルと本文を読み込む。notes/以下を再帰的に探索する(memo/diary/article等すべて対象)。
    戻り値: [{'title': str, 'path': str, 'body': str}, ...]

    titleはファイル名のみ(拡張子なし)。memo/diary/article間で同名ファイルがあった場合に備え、
    内部的な一意キーにはpathを使うが、AIへの表示や[[ ]]のリンク先指定にはtitle(ファイル名)を使う。
    Obsidianのリンク解決もファイル名ベースのため、ここはファイル名を正としておく。
    """
    notes = []
    for filepath in sorted(glob.glob(os.path.join(NOTES_DIR, '**', '*.md'), recursive=True)):
        title = os.path.basename(filepath).replace('.md', '')
        with open(filepath, 'r', encoding='utf-8') as f:
            body = f.read()
        notes.append({'title': title, 'path': filepath, 'body': body})
    return notes


def find_links_for_note(target_note, other_notes):
    """
    target_note の本文を読み、other_notes の中から意味的に関連するものを探す。
    見つかった場合、target_note の本文中で関連語句をどう [[ ]] で囲むべきかをAIに提案させる。

    戻り値: {'updated_body': str, 'linked_titles': [str, ...]} または None（関連なしの場合）
    """
    if not other_notes:
        return None

    # 既存ノートの一覧をAIに見せる（タイトルと冒頭150字だけで十分。本文全体を渡すと無駄に長くなる）
    others_text = "\n".join(
        f"- 「{n['title']}」: {n['body'].strip()[:150].replace(chr(10), ' ')}"
        for n in other_notes
    )

    prompt = f"""以下は、ある人物が書いた「新しいメモ」と、これまでに書かれた「既存のメモ一覧」です。

# 新しいメモのタイトル
{target_note['title']}

# 新しいメモの本文
{target_note['body']}

# 既存のメモ一覧（タイトルと冒頭抜粋）
{others_text}

# 指示
新しいメモの本文を読み、既存のメモ一覧の中で、意味的に明確に関連するものがあれば、
新しいメモの本文中の「既存の語句」をそのまま [[ノートのタイトル]] という形式で囲んでください。

厳守事項:
- 本文の言葉や言い回し、語順、改行は一切変更しないこと。既存の語句を [[ ]] で囲むだけ。
- 新しい文章や説明、要約、考察を追加しないこと。
- 関連が薄い、こじつけになりそうな場合は絶対にリンクを作らないこと。関連が本当にないなら、本文をそのまま返す。
- リンクは多くても3つまで。確信度の高いものだけ。
- 「新しいメモ」自身のタイトル（{target_note['title']}）へのリンクは絶対に作らないこと（自己参照は禁止）。
- すでに本文中に [[ ]] が存在する場合、それらはそのまま残し、二重にリンクを追加しないこと。

返答は以下の形式で、説明文やコードブロック記号(```)は一切付けないこと。
本文はエスケープせず、改行はそのまま改行として出力すること。

最初に区切り行 ===BODY=== を1行だけ書き、その次の行から本文全文を出力する。
本文が終わったら区切り行 ===LINKS=== を1行だけ書き、その次の行にリンクしたタイトルをカンマ区切りで1行で書く（関連なしの場合は空行のままでよい）。

出力例:
===BODY===
（ここから本文。複数行になってもよい。最後の行まで本文が続く）
===LINKS===
タイトルA,タイトルB
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )

    if message.stop_reason == 'max_tokens':
        raise ParseError(
            f"出力が長すぎてmax_tokensで切れた: {target_note['title']} "
            f"(本文が長すぎる可能性。max_tokensをさらに増やすか、本文を分割してください)"
        )

    text = message.content[0].text.strip()

    if '===BODY===' not in text or '===LINKS===' not in text:
        preview = text[:300].replace('\n', '\\n')
        raise ParseError(f"想定外の返答形式: {target_note['title']} / 応答の先頭300字: {preview}")

    try:
        body_part = text.split('===BODY===', 1)[1].split('===LINKS===')[0]
        links_part = text.split('===LINKS===', 1)[1]
    except IndexError:
        raise ParseError(f"返答の分割に失敗: {target_note['title']}")

    updated_body = body_part.strip('\n')
    linked_titles_raw = [t.strip() for t in links_part.strip().split(',') if t.strip()]

    # 自己参照と、existing other_notesに存在しないタイトルを除外（AIの誤りに対する二重の安全策）
    valid_titles = {n['title'] for n in other_notes}
    linked_titles = [
        t for t in linked_titles_raw
        if t != target_note['title'] and t in valid_titles
    ]

    if not linked_titles:
        return None

    return {'updated_body': updated_body, 'linked_titles': linked_titles}


def add_backlink(linked_note_path, from_title):
    """
    リンクされた側のノートの末尾に、参照元への逆リンクを追記する。
    本文を書き換えるのではなく、ファイル末尾に「## 関連メモ」セクションとして追記する。
    既にそのセクションがあれば追記、なければ新規作成。
    """
    with open(linked_note_path, 'r', encoding='utf-8') as f:
        content = f.read()

    backlink_line = f"- [[{from_title}]]"

    if '## 関連メモ' in content:
        if backlink_line in content:
            return  # 既に同じ逆リンクがあれば何もしない
        content = content.rstrip() + f"\n{backlink_line}\n"
    else:
        content = content.rstrip() + f"\n\n## 関連メモ\n{backlink_line}\n"

    with open(linked_note_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    print("🌿 ノート間リンクの解析を開始します...")
    processed = load_processed()
    all_notes = load_all_notes()
    title_to_path = {n['title']: n['path'] for n in all_notes}

    updated_count = 0

    for note in all_notes:
        h = content_hash(note['body'])
        if processed.get(note['title']) == h:
            continue  # 内容に変更がなければスキップ

        other_notes = [n for n in all_notes if n['title'] != note['title']]
        print(f"  解析中: {note['title'][:40]}...")

        try:
            result = find_links_for_note(note, other_notes)
        except ParseError as e:
            print(f"  ⚠️ 解析エラー(次回再試行されます): {e}")
            continue
        except Exception as e:
            print(f"  ❌ 予期しないエラー(次回再試行されます): {e}")
            continue

        if result is None:
            print(f"    → 関連なし")
            processed[note['title']] = h
            save_processed(processed)
            continue

        # 本文を更新
        with open(note['path'], 'w', encoding='utf-8') as f:
            f.write(result['updated_body'])

        # リンク先ノートに逆リンクを追記
        for linked_title in result['linked_titles']:
            linked_path = title_to_path.get(linked_title)
            if linked_path:
                add_backlink(linked_path, note['title'])

        print(f"    ✅ リンク追加: {result['linked_titles']}")
        # ハッシュは更新後の本文で記録（次回また同じ内容で再処理しないように）
        processed[note['title']] = content_hash(result['updated_body'])
        save_processed(processed)
        updated_count += 1

    print(f"\n🌿 完了: {updated_count}件のノートにリンクを追加しました")


if __name__ == '__main__':
    main()
