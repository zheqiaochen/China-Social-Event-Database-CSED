<template>
  <div class="event-timeline" :style="{ height: timelineHeight }">

    <!-- 骨架屏：在尚未加载完任何数据时显示 -->
    <div v-if="loading && displayedEvents.length === 0" class="timeline-container skeleton-container">
      <!-- 左侧事件列表骨架 -->
      <div class="event-list">
        <div v-for="i in 8" :key="i" class="event-item skeleton">
          <div class="skeleton-time"></div>
          <div class="skeleton-title"></div>
        </div>
      </div>
      <!-- 右侧内容区域骨架 -->
      <div class="content-area">
        <div class="event-content">
          <div v-for="i in 8" :key="i" class="skeleton-post">
            <div class="skeleton-header">
              <div class="skeleton-name"></div>
            </div>
            <div class="skeleton-content">
              <div class="skeleton-line"></div>
              <div class="skeleton-line"></div>
            </div>
            <div class="skeleton-stats">
              <div class="skeleton-stat"></div>
              <div class="skeleton-stat"></div>
              <div class="skeleton-stat"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <!-- 正式内容 -->
    <div v-else class="timeline-container" :class="{ 'content-view': showContent }">

      <!-- 移动端的返回按钮：当进入内容区域后显示 -->
      <div v-if="showContent && !isDesktop" class="mobile-back" @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回事件列表
      </div>

      <!-- 左侧事件列表 -->
      <div class="event-list" v-show="!showContent || isDesktop">
        <div
          v-for="event in displayedEvents"
          :key="event._id"
          class="event-item"
          :class="{ 
            active: activeEvent === event._id
          }"
          @click="handleEventSelect(event._id)"
        >
          <!-- 以首条帖子时间做粗略显示 -->
          <div class="event-time">{{ formatTime(event.posts?.[0]?.created_at) }}</div>
          <div class="event-info">
            <div class="latest-post-time">{{ formatTime(event.latest_post?.created_at) }}</div>
            <div class="title-row">
              <div class="event-title">{{ event.event_title }}</div>
              <div class="post-count">{{ event.posts_count }} 条</div>
            </div>
          </div>
        </div>
        
        <!-- 加载状态提示 -->
        <div v-if="loadingMore" class="loading-more">
          <el-icon class="loading"><Loading /></el-icon>
          正在加载更多...
        </div>
        
        <!-- 无更多数据提示 -->
        <div v-if="!hasMore && displayedEvents.length > 0" class="no-more">
          没有更多数据了
        </div>
      </div>

      <!-- 右侧帖子内容区域 -->
      <div class="content-area" v-show="showContent || isDesktop">

        <!-- 已选事件的话，显示时间线 -->
        <el-timeline v-if="activeEventPosts.length">
          <el-timeline-item
            v-for="post in activeEventPosts"
            :key="post.id"
            :timestamp="formatTime(post.created_at)"
            placement="top"
          >
            <el-card class="post-card">
              <div class="user-info">
                <div class="title-section">
                  <div class="name-with-link"
                       @click="openWeiboLink(post)"
                       :title="'点击查看原微博'">
                    <span class="screen-name">{{ post.screen_name }}</span>
                    <el-icon class="link-icon"><Link /></el-icon>
                  </div>
                </div>
              </div>
              <div class="post-content">
                {{ post.text }}
              </div>
              <div class="interaction-stats">
                <span class="stat">
                  <el-icon><CaretTop /></el-icon>
                  {{ formatNumber(post.attitudes_count) }}
                </span>
                <span class="stat">
                  <el-icon><ChatRound /></el-icon>
                  {{ formatNumber(post.comments_count) }}
                </span>
                <span class="stat">
                  <el-icon><Position /></el-icon>
                  {{ formatNumber(post.reposts_count) }}
                </span>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, defineExpose, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CaretTop, ChatRound, Position, ArrowLeft, Link, Loading } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useWindowSize } from '@vueuse/core'
import _ from 'lodash'

/* 
  1) 修正：定义 loadingMore / hasMore，避免模板中报错
  2) 日后如需实现“下拉/滚动加载更多”功能，可配合接口逻辑改动
*/
const loadingMore = ref(false)
const hasMore = ref(false)

/**
 * ------------------ 核心状态 ------------------
 */
const originalEvents = ref([])
const displayedEvents = ref([])
const loading = ref(false)
const error = ref(null)
const activeEvent = ref(null)
const activeEventPosts = ref([])

// 移动端与桌面端判断
const { width: screenWidth } = useWindowSize()
const isDesktop = computed(() => screenWidth.value >= 768)
const showContent = ref(false)

// 时间线容器高度
const timelineHeight = ref('calc(100vh - 100px)')

/**
 * ------------------ 工具方法 ------------------
 */

