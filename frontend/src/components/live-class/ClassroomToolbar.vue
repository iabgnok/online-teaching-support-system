<template>
  <div class="classroom-toolbar" :class="{ collapsed: isCollapsed }">
    <!-- 折叠按钮 -->
    <button class="collapse-btn" @click="toggleCollapse" :title="isCollapsed ? '展开工具栏' : '折叠工具栏'">
      <svg v-if="isCollapsed" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="18 15 12 9 6 15"></polyline>
      </svg>
    </button>

    <!-- 工具栏内容 -->
    <div v-show="!isCollapsed" class="toolbar-content">
      <!-- 左侧：课堂信息 -->
      <div class="toolbar-left">
        <div class="class-info">
          <span class="class-title">{{ lessonInfo?.title || '线上课堂' }}</span>
          <span class="class-status">
            <span class="status-dot"></span>
            直播中
          </span>
        </div>
      </div>

      <!-- 右侧：操作按钮 -->
      <div class="toolbar-right">
        <!-- 角色功能按钮 -->
        <div class="dropdown">
          <button class="btn-role" @click="toggleRoleMenu">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            角色功能
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
          <div v-show="showRoleMenu" class="dropdown-menu">
            <button v-if="isTeacher" class="menu-item" @click="handleStartAttendance">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 11l3 3L22 4"></path>
                <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
              </svg>
              开始点名
            </button>
            <button v-if="isTeacher" class="menu-item" @click="handlePublishTask">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              发布任务
            </button>
            <button v-if="isTeacher" class="menu-item" @click="handleStartQuiz">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
              开始测验
            </button>
            <button v-if="isStudent" class="menu-item" @click="handleRaiseHand">
              <span class="emoji">✋</span>
              举手
            </button>
            <button class="menu-item" @click="handleShareBoard">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="9" cy="9" r="2"></circle>
                <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"></path>
              </svg>
              分享画板
            </button>
          </div>
        </div>

        <!-- 显示参与者按钮 -->
        <button class="btn-participants" @click="$emit('toggle-participants')" :class="{ active: showParticipants }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          参与者 ({{ participantCount }})
        </button>

        <!-- 退出/结束按钮 -->
        <button class="btn-exit" @click="handleExit" :class="{ 'btn-end': isTeacher }">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
          {{ isTeacher ? '结束授课' : '退出课堂' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ClassroomToolbar',
  props: {
    lessonInfo: Object,
    classroomStatus: String,
    participantCount: Number,
    showParticipants: Boolean,
    isTeacher: Boolean,
    isStudent: Boolean
  },
  emits: ['toggle-participants', 'start-attendance', 'publish-task', 'start-quiz', 'raise-hand', 'share-board', 'exit'],
  setup(props, { emit }) {
    const isCollapsed = ref(false)
    const showRoleMenu = ref(false)

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    const toggleRoleMenu = () => {
      showRoleMenu.value = !showRoleMenu.value
    }

    const handleStartAttendance = () => {
      emit('start-attendance')
      showRoleMenu.value = false
    }

    const handlePublishTask = () => {
      emit('publish-task')
      showRoleMenu.value = false
    }

    const handleStartQuiz = () => {
      emit('start-quiz')
      showRoleMenu.value = false
    }

    const handleRaiseHand = () => {
      emit('raise-hand')
      showRoleMenu.value = false
    }

    const handleShareBoard = () => {
      emit('share-board')
      showRoleMenu.value = false
    }

    const handleExit = () => {
      emit('exit')
    }

    return {
      isCollapsed,
      showRoleMenu,
      toggleCollapse,
      toggleRoleMenu,
      handleStartAttendance,
      handlePublishTask,
      handleStartQuiz,
      handleRaiseHand,
      handleShareBoard,
      handleExit
    }
  }
}
</script>

<style scoped>
.classroom-toolbar {
  position: relative;
  flex-shrink: 0;
  min-height: 56px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.classroom-toolbar.collapsed {
  min-height: 28px;
}

.collapse-btn {
  position: absolute;
  top: 50%;
  right: 16px;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  z-index: 11;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.toolbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 60px 12px 16px;
  min-height: 48px;
}

.classroom-toolbar.collapsed .toolbar-content {
  display: none;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.class-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.class-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.class-status {
  font-size: 12px;
  color: #dc3545;
  background: rgba(220, 53, 69, 0.1);
  padding: 4px 8px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #dc3545;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: visible; /* allow dropdown to overflow */
} 

.dropdown {
  position: relative;
  overflow: visible; /* ensure child can overflow */
} 

.btn-role {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-role:hover {
  background: #e9ecef;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  margin-top: 4px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.menu-item:hover {
  background: #f8f9fa;
}

.menu-item:first-child {
  border-radius: 6px 6px 0 0;
}

.menu-item:last-child {
  border-radius: 0 0 6px 6px;
}

.emoji {
  font-size: 16px;
}

.btn-participants {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-participants:hover {
  background: #e9ecef;
}

.btn-participants.active {
  background: #007bff;
  color: #fff;
  border-color: #007bff;
}

.btn-exit {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #dc3545;
  color: #fff;
  border: 1px solid #dc3545;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-exit:hover {
  background: #c82333;
  border-color: #bd2130;
}

.btn-end {
  background: #dc3545;
  border-color: #dc3545;
}

.btn-end:hover {
  background: #c82333;
  border-color: #bd2130;
}
</style>