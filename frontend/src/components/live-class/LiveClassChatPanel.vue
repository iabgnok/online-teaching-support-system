<template>
  <div class="live-class-chat-panel">
    <!-- 聊天头部横幅 - 引入聊天模块样式 -->
    <div class="chat-header">
      <div class="header-content">
        <!-- 左侧：标题和在线状态 -->
        <div class="header-left">
          <div class="conv-info">
            <div class="conv-title">{{ activeTab === 'discussion' ? '💬 课堂讨论' : '👥 班级群聊' }}</div>
            <div class="conv-subtitle">
              <span class="status-online" v-if="isOnline">● {{ onlineCount }} 人在线</span>
              <span class="status-offline" v-else>离线</span>
            </div>
          </div>
        </div>

        <!-- 右侧：切换按钮和折叠按钮 -->
        <div class="header-actions">
          <!-- 切换按钮 -->
          <button
            class="action-btn tab-switch-btn"
            @click="switchTab"
            :title="activeTab === 'discussion' ? '切换到班级群聊' : '切换到课堂讨论'"
          >
            <svg v-if="activeTab === 'discussion'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span v-if="getUnreadCount() > 0" class="unread-badge">{{ getUnreadCount() }}</span>
          </button>

          <!-- 折叠按钮 -->
          <button
            class="action-btn collapse-btn"
            @click="$emit('toggle-collapse')"
            :title="isCollapsed ? '展开聊天面板' : '收起聊天面板'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: isCollapsed }">
              <path d="M6 9l6 6 6-6"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 聊天内容区域 - 按照ChatWindow布局 -->
    <div class="chat-content">
      <!-- 消息列表区域 -->
      <div class="messages-container">
        <MessageList
          ref="messageListRef"
          :conversation-id="currentConversationId"
          :messages="currentMessages"
          :conversation-subtype="activeTab === 'discussion' ? 'live_class_discussion' : 'normal'"
          :role="role"
          @load-more="handleLoadMore"
          @reply="handleReply"
          @edit="handleEdit"
          @delete="handleDelete"
          @open-comments="handleOpenComments"
        />
      </div>

      <!-- 消息输入区域 -->
      <div class="input-container">
        <MessageInput
          ref="messageInputRef"
          :conversation-id="currentConversationId"
          :conversation-subtype="activeTab === 'discussion' ? 'live_class_discussion' : 'normal'"
          :reply-to="replyToMessage"
          :editing-message="editingMessage"
          :show-classroom-features="activeTab === 'discussion'"
          :role="role"
          @send="handleSendMessage"
          @cancel-reply="replyToMessage = null"
          @cancel-edit="editingMessage = null"
          @typing="handleTyping"
          @start-attendance="$emit('start-attendance')"
          @publish-task="$emit('publish-task')"
          @share-board="$emit('share-board')"
          @raise-hand="$emit('raise-hand', $event)"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue'
import MessageList from '../chat/MessageList.vue'
import MessageInput from '../chat/MessageInput.vue'

