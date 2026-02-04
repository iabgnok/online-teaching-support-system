<template>
  <div class="message-input-container" 
    @drop.prevent="handleDrop"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    :class="{ dragging: isDragging }"
  >
    <!-- @提及选择器 -->
    <MentionSelector
      :conversation-id="conversationId"
      :show="showMentionSelector"
      :keyword="mentionKeyword"
      :position="mentionPosition"
      @select="handleMentionSelect"
      ref="mentionSelectorRef"
    />

    <!-- 回复消息预览 -->
    <div v-if="replyTo" class="reply-preview">
      <div class="reply-content">
        <div class="reply-header">
          <i class="el-icon-chat-line-round"></i>
          <span>回复 {{ replyTo.sender_name }}</span>
        </div>
        <div class="reply-text">{{ replyTo.content }}</div>
      </div>
      <el-button icon="el-icon-close" circle size="small" @click="cancelReply"></el-button>
    </div>
    
    <!-- 编辑消息预览 -->
    <div v-if="editingMessage" class="edit-preview">
      <div class="edit-content">
        <div class="edit-header">
          <i class="el-icon-edit"></i>
          <span>编辑消息</span>
        </div>
      </div>
      <el-button icon="el-icon-close" circle size="small" @click="cancelEdit"></el-button>
    </div>
    
    <!-- Telegram风格输入框 -->
    <div class="telegram-input">
      <!-- 左侧按钮组 -->
      <div class="left-buttons">
        <!-- 功能菜单按钮（+号） -->
        <el-popover
          placement="top-start"
          :width="220"
          trigger="click"
        >
          <template #reference>
            <button class="icon-btn plus-btn" title="更多功能">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="16"></line>
                <line x1="8" y1="12" x2="16" y2="12"></line>
              </svg>
            </button>
          </template>
          <div class="function-menu">
            <!-- 通用功能 -->
            <el-upload
              ref="imageUpload"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :before-upload="beforeImageUpload"
              :on-success="handleImageSuccess"
              accept="image/*"
            >
              <div class="menu-item">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                <span>发送图片</span>
              </div>
            </el-upload>
            
            <el-upload
              ref="fileUpload"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :before-upload="beforeFileUpload"
              :on-success="handleFileSuccess"
            >
              <div class="menu-item">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                  <polyline points="13 2 13 9 20 9"></polyline>
                </svg>
                <span>发送文件</span>
              </div>
            </el-upload>

            <!-- 课堂专属功能（仅在课堂讨论区显示） -->
            <template v-if="showClassroomFeatures">
              <!-- 教师专属功能 -->
              <template v-if="userRole === 'teacher'">
                <div class="menu-divider"></div>
                <div class="menu-item" @click="handleStartAttendance">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                  </svg>
                  <span>发起考勤</span>
                </div>
                <div class="menu-item" @click="handlePublishTask">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                  </svg>
                  <span>发布任务</span>
                </div>
                <div class="menu-item" @click="handleShareBoard">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                  </svg>
                  <span>分享板书</span>
                </div>
                <div class="menu-item" @click="handleScreenShare">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                    <line x1="8" y1="21" x2="16" y2="21"></line>
                    <line x1="12" y1="17" x2="12" y2="21"></line>
                  </svg>
                  <span>屏幕共享</span>
                </div>
              </template>

              <!-- 学生专属功能 -->
              <template v-if="userRole === 'student'">
                <div class="menu-divider"></div>
                <div class="menu-item" @click="handleRaiseHand">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"></path>
                    <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"></path>
                    <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"></path>
                    <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"></path>
                  </svg>
                  <span>举手发言</span>
                </div>
                <div class="menu-item" @click="handleAskQuestion">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                  </svg>
                  <span>提问</span>
                </div>
              </template>
            </template>
          </div>
        </el-popover>
        
        <!-- 表情按钮 -->
        <el-popover
          placement="top-start"
          :width="320"
          trigger="click"
        >
          <template #reference>
            <button class="icon-btn" title="表情">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
                <line x1="9" y1="9" x2="9.01" y2="9"></line>
                <line x1="15" y1="9" x2="15.01" y2="9"></line>
              </svg>
            </button>
          </template>
          <div class="emoji-picker">
            <span v-for="emoji in emojis" :key="emoji" 
              class="emoji-item" 
              @click="insertEmoji(emoji)"
            >
              {{ emoji }}
            </span>
          </div>
        </el-popover>
      </div>
      
      <!-- 中间：输入框 -->
      <div class="input-box">
        <textarea
          ref="textareaRef"
          v-model="messageContent"
          class="message-textarea"
          :placeholder="placeholder"
          :disabled="isInputDisabled"
          @keydown.enter.exact.prevent="handleEnterKey"
          @keydown.shift.enter="handleNewLine"
          @keydown="handleKeyDown"
          @input="handleInput"
          @focus="handleFocus"
          @blur="handleBlur"
        />
      </div>
      
      <!-- 右侧：发送按钮 -->
      <button 
        class="icon-btn send-btn" 
        :class="{ active: canSend }"
        @click="sendMessage"
        :disabled="!canSend"
        :title="editingMessage ? '保存' : '发送'"
      >
        <svg v-if="editingMessage" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </div>
    
    <!-- 拖放遮罩 -->
    <div v-if="isDragging" class="drop-overlay">
      <i class="el-icon-upload"></i>
      <p>释放以发送文件</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import MentionSelector from './MentionSelector.vue'

