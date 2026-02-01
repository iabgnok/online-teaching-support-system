<template>
  <div class="chat-window">
    <!-- 左侧：对话列表 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <h2>消息</h2>
        <button class="btn-new-chat" @click="showNewChatDialog = true" title="新建对话">
          <i class="el-icon-plus"></i>
        </button>
      </div>
      
      <div class="search-box">
        <el-input 
          v-model="searchQuery" 
          placeholder="搜索对话或消息..." 
          prefix-icon="el-icon-search"
          clearable
        />
      </div>
      
      <div class="conversation-list">
        <ConversationItem 
          v-for="conv in filteredConversations" 
          :key="conv.id"
          :conversation="conv"
          :active="currentConversationId === conv.id"
          @click="selectConversation(conv.id)"
        />
        
        <div v-if="conversations.length === 0" class="empty-state">
          <p>暂无对话</p>
          <el-button type="primary" size="small" @click="showNewChatDialog = true">
            开始聊天
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 中间：聊天主区域 -->
    <div class="chat-main">
      <template v-if="currentConversation">
        <ChatHeader 
          :conversation="currentConversation"
          @show-info="showInfoPanel = !showInfoPanel"
        />
        
        <MessageList 
          ref="messageList"
          :conversation-id="currentConversationId"
          :messages="currentMessages"
          @load-more="loadMoreMessages"
          @reply="handleReply"
          @edit="handleEdit"
          @delete="handleDelete"
        />
        
        <MessageInput 
          ref="messageInput"
          :conversation-id="currentConversationId"
          :reply-to="replyToMessage"
          :editing-message="editingMessage"
          @send="handleSendMessage"
          @cancel-reply="replyToMessage = null"
          @cancel-edit="editingMessage = null"
          @typing="handleTyping"
        />
      </template>
      
      <div v-else class="no-conversation">
        <div class="welcome-message">
          <i class="el-icon-chat-dot-round"></i>
          <h3>选择一个对话开始聊天</h3>
          <p>或创建新的对话</p>
        </div>
      </div>
    </div>
    
    <!-- 右侧：信息面板 -->
    <transition name="slide">
      <div v-if="showInfoPanel && currentConversation" class="chat-info-panel">
        <ChatInfoPanel 
          :conversation="currentConversation"
          @close="showInfoPanel = false"
          @search="handleSearch"
          @updated="loadConversations"
        />
      </div>
    </transition>
    
    <!-- 新建对话对话框 -->
    <el-dialog 
      v-model="showNewChatDialog" 
      title="新建对话" 
      width="500px"
    >
      <el-form :model="newChatForm" label-width="100px">
        <el-form-item label="对话类型">
          <el-radio-group v-model="newChatForm.type" @change="handleTypeChange">
            <el-radio label="private">👤 私聊</el-radio>
            <el-radio label="group">👥 群聊</el-radio>
            <el-radio label="class_group">🏫 班级群组</el-radio>
            <el-radio label="course_group">📚 课程群组</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item v-if="newChatForm.type === 'group'" label="群组名称">
          <el-input v-model="newChatForm.title" placeholder="输入群组名称" />
        </el-form-item>
        
        <el-form-item v-if="newChatForm.type === 'class_group' || newChatForm.type === 'course_group'" label="选择班级">
          <el-select 
            v-model="newChatForm.classId" 
            filterable 
            placeholder="选择班级"
            style="width: 100%"
            @focus="loadClasses"
          >
            <el-option
              v-for="cls in classList"
              :key="cls.class_id"
              :label="cls.class_name"
              :value="cls.class_id"
            />
          </el-select>
          <div class="form-hint">
            <span v-if="newChatForm.type === 'class_group'">班级群组将自动添加所有学生和教师</span>
            <span v-else>课程群组只包含教师，用于教学讨论</span>
          </div>
        </el-form-item>
        
        <el-form-item v-if="newChatForm.type === 'private' || newChatForm.type === 'group'" label="添加成员">
          <el-select 
            v-model="newChatForm.members" 
            multiple 
            filterable 
            remote
            reserve-keyword
            placeholder="搜索用户"
            :remote-method="searchUsers"
            :loading="searchingUsers"
            style="width: 100%"
          >
            <el-option
              v-for="user in userSearchResults"
              :key="user.id"
              :label="`${user.real_name} (${user.username})`"
              :value="user.id"
            >
              <span>{{ user.real_name }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ user.username }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showNewChatDialog = false">取消</el-button>
        <el-button type="primary" @click="createConversation">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import io from 'socket.io-client'
