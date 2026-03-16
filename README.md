# saiteki-doc

エンジニアが「この作業はAIに任せられる」と定義した仮説をナレッジに蓄積し、タスク作成時にAIがそのナレッジをもとにコメントします。取りこぼしなくAI活用できているかを、タスクのレビューのような形でチームに届けます。

フィードバックをナレッジに追加していくことで、AIに任せられる作業の確度とフローが継続的に磨かれていくことを狙っています。

---

## システムフロー

```mermaid
sequenceDiagram
    actor Engineer as エンジニア
    participant Notion
    participant GHPages as GitHub Pages<br/>（Markdown）
    participant Neo4j as Neo4j<br/>（ナレッジグラフ）
    participant Issue as GitHub Issue
    participant Actions as GitHub Actions
    participant Gemini as Gemini API

    %% ナレッジ構築フェーズ
    rect rgb(230, 240, 255)
        Note over Engineer,Neo4j: ナレッジ構築フェーズ
        Engineer->>Notion: AI活用の仮説を記述<br/>（人の作業 / AIの作業）
        Notion->>GHPages: Markdownとして公開
        GHPages->>Neo4j: notion_to_neo4j.py で<br/>ナレッジグラフ化
    end

    %% タスクレビューフェーズ
    rect rgb(230, 255, 235)
        Note over Engineer,Gemini: タスクレビューフェーズ
        Engineer->>Issue: issueを作成<br/>（タスクの概要を記述）
        Issue->>Actions: issues.opened イベントで起動
        Actions->>Neo4j: issueのキーワードで<br/>HumanTask / AIGuidanceを検索
        Neo4j-->>Actions: 関連ナレッジを返す
        Actions->>Gemini: ナレッジ + issueを渡して<br/>コメント文を生成
        Gemini-->>Actions: AI活用ガイダンスを返す
        Actions->>Issue: コメントを自動投稿<br/>（AIに任せられる作業・人が判断する作業）
        Engineer->>Issue: コメントを確認してタスクを進める
    end

    %% フィードバックフェーズ
    rect rgb(255, 245, 220)
        Note over Engineer,Neo4j: フィードバックフェーズ
        Engineer->>Notion: 実際のタスクを通じた気づきを追記<br/>（仮説の検証・修正）
        Notion->>GHPages: Markdownを更新
        GHPages->>Neo4j: ナレッジグラフを再生成<br/>（確度・フローが磨かれる）
    end
```

---

## 現在のナレッジベース

| フェーズ | ナレッジページ |
|---|---|
| テスト | テスト観点抽出・テスト設計書作成・テスト戦略 |
| 追加予定 | 要件定義・設計・実装 |

---

## 使い方

### issueを作成してAIレビューをもらう

[新しいissueを作成する](../../issues/new) だけで、30〜60秒後にAI活用ガイダンスのコメントが自動で届きます。

### ナレッジを追加・更新する

1. Notionにページを追加・編集する
2. GitHub Pagesに公開されたMarkdownを確認する
3. `scripts/notion_to_neo4j.py` の `PAGE_IDS` に追加するページIDを記載してスクリプトを実行する

```bash
export NOTION_TOKEN="your-notion-token"
export NEO4J_PASSWORD="your-neo4j-password"
python3 scripts/notion_to_neo4j.py
```

---

## GitHub Secrets の設定

リポジトリの **Settings → Secrets and variables → Actions** に以下を登録してください。

| シークレット名 | 内容 |
|---|---|
| `GEMINI_API_KEY` | Google Gemini APIキー |
| `NEO4J_PASSWORD` | Neo4j Auraのパスワード |

---

## ファイル構成

```
.github/workflows/ai_guidance.yml    # issueトリガーワークフロー
scripts/generate_ai_guidance.py      # コメント生成スクリプト
scripts/notion_to_neo4j.py           # ナレッジグラフ生成スクリプト
```
