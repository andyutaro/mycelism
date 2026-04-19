import os, re, glob, json, yaml
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

VAULT_PATH = '/Users/andy/quartz/content'
PROCESSED_FILE = '/Users/andy/quartz/processed_concepts.json'

SHOW_NAMES = {
    'sakanakaigi': 'サカナカイギ',
    'mimoriradio': 'ミモリラジオ',
    'longpost': 'ロングポスト',
}

def load_processed():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_processed(data):
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_transcript(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'## 文字起こし\n\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
    if m:
        text = m.group(1).strip()
        if text and text != '（取得予定）':
            return text[:6000]  # 長すぎる場合は切る
    return None

def get_episode_refs(concept_content):
    """conceptページの参照元エピソードを取得"""
    refs = re.findall(r'\[\[episodes/(\w+)/([^\|]+?)(?:\|[^\]]+)?\]\]', concept_content)
    return refs  # [(show_name, filename), ...]

def get_episode_md_path(show_name, filename):
    pattern = f"{VAULT_PATH}/episodes/{show_name}/{filename}.md"
    if os.path.exists(pattern):
        return pattern
    # ファイル名が少し違う場合も探す
    files = glob.glob(f"{VAULT_PATH}/episodes/{show_name}/*.md")
    for f in files:
        if filename[:30] in os.path.basename(f):
            return f
    return None

def get_episode_info(md_path):
    """エピソードのタイトルとトランスクリプトを取得"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    title_m = re.search(r'^title:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
    title = title_m.group(1) if title_m else os.path.basename(md_path)
    transcript = get_transcript(md_path)
    return title, transcript

def generate_concept_description(concept_name, episodes_by_show):
    """GPT-4oでconceptの説明文を生成"""
    
    # 番組ごとに最大2エピソードまでに制限
    total_eps = sum(len(v) for v in episodes_by_show.values())
    limited_episodes_by_show = {}
    for show_name, episodes in episodes_by_show.items():
        limited_episodes_by_show[show_name] = episodes[:2]
    extra_count = max(0, total_eps - sum(len(v) for v in limited_episodes_by_show.values()))
    episodes_by_show = limited_episodes_by_show

    # 番組ごとのセクションを構築
    show_sections = []
    for show_name, episodes in episodes_by_show.items():
        show_display = SHOW_NAMES.get(show_name, show_name)
        ep_texts = []
        for title, transcript in episodes:
            if transcript:
                ep_texts.append(f"【{title}】\n{transcript[:3000]}")
            else:
                ep_texts.append(f"【{title}】\n(トランスクリプトなし)")
        show_sections.append(f"=== {show_display} ===\n" + "\n\n".join(ep_texts))
    
    all_content = "\n\n".join(show_sections)
    
    prompt = f"""以下は「{concept_name}」というキーワードが登場するポッドキャストエピソードの文字起こしです。

{all_content}

これらのエピソードを元に、以下の形式でMarkdownを生成してください：

1. ## {concept_name} の直下に、全エピソードを踏まえた概要（3〜5文）
2. 番組ごとに ### [番組名]での扱い というセクションを作り、各エピソードでこのキーワードがどのように語られたかを詳しく記述（エピソードごとに段落を分ける）

注意：
- 話者名は不要
- 具体的な内容・文脈を重視
- 長文OK、読み応えのある文章に
- Markdownのセクション見出しのみ使用（## と ### のみ）
- 「参照元」セクションは含めない

返答はMarkdown形式のみ。前置きや説明文は不要。コードブロック（```）は使わない。"""

    extra_note = f"\n\nその他{extra_count}件のエピソードでも言及されている。" if extra_count > 0 else ""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip() + extra_note

def update_concept_file(filepath, concept_name, new_description):
    """conceptファイルの説明文セクションを更新"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 参照元セクションを保持
    refs_m = re.search(r'(## 参照元.+)', content, re.DOTALL)
    refs_section = refs_m.group(1) if refs_m else ''
    
    # YAMLフロントマターを保持
    yaml_m = re.search(r'^(---\n.+?\n---\n)', content, re.DOTALL)
    yaml_section = yaml_m.group(1) if yaml_m else '---\ntags:\n  - concept\n---\n'
    
    new_content = f"{yaml_section}\n{new_description}\n\n{refs_section}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

def process_concept(filepath, processed):
    concept_name = os.path.basename(filepath).replace('.md', '')
    
    if processed.get(concept_name) == 'done':
        return 'skip'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    refs = get_episode_refs(content)
    if not refs:
        processed[concept_name] = 'no_refs'
        return 'skip'
    
    # 番組ごとにグループ化
    episodes_by_show = {}
    for show_name, filename in refs:
        md_path = get_episode_md_path(show_name, filename)
        if not md_path:
            continue
        title, transcript = get_episode_info(md_path)
        if show_name not in episodes_by_show:
            episodes_by_show[show_name] = []
        episodes_by_show[show_name].append((title, transcript))
    
    if not episodes_by_show:
        processed[concept_name] = 'no_episodes'
        return 'skip'
    
    description = generate_concept_description(concept_name, episodes_by_show)
    update_concept_file(filepath, concept_name, description)
    processed[concept_name] = 'done'
    return 'done'

if __name__ == '__main__':
    import sys
    processed = load_processed()
    test_mode = '--all' not in sys.argv
    
    concept_files = sorted(glob.glob(f'{VAULT_PATH}/concepts/*.md'))
    
    if test_mode:
        print("🧪 テストモード（クジラのみ）")
        target = f'{VAULT_PATH}/concepts/クジラ.md'
        if os.path.exists(target):
            result = process_concept(target, processed)
            save_processed(processed)
            if result == 'done':
                with open(target, 'r') as f:
                    print(f.read()[:1000])
        else:
            print("クジラ.mdが見つかりません")
    else:
        print(f"🌿 全concept処理開始: {len(concept_files)}件")
        done = skip = error = 0
        for i, filepath in enumerate(concept_files):
            concept_name = os.path.basename(filepath).replace('.md', '')
            try:
                result = process_concept(filepath, processed)
                if result == 'done':
                    print(f"  ✅ [{i+1}/{len(concept_files)}] {concept_name}")
                    done += 1
                else:
                    skip += 1
                save_processed(processed)
            except Exception as e:
                print(f"  ❌ [{i+1}/{len(concept_files)}] {concept_name}: {e}")
                error += 1
        print(f"\n🌿 完了: {done}件 / スキップ: {skip}件 / エラー: {error}件")
