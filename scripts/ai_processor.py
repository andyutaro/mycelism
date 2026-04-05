import os
import anthropic
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

def process_episode(episode, show):
    title = episode['title']
    description = episode['description']
    max_keywords = show.get('max_keywords', 6)
    extraction_notes = show.get('extraction_notes', '')

    prompt = f"""以下はポッドキャストのエピソード情報です。

タイトル: {title}
説明文: {description}

以下の4つを生成してください。必ずJSON形式で返してください。

1. summary: エピソード内容の要約（200字以内）
2. caption: エピソードの紹介文（1〜2文、SNSで使えるような魅力的な文章）
3. keywords: このエピソードの重要キーワードリスト（最大{max_keywords}個）
   - 条件: トピック・概念・テーマ・固有名詞（場所・作品・組織）のみ
   - 除外: 人物名・話者名・ゲスト名はすべて除外
   {f'- 追加指示: {extraction_notes}' if extraction_notes else ''}
4. parent_concept: タイトルに「〇〇編」「〇〇シリーズ」が含まれる場合その大テーマ名（なければnull）

返答はJSON形式のみ。説明文は不要。
例:
{{
  "summary": "...",
  "caption": "...",
  "keywords": ["キーワード1", "キーワード2"],
  "parent_concept": "ネコ" or null
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    text = message.content[0].text
    text = text.replace('```json', '').replace('```', '').strip()
    return json.loads(text)

if __name__ == '__main__':
    test_episode = {
        'title': '#7 世界に広がる「ネコ」の進化とサクセスストーリー〜イエネコ編その1【ミモリラジオ】',
        'description': '【ネコ編・その1】森にもいる。どこにでもいる。/ たまにキツネは痩せていてもネコは丸々 / ネコの学名はイエネコ (Felis catus) / 「侵略的外来種ワースト100」に登録されているネコ',
    }
    test_show = {
        'name': 'mimoriradio',
        'max_keywords': 6,
    }

    print("処理中...")
    result = process_episode(test_episode, test_show)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
