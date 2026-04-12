import os, json, glob, re

VAULT_PATH = '/Users/andy/quartz/content'
SERIES_FILE = '/Users/andy/quartz/series_groups.json'

def get_episode_keywords(show_name, episode_title):
    files = glob.glob(f'{VAULT_PATH}/episodes/{show_name}/*.md')
    for f in files:
        basename = os.path.basename(f).replace('.md', '')
        ep_title = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', basename)
        if episode_title in ep_title or ep_title in episode_title:
            with open(f, 'r', encoding='utf-8') as fp:
                content = fp.read()
            m = re.search(r'## キーワード\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
            if m:
                return re.findall(r'\[\[(.+?)\]\]', m.group(1))
    return []

def ensure_concept_exists(concept_name):
    filepath = f'{VAULT_PATH}/concepts/{concept_name}.md'
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'---\ntags:\n  - concept\n---\n\n## {concept_name}\n\n## 関連\n\n## 参照元\n')
        print(f"  📄 新規作成: {concept_name}")
    return filepath

def add_parent_link(concept_path, parent_name):
    with open(concept_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    parent_link = f'[[{parent_name}]]'
    if parent_link in content:
        return False

    if '## 関連' in content:
        content = content.replace('## 関連\n', f'## 関連\n\n{parent_link}\n')
    else:
        # YAMLの直後に関連セクションを挿入
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            content = parts[0] + '---\n' + parts[1] + '---\n\n## 関連\n\n' + parent_link + '\n\n' + parts[2]
        else:
            content = content + f'\n## 関連\n\n{parent_link}\n'

    with open(concept_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

def main():
    with open(SERIES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_links = 0

    for group in data['groups']:
        show = group['show']
        parent = group['parent']
        titles = group['titles']

        print(f"\n【{show}】{parent} ({len(titles)}件)")

        ensure_concept_exists(parent)

        all_keywords = set()
        for title in titles:
            keywords = get_episode_keywords(show, title)
            all_keywords.update(keywords)

        all_keywords.discard(parent)

        linked = 0
        for keyword in all_keywords:
            concept_path = f'{VAULT_PATH}/concepts/{keyword}.md'
            if os.path.exists(concept_path):
                if add_parent_link(concept_path, parent):
                    linked += 1

        total_links += linked
        print(f"  → {len(all_keywords)}個のconcept中 {linked}個にリンク追加")

    print(f"\n🌿 完了: 合計{total_links}件のリンクを追加")

if __name__ == '__main__':
    main()
