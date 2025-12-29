import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Saiteki AI Docs",
  description: "AI Adoption Guidelines & Roadmap",
  base: "/saiteki-doc/",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Roadmap', link: '/エンジニア向けAI導入ロードマップ' },
      { text: 'All Employees', link: '/全社員向け資料-AI導入の背景〜NextActionまで' }
    ],

    sidebar: [
      {
        text: 'AI Adoption',
        items: [
          { text: 'エンジニア向けロードマップ', link: '/エンジニア向けAI導入ロードマップ',
            items: [
              { text: 'Lv.1 Individual (個人支援)', link: '/maturity-model/lv1-individual' },
              { text: 'Lv.2 Shared (シェア型)', link: '/maturity-model/lv2-shared' },
              { text: 'Lv.3 Autonomous (自律型)', link: '/maturity-model/lv3-autonomous' }
            ]
          },
          { text: '全社員向け資料', link: '/全社員向け資料-AI導入の背景〜NextActionまで' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Saitekiinc-com/saiteki-doc' }
    ]
  }
})
