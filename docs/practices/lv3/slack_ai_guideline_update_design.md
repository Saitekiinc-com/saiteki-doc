# Slack AI活用ガイドライン更新 設計書

## 目的

Lv.3のAI活用ガイドラインを、実際の運用に合わせて更新する。古くなったGitHub入口前提の説明をSlack完結前提へ上書きし、社員情報管理AIの発展形としてSlackプロファイル検索ページを追加する。

## 対象範囲

- 読書サイクルの説明を、Slackで申請・承認・領収書提出・レポート提出が進む前提に更新する。
- 社員情報管理AIの説明を、プロフィール生成だけでなくSlackから人を探す運用へ更新する。
- 社員情報管理AIの配下に、Slackプロファイル検索の実践ページを追加する。
- Slackプロファイル検索ページに、用意するデータ、データ構造、index生成、embedding、検索方式、AI再ランキングの説明を追加する。
- 現行運用ではメッセージindex検索が主で、プロフィールindex検索はfallback設定を有効化した場合のみ使う前提を明記する。
- Lv.3成熟度モデル内の読書サイクル説明も、Slack前提へ合わせる。
- 同階層設計書は公開ページとして扱わないよう、VitePressの公開ルートから除外する。

## 主要な処理の流れ

1. 既存公開ページの古い前提を確認する。
2. `saiteki-study-doc` のSlack書籍購入補助フローを確認する。
3. `saiteki-employee-management` のSlack People Finder構成を確認する。
4. `origin/main` の検索index生成スクリプト、Worker、workflowからデータ構造と検索フローを確認する。
5. Lv.3配下の本文とサイドバーを更新する。
6. 同階層設計書を `srcExclude` で除外する。
7. VitePressビルドでリンクとMarkdown構造を確認する。

## 変更するファイル

- `docs/practices/lv3/reading_cycle.md`
- `docs/practices/lv3/employee_management.md`
- `docs/practices/lv3/employee_profile_search.md`
- `docs/practices/lv3/slack_ai_guideline_update_design.md`
- `docs/maturity-model/lv3-autonomous.md`
- `docs/maturity-model/slack_ai_guideline_lv3_design.md`
- `docs/.vitepress/config.mts`
- `docs/.vitepress/slack_ai_guideline_sidebar_design.md`

## ブランチ・PR戦略

- ベースブランチ: `main`
- 作業ブランチ: `codex/profile-search-data-flow-docs`
- PRサイズ目安: 公開ドキュメント中心で300行前後を目標にする。
- 分割基準: 実装コード、Slack App設定、検索index生成ロジックの変更は別PRに分ける。
- PR作成タイミング: 本文更新、サイドバー更新、ビルド確認後に作成する。

## 確認方法

- `git diff --check`
- `npm run docs:build`
