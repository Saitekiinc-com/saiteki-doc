# リポジトリ運用整理 設計書

## 目的

公開対象、内部設計書、READMEの運用ルールを整理し、不要な公開ページを削除する。公開ページと内部資料の境界を明確にし、今後のページ追加時に確認すべき項目をREADMEから参照できるようにする。

## 対象範囲

- `docs/practices/lv3/onboarding.md` を削除する。
- `docs/全社員向け資料-AI導入の背景〜NextActionまで.md` を削除する。
- 内部設計書を `docs/_design/` に集約する。
- VitePressのサイドバーと公開除外設定を更新する。
- READMEを最新構成と運用ルールに合わせて更新する。

## 主要な処理の流れ

1. 公開不要なページを削除する。
2. 設計書を `docs/_design/` に移動する。
3. VitePress設定から削除ページのサイドバーリンクを外し、`docs/_design/` を公開対象から除外する。
4. 設計書内の参照パスを新しい配置へ更新する。
5. READMEに公開ページ範囲、設計書単位、ページ追加チェック、整理ルールを追記する。
6. VitePressビルドでリンク切れがないことを確認する。

## 変更するファイル

- `README.md`
- `docs/.vitepress/config.mts`
- `docs/_design/README.md`
- `docs/_design/repo_ops_cleanup_design.md`
- `docs/_design/*_design.md`
- `docs/practices/lv3/onboarding.md`
- `docs/全社員向け資料-AI導入の背景〜NextActionまで.md`

## ブランチ・PR戦略

- ベースブランチ: `main`
- 作業ブランチ: `codex/repo-ops-cleanup`
- PRサイズ目安: README更新、不要ページ削除、設計書移動に限定し、300行前後に収める。
- 分割基準: GitHub ActionsやNeo4j反映スクリプトの挙動変更は別PRに分ける。
- PR作成タイミング: README更新、不要ページ削除、設計書移動、ビルド確認後に作成する。

## 確認方法

- `git diff --check`
- `npm run docs:build`
