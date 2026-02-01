<template>
  <div class="message-list" ref="messageContainer" @scroll="handleScroll">
    <div v-if="loading" class="loading">
      <i class="el-icon-loading"></i> 加载更多消息...
    </div>
    
    <div class="messages">
      <template v-for="(message, index) in messages" :key="message.id">
        <!-- 时间分隔线 -->
        <div v-if="shouldShowDateDivider(message, index)" class="date-divider">
          <span>{{ formatDateDivider(message.created_at) }}</span>
        </div>
        
        <!-- 消息项 -->
        <div 
          :class="['message-item', message.sender_id == currentUserId ? 'sent' : 'received']"
          @contextmenu.prevent="showContextMenu($event, message)"
        >
          <div v-if="message.sender_id != currentUserId" class="avatar">
            {{ message.sender_name?.substring(0, 1) }}
          </div>
          
          <div class="message-content">
            <div v-if="message.sender_id != currentUserId" class="sender-name">
              {{ message.sender_name }}
            </div>
            
            <!-- 回复的消息引用 -->
            <div v-if="message.reply_to" class="reply-reference" @click="scrollToMessage(message.reply_to.id)">
              <div class="reply-line"></div>
              <div class="reply-content">
                <div class="reply-sender">{{ message.reply_to.sender_name }}</div>
                <div class="reply-text">{{ message.reply_to.content }}</div>
              </div>
            </div>
            
            <div class="message-bubble" :title="formatFullTime(message.created_at)">
              <div v-if="message.message_type === 'text'" class="text-message">
                {{ message.content }}
              </div>
              <div v-else-if="message.message_type === 'image'" class="image-message">
                <img :src="message.media_url" @click="previewImage(message.media_url)" />
              </div>
              <div v-else-if="message.message_type === 'file'" class="file-message">
                <i class="el-icon-document"></i>
                <span>{{ message.file_name }}</span>
              </div>
              <div v-else-if="message.message_type === 'live_class_entry'" class="live-class-entry">
                <div class="entry-header">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                  </svg>
                  <span class="entry-title">{{ getClassEntryData(message).title }}</span>
                </div>
                <div v-if="getClassEntryData(message).description" class="entry-description">
                  {{ getClassEntryData(message).description }}
                </div>
                <div class="entry-footer">
                  <span class="entry-duration">预计 {{ getClassEntryData(message).duration }} 分钟</span>
                  <button class="entry-join-btn" @click="joinClass(getClassEntryData(message).lesson_id)">
                    进入课堂
                  </button>
                </div>
              </div>
              <div v-else-if="message.message_type === 'system'" class="system-message">
                {{ message.content }}
              </div>
              
              <div class="message-meta">
                <span class="time">{{ formatTime(message.created_at) }}</span>
                <span v-if="message.is_edited" class="edited">已编辑</span>
                <span v-if="message.sender_id == currentUserId" class="status">
                  <i v-if="message.pending" class="el-icon-loading"></i>
                  <i v-else-if="message.failed" class="el-icon-warning" style="color: #f56c6c"></i>
                  <i v-else-if="message.read_by && message.read_by.length > 0" class="el-icon-check read" style="color: #409eff"></i>
                  <i v-else class="el-icon-check"></i>
                </span>
              </div>
            </div>
          </div>
          
          <div v-if="message.sender_id == currentUserId" class="avatar">
            {{ currentUserName?.substring(0, 1) }}
          </div>
        </div>
      </template>
    </div>
    
    <!-- 正在输入指示器 -->
    <div v-if="typingUsers.length > 0" class="typing-indicator">
      <div class="typing-avatar"></div>
      <div class="typing-bubble">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
      <span class="typing-text">{{ typingUsers[0] }} 正在输入...</span>
    </div>
    
    <!-- 滚动到底部按钮 -->
    <transition name="fade">
      <div v-if="showScrollButton" class="scroll-to-bottom" @click="scrollToBottom">
        <i class="el-icon-arrow-down"></i>
        <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }}</span>
      </div>
    </transition>
    
    <!-- 右键菜单 -->
    <transition name="fade">
      <div v-if="contextMenu.visible" 
        class="context-menu" 
        :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
        @click="hideContextMenu"
      >
        <div class="menu-item" @click="replyMessage(contextMenu.message)">
          <i class="el-icon-chat-line-round"></i> 回复
        </div>
        <div class="menu-item" @click="copyMessage(contextMenu.message)">
          <i class="el-icon-document-copy"></i> 复制
        </div>
        <div v-if="contextMenu.message?.sender_id == currentUserId" 
          class="menu-item" @click="editMessage(contextMenu.message)">
          <i class="el-icon-edit"></i> 编辑
        </div>
        <div v-if="contextMenu.message?.sender_id == currentUserId" 
          class="menu-item danger" @click="deleteMessage(contextMenu.message)">
          <i class="el-icon-delete"></i> 删除
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const props = defineProps({
  conversationId: Number,
  messages: Array
})

