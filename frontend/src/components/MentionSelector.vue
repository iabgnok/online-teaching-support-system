<template>
  <transition name="fade">
    <div
      v-if="show && filteredMembers.length > 0"
      class="mention-selector"
      :style="{ top: position.top + 'px', left: position.left + 'px' }"
    >
      <div class="mention-list">
        <div
          v-for="(member, index) in filteredMembers"
          :key="member.user_id"
          class="mention-item"
          :class="{ active: index === selectedIndex }"
          @click="selectMember(member)"
          @mouseenter="selectedIndex = index"
        >
          <div class="member-avatar">
            <span class="avatar-text">{{ member.real_name.charAt(0) }}</span>
          </div>
          <div class="member-info">
            <div class="member-name">{{ member.real_name }}</div>
            <div class="member-username">@{{ member.username }}</div>
          </div>
          <div v-if="member.role === 'admin' || member.role === 'owner'" class="member-role">
            {{ member.role === 'owner' ? '群主' : '管理员' }}
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import api from '../api';

export default {
  name: 'MentionSelector',
  props: {
    conversationId: {
      type: Number,
      required: true
    },
    show: {
      type: Boolean,
      default: false
    },
    keyword: {
      type: String,
      default: ''
    },
    position: {
      type: Object,
      default: () => ({ top: 0, left: 0 })
    }
  },
  data() {
    return {
      members: [],
      selectedIndex: 0,
      loading: false
    };
  },
  computed: {
    filteredMembers() {
      if (!this.keyword) return this.members;
      
      const keyword = this.keyword.toLowerCase();
      return this.members.filter(member =>
        member.real_name.toLowerCase().includes(keyword) ||
        member.username.toLowerCase().includes(keyword)
      );
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        this.selectedIndex = 0;
        this.searchMembers();
      }
    },
    keyword() {
      this.selectedIndex = 0;
      this.searchMembers();
    },
    filteredMembers(newVal) {
      // 确保选中索引不超出范围
      if (this.selectedIndex >= newVal.length) {
        this.selectedIndex = Math.max(0, newVal.length - 1);
      }
    }
  },
  methods: {
    async searchMembers() {
      if (this.loading) return;
      
      this.loading = true;
      try {
        const response = await api.get(
          `/chat/conversations/${this.conversationId}/members/search`,
          { params: { q: this.keyword } }
        );
        this.members = response.data;
      } catch (error) {
        console.error('Search members failed:', error);
      } finally {
        this.loading = false;
      }
    },

    selectMember(member) {
      this.$emit('select', member);
      this.selectedIndex = 0;
    },

    selectNext() {
      if (this.filteredMembers.length === 0) return;
      this.selectedIndex = (this.selectedIndex + 1) % this.filteredMembers.length;
    },

    selectPrevious() {
      if (this.filteredMembers.length === 0) return;
      this.selectedIndex = (this.selectedIndex - 1 + this.filteredMembers.length) % this.filteredMembers.length;
    },

    selectCurrent() {
      if (this.filteredMembers.length > 0 && this.filteredMembers[this.selectedIndex]) {
        this.selectMember(this.filteredMembers[this.selectedIndex]);
      }
    }
  }
};
</script>

<style scoped>
.mention-selector {
  position: fixed;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  min-width: 260px;
  max-width: 320px;
  max-height: 280px;
  overflow: hidden;
  z-index: 1000;
}

.mention-list {
  overflow-y: auto;
  max-height: 280px;
}

.mention-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.2s;
  gap: 12px;
}

.mention-item:hover,
.mention-item.active {
  background: #f5f7fa;
}

.mention-item.active {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.avatar-text {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-username {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-role {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: linear-gradient(135deg, #ffd54f 0%, #ffb300 100%);
  color: #333;
  font-weight: 500;
  flex-shrink: 0;
}

/* 滚动条样式 */
.mention-list::-webkit-scrollbar {
  width: 6px;
}

.mention-list::-webkit-scrollbar-track {
  background: transparent;
}

.mention-list::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 3px;
}

.mention-list::-webkit-scrollbar-thumb:hover {
  background: #ccc;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
