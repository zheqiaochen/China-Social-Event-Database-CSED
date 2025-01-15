<template>
  <div class="event-timeline" :style="{ height: timelineHeight }">
    <div v-if="loading" class="timeline-container skeleton-container">
      <!-- 事件列表骨架屏 -->
      <div class="event-list">
        <div v-for="i in 5" :key="i" class="event-item skeleton">
          <div class="skeleton-time"></div>
          <div class="skeleton-title"></div>
        </div>
      </div>

      <!-- 内容区域骨架屏 -->
      <div class="content-area">
        <div class="event-content">
          <div v-for="i in 3" :key="i" class="skeleton-post">
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
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else class="timeline-container" :class="{'content-view': showContent}">
      <!-- 移动端返回按钮 -->
      <div v-if="showContent" class="mobile-back" @click="handleBack">
        <el-icon><ArrowLeft /></el-icon>
        返回事件列表
      </div>
      
      <!-- 事件列表 -->
      <div class="event-list" v-show="!showContent || isDesktop" @scroll="handleScroll">
        <div
          v-for="event in displayedEvents"
          :key="event.eventId"
          class="event-item"
          :class="{ 
            active: activeEvent === event.eventId,
            'with-dot': activeEvent === event.eventId && isDesktop
          }"
          @click="handleEventSelect(event.eventId)"
        >
          <div class="event-time">{{ formatTime(getEarliestTime(event.posts)) }}</div>
          <div class="event-title-container">
            <div class="event-title">{{ event.eventTitle }}</div>
            <div class="post-count">{{ event.posts.length }}</div>
          </div>
        </div>
        
        <!-- 加载状态提示 -->
        <div v-if="hasMore" class="loading-more">
          加载更多...
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="content-area" v-show="showContent || isDesktop">
        <template v-for="event in groupedEvents" :key="event.eventId">
          <div v-show="activeEvent === event.eventId" class="event-content">
            <el-timeline>
              <el-timeline-item
                v-for="post in event.posts"
                :key="post._id"
                :timestamp="formatTime(post.created_at)"
                placement="top"
              >
                <el-card class="post-card">
                  <div class="user-info">
                    <div class="title-section">
                      <div class="name-with-link" @click="openWeiboLink(post)" :title="'点击查看原微博'">
                        <span class="screen-name">{{ post.screen_name }}</span>
                        <el-icon class="link-icon"><Link /></el-icon>
                      </div>
                      <!-- 取消星星 -->
                      <!-- <el-icon v-if="(post.response ?? 0) === 1" class="response-icon">
                        <Star />
                      </el-icon> -->
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
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CaretTop, ChatRound, Position, Link, Star, ArrowLeft } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useRouter, useRoute } from 'vue-router'
import { useWindowSize } from '@vueuse/core'

// 状态变量
const activeEvent = ref('')
const groupedEvents = ref([])
const loading = ref(false)
const error = ref(null)
const originalEvents = ref([])
const showEventList = ref(true)
const showContent = ref(false)
const { width: screenWidth } = useWindowSize()
const pageSize = ref(10)
const currentPage = ref(0)
const displayedEvents = ref([])
const hasMore = ref(true)

// 格式化数字
const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm')
}

// 打开微博链接
const openWeiboLink = (post) => {
  if (!post.url) {
    ElMessage.warning('该微博链接不可用')
    return
  }
  window.open(post.url, '_blank')
}