const emit = defineEmits(['load-more', 'reply', 'edit', 'delete'])

const messageContainer = ref(null)
const loading = ref(false)
const currentUserId = localStorage.getItem('user_id')
const currentUserName = localStorage.getItem('user_name') || localStorage.getItem('real_name') || localStorage.getItem('username')
const showScrollButton = ref(false)
const unreadCount = ref(0)
const typingUsers = ref([])
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  message: null
})

let isNearBottom = true

const handleScroll = () => {
  if (!messageContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messageContainer.value
  
  // 检查是否在顶部（加载更多）
  if (scrollTop < 100 && !loading.value) {
    loading.value = true
    emit('load-more')
    setTimeout(() => loading.value = false, 1000)
  }
  
  // 检查是否接近底部
  isNearBottom = scrollHeight - scrollTop - clientHeight < 100
  showScrollButton.value = !isNearBottom
  
  if (isNearBottom) {
    unreadCount.value = 0
  }
}

const shouldShowDateDivider = (message, index) => {
  if (index === 0) return true
  
  const prevMessage = props.messages[index - 1]
  if (!prevMessage) return false
  
  const currentDate = new Date(message.created_at)
  const prevDate = new Date(prevMessage.created_at)
  
  // 如果日期不同，显示分隔线
  return currentDate.toDateString() !== prevDate.toDateString()
}

const formatDateDivider = (timestamp) => {
  const date = new Date(timestamp)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  
  if (date.toDateString() === today.toDateString()) {
    return '今天'
  } else if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  } else {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}年${month}月${day}日`
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatFullTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getClassEntryData = (message) => {
  try {
    return JSON.parse(message.content)
  } catch {
    return {
      lesson_id: '',
      title: '在线授课',
      description: '',
      duration: 45
    }
  }
}

const joinClass = (lessonId) => {
  const userRole = localStorage.getItem('user_role')
  if (userRole === 'teacher') {
    router.push(`/teacher/live-class/${lessonId}`)
  } else {
    router.push(`/student/live-class/${lessonId}`)
  }
}

const previewImage = (url) => {
  window.open(url, '_blank')
}

const scrollToBottom = (smooth = true) => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTo({
        top: messageContainer.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
      unreadCount.value = 0
    }
  })
}

const scrollToMessage = (messageId) => {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`)
  if (messageElement) {
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    messageElement.classList.add('highlight')
    setTimeout(() => messageElement.classList.remove('highlight'), 2000)
  }
}

// 右键菜单
const showContextMenu = (event, message) => {
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    message
  }
}

const hideContextMenu = () => {
  contextMenu.value.visible = false
}

const replyMessage = (message) => {
  emit('reply', message)
  hideContextMenu()
}

const copyMessage = (message) => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(message.content)
    ElMessage.success('已复制到剪贴板')
  }
  hideContextMenu()
}

const editMessage = (message) => {
  emit('edit', message)
  hideContextMenu()
}

const deleteMessage = async (message) => {
  hideContextMenu()
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    emit('delete', message)
  } catch {
    // 用户取消
  }
}

