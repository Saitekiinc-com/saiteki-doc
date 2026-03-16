# saiteki-doc

> **AI活用ナレッジ駆動型 開発支援システム**
>
> Notionのナレッジをグラフ化し、GitHub Issueが作成されたときに「この作業はAIに任せられるか」を自動でアドバイスします。

---

## このリポジトリの目的

開発プロジェクトで発生するタスクに対して、**社内ナレッジグラフをもとにAIが自動でアドバイスを投稿**します。

```
Notionのページ（ナレッジ）
    ↓ notion_to_neo4j.py で変換
Neo4jナレッジグラフ
    ↓ GitHub Issueが作成されると
GitHub Actions が起動
    ↓ issueタイトル・本文のキーワードでグラフ検索
HumanTask / AIGuidance ノードを取得
    ↓ Gemini APIで自然言語コメントを生成
GitHub Issue にコメントを自動投稿
```

---

## 現在のナレッジベース

| Notionページ | フェーズ | 概要 |
|---|---|---|
| テスト観点抽出（汎用） | テスト | ドメイン固有の観点を体系化・再利用可能にする |
| テスト設計書作成 | テスト | 要件からテストケースを設計するフロー |
| テスト戦略 | テスト | 品質リスクに対する方針を明確にするフロー |

### 今後追加予定のフェーズ

- 要件定義
- システム設計・基本設計
- 実装・コードレビュー
- リリース・デプロイ

---

## ナレッジグラフの構造

```
NotionPage
    └─[DEFINES]──▶ HumanTask（人の作業）
                        ├─ replaceable: full / partial / human_only
                        ├─[REPLACEABLE_BY]──▶ AIGuidance（AI指示テンプレート）
                        │                         └─[USES_ROLE]──▶ AIRole
                        ├─[PARTIALLY_BY]───▶ AIGuidance
                        ├─[TRIGGERED_BY]──▶ DomainKeyword（issueとのマッチングキー）
                        └─[APPLIES_WHEN]──▶ Condition（AI活用が有効な条件）
```

### AIに置き換えられる度合い

| 値 | 意味 |
|---|---|
| `full` | ほぼAIに任せられる |
| `partial` | AIが草案・候補生成、人が最終判断 |
| `human_only` | 人が必須（方針・戦略の意思決定など） |

---

## 使い方

### issueを作ってAIアドバイスをもらう

1. [新しいissueを作成](../../issues/new)
2. タイトルと本文にやりたいことを書く
3. 30〜60秒でAI活用ガイダンスのコメントが自動投稿される

**issueタイトルの例**

- 「決済機能のテスト観点を洗い出したい」
- 「新機能追加に伴うリスク分析をしたい」
- 「テスト設計書を作成したい」
- 「要件定義書からテスト戦略を立てたい」

---

## セットアップ

### 必要なシークレット

リポジトリの **Settings → Secrets and variables → Actions** に以下を登録します：

| シークレット名 | 説明 |
|---|---|
| `GEMINI_API_KEY` | Google Gemini APIキー |
| `NEO4J_PASSWORD` | Neo4j Auraのパスワード |

`GITHUB_TOKEN` はGitHub Actionsが自動で発行するため不要です。

### ナレッジを更新・追加する

1. Notionにページを追加・編集する
2. `scripts/notion_to_neo4j.py` の `PAGE_IDS` に追加するページのIDを記載する

```python
PAGE_IDS = [
    "2fedfb42-679c-809e-921e-e2847839d2c7",  # テスト観点抽出（汎用）
    "30bdfb42-679c-802e-a6ab-ff11edaa2af9",  # テスト戦略
    "30bdfb42-679c-80b6-99b4-f5bab3f42ad2",  # テスト設計書作成
    # ← ここに追加
]
```

3. スクリプトを実行する

```bash
python3 scripts/notion_to_neo4j.py
```

---

## ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── ai_guidance.yml       # issueトリガーワークフロー
├── scripts/
│   ├── generate_ai_guidance.py   # Neo4j + Gemini を使ったコメント生成
│   └── notion_to_neo4j.py        # NotionページをNeo4jグラフに変換
└── docs/                         # その他ドキュメント
```

---

## インフラ

| サービス | 用途 | プラン |
|---|---|---|
| Notion | ナレッジの記述・管理 | 既存プランを利用 |
| Neo4j Aura | ナレッジグラフのDB | Freeプラン |
| Google Gemini API | コメント文生成 | 従量課金（開発中は無料枠内） |
| GitHub Actions | 自動化パイプライン | 無料枠内 |
