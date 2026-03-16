---
layout: page
head:
  - - meta
    - http-equiv: refresh
      content: "0; url=/saiteki-doc/saiteki_ai_standard.html"
---

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vitepress'
const router = useRouter()
onMounted(() => {
  router.go('/saiteki_ai_standard')
})
</script>
