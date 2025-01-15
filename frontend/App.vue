<template>
  <div class="app" :style="{ height: appHeight }">
    <header class="header">
      <div class="header-content">
        <router-link to="/" class="title-link">
          <h1 class="title">中国社会事件数据库</h1>
        </router-link>
        <div class="header-right">
          <el-input
            v-model="searchText"
            placeholder="搜索事件..."
            class="search-input"
            :prefix-icon="Search"
            @input="handleSearch"
            clearable
          />
          <nav class="nav">
            <router-link to="/about" class="nav-link">关于</router-link>
          </nav>
        </div>
      </div>
    </header>
    <router-view v-if="$route.path === '/about'" />
    <EventTimeline v-else ref="eventTimeline" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import EventTimeline from './components/EventTimeline.vue'

const searchText = ref('')
const eventTimeline = ref(null)
const appHeight = ref('100vh')

// 添加移动端高度适配
onMounted(() => {
  const setAppHeight = () => {
    appHeight.value = `${document.documentElement.clientHeight}px`
  }
  setAppHeight()
  window.addEventListener('resize', setAppHeight)
})

const handleSearch = (value) => {
  if (eventTimeline.value) {
    eventTimeline.value.filterEvents(value)
  }
}
</script>

<style>
.app {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-width: 100%;
  margin: 0 auto;
  padding: 10px;
}

.header {
  flex-shrink: 0;
  margin-bottom: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #eaeaea;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.search-input {
  width: 200px;
}

.title {
  font-size: 24px;
  margin: 0;
}

.nav-link {
  color: #606266;
  text-decoration: none;
  font-size: 16px;
  transition: color 0.3s;
}

.nav-link:hover {
  color: #2f2f2f;
}

.title-link {
  text-decoration: none;
  color: inherit;
  transition: opacity 0.3s;
}

.title-link:hover {
  opacity: 0.8;
}

.nav {
  text-align: center;
}

/* 移动端样式 */
@media screen and (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 12px;
    padding: 0 5px;
  }

  .title {
    font-size: 18px;
    text-align: center;
  }

  .header-right {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .nav {
    display: flex;
    gap: 15px;
    align-items: center;
  }
}

:root {
  --el-color-primary: #2f2f2f; 
}
</style> 