<template>
  <div class="layout">
    <header>
      <h1 @click="goToHome" class="site-title">中国社会事件数据库</h1>
      <!-- ... 其他header内容 ... -->
    </header>
    <main>
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToHome = () => {
  router.push('/')
}
</script>

<style scoped>
.site-title {
  cursor: pointer;
  user-select: none;
}

.site-title:hover {
  opacity: 0.8;
}
</style> 