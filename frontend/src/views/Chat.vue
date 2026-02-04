<template>
  <div class="chat-window">
    <!-- 悬浮直播状态 -->
    <LiveStatusBanner />
    
    <!-- 左侧：对话列表 -->
    <div class="chat-sidebar">
      <!-- 对话列表区域 -->
      <div class="conversation-area">
        <div class="sidebar-header">
          <h2>教学群组</h2>
          <button class="btn-new-chat" @click="showNewChatDialog = true" title="新建群组">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
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
        
        <!-- 分类栏：位于搜索框与群组列表之间 -->
        <div class="category-bar">
          <div class="category-tabs">
            <div 
              class="category-tab" 
              :class="{ active: activeFolderId === 'all' }"
              @click="handleFolderChange('all')"
            >
              全部
            </div>
            <div 
              v-if="totalUnreadCount > 0"
              class="category-tab" 
              :class="{ active: activeFolderId === 'unread' }"
              @click="handleFolderChange('unread')"
            >
              未读
              <span v-if="totalUnreadCount > 0" class="category-badge">{{ totalUnreadCount > 99 ? '99+' : totalUnreadCount }}</span>
            </div>
            <div 
              v-for="folder in folders" 
              :key="folder.id"
              class="category-tab folder-tab"
              :class="{ active: activeFolderId === folder.id }"
              @click="handleFolderChange(folder.id)"
            >
              {{ folder.name }}
              <button class="tab-delete-btn" @click.stop="deleteFolder(folder.id)" title="删除">
                <i class="el-icon-close"></i>
              </button>
            </div>
          </div>
          <button class="btn-add-folder" @click="showNewFolderDialog = true" title="新建文件夹">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
          </button>
        </div>
        
        <div class="conversation-list">
          <ConversationItem 
            v-for="conv in filteredConversations" 
            :key="conv.id"
            :conversation="conv"
            :active="currentConversationId === conv.id"
            :context-menu-visible="activeContextMenu === conv.id"
            :folders="folders"
            :active-folder-id="activeFolderId"
            @click="selectConversation(conv.id)"
            @show-context-menu="handleShowContextMenu(conv.id, $event)"
            @hide-context-menu="handleHideContextMenu"
            @pin="handlePinConversation"
            @mute="handleMuteConversation"
            @read="handleMarkAsRead"
            @add-to-folder="handleAddToFolder"
            @open-create-folder="handleOpenCreateFolder"
            @remove-from-folder="handleRemoveFromFolder"
            @leave="handleLeaveGroup"
          />
          
          <div v-if="conversations.length === 0" class="empty-state">
            <p>暂无对话</p>
            <el-button type="primary" size="small" @click="showNewChatDialog = true">
              开始聊天
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 中间：聊天主区域 -->
    <div class="chat-main">
      <template v-if="currentConversation">
        <!-- 只在非讨论模式下显示群组头部 -->
        <ChatHeader 
          v-if="!discussionMode"
          :conversation="currentConversation"
          @show-info="showInfoPanel = !showInfoPanel"
        />
        
        <PinnedMessageBar
          ref="pinnedMessageBar"
          :conversation-id="currentConversationId"
          :can-unpin="canUnpin"
          @jump-to-message="handleJumpToMessage"
          @message-unpinned="handleMessageUnpinned" 
        />

        <!-- 讨论模式头部 -->
        <div v-if="discussionMode" class="discussion-mode-header">
          <!-- 顶部控制栏 -->
          <div class="discussion-top-bar">
            <button class="back-btn" @click="exitDiscussionMode" title="返回频道">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
            </button>
            <span class="discussion-title">讨论群组</span>
          </div>
          
          <!-- 原消息卡片 -->
          <div v-if="rootMessage" class="root-message-card" @click="rootMessageExpanded = !rootMessageExpanded">
            <div class="root-sender">{{ rootMessage.sender_name }}</div>
            <div class="root-content" :class="{ expanded: rootMessageExpanded }">
              {{ rootMessage.content }}
            </div>
            <div class="root-meta">
              <span>{{ formatTime(rootMessage.created_at) }}</span>
              <span class="expand-hint">{{ rootMessageExpanded ? '点击收起' : '点击查看完整内容' }}</span>
            </div>
          </div>
        </div>

        <div v-if="messageFilterType" class="filter-indicator">
          <span>
            <i class="el-icon-filter"></i>
            正在筛选: {{ messageFilterType === 'image' ? '图片' : messageFilterType === 'file' ? '文件' : '链接' }}
          </span>
          <el-button type="text" size="small" @click="handleFilter(null)" style="margin-left: 10px">清除筛选</el-button>
        </div>
        
        <!-- 消息和输入区域：包含消息列表和输入框的统一容器 -->
        <div class="chat-container">
          <MessageList 
            ref="messageList"
            :conversation-id="currentConversationId"
            :messages="currentMessages"
            :conversation-subtype="currentConversation?.group_subtype"
            @load-more="loadMoreMessages"
            @reply="handleReply"
            @edit="handleEdit"
            @delete="handleDelete"
            @open-comments="handleOpenComments"
          />
          
          <!-- 滚动到底部按钮 -->
          <transition name="fade-scale">
            <div v-if="messageList?.showScrollButton" class="scroll-bottom-container" @click="scrollToBottom">
              <!-- 未读消息数气泡 -->
              <div v-if="messageList?.unreadCount > 0" class="unread-bubble">
                {{ messageList?.formattedUnreadCount }}
              </div>
              <!-- 圆形按钮 -->
              <div class="down-button">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
              </div>
            </div>
          </transition>
          
          <MessageInput 
            ref="messageInput"
            :conversation-id="currentConversationId"
            :conversation-subtype="currentConversation?.group_subtype"
            :discussion-mode="discussionMode"
            :reply-to="replyToMessage"
            :editing-message="editingMessage"
            @send="handleSendMessage"
            @cancel-reply="replyToMessage = null"
            @cancel-edit="editingMessage = null"
            @typing="handleTyping"
          />
        </div>
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
          @filter="handleFilter"
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
        <!-- 主分类：频道 or 普通群组 -->
        <el-form-item label="主分类">
          <el-radio-group v-model="newChatForm.mainCategory" @change="handleMainCategoryChange">
            <el-radio label="channel" :disabled="userRole !== 'teacher'">📢 频道</el-radio>
            <el-radio label="normal">💬 普通群组</el-radio>
          </el-radio-group>
          <div v-if="userRole !== 'teacher' && newChatForm.mainCategory === 'channel'" class="form-hint">
            <span style="color: #f56c6c;">只有教师可以创建频道</span>
          </div>
        </el-form-item>
        
        <!-- 频道选项 -->
        <template v-if="newChatForm.mainCategory === 'channel'">
          <el-form-item label="频道名称">
            <el-input v-model="newChatForm.title" placeholder="输入频道名称" />
          </el-form-item>
          
          <el-form-item label="频道描述">
            <el-input 
              v-model="newChatForm.description" 
              type="textarea" 
              :rows="3"
              placeholder="简要描述频道用途" 
            />
          </el-form-item>
        </template>
        
        <!-- 普通群组选项 -->
        <template v-else>
          <!-- 普通群组的子类型标签 -->
          <el-form-item label="群组类型">
            <el-radio-group v-model="newChatForm.type" @change="handleTypeChange">
              <el-radio label="private">👤 私聊</el-radio>
              <el-radio label="group">👥 群聊</el-radio>
              <el-radio label="class_group" :disabled="userRole !== 'teacher'">🏫 班级群</el-radio>
              <el-radio label="course_group" :disabled="userRole !== 'teacher'">📚 课程群</el-radio>
            </el-radio-group>
            <div v-if="userRole === 'student'" class="form-hint">
              <span style="color: #909399;">学生可以创建私聊和群聊</span>
            </div>
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
              <span v-if="newChatForm.type === 'class_group'">班级群将自动添加所有学生和教师</span>
              <span v-else>课程群只包含教师，用于教学讨论</span>
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
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="showNewChatDialog = false">取消</el-button>
        <el-button type="primary" @click="createConversation">创建</el-button>
      </template>
    </el-dialog>

    <!-- New Folder Dialog -->
    <el-dialog
      v-model="showNewFolderDialog"
      title="新建文件夹"
      width="400px"
    >
      <el-form @submit.prevent="createFolder">
        <el-form-item label="名称">
          <el-input v-model="newFolderName" placeholder="例如：重要通知、学生咨询" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNewFolderDialog = false">取消</el-button>
        <el-button type="primary" :loading="folderCreating" @click="createFolder">创建</el-button>
      </template>
    </el-dialog>
    
    <!-- Add to Folder Dialog -->
    <el-dialog
      v-model="showAddToFolderDialog"
      title="加入文件夹"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="!showCreateFolderForm" class="folder-selection">
        <div v-if="folders.length === 0" class="empty-folders">
          <i class="el-icon-folder"></i>
          <p>还没有文件夹</p>
          <p class="hint">创建文件夹来整理您的对话</p>
        </div>
        <div v-else class="folder-list-selection">
          <div 
            v-for="folder in folders" 
            :key="folder.id"
            class="folder-item"
            @click="addConversationToFolder(folder.id)"
          >
            <div class="folder-icon">
              <i class="el-icon-folder"></i>
            </div>
            <div class="folder-info">
              <div class="folder-name">{{ folder.name }}</div>
              <div class="folder-count">{{ folder.conversations?.length || 0 }} 个对话</div>
            </div>
            <i class="el-icon-arrow-right"></i>
          </div>
        </div>
        <div class="create-folder-trigger" @click="showCreateFolderForm = true">
          <i class="el-icon-plus"></i>
          <span>创建新文件夹</span>
        </div>
      </div>
      
      <!-- Create Folder Form -->
      <div v-else class="create-folder-form">
        <div class="form-header">
          <el-button 
            type="text" 
            icon="el-icon-arrow-left" 
            @click="showCreateFolderForm = false"
          >
            返回
          </el-button>
          <span class="form-title">新文件夹</span>
        </div>
        
        <el-form label-position="top" @submit.prevent="createFolderFromDialog">
          <el-form-item label="文件夹名称">
            <el-input 
              v-model="newFolderNameInDialog" 
              placeholder="例如：重要通知、学生咨询"
              maxlength="20"
              show-word-limit
            />
          </el-form-item>
          
          <el-form-item label="包含的聊天">
            <div class="included-chats">
              <div class="chat-chip">
                <span>{{ getConversationName(selectedConversationForFolder) }}</span>
              </div>
              <el-button type="text" size="small" icon="el-icon-plus">
                添加聊天
              </el-button>
            </div>
            <div class="form-hint">选择将出现在此文件夹中的聊天和聊天类型。</div>
          </el-form-item>
          
          <el-form-item label="排除的聊天">
            <el-button type="text" size="small" icon="el-icon-plus">
              添加以排除聊天
            </el-button>
            <div class="form-hint">选择不会出现在此文件夹中的聊天或聊天类型。</div>
          </el-form-item>
        </el-form>
        
        <div class="form-footer">
          <el-button @click="showCreateFolderForm = false; showAddToFolderDialog = false">
            取消
          </el-button>
          <el-button 
            type="primary" 
            :loading="folderCreating" 
            @click="createFolderFromDialog"
          >
            创建
          </el-button>
        </div>
      </div>
    </el-dialog>
    
    <!-- New Folder Dialog (from top toolbar) -->
    <el-dialog
      v-model="showNewFolderDialog"
      title="新建文件夹"
      width="400px"
    >
      <el-form @submit.prevent="createFolder">
        <el-form-item label="名称">
          <el-input v-model="newFolderName" placeholder="例如：重要通知、学生咨询" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNewFolderDialog = false">取消</el-button>
        <el-button type="primary" :loading="folderCreating" @click="createFolder">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import io from 'socket.io-client'
