<template>
  <div class="live-class-chat" :class="{ collapsed: isCollapsed }">
    <!-- 折叠/展开按钮 -->
    <div class="collapse-handle" @click="toggleCollapse">
      <svg 
        width="16" 
        height="16" 
        viewBox="0 0 24 24" 
        fill="none" 
        stroke="currentColor" 
        stroke-width="2"
        :class="{ rotated: isCollapsed }"
      >
        <polyline points="15 18 9 12 15 6"></polyline>
      </svg>
    </div>
    
    <!-- 主面板内容 -->
    <div class="chat-panel-content" v-show="!isCollapsed">
      <!-- 顶部横幅 -->
      <div class="chat-module-header">
        <div class="header-left-actions" v-if="activeTab === 'classGroup' && selectedConversation">
          <button class="back-btn" @click="selectedConversation = null" title="返回列表">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
        </div>
        <div class="header-left-actions" v-else-if="discussionMode">
          <button class="back-btn" @click="exitDiscussionMode" title="返回频道">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
        </div>
        <div class="header-title">
          <template v-if="discussionMode && selectedConversation">评论</template>
          <template v-else-if="activeTab === 'discussion'">课堂讨论</template>
          <template v-else-if="!selectedConversation">消息中心</template>
          <template v-else>{{ selectedConversation.title }}</template>
        </div>
        <div class="header-tabs">
          <button 
            class="header-tab-btn"
            :class="{ active: activeTab === 'discussion' }"
            @click="switchTab('discussion')"
            title="课堂讨论"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span v-if="discussionUnread > 0" class="unread-dot"></span>
          </button>
          
          <button 
            class="header-tab-btn"
            :class="{ active: activeTab === 'classGroup' }"
            @click="switchTab('classGroup')"
            title="班级群组"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <span v-if="classGroupUnread > 0" class="unread-dot"></span>
          </button>
        </div>
      </div>
      
      <!-- 讨论模式界面 -->
      <template v-if="activeTab === 'discussion'">
        <div class="online-status">
          <span class="online-dot"></span>
          <span>{{ onlineCount }} 人在线</span>
        </div>
        
        <ChatWindow
          :conversation-id="discussionConversationId"
          :messages="discussionMessages"
          conversation-subtype="live_class_discussion"
          :user-role="role"
          :is-live-mode="true"
          :hide-header="true"
          :show-classroom-features="true"
          :reply-to-message="replyToMessage"
          :editing-message="editingMessage"
          @send="handleSend"
          @load-more="handleLoadMore"
          @reply="handleReply"
          @edit="handleEdit"
          @delete="handleDelete"
          @cancel-reply="replyToMessage = null"
          @cancel-edit="editingMessage = null"
          @start-attendance="$emit('start-attendance')"
          @publish-task="$emit('publish-task')"
          @share-board="$emit('share-board')"
          @raise-hand="$emit('raise-hand', $event)"
        />
      </template>

      <!-- 消息中心模式界面 -->
      <template v-else>
        <!-- 群组列表视图 -->
        <ConversationList
          v-if="!selectedConversation"
          :conversations="allConversations"
          :total-unread-count="classGroupUnread"
          :folders="folders"
          :hide-header="true"
          :active-folder-id="activeFolderId"
          :search-query="conversationSearch"
          @update:searchQuery="conversationSearch = $event"
          @select="selectConversationById"
          @folder-change="handleFolderChange"
        />

        <!-- 选定群组的聊天视图 -->
        <ChatWindow
          v-else
          :conversation-id="selectedConversation.id"
          :conversation="selectedConversation"
          :messages="currentMessages"
          :conversation-subtype="selectedConversation.group_subtype || 'normal'"
          :user-role="role"
          :is-live-mode="true"
          :hide-header="true"
          :reply-to-message="replyToMessage"
          :editing-message="editingMessage"
          :is-discussion-mode="discussionMode"
          :root-message="rootMessage"
          @send="handleSend"
          @load-more="handleLoadMore"
          @reply="handleReply"
          @edit="handleEdit"
          @delete="handleDelete"
          @open-comments="handleOpenComments"
          @exit-discussion="exitDiscussionMode"
          @cancel-reply="replyToMessage = null"
          @cancel-edit="editingMessage = null"
        />
      </template>
    </div>
    
    <!-- 折叠时的迷你视图 -->
    <div class="collapsed-view" v-show="isCollapsed" @click="toggleCollapse">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
      <span v-if="totalUnread > 0" class="collapsed-badge">{{ totalUnread }}</span>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import ConversationList from '../chat/ConversationList.vue'