import api from '../api'
import ConversationItem from '../components/ConversationItem.vue'
import ChatHeader from '../components/ChatHeader.vue'
import MessageList from '../components/MessageList.vue'
import MessageInput from '../components/MessageInput.vue'
import ChatInfoPanel from '../components/ChatInfoPanel.vue'

// 状态
const conversations = ref([])
const currentConversationId = ref(null)
const currentMessages = ref([])
const showInfoPanel = ref(false)
const searchQuery = ref('')
const showNewChatDialog = ref(false)
const searchingUsers = ref(false)
const userSearchResults = ref([])
const replyToMessage = ref(null)
const editingMessage = ref(null)
const messageList = ref(null)
const messageInput = ref(null)

// Socket连接
let socket = null
const userId = localStorage.getItem('user_id')
const userName = localStorage.getItem('user_name') || localStorage.getItem('real_name') || localStorage.getItem('username')

// 新建对话表单
const newChatForm = ref({
  type: 'private',
  title: '',
  members: [],
  classId: null
})

const classList = ref([])

// 计算属性
const currentConversation = computed(() => {
  return conversations.value.find(c => c.id === currentConversationId.value)
})

const filteredConversations = computed(() => {
  if (!searchQuery.value) return conversations.value
  
  const query = searchQuery.value.toLowerCase()
  return conversations.value.filter(conv => {
    return conv.title?.toLowerCase().includes(query) ||
           conv.last_message?.content?.toLowerCase().includes(query)
  })
})

// 生命周期
onMounted(() => {
  loadConversations()
  initSocket()
})

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
  }
})

// WebSocket初始化
const initSocket = () => {
  socket = io({
    transports: ['websocket'],
    reconnection: true
  })
  
  socket.on('connect', () => {
    console.log('Socket connected')
    socket.emit('chat:connect', { user_id: userId })
  })
  
  socket.on('chat:new_message', (message) => {
    handleNewMessage(message)
  })
  
  socket.on('chat:message_sent', (data) => {
    // 服务器确认消息已发送，更新临时消息
    if (data.temp_id) {
      const tempIndex = currentMessages.value.findIndex(m => m.temp_id === data.temp_id)
      if (tempIndex !== -1) {
        currentMessages.value[tempIndex].id = data.id
        currentMessages.value[tempIndex].created_at = data.created_at
        currentMessages.value[tempIndex].pending = false
      }
    }
  })
  
  socket.on('chat:message_status', (status) => {
    updateMessageStatus(status)
  })
  
  socket.on('chat:user_typing', (data) => {
    if (data.conversation_id === currentConversationId.value && data.user_id != userId) {
      if (messageList.value) {
        messageList.value.setTypingUsers([data.user_name])
      }
    }
  })
  
  socket.on('chat:user_stop_typing', (data) => {
    if (data.conversation_id === currentConversationId.value) {
      if (messageList.value) {
        messageList.value.setTypingUsers([])
      }
    }
  })
  
  socket.on('chat:message_deleted', (data) => {
    removeMessage(data.message_id)
  })
  
  socket.on('chat:message_edited', (data) => {
    updateMessage(data)
  })
  
  socket.on('chat:user_online', (data) => {
    updateUserOnlineStatus(data.user_id, true)
  })
  
  socket.on('chat:user_offline', (data) => {
    updateUserOnlineStatus(data.user_id, false)
  })
}

