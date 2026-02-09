<template>
  <transition name="slide-panel">
    <div v-if="visible" class="participants-panel">
      <!-- 头部 -->
      <div class="panel-header">
        <h3 class="title">
          <span class="icon">👥</span>
          参与者
          <span class="count">({{ participants.length }})</span>
        </h3>
        <button class="close-btn" @click="$emit('close')" title="关闭">
          <span class="close-icon">✕</span>
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="搜索参与者..."
          class="search-input"
        />
        <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">
          ✕
        </button>
      </div>

      <!-- 统计信息 -->
      <div class="stats-bar">
        <div class="stat-item online">
          <span class="dot"></span>
          在线 {{ onlineCount }}
        </div>
        <div class="stat-item offline">
          <span class="dot"></span>
          离线 {{ offlineCount }}
        </div>
        <div v-if="handRaisedCount > 0" class="stat-item hands">
          <span class="hand-icon">✋</span>
          举手 {{ handRaisedCount }}
        </div>
      </div>

      <!-- 参与者列表 -->
      <div class="participants-list" ref="listRef">
        <!-- 教师区域 -->
        <div class="section" v-if="filteredTeachers.length > 0">
          <div class="section-title">
            <span class="title-icon teacher-icon">👨‍🏫</span>
            教师 ({{ filteredTeachers.length }})
          </div>
          <div 
            v-for="teacher in filteredTeachers" 
            :key="teacher.id"
            class="participant-item teacher"
          >
            <div class="avatar">
              <img v-if="teacher.avatar" :src="teacher.avatar" :alt="teacher.name" />
              <span v-else class="avatar-text">{{ getInitial(teacher.name) }}</span>
              <span class="status-dot online"></span>
            </div>
            <div class="info">
              <div class="name">
                {{ teacher.name }}
                <span class="role-tag">教师</span>
              </div>
              <div class="status-text">授课中</div>
            </div>
          </div>
        </div>

        <!-- 学生区域 -->
        <div class="section" v-if="filteredStudents.length > 0">
          <div class="section-title">
            <span class="title-icon student-icon">👨‍🎓</span>
            学生 ({{ filteredStudents.length }})
          </div>
          <div class="participants-list">
            <div 
              v-for="student in filteredStudents" 
              :key="student.id"
              class="participant-item"
              :class="{ 'hand-raised': student.hand_raised }"
            >
              <div class="avatar">
                <img v-if="student.avatar" :src="student.avatar" :alt="student.name" />
                <span v-else class="avatar-text">{{ getInitial(student.name) }}</span>
                <span class="status-dot" :class="{ online: student.online }"></span>
              </div>
              <div class="info">
                <div class="name">
                  {{ student.name }}
                  <span v-if="student.hand_raised" class="hand-icon" title="已举手">✋</span>
                </div>
                <div class="status-text">
                  <span v-if="student.online">在线</span>
                  <span v-else class="offline">离线</span>
                  <span v-if="student.last_active" class="last-active">
                    · {{ formatLastActive(student.last_active) }}
                  </span>
                </div>
              </div>
              <!-- 教师操作菜单 -->
              <div v-if="isTeacher" class="actions">
                <button 
                  v-if="student.hand_raised"
                  class="action-btn answer"
                  @click="$emit('answer-student', student)"
                  title="回应举手"
                >
                  💬
                </button>
                <button 
                  v-if="student.hand_raised"
                  class="action-btn dismiss"
                  @click="$emit('dismiss-hand', student)"
                  title="放下举手"
                >
                  ⬇️
                </button>
                <button 
                  class="action-btn"
                  :class="{ active: student.can_speak }"
                  @click="$emit('allow-speak', student)"
                  :title="student.can_speak ? '禁止发言' : '允许发言'"
                >
                  {{ student.can_speak ? '🔊' : '🔇' }}
                </button>
                <button 
                  class="action-btn focus"
                  @click="$emit('focus-student', student)"
                  title="聚焦"
                >
                  🎯
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="filteredParticipants.length === 0" class="empty-state">
          <div class="empty-icon">👀</div>
          <p v-if="searchQuery">未找到匹配的参与者</p>
          <p v-else>暂无参与者</p>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div v-if="isTeacher" class="panel-footer">
        <button class="footer-btn" @click="handleMuteAll">
          <span class="btn-icon">🔇</span>
          全部静音
        </button>
        <button class="footer-btn" @click="handleDismissAllHands">
          <span class="btn-icon">⬇️</span>
          放下所有手
        </button>
      </div>
    </div>
  </transition>

  <!-- 背景遮罩 -->
  <transition name="fade">
    <div 
      v-if="visible" 
      class="panel-overlay" 
      @click="$emit('close')"
    ></div>
  </transition>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'ParticipantsPanel',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    participants: {
      type: Array,
      default: () => []
    },
    role: {
      type: String,
      default: 'student'
    }
  },
  emits: ['close', 'allow-speak', 'focus-student', 'answer-student', 'dismiss-hand'],
  setup(props) {
    const searchQuery = ref('')
    const listRef = ref(null)

    const isTeacher = computed(() => props.role === 'teacher')

    const filteredParticipants = computed(() => {
      if (!searchQuery.value) return props.participants
      const query = searchQuery.value.toLowerCase()
      return props.participants.filter(p => 
        p.name?.toLowerCase().includes(query)
      )
    })

    const filteredTeachers = computed(() => 
      filteredParticipants.value.filter(p => p.role === 'teacher')
    )

    const filteredStudents = computed(() => 
      filteredParticipants.value.filter(p => p.role === 'student')
    )

    const onlineCount = computed(() => 
      props.participants.filter(p => p.online).length
    )

    const offlineCount = computed(() => 
      props.participants.filter(p => !p.online).length
    )

    const handRaisedCount = computed(() => 
      props.participants.filter(p => p.hand_raised).length
    )

    const getInitial = (name) => {
      return name ? name.charAt(0).toUpperCase() : '?'
    }

    const formatLastActive = (time) => {
      if (!time) return ''
      const now = Date.now()
      const diff = now - new Date(time).getTime()
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(minutes / 60)
      const days = Math.floor(hours / 24)

      if (minutes < 1) return '刚刚'
      if (minutes < 60) return `${minutes}分钟前`
      if (hours < 24) return `${hours}小时前`
      return `${days}天前`
    }

    const handleMuteAll = () => {
      console.log('Mute all')
    }

    const handleDismissAllHands = () => {
      console.log('Dismiss all hands')
    }

    return {
      searchQuery,
      listRef,
      isTeacher,
      filteredParticipants,
      filteredTeachers,
      filteredStudents,
      onlineCount,
      offlineCount,
      handRaisedCount,
      getInitial,
      formatLastActive,
      handleMuteAll,
      handleDismissAllHands
    }
  }
}
</script>

