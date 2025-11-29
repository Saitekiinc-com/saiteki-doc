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
          { text: 'エンジニア向けロードマップ', link: '/エンジニア向けAI導入ロードマップ' },
          { text: '全社員向け資料', link: '/全社員向け資料-AI導入の背景〜NextActionまで' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Saitekiinc-com/saiteki-doc' }
    ]
  }
})