// 加载对话列表
const loadConversations = async () => {
  try {
    const response = await api.get('/chat/conversations')
    conversations.value = response.data
  } catch (error) {
    console.error('加载对话列表失败:', error)
    
    // 如果是401错误，提示用户重新登录
    if (error.response && error.response.status === 401) {
      ElMessage.error({
        message: '登录已过期，请重新登录',
        duration: 3000,
        onClose: () => {
          localStorage.clear()
          window.location.href = '/login'
        }
      })
    } else {
      ElMessage.error('加载对话列表失败')
    }
  }
}

// 选择对话
const selectConversation = async (conversationId) => {
  currentConversationId.value = conversationId
  
  // 加载消息
  await loadMessages(conversationId)
  
  // 加入对话房间
  if (socket) {
    socket.emit('chat:join', {
      conversation_id: conversationId,
      user_id: userId
    })
  }
  
  // 标记已读
  markConversationRead(conversationId)
}

// 加载消息
const loadMessages = async (conversationId, beforeId = null) => {
  try {
    const params = beforeId ? { before_id: beforeId } : {}
    const response = await api.get(`/chat/conversations/${conversationId}/messages`, { params })
    
    if (beforeId) {
      // 加载更多历史消息
      currentMessages.value = [...response.data.messages, ...currentMessages.value]
    } else {
      // 首次加载
      currentMessages.value = response.data.messages
    }
    
    return response.data.has_more
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  }
}

// 加载更多消息
const loadMoreMessages = async () => {
  if (currentMessages.value.length === 0) return
  
  const firstMessageId = currentMessages.value[0].id
  await loadMessages(currentConversationId.value, firstMessageId)
}

// 发送消息
const handleSendMessage = async (messageData) => {
  if (!socket || !currentConversationId.value) return
  
  // 如果是编辑消息
  if (messageData.isEdit) {
    try {
      await api.put(`/chat/messages/${messageData.message_id}`, {
        content: messageData.content
      })
      
      // 通过Socket广播编辑
      socket.emit('chat:edit_message', {
        message_id: messageData.message_id,
        conversation_id: currentConversationId.value,
        content: messageData.content
      })
      
      editingMessage.value = null
      ElMessage.success('消息已编辑')
    } catch (error) {
      console.error('编辑消息失败:', error)
      ElMessage.error('编辑消息失败')
    }
    return
  }
  
  const tempId = Date.now() // 临时ID用于匹配
  
  // 乐观更新UI
  const optimisticMessage = {
    id: tempId,
    temp_id: tempId,
    sender_id: userId,
    sender_name: userName,
    content: messageData.content,
    message_type: messageData.message_type || 'text',
    created_at: new Date().toISOString(),
    pending: true
  }
  
  // 添加回复引用
  if (replyToMessage.value) {
    optimisticMessage.reply_to = {
      id: replyToMessage.value.id,
      sender_name: replyToMessage.value.sender_name,
      content: replyToMessage.value.content
    }
  }
  
  currentMessages.value.push(optimisticMessage)
  
  // 通过Socket发送
  socket.emit('chat:send_message', {
    conversation_id: currentConversationId.value,
    user_id: userId,
    temp_id: tempId,
    reply_to_id: replyToMessage.value?.id,
    ...messageData
  })
  
  // 清除回复状态
  replyToMessage.value = null
}