import api from '../api'
import ConversationItem from '../components/ConversationItem.vue'
import ChatHeader from '../components/ChatHeader.vue'
import MessageList from '../components/MessageList.vue'
import MessageInput from '../components/MessageInput.vue'
import ChatInfoPanel from '../components/ChatInfoPanel.vue'
import PinnedMessageBar from '../components/PinnedMessageBar.vue'
import LiveStatusBanner from '../components/LiveStatusBanner.vue'
import { eventBus } from '../utils/eventBus'
import { formatTime } from '@/utils/timeUtils'

const route = useRoute()
const router = useRouter()

// 状态
const conversations = ref([])
const currentConversationId = ref(null)
const allMessages = ref([])

const currentMessages = computed(() => {
  if (discussionMode.value && rootMessageId.value) {
    // 讨论模式：只显示某条消息的评论
    return allMessages.value.filter(msg => msg.root_message_id === rootMessageId.value)
  }
  // 正常模式：显示所有非评论消息
  return allMessages.value.filter(msg => !msg.root_message_id)
})
const showInfoPanel = ref(false)
const searchQuery = ref('')
const showNewChatDialog = ref(false)
const searchingUsers = ref(false)
const userSearchResults = ref([])
const replyToMessage = ref(null)
const editingMessage = ref(null)
const messageList = ref(null)
const messageInput = ref(null)
const pinnedMessageBar = ref(null)