import ChatWindow from '../chat/ChatWindow.vue'
import api from '../../api'

export default {
  name: 'LiveClassChat',
  components: {
    ConversationList,
    ChatWindow
  },
  props: {
    // 课堂讨论对话ID
    discussionConversationId: {
      type: [Number, String],
      default: null
    },
    // 班级群对话ID
    classGroupConversationId: {
      type: [Number, String],
      default: null
    },
    // 用户角色
    role: {
      type: String,
      default: 'student',
      validator: (value) => !value || ['teacher', 'student'].includes(value)
    },
    // Socket实例
    socket: {
      type: Object,
      default: null
    },
    // 初始折叠状态
    initialCollapsed: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'collapse-change',
    'start-attendance',
    'publish-task',
    'share-board',
    'raise-hand'
  ],
  setup(props, { emit }) {
    const router = useRouter()
    
    // ========== Refs ==========
    const messageListRef = ref(null)
    const messageInputRef = ref(null)
    
    // ========== State ==========
    const isCollapsed = ref(props.initialCollapsed)
    const activeTab = ref('discussion')
    const showScrollButton = ref(false)
    const unreadCount = ref(0)
    const discussionUnread = ref(0)
    const classGroupUnread = ref(0)
    const onlineCount = ref(0)
    
    // 群组列表相关
    const allConversations = ref([])
    const selectedConversation = ref(null)
    const conversationSearch = ref('')
    const folders = ref([])
    const activeFolderId = ref('all')
    
    // 消息数据
    const discussionMessages = ref([])
    const classGroupMessages = ref([])
    const discussionComments = ref([])  // 讨论模式下的评论，独立于频道消息
    
    // 讨论模式相关
    const discussionMode = ref(false)
    const rootMessageId = ref(null)
    const rootMessage = ref(null)
    
    // 回复/编辑状态
    const replyToMessage = ref(null)
    const editingMessage = ref(null)
    
    // 加载状态
    const loading = ref(false)
    
    // ========== Computed ==========
    const currentConversationId = computed(() => {
      // 如果在讨论模式且频道有关联讨论组，使用讨论组ID
      if (discussionMode.value && selectedConversation.value?.linked_discussion_id) {
        return selectedConversation.value.linked_discussion_id
      }
      return activeTab.value === 'discussion' 
        ? props.discussionConversationId 
        : (selectedConversation.value?.id || props.classGroupConversationId)
    })
    
    const currentMessages = computed(() => {
      if (discussionMode.value) {
        // 在讨论模式下，显示评论（不包括根消息本身，因为它在header中显示）
        return discussionComments.value
      }
      return activeTab.value === 'discussion' 
        ? discussionMessages.value 
        : classGroupMessages.value
    })
    
    const totalUnread = computed(() => {
      return discussionUnread.value + classGroupUnread.value
    })

    const filteredConversations = computed(() => {
      if (!conversationSearch.value) return allConversations.value
      const query = conversationSearch.value.toLowerCase()
      return allConversations.value.filter(c => 
        (c.title && c.title.toLowerCase().includes(query)) ||
        (c.last_message && c.last_message.toLowerCase().includes(query))
      )
    })
    
    // ========== Methods ==========
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      emit('collapse-change', isCollapsed.value)
      
      if (!isCollapsed.value) {
        nextTick(() => scrollToBottom())
      }
    }
    
    const switchTab = (tab) => {
      activeTab.value = tab
      
      // 清除当前tab的未读
      if (tab === 'discussion') {
        discussionUnread.value = 0
        // 切换到讨论标签页时，退出讨论模式
        discussionMode.value = false
        rootMessageId.value = null
        rootMessage.value = null
      } else {
        classGroupUnread.value = 0
        // 切换到群组中心时，如果没有选定对话，加载对话列表
        if (!selectedConversation.value) {
          loadAllConversations()
        }
      }
      
      nextTick(() => scrollToBottom())
    }

    const loadAllConversations = async () => {
      try {
        const [convRes, folderRes] = await Promise.all([
          api.get('/chat/conversations'),
          api.get('/chat/folders')
        ])
        allConversations.value = convRes.data || []
        const folderData = folderRes.data.data || folderRes.data || []
        folders.value = folderData.map(folder => ({
          ...folder,
          id: String(folder.id)
        }))
      } catch (error) {
        console.error('Failed to load conversations/folders:', error)
      }
    }

    const handleFolderChange = (folderId) => {
      activeFolderId.value = String(folderId)
    }

    const selectConversationById = (id) => {
      const conv = allConversations.value.find(c => c.id === id)
      if (conv) {
        selectedConversation.value = conv
        // 清空当前消息，避免显示旧消息
        classGroupMessages.value = []
        discussionComments.value = []
        // 重置讨论模式
        discussionMode.value = false
        rootMessageId.value = null
        rootMessage.value = null
        // 立即加载该群组的消息
        nextTick(() => {
          loadMessages(id, 'classGroup')
        })
      }
    }
    
    const loadMessages = async (conversationId, type) => {
      if (!conversationId) return
      
      loading.value = true
      try {
        const response = await api.get(`/chat/conversations/${conversationId}/messages`)
        const messages = response.data.messages || []
        
        if (type === 'discussion') {
          discussionMessages.value = messages
        } else {
          classGroupMessages.value = messages
        }
        
        nextTick(() => scrollToBottom())
      } catch (error) {
        console.error(`Failed to load ${type} messages:`, error)
      } finally {
        loading.value = false
      }
    }
    
    const handleLoadMore = () => {
      // TODO: 实现加载更多历史消息
      console.log('Load more messages')
    }
    
    const handleReply = (message) => {
      replyToMessage.value = message
      messageInputRef.value?.focus()
    }
    
    const handleEdit = (message) => {
      editingMessage.value = message
      messageInputRef.value?.focus()
    }
    
    const handleDelete = async (message) => {
      try {
        await api.delete(`/chat/messages/${message.id}`)
        
        // 从本地移除
        const targetArray = message.conversation_id === props.discussionConversationId
          ? discussionMessages.value
          : classGroupMessages.value
        
        const index = targetArray.findIndex(m => m.id === message.id)
        if (index > -1) {
          targetArray.splice(index, 1)
        }
      } catch (error) {
        console.error('Failed to delete message:', error)
      }
    }
    
    const handleOpenComments = (message) => {
      // 检查当前对话是否是频道
      if (selectedConversation.value?.group_subtype === 'channel') {
        // 如果是频道，在窗口内启用讨论模式
        discussionMode.value = true
        rootMessageId.value = message.id
        rootMessage.value = message
        // 保持在班级群组标签页，因为评论消息在频道中
        activeTab.value = 'classGroup'
        
        // 如果频道有关联的讨论组，从讨论组加载评论，否则从频道加载
        const conversationIdForComments = selectedConversation.value.linked_discussion_id || selectedConversation.value.id
        loadComments(message.id, conversationIdForComments)
      } else {
        // 普通群组的评论处理（如果需要的话）
        console.log('Open comments for group message:', message)
      }
    }
    
    const exitDiscussionMode = () => {
      discussionMode.value = false
      rootMessageId.value = null
      rootMessage.value = null
      discussionComments.value = []  // 清空讨论评论
    }
    
    const loadComments = async (messageId, conversationId) => {
      try {
        // 清空之前的评论
        discussionComments.value = []
        
        // 加载该消息的所有评论
        const response = await api.get(`/chat/conversations/${conversationId}/messages`, {
          params: {
            root_id: messageId
          }
        })
        
        const comments = response.data.messages || []
        
        console.log('loadComments:', {
          messageId,
          targetConversationId: conversationId,
          commentsFound: comments.length
        })
        
        // 按时间排序后添加到讨论评论列表
        comments.sort((a, b) => {
          return new Date(a.created_at) - new Date(b.created_at)
        })
        
        discussionComments.value = comments
      } catch (error) {
        console.error('Failed to load comments:', error)
      }
    }
    
    const handleSend = async (messageData) => {
      const conversationId = currentConversationId.value
      
      // 乐观更新：立即显示消息
      const tempMessage = {
        id: `temp_${Date.now()}`,
        conversation_id: conversationId,
        sender_id: parseInt(localStorage.getItem('user_id')),
        sender_name: localStorage.getItem('real_name') || localStorage.getItem('username') || '我',
        content: messageData.content,
        message_type: messageData.message_type || 'text',
        created_at: new Date().toISOString(),
        is_pending: true,
        root_message_id: discussionMode.value ? rootMessageId.value : null
      }
      
      const targetArray = discussionMode.value
        ? discussionComments.value
        : (activeTab.value === 'discussion' 
            ? discussionMessages.value 
            : classGroupMessages.value)
      targetArray.push(tempMessage)
      
      nextTick(() => scrollToBottom())
      
      // 发送到服务器
      try {
        const response = await api.post(`/chat/conversations/${conversationId}/messages`, {
          content: messageData.content,
          message_type: messageData.message_type || 'text',
          reply_to_id: replyToMessage.value?.id,
          edit_id: editingMessage.value?.id,
          root_message_id: discussionMode.value ? rootMessageId.value : null
        })
        
        // 用服务器返回的真实消息替换临时消息
        const index = targetArray.findIndex(m => m.id === tempMessage.id)
        if (index > -1) {
          targetArray[index] = response.data.message || response.data
        }
        
        // 通过Socket广播（如果有）
        if (props.socket) {
          props.socket.emit('chat:send_message', {
            conversation_id: conversationId,
            message: response.data.message || response.data
          })
        }
      } catch (error) {
        console.error('Failed to send message:', error)
        // 标记发送失败
        const index = targetArray.findIndex(m => m.id === tempMessage.id)
        if (index > -1) {
          targetArray[index].is_failed = true
          targetArray[index].is_pending = false
        }
      }
      
      // 清除状态
      replyToMessage.value = null
      editingMessage.value = null
    }
    
    const handleTyping = () => {
      if (props.socket) {
        props.socket.emit('chat:typing', {
          conversation_id: currentConversationId.value
        })
      }
    }
    
    const scrollToBottom = () => {
      if (messageListRef.value) {
        messageListRef.value.scrollToBottom?.()
      }
      showScrollButton.value = false
      unreadCount.value = 0
    }
    
    // 接收新消息
    const receiveMessage = (message) => {
      if (!message?.conversation_id) return
      
      const isDiscussion = message.conversation_id === props.discussionConversationId
      const isClassGroup = selectedConversation.value && message.conversation_id === selectedConversation.value.id
      // 也检查是否是频道关联的讨论组的消息
      const isLinkedDiscussion = selectedConversation.value && 
                                 selectedConversation.value.group_subtype === 'channel' &&
                                 message.conversation_id === selectedConversation.value.linked_discussion_id
      
      // 如果不是当前讨论，也不是当前选中的群组，只更新未读数或列表
      if (isDiscussion) {
        if (discussionMessages.value.some(m => m.id === message.id)) return
        discussionMessages.value.push(message)
        if (isCollapsed.value || activeTab.value !== 'discussion') {
          discussionUnread.value++
        }
      } else {
        // 更新会话列表中的最后一条消息
        const conv = allConversations.value.find(c => c.id === message.conversation_id)
        if (conv) {
          conv.last_message = message.content
          conv.last_message_time = message.created_at
          if (!isClassGroup && !isLinkedDiscussion) conv.unread_count = (conv.unread_count || 0) + 1
        }
        
        // 讨论模式下且消息来自关联讨论组，添加到讨论评论
        if (discussionMode.value && isLinkedDiscussion && message.root_message_id === rootMessageId.value) {
          if (discussionComments.value.some(m => m.id === message.id)) return
          discussionComments.value.push(message)
        } else if (isClassGroup) {
          // 普通频道消息
          if (classGroupMessages.value.some(m => m.id === message.id)) return
          classGroupMessages.value.push(message)
        } else {
          classGroupUnread.value++
        }
      }
      
      // 如果在当前显示区域，滚动到底部
      if ((isDiscussion && activeTab.value === 'discussion') ||
          (isClassGroup && activeTab.value === 'classGroup') ||
          (discussionMode.value && isLinkedDiscussion)) {
        if (!showScrollButton.value) {
          nextTick(() => scrollToBottom())
        } else {
          unreadCount.value++
        }
      }
    }
    
    // 更新在线人数
    const updateOnlineCount = (count) => {
      onlineCount.value = count
    }
    
    // ========== Socket Events ==========
    const setupSocketListeners = () => {
      if (!props.socket) return
      
      props.socket.on('chat:new_message', receiveMessage)
      props.socket.on('classroom:participant_count', ({ count }) => {
        updateOnlineCount(count)
      })
    }
    
    const removeSocketListeners = () => {
      if (!props.socket) return
      
      props.socket.off('chat:new_message', receiveMessage)
      props.socket.off('classroom:participant_count')
    }
    
    // ========== Lifecycle ==========
    onMounted(async () => {
      // 加载课堂讨论消息
      await loadMessages(props.discussionConversationId, 'discussion')
      
      // 如果有班级群，也加载
      if (props.classGroupConversationId) {
        await loadMessages(props.classGroupConversationId, 'classGroup')
      }
      
      setupSocketListeners()
    })
    
    onBeforeUnmount(() => {
      removeSocketListeners()
    })
    
    // 监听Socket变化
    watch(() => props.socket, (newSocket, oldSocket) => {
      if (oldSocket) {
        oldSocket.off('chat:new_message', receiveMessage)
        oldSocket.off('classroom:participant_count')
      }
      if (newSocket) {
        setupSocketListeners()
      }
    })
    
    // ========== Return ==========
    return {
      // Refs
      messageListRef,
      messageInputRef,
      
      // State
      isCollapsed,
      activeTab,
      showScrollButton,
      unreadCount,
      discussionUnread,
      classGroupUnread,
      onlineCount,
      replyToMessage,
      editingMessage,
      allConversations,
      selectedConversation,
      conversationSearch,
      discussionMessages,
      classGroupMessages,
      folders,
      activeFolderId,
      
      // Discussion mode state
      discussionMode,
      rootMessageId,
      rootMessage,
      
      // Computed
      currentConversationId,
      currentMessages,
      totalUnread,
      filteredConversations,
      
      // Methods
      toggleCollapse,
      switchTab,
      selectConversationById,
      backToList: () => { selectedConversation.value = null },
      handleLoadMore,
      handleReply,
      handleEdit,
      handleDelete,
      handleOpenComments,
      handleSend,
      handleTyping,
      scrollToBottom,
      receiveMessage,
      updateOnlineCount,
      handleFolderChange,
      exitDiscussionMode
    }
  }
}
</script>