// 获取数据
const fetchEventData = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await fetch('/api/events')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    if (!data.events) {
      throw new Error('返回数据格式错误')
    }
    
    const processedEvents = data.events
      .map(event => ({
        eventId: event._id,
        eventTitle: event.event_title || '未命名事件',
        firstPostTime: Math.min(...event.posts.map(post => new Date(post.created_at || 0).getTime())),
        posts: (event.posts || [])
          .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
          .map(post => ({
            ...post,
            url: `https://m.weibo.cn/detail/${post.id}`,
            response: post.response ?? 0
          }))
      }))
      .sort((a, b) => b.firstPostTime - a.firstPostTime)
    
    originalEvents.value = processedEvents
    groupedEvents.value = processedEvents
    loadMoreEvents()
    
    if (groupedEvents.value.length > 0) {
      activeEvent.value = groupedEvents.value[0].eventId
    }
    
  } catch (err) {
    console.error('获取数据失败:', err)
    error.value = `获取数据失败: ${err.message}`
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

// 新增获取最早时间的方法
const getEarliestTime = (posts) => {
  if (!posts || posts.length === 0) return ''
  const times = posts.map(post => new Date(post.created_at).getTime())
  return Math.min(...times)
}

const route = useRoute()
const router = useRouter()

const handleEventSelect = (eventId) => {
  activeEvent.value = eventId
  // 重置内容区域的滚动位置
  const contentArea = document.querySelector('.content-area')
  if (contentArea) {
    contentArea.scrollTop = 0
  }
  
  if (screenWidth.value < 768) {
    showContent.value = true
    router.push(`/event/${eventId}`)
  }
}

const handleBack = () => {
  showContent.value = false
  router.push('/')
}

const filterEvents = (searchText) => {
  if (!searchText) {
    currentPage.value = 0
    displayedEvents.value = []
    hasMore.value = true
    loadMoreEvents()
  } else {
    const filteredEvents = originalEvents.value.filter(event => 
      event.eventTitle.toLowerCase().includes(searchText.toLowerCase()) ||
      event.posts.some(post => 
        post.text.toLowerCase().includes(searchText.toLowerCase())
      )
    )
    displayedEvents.value = filteredEvents
    hasMore.value = false
  }
}

const toggleEventList = () => {
  showEventList.value = !showEventList.value
}

const isDesktop = computed(() => screenWidth.value >= 768)

// 添加视口高度响应
const timelineHeight = ref('calc(100vh - 100px)')

onMounted(() => {
  fetchEventData().then(() => {
    const eventId = route.params.id
    if (eventId && screenWidth.value < 768) {
      activeEvent.value = eventId
      showContent.value = true
    }
  })

  const updateTimelineHeight = () => {
    timelineHeight.value = `calc(${document.documentElement.clientHeight}px - 100px)`
  }
  updateTimelineHeight()
  window.addEventListener('resize', updateTimelineHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateTimelineHeight)
})

// 监听路由变化
watch(
  () => route.path,
  (newPath) => {
    if (newPath === '/' && showContent.value) {
      showContent.value = false
    }
  }
)

// 暴露方法给父组件
defineExpose({
  filterEvents
})

// 添加新的加载方法
const loadMoreEvents = () => {
  const start = currentPage.value * pageSize.value
  const end = start + pageSize.value
  const newEvents = originalEvents.value.slice(start, end)
  
  if (newEvents.length > 0) {
    displayedEvents.value = [...displayedEvents.value, ...newEvents]
    if (currentPage.value === 0) {
      groupedEvents.value = originalEvents.value
    }
    currentPage.value++
    hasMore.value = end < originalEvents.value.length
  } else {
    hasMore.value = false
  }
}

// 添加滚动处理方法
const handleScroll = (e) => {
  const element = e.target
  if (
    element.scrollHeight - element.scrollTop - element.clientHeight < 50 && 
    hasMore.value && 
    !loading.value
  ) {
    loadMoreEvents()
  }
}
// 过滤帖子小于6条的事件
const events = computed(() => {
  if (!eventData.value) return []
  return eventData.value
    .filter(event => event.post_count >= 6)
    .sort((a, b) => {
      return new Date(b.start_time) - new Date(a.start_time)
    })
})
</script>

<style scoped>
.event-timeline {
  flex: 1;
  overflow: hidden;
  padding: 10px;
  box-sizing: border-box;
}

.timeline-container {
  height: 100%;
  display: flex;
  background: #fff;
  border-radius: 8px;
}

.event-list {
  width: 310px;
  height: 100%;
  overflow-y: auto;
  border-right: 1px solid #e4e7ed;
  padding: 10px;
}

.event-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: pointer;
}

.event-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.event-title {
  font-size: 14px;
  line-height: 1.4;
}

.content-area {
  flex: 1;
  padding: 20px 25px;
  overflow-y: auto;
}

/* 移动端样式 */
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
    padding: 15px;
    height: 100%;
  }

  .timeline-container.content-view .event-list {
    display: none;
  }

  .timeline-container.content-view .content-area {
    padding-top: 0;
  }

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

.post-card {
  margin-bottom: 15px;
  border-radius: 8px;
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
  padding: 0;
  margin-top: 10px;
  border-top: none;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat .el-icon {
  font-size: 16px;
}

@media screen and (max-width: 768px) {
  .interaction-stats {
    gap: 20px;
    padding: 10px 0;
  }
  
  .stat {
    gap: 4px;
  }
  
  .stat .el-icon {
    font-size: 14px;
  }
}

.response-icon {
  color: #f7ba2a;  /* 金黄色 */
  font-size: 16px;
  margin-left: 4px;
}

.title-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.name-with-link {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.link-icon {
  color: #909399;
  font-size: 16px;
}

.response-icon {
  color: #f7ba2a;
  font-size: 16px;
}

/* 修改时间轴和卡片布局 */
@media screen and (max-width: 768px) {
  .el-timeline {
    padding-left: 0;
  }

  .el-timeline-item {
    padding-left: 28px;
  }

  .el-timeline-item__node {
    left: 0;
  }

  .el-timeline-item__tail {
    left: 4px;
  }

  .el-timeline-item__wrapper {
    padding-left: 0;
    padding-right: 0;
  }

  .post-card {
    margin: 0 auto 15px;
    width: 92%;
    border-radius: 8px;
  }
}

.event-item.with-dot {
  position: relative;
}

.event-item.with-dot::before {
  content: '';
  position: absolute;
  left: -7px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  background-color: #dd1111;
  border-radius: 50%;
}

.event-item.with-dot {
  padding-left: 18px;  /* 有红点就加一点缩进 */
}

/* 添加骨架屏样式 */
@keyframes skeleton-loading {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

.skeleton {
  background: none;
  padding: 12px;
}

.skeleton-container {
  background: #fff;
}

.skeleton-time {
  height: 14px;
  width: 100px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-title {
  height: 16px;
  width: 80%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
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
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

.skeleton-content {
  margin: 15px 0;
}

.skeleton-line {
  height: 14px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-line:first-child {
  width: 100%;
}

.skeleton-line:last-child {
  width: 60%;
}

.skeleton-stats {
  display: flex;
  gap: 24px;
  margin-top: 15px;
}

.skeleton-stat {
  height: 14px;
  width: 50px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .skeleton-post {
    margin: 0 auto 15px;
    width: 92%;
  }
  
  .skeleton-stats {
    gap: 20px;
  }
}

.loading-more {
  text-align: center;
  padding: 10px;
  color: #909399;
  font-size: 14px;
}

.event-title-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.post-count {
  font-size: 12px;
  color: #909399;
  background-color: #f4f4f5;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

/* 确保标题不会因为数字太长而被挤压 */
.event-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style> 