const props = defineProps({
  conversationId: Number,
  replyTo: Object,
  editingMessage: Object,
  conversationSubtype: String,  // 'channel', 'normal', 'discussion'
  discussionMode: Boolean,  // 是否在讨论模式中
  showClassroomFeatures: {  // 是否显示课堂专属功能（考勤、任务、板书等）
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send', 'cancel-reply', 'cancel-edit', 'typing', 'screen-share', 'start-poll', 'assign-task', 'raise-hand', 'ask-question', 'start-attendance', 'publish-task', 'share-board'])

const messageContent = ref('')
const textareaRef = ref(null)
const mentionSelectorRef = ref(null)
const isDragging = ref(false)
const isTyping = ref(false)
let typingTimer = null

// 获取用户角色
const userRole = localStorage.getItem('user_role')

// @提及相关
const showMentionSelector = ref(false)
const mentionKeyword = ref('')
const mentionPosition = ref({ top: 0, left: 0 })
const mentionStartPos = ref(-1)

// 判断输入框是否应该禁用
const isInputDisabled = computed(() => {
  // 如果是频道且不在讨论模式，学生无法发送消息
  if (props.conversationSubtype === 'channel' && !props.discussionMode && userRole !== 'teacher') {
    return true
  }
  return false
})

const uploadUrl = computed(() => `/api/v1/chat/upload`)
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}))

const placeholder = computed(() => {
  if (isInputDisabled.value) return '只有教师可以在频道中发布消息，您可以点击消息下方的"讨论"按钮参与评论'
  if (props.editingMessage) return '编辑消息...'
  if (props.replyTo) return `回复 ${props.replyTo.sender_name}...`
  return '输入消息... (Shift+Enter换行, Enter发送)'
})

const canSend = computed(() => {
  return !isInputDisabled.value && messageContent.value.trim().length > 0
})

// Emoji 列表
const emojis = [
  '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣',
  '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰',
  '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜',
  '🤪', '🤨', '🧐', '🤓', '😎', '🥸', '🤩', '🥳',
  '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️',
  '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤',
  '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱',
  '😨', '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫',
  '🥱', '😶', '😐', '😑', '😬', '🙄', '😯', '😦',
  '😧', '😮', '😲', '🤐', '🤤', '😴', '😪', '😵',
  '👍', '👎', '👏', '🙌', '🤝', '🙏', '❤️', '💔',
  '💕', '💖', '💗', '💞', '💓', '💟', '❤️‍🔥', '❤️‍🩹',
  '👌', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉',
  '👆', '👇', '☝️', '✋', '🤚', '🖐️', '👊', '✊'
]

