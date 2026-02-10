<template>
  <div class="chat-window-container" :class="{ 'live-mode': isLiveMode }">
    <!-- 头部 -->
    <ChatHeader 
      v-if="!hideHeader && !isDiscussionMode"
      :conversation="conversation"
      @show-info="$emit('show-info')"
    />

    <!-- 置顶消息 -->
    <PinnedMessageBar
      v-if="!hidePinnedBar"
      ref="pinnedMessageBar"
      :conversation-id="conversationId"
      :can-unpin="canUnpin"
      @jump-to-message="$emit('jump-to-message', $event)"
      @message-unpinned="$emit('message-unpinned', $event)" 
    />

    <!-- 讨论模式头部 -->
    <div v-if="isDiscussionMode" class="discussion-mode-header">
      <div class="discussion-top-bar">
        <button class="back-btn" @click="$emit('exit-discussion')" title="返回频道">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <span class="discussion-title">讨论详情</span>
      </div>
      
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

    <!-- 筛选提示 -->
    <div v-if="messageFilterType" class="filter-indicator">
      <span>
        <i class="el-icon-filter"></i>
        正在筛选: {{ messageFilterType === 'image' ? '图片' : messageFilterType === 'file' ? '文件' : '链接' }}
      </span>
      <el-button type="text" size="small" @click="$emit('clear-filter')" style="margin-left: 10px">清除筛选</el-button>
    </div>
    
    <!-- 消息列表 -->
    <div class="message-area-wrapper">
      <MessageList 
        ref="messageListRef"
        :conversation-id="conversationId"
        :messages="messages"
        :conversation-subtype="conversationSubtype"
        :role="userRole"
        @load-more="$emit('load-more')"
        @reply="$emit('reply', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
        @open-comments="$emit('open-comments', $event)"
        @scroll-button-change="showScrollButton = $event"
        @unread-count-change="unreadCount = $event"
      />
      
      <!-- 下滑按钮 -->
      <BetterScrollDownButton 
        :show="showScrollButton" 
        :unread-count="unreadCount"
        @click="scrollToBottom"
      />
    </div>

    <!-- 输入框 -->
    <MessageInput 
      ref="messageInputRef"
      :conversation-id="conversationId"
      :conversation-subtype="conversationSubtype"
      :discussion-mode="isDiscussionMode"
      :reply-to="replyToMessage"
      :editing-message="editingMessage"
      :role="userRole"
      :show-classroom-features="showClassroomFeatures"
      @send="$emit('send', $event)"
      @cancel-reply="$emit('cancel-reply')"
      @cancel-edit="$emit('cancel-edit')"
      @typing="$emit('typing', $event)"
      @start-attendance="$emit('start-attendance')"
      @publish-task="$emit('publish-task')"
      @share-board="$emit('share-board')"
      @raise-hand="$emit('raise-hand', $event)"
      @screen-share="$emit('screen-share')"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import ChatHeader from './ChatHeader.vue'
import PinnedMessageBar from './PinnedMessageBar.vue'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'
import BetterScrollDownButton from './ScrollDownButton.vue'
import { formatTime } from '@/utils/timeUtils'

const props = defineProps({
  conversationId: [Number, String],
  conversation: Object,
  messages: Array,
  conversationSubtype: String,
  userRole: {
    type: String,
    default: 'student'
  },
  isLiveMode: Boolean,
  hideHeader: Boolean,
  hidePinnedBar: Boolean,
  isDiscussionMode: Boolean,
  rootMessage: Object,
  messageFilterType: String,
  replyToMessage: Object,
  editingMessage: Object,
  canUnpin: Boolean,
  showClassroomFeatures: Boolean
})

const emit = defineEmits([
  'show-info',
  'jump-to-message',
  'message-unpinned',
  'exit-discussion',
  'clear-filter',
  'load-more',
  'reply',
  'edit',
  'delete',
  'open-comments',
  'send',
  'cancel-reply',
  'cancel-edit',
  'typing',
  'start-attendance',
  'publish-task',
  'share-board',
  'raise-hand',
  'screen-share'
])

const messageListRef = ref(null)
const messageInputRef = ref(null)
const showScrollButton = ref(false)
const unreadCount = ref(0)
const rootMessageExpanded = ref(false)

const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollToBottom()
  }
}

onMounted(() => {
})

onUnmounted(() => {
})

defineExpose({
  scrollToBottom,
  messageListRef,
  messageInputRef
})
</script>

<style scoped>
.chat-window-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  position: relative;
  overflow: hidden;
  gap: 0; /* 去除间隙 */
}

.chat-window-container.live-mode {
  border-radius: 0;
}

.message-area-wrapper {
  flex: 1;
  position: relative;
  min-height: 0;
}

/* 讨论模式样式 */
.discussion-mode-header {
  background: #fff;
  border-bottom: 1px solid #f0f2f5;
  padding: 8px 16px;
}

.discussion-top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 48px;
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
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f1f5f9;
  color: #409eff;
}

.discussion-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.root-message-card {
  margin-top: 8px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
  border-left: 4px solid #409eff;
  cursor: pointer;
  transition: all 0.2s;
}

.root-message-card:hover {
  background: #f1f5f9;
}

.root-sender {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 4px;
}

.root-content {
  font-size: 14px;
  color: #334155;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.root-content.expanded {
  -webkit-line-clamp: unset;
}

.root-meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #94a3b8;
}

.expand-hint {
  color: #409eff;
}

/* 直播模式下全局容器的调整 */
.chat-window-container.live-mode {
  border: none;
  border-radius: 0;
  box-shadow: none;
}

/* 直播模式下的子组件样式穿透 */
.chat-window-container.live-mode :deep(.message-list) {
  border-radius: 0;
}

.chat-window-container.live-mode :deep(.message-input) {
  border-radius: 0;
  border-top: 1px solid #e9ecef;
}
</style>