// 修正后的时间格式化：使用 dayjs 判断是否今天/昨天，否则显示完整日期
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const d = dayjs(timestamp)
  const today = dayjs()
  const yesterday = dayjs().subtract(1, 'day')

  if (d.isSame(today, 'day')) {
    // 同一天
    return `今天 ${d.format('HH:mm')}`
  } else if (d.isSame(yesterday, 'day')) {
    // 昨天
    return `昨天 ${d.format('HH:mm')}`
  } else {
    // 其他情况显示 月/日 HH:mm
    // 如果需要跨年显示，可以改成：d.format('YYYY年M月D日 HH:mm')
    return d.format('M月D日 HH:mm')
  }
}

const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

/**
 * ------------------ 核心逻辑 ------------------
 */
// 获取事件列表
const fetchEvents = async () => {
  loading.value = true
  error.value = null
  try {
    const resp = await fetch('/api/events')
    if (!resp.ok) throw new Error(`HTTP error! status: ${resp.status}`)
    const data = await resp.json()
    
    // 处理事件数据
    const processed = data.events.map(evt => ({
      ...evt,
      latestTimestamp: evt.latest_post ? dayjs(evt.latest_post.created_at).valueOf() : 0
    }))

    // 存储原始数据
    originalEvents.value = processed

    // 过滤并排序显示的事件，这里仍然保留“posts_count >= 6”的逻辑
    const filtered = processed
      .filter(e => e.posts_count >= 6)
      .sort((a, b) => {
        if (a.latestTimestamp === b.latestTimestamp) {
          return String(a._id).localeCompare(String(b._id))
        }
        return b.latestTimestamp - a.latestTimestamp
      })

    displayedEvents.value = filtered

    // 若有事件，默认选中第一个并加载其帖子
    if (filtered.length) {
      const firstEvent = filtered[0]
      activeEvent.value = firstEvent._id
      await fetchEventPosts(firstEvent._id)
    }

  } catch (err) {
    console.error('加载事件失败:', err)
    error.value = `加载数据失败：${err.message}`
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

// 获取特定事件的帖子
const fetchEventPosts = async (eventId) => {
  try {
    const resp = await fetch(`/api/event_posts/${eventId}`)
    if (!resp.ok) throw new Error(`HTTP error! status: ${resp.status}`)
    const data = await resp.json()
    
    // 处理帖子数据
    activeEventPosts.value = data.posts.map(post => ({
      ...post,
      timestamp: dayjs(post.created_at).valueOf(),
      // 将微博链接放到这里，供 openWeiboLink 使用
      url: `https://www.weibo.com/detail/${post.id}`
    }))
    // 如果需要从新到旧，可用 sort((a,b) => b.timestamp - a.timestamp)
    // 若想从旧到新则取 a.timestamp - b.timestamp
    activeEventPosts.value.sort((a, b) => b.timestamp - a.timestamp)
    
  } catch (err) {
    console.error('加载帖子失败:', err)
    ElMessage.error(`加载帖子失败：${err.message}`)
    activeEventPosts.value = []
  }
}

// 点击选择事件
const handleEventSelect = async (eventId) => {
  activeEvent.value = eventId
  await fetchEventPosts(eventId)

  // 移动端 -> 显示内容区域
  if (!isDesktop.value) {
    showContent.value = true
  }

  // 从头开始显示
  await nextTick()
  const contentArea = document.querySelector('.content-area')
  if (contentArea) {
    contentArea.scrollTop = 0
  }
}

// 移动端返回列表
const handleBack = () => {
  showContent.value = false
}

// 修正：定义 openWeiboLink，用新标签打开微博详情页
const openWeiboLink = (post) => {
  if (post && post.url) {
    window.open(post.url, '_blank')
  }
}

/**
 * ------------------ 搜索逻辑 ------------------
 */
const filterEvents = (searchText) => {
  if (!originalEvents.value.length) return
  
  if (!searchText) {
    displayedEvents.value = originalEvents.value
      .filter(e => e.posts_count >= 6)
      .sort((a, b) => b.latestTimestamp - a.latestTimestamp)
    return
  }
  
  const lowerText = searchText.toLowerCase()
  const filtered = originalEvents.value
    .filter(event => {
      if (event.posts_count < 6) return false
      return event.event_title.toLowerCase().includes(lowerText)
    })
    .sort((a, b) => b.latestTimestamp - a.latestTimestamp)
  
  displayedEvents.value = filtered
}

defineExpose({ filterEvents, handleBack })

onMounted(() => {
  fetchEvents()
  
  const updateTimelineHeight = () => {
    const windowHeight = window.innerHeight || document.documentElement.clientHeight
    timelineHeight.value = `${windowHeight - 100}px`
  }
  
  updateTimelineHeight()
  window.addEventListener('resize', updateTimelineHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateTimelineHeight)
})
</script>

<style scoped>
/* ---------- 主要容器布局 ---------- */
.event-timeline {
  flex: 1;
  overflow: hidden; 
  padding: 10px;
  box-sizing: border-box;
  height: 100%; 
}

.timeline-container {
  height: 100%;
  display: flex;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

/* 左侧事件列表 */
.event-list {
  width: 310px;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: 1px solid #e4e7ed;
  padding: 10px;
  -webkit-overflow-scrolling: touch; 
}

.event-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: pointer;
}

.event-item.active {
  background-color: #f4f4f5;
}

.event-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.latest-post-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}

.event-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 8px;
}

