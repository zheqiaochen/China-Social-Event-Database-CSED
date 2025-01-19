<template>
  <div class="event-timeline" :style="{ height: timelineHeight }">

    <!-- 骨架屏：在尚未加载完任何数据时显示 -->
    <div v-if="loading && displayedEvents.length === 0" class="timeline-container skeleton-container">
      <!-- 左侧事件列表骨架 -->
      <div class="event-list">
        <div v-for="i in 5" :key="i" class="event-item skeleton">
          <div class="skeleton-time"></div>
          <div class="skeleton-title"></div>
        </div>
      </div>
      <!-- 右侧内容区域骨架 -->
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
            active: activeEvent === event._id,
            'with-dot': activeEvent === event._id && isDesktop
          }"
          @click="handleEventSelect(event._id)"
        >
          <!-- 显示事件时间（以 posts[0] 为参考）-->
          <div class="event-time">{{ formatTime(event.posts?.[0]?.created_at) }}</div>
          <div class="event-title-container">
            <div class="event-title">
              {{ event.event_title || '未命名事件' }}
            </div>
            <div class="post-count">
              {{ event.posts?.length || 0 }}
            </div>
          </div>
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
import { ref, onMounted, computed, nextTick, defineExpose } from 'vue'
import { ElMessage } from 'element-plus'
import { CaretTop, ChatRound, Position, ArrowLeft, Link } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { useWindowSize } from '@vueuse/core'

/**
 * ------------------ 核心状态 ------------------
 */
// 存放从后端获取的“全部事件”
const originalEvents = ref([])

// 当前在前端显示的事件（基于 originalEvents 过滤/搜索）
const displayedEvents = ref([])

// 是否加载中 / 错误信息
const loading = ref(false)
const error = ref(null)

// 当前选中的事件 ID 及其帖子
const activeEvent = ref(null)
const activeEventPosts = ref([])

// 移动端与桌面端判断
const { width: screenWidth } = useWindowSize()
const isDesktop = computed(() => screenWidth.value >= 768)
const showContent = ref(false) // 移动端：是否进入内容视图

// 时间线容器高度
const timelineHeight = ref('calc(100vh - 100px)')

/**
 * ------------------ 工具方法 ------------------
 */
// 时间格式化
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm')
}

// 数字格式化
const formatNumber = (num) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

// 获取事件时间(这里假定事件时间以 posts[0].created_at 为参考)
const getEventTime = (event) => {
  if (!event.posts?.length) return 0
  return new Date(event.posts[0].created_at).getTime()
}

/**
 * 打开微博链接
 */
const openWeiboLink = (post) => {
  if (!post.url) return
  window.open(post.url, '_blank')
}

/**
 * ------------------ 核心逻辑 ------------------
 */

/**
 * 一次性加载所有事件，存到 originalEvents
 * 然后过滤出「帖子数 >= 6」的事件，并按时间倒序排序存到 displayedEvents
 */
const fetchAllEvents = async () => {
  loading.value = true
  error.value = null
  try {
    const resp = await fetch('/api/events')
    if (!resp.ok) {
      throw new Error(`HTTP error! status: ${resp.status}`)
    }
    const data = await resp.json()
    if (!data.events) {
      throw new Error('接口返回数据格式有误')
    }

    // 先对事件做一次处理和排序
    const processed = data.events.map(evt => {
      // 排序帖子：按时间从新到旧
      evt.posts = (evt.posts || [])
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .map(p => ({
          ...p,
          // 如果后端没给 url，则自行拼接
          url: p.url || `https://www.weibo.com/detail/${p.id}`
        }))
      return evt
    })

    // 存放处理后的事件列表
    originalEvents.value = processed

    // 做过滤和排序（帖子数 >= 6）
    const filtered = originalEvents.value
      .filter(e => e.posts?.length >= 6)
      .sort((a, b) => getEventTime(b) - getEventTime(a))

    displayedEvents.value = filtered

    // 若有事件，则默认选中第一个
    if (displayedEvents.value.length) {
      activeEvent.value = displayedEvents.value[0]._id
      activeEventPosts.value = displayedEvents.value[0].posts
    }

  } catch (err) {
    error.value = `加载数据失败：${err.message}`
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

/**
 * 切换选中事件
 */
const handleEventSelect = async (eventId) => {
  activeEvent.value = eventId
  const event = displayedEvents.value.find(e => e._id === eventId)
  activeEventPosts.value = event?.posts || []

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

/**
 * 移动端 -> 返回列表
 */
const handleBack = () => {
  showContent.value = false
}

/**
 * ------------------ 搜索逻辑：本地搜索 ------------------
 * 父组件通过 ref 调用 filterEvents
 */
const filterEvents = (searchText) => {
  if (!originalEvents.value.length) return

  // 若搜索文本为空，恢复正常列表
  if (!searchText) {
    displayedEvents.value = originalEvents.value
      .filter(e => e.posts?.length >= 6)
      .sort((a, b) => getEventTime(b) - getEventTime(a))
    return
  }

  // 搜索标题或帖子文本中包含关键字
  const lowerText = searchText.toLowerCase()
  const filtered = originalEvents.value.filter(event => {
    // 帖子数要>=6
    if ((event.posts?.length || 0) < 6) return false

    // 标题匹配 or 帖子文本匹配
    const inTitle = (event.event_title || '').toLowerCase().includes(lowerText)
    const inPosts = event.posts.some(post =>
      (post.text || '').toLowerCase().includes(lowerText)
    )
    return (inTitle || inPosts)
  })

  // 再按时间排序
  filtered.sort((a, b) => getEventTime(b) - getEventTime(a))

  displayedEvents.value = filtered
}

/**
 * ------------------ 暴露给父组件的方法 ------------------
 */
defineExpose({
  filterEvents
})

/**
 * ------------------ 生命周期函数 ------------------
 */
onMounted(() => {
  // 拉取所有事件
  fetchAllEvents()

  // 设置初始高度
  const updateTimelineHeight = () => {
    timelineHeight.value = `calc(${document.documentElement.clientHeight}px - 100px)`
  }
  updateTimelineHeight()
  window.addEventListener('resize', updateTimelineHeight)
})
</script>

<style scoped>
/* ---------- 主要容器布局 ---------- */
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

/* 左侧事件列表 */
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

.event-item.active {
  background-color: #f4f4f5;
}

.event-time {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.event-title-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.event-title {
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.error {
  color: red;
  padding: 20px;
}

/* 右侧内容区域 */
.content-area {
  flex: 1;
  padding: 20px 25px;
  overflow-y: auto;
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
</style>