// Folder refs
const activeFolderId = ref('all')
const folders = ref([])
const showNewFolderDialog = ref(false)
const newFolderName = ref('')
const folderCreating = ref(false)
const showAddToFolderDialog = ref(false)
const selectedConversationForFolder = ref(null)
const showCreateFolderForm = ref(false)
const newFolderNameInDialog = ref('')

// Context menu refs
const activeContextMenu = ref(null)
const contextMenuPosition = ref({ x: 0, y: 0 })

// Message Filter
const messageFilterType = ref(null)

// Discussion Mode (Telegram风格评论)
const discussionMode = ref(false)
const rootMessageId = ref(null)
const rootMessage = ref(null)
const rootMessageExpanded = ref(false)  // 原消息是否展开
const hiddenConversation = ref(null)  // 存储隐藏的对话（如讨论组）

// Socket连接
let socket = null
const userId = localStorage.getItem('user_id')
const userRole = localStorage.getItem('user_role')
const userName = localStorage.getItem('user_name') || localStorage.getItem('real_name') || localStorage.getItem('username')

// 新建对话表单
const newChatForm = ref({
  mainCategory: 'normal',  // 'channel' or 'normal'
  type: 'group',  // 'private', 'group', 'class_group', 'course_group'
  title: '',
  description: '',
  members: [],
  classId: null
})

const classList = ref([])

// 计算属性
const canUnpin = computed(() => {
  return ['teacher', 'admin'].includes(userRole)
})

const currentConversation = computed(() => {
  // 如果有隐藏的对话（讨论组），优先使用它
  if (hiddenConversation.value && hiddenConversation.value.id === currentConversationId.value) {
    return hiddenConversation.value
  }
  return conversations.value.find(c => c.id === currentConversationId.value)
})

const totalUnreadCount = computed(() => {
  return conversations.value.reduce((sum, conv) => sum + (conv.unread_count || 0), 0)
})

// 监听未读总数变化，通知 App.vue 更新导航栏徽章
watch(totalUnreadCount, (newCount) => {
  eventBus.emit('unread-count-changed', newCount)
})

const filteredConversations = computed(() => {
  let result = conversations.value

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(conv => {
      return conv.title?.toLowerCase().includes(query) ||
             conv.last_message?.content?.toLowerCase().includes(query)
    })
  }
  
  // Folder filter
  if (activeFolderId.value === 'all') {
    return result
  } else if (activeFolderId.value === 'unread') {
    return result.filter(conv => (conv.unread_count || 0) > 0)
  } else {
    // Custom folder
    const folder = folders.value.find(f => f.id === activeFolderId.value)
    console.log('Current folder:', folder)
    console.log('All conversations:', result.map(c => c.id))
    if (folder && folder.conversations) {
       // folder.conversations is list of conversation IDs
       console.log('Folder conversations:', folder.conversations)
       return result.filter(conv => folder.conversations.includes(conv.id))
    }
    return []
  }
})

// 生命周期
onMounted(async () => {
  await loadConversations()
  loadFolders()
  initSocket()
  
  // 检查URL参数以决定是否进入讨论模式
  const queryId = route.query.id
  const queryRootId = route.query.rootId
  
  // 先设置讨论模式状态
  if (queryRootId) {
    discussionMode.value = true
    rootMessageId.value = parseInt(queryRootId)
    await loadRootMessage(rootMessageId.value)
  }
  
  // 然后加载对话 - 先验证对话是否存在于列表中
  if (queryId) {
    const convId = parseInt(queryId)
    const convExists = conversations.value.some(c => c.id === convId)
    
    if (convExists) {
      await selectConversation(convId)
    } else {
      // 对话不存在（可能已被过滤），清除URL参数
      router.replace({ path: '/chat', query: {} })
      ElMessage.warning('该对话已不可用')
    }
  }
  
  // 添加全局点击事件监听，关闭右键菜单
  document.addEventListener('click', closeAllContextMenus)
})