<style scoped>
.live-class-chat {
  position: relative;
  display: flex;
  width: 380px;
  min-width: 380px;
  max-width: 480px;
  background: #fff;
  border-radius: 12px 0 0 12px;
  box-shadow: -2px 0 16px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  overflow: hidden;
}

.live-class-chat.collapsed {
  width: 56px;
  min-width: 56px;
}

/* 折叠把手 */
.collapse-handle {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 60px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  border-radius: 0 8px 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 2px 0 8px rgba(64, 158, 255, 0.3);
}

.collapse-handle:hover {
  width: 24px;
}

.collapse-handle svg {
  color: #fff;
  transition: transform 0.3s;
}

.collapse-handle svg.rotated {
  transform: rotate(180deg);
}

/* 对话面板内容 */
.chat-panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 20px;
  min-width: 0;
  position: relative; /* 核心：为下滑按钮提供定位基准 */
}

/* 顶部横幅 */
.chat-module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #f0f2f5;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.header-tabs {
  display: flex;
  gap: 8px;
}

.header-tab-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #f5f7fa;
  color: #64748b;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.header-tab-btn:hover {
  background: #eef1f6;
  color: #409eff;
  transform: translateY(-1px);
}

.header-tab-btn.active {
  background: #409eff;
  color: #fff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.back-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 8px;
  cursor: pointer;
  margin-right: 8px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f0f2f5;
  color: #409eff;
}

.unread-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 10px;
  height: 10px;
  background: #ff4757;
  border: 2px solid #fff;
  border-radius: 50%;
}

/* 在线状态 */
.online-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  font-size: 12px;
  color: #94a3b8;
  background: #fafbfc;
}

.online-dot {
  width: 8px;
  height: 8px;
  background: #52c41a;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 消息区域 */
.chat-messages-area {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 输入区域 */
.chat-input-area {
  border-top: 1px solid #f0f0f0;
  padding: 8px;
}

/* 折叠视图 */
.collapsed-view {
  width: 56px;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #409eff;
  position: relative;
}

.collapsed-badge {
  position: absolute;
  top: 50%;
  right: 8px;
  transform: translateY(-50%);
  min-width: 18px;
  height: 18px;
  background: #ff4757;
  color: #fff;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

/* 动画 */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.2s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
