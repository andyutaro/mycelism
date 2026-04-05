import os
import sys
import json
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from fetcher import fetch_new_episodes, load_config, load_processed, save_processed
from ai_processor import process_episode
from md_writer import write_episode, write_concept

def main():
    print("🌿 Mycelism 更新を開始します...")
    config = load_config()
    processed = load_processed()
    total_new = 0

    for show in config['shows']:
        print(f"\n📻 {show['name']} を処理中...")
        new_episodes = fetch_new_episodes(show)

        if not new_episodes:
            print(f"  新着なし")
            continue

        print(f"  新着: {len(new_episodes)}件")

        for episode in reversed(new_episodes):
            print(f"  処理中: {episode['title'][:40]}...")

            try:
                ai_result = process_episode(episode, show)
                ep_path = write_episode(episode, ai_result, show)
                print(f"  ✅ エピソードページ生成")

                for kw in ai_result['keywords']:
                    write_concept(kw, episode, ai_result, show)
                print(f"  ✅ conceptページ更新 ({len(ai_result['keywords'])}個)")

                ep_id = episode['id']
                if show['name'] not in processed['episodes']:
                    processed['episodes'][show['name']] = []
                processed['episodes'][show['name']].append(ep_id)
                save_processed(processed)
                total_new += 1

            except Exception as e:
                print(f"  ❌ エラー: {e}")
                continue

    print(f"\n🌿 完了！ 新規処理: {total_new}件")

if __name__ == '__main__':
    main()
