# Mycelism — Claude向け完全コンテキストファイル

> このファイルはClaude（AI）が新しいセッションでプロジェクトを即座に把握するために書かれている。
> 人間向けのドキュメントではない。Claudeはこのファイルを読んだ上で、続きの作業に入ること。

---

## 0. このプロジェクトで最初に知るべきこと

**Andyはコードが書けない。ディレクター役として指示を出す人間だ。**

つまりClaudeがエンジニアとして全ての実装を担当する。Andy自身はターミナルでコマンドを打つことはできるが、コードを読んで理解・修正することは基本的にできない。

**このプロジェクトの本質:**
ポッドキャストのエピソードをRSSから自動取得し、Claude APIで処理して、Quartzというサイトジェネレーターで公開するデジタルガーデン。知識がノードとして繋がるObsidianライクな構造。

**プロジェクト名:** Mycelism（菌糸＝知識が地下でつながるイメージ）

---

## 1. オーナー情報

| 項目 | 内容 |
|---|---|
| 名前 | Andy（@andyutaro） |
| 拠点 | 北海道白老町 |
| 職業 | ポッドキャスター・ポッドキャストディレクター |
| 技術レベル | コードは書けない。ターミナル操作は可能 |
| マシン | MacBook Air M4 / macOS Tahoe 26.3.1（ベータ） |
| GitHub | github.com/andyutaro |
| コミュニケーション | 日本語。「治した」「直らない」「完璧」「ナイス」などカジュアルな表現が多い |

**Andyとのやりとりで重要なこと:**
- 長い説明より「このコマンドを打って」の方が好まれる
- エラーが出たらターミナルの出力をそのまま貼り付けてくれる
- 「変化なし」「治らない」は問題が解決していないサインで、粘り強く原因を追う必要がある
- スクリーンショットをよく添付してくれる。UI上の問題はスクリーンショットで判断すること

---

## 2. リポジトリ・環境情報

```
ローカルパス:    ~/quartz/
GitHub:         github.com/andyutaro/mycelism
公開URL:        （GitHub Pages、未設定）
ブランチ:       main
```

### 環境

| ツール | バージョン | 備考 |
|---|---|---|
| Quartz | 4.5.2 | サイトジェネレーター |
| Node.js | （Quartz同梱） | |
| Python | 3.11.15 | venv: ~/quartz/venv/ |
| Git | 2.53.0 | SSH接続設定済み |
| Homebrew | 5.1.3 | |

### Python仮想環境

```bash
cd ~/quartz
source venv/bin/activate    # 有効化
deactivate                  # 無効化
```

### APIキー

```
~/quartz/.env に ANTHROPIC_API_KEY=xxx の形式で保存
gitignore済み。絶対にコミットしない
```

### よく使うコマンド

```bash
# 新着エピソード処理（zshrcエイリアス）
デジタルガーデン更新

# ローカルプレビュー
cd ~/quartz && npx quartz build --serve
# → http://localhost:8080

# フルリビルド（キャッシュ問題が起きたとき）
cd ~/quartz && rm -rf public/ && npx quartz build --serve

# さらに強力なリビルド（SCSSキャッシュも含む）
cd ~/quartz && rm -rf public/ node_modules/.cache .quartz-cache && npx quartz build --serve

# GitHubにプッシュ
cd ~/quartz && git add . && git commit -m "update" && git push
```

---

## 3. ファイル構造（完全版）

