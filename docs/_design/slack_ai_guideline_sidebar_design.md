# Slack AI活用ガイドライン サイドバー更新 設計書

## 目的

Lv.3ガイドラインに追加した社員プロファイル検索ページへ、公開サイトのサイドバーから移動できるようにする。

## 対象範囲

- `docs/.vitepress/config.mts` のLv.3サイドバー設定
- 社員情報管理AIページの配下に置く追加ページの導線
- 内部設計書を公開ルートから除外する `srcExclude` 設定

## 主要な処理の流れ

1. 社員情報管理AIの項目を親項目として維持する。
2. 配下に `Slackから行う社員プロファイル検索` を追加する。
3. `docs/_design/` 配下は公開ページとして扱わないため、`srcExclude` で除外する。
4. VitePressビルドで新規ページがHTML化されることを確認する。

## 変更するファイル

- `docs/.vitepress/config.mts`
- `docs/_design/slack_ai_guideline_sidebar_design.md`

## ブランチ・PR戦略

- ベースブランチ: `main`
- 作業ブランチ: `codex/slack-ai-guideline-docs`
- PRサイズ目安: サイドバー導線と公開除外設定に限定し、小さな差分に収める。
- 分割基準: 公開ページ本文や自動化スクリプトの変更は別PRに分ける。
- PR作成タイミング: サイドバー更新、設計書更新、ビルド確認後に作成する。

## 確認方法

- `git diff --check`
- `npm run docs:build`
- ローカルプレビューまたは生成HTMLでサイドバーリンクを確認する。
