<template>
  <transition name="slide-down">
    <div v-if="pinnedMessages.length > 0" class="pinned-message-bar">
      <div class="pinned-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16,12V4H17V2H7V4H8V12L6,14V16H11.2V22H12.8V16H18V14L16,12Z" />
        </svg>
      </div>

      <div class="pinned-content">
        <div class="pinned-header">
          <span class="pinned-label">置顶消息</span>
          <span v-if="pinnedMessages.length > 1" class="pinned-count">
            {{ currentIndex + 1 }} / {{ pinnedMessages.length }}
          </span>
        </div>

        <div class="pinned-message" @click="jumpToMessage(currentMessage)">
          <div class="pinned-sender">{{ currentMessage.pinned_by }}</div>
          <div class="pinned-text">{{ formatContent(currentMessage.content) }}</div>
        </div>
      </div>

      <div class="pinned-actions">
        <!-- 多条置顶消息时显示切换按钮 -->
        <button
          v-if="pinnedMessages.length > 1"
          class="nav-btn"
          @click="previousMessage"
          title="上一条"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z" />
          </svg>
        </button>

        <button
          v-if="pinnedMessages.length > 1"
          class="nav-btn"
          @click="nextMessage"
          title="下一条"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" />
          </svg>
        </button>

        <!-- 管理员可以取消置顶 -->
        <button
          v-if="canUnpin"
          class="unpin-btn"
          @click="unpinMessage(currentMessage)"
          title="取消置顶"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" />
          </svg>
        </button>

        <button class="close-btn" @click="$emit('close')" title="关闭">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" />
          </svg>
        </button>
      </div>
    </div>
  </transition>
</template>

<script>
import api from '../api';

export default {
  name: 'PinnedMessageBar',
  props: {
    conversationId: {
      type: Number,
      required: true
    },
    canUnpin: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      pinnedMessages: [],
      currentIndex: 0,
      loading: false
    };
  },
  computed: {
    currentMessage() {
      return this.pinnedMessages[this.currentIndex] || null;
    }
  },
  watch: {
    conversationId: {
      immediate: true,
      handler() {
        this.fetchPinnedMessages();
      }
    }
  },
  methods: {
    async fetchPinnedMessages() {
      if (this.loading) return;
      
      this.loading = true;
      try {
        const response = await api.get(
          `/chat/conversations/${this.conversationId}/pinned_messages`
        );
        this.pinnedMessages = response.data;
        this.currentIndex = 0;
      } catch (error) {
        console.error('Fetch pinned messages failed:', error);
      } finally {
        this.loading = false;
      }
    },

    async unpinMessage(message) {
      if (!this.canUnpin) return;

      try {
        await this.$confirm('确定要取消置顶这条消息吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        });

        await api.delete(`/chat/pinned_messages/${message.pin_id}`);
        
        this.$message.success('已取消置顶');
        await this.fetchPinnedMessages();
        
        this.$emit('message-unpinned', message);
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Unpin message failed:', error);
          this.$message?.error('取消置顶失败：' + (error.response?.data?.error || error.message));
        }
      }
    },

    jumpToMessage(message) {
      this.$emit('jump-to-message', message.message_id);
    },

    nextMessage() {
      this.currentIndex = (this.currentIndex + 1) % this.pinnedMessages.length;
    },

    previousMessage() {
      this.currentIndex = (this.currentIndex - 1 + this.pinnedMessages.length) % this.pinnedMessages.length;
    },

    formatContent(content) {
      if (!content) return '';
      // 截断过长的内容
      return content.length > 100 ? content.substring(0, 100) + '...' : content;
    },

    // 外部调用以刷新置顶消息
    refresh() {
      this.fetchPinnedMessages();
    }
  }
};
</script>

<style scoped>
.pinned-message-bar {
  background: linear-gradient(135deg, #fff9e6 0%, #fffaf0 100%);
  border-bottom: 1px solid #ffd54f;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.pinned-icon {
  flex-shrink: 0;
  color: #ff9800;
  display: flex;
  align-items: center;
}

.pinned-content {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.pinned-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.pinned-label {
  font-size: 12px;
  font-weight: 600;
  color: #f57c00;
  text-transform: uppercase;
}

.pinned-count {
  font-size: 11px;
  color: #666;
  background: rgba(255, 152, 0, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

.pinned-message {
  transition: opacity 0.2s;
}

.pinned-message:hover {
  opacity: 0.8;
}

.pinned-sender {
  font-size: 12px;
  font-weight: 500;
  color: #666;
  margin-bottom: 2px;
}

.pinned-text {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pinned-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.nav-btn,
.unpin-btn,
.close-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #666;
}

.nav-btn:hover,
.close-btn:hover {
  background: rgba(255, 152, 0, 0.1);
  color: #f57c00;
}

.unpin-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

/* 动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from {
  opacity: 0;
  transform: translateY(-100%);
}

.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}
</style>
