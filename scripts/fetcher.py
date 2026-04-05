import feedparser
import yaml
import json
import os
from datetime import datetime

def load_config():
    with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as f:
        return yaml.safe_load(f)

def load_processed():
    path = os.path.join(os.path.dirname(__file__), '..', 'processed.json')
    with open(path, 'r') as f:
        return json.load(f)

def save_processed(data):
    path = os.path.join(os.path.dirname(__file__), '..', 'processed.json')
    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_new_episodes(show):
    feed = feedparser.parse(show['rss_url'])
    processed = load_processed()
    done = processed['episodes'].get(show['name'], [])

    new_episodes = []
    for entry in feed.entries:
        ep_id = entry.get('id') or entry.get('link')
        if ep_id in done:
            continue

        audio_url = ''
        for enclosure in entry.get('enclosures', []):
            if 'audio' in enclosure.get('type', ''):
                audio_url = enclosure.get('href', '')
                break

        spotify_url = ''
        apple_url = ''
        for link in entry.get('links', []):
            href = link.get('href', '')
            if 'spotify.com' in href:
                spotify_url = href
            elif 'apple.com' in href or 'podcasts.apple.com' in href:
                apple_url = href

        pub_date = entry.get('published', '')
        try:
            parsed_date = datetime(*entry.published_parsed[:6])
            pub_date = parsed_date.strftime('%Y-%m-%d')
        except:
            pass

        new_episodes.append({
            'id': ep_id,
            'title': entry.get('title', ''),
            'description': entry.get('summary', ''),
            'pub_date': pub_date,
            'audio_url': audio_url,
            'spotify_url': spotify_url,
            'apple_url': apple_url,
        })

    return new_episodes

if __name__ == '__main__':
    config = load_config()
    for show in config['shows']:
        print(f"\n--- {show['name']} ---")
        episodes = fetch_new_episodes(show)
        print(f"新着エピソード数: {len(episodes)}")
        if episodes:
            print(f"最新: {episodes[0]['title']}")
            print(f"audio_url: {episodes[0]['audio_url'][:50] if episodes[0]['audio_url'] else 'なし'}")
