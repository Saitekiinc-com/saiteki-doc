# saiteki-doc

SaitekiにおけるAI活用の標準、成熟度モデル、実践ガイドラインを公開するVitePressドキュメントです。

このリポジトリでは、AI活用を固定的なルールではなく、案件での検証結果に応じて更新し続けるナレッジとして扱います。Notionなどで検討した仮説を公開ページに反映し、必要に応じてNeo4jのナレッジグラフやGitHub IssueのAI活用ガイダンスから参照できる状態にします。

## 主な構成

```text
.github/
  ISSUE_TEMPLATE/          GitHub Issue入力フォーム
  workflows/               PagesデプロイとAIガイダンス生成
docs/
  .vitepress/              VitePress設定
  _design/                 内部設計書
  maturity-model/          Lv.1〜Lv.3の成熟度モデル
  practices/
    lv1/                   個人の作業効率化の実践ガイド
    lv2/                   作業領域の拡大の実践ガイド
    lv3/                   組織能力の拡張の実践ガイド
  index.md                 Saiteki AI Standardへのリダイレクト
  saiteki_ai_standard.md   AI活用標準の入口
scripts/
  generate_ai_guidance.py  Issue向けAI活用ガイダンス生成
  notion_to_markdown.py    NotionページのMarkdown化
  notion_to_neo4j.py       docs/practicesからNeo4jグラフを生成
```

## 公開ページの範囲

公開ページは原則として次の場所に限定します。

- `docs/saiteki_ai_standard.md`
- `docs/maturity-model/`
- `docs/practices/lv*/`

`docs/index.md` はサイト入口から `docs/saiteki_ai_standard.md` へ移動するためのリダイレクトだけに使います。新しい本文ページは上記の範囲に追加します。

`docs/_design/` は内部設計書の置き場であり、VitePressの公開対象から除外します。検討中、TBDだけのページ、過去資料、単発の調査メモは公開導線に載せず、必要なら設計書や別リポジトリで管理します。

## ページ追加・更新ルール

ページを追加または大きく更新するときは、次の4点を確認します。

| 確認項目 | 内容 |
| --- | --- |
| 本文 | 目的、対象範囲、人が判断すること、AIに任せること、必要なデータや成果物が書かれているか |
| サイドバー | 公開するページだけが `docs/.vitepress/config.mts` に載っているか |
| 設計書 | `docs/_design/` に変更意図、対象範囲、変更ファイル、確認方法が残っているか |
| ビルド | `npm run docs:build` が通るか |

古くなった情報は残して併記するよりも、現在の判断として上書きすることを優先します。新しいAI活用の試みを追加するときは、既存ページの構成やトーンに合わせます。

## 設計書の単位

設計書は `docs/_design/<topic>_design.md` に置きます。公開ページと同じ階層には置きません。

設計書は、原則として **1 PR / 1 変更意図** を単位にします。1つの変更意図で複数ファイルを触る場合は、1つの設計書にまとめて構いません。逆に、以下の場合は設計書やPRを分けます。

- Lv別ガイドライン本文の追加と自動化スクリプト変更を同時に行う場合
- 公開ページの内容変更と、Neo4jやGitHub Actionsの挙動変更が独立している場合
- レビュー観点が異なる大きな変更になる場合

設計書には、少なくとも次を含めます。

- 目的
- 対象範囲
- 主要な処理の流れ
- 変更するファイル
- ブランチ・PR戦略
- 確認方法

## ローカルコマンド

```bash
npm ci
npm run docs:dev
npm run docs:build
npm run docs:preview
```

PR前には少なくとも次を実行します。

```bash
git diff --check
npm run docs:build
```

## ナレッジグラフへの反映

`docs/practices/**/*.md` をNeo4jへ反映する場合は、次を実行します。

```bash
export NEO4J_PASSWORD="your-neo4j-password"
python3 scripts/notion_to_neo4j.py
```

NotionからMarkdownを生成する場合は、`scripts/notion_to_markdown.py` の `PAGE_CONFIGS` に対象ページIDと出力先Lvを追加して実行します。

```bash
export NOTION_TOKEN="your-notion-token"
python3 scripts/notion_to_markdown.py
```

## GitHub Actions

- `deploy.yml`: `main` へのpushでVitePressをビルドし、GitHub Pagesへデプロイします。
- `ai_guidance.yml`: Issue作成時にNeo4jとGeminiを使ってAI活用ガイダンスをコメントします。

必要なSecretsは次の通りです。

| Secret | 用途 |
| --- | --- |
| `GEMINI_API_KEY` | Geminiによる関連ページ判定とコメント生成 |
| `NEO4J_PASSWORD` | Neo4j Auraへの接続 |

## 整理ルール

- `(TBD)` だけのページは公開サイドバーに載せない。
- 公開導線に載っていない過去資料は、必要性を確認して削除または別管理へ移す。
- `docs/.vitepress/dist/`, `docs/.vitepress/cache/`, `node_modules/`, `.DS_Store` は生成物・ローカルファイルとしてGit管理しない。
- PRは300行前後を目安に小さく保ち、ドキュメント更新と自動化コード更新を分ける。
