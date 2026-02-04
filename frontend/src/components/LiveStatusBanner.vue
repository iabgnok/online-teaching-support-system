<template>
  <!-- 悬浮按钮 -->
  <div v-if="activeLives.length > 0" class="live-status-float">
    <transition name="expand">
      <div v-if="isExpanded" class="live-status-panel">
        <div class="panel-header">
          <span class="header-title">
            <span class="pulse-dot"></span>
            正在直播 ({{ activeLives.length }})
          </span>
          <el-icon class="collapse-btn" @click="togglePanel"><ArrowDown /></el-icon>
        </div>
        <div class="live-list">
          <div 
            v-for="live in activeLives" 
            :key="live.live_id" 
            class="live-item"
            @click="joinLiveClass(live)"
          >
            <div class="live-icon">
              <el-icon size="18" color="#409eff"><VideoCamera /></el-icon>
            </div>
            <div class="live-info">
              <div class="live-teacher">{{ live.teacher_name }}</div>
              <div class="live-details">
                <span class="live-class">{{ live.class_name }}</span>
                <span class="live-separator">·</span>
                <span class="live-participants">
                  <el-icon size="12"><User /></el-icon>
                  {{ live.participants_count || 0 }}人
                </span>
              </div>
              <div class="live-time">{{ formatDuration(live.start_time) }}</div>
            </div>
            <el-icon class="enter-icon" size="16"><Right /></el-icon>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 折叠状态的按钮 -->
    <div v-if="!isExpanded" class="live-status-badge" @click="togglePanel">
      <span class="pulse-dot"></span>
      <span class="badge-text">{{ activeLives.length }}个直播</span>
    </div>
  </div>
</template>

<script>
import api from '../api'
import { VideoCamera, User, Right, ArrowDown } from '@element-plus/icons-vue'

export default {
  name: 'LiveStatusBanner',
  components: {
    VideoCamera,
    User,
    Right,
    ArrowDown
  },
  data() {
    return {
      activeLives: [],
      timer: null,
      isExpanded: false
    }
  },
  mounted() {
    this.fetchLiveStatus()
    // Poll every 15 seconds for real-time updates
    this.timer = setInterval(this.fetchLiveStatus, 15000)
  },
  beforeUnmount() {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
    }
  },
  methods: {
    async fetchLiveStatus() {
      try {
        const response = await api.get('/chat/live_status')
        if (response.data.code === 200) {
          this.activeLives = response.data.data || []
          // 如果有新的直播且当前是折叠状态，自动展开
          if (this.activeLives.length > 0 && !this.isExpanded) {
            // 可选：第一次有直播时自动展开
            // this.isExpanded = true
          }
        }
      } catch (error) {
        // 静默失败，不影响用户体验
        console.debug('无法获取直播状态:', error.message)
      }
    },
    togglePanel() {
      this.isExpanded = !this.isExpanded
    },
    joinLiveClass(live) {
      // Navigate to live classroom
      this.$router.push({
        name: 'LiveClassroom',
        params: { 
          liveId: live.live_id
        }
      })
    },
    formatDuration(startTime) {
      if (!startTime) return '刚刚开始'
      const start = new Date(startTime)
      const now = new Date()
      const minutes = Math.floor((now - start) / 60000)
      if (minutes < 1) return '刚刚开始'
      if (minutes < 60) return `${minutes}分钟`
      const hours = Math.floor(minutes / 60)
      return `${hours}小时${minutes % 60}分钟`
    }
  }
}
</script>

<style scoped>
.live-status-float {
  position: fixed;
  bottom: 20px;
  left: 20px;
  z-index: 1000;
}

.live-status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: all 0.3s;
  user-select: none;
}

.live-status-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}

.badge-text {
  font-size: 13px;
  font-weight: 600;
}

.live-status-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  overflow: hidden;
  width: 320px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  gap: 8px;
}

.collapse-btn {
  cursor: pointer;
  transition: transform 0.3s;
}

.collapse-btn:hover {
  transform: scale(1.1);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background-color: #ff4444;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.live-list {
  overflow-y: auto;
  max-height: 340px;
}

.live-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.live-item:hover {
  background-color: #f5f7fa;
}

.live-item:last-child {
  border-bottom: none;
}

.live-icon {
  margin-right: 12px;
}

.live-info {
  flex: 1;
  overflow: hidden;
}

.live-teacher {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.live-details {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
}

.live-class {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.live-separator {
  color: #dcdfe6;
}

.live-participants {
  display: flex;
  align-items: center;
  gap: 2px;
}

.live-time {
  font-size: 11px;
  color: #67c23a;
}

.enter-icon {
  margin-left: 8px;
  color: #909399;
}

/* 动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
}

.expand-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.9);
}

.expand-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.9);
}

@keyframes pulse {
  0%, 100% { 
    box-shadow: 0 0 0 0 rgba(255, 68, 68, 0.7);
  }
  50% { 
    box-shadow: 0 0 0 6px rgba(255, 68, 68, 0);
  }
}
</style>