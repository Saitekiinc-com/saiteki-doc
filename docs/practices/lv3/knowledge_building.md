# ナレッジ構築フロー

## 【背景】なぜこのフローが必要なのか

エンジニアが「この作業はAIに任せられる」と感じている仮説は、多くの場合メンバーの頭の中にとどまり、チームで共有・活用されていません。
このフローでは、その仮説をNotionに記述し、GitHub Pages（Markdown）とNeo4j（ナレッジグラフ）へと変換・蓄積することで、AIが参照できる状態のナレッジベースを構築します。

### AI活用による課題解決のアプローチ

本カリキュラムでは、**「人の仮説記述 × 自動変換パイプライン」** によって、常に最新のナレッジグラフを維持します。

1.  **仮説の構造化**: Notionに「人がやること」「AIにやってほしいこと」を分けて記述することで、AIが理解しやすい構造でナレッジを蓄積する。
2.  **公開と透明性**: MarkdownとしてGitHub Pagesに公開することで、チームメンバーが随時参照・更新できる状態にする。
3.  **グラフ化による検索性**: Neo4jのナレッジグラフに変換することで、どのタスクにどのAI活用が有効かを高速に検索できるようにする。

## フローの概要

Notionで記述したAI活用の仮説を、GitHub PagesとNeo4jナレッジグラフへ自動変換するフローです。

| 人のInput | 自動変換Output |
| :--- | :--- |
| **Notionページ**<br>人の作業 / AIにやってほしいことを記述 | **Markdown（GitHub Pages）**<br>Neo4jナレッジグラフ（HumanTask / AIGuidance） |

### 協働フロー

1. 👤 **エンジニア (Human)** — **AI活用の仮説をNotionに記述**
    *   作業の中で「これはAIに任せられそう」と感じた箇所をNotionページに記述します。
    *   構成は **「人がやること」** と **「AIにやってほしいこと」** に分けて整理します。
    *   対象フェーズ（テスト・要件定義・設計・実装など）のページに追記していきます。

2. 🤖 **自動パイプライン** — **Markdown化（GitHub Pages公開）**
    *   `notion_to_markdown.py` を実行すると、NotionページがMarkdownに変換されます。
    *   `docs/practices/lv{n}/` 配下に保存され、git pushするとGitHub Pagesに自動反映されます。
    *   チームメンバーはブラウザからナレッジを確認・活用できます。

3. 🤖 **自動パイプライン** — **Neo4jナレッジグラフ化**
    *   `notion_to_neo4j.py` を実行すると、Markdownを読み込んでNeo4jにグラフを構築します。
    *   `HumanTask`・`AIGuidance`・`DomainKeyword` のノードとリレーションが作成されます。
    *   このグラフが、タスクレビューフェーズでのAIコメント生成の知識ベースになります。

```bash
# ナレッジを更新する手順
export NOTION_TOKEN="your-notion-token"
export NEO4J_PASSWORD="your-neo4j-password"

# Step 1: NotionからMarkdownを生成してpush
python3 scripts/notion_to_markdown.py
git add docs/practices/ && git commit -m "docs: ナレッジ更新" && git push

# Step 2: Neo4jナレッジグラフを再生成
python3 scripts/notion_to_neo4j.py
```
