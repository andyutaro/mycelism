import os
import yaml

def load_config():
    with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as f:
        return yaml.safe_load(f)

def write_episode(episode, ai_result, show):
    config = load_config()
    vault_path = config['vault_path']
    show_name = show['name']

    dir_path = os.path.join(vault_path, 'episodes', show_name)
    os.makedirs(dir_path, exist_ok=True)

    safe_title = episode["title"].replace(chr(34), "'").replace('/', '／').replace(':', '：')[:60]
    filename = f"{episode['pub_date']}-{safe_title}.md"
    filepath = os.path.join(dir_path, filename)

    keywords_wikilinks = ' '.join([f'[[{kw}]]' for kw in ai_result['keywords']])

    spotify_btn = f'<a href="{episode["spotify_url"]}" target="_blank">Spotifyで聴く</a>' if episode.get('spotify_url') else ''
    apple_btn = f'<a href="{episode["apple_url"]}" target="_blank">Apple Podcastsで聴く</a>' if episode.get('apple_url') else ''

    audio_player = ''
    if episode.get('audio_url'):
        audio_player = f'''<audio controls style="width:100%">
  <source src="{episode['audio_url']}" type="audio/mpeg">
</audio>'''

    content = f"""---
title: "{title_yaml}"
date: {episode['pub_date']}
show: {show_name}
audio_url: "{episode.get('audio_url', '')}"
spotify_url: "{episode.get('spotify_url', '')}"
apple_url: "{episode.get('apple_url', '')}"
tags:
  - episode
  - {show_name}
---

## {episode['title']}

{ai_result['caption']}

{spotify_btn}
{apple_btn}

{audio_player}

## 要約

{ai_result['summary']}

## キーワード

{keywords_wikilinks}

## 文字起こし

（取得予定）
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath

def write_concept(keyword, episode, ai_result, show):
    config = load_config()
    vault_path = config['vault_path']

    dir_path = os.path.join(vault_path, 'concepts')
    os.makedirs(dir_path, exist_ok=True)

    filepath = os.path.join(dir_path, f'{keyword}.md')
    show_name = show['name']
    ep_title = episode['title']
    ep_date = episode['pub_date']

    new_ref = f"- [[episodes/{show_name}/{ep_date}-{ep_title[:60].replace('/', '／').replace(':', '：')}|{ep_title[:40]}]] ({ep_date})"

    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing = f.read()
        updated = existing.rstrip() + '\n' + new_ref + '\n'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
    else:
        content = f"""---
tags:
  - concept
---

## {keyword}

（説明文は今後のエピソードから自動生成されます）

## 参照元

{new_ref}
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return filepath

if __name__ == '__main__':
    from ai_processor import process_episode

    test_episode = {
        'title': '#7 世界に広がる「ネコ」の進化とサクセスストーリー〜イエネコ編その1【ミモリラジオ】',
        'description': '【ネコ編・その1】森にもいる。どこにでもいる。/ ネコの学名はイエネコ (Felis catus) / 「侵略的外来種ワースト100」に登録されているネコ',
        'pub_date': '2022-11-29',
        'audio_url': 'https://anchor.fm/s/ccd5236c/podcast/play/81334770',
        'spotify_url': '',
        'apple_url': '',
    }
    test_show = {
        'name': 'mimoriradio',
        'max_keywords': 6,
    }

    print("AI処理中...")
    result = process_episode(test_episode, test_show)

    print("Markdown生成中...")
    ep_path = write_episode(test_episode, result, test_show)
    print(f"エピソードページ: {ep_path}")

    for kw in result['keywords']:
        cp_path = write_concept(kw, test_episode, result, test_show)
        print(f"conceptページ: {cp_path}")