```
~/quartz/
├── content/                        ← Obsidian Vault（サイトのコンテンツ）
│   ├── concepts/                   ← AI自動生成のキーワードノード（1066個）
│   ├── episodes/                   ← エピソードページ（237件）
│   │   ├── captions/               ← 1件
│   │   ├── mimoriradio/            ← 117件
│   │   ├── on-airdo/               ← 68件
│   │   └── sakanakaigi/            ← 51件
│   ├── notes/
│   │   ├── article/                ← 手書き記事（空）
│   │   ├── diary/                  ← 日記（4件）
│   │   └── memo/                   ← メモ（20件）
│   └── index.md                    ← トップページ
│
├── scripts/                        ← パイプライン処理スクリプト
│   ├── run.py                      ← メインスクリプト（全処理を統合）
│   ├── fetcher.py                  ← RSS取得・差分検知
│   ├── ai_processor.py             ← Claude API処理
│   └── md_writer.py                ← Markdown生成
│
├── quartz/                         ← Quartzフレームワーク本体（基本触らない）
│   ├── components/scripts/
│   │   └── explorer.inline.ts      ← 修正済み（mobile-no-scroll問題）
│   ├── plugins/emitters/
│   │   └── contentIndex.tsx        ← 修正済み（delete content.date をコメントアウト）
│   └── styles/
│       ├── base.scss               ← Quartzのベーススタイル（基本触らない）
│       ├── custom.scss             ← カスタムCSS（修正済み・グリッド強制適用）
│       └── variables.scss          ← ブレークポイント（desktop: 1000pxに変更済み）
│
├── config.yaml                     ← 番組設定・max_keywords等
├── processed.json                  ← 差分管理（処理済みエピソードのID一覧）
├── .env                            ← ANTHROPIC_API_KEY（gitignore済み）
├── quartz.config.ts                ← Quartzサイト設定
├── quartz.layout.ts                ← レイアウト・Explorerのsort/filter設定
├── package.json                    ← Node.js依存関係
└── venv/                           ← Python仮想環境
```

---

## 4. 番組リスト

| config名 | 番組名 | show_id（Spotify） | ステータス |
|---|---|---|---|
| captions | Captions | 34phiuFlCBcfscYLP5iCyb | active |
| on-airdo | ON-AIRDO | 1EjsDlGdwwEDc1xsNxpEAP | active |
| sakanakaigi | サカナカイギ | 2oyDL4w0U7hRmwIFRC7jDK | active |
| mimoriradio | ミモリラジオ | 0rkdfNkYUCfMyQmki7fdc1 | archived |

### RSSフィード

```
captions:    https://anchor.fm/s/f20aee28/podcast/rss
on-airdo:    https://anchor.fm/s/fe6f8048/podcast/rss
sakanakaigi: https://anchor.fm/s/1039cb824/podcast/rss
mimoriradio: https://anchor.fm/s/ccd5236c/podcast/rss
```

---

## 5. パイプライン処理の詳細

### 全体フロー

```
「デジタルガーデン更新」コマンド
  └→ run.py 実行
        └→ fetcher.py
              └→ RSSフィード取得（4番組）
              └→ processed.json と照合して新着エピソードのみ抽出
        └→ ai_processor.py（Claude API: claude-sonnet-4-20250514）
              └→ 要約生成
              └→ キャプション（SNS投稿用短文）生成
              └→ キーワード（concepts）生成 ← 人物名は除外
              └→ parent_concept（メインキーワード）決定
        └→ md_writer.py
              └→ content/episodes/{show}/YYYY-MM-DD-{title}.md 生成
              └→ content/concepts/{keyword}.md 生成（なければ新規作成）
              └→ processed.json 更新
```

### エピソードMarkdownの形式

```markdown
---
title: "#10 タイトル"
date: 2025-02-20
show: on-airdo
audio_url: "https://..."
spotify_url: "https://..."
---

# タイトル

キャプション文章

[Spotifyで聴く](URL)

<audio controls src="..."></audio>

## 要約

要約テキスト

## キーワード

[[concepts/キーワード1]] [[concepts/キーワード2]] ...

## 文字起こし

（取得予定）
```

### conceptsMarkdownの形式

```markdown
---
title: "キーワード名"
tags: ["concept"]
---

# キーワード名

（説明文は今後のエピソードから自動生成されます）

## 参照元

- [[episodes/.../エピソード名]] (YYYY-MM-DD)
```

### 重要な実装注意事項

**YAMLの引用符問題:**
タイトルに `"` が含まれるとYAMLパースエラーになる。
`md_writer.py` でタイトル内の `"` を `'` に自動変換している。
既存ファイルは一括修正済み（15ファイル）。

**processed.jsonの管理:**
差分検知に使用。エピソードのGUID（Spotify episode ID）で管理。
このファイルを削除すると全エピソードが再処理される（意図的にリセットしたい場合のみ）。

---

## 6. Quartzの設定（現在の状態）

### quartz.config.ts の重要設定

```typescript
configuration: {
  pageTitle: "Mycelism",
  enableSPA: true,
  enablePopovers: true,
  locale: "en-US",
  baseUrl: "quartz.jzhao.xyz",  // デプロイ時に変更が必要
  defaultDateType: "modified",   // "frontmatter"は存在しない（エラーになる）
}
```