// 处理新消息
const handleNewMessage = (message) => {
  // 更新对话列表中的最后消息
  const conv = conversations.value.find(c => c.id === message.conversation_id)
  if (conv) {
    conv.last_message = {
      content: message.content,
      sender_name: message.sender_name,
      created_at: message.created_at,
      message_type: message.message_type
    }
    conv.updated_at = message.created_at
    
    // 如果不是当前对话，增加未读数
    if (message.conversation_id !== currentConversationId.value && message.sender_id !== userId) {
      conv.unread_count = (conv.unread_count || 0) + 1
    }
    
    // 对话列表排序
    conversations.value.sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return b.is_pinned - a.is_pinned
      return new Date(b.updated_at) - new Date(a.updated_at)
    })
  }
  
  // 如果是当前对话，添加到消息列表
  if (message.conversation_id === currentConversationId.value) {
    // 如果是自己发送的消息，检查是否已经有临时消息
    if (message.sender_id == userId) {  // 使用==而不是===，因为可能类型不同
      // 查找是否已有临时消息或相同ID的消息
      const existingIndex = currentMessages.value.findIndex(m => 
        m.id === message.id || (m.temp_id && m.pending)
      )
      if (existingIndex !== -1) {
        // 替换临时消息
        currentMessages.value.splice(existingIndex, 1, {
          ...message,
          pending: false
        })
        return
      }
    }
    
    // 其他情况，检查是否已存在该消息（避免重复）
    const exists = currentMessages.value.some(m => m.id === message.id)
    if (!exists) {
      currentMessages.value.push(message)
    }
    
    // 滚动到底部
    setTimeout(() => {
      scrollToBottom()
    }, 100)
    
    // 发送已读回执
    if (message.sender_id != userId) {  // 使用!=而不是!==
      socket.emit('chat:message_read', {
        message_id: message.id,
        user_id: userId,
        conversation_id: message.conversation_id
      })
    }
  }
}

// 更新消息状态
const updateMessageStatus = (status) => {
  const message = currentMessages.value.find(m => m.id === status.message_id)
  if (message) {
    if (!message.read_by) message.read_by = []
    if (status.status === 'read' && !message.read_by.includes(status.user_id)) {
      message.read_by.push(status.user_id)
    }
  }
}