// 监听路由变化
watch(() => route.query, async (newQuery, oldQuery) => {
  const newId = newQuery.id
  const newRootId = newQuery.rootId
  const oldId = oldQuery?.id
  const oldRootId = oldQuery?.rootId
  
  // 先更新讨论模式状态（在加载消息之前）
  if (newRootId) {
    // 进入讨论模式
    discussionMode.value = true
    rootMessageId.value = parseInt(newRootId)
    await loadRootMessage(rootMessageId.value)
  } else {
    // 退出讨论模式
    discussionMode.value = false
    rootMessageId.value = null
    rootMessage.value = null
  }
  
  // 然后处理对话切换或消息重新加载
  if (newId && parseInt(newId) !== currentConversationId.value) {
    // 切换到不同的对话
    
    // 先离开旧房间
    if (socket && currentConversationId.value) {
      socket.emit('chat:leave', {
        conversation_id: currentConversationId.value,
        user_id: userId
      })
    }
    
    currentConversationId.value = parseInt(newId)
    
    // 如果对话不在列表中（比如讨论组），从API加载对话信息
    if (!conversations.value.find(c => c.id === currentConversationId.value)) {
      try {
        const response = await api.get(`/chat/conversations/${currentConversationId.value}`)
        // 如果是讨论组，存储到hiddenConversation而不是添加到列表
        if (response.data.group_subtype === 'discussion') {
          hiddenConversation.value = response.data
        } else {
          conversations.value.push(response.data)
        }
      } catch (error) {
        console.error('加载对话信息失败:', error)
      }
    }
    
    // 直接加载消息（不使用selectConversation，避免重复加载）
    await loadMessages(currentConversationId.value)
    
    // 加入新对话房间
    if (socket) {
      socket.emit('chat:join', {
        conversation_id: currentConversationId.value,
        user_id: userId
      })
    }
    
    // 标记已读
    markConversationRead(currentConversationId.value)
  } else if (newId && currentConversationId.value) {
    // 同一个对话但模式变化了（频道<->讨论区），重新加载消息
    if (newRootId !== oldRootId) {
      await loadMessages(currentConversationId.value)
    }
  }
}, { deep: true })

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
  }
  
  // 移除全局点击事件监听
  document.removeEventListener('click', closeAllContextMenus)
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
    // 注意：不清除pending，等待chat:new_message事件来替换临时消息
    if (data.temp_id) {
      const tempIndex = allMessages.value.findIndex(m => m.temp_id === data.temp_id)
      if (tempIndex !== -1) {
        // 只更新ID和时间，保留pending状态
        allMessages.value[tempIndex].id = data.id
        allMessages.value[tempIndex].created_at = data.created_at
        console.log('chat:message_sent - 更新临时消息ID:', data.temp_id, '->', data.id)
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
  
  // 监听课堂入口消息状态更新
  socket.on('chat:message_updated', (data) => {
    if (data.lesson_id && data.status === 'ended') {
      // 刷新当前对话的消息以获取更新后的状态
      if (currentConversationId.value) {
        loadMessages(currentConversationId.value)
      }
    }
  })
  
  socket.on('chat:user_online', (data) => {
    updateUserOnlineStatus(data.user_id, true)
  })
  
  socket.on('chat:user_offline', (data) => {
    updateUserOnlineStatus(data.user_id, false)
  })
}

// Folder Management
const loadFolders = async () => {
  try {
    const response = await api.get('/chat/folders')
    // 后端返回格式: {code: 200, data: [...]}
    const folderData = response.data.data || response.data || []
    console.log('Loaded folders:', folderData)
    folders.value = folderData
  } catch (error) {
    console.error('Failed to load folders:', error)
  }
}

const handleFolderChange = (folderId) => {
  activeFolderId.value = folderId
}

const deleteFolder = async (folderId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个文件夹吗？文件夹中的对话不会被删除。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/chat/folders/${folderId}`)
    ElMessage.success('文件夹已删除')
    
    // 如果当前在被删除的文件夹中，切换到全部
    if (activeFolderId.value === folderId) {
      activeFolderId.value = 'all'
    }
    
    await loadFolders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件夹失败:', error)
      ElMessage.error('删除文件夹失败')
    }
  }
}

const createFolder = async () => {
  if (!newFolderName.value.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  
  folderCreating.value = true
  try {
    await api.post('/chat/folders', { name: newFolderName.value })
    ElMessage.success('文件夹创建成功')
    showNewFolderDialog.value = false
    newFolderName.value = ''
    await loadFolders()
  } catch (error) {
    console.error('创建文件夹失败:', error)
    ElMessage.error('创建文件夹失败')
  } finally {
    folderCreating.value = false
  }
}

// 加载对话列表
const handleJumpToMessage = (messageId) => {
  if (messageList.value) {
    messageList.value.scrollToMessage(messageId)
  }
}

const handleMessageUnpinned = (message) => {
  // 可以在这里添加一些通知或者逻辑
  console.log('Message unpinned:', message)
}

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
  // 使用路由导航，确保清除讨论模式状态
  router.push({
    path: '/chat',
    query: {
      id: conversationId
    }
  })
}

const handleFilter = (type) => {
  messageFilterType.value = type
  showInfoPanel.value = false
  if (currentConversationId.value) {
    loadMessages(currentConversationId.value)
    ElMessage.info(`已筛选: ${type === 'image' ? '图片' : type === 'file' ? '文件' : '链接'}`)
  }
}

// 加载消息
const loadMessages = async (conversationId, beforeId = null) => {
  try {
    const params = {
      before_id: beforeId,
      type: messageFilterType.value
    }
    
    // 如果在讨论模式中，添加root_id参数
    if (discussionMode.value && rootMessageId.value) {
      params.root_id = rootMessageId.value
    }
    
    // Remove null/undefined keys
    Object.keys(params).forEach(key => params[key] == null && delete params[key])

    console.log('loadMessages 调用:', {
      conversationId,
      beforeId,
      discussionMode: discussionMode.value,
      rootMessageId: rootMessageId.value,
      params
    })

    const response = await api.get(`/chat/conversations/${conversationId}/messages`, { params })
    
    console.log('loadMessages 响应:', {
      messagesCount: response.data.messages?.length || 0,
      messages: response.data.messages
    })
    
    if (beforeId) {
      // 加载更多历史消息
      allMessages.value = [...response.data.messages, ...allMessages.value]
    } else {
      // 首次加载，完全替换
      allMessages.value = response.data.messages || []
    }
    
    // 去除可能存在的重复消息（根据id去重，保留最后一条）
    const messageMap = new Map()
    allMessages.value.forEach(msg => {
      if (messageMap.has(msg.id)) {
        console.warn('发现重复消息:', msg.id, '，保留最新的')
      }
      messageMap.set(msg.id, msg)
    })
    allMessages.value = Array.from(messageMap.values())
    
    return response.data.has_more
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  }
}

// 加载更多消息
const loadMoreMessages = async () => {
  const messages = currentMessages.value
  if (messages.length === 0) return
  
  const firstMessageId = messages[0].id
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
  
  // 如果在讨论模式中，添加root_message_id
  if (discussionMode.value && rootMessageId.value) {
    optimisticMessage.root_message_id = rootMessageId.value
    // 如果是回复讨论中的某条评论，设置parent_message_id
    if (replyToMessage.value && replyToMessage.value.root_message_id === rootMessageId.value) {
      optimisticMessage.parent_message_id = replyToMessage.value.id
    }
  }
  
  // 添加回复引用
  if (replyToMessage.value) {
    optimisticMessage.reply_to = {
      id: replyToMessage.value.id,
      sender_name: replyToMessage.value.sender_name,
      content: replyToMessage.value.content
    }
  }
  
  allMessages.value.push(optimisticMessage)
  
  console.log('发送消息:', {
    conversationId: currentConversationId.value,
    discussionMode: discussionMode.value,
    rootMessageId: rootMessageId.value,
    optimisticMessage,
    allMessagesCount: allMessages.value.length
  })
  
  // 准备发送数据
  const sendData = {
    conversation_id: currentConversationId.value,
    user_id: userId,
    temp_id: tempId,
    reply_to_id: replyToMessage.value?.id,
    ...messageData
  }
  
  // 如果在讨论模式中，添加root_message_id和parent_message_id
  if (discussionMode.value && rootMessageId.value) {
    sendData.root_message_id = rootMessageId.value
    // 如果是回复讨论中的某条评论，设置parent_message_id
    if (replyToMessage.value && replyToMessage.value.root_message_id === rootMessageId.value) {
      sendData.parent_message_id = replyToMessage.value.id
    }
  }
  
  // 通过Socket发送
  socket.emit('chat:send_message', sendData)
  
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
    console.log('接收到新消息:', {
      messageId: message.id,
      conversationId: message.conversation_id,
      currentConversationId: currentConversationId.value,
      discussionMode: discussionMode.value,
      rootMessageId: rootMessageId.value,
      messageRootId: message.root_message_id
    })
    
    // 检查讨论模式是否匹配
    // 如果在讨论模式中，只接受当前 root_message_id 的评论
    if (discussionMode.value && rootMessageId.value) {
      if (message.root_message_id !== rootMessageId.value) {
        return  // 不是当前评论区的消息，忽略
      }
    } else {
      // 如果不在讨论模式中，只接受非评论消息
      if (message.root_message_id) {
        return  // 是评论消息但不在讨论模式，忽略
      }
    }
    
    // 如果是自己发送的消息，检查是否已经有临时消息
    if (message.sender_id == userId) {  // 使用==而不是===，因为可能类型不同
      // 查找是否已有临时消息（优先使用temp_id匹配）
      let existingIndex = -1
      
      // 第一步：查找相同ID的消息（避免重复）
      existingIndex = allMessages.value.findIndex(m => m.id === message.id && !m.pending)
      if (existingIndex !== -1) {
        console.log('chat:new_message - 消息已存在，忽略:', message.id)
        return
      }
      
      // 第二步：查找待替换的临时消息（有pending标志）
      existingIndex = allMessages.value.findIndex(m => m.pending && m.temp_id)
      if (existingIndex !== -1) {
        console.log('chat:new_message - 替换临时消息:', allMessages.value[existingIndex].temp_id, '->', message.id)
        // 替换临时消息
        allMessages.value.splice(existingIndex, 1, {
          ...message,
          pending: false
        })
        return
      }
    }
    
    // 其他情况，检查是否已存在该消息（避免重复）
    const exists = allMessages.value.some(m => m.id === message.id)
    if (!exists) {
      allMessages.value.push(message)
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
  const message = allMessages.value.find(m => m.id === status.message_id)
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
  // 权限验证
  if (newChatForm.value.mainCategory === 'channel' && userRole !== 'teacher') {
    ElMessage.error('只有教师可以创建频道')
    return
  }
  
  if (userRole === 'student' && ['class_group', 'course_group'].includes(newChatForm.value.type)) {
    ElMessage.error('学生只能创建私聊和群聊')
    return
  }
  
  // 验证
  if (newChatForm.value.mainCategory === 'channel' && !newChatForm.value.title) {
    ElMessage.warning('请输入频道名称')
    return
  }
  
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
  
  // 私聊必须选择一个成员，群聊至少需要一个成员
  if (newChatForm.value.type === 'private' && newChatForm.value.members.length === 0) {
    ElMessage.warning('请选择对话对象')
    return
  }
  
  if (newChatForm.value.type === 'group' && newChatForm.value.members.length === 0) {
    ElMessage.warning('请至少添加一个成员')
    return
  }
  
  try {
    const requestData = {
      type: newChatForm.value.mainCategory === 'channel' ? 'group' : newChatForm.value.type,
      title: newChatForm.value.title,
      description: newChatForm.value.description,
      member_ids: newChatForm.value.members,
      group_subtype: newChatForm.value.mainCategory === 'channel' ? 'channel' : 'normal',
      conversation_subtype: newChatForm.value.type  // 保存子类型标签
    }
    
    // 班级群组和课程群组需要class_id
    if (newChatForm.value.type === 'class_group' || newChatForm.value.type === 'course_group') {
      requestData.class_id = newChatForm.value.classId
    }
    
    const response = await api.post('/chat/conversations', requestData)
    
    ElMessage.success(newChatForm.value.mainCategory === 'channel' ? '频道创建成功' : '对话创建成功')
    showNewChatDialog.value = false
    
    // 重置表单
    newChatForm.value = {
      mainCategory: 'normal',
      type: 'group',
      title: '',
      description: '',
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
  if (messageList.value) {
    messageList.value.scrollToBottom()
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
    
    // 使用 removeMessage 函数从消息列表中移除该消息
    removeMessage(message.id)
    
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

// 处理打开评论
const handleOpenComments = (message) => {
  if (!message || !message.id) return
  
  // 如果已经有关联的讨论组，跳转到讨论组的讨论模式
  if (currentConversation.value?.linked_discussion_id) {
    router.push({
      path: '/chat',
      query: {
        id: currentConversation.value.linked_discussion_id,
        rootId: message.id
      }
    })
  } else {
    ElMessage.warning('该频道尚未绑定讨论组')
  }
}

// 退出讨论模式
const exitDiscussionMode = () => {
  router.push({
    path: '/chat',
    query: {
      id: currentConversation.value.linked_channel_id || currentConversationId.value
    }
  })
}

// 加载根消息（频道原贴）
const loadRootMessage = async (messageId) => {
  try {
    const response = await api.get(`/chat/messages/${messageId}`)
    rootMessage.value = response.data
  } catch (error) {
    console.error('加载根消息失败:', error)
    ElMessage.error('加载原消息失败')
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

// 全局右键菜单管理
const handleShowContextMenu = (conversationId, position) => {
  // 关闭之前打开的菜单
  if (activeContextMenu.value !== null) {
    activeContextMenu.value = null
  }
  
  // 使用 nextTick 确保旧菜单已关闭，然后打开新菜单
  setTimeout(() => {
    activeContextMenu.value = conversationId
    contextMenuPosition.value = position
  }, 10)
}

const handleHideContextMenu = () => {
  activeContextMenu.value = null
}

const closeAllContextMenus = () => {
  activeContextMenu.value = null
}


// 处理置顶会话
const handlePinConversation = async (conversationId) => {
  try {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation) return
    
    const action = conversation.is_pinned ? 'unpin' : 'pin'
    await api.post(`/chat/conversations/${conversationId}/${action}`)
    
    // 更新本地状态
    conversation.is_pinned = !conversation.is_pinned
    ElMessage.success(conversation.is_pinned ? '已置顶' : '已取消置顶')
    
    // 重新加载对话列表以更新排序
    loadConversations()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

// 处理免打扰
const handleMuteConversation = async (conversationId) => {
  try {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation) return
    
    const action = conversation.is_muted ? 'unmute' : 'mute'
    await api.post(`/chat/conversations/${conversationId}/${action}`)
    
    // 更新本地状态
    conversation.is_muted = !conversation.is_muted
    ElMessage.success(conversation.is_muted ? '已开启免打扰' : '已取消免打扰')
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

// 处理标记为已读
const handleMarkAsRead = async (conversationId) => {
  try {
    await api.post(`/chat/conversations/${conversationId}/read`)
    
    // 更新本地状态
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      conversation.unread_count = 0
    }
    ElMessage.success('已标记为已读')
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

// 处理归档会话
const handleArchiveConversation = async (conversationId) => {
  try {
    await api.post(`/chat/conversations/${conversationId}/archive`)
    
    // 从列表中移除
    const index = conversations.value.findIndex(c => c.id === conversationId)
    if (index !== -1) {
      conversations.value.splice(index, 1)
    }
    
    // 如果当前正在查看这个会话，清空当前会话
    if (currentConversationId.value === conversationId) {
      currentConversationId.value = null
      allMessages.value = []
    }
    
    ElMessage.success('已归档')
  } catch (error) {
    console.error('归档失败:', error)
    ElMessage.error('归档失败')
  }
}

// 处理加入文件夹
const handleAddToFolder = (conversationId, folderId) => {
  if (folderId) {
    // 直接加入指定文件夹
    addConversationToFolder(folderId, conversationId)
  } else {
    // 打开文件夹选择对话框
    selectedConversationForFolder.value = conversationId
    showCreateFolderForm.value = false
    showAddToFolderDialog.value = true
  }
}

const handleOpenCreateFolder = (conversationId) => {
  selectedConversationForFolder.value = conversationId
  showCreateFolderForm.value = true
  showAddToFolderDialog.value = true
}

const getConversationName = (conversationId) => {
  const conv = conversations.value.find(c => c.id === conversationId)
  return conv?.title || '对话'
}

const addConversationToFolder = async (folderId, conversationId) => {
  const targetConvId = conversationId || selectedConversationForFolder.value
  try {
    await api.post(`/chat/folders/${folderId}/items`, {
      conversation_id: targetConvId
    })
    ElMessage.success('已加入文件夹')
    showAddToFolderDialog.value = false
    showCreateFolderForm.value = false
    await loadFolders()
  } catch (error) {
    console.error('加入文件夹失败:', error)
    ElMessage.error(error.response?.data?.error || '加入文件夹失败')
  }
}

const createFolderFromDialog = async () => {
  if (!newFolderNameInDialog.value.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  
  folderCreating.value = true
  try {
    const response = await api.post('/chat/folders', { 
      name: newFolderNameInDialog.value
    })
    const newFolderId = response.data.data?.id
    
    // 将当前群组加入到新创建的文件夹
    if (newFolderId && selectedConversationForFolder.value) {
      await api.post(`/chat/folders/${newFolderId}/items`, {
        conversation_id: selectedConversationForFolder.value
      })
    }
    
    ElMessage.success('文件夹创建成功，对话已加入')
    showAddToFolderDialog.value = false
    showCreateFolderForm.value = false
    newFolderNameInDialog.value = ''
    await loadFolders()
  } catch (error) {
    console.error('创建文件夹失败:', error)
    ElMessage.error('创建文件夹失败')
  } finally {
    folderCreating.value = false
  }
}

// 处理退出群组
const handleLeaveGroup = async (conversationId) => {
  try {
    await api.post(`/chat/conversations/${conversationId}/leave`)
    
    // 从列表中移除
    const index = conversations.value.findIndex(c => c.id === conversationId)
    if (index !== -1) {
      conversations.value.splice(index, 1)
    }
    
    // 如果当前正在查看这个会话，清空当前会话
    if (currentConversationId.value === conversationId) {
      currentConversationId.value = null
      allMessages.value = []
    }
    
    ElMessage.success('已退出群组')
  } catch (error) {
    console.error('退出失败:', error)
    ElMessage.error(error.response?.data?.error || '退出失败')
  }
}

const handleRemoveFromFolder = async (conversationId) => {
  if (!activeFolderId.value || activeFolderId.value === 'all' || activeFolderId.value === 'unread') {
    return
  }
  
  try {
    await ElMessageBox.confirm('确定要从文件夹中移除这个对话吗？', '提示', {
      confirmButtonText: '移除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/chat/folders/${activeFolderId.value}/items/${conversationId}`)
    ElMessage.success('已从文件夹中移除')
    await loadFolders()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除失败:', error)
      ElMessage.error('移除失败')
    }
  }
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
  newChatForm.value.description = ''
  newChatForm.value.members = []
  newChatForm.value.classId = null
}