.event-title {
  font-size: 0.9em;
  font-weight: normal;
  color: var(--el-text-color-primary);
  line-height: 1.4;
  flex: 1;
  margin-right: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-count {
  font-size: 0.8em;
  color: #909399;
  background-color: #f4f4f5;
  padding: 2px 7px;
  border-radius: 10px;
  white-space: nowrap;
  text-align: center;
}

.error {
  color: red;
  padding: 20px;
}

/* 右侧内容区域 */
.content-area {
  flex: 1;
  height: 100%;
  padding: 20px 25px;
  overflow-y: auto;
  overflow-x: hidden; 
  -webkit-overflow-scrolling: touch;
}

.event-content {
  margin-bottom: 20px;
}

/* 帖子卡片样式 */
.post-card {
  margin-bottom: 15px;
  border-radius: 8px;
}

.user-info {
  margin-bottom: 10px;
}

.post-content {
  margin: 10px 0 20px;
  font-size: 14px;
  line-height: 1.6;
}

.interaction-stats {
  display: flex;
  gap: 24px;
  color: #909399;
  font-size: 13px;
  margin-top: 10px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
}
.stat .el-icon {
  font-size: 16px;
}

/* ---------- 移动端适配 ---------- */
@media screen and (max-width: 768px) {
  .timeline-container {
    flex-direction: column;
  }
  .event-list {
    width: 100%;
    height: 100%;
    border-right: none;
  }
  .content-area {
    height: 100%;
    padding: 15px;
  }
  /* 当处于 content-view（点击事件后）时，隐藏左侧事件列表 */
  .timeline-container.content-view .event-list {
    display: none;
  }
  .timeline-container.content-view .content-area {
    padding-top: 0;
  }

  /* 移动端返回按钮 */
  .mobile-back {
    display: flex;
    align-items: center;
    padding: 10px 15px;
    background: #f5f7fa;
    font-size: 14px;
    color: #3f3f3f;
    gap: 5px;
    cursor: pointer;
  }

  .post-card {
    margin: 0 -15px 15px;
    border-radius: 0;
    border-bottom: 8px solid #f5f7fa;
  }

  /* 时间轴在移动端的收缩 */
  :deep(.el-timeline) {
    padding-left: 0;
  }
  :deep(.el-timeline-item__wrapper) {
    padding-left: 0;
  }
  :deep(.el-timeline-item) {
    padding-left: 28px;
  }
  :deep(.el-timeline-item__node) {
    left: 0;
  }
  :deep(.el-timeline-item__tail) {
    left: 4px;
  }
}
/* 桌面端隐藏移动端返回按钮 */
.mobile-back {
  display: none;
}

/* ---------- 骨架屏 ---------- */
@keyframes skeleton-loading {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

.skeleton-container {
  background: #fff;
  display: flex;
  width: 100%;
}

.skeleton {
  background: none;
  padding: 12px;
}

.skeleton-time,
.skeleton-title,
.skeleton-name,
.skeleton-line,
.skeleton-stat {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

.skeleton-time {
  height: 14px;
  width: 100px;
  margin-bottom: 8px;
}

.skeleton-title {
  height: 16px;
  width: 80%;
}

.skeleton-post {
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.skeleton-header {
  margin-bottom: 15px;
}

.skeleton-name {
  height: 16px;
  width: 120px;
}

.skeleton-content {
  margin: 15px 0;
}

.skeleton-line {
  height: 14px;
  margin-bottom: 8px;
}

.skeleton-line:first-child { width: 100%; }
.skeleton-line:last-child  { width: 60%; }

.skeleton-stats {
  display: flex;
  gap: 24px;
  margin-top: 15px;
}

.skeleton-stat {
  height: 14px;
  width: 50px;
}

.name-with-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 15px;
  color: #1d1d1d;
  cursor: pointer;
  font-weight: 450;
}

.link-icon {
  color: #909399;
  font-size: 16px;
}

/* 添加加载更多的样式 */
.loading-more {
  text-align: center;
  padding: 15px 0;
  color: #909399;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.loading-more .loading {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.no-more {
  text-align: center;
  padding: 15px 0;
  color: #909399;
  font-size: 14px;
}

</style>