// 标记对话已读
const markConversationRead = async (conversationId) => {
  try {
    await api.post(`/chat/conversations/${conversationId}/read_all`)
    
    // 更新本地未读数
    const conv = conversations.value.find(c => c.id === conversationId)
    if (conv) {
      conv.unread_count = 0
    }
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

// 搜索用户
const searchUsers = async (query) => {
  if (!query || query.length < 2) {
    userSearchResults.value = []
    return
  }
  
  searchingUsers.value = true
  try {
    const response = await api.get('/users/search', { params: { q: query } })
    userSearchResults.value = response.data
  } catch (error) {
    console.error('搜索用户失败:', error)
  } finally {
    searchingUsers.value = false
  }
}

// 创建对话
const createConversation = async () => {
  // 验证
  if (newChatForm.value.type === 'private' && newChatForm.value.members.length !== 1) {
    ElMessage.warning('私聊只能选择一个用户')
    return
  }
  
  if (newChatForm.value.type === 'group' && !newChatForm.value.title) {
    ElMessage.warning('请输入群组名称')
    return
  }
  
  if ((newChatForm.value.type === 'class_group' || newChatForm.value.type === 'course_group') && !newChatForm.value.classId) {
    ElMessage.warning('请选择班级')
    return
  }
  
  if ((newChatForm.value.type === 'private' || newChatForm.value.type === 'group') && newChatForm.value.members.length === 0) {
    ElMessage.warning('请选择成员')
    return
  }
  
  try {
    const requestData = {
      type: newChatForm.value.type,
      title: newChatForm.value.title,
      member_ids: newChatForm.value.members
    }
    
    // 班级群组和课程群组需要class_id
    if (newChatForm.value.type === 'class_group' || newChatForm.value.type === 'course_group') {
      requestData.class_id = newChatForm.value.classId
    }
    
    const response = await api.post('/chat/conversations', requestData)
    
    ElMessage.success('对话创建成功')
    showNewChatDialog.value = false
    
    // 重置表单
    newChatForm.value = {
      type: 'private',
      title: '',
      members: [],
      classId: null
    }
    
    // 重新加载对话列表
    await loadConversations()
    
    // 选择新创建的对话
    selectConversation(response.data.id)
  } catch (error) {
    console.error('创建对话失败:', error)
    ElMessage.error(error.response?.data?.error || '创建对话失败')
  }
}

// 工具函数
const scrollToBottom = () => {
  const messageList = document.querySelector('.message-list')
  if (messageList) {
    messageList.scrollTop = messageList.scrollHeight
  }
}

// 处理回复
const handleReply = (message) => {
  replyToMessage.value = message
  messageInput.value?.focus()
}

// 处理编辑
const handleEdit = (message) => {
  editingMessage.value = message
  messageInput.value?.focus()
}

// 处理删除
const handleDelete = async (message) => {
  try {
    await api.delete(`/chat/messages/${message.id}`)
    
    // 通过Socket广播删除
    socket.emit('chat:delete_message', {
      message_id: message.id,
      conversation_id: currentConversationId.value
    })
    
    ElMessage.success('消息已删除')
  } catch (error) {
    console.error('删除消息失败:', error)
    ElMessage.error('删除消息失败')
  }
}

// 处理正在输入
const handleTyping = (isTyping) => {
  if (!socket || !currentConversationId.value) return
  
  if (isTyping) {
    socket.emit('chat:typing', {
      conversation_id: currentConversationId.value,
      user_id: userId,
      user_name: userName
    })
  } else {
    socket.emit('chat:stop_typing', {
      conversation_id: currentConversationId.value,
      user_id: userId
    })
  }
}

// 处理搜索
const handleSearch = () => {
  // TODO: 实现消息搜索功能
  ElMessage.info('搜索功能开发中...')
}

// 加载班级列表
const loadClasses = async () => {
  if (classList.value.length > 0) return // 已加载
  
  try {
    const userRole = localStorage.getItem('role')
    let endpoint = ''
    
    if (userRole === 'teacher') {
      endpoint = '/teacher/classes'
    } else if (userRole === 'student') {
      endpoint = '/student/classes'
    } else {
      endpoint = '/admin/classes'
    }
    
    const response = await api.get(endpoint)
    classList.value = response.data
  } catch (error) {
    console.error('加载班级列表失败:', error)
  }
}

// 处理类型变化
const handleTypeChange = () => {
  // 清空相关字段
  newChatForm.value.title = ''
  newChatForm.value.members = []
  newChatForm.value.classId = null
}

const removeMessage = (messageId) => {
  const index = currentMessages.value.findIndex(m => m.id === messageId)
  if (index !== -1) {
    currentMessages.value.splice(index, 1)
  }
}

const updateMessage = (data) => {
  const message = currentMessages.value.find(m => m.id === data.message_id)
  if (message) {
    message.content = data.content
    message.is_edited = true
    message.edited_at = data.edited_at
  }
}

const updateUserOnlineStatus = (userId, isOnline) => {
  conversations.value.forEach(conv => {
    if (conv.other_user && conv.other_user.user_id === userId) {
      conv.other_user.is_online = isOnline
      if (!isOnline) {
        conv.other_user.last_seen = new Date().toISOString()
      }
    }
  })
}
</script>

<style scoped>
.chat-window {
  display: flex;
  height: calc(100vh - 60px);
  background: #fff;
}

/* 左侧栏 */
.chat-sidebar {
  width: 320px;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
  background: #fff;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.btn-new-chat {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.btn-new-chat:hover {
  background: linear-gradient(135deg, #3a8ee6 0%, #409eff 100%);
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.search-box {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e5e5e5;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

/* 中间主区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  position: relative;
}

.no-conversation {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-message {
  text-align: center;
  color: #999;
}

.welcome-message i {
  font-size: 64px;
  margin-bottom: 20px;
  color: #409eff;
  opacity: 0.5;
}

.welcome-message h3 {
  margin: 10px 0;
  color: #666;
}

/* 右侧信息面板 */
.chat-info-panel {
  width: 300px;
  border-left: 1px solid #e5e5e5;
  background: #f8f9fa;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* 滚动条样式 */
.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 表单提示 */
.form-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.form-hint span {
  display: block;
  padding: 6px 10px;
  background: #f0f9ff;
  border-left: 3px solid #409eff;
  border-radius: 4px;
}
</style>