### quartz.layout.ts の現在の設定（完全版）

```typescript
const explorerOptions = {
  folderClickBehavior: "collapse" as const,
  folderDefaultState: "collapsed" as const,
  useSavedState: true,
  filterFn: (node: any) => {
    // conceptsフォルダをサイドバーから除外（1066個が展開されてUIが壊れるため）
    return node.name !== "concepts"
  },
  sortFn: (a: any, b: any) => {
    if (!a.isFolder && b.isFolder) return 1
    if (a.isFolder && !b.isFolder) return -1
    if (a.isFolder && b.isFolder) {
      return a.displayName.localeCompare(b.displayName, undefined, {
        numeric: true,
        sensitivity: "base",
      })
    }
    // ファイル同士はdateで降順（新しい順）
    const aDate = a.data?.date ? new Date(a.data.date) : new Date(0)
    const bDate = b.data?.date ? new Date(b.data.date) : new Date(0)
    return bDate.getTime() - aDate.getTime()
  },
  mapFn: (node: any) => { return node },
}
```

**重要:** `sortFn` で使うべきプロパティは `a.isFolder` / `b.isFolder`。
`a.file` は存在しない（FileTrieNodeの仕様）。これを間違えると何度やっても直らない。

### custom.scss の内容（グリッドレイアウト強制適用）

```scss
html {
  overflow-x: auto !important;
}

html.mobile-no-scroll {
  overflow: auto !important;
}

.page > #quartz-body {
  display: grid !important;
  grid-template-columns: 320px auto 320px !important;
  grid-template-areas:
    "grid-sidebar-left grid-header grid-sidebar-right"
    "grid-sidebar-left grid-center grid-sidebar-right"
    "grid-sidebar-left grid-footer grid-sidebar-right" !important;
}

@media (max-width: 800px) {
  .page > #quartz-body {
    grid-template-columns: auto !important;
    grid-template-areas:
      "grid-sidebar-left"
      "grid-header"
      "grid-center"
      "grid-sidebar-right"
      "grid-footer" !important;
  }
}
```

---

## 7. Quartz固有の罠（解決済みの問題と解決法）

これを知らずに作業すると同じ問題で何時間もハマる。必ず読むこと。

### 罠1: mobile-no-scroll問題（最大の罠）★★★

**症状:** デスクトップのフルスクリーンでも2カラム表示になり、Explorerが展開されると本文が下に押し下げられる。

**根本原因:**
`quartz/components/scripts/explorer.inline.ts` の `window.addEventListener("resize")` で、Explorerが開いている状態でリサイズイベントが発生すると **画面幅に関係なく** `html` タグに `mobile-no-scroll` クラスを付与してしまう。

**解決法:**
`custom.scss` で `.page > #quartz-body` のグリッドを `!important` で上書き（上記参照）。

**なぜ `variables.scss` の変更では効かないのか:**
ビルドされたCSSに `grid-template-columns` が出力されないことがある。`custom.scss` での直接指定が唯一の確実な方法。

### 罠2: ExplorerのsortFnで使えるプロパティ ★★★

**正しい型定義:**
```typescript
class FileTrieNode {
  isFolder: boolean      // ← これを使う
  children: Array<FileTrieNode>
  data: ContentDetails | null  // { slug, title, links, tags, content, date? }
}
```

**よくある間違い:** `a.file`、`a.file?.name`、`a.file?.frontmatter` → 全て存在しない

### 罠3: contentIndex.jsonからdateが削除される ★★

**原因:**
`quartz/plugins/emitters/contentIndex.tsx` の147行目に `delete content.date` があり、JSON出力前にdateが削除される。

**解決法（実施済み）:**
```typescript
// delete content.date  ← コメントアウト済み
```
Quartzを `git pull` で更新した場合、この変更が上書きされる可能性があるため注意。

### 罠4: YAMLパースエラー ★★

**症状:** ビルド時に `bad indentation of a mapping entry` エラー。

**原因:** エピソードタイトルに `"` が含まれているとYAMLが壊れる。

**解決法:** `md_writer.py` でタイトル内の `"` を `'` に変換（実装済み）。

### 罠5: defaultDateTypeに "frontmatter" は存在しない ★