const sendMessage = () => {
  const content = messageContent.value.trim()
  if (!content) {
    ElMessage.warning('消息内容不能为空')
    return
  }
  
  const messageData = {
    content,
    message_type: 'text'
  }
  
  if (props.replyTo) {
    messageData.reply_to_id = props.replyTo.id
  }
  
  if (props.editingMessage) {
    messageData.message_id = props.editingMessage.id
    emit('send', { ...messageData, isEdit: true })
  } else {
    emit('send', messageData)
  }
  
  messageContent.value = ''
  stopTyping()
  resetTextareaHeight()
}

// 教师功能处理
const handleStartAttendance = () => {
  emit('start-attendance')
  ElMessage.success('发起考勤')
}

const handlePublishTask = () => {
  emit('publish-task')
  ElMessage.success('发布任务')
}

const handleShareBoard = () => {
  emit('share-board')
  ElMessage.success('分享板书')
}

const handleScreenShare = () => {
  emit('screen-share')
  ElMessage.success('屏幕共享功能')
}

const handleStartPoll = () => {
  emit('start-poll')
  ElMessage.success('发起投票功能')
}

const handleAssignTask = () => {
  emit('assign-task')
  ElMessage.success('布置作业功能')
}

// 学生功能处理
const handleRaiseHand = () => {
  emit('raise-hand')
  ElMessage.success('已举手发言')
}

const handleAskQuestion = () => {
  emit('ask-question')
  ElMessage.success('提问功能')
}

const handleNewLine = (e) => {
  // Shift+Enter 已经会自动添加换行
  // 这里只需要调整高度
  nextTick(() => adjustTextareaHeight())
}

const handleInput = () => {
  adjustTextareaHeight()
  
  // 检测@符号
  checkMentionTrigger()
  
  // 发送正在输入信号
  if (!isTyping.value) {
    isTyping.value = true
    emit('typing', true)
  }
  
  // 重置定时器
  clearTimeout(typingTimer)
  typingTimer = setTimeout(() => {
    stopTyping()
  }, 3000)
}

// 检测是否触发@提及
const checkMentionTrigger = () => {
  const textarea = textareaRef.value
  if (!textarea) return
  
  const cursorPos = textarea.selectionStart
  const textBeforeCursor = messageContent.value.substring(0, cursorPos)
  
  // 查找最近的 @
  const lastAtIndex = textBeforeCursor.lastIndexOf('@')
  
  if (lastAtIndex !== -1) {
    // 检查@后面是否有空格或换行
    const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1)
    if (!/[\s\n]/.test(textAfterAt)) {
      // 显示提及选择器
      mentionStartPos.value = lastAtIndex
      mentionKeyword.value = textAfterAt
      showMentionSelector.value = true
      
      // 计算选择器位置
      updateMentionPosition()
      return
    }
  }
  
  // 关闭选择器
  showMentionSelector.value = false
}

// 更新@选择器位置
const updateMentionPosition = () => {
  const textarea = textareaRef.value
  if (!textarea) return
  
  const rect = textarea.getBoundingClientRect()
  mentionPosition.value = {
    top: rect.top - 10,  // 在输入框上方
    left: rect.left
  }
}

// 处理键盘事件
const handleKeyDown = (e) => {
  if (showMentionSelector.value) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      mentionSelectorRef.value?.selectNext()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      mentionSelectorRef.value?.selectPrevious()
    } else if (e.key === 'Escape') {
      showMentionSelector.value = false
    }
  }
}