<style scoped>
.participants-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 320px;
  height: 100vh;
  background: #fff;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
  z-index: 200;
  display: flex;
  flex-direction: column;
}

.panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 199;
}

/* 头部 */
.panel-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title .icon {
  font-size: 18px;
}

.title .count {
  font-weight: 400;
  opacity: 0.9;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.close-icon {
  color: #fff;
  font-size: 14px;
}

/* 搜索框 */
.search-box {
  padding: 12px 16px;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-icon {
  font-size: 14px;
  opacity: 0.6;
}

.search-input {
  flex: 1;
  border: none;
  background: #fff;
  padding: 8px 12px;
  border-radius: 20px;
  font-size: 13px;
  outline: none;
  transition: box-shadow 0.2s;
}

.search-input:focus {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.3);
}

.clear-btn {
  width: 20px;
  height: 20px;
  border: none;
  background: #ddd;
  border-radius: 50%;
  font-size: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 统计栏 */
.stats-bar {
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
  display: flex;
  gap: 16px;
  font-size: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
}

.stat-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-item.online .dot {
  background: #52c41a;
}

.stat-item.offline .dot {
  background: #ccc;
}

.stat-item.hands .hand-icon {
  font-size: 14px;
}

/* 参与者列表 */
.participants-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.section {
  margin-bottom: 8px;
}

.section-title {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #999;
  display: flex;
  align-items: center;
  gap: 6px;
}

.title-icon {
  font-size: 14px;
}

.participant-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  gap: 12px;
  transition: background 0.2s;
}

.participant-item:hover {
  background: #f5f7fa;
}

.participant-item.hand-raised {
  background: #fffbeb;
}

.participant-item.teacher {
  background: #f0f7ff;
}

.avatar {
  position: relative;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-text {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
}

.status-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #ccc;
}

.status-dot.online {
  background: #52c41a;
}

.info {
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

.role-tag {
  font-size: 10px;
  padding: 2px 6px;
  background: #409eff;
  color: #fff;
  border-radius: 10px;
}

.hand-icon {
  font-size: 14px;
  animation: wave 1s infinite;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(20deg); }
  75% { transform: rotate(-20deg); }
}

.status-text {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.status-text .offline {
  color: #ccc;
}

.last-active {
  color: #bbb;
}

/* 操作按钮 */
.actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.participant-item:hover .actions,
.participant-item.hand-raised .actions {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #e0e0e0;
  transform: scale(1.1);
}

.action-btn.active {
  background: #409eff;
  color: #fff;
}

.action-btn.answer {
  background: #52c41a;
}

.action-btn.dismiss {
  background: #faad14;
}

/* 空状态 */
.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

/* 底部操作栏 */
.panel-footer {
  padding: 12px 16px;
  background: #f8f9fa;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
}

.footer-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
}

.footer-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

/* 动画 */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.3s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
