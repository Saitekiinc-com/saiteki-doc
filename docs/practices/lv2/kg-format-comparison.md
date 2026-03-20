# ナレッジグラフ形式の比較：Neo4j vs JSON-LD

## このドキュメントについて

このシステムはNeo4j（グラフDB）にナレッジを格納し、issueが作成されるとGeminiがそのグラフを読み取ってAIコメントを生成します。

「Neo4jにグラフを入れる」「JSON-LDとしてテキストで渡す」の2つのアプローチで、AI生成の品質にどのような差が生まれるかを整理します。

---

## 全体像：2つのアプローチ

```
【アプローチA: 現在の構成 (Neo4j)】
Markdown → Neo4j（グラフDB） → Cypher検索 → Gemini → issueコメント

【アプローチB: JSON-LDでテキスト渡し】
Markdown → JSON-LD文字列 → プロンプトに埋め込み → Gemini → issueコメント
```

---

## 比較表

| 観点 | Neo4j（グラフDB） | JSON-LD（テキスト埋め込み） |
|---|---|---|
| **データの持ち方** | ノード・エッジとしてDB内で永続化 | JSON文字列としてプロンプト内に展開 |
| **関係性の表現** | エッジ（`DEFINES`, `REPLACEABLE_BY`等）で構造化 | `@type`, `@id`, プロパティのネストで表現 |
| **検索・フィルタ** | Cypherクエリで精密に絞り込み可能 | Gemini自身がJSONを読み解いて絞り込む |
| **スケールへの対応** | ナレッジが増えてもDBで管理。AIへの入力量は一定 | ナレッジが増えるとトークン数が増大 |
| **リアルタイム性** | 更新するとすぐ次のissueに反映 | テキスト生成・プロンプト更新が必要 |
| **メンテナンス** | Markdownを更新 → スクリプト実行でOK | JSON-LD生成スクリプトの追加管理が必要 |
| **AI生成への入力** | 構造化データから必要な列のみ抽出して渡す | 全構造をテキストとして渡す |
| **コスト** | Neo4j Auraのインフラコスト + API料金 | APIトークン数増加分のコストのみ |

---

## issueワークフローにおける具体的な違い

### 現在の構成（Neo4j）でのフロー

```
1. issue作成
       ↓
2. GitHub Actions起動
       ↓
3. Cypherクエリでナレッジグラフ全体を取得
   ※ 必要なノード・プロパティだけ抽出
       ↓
4. Gemini ①: issueと関連するページ名を特定（JSON返答）
       ↓
5. Gemini ②: 関連ページの詳細をもとにロードマップ生成
       ↓
6. issueにコメント投稿
```

**AIへ渡すデータの例（Neo4jから取得したもの）：**
```python
{
  "page_title": "テスト戦略の策定",
  "lv": 1,
  "ai_tasks": ["品質リスク抽出", "テスト戦略ドラフト生成"],
  "prompt_template": "以下の要件をもとに...",
  "output_example": "テスト戦略文書",
  "ai_role": "テストアーキテクト"
}
```
→ **Geminiは「どのページを選ぶか」だけを判断すればよい。関係性はDB側で担保済み。**

---

### JSON-LDで渡す場合のフロー

```
1. issue作成
       ↓
2. GitHub Actions起動
       ↓
3. JSON-LDファイル（またはMarkdown生成JSON）をプロンプトに展開
       ↓
4. Gemini ①: JSON-LD全体を読み解き、関連ノードを特定
       ↓
5. Gemini ②: 同じJSON-LDから詳細を再解釈してロードマップ生成
       ↓
6. issueにコメント投稿
```

**AIへ渡すデータの例（JSON-LD形式）：**
```json
{
  "@context": {
    "schema": "https://schema.org/",
    "saiteki": "https://saitekiinc-com.github.io/saiteki-doc/vocab#"
  },
  "@graph": [
    {
      "@id": "saiteki:practices/lv1/test_strategy",
      "@type": "saiteki:KnowledgePage",
      "schema:name": "テスト戦略の策定",
      "saiteki:level": 1,
      "saiteki:defines": {
        "@type": "saiteki:HumanTask",
        "schema:description": "品質リスクを優先的に潰すためのテスト方針・体制を策定するフロー",
        "saiteki:replaceableBy": {
          "@type": "saiteki:AIGuidance",
          "saiteki:aiTasks": ["品質リスク抽出", "テスト戦略ドラフト生成"],
          "saiteki:usesRole": { "schema:name": "テストアーキテクト" }
        }
      }
    }
  ]
}
```
→ **Geminiが関係性の解釈・ノード選択・詳細抽出をすべて一度に行う必要がある。**

---

## AI生成品質への影響

### 精度の観点

| 観点 | Neo4j | JSON-LD |
|---|---|---|
| **関連ページの特定精度** | 高い（DB側で構造化済み。Geminiは選択だけ） | ページ数が増えると読み落としリスクあり |
| **ロードマップの一貫性** | 高い（必要データだけ渡すため余計な情報がない） | JSON-LD全体の解釈ぶれが出やすい |
| **プロンプトの簡潔さ** | 短い（構造化済みのPythondictを渡すだけ） | 長くなる（JSON全体 + 解釈指示が必要） |

### スケールの観点

- ナレッジが **10ページ → 100ページ** になったとき：
  - **Neo4j**: Cypherが必要なページだけ返す。AIへの入力量は変わらない
  - **JSON-LD**: テキストが10倍に膨らむ。トークン数・コスト・精度がすべて影響を受ける

### 更新コストの観点

- **Neo4j**: Markdownを更新して `notion_to_neo4j.py` を実行するだけ
- **JSON-LD**: JSON-LDの生成・検証・プロンプトへの組み込みを別途管理する必要がある

---

## どちらを選ぶべきか

| 条件 | 推奨 |
|---|---|
| ナレッジ件数が増える（30件以上）| **Neo4j** |
| チームでナレッジを継続更新する | **Neo4j** |
| 素早くプロトタイプを作りたい | **JSON-LD**（インフラ不要） |
| ナレッジが固定・小規模（10件未満） | **JSON-LD** |
| 関係性の複雑な検索が必要 | **Neo4j** |

**このシステムがNeo4jを選んでいる理由：**
1. ナレッジは継続的に追加される想定
2. ページ間の関係性（HumanTask → AIGuidance → AIRole）を型として管理したい
3. AI（Gemini）への入力を必要最小限にすることでトークンコストと精度を両立したい

---

## 参考：このシステムのグラフ構造

```
(MarkdownPage) -[:DEFINES]→ (HumanTask)
(HumanTask)    -[:REPLACEABLE_BY]→ (AIGuidance)
(HumanTask)    -[:PARTIALLY_BY]→   (AIGuidance)
(AIGuidance)   -[:USES_ROLE]→      (AIRole)
```

このエッジ構造があることで、Cypherクエリで「このページには人の作業があり、それをAIが代替でき、使うロールはXだ」という情報を一発で取得できます。

JSON-LDで同じことをやろうとすると、AIがネストされた構造を追いながら同じ解釈をしなければならず、ページ数が増えると信頼性が下がります。