// 处理Enter键
const handleEnterKey = () => {
  if (showMentionSelector.value) {
    // 如果@选择器打开，选择当前项
    mentionSelectorRef.value?.selectCurrent()
  } else {
    // 否则发送消息
    sendMessage()
  }
}

// 处理@提及选择
const handleMentionSelect = (member) => {
  const textarea = textareaRef.value
  if (!textarea || mentionStartPos.value === -1) return
  
  const before = messageContent.value.substring(0, mentionStartPos.value)
  const after = messageContent.value.substring(textarea.selectionStart)
  
  // 插入@用户名
  messageContent.value = before + `@${member.username} ` + after
  
  // 设置光标位置
  nextTick(() => {
    const newPos = before.length + member.username.length + 2
    textarea.setSelectionRange(newPos, newPos)
    textarea.focus()
  })
  
  // 关闭选择器
  showMentionSelector.value = false
  mentionStartPos.value = -1
}

const handleFocus = () => {
  // 聚焦时可以做一些操作
}

const handleBlur = () => {
  stopTyping()
}

const stopTyping = () => {
  if (isTyping.value) {
    isTyping.value = false
    emit('typing', false)
  }
}

const adjustTextareaHeight = () => {
  if (!textareaRef.value) return
  
  const textarea = textareaRef.value
  textarea.style.height = 'auto'
  const newHeight = Math.min(Math.max(textarea.scrollHeight, 40), 200)
  textarea.style.height = newHeight + 'px'
}

const resetTextareaHeight = () => {
  if (!textareaRef.value) return
  textareaRef.value.style.height = '40px'
}

const insertEmoji = (emoji) => {
  const textarea = textareaRef.value
  const startPos = textarea.selectionStart
  const endPos = textarea.selectionEnd
  const textBefore = messageContent.value.substring(0, startPos)
  const textAfter = messageContent.value.substring(endPos)
  
  messageContent.value = textBefore + emoji + textAfter
  
  nextTick(() => {
    textarea.focus()
    const newPos = startPos + emoji.length
    textarea.setSelectionRange(newPos, newPos)
    adjustTextareaHeight()
  })
}

const cancelReply = () => {
  emit('cancel-reply')
}

const cancelEdit = () => {
  messageContent.value = ''
  emit('cancel-edit')
  resetTextareaHeight()
}

// 文件上传
const beforeImageUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }
  return true
}

const beforeFileUpload = (file) => {
  const isLt20M = file.size / 1024 / 1024 < 20
  
  if (!isLt20M) {
    ElMessage.error('文件大小不能超过 20MB！')
    return false
  }
  return true
}

const handleImageSuccess = (response) => {
  emit('send', {
    message_type: 'image',
    media_url: response.url,
    content: '[\u56fe\u7247]'
  })
}

const handleFileSuccess = (response) => {
  emit('send', {
    message_type: 'file',
    file_url: response.url,
    file_name: response.filename,
    content: `[\u6587\u4ef6] ${response.filename}`
  })
}

const handleDrop = (e) => {
  isDragging.value = false
  const files = e.dataTransfer.files
  
  if (files.length === 0) return
  
  const file = files[0]
  
  if (file.type.startsWith('image/')) {
    // 上传图片
    if (beforeImageUpload(file)) {
      uploadFile(file, 'image')
    }
  } else {
    // 上传文件
    if (beforeFileUpload(file)) {
      uploadFile(file, 'file')
    }
  }
}

const uploadFile = async (file, type) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('conversation_id', props.conversationId)
  
  try {
    const response = await api.post('/chat/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (type === 'image') {
      handleImageSuccess(response.data)
    } else {
      handleFileSuccess(response.data)
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败')
  }
}

// 监听编辑消息
watch(() => props.editingMessage, (newVal) => {
  if (newVal) {
    messageContent.value = newVal.content
    nextTick(() => {
      textareaRef.value?.focus()
      adjustTextareaHeight()
    })
  }
})

