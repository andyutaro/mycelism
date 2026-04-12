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

    # 新エピソードがあれば各種更新
    if total_new > 0:
        import subprocess
        base = os.path.dirname(os.path.dirname(__file__))

        print(f"\n🔗 シリーズリンクを更新中...")
        try:
            subprocess.run(['python3', 'scripts/series_linker.py'], cwd=base)
        except Exception as e:
            print(f"  ⚠️ シリーズリンク更新エラー: {e}")

        print(f"\n📝 concept説明文を更新中...")
        try:
            subprocess.run(['python3', 'scripts/concept_enricher.py', '--all'], cwd=base)
        except Exception as e:
            print(f"  ⚠️ concept更新エラー: {e}")

        print(f"\n🎙 トランスクリプトを取得中...")
        try:
            subprocess.run(['python3', '-u', 'scripts/transcript_fetcher.py', '--all'], cwd=base)
        except Exception as e:
            print(f"  ⚠️ トランスクリプト取得エラー: {e}")

    # ビルド＆git push（常に実行）
    print(f"\n🔨 ビルド中...")
    try:
        import subprocess
        base = os.path.dirname(os.path.dirname(__file__))
        subprocess.run(['npx', 'quartz', 'build'], cwd=base)
        subprocess.run(['git', 'add', '.'], cwd=base)
        msg = f'update: {total_new}件の新エピソードを追加' if total_new > 0 else 'update: コンテンツ更新'
        subprocess.run(['git', 'commit', '-m', msg], cwd=base)
        subprocess.run(['git', 'push'], cwd=base)
        print(f"  ✅ push完了")
    except Exception as e:
        print(f"  ⚠️ pushエラー: {e}")

    print(f"\n🌿 完了！ 新規処理: {total_new}件")

if __name__ == '__main__':
    main()
