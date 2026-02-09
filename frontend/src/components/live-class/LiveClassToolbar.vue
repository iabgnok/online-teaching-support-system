<template>
  <div class="live-class-toolbar">
    <div class="toolbar-left">
      <!-- 返回按钮 -->
      <button class="btn-back" @click="handleBack" title="返回">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"></line>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
      </button>
      
      <!-- 课堂信息 -->
      <div class="class-info">
        <h2 class="class-title">{{ lessonInfo?.title || '线上课堂' }}</h2>
        <div class="class-meta">
          <span class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            ID: {{ lessonInfo?.lessonId || lessonInfo?.lesson_id || '' }}
          </span>
          <span class="meta-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            {{ participantCount }} 人在线
          </span>
          <span class="meta-item duration" v-if="duration">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            {{ formattedDuration }}
          </span>
        </div>
      </div>
    </div>
    
    <div class="toolbar-center">
      <!-- 直播状态指示 -->
      <div class="live-indicator">
        <span class="live-dot"></span>
        <span class="live-text">直播中</span>
      </div>
    </div>
    
    <div class="toolbar-right">
      <!-- 教师特有按钮 -->
      <template v-if="role === 'teacher'">
        <!-- 屏幕共享 -->
        <button 
          class="toolbar-btn" 
          :class="{ active: isScreenSharing }"
          @click="toggleScreenShare"
          :title="isScreenSharing ? '停止共享' : '共享屏幕'"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
          <span>{{ isScreenSharing ? '停止共享' : '共享屏幕' }}</span>
        </button>
        
        <!-- 课堂操作 -->
        <div class="dropdown-wrapper">
          <button class="toolbar-btn" @click="showActionsMenu = !showActionsMenu">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="1"></circle>
              <circle cx="12" cy="5" r="1"></circle>
              <circle cx="12" cy="19" r="1"></circle>
            </svg>
            <span>课堂操作</span>
          </button>
          
          <transition name="dropdown">
            <div v-if="showActionsMenu" class="dropdown-menu">
              <button class="dropdown-item" @click="handleAction('attendance')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                  <circle cx="8.5" cy="7" r="4"></circle>
                  <polyline points="17 11 19 13 23 9"></polyline>
                </svg>
                发起签到
              </button>
              <button class="dropdown-item" @click="handleAction('task')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
                发布任务
              </button>
              <button class="dropdown-item" @click="handleAction('quiz')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                随堂测验
              </button>
              <div class="dropdown-divider"></div>
              <button class="dropdown-item" @click="handleAction('shareBoard')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path>
                  <polyline points="16 6 12 2 8 6"></polyline>
                  <line x1="12" y1="2" x2="12" y2="15"></line>
                </svg>
                分享板书
              </button>
            </div>
          </transition>
        </div>
      </template>
      
      <!-- 通用按钮 -->
      <button 
        class="toolbar-btn" 
        :class="{ active: showParticipants }"
        @click="$emit('toggle-participants')"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
          <circle cx="9" cy="7" r="4"></circle>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
        </svg>
        <span>参与者</span>
      </button>
      
      <!-- 结束/退出按钮 -->
      <button 
        class="toolbar-btn danger" 
        @click="handleExit"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
        <span>{{ role === 'teacher' ? '结束授课' : '退出课堂' }}</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

export default {
  name: 'LiveClassToolbar',
  props: {
    role: {
      type: String,
      default: 'student',
      validator: (value) => !value || ['teacher', 'student'].includes(value)
    },
    lessonInfo: {
      type: Object,
      default: () => ({})
    },
    participantCount: {
      type: Number,
      default: 0
    },
    showParticipants: {
      type: Boolean,
      default: false
    },
    isScreenSharing: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'back',
    'end-class',
    'exit-class',
    'toggle-participants',
    'toggle-screen-share',
    'start-attendance',
    'publish-task',
    'start-quiz',
    'share-board'
  ],
  setup(props, { emit }) {
    const showActionsMenu = ref(false)
    const duration = ref(0)
    let durationTimer = null
    
    // 格式化时长
    const formattedDuration = computed(() => {
      const hours = Math.floor(duration.value / 3600)
      const minutes = Math.floor((duration.value % 3600) / 60)
      const seconds = duration.value % 60
      
      if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
      }
      return `${minutes}:${String(seconds).padStart(2, '0')}`
    })
    
    // 返回
    const handleBack = () => {
      emit('back')
    }
    
    // 切换屏幕共享
    const toggleScreenShare = () => {
      emit('toggle-screen-share')
    }
    
    // 处理操作
    const handleAction = (action) => {
      showActionsMenu.value = false
      
      switch (action) {
        case 'attendance':
          emit('start-attendance')
          break
        case 'task':
          emit('publish-task')
          break
        case 'quiz':
          emit('start-quiz')
          break
        case 'shareBoard':
          emit('share-board')
          break
      }
    }
    
    // 退出/结束
    const handleExit = () => {
      if (props.role === 'teacher') {
        emit('end-class')
      } else {
        emit('exit-class')
      }
    }
    
    // 点击外部关闭菜单
    const handleClickOutside = (e) => {
      if (showActionsMenu.value && !e.target.closest('.dropdown-wrapper')) {
        showActionsMenu.value = false
      }
    }
    
    // 计时器
    const startDurationTimer = () => {
      durationTimer = setInterval(() => {
        duration.value++
      }, 1000)
    }
    
    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
      startDurationTimer()
    })
    
    onBeforeUnmount(() => {
      document.removeEventListener('click', handleClickOutside)
      if (durationTimer) {
        clearInterval(durationTimer)
      }
    })
    
    return {
      showActionsMenu,
      duration,
      formattedDuration,
      handleBack,
      toggleScreenShare,
      handleAction,
      handleExit
    }
  }
}
</script>

<style scoped>
.live-class-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

/* 左侧 */
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
}

.class-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.class-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.2;
}

.class-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  opacity: 0.9;
}

.meta-item svg {
  opacity: 0.8;
}

.meta-item.duration {
  background: rgba(255, 255, 255, 0.15);
  padding: 2px 8px;
  border-radius: 12px;
}

/* 中间 */
.toolbar-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 59, 48, 0.9);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.live-dot {
  width: 8px;
  height: 8px;
  background: #fff;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.9); }
}

.live-text {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 右侧 */
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.toolbar-btn.active {
  background: rgba(255, 255, 255, 0.3);
}

.toolbar-btn.danger {
  background: rgba(255, 59, 48, 0.8);
}

.toolbar-btn.danger:hover {
  background: rgba(255, 59, 48, 1);
}

/* 下拉菜单 */
.dropdown-wrapper {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  min-width: 180px;
  overflow: hidden;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: none;
  color: #333;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

.dropdown-item svg {
  color: #666;
}

.dropdown-divider {
  height: 1px;
  background: #eee;
  margin: 4px 0;
}

/* 动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