const handleMainCategoryChange = () => {
  // 切换主分类时重置表单
  if (newChatForm.value.mainCategory === 'channel') {
    newChatForm.value.type = 'channel'
  } else {
    // 普通群组，默认为群聊
    newChatForm.value.type = 'group'
  }
  handleTypeChange()
}

const removeMessage = (messageId) => {
  const index = allMessages.value.findIndex(m => m.id === messageId)
  if (index !== -1) {
    allMessages.value.splice(index, 1)
  }
}

const updateMessage = (data) => {
  const message = allMessages.value.find(m => m.id === data.message_id)
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
  overflow: hidden;
}

/* 左侧栏 */
.chat-sidebar {
  width: 320px;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  overflow: hidden;
}

/* 对话列表区域 */
.conversation-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* 分类栏：位于搜索框下方 */
.category-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fff;
  border-bottom: 1px solid #e5e5e5;
  flex-shrink: 0;
  height: 36px;
}

.category-tabs {
  display: flex;
  gap: 24px;
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
}

.category-tabs::-webkit-scrollbar {
  display: none;
}

.category-tab {
  position: relative;
  padding: 10px 0;
  color: #606266;
  font-size: 14px;
  cursor: pointer;
  transition: color 0.3s;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.category-tab:hover {
  color: #409eff;
}

.category-tab.active {
  color: #409eff;
  font-weight: 500;
}

.category-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: #409eff;
}

