<template>
  <div class="chat-view">
    <!-- 悬浮直播状态 -->
    <LiveStatusBanner v-if="showLiveStatus" />

    <!-- 左侧：对话列表 -->
    <div class="chat-sidebar">
      <div class="conversation-area">
        <div class="sidebar-header">
          <h2>{{ sidebarTitle }}</h2>
          <BaseButton
            v-if="showNewChatButton"
            size="small"
            @click="$emit('new-chat')"
          >
            新建
          </BaseButton>
        </div>

        <BaseInput
          v-if="showSearch"
          v-model="searchQuery"
          placeholder="搜索对话..."
          style="margin-bottom: 12px;"
        />

        <div class="conversation-list">
          <ConversationItem
            v-for="conv in filteredConversations"
            :key="conv.id"
            :conversation="conv"
            :active="currentConversationId === conv.id"
            @click="$emit('select-conversation', conv.id)"
          />

          <div v-if="filteredConversations.length === 0" class="empty-state">
            <p>暂无对话</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：聊天窗口 -->
    <div class="chat-main">
      <ChatWindow
        v-if="currentConversation"
        :title="currentConversation.title"
        :participants="currentConversation.participants"
        :messages="messages"
        :current-user="currentUser"
        :conversation-id="currentConversationId"
        :conversation-subtype="currentConversation.subtype"
        :user-role="userRole"
        @send="handleSendMessage"
        @close="$emit('close-chat')"
      />
      <div v-else class="chat-placeholder">
        <p>选择一个对话开始聊天</p>
      </div>
    </div>
  </div>
</template>

<script>
import BaseInput from '../common/ui/BaseInput.vue'
import BaseButton from '../common/ui/BaseButton.vue'
import ConversationItem from './ConversationItem.vue'
import ChatWindow from './ChatWindow.vue'
import LiveStatusBanner from '../live-class/LiveStatusBanner.vue'

export default {
  name: 'ChatView',
  components: {
    BaseInput,
    BaseButton,
    ConversationItem,
    ChatWindow,
    LiveStatusBanner
  },
  props: {
    conversations: {
      type: Array,
      default: () => []
    },
    currentConversationId: {
      type: [String, Number],
      default: null
    },
    messages: {
      type: Array,
      default: () => []
    },
    currentUser: {
      type: Object,
      required: true
    },
    sidebarTitle: {
      type: String,
      default: '对话列表'
    },
    showSearch: {
      type: Boolean,
      default: true
    },
    showNewChatButton: {
      type: Boolean,
      default: true
    },
    userRole: {
      type: String,
      default: 'student'
    }
  },
  emits: ['select-conversation', 'send-message', 'new-chat', 'close-chat'],
  data() {
    return {
      searchQuery: ''
    }
  },
  computed: {
    currentConversation() {
      return this.conversations.find(conv => conv.id === this.currentConversationId)
    },
    filteredConversations() {
      if (!this.searchQuery.trim()) {
        return this.conversations
      }
      const query = this.searchQuery.toLowerCase()
      return this.conversations.filter(conv =>
        conv.title.toLowerCase().includes(query) ||
        conv.lastMessage?.toLowerCase().includes(query)
      )
    }
  },
  methods: {
    handleSendMessage(message) {
      this.$emit('send-message', {
        conversationId: this.currentConversationId,
        message
      })
    }
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

.chat-sidebar {
  width: 320px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.conversation-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.empty-state p {
  margin: 0 0 16px 0;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  color: #999;
}
</style>