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

    base = os.path.dirname(os.path.dirname(__file__))
    update_index_updates(base)
    print(f"\n🌿 完了！ 新規処理: {total_new}件")


def update_index_updates(base):
    """index.mdのUpdatesセクションを最新5件で更新"""
    import glob
    import re
    from datetime import datetime

    # episodesとnotesから最新ファイルを取得
    patterns = [
        os.path.join(base, 'content/episodes/**/*.md'),
        os.path.join(base, 'content/notes/**/*.md'),
    ]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern, recursive=True))

    # 更新日時でソート
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    latest = files[:5]

    # リスト生成
    lines = []
    for f in latest:
        rel = f.replace(os.path.join(base, 'content/'), '').replace('.md', '')
        name = os.path.basename(f).replace('.md', '')
        date = datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d')
        lines.append(f"- [[{rel}|{name}]] - {date}")

    updates_text = "## Updates\n" + "\n".join(lines) + "\n"

    # index.md を更新
    index_path = os.path.join(base, 'content/index.md')
    with open(index_path, 'r') as f:
        content = f.read()

    if '## Updates' in content:
        content = re.sub(r'## Updates.*?(?=\n## |\Z)', updates_text, content, flags=re.DOTALL)
    else:
        content = content.rstrip() + '\n\n' + updates_text

    with open(index_path, 'w') as f:
        f.write(content)
    print("📋 Updatesセクションを更新しました")

if __name__ == '__main__':
    main()
