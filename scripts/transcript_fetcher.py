import os
import requests
import tempfile
import yaml
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def load_config():
    with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as f:
        return yaml.safe_load(f)

def get_transcript(audio_url, whisper_prompt):
    """音声URLからWhisperで文字起こしを取得"""
    # 音声ダウンロード
    r = requests.get(audio_url, stream=True, timeout=60)
    suffix = '.m4a' if 'm4a' in audio_url else '.mp3'
    
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
        tmp_path = f.name

    try:
        with open(tmp_path, 'rb') as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ja",
                prompt=whisper_prompt
            )
        return transcript.text
    finally:
        os.unlink(tmp_path)

def update_transcript(md_path, transcript_text):
    """既存のMarkdownファイルの文字起こしセクションを更新"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if '（取得予定）' in content:
        content = content.replace('（取得予定）', transcript_text)
    elif '## 文字起こし' in content:
        # すでに取得済みならスキップ
        after = content.split('## 文字起こし')[1].strip()
        if after and after != '（取得予定）':
            return False  # スキップ
        content = content.replace('## 文字起こし\n\n（取得予定）', f'## 文字起こし\n\n{transcript_text}')

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

if __name__ == '__main__':
    import glob
    import feedparser

    config = load_config()
    vault_path = config['vault_path']

    # 1番組・1エピソードでテスト
    show_key = 'on-airdo'
    show = next(s for s in config['shows'] if s['name'] == show_key)
    whisper_prompt = show.get('whisper_prompt', '')

    # 最新エピソードのmdファイルを探す
    md_files = sorted(glob.glob(f"{vault_path}/episodes/{show_key}/*.md"), reverse=True)
    if not md_files:
        print("mdファイルが見つかりません")
        exit()

    md_path = md_files[0]
    print(f"対象: {os.path.basename(md_path)}")

    # audio_urlをmdから取得
    with open(md_path, 'r') as f:
        content = f.read()

    import re
    m = re.search(r'audio_url:\s*"([^"]+)"', content)
    if not m or not m.group(1):
        print("audio_urlが見つかりません")
        exit()

    audio_url = m.group(1)
    print(f"音声URL: {audio_url[:60]}...")
    print("文字起こし中（数分かかります）...")

    transcript = get_transcript(audio_url, whisper_prompt)
    updated = update_transcript(md_path, transcript)
    
    if updated:
        print("完了！文字起こしを保存しました")
        print(f"\n--- 最初の300文字 ---")
        print(transcript[:300])
    else:
        print("すでに文字起こし済みです")