// 全局点击隐藏右键菜单
onMounted(() => {
  document.addEventListener('click', hideContextMenu)
  document.addEventListener('scroll', hideContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', hideContextMenu)
  document.removeEventListener('scroll', hideContextMenu)
})

// 监听消息变化
watch(() => props.messages.length, (newLen, oldLen) => {
  if (newLen > oldLen) {
    // 新消息
    if (isNearBottom) {
      scrollToBottom()
    } else {
      // 不在底部时，增加未读数
      const newMessage = props.messages[props.messages.length - 1]
      if (newMessage && newMessage.sender_id != currentUserId) {
        unreadCount.value++
      }
    }
  }
})

// 暴露方法给父组件
defineExpose({
  scrollToBottom,
  setTypingUsers: (users) => { typingUsers.value = users }
})
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 100px;
  background: linear-gradient(to bottom, #f0f2f5 0%, #e8eaed 100%);
  position: relative;
}

.loading {
  text-align: center;
  padding: 10px;
  color: #409eff;
  font-size: 14px;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 100%;
}

/* 日期分隔线 */
.date-divider {
  text-align: center;
  margin: 20px 0;
}

.date-divider span {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  font-size: 12px;
  color: #666;
}

/* 消息项 */
.message-item {
  display: flex;
  gap: 8px;
  max-width: 65%;
  align-items: flex-end;
  animation: messageSlideIn 0.2s ease-out;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.sent {
  align-self: flex-end;
  flex-direction: row;
}

.message-item.received {
  align-self: flex-start;
}

.message-item:hover .message-bubble {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-item.highlight .message-bubble {
  animation: highlight 1s ease;
}

@keyframes highlight {
  0%, 100% { background-color: inherit; }
  50% { background-color: #fff3cd; }
}

/* 头像 */
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 消息内容 */
.message-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-width: 100%;
}

.sender-name {
  font-size: 12px;
  color: #409eff;
  font-weight: 600;
  padding-left: 12px;
  margin-bottom: 2px;
}

/* 回复引用 */
.reply-reference {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px 8px 0 0;
  margin-bottom: -2px;
  cursor: pointer;
  transition: background 0.2s;
}

.reply-reference:hover {
  background: rgba(0, 0, 0, 0.08);
}

.reply-line {
  width: 3px;
  background: #409eff;
  border-radius: 2px;
}

.reply-content {
  flex: 1;
  overflow: hidden;
}

.reply-sender {
  font-size: 12px;
  color: #409eff;
  font-weight: 600;
  margin-bottom: 2px;
}

.reply-text {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 消息气泡 */
.message-bubble {
  padding: 10px 14px;
  border-radius: 18px;
  word-wrap: break-word;
  transition: all 0.2s;
  position: relative;
}

.message-item.received .message-bubble {
  background: #fff;
  color: #333;
  border-radius: 18px 18px 18px 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-item.sent .message-bubble {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.3);
}

.text-message {
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
}

.image-message img {
  max-width: 100%;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.image-message img:hover {
  transform: scale(1.02);
}

.file-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.system-message {
  font-size: 13px;
  font-style: italic;
  color: #888;
}

/* 课堂入口消息 */
.live-class-entry {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border-radius: 12px;
  min-width: 280px;
}

.entry-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.entry-header svg {
  flex-shrink: 0;
}

.entry-title {
  font-size: 16px;
  font-weight: 600;
}

.entry-description {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 12px;
  line-height: 1.5;
}

.entry-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.entry-duration {
  font-size: 13px;
  opacity: 0.8;
}

.entry-join-btn {
  padding: 8px 16px;
  background: white;
  color: #667eea;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.entry-join-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
}

.entry-join-btn:active {
  transform: translateY(0);
}

/* 消息元信息 */
.message-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  margin-top: 2px;
}

.message-item.received .message-meta {
  color: rgba(0, 0, 0, 0.4);
}

.message-item.sent .message-meta {
  color: rgba(255, 255, 255, 0.8);
  justify-content: flex-end;
}

.edited {
  font-style: italic;
}

.status {
  display: flex;
  align-items: center;
}

.status .read {
  font-weight: bold;
}

/* 正在输入指示器 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  animation: fadeIn 0.3s;
}

.typing-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #ddd;
}

.typing-bubble {
  padding: 10px 14px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #999;
  animation: typingDot 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingDot {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-8px);
  }
}

.typing-text {
  font-size: 13px;
  color: #666;
}

/* 滚动到底部按钮 */
.scroll-to-bottom {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transition: all 0.3s;
  z-index: 10;
}

.scroll-to-bottom:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
}

.scroll-to-bottom .unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: #f56c6c;
  color: white;
  border-radius: 10px;
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 右键菜单 */
.context-menu {
  position: fixed;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 6px 0;
  min-width: 140px;
  z-index: 1000;
  animation: fadeIn 0.15s;
}

.menu-item {
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;
}

.menu-item:hover {
  background: #f5f5f5;
}

.menu-item.danger {
  color: #f56c6c;
}

.menu-item.danger:hover {
  background: #fef0f0;
}

/* 动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 滚动条样式 */
.message-list::-webkit-scrollbar {
  width: 8px;
}

.message-list::-webkit-scrollbar-track {
  background: transparent;
}

.message-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>