.category-tab.folder-tab:hover .tab-delete-btn {
  display: inline-flex;
}

.tab-delete-btn {
  display: none;
  margin-left: 4px;
  padding: 0;
  width: 14px;
  height: 14px;
  border: none;
  background: transparent;
  color: #909399;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.tab-delete-btn:hover {
  color: #f56c6c;
}

.btn-add-folder {
  padding: 0;
  width: 24px;
  height: 24px;
  background: #fff;
  border: 1px solid #dcdfe6;
  cursor: pointer;
  color: #909399;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  flex-shrink: 0;
}

.btn-add-folder:hover {
  border-color: #409eff;
  color: #409eff;
}

.category-badge {
  margin-left: 4px;
  background: #f56c6c;
  color: white;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
  font-weight: 600;
  line-height: 1.5;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
  background: #fff;
  flex-shrink: 0;  /* 防止头部被压缩 */
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
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.btn-new-chat svg {
  display: block;
}

.btn-new-chat:hover {
  background: linear-gradient(135deg, #3a8ee6 0%, #409eff 100%);
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.search-box {
  padding: 12px 16px;
  background: #fff;
  flex-shrink: 0;  /* 防止搜索框被压缩 */
}

/* 占位符栏 */
.placeholder-bar {
  height: 8px;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.02), transparent);
  flex-shrink: 0;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

/* 群组列表滚动条样式 */
.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 3px;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
  transition: background 0.3s;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: #909399;
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
  overflow: hidden;  /* 防止整体滚动 */
  min-width: 0;  /* 重要：允许flex子元素正确收缩 */
  flex-direction: column;
  background: #fff;
  position: relative;
}

/* 右侧信息面板 */
.chat-info-panel {
  width: 300px;
  overflow: hidden;  /* 防止整体滚动 */
  display: flex;
  flex-direction: column;
  border-left: 1px solid #e5e5e5;
  background: #f8f9fa;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* 消息和输入区域统一容器 */
.chat-container {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* 滚动到底部按钮容器 */
.scroll-bottom-container {
  position: absolute;
  /* 相对于父容器（chat-container）定位，在输入框上方20px */
  bottom: 80px; /* 容器底padding(20px) + 输入框高度(40px) + 间距(20px) */
  /* 右侧与发送按钮对齐：容器右padding(28px) + telegram-input右padding(8px) = 36px */
  right: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  z-index: 100;
  /* 确保按钮在所有内容之上 */
  pointer-events: auto;
}

/* 未读消息数气泡 */
.unread-bubble {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 12px;
  margin-bottom: -10px; /* 关键：产生压盖效果 */
  z-index: 2;
  min-width: 20px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.4);
  animation: bounceIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* 圆形下滑按钮 */
.down-button {
  background: rgba(64, 158, 255, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  z-index: 1;
}

.down-button svg {
  color: white;
  transition: color 0.2s;
}

.scroll-bottom-container:hover .down-button {
  background: rgba(64, 158, 255, 1);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.scroll-bottom-container:hover .down-button svg {
  color: white;
}

.scroll-bottom-container:active .down-button {
  transform: translateY(0);
}

/* 弹出动画 */
@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Vue 过渡动画 */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.8);
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

/* Folder Tabs */
.folder-tabs-container {
  display: flex;
  align-items: center;
  flex-shrink: 0;  /* 防止被压缩 */
  padding: 0 8px;
  background: #fff;
  border-bottom: 1px solid #e5e5e5;
  height: 40px;
  position: relative;
}

.folder-tabs {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 0 12px;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: #dcdfe6 transparent;
}

.folder-tabs::-webkit-scrollbar {
  height: 4px;
}

.folder-tabs::-webkit-scrollbar-track {
  background: transparent;
}

.folder-tabs::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 2px;
}

.folder-tabs::-webkit-scrollbar-thumb:hover {
  background-color: #c0c4cc;
}

.folder-tab {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
  cursor: pointer;
  padding: 10px 8px 10px 0;
  position: relative;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.folder-name {
  flex: 1;
  font-size: 13px;
}

.folder-delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  background: transparent;
  color: #c0c4cc;
  opacity: 0;
  transition: all 0.2s;
  cursor: pointer;
  padding: 0;
  border-radius: 3px;
  flex-shrink: 0;
}

.folder-tab:hover .folder-delete-btn {
  opacity: 1;
}

.folder-delete-btn:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.folder-delete-btn svg {
  display: block;
}

.folder-tab.active {
  color: #409eff;
  font-weight: 500;
}

.folder-tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #409eff;
}

.folder-tab:hover {
  color: #409eff;
}

.badge-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: #f56c6c;
  border-radius: 50%;
  position: absolute;
  top: 6px;
  right: -8px;
}

.btn-add-folder {
  border: none;
  background: transparent;
  width: 28px;
  height: 28px;
  cursor: pointer;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.btn-add-folder svg {
  display: block;
}

.btn-add-folder:hover {
  background-color: #f0f2f5;
  color: #409eff;
}

/* Folder Selection Dialog */
.folder-selection {
  min-height: 200px;
}

.empty-folders {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-folders i {
  font-size: 48px;
  color: #dcdfe6;
  margin-bottom: 16px;
}

.empty-folders p {
  margin: 8px 0;
  font-size: 14px;
}

.empty-folders .hint {
  font-size: 12px;
  color: #c0c4cc;
}

.folder-list-selection {
  max-height: 400px;
  overflow-y: auto;
}

.folder-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e4e7ed;
  margin-bottom: 8px;
}

.folder-item:hover {
  background-color: #f5f7fa;
  border-color: #409eff;
}

.folder-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.folder-icon i {
  font-size: 20px;
  color: white;
}

.folder-info {
  flex: 1;
}

.folder-name {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.folder-count {
  font-size: 13px;
  color: #909399;
}

.folder-item > .el-icon-arrow-right {
  color: #c0c4cc;
  font-size: 16px;
}

.create-folder-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #409eff;
  font-size: 14px;
  margin-top: 8px;
}

.create-folder-trigger:hover {
  background-color: #ecf5ff;
  border-color: #409eff;
}

.create-folder-trigger i {
  font-size: 16px;
  margin-right: 8px;
}

/* Create Folder Form */
.create-folder-form {
  padding: 0;
}

.form-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.form-header .el-button {
  padding: 8px;
  margin-right: 8px;
}

.form-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.included-chats {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.chat-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background-color: #f0f2f5;
  border-radius: 16px;
  font-size: 13px;
  color: #606266;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.folder-option {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.folder-option:hover {
  background-color: #f5f7fa;
  border-color: #409eff;
}

.folder-option i {
  font-size: 16px;
}

.new-folder-btn {
  color: #409eff;
  border-style: dashed;
}

.new-folder-btn:hover {
  background-color: #ecf5ff;
}

/* 讨论模式样式 */
.discussion-mode-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.discussion-top-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 6px 16px;
  min-height: 42px;
  border-bottom: 1px solid #f0f0f0;
}

.back-btn {
  position: absolute;
  left: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 50%;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.discussion-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.root-message-card {
  background: #f9fafb;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.root-message-card:hover {
  background: #f0f2f5;
}

.root-sender {
  font-size: 12px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 3px;
}

.root-content {
  font-size: 13px;
  color: #303133;
  line-height: 1.4;
  margin-bottom: 3px;
  max-height: 36px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  transition: max-height 0.3s ease;
}

.root-content.expanded {
  max-height: none;
  -webkit-line-clamp: unset;
}

.root-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.expand-hint {
  color: #409eff;
  font-size: 11px;
}
</style>

.filter-indicator {
  padding: 8px 16px;
  background-color: #f0f9eb;
  border-bottom: 1px solid #e1f3d8;
  color: #67c23a;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}