export default {
  name: 'LiveClassChatPanel',
  components: {
    MessageList,
    MessageInput
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
    // 是否在线
    isOnline: {
      type: Boolean,
      default: true
    },
    // 在线人数
    onlineCount: {
      type: Number,
      default: 0
    },
    // 是否折叠
    isCollapsed: {
      type: Boolean,
      default: false
    },
    // 讨论标签
    discussionLabel: {
      type: String,
      default: '课堂讨论'
    },
    // 班级群标签
    classGroupLabel: {
      type: String,
      default: '班级群聊'
    },
    // 讨论未读数
    discussionUnread: {
      type: Number,
      default: 0
    },
    // 班级群未读数
    classGroupUnread: {
      type: Number,
      default: 0
    }
  },
  emits: [
    'switch-tab',
    'send-message',
    'load-more',
    'reply',
    'edit',
    'delete',
    'open-comments',
    'react',
    'pin',
    'toggle-collapse'
  ],
  setup(props, { emit }) {
    const activeTab = ref('discussion')
    const replyToMessage = ref(null)
    const editingMessage = ref(null)

    // 当前对话ID
    const currentConversationId = computed(() => {
      return activeTab.value === 'discussion'
        ? props.discussionConversationId
        : props.classGroupConversationId
    })

    // 当前消息列表（需要从父组件传入）
    const currentMessages = computed(() => {
      // 这里需要父组件提供消息数据
      return []
    })

    // 切换标签
    const switchTab = () => {
      activeTab.value = activeTab.value === 'discussion' ? 'classGroup' : 'discussion'
      emit('switch-tab', activeTab.value)
    }

    // 获取未读消息数量
    const getUnreadCount = () => {
      return activeTab.value === 'discussion'
        ? props.classGroupUnread
        : props.discussionUnread
    }

    // 消息处理方法
    const handleSendMessage = (message) => {
      emit('send-message', {
        ...message,
        tab: activeTab.value
      })
    }

    const handleLoadMore = () => {
      emit('load-more', activeTab.value)
    }

    const handleReply = (data) => {
      emit('reply', { ...data, tab: activeTab.value })
    }

    const handleEdit = (data) => {
      emit('edit', { ...data, tab: activeTab.value })
    }

    const handleDelete = (data) => {
      emit('delete', { ...data, tab: activeTab.value })
    }

    const handleOpenComments = (data) => {
      emit('open-comments', { ...data, tab: activeTab.value })
    }

    const handleReact = (data) => {
      emit('react', { ...data, tab: activeTab.value })
    }

    const handlePin = (data) => {
      emit('pin', { ...data, tab: activeTab.value })
    }

    return {
      activeTab,
      currentConversationId,
      currentMessages,
      switchTab,
      getUnreadCount,
      handleSendMessage,
      handleLoadMore,
      handleReply,
      handleEdit,
      handleDelete,
      handleOpenComments,
      handleReact,
      handlePin
    }
  }
}
</script>

<style scoped>
.live-class-chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* 聊天头部横幅 - 引入聊天模块样式 */
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
  position: relative;
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

/* 切换按钮特殊样式 */
.tab-switch-btn {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.tab-switch-btn:hover {
  background: rgba(64, 158, 255, 0.2);
}

/* 未读消息徽章 */
.unread-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #ff4757;
  color: white;
  border-radius: 10px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: bold;
  min-width: 16px;
  text-align: center;
  border: 2px solid white;
}

/* 折叠按钮 */
.collapse-btn {
  background: rgba(142, 142, 147, 0.1);
}

.collapse-btn:hover {
  background: rgba(142, 142, 147, 0.2);
}

.rotated {
  transform: rotate(180deg);
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow: hidden;
}

.input-container {
  border-top: 1px solid #e9ecef;
  background: white;
}

.chat-switcher {
  display: flex;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  padding: 8px;
  gap: 4px;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.online-status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-size: 13px;
  color: #666;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.online-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
  transition: background-color 0.3s ease;
}

.online-dot.active {
  background: #52c41a;
  box-shadow: 0 0 6px rgba(82, 196, 26, 0.4);
}

.online-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #999;
}

.chat-window-container {
  flex: 1;
  overflow: hidden;
}

.panel-controls {
  display: flex;
  justify-content: flex-end;
  padding: 8px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #666;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.rotated {
  transform: rotate(180deg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-switcher {
    padding: 6px;
  }

  .online-status-bar {
    padding: 6px 12px;
    font-size: 12px;
  }

  .panel-controls {
    padding: 6px;
  }
}

/* 动画效果 */
.live-class-chat-panel {
  transition: all 0.3s ease;
}

.chat-switcher {
  transition: all 0.3s ease;
}

.online-status-bar {
  transition: all 0.3s ease;
}
</style>