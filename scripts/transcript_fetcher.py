import os, re, glob, json, requests, tempfile, yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

LISTEN_TOKEN = os.environ.get('LISTEN_API_TOKEN')
OPENAI_CLIENT = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
VAULT_PATH = '/Users/andy/quartz/content'
PROCESSED_FILE = '/Users/andy/quartz/processed_transcripts.json'

LISTEN_SHOWS = {
    'sakanakaigi': '01khxgmkwpazf4axtsmh04wvh9',
    'mimoriradio':  '01khxg4sm73tkv2xw8bgh8cdmd',
    'longpost':     '01knxjrb66jaxjvvaybnjz0662',
}

def load_config():
    with open('/Users/andy/quartz/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_processed(data):
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def graphql(query):
    r = requests.post(
        'https://listen.style/graphql',
        json={'query': query},
        headers={'Authorization': f'Bearer {LISTEN_TOKEN}'}
    )
    return r.json()

def get_listen_episodes(podcast_id):
    query = f"""
    query {{
      podcast(id: "{podcast_id}") {{
        episodes(first: 200) {{
          data {{ id title pubDate transcriptTxt }}
        }}
      }}
    }}
    """
    data = graphql(query)
    return data['data']['podcast']['episodes']['data']

def find_md_file(show_name, pub_date, title):
    """pubDateとタイトルでMarkdownファイルを探す"""
    date_str = pub_date[:10]
    pattern = f"{VAULT_PATH}/episodes/{show_name}/{date_str}-*.md"
    files = glob.glob(pattern)
    if len(files) == 1:
        return files[0]
    # 複数ある場合はタイトルで絞り込む
    for f in files:
        basename = os.path.basename(f).replace('.md', '')
        file_title = basename[11:]  # 日付部分を除く
        if file_title[:20] in title[:20] or title[:20] in file_title[:20]:
            return f
    return files[0] if files else None

def update_transcript_in_md(md_path, transcript_text):
    """MarkdownファイルのTranscriptセクションを更新"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if '（取得予定）' not in content:
        return False  # すでに処理済み
    content = content.replace('（取得予定）', transcript_text)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

def get_transcript_whisper(audio_url, whisper_prompt):
    """Whisper APIで文字起こし"""
    r = requests.get(audio_url, stream=True, timeout=60)
    suffix = '.m4a' if 'm4a' in audio_url else '.mp3'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
        tmp_path = f.name
    try:
        with open(tmp_path, 'rb') as f:
            result = OPENAI_CLIENT.audio.transcriptions.create(
                model="whisper-1", file=f, language="ja", prompt=whisper_prompt
            )
        return result.text
    finally:
        os.unlink(tmp_path)

def process_listen_show(show_name, podcast_id, processed):
    """LISTENからトランスクリプトを取得して保存"""
    print(f"\n📻 {show_name} (LISTEN)")
    episodes = get_listen_episodes(podcast_id)
    done = 0
    skipped = 0
    no_transcript = 0

    for ep in episodes:
        ep_id = ep['id']
        if processed.get(ep_id):
            skipped += 1
            continue
        transcript = ep.get('transcriptTxt')
        if not transcript:
            no_transcript += 1
            processed[ep_id] = 'no_transcript'
            continue
        md_path = find_md_file(show_name, ep['pubDate'], ep['title'])
        if not md_path:
            print(f"  ⚠️ MDファイル見つからず: {ep['pubDate'][:10]} {ep['title'][:30]}")
            continue
        updated = update_transcript_in_md(md_path, transcript)
        if updated:
            print(f"  ✅ {ep['pubDate'][:10]} {ep['title'][:40]}")
            done += 1
        else:
            skipped += 1
        processed[ep_id] = 'done'
        save_processed(processed)

    print(f"  完了: {done}件 / スキップ: {skipped}件 / トランスクリプトなし: {no_transcript}件")

def get_fresh_audio_url(show_rss, episode_title):
    """RSSから最新の音声URLを取得"""
    import feedparser
    feed = feedparser.parse(show_rss)
    for entry in feed.entries:
        if entry.title[:20] in episode_title or episode_title[:20] in entry.title:
            return entry.enclosures[0].href if entry.enclosures else None
    return None

def process_whisper_show(show_name, processed):
    """Whisper APIでトランスクリプトを取得して保存"""
    config = load_config()
    show = next(s for s in config['shows'] if s['name'] == show_name)
    whisper_prompt = show.get('whisper_prompt', '')

    print(f"\n📻 {show_name} (Whisper)")
    md_files = sorted(glob.glob(f"{VAULT_PATH}/episodes/{show_name}/*.md"))
    done = 0
    skipped = 0

    for md_path in md_files:
        filename = os.path.basename(md_path)
        if processed.get(filename):
            skipped += 1
            continue
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if '（取得予定）' not in content:
            skipped += 1
            processed[filename] = 'done'
            continue
        m = re.search(r'audio_url:\s*"([^"]+)"', content)
        if not m or not m.group(1):
            print(f"  ⚠️ audio_urlなし: {filename[:40]}")
            continue
        # RSSから最新URLを取得（保存済みURLは期限切れの場合あり）
        episode_title = filename[11:].replace('.md', '')
        fresh_url = get_fresh_audio_url(show['rss_url'], episode_title)
        audio_url = fresh_url if fresh_url else m.group(1)
        print(f"  🎙 {filename[:50]}...")
        success = False
        for attempt in range(3):
            try:
                transcript = get_transcript_whisper(audio_url, whisper_prompt)
                update_transcript_in_md(md_path, transcript)
                print(f"  ✅ 完了")
                done += 1
                success = True
                break
            except Exception as e:
                if attempt < 2:
                    import time
                    print(f"  ⚠️ リトライ {attempt+1}/3: {e}")
                    time.sleep(10)
                else:
                    print(f"  ❌ エラー: {e}")
        if not success:
            continue
        processed[filename] = 'done'
        save_processed(processed)

    print(f"  完了: {done}件 / スキップ: {skipped}件")

if __name__ == '__main__':
    import sys
    processed = load_processed()

    # テストモード（引数なし）は1件だけ
    test_mode = '--all' not in sys.argv

    if test_mode:
        print("🧪 テストモード（1番組1件のみ）")
        print("全件処理するには: python3 transcript_fetcher.py --all")

        # サカナカイギで1件だけテスト
        episodes = get_listen_episodes(LISTEN_SHOWS['sakanakaigi'])
        ep = next((e for e in episodes if e.get('transcriptTxt')), None)
        if ep:
            md_path = find_md_file('sakanakaigi', ep['pubDate'], ep['title'])
            if md_path:
                print(f"\n対象: {os.path.basename(md_path)}")
                updated = update_transcript_in_md(md_path, ep['transcriptTxt'])
                if updated:
                    print("✅ 文字起こしを保存しました")
                    print(f"\n--- 最初の200文字 ---")
                    print(ep['transcriptTxt'][:200])
                else:
                    print("すでに処理済みです")
    else:
        print("🌿 全エピソード処理開始")
        # LISTEN対応番組
        for show_name, podcast_id in LISTEN_SHOWS.items():
            process_listen_show(show_name, podcast_id, processed)
        # Whisper対応番組
        process_whisper_show('on-airdo', processed)
        print("\n🌿 全処理完了！")
