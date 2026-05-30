# Slack AI活用ガイドライン サイドバー更新 設計書

## 目的

Lv.3ガイドラインに追加した社員プロファイル検索ページへ、公開サイトのサイドバーから移動できるようにする。

## 対象範囲

- `docs/.vitepress/config.mts` のLv.3サイドバー設定
- 社員情報管理AIページの配下に置く追加ページの導線
- 今回追加した設計書を公開ルートから除外する `srcExclude` 設定
- Saiteki AI Standard運用方針の設計書を公開ルートから除外する `srcExclude` 設定

## 主要な処理の流れ

1. 社員情報管理AIの項目を親項目として維持する。
2. 配下に `Slackから行う社員プロファイル検索` を追加する。
3. `slack_ai_guideline_*_design.md` と `ai_standard_operation_policy_design.md` は公開ページとして扱わないため、`srcExclude` で除外する。
4. VitePressビルドで新規ページがHTML化されることを確認する。

## 変更するファイル

- `docs/.vitepress/config.mts`
- `docs/.vitepress/slack_ai_guideline_sidebar_design.md`

## 確認方法

- `npm run docs:build`
- ローカルプレビューまたは生成HTMLでサイドバーリンクを確認する。
