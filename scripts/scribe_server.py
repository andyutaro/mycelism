"""
scribe_server.py

「まっさらな書く場所」のローカルサーバー。
Python標準ライブラリのみで動作する(Flask等のインストールを不要にするための判断)。

起動方法:
    python3 scribe_server.py

起動すると http://localhost:8765 が立ち上がる。
ブラウザでこのURLを開くと、まっさらなエディタが表示される。

保存先:
    content/notes/diary/YYYY-MM-DD.md  (1日1ファイル、何度書いても同じファイルに上書き保存)
    content/notes/diary/images/        (ドラッグ&ドロップした画像・PDFの保存先)

このサーバーは「HTMLとして」エディタの内容を保持しつつ、保存時にMarkdown相当の
プレーンテキスト+画像/PDFリンクに変換してファイルに書き出す。
Andyさんの「・」「①②③」「【】」「空白行」といった独自の区切り方は、
そのままプレーンテキストとして温存される(余計な整形をしない、という設計判断)。
"""

import http.server
import socketserver
import json
import os
import re
import html as html_module
import uuid
import datetime

PORT = 8765

# このファイル自身の場所から、quartzリポジトリのcontent/notes/diaryを逆算する。
# scribe_server.py は ~/quartz/scripts/ に置く想定 (run.py等と同じ場所)。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIARY_DIR = os.path.join(BASE_DIR, 'content', 'notes', 'diary')
IMAGES_DIR = os.path.join(DIARY_DIR, 'images')
INDEX_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scribe_index.html')