**有効な値:** `"modified"` または `"created"` のみ。`"frontmatter"` を指定するとビルドエラー。

### 罠6: Explorerでconceptsが1066個展開される ★★

**解決法:** filterFnで除外する。
```typescript
filterFn: (node: any) => node.name !== "concepts"
```

### 罠7: numeric sortで #10が#2の前に来る ★★

**解決法:**
```typescript
a.displayName.localeCompare(b.displayName, undefined, {
  numeric: true,      // ← これが必要
  sensitivity: "base"
})
```

### 罠8: ビルドキャッシュが残る ★

```bash
# 段階的に試す
rm -rf ~/quartz/public/
rm -rf ~/quartz/public/ ~/quartz/node_modules/.cache ~/.quartz-cache
# ブラウザ: Command+Shift+R（ハードリロード）
```

---

## 8. 残フェーズ（未実装）

| Phase | 内容 | 優先度 | 備考 |
|---|---|---|---|
| Phase 4 | Spotifyトランスクリプト取得 | 高 | Spotify APIから字幕取得。scripts/transcript_fetcher.py を新規作成 |
| Phase 5 | conceptページの説明文AI充実化 | 中 | 参照元エピソードを元にAIが説明文生成。--enrich-concepts オプション追加予定 |
| Phase 6 | トップページのグラフビュー全体表示 | 中 | index.mdをグラフ全画面表示にカスタマイズ |
| Phase 7 | GitHub Actions自動デプロイ | 高 | 毎週土曜 10:00 JST。cron: '0 1 * * 6' |

---

## 9. 設計思想・重要な判断記録

### conceptsの役割

エピソードから抽出されたキーワードがノードになる。グラフビューで見ると、番組をまたいで共通するテーマが可視化される。

### 人物名をconceptsから除外する理由

人物名がconceptノードになると無数に増えてグラフが汚くなる。`ai_processor.py` のプロンプトで除外指示済み。

### captionsのみkeyword除外リストがある理由

captionsはAndyの個人番組で近況報告が多い。一時的な出来事がキーワードになるのを防ぐため。

---

## 10. Claudeへの引き継ぎ事項

### 作業するときの原則

1. **コマンドは完全な形で提示する** - Andyはコードを読まないので、コピペで動くコマンドを出す
2. **ファイル修正はpython3スクリプトで行う** - sedよりpython3の方が確実（日本語・特殊文字に強い）
3. **ビルドして確認する** - 変更後は必ず `npx quartz build --serve` で動作確認を促す
4. **スクリーンショットを求める** - UIの問題はAndyにスクリーンショットを貼ってもらう
5. **「変化なし」が来たら根本から疑う** - キャッシュ、ファイルパス、プロパティ名を全て確認し直す

### よく使うデバッグコマンド

```bash
# ビルドされたCSSに変更が反映されているか確認
grep "確認したいキーワード" ~/quartz/public/index.css

# sortFnがどう埋め込まれているか確認
grep -o "sortFn.*filterFn" ~/quartz/public/index.html | python3 -c "import sys,html; print(html.unescape(sys.stdin.read()))"

# contentIndex.jsonの内容確認
cat ~/quartz/public/static/contentIndex.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
ep = {k:v for k,v in d.items() if k.startswith('episodes/on-airdo')}
print(json.dumps(dict(list(ep.items())[:2]), ensure_ascii=False, indent=2))
"

# mobile-no-scrollクラスが付いているか確認（開発者ツールConsoleで）
# document.documentElement.classList.contains('mobile-no-scroll')
```

---

## 11. 現在の動作確認済み状態（2026-04-05時点）

- [x] `デジタルガーデン更新` コマンドで新着エピソードを自動処理
- [x] 237エピソード・1066 concept が生成済み
- [x] `npx quartz build --serve` でlocalhost:8080に表示
- [x] 3カラムレイアウト（左サイドバー・中央・右サイドバー）が正常表示
- [x] サイドバーにconcepts非表示、episodes/notesのみ表示
- [x] エピソードが日付降順でソート（新しいものが上）
- [x] サイトタイトル「Mycelism」
- [x] GitHub（github.com/andyutaro/mycelism）にpush済み
- [ ] GitHub Pages公開（未設定）
- [ ] Phase 4〜7（未実装）
