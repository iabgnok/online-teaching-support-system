<template>
  <div class="chat-header">
    <div class="header-content">
      <!-- 左侧：头像+信息 -->
      <div class="header-left">
        <div class="conv-avatar">
          <img v-if="conversation.avatar" :src="conversation.avatar" />
          <div v-else class="avatar-placeholder">
            {{ getAvatarText() }}
          </div>
        </div>
        
        <div class="conv-info">
          <div class="conv-title">{{ conversation.title || '未命名对话' }}</div>
          <div class="conv-subtitle">
            <template v-if="conversation.type === 'private' && conversation.other_user">
              <span v-if="conversation.other_user.is_online" class="status-online">在线</span>
              <span v-else class="status-offline">{{ formatLastSeen(conversation.other_user.last_seen) }}</span>
            </template>
            <template v-else-if="conversation.member_count">
              {{ conversation.member_count }} 名成员
            </template>
          </div>
        </div>
      </div>
      
      <!-- 右侧：功能按钮 -->
      <div class="header-actions">
        <!-- 班级群教师可以开始授课 -->
        <button 
          v-if="canStartClass" 
          @click="showClassSettings = true"
          :disabled="startingClass"
          class="action-btn primary-btn"
          title="开始授课"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="23 7 16 12 23 17 23 7"></polygon>
            <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
          </svg>
        </button>
        
        <!-- 如果课堂正在进行，显示进入课堂按钮 -->
        <button 
          v-if="hasActiveClass" 
          @click="handleJoinClass"
          class="action-btn success-btn"
          title="进入课堂"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polygon points="10 8 16 12 10 16 10 8"></polygon>
          </svg>
        </button>
        
        <button 
          @click="$emit('search')"
          class="action-btn"
          title="搜索"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
        </button>
        
        <button 
          @click="$emit('show-info')"
          class="action-btn"
          title="详情"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="1"></circle>
            <circle cx="12" cy="5" r="1"></circle>
            <circle cx="12" cy="19" r="1"></circle>
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 课堂设置对话框 -->
    <LiveClassSettingsDialog
      v-model="showClassSettings"
      :conversation="conversation"
      @confirm="handleStartClass"
    />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'
import LiveClassSettingsDialog from './LiveClassSettingsDialog.vue'

const router = useRouter()

const props = defineProps({
  conversation: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['search', 'show-info'])

const startingClass = ref(false)
const activeClassInfo = ref(null)
const userRole = ref(localStorage.getItem('user_role'))
const showClassSettings = ref(false)

// 判断是否可以开始授课（班级群且是教师）
const canStartClass = computed(() => {
  const conversationType = props.conversation.type
  const hasClassId = !!props.conversation.class_id
  
  return userRole.value === 'teacher' && 
         (conversationType === 'class_group' || conversationType === 'course_group') &&
         hasClassId
})

// 判断是否有进行中的课堂
const hasActiveClass = computed(() => {
  return activeClassInfo.value !== null
})

// 检查当前班级是否有进行中的课堂
const checkActiveClass = async () => {
  if (!props.conversation.class_id) {
    return
  }
  
  try {
    const response = await api.get('/live-class/active')
    const activeClasses = response.data || []
    
    // 查找当前班级的活跃课堂
    const classActive = activeClasses.find(
      cls => cls.class_id === props.conversation.class_id
    )
    
    if (classActive) {
      activeClassInfo.value = classActive
    } else {
      activeClassInfo.value = null
    }
  } catch (error) {
    console.error('检查活跃课堂失败:', error)
  }
}

// 开始授课
const handleStartClass = async (settings) => {
  if (!props.conversation.class_id) {
    ElMessage.error('无法获取班级信息')
    return
  }
  
  startingClass.value = true
  showClassSettings.value = false
  
  try {
    const response = await api.post('/live-class/start', {
      class_id: props.conversation.class_id,
      title: settings.title,
      description: settings.description,
      duration: settings.duration,
      notify_methods: settings.notifyMethods,
      conversation_id: props.conversation.id  // 传递对话ID
    })
    
    const lessonId = response.data.lesson_id
    
    ElMessage.success('课堂已开启')
    
    // 跳转到授课页面
    router.push(`/teacher/live-class/${lessonId}`)
  } catch (error) {
    console.error('开始授课失败:', error)
    ElMessage.error(error.response?.data?.error || '开始授课失败')
  } finally {
    startingClass.value = false
  }
}

// 进入课堂
const handleJoinClass = () => {
  if (!activeClassInfo.value) return
  
  const lessonId = activeClassInfo.value.lesson_id
  
  if (userRole.value === 'teacher') {
    router.push(`/teacher/live-class/${lessonId}`)
  } else {
    router.push(`/live-class/${lessonId}`)
  }
}

// 组件挂载时检查活跃课堂
onMounted(() => {
  if (canStartClass.value || props.conversation.type === 'class_group') {
    checkActiveClass()
    
    // 每30秒检查一次
    setInterval(checkActiveClass, 30000)
  }
})

const getAvatarText = () => {
  const title = props.conversation.title || ''
  return title.substring(0, 2) || '?'
}

const formatLastSeen = (lastSeen) => {
  if (!lastSeen) return '离线'
  
  const date = new Date(lastSeen)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 5) return '刚刚在线'
  if (diffMins < 60) return `${diffMins}分钟前在线`
  
  const diffHours = Math.floor(diffMs / 3600000)
  if (diffHours < 24) return `${diffHours}小时前在线`
  
  return '离线'
}
</script>

<style scoped>
/* Telegram风格聊天头部 */
.chat-header {
  border-bottom: 1px solid #e5e5e5;
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  min-height: 56px;
}

/* 左侧区域 */
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.header-left:hover .conv-title {
  color: #409eff;
}

/* 头像 */
.conv-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.conv-avatar:hover {
  opacity: 0.9;
}

.conv-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.conv-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conv-title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.2s;
  margin: 0;
}

.conv-subtitle {
  font-size: 13px;
  color: #8e8e93;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-online {
  color: #52c41a;
}

.status-online::before {
  content: '● ';
}

.status-offline {
  color: #8e8e93;
}

/* 右侧按钮组 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #8e8e93;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
}

.action-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.action-btn:active {
  transform: scale(0.95);
}

.action-btn svg {
  width: 20px;
  height: 20px;
}

/* 主要按钮（开始授课） */
.primary-btn {
  background: #409eff;
  color: white;
}

.primary-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 成功按钮（进入课堂） */
.success-btn {
  background: #67c23a;
  color: white;
}

.success-btn:hover {
  background: #85ce61;
}
</style>
