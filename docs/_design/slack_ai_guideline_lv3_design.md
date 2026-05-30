# Lv.3成熟度モデル 読書サイクル更新 設計書

## 目的

Lv.3成熟度モデル内の読書サイクル説明を、現在のSlack完結運用と一致させる。

## 対象範囲

- `docs/maturity-model/lv3-autonomous.md` の読書サイクル節
- 書籍購入補助の公開リンク表記

## 主要な処理の流れ

1. 旧来のGitHub Flow前提を削除する。
2. 利用者向け操作はSlack完結であることを明記する。
3. GitHubは読後レポートの保存・公開基盤として位置づける。
4. AI/RAG活用はSlack上の選書相談へ接続する表現に更新する。

## 変更するファイル

- `docs/maturity-model/lv3-autonomous.md`
- `docs/_design/slack_ai_guideline_lv3_design.md`

## ブランチ・PR戦略

- ベースブランチ: `main`
- 作業ブランチ: `codex/slack-ai-guideline-docs`
- PRサイズ目安: Lv.3成熟度モデルの表現更新に限定し、小さな差分に収める。
- 分割基準: 実践ガイド本文や自動化スクリプトの変更は別PRに分ける。
- PR作成タイミング: 本文更新、設計書更新、ビルド確認後に作成する。

## 確認方法

- `git diff --check`
- `npm run docs:build`
- 対象ページで「Slack完結の制度運用」と表示されることを確認する。
