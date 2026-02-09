<template>
  <el-dialog
    v-model="visible"
    title="转发消息"
    width="500px"
    :before-close="handleClose"
  >
    <div class="forward-dialog">
      <!-- 搜索框 -->
      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索对话..."
          prefix-icon="el-icon-search"
          clearable
        />
      </div>

      <!-- 对话列表 -->
      <div class="conversation-list">
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ selected: isSelected(conv.id) }"
          @click="toggleSelection(conv.id)"
        >
          <div class="checkbox">
            <svg v-if="isSelected(conv.id)" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10,17L5,12L6.41,10.58L10,14.17L17.59,6.58L19,8M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
            </svg>
          </div>

          <div class="conv-avatar">
            <span class="avatar-text">{{ conv.title.charAt(0) }}</span>
          </div>

          <div class="conv-info">
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-type">{{ getTypeLabel(conv.type) }}</div>
          </div>

          <div v-if="conv.is_pinned" class="conv-badge">📌</div>
        </div>

        <div v-if="filteredConversations.length === 0" class="empty-state">
          <div class="empty-icon">💬</div>
          <div class="empty-text">没有找到对话</div>
        </div>
      </div>

      <!-- 已选择的统计 -->
      <div v-if="selectedIds.length > 0" class="selected-info">
        已选择 {{ selectedIds.length }} 个对话
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="forwarding"
          :disabled="selectedIds.length === 0"
          @click="handleForward"
        >
          转发 ({{ selectedIds.length }})
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import api from '../../api';

export default {
  name: 'ForwardDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    messageId: {
      type: Number,
      default: null
    },
    currentConversationId: {
      type: Number,
      default: null
    }
  },
  emits: ['update:modelValue', 'forward-success'],
  data() {
    return {
      conversations: [],
      selectedIds: [],
      searchKeyword: '',
      forwarding: false,
      loading: false
    };
  },
  computed: {
    visible: {
      get() {
        return this.modelValue;
      },
      set(val) {
        this.$emit('update:modelValue', val);
      }
    },
    filteredConversations() {
      let filtered = this.conversations;

      // 过滤掉当前对话
      if (this.currentConversationId) {
        filtered = filtered.filter(c => c.id !== this.currentConversationId);
      }

      // 搜索过滤
      if (this.searchKeyword) {
        const keyword = this.searchKeyword.toLowerCase();
        filtered = filtered.filter(c =>
          c.title.toLowerCase().includes(keyword)
        );
      }

      return filtered;
    }
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.fetchConversations();
        this.selectedIds = [];
      }
    }
  },
  methods: {
    async fetchConversations() {
      if (this.loading) return;

      this.loading = true;
      try {
        const response = await api.get('/chat/conversations');
        this.conversations = response.data;
      } catch (error) {
        console.error('Fetch conversations failed:', error);
        this.$message?.error('加载对话列表失败');
      } finally {
        this.loading = false;
      }
    },

    toggleSelection(convId) {
      const index = this.selectedIds.indexOf(convId);
      if (index > -1) {
        this.selectedIds.splice(index, 1);
      } else {
        this.selectedIds.push(convId);
      }
    },

    isSelected(convId) {
      return this.selectedIds.includes(convId);
    },

    getTypeLabel(type) {
      const labels = {
        private: '私聊',
        group: '群聊',
        class_group: '班级群',
        course_group: '课程群',
        live_class: '直播课'
      };
      return labels[type] || type;
    },

    async handleForward() {
      if (this.selectedIds.length === 0) {
        this.$message?.warning('请选择至少一个对话');
        return;
      }

      if (!this.messageId) {
        this.$message?.error('消息ID缺失');
        return;
      }

      this.forwarding = true;
      try {
        const response = await api.post(
          `/chat/messages/${this.messageId}/forward`,
          { conversation_ids: this.selectedIds }
        );

        this.$message?.success(response.data.message);
        this.$emit('forward-success', {
          messageId: this.messageId,
          conversationIds: this.selectedIds,
          count: response.data.count
        });

        this.visible = false;
      } catch (error) {
        console.error('Forward message failed:', error);
        this.$message?.error('转发失败：' + (error.response?.data?.error || error.message));
      } finally {
        this.forwarding = false;
      }
    },

    handleClose() {
      this.visible = false;
      this.selectedIds = [];
      this.searchKeyword = '';
    }
  }
};
</script>

<style scoped>
.forward-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-box {
  padding: 0;
}

.conversation-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 12px;
  border-bottom: 1px solid #f5f5f5;
}

.conversation-item:last-child {
  border-bottom: none;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.selected {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
}

.checkbox {
  color: #409eff;
  flex-shrink: 0;
}

.conversation-item:not(.selected) .checkbox {
  color: #ccc;
}

.conv-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.avatar-text {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-type {
  font-size: 12px;
  color: #999;
}

.conv-badge {
  font-size: 16px;
  flex-shrink: 0;
}

.selected-info {
  padding: 8px 12px;
  background: #e3f2fd;
  border-radius: 6px;
  font-size: 14px;
  color: #1976d2;
  font-weight: 500;
  text-align: center;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
  color: #999;
}

/* 滚动条样式 */
.conversation-list::-webkit-scrollbar {
  width: 6px;
}

.conversation-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 3px;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: #ccc;
}
</style>
