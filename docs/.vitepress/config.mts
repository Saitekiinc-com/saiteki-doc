import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

// https://vitepress.dev/reference/site-config
export default withMermaid({
  title: "Saiteki AI Standardドキュメント",
  description: "AI駆動開発の標準化指針と実践カリキュラム",
  base: "/saiteki-doc/",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Standard (指針)', link: '/saiteki_ai_standard' }
    ],

    sidebar: [
      {
        text: 'AI導入指針 (Adoption)',
        items: [
          {
            text: 'Saiteki AI Standard', link: '/saiteki_ai_standard',
            items: [
              { text: 'Lv.1 Individual (個人支援)', link: '/maturity-model/lv1-individual' },
              { text: 'Lv.2 Shared (シェア型)', link: '/maturity-model/lv2-shared' },
              { text: 'Lv.3 Autonomous (自律型)', link: '/maturity-model/lv3-autonomous' }
            ]
          }
        ]
      },
      {
        text: 'ガイドライン',
        items: [
          {
            text: 'Lv.1 個人の作業効率化',
            items: [
              { text: 'テスト観点抽出（汎用）', link: '/practices/lv1/test_viewpoint_extraction' },
              { text: 'テスト戦略の策定', link: '/practices/lv1/test_strategy' },
              { text: 'テスト設計書作成', link: '/practices/lv1/test_design_document' },
              { text: '実行用テストケース実装', link: '/practices/lv1/test_case_implementation' },
              { text: '工数見積もりの精緻化', link: '/practices/lv1/estimation' },
              { text: 'API仕様の先行確定', link: '/practices/lv1/api_spec' },
              { text: 'フロントエンド実装の加速', link: '/practices/lv1/frontend_impl' },
              { text: 'サーバーサイド実装の加速', link: '/practices/lv1/backend_impl' },
              { text: 'ユニットテストの自動生成', link: '/practices/lv1/unit_test' },
              { text: '結合テストの効率化', link: '/practices/lv1/integration_test' },
            ]
          },
          {
            text: 'Lv.2 合意形成の加速',
            items: [
              { text: 'HTMLモック早期生成', link: '/practices/lv2/mock_driven' },
              { text: 'API・データモデルの先行生成', link: '/practices/lv2/api_data' },
            ]
          },
          {
            text: 'Lv.3 組織能力の拡張',
            items: [
              { text: '独自モデルの構築', link: '/practices/lv3/custom_model' },
              { text: 'オンボーディング計画作成', link: '/practices/lv3/onboarding' },
              { text: '社員情報管理AIの活用', link: '/practices/lv3/employee_management' },
              { text: '読書サイクル', link: '/practices/lv3/reading_cycle' },
              { text: 'AIタスクレビューシステム', link: '/practices/lv3/ai_task_review' },
            ]
          }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Saitekiinc-com/saiteki-doc' }
    ]
  }
})