os.makedirs(DIARY_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


def today_filename():
    return datetime.date.today().strftime('%Y-%m-%d') + '.md'


def today_path():
    return os.path.join(DIARY_DIR, today_filename())


def html_to_text(raw_html):
    """
    contenteditableのinnerHTMLを、保存用のプレーンテキスト(+画像/PDF/埋め込みの参照)に変換する。
    Markdown記法への変換は行わない。Andyさんが書いた区切り文字(・、①②③、【】、空行)を
    そのまま尊重し、改行構造だけを素直にテキスト化する。
    """
    text = raw_html

    # 画像 -> Markdown画像記法（パスはQuartzルートから見た絶対パスに変換）
    # 例: images/foo.png -> /notes/diary/images/foo.png
    # class属性は "embed-image" 単体とは限らず、選択状態などで他のクラスと併記される
    # 場合もあるため、クラス名を含むかどうかで判定する(完全一致にしない)。
    # 前後に改行は付与しない(改行の管理は後続のdiv構造解析に一本化するため)。
    text = re.sub(
        r'<img[^>]*class="[^"]*embed-image[^"]*"[^>]*src="([^"]+)"[^>]*>',
        lambda m: f'![](/notes/diary/{m.group(1)})',
        text
    )
    # PDFリンク（同様に絶対パスへ変換）
    text = re.sub(
        r'<a[^>]*class="[^"]*embed-pdf[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        lambda m: f'[{re.sub("<.*?>", "", m.group(2))}](/notes/diary/{m.group(1)})',
        text,
        flags=re.DOTALL
    )
    # ポッドキャスト埋め込み(iframe) -> 元のURLを復元できないため、iframeのsrcをそのままリンクとして残す
    text = re.sub(
        r'<div[^>]*class="[^"]*embed-podcast[^"]*"[^>]*>\s*<iframe[^>]*src="([^"]+)"[^>]*>.*?</iframe>\s*</div>',
        lambda m: convert_embed_src_to_original(m.group(1)),
        text,
        flags=re.DOTALL
    )

    # 改行系タグをテキストの改行に変換する。
    #
    # ブラウザのcontenteditableでは、Enterキーを押すたびに新しい<div>が
    # 作られる。つまり「1個の<div>」が「1行」に対応する。空行を作りたい場合、
    # その行のdivは中身が空(<br>のみ、または完全に空)になる。
    # ここでは正規表現の繰り返し書き換えによる数え上げの重複を避けるため、
    # HTMLをdivの境界で分割し、各行を素直に\nで連結し直す。
    #
    # 例: <div>1行目</div><div><br></div><div>3行目</div>
    #   -> ["1行目", "", "3行目"] -> "1行目\n\n3行目" (空行1つ分の\n\nが入る)
    div_pattern = re.compile(r'<div[^>]*>(.*?)</div>', re.DOTALL)
    divs = div_pattern.findall(text)

    if divs:
        # 最初のdivより前にあるテキスト(1行目。まだdivで囲まれていない場合がある)
        first_div_start = text.find('<div')
        prefix = text[:first_div_start] if first_div_start != -1 else ''

        lines = [prefix] if prefix.strip() or prefix == '' else []
        for d in divs:
            # <br>だけ、または完全に空のdivは「空行」を表す
            stripped = re.sub(r'<br\s*/?>', '', d).strip()
            lines.append('' if stripped == '' and ('<br' in d or d.strip() == '') else d)
        # 行と行の間は最低でも2個の改行(Markdown上で確実に改行・段落として
        # 認識されるための下限)を保証する。Enterを多く押して作った、
        # より大きい余白(空行が複数続く場合)は、その分さらに増やして反映する。
        # 1 div = 1 行 として忠実に連結（空行も打った通りに保存）
        text = '\n'.join(lines)
    else:
        # divが存在しない(単純な<br>だけの場合)
        text = re.sub(r'<br\s*/?>', '\n', text)

    # 残った全てのHTMLタグを除去
    text = re.sub(r'<[^>]+>', '', text)

    # HTMLエンティティをデコード(&amp; &lt; など)
    text = html_module.unescape(text)

    # 改行が無限に肥大化することだけを防ぐための上限(Enterを10回以上連続で
    # 押すような極端なケースのみ制限し、通常使う2-4回程度の改行は保持する)。
    text = re.sub(r'\n{12,}', '\n' * 11, text)

    return text.strip() + '\n'


def convert_embed_src_to_original(embed_src):
    """埋め込み用URL(iframeのsrc)を、人間が読んで分かる元のURL形式に戻す(完全な逆変換ではなく実用上の近似)"""
    if 'open.spotify.com/embed/episode/' in embed_src:
        return embed_src.replace('/embed/episode/', '/episode/')
    if 'open.spotify.com/embed/show/' in embed_src:
        return embed_src.replace('/embed/show/', '/show/')
    if 'embed.podcasts.apple.com' in embed_src:
        return embed_src.replace('embed.podcasts.apple.com', 'podcasts.apple.com')
    if 'youtube.com/embed/' in embed_src:
        vid = embed_src.split('/embed/')[-1].split('?')[0]
        return f'https://www.youtube.com/watch?v={vid}'
    return embed_src


def text_to_html_preview(text):
    """
    保存されたテキストを読み込んで、エディタ(contenteditable)に再表示するためのHTMLに戻す。
    画像/PDFのMarkdown記法は埋め込み要素に戻す。ポッドキャストURLも再カード化する。
    """
    if not text:
        return ''

    escaped = html_module.escape(text)

    # 画像 ![]() -> img
    escaped = re.sub(
        r'!\[\]\(([^)]+)\)',
        lambda m: f'<img class="embed-image" contenteditable="false" src="{m.group(1)}">',
        escaped
    )
    # PDFリンク [text](url) -> a (画像記法に変換されなかった残り)
    escaped = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: f'<a class="embed-pdf" contenteditable="false" href="{m.group(2)}" target="_blank">📄 {m.group(1)}</a>',
        escaped
    )

    # 改行をbrに戻す
    escaped = escaped.replace('\n', '<br>')

    return escaped


def parse_multipart(body, boundary):
    """
    cgiモジュールに依存せず、multipart/form-dataの本文から
    ファイルパート(filename, content)を抜き出す簡易パーサー。
    今回の用途(単一ファイルのアップロード)に限定したシンプルな実装。
    """
    boundary_bytes = ('--' + boundary).encode('utf-8')
    parts = body.split(boundary_bytes)
    for part in parts:
        if b'filename=' not in part:
            continue
        # ヘッダーとボディの区切り(\r\n\r\n)を見つける
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            continue
        header_bytes = part[:header_end]
        content = part[header_end + 4:]
        # 末尾の \r\n-- を取り除く
        content = content.rstrip(b'\r\n')
        if content.endswith(b'--'):
            content = content[:-2].rstrip(b'\r\n')

        header_text = header_bytes.decode('utf-8', errors='ignore')
        m = re.search(r'filename="([^"]*)"', header_text)
        filename = m.group(1) if m else 'upload'
        return filename, content
    return None, None


class ScribeHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        # /api/load, /api/today は常に最新の状態を返す必要があるため、キャッシュを禁止する
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self._serve_index()
        elif self.path == '/api/load':
            self._handle_load()
        elif self.path == '/api/today':
            self._handle_today()
        elif self.path.startswith('/images/') or self.path.startswith('/notes/diary/images/'):
            self._serve_image()
        else:
            self.send_error(404)

    def _handle_today(self):
        # ブラウザ側が「日付が変わったか」を定期的に確認するための軽量API
        self._send_json({'date': datetime.date.today().isoformat()})

    def _serve_image(self):
        # /images/ファイル名 または /notes/diary/images/ファイル名 のどちらの形式でも受け付ける。
        # (前者はscribe内での再表示用、後者はQuartz本番サイトと同じ絶対パス形式)
        # パストラバーサル(../など)を防ぐため、basenameだけを取り出してIMAGES_DIR内に限定する。
        filename = os.path.basename(self.path)
        filepath = os.path.join(IMAGES_DIR, filename)

        if not os.path.isfile(filepath):
            self.send_error(404)
            return

        ext = os.path.splitext(filename)[1].lower()
        content_type = {
            '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.gif': 'image/gif', '.webp': 'image/webp', '.pdf': 'application/pdf',
        }.get(ext, 'application/octet-stream')

        with open(filepath, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == '/api/save':
            self._handle_save()
        elif self.path == '/api/upload':
            self._handle_upload()
        else:
            self.send_error(404)

    def _serve_index(self):
        try:
            with open(INDEX_HTML_PATH, 'rb') as f:
                body = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_error(500, 'scribe_index.html が見つかりません')

    def _handle_load(self):
        path = today_path()
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            self._send_json({'html': text_to_html_preview(text)})
        else:
            self._send_json({'html': ''})

    def _handle_save(self):
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode('utf-8'))
        except json.JSONDecodeError:
            self._send_json({'ok': False}, status=400)
            return

        # 通常は「今日」のファイルに保存する。ただし、日付をまたいだ直後など
        # 「この内容は元々別の日に書かれたものだ」と分かっている場合は、
        # クライアント側から target_date (YYYY-MM-DD) を明示的に指定できる。
        # これにより、日付が変わった後の内容を誤って新しい日のファイルに
        # 書き込んでしまう事故を防ぐ。
        target_date = data.get('target_date')
        if target_date:
            try:
                datetime.date.fromisoformat(target_date)  # 形式の妥当性チェック
                save_path = os.path.join(DIARY_DIR, f'{target_date}.md')
            except ValueError:
                save_path = today_path()
        else:
            save_path = today_path()

        text = html_to_text(data.get('html', ''))
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(text)
        self._send_json({'ok': True})

    def _handle_upload(self):
        content_type = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in content_type:
            self._send_json({'url': None}, status=400)
            return

        m = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type)
        if not m:
            self._send_json({'url': None}, status=400)
            return
        boundary = m.group(1) or m.group(2)

        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        filename, content = parse_multipart(body, boundary)
        if content is None:
            self._send_json({'url': None}, status=400)
            return

        ext = os.path.splitext(filename)[1] or ''
        unique_name = f"{datetime.date.today().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}{ext}"
        save_path = os.path.join(IMAGES_DIR, unique_name)

        with open(save_path, 'wb') as f:
            f.write(content)

        # diary/*.md から見た相対パス (同じdiaryフォルダ内のimages/を指す)
        relative_url = f'images/{unique_name}'
        self._send_json({'url': relative_url})

    def log_message(self, format, *args):
        # コンソールを静かにする(必要なら標準のログ出力に変更可)
        pass


def main():
    with socketserver.TCPServer(('127.0.0.1', PORT), ScribeHandler) as httpd:
        url = f'http://localhost:{PORT}'
        print(f'🖋  scribe is running at {url}')
        print(f'   ブラウザでこのURLを開いてください: {url}')
        print(f'   保存先: {DIARY_DIR}')
        print(f'   (再起動のたびに新しいタブが開くのを防ぐため、自動オープンはしていません)')
        httpd.serve_forever()


# NORMALIZE_HOOK
from scribe_normalize import normalize as _nz_normalize
_nz_orig_html_to_text = html_to_text
def html_to_text(raw_html):
    return _nz_normalize(_nz_orig_html_to_text(raw_html))
# /NORMALIZE_HOOK

if __name__ == '__main__':
    main()