// 暴露方法
defineExpose({
  focus: () => textareaRef.value?.focus(),
  clear: () => {
    messageContent.value = ''
    resetTextareaHeight()
  }
})
</script>

<style scoped>
.message-input-container {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 28px 20px 28px;
  background: transparent;
  gap: 10px;
  pointer-events: none;
}

.message-input-container > * {
  pointer-events: auto;
}

.message-input-container.dragging {
  background: #f0f9ff;
  border-color: #409eff;
}

/* 回复预览 */
.reply-preview,
.edit-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f5f7fa;
  border-left: 3px solid #409eff;
  border-radius: 4px;
}

.reply-content,
.edit-content {
  flex: 1;
}

.reply-header,
.edit-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #409eff;
  font-weight: 600;
  margin-bottom: 4px;
}

.reply-text {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Telegram风格输入框 */
.telegram-input {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  padding: 4px 8px;
  background: #ffffff;
  border-radius: 22px;
  gap: 4px;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.telegram-input:focus-within {
  background: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

/* 左侧按钮组 */
.left-buttons {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

/* 通用圆形图标按钮 */
.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #8e8e93;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
  padding: 0;
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

.icon-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.06);
  transform: scale(1.08);
}

.icon-btn:active {
  transform: scale(0.95);
}

/* 输入框容器 */
.input-box {
  flex: 1;
  min-width: 0;
  max-height: 120px;
  display: flex;
  align-items: center;
  padding: 2px 4px;
}

/* 发送按钮 */
.send-btn {
  background: #409eff !important;
  color: white !important;
}

.send-btn:hover:not(:disabled) {
  background: #66b1ff !important;
}

.send-btn.active {
  animation: pulse 0.5s;
}

.send-btn:disabled {
  background: #e4e7ed !important;
  color: #c0c4cc !important;
  cursor: not-allowed;
}

.send-btn:disabled:hover {
  transform: none;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

/* 附件菜单（已废弃，使用function-menu） */
.attachment-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
}

/* 功能菜单 */
.function-menu {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
  user-select: none;
}

.menu-item:hover {
  background: #ecf5ff;
}

.menu-item svg {
  flex-shrink: 0;
  color: #409eff;
  transition: transform 0.2s;
}

.menu-item:hover svg {
  transform: scale(1.1);
}

.menu-item i {
  font-size: 20px;
  color: #409eff;
}

.menu-item span {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

/* 菜单分隔线 */
.menu-divider {
  height: 1px;
  background: #e4e7ed;
  margin: 4px 0;
}

/* Plus按钮特殊样式 */
.plus-btn {
  position: relative;
}

.plus-btn::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s;
}

.plus-btn:hover::before {
  opacity: 0.1;
}

/* Emoji 选择器 */
.emoji-picker {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
}

.emoji-item {
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  transition: background 0.2s;
}

.emoji-item:hover {
  background: #f5f5f5;
  transform: scale(1.2);
}

/* 输入框文本域 */
.message-textarea {
  width: 100%;
  min-height: 18px;
  max-height: 120px;
  padding: 0;
  border: none;
  background: transparent;
  font-size: 14px;
  line-height: 18px;
  resize: none;
  font-family: inherit;
  outline: none;
  color: #303133;
}

.message-textarea::placeholder {
  color: #adb5bd;
}

.message-textarea::-webkit-scrollbar {
  width: 4px;
}

.message-textarea::-webkit-scrollbar-track {
  background: transparent;
}

.message-textarea::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

.message-textarea::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

/* 拖放遮罩 */
.drop-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(64, 158, 255, 0.1);
  border: 2px dashed #409eff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: none;
}

.drop-overlay i {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 10px;
}

.drop-overlay p {
  font-size: 16px;
  color: #409eff;
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .message-input-container {
    padding: 8px 12px;
  }
  
  .emoji-picker {
    grid-template-columns: repeat(6, 1fr);
  }
}</style>
