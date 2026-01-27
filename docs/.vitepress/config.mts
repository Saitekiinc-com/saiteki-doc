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
              { text: '企画視点の作業リスト', link: '/practices/lv1/planning' },
              {
                text: '開発視点の作業リスト',
                collapsed: false,
                items: [
                  { text: '目次', link: '/practices/lv1/development/' },
                  { text: '要件定義の構造化', link: '/practices/lv1/development/req_test' }
                ]
              },
              { text: 'QA視点の作業リスト', link: '/practices/lv1/qa' },
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
              { text: '日報ナレッジ蓄積プロセス', link: '/practices/lv3/knowledge_process' },
              { text: '自律型ナレッジシェア', link: '/practices/lv3/knowledge_share' },
              { text: '読書サイクル', link: '/practices/lv3/reading_cycle' },
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
