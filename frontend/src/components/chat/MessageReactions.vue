<template>
  <div class="message-reactions">
    <!-- 反应选择面板 -->
    <transition name="slide-up">
      <div v-if="showPicker" class="reaction-picker">
        <div class="reaction-picker-content">
          <button
            v-for="emoji in availableReactions"
            :key="emoji"
            class="reaction-option"
            @click="toggleReaction(emoji)"
            :class="{ active: hasMyReaction(emoji) }"
          >
            {{ emoji }}
          </button>
        </div>
      </div>
    </transition>

    <!-- 已有的反应显示 -->
    <div v-if="reactions.length > 0" class="reactions-display">
      <button
        v-for="reaction in reactions"
        :key="reaction.reaction"
        class="reaction-bubble"
        :class="{ 'my-reaction': reaction.i_reacted }"
        @click="toggleReaction(reaction.reaction)"
        :title="getReactionTooltip(reaction)"
      >
        <span class="reaction-emoji">{{ reaction.reaction }}</span>
        <span class="reaction-count">{{ reaction.count }}</span>
      </button>
      
      <!-- 添加反应按钮 -->
      <button 
        class="add-reaction-btn"
        @click="showPicker = !showPicker"
        title="添加反应"
      >
        <span>+</span>
      </button>
    </div>

    <!-- 如果没有反应，只显示添加按钮 -->
    <div v-else-if="canReact" class="no-reactions">
      <button 
        class="add-reaction-btn"
        @click="showPicker = !showPicker"
        title="添加反应"
      >
        <span>😊</span>
      </button>
    </div>
  </div>
</template>

<script>
import api from '../../api';

export default {
  name: 'MessageReactions',
  props: {
    messageId: {
      type: Number,
      required: true
    },
    initialReactions: {
      type: Array,
      default: () => []
    },
    canReact: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      reactions: [...this.initialReactions],
      showPicker: false,
      availableReactions: ['👍', '❤️', '😂', '😮', '😢', '🙏', '🔥', '👏'],
      loading: false
    };
  },
  watch: {
    initialReactions: {
      handler(newVal) {
        this.reactions = [...newVal];
      },
      deep: true
    }
  },
  methods: {
    async toggleReaction(emoji) {
      if (!this.canReact || this.loading) return;
      
      this.loading = true;
      this.showPicker = false;

      try {
        const response = await api.post(
          `/chat/messages/${this.messageId}/reactions`,
          { reaction: emoji }
        );

        // 重新获取反应列表
        await this.fetchReactions();
        
        this.$emit('reaction-changed', {
          messageId: this.messageId,
          action: response.data.action
        });
      } catch (error) {
        console.error('Toggle reaction failed:', error);
        this.$message?.error('操作失败：' + (error.response?.data?.error || error.message));
      } finally {
        this.loading = false;
      }
    },

    async fetchReactions() {
      try {
        const response = await api.get(
          `/chat/messages/${this.messageId}/reactions`
        );
        this.reactions = response.data;
      } catch (error) {
        console.error('Fetch reactions failed:', error);
      }
    },

    hasMyReaction(emoji) {
      const reaction = this.reactions.find(r => r.reaction === emoji);
      return reaction && reaction.i_reacted;
    },

    getReactionTooltip(reaction) {
      if (reaction.count === 1 && reaction.i_reacted) {
        return '您';
      }
      // 这里可以扩展显示具体用户名
      return `${reaction.count} 人`;
    }
  }
};
</script>

<style scoped>
.message-reactions {
  position: relative;
  margin-top: 4px;
}

/* 反应选择面板 */
.reaction-picker {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  z-index: 100;
}

.reaction-picker-content {
  background: white;
  border-radius: 24px;
  padding: 8px 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  gap: 4px;
}

.reaction-option {
  border: none;
  background: transparent;
  font-size: 24px;
  cursor: pointer;
  padding: 6px;
  border-radius: 50%;
  transition: all 0.2s;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reaction-option:hover {
  background: #f0f0f0;
  transform: scale(1.2);
}

.reaction-option.active {
  background: #e3f2fd;
}

/* 反应显示 */
.reactions-display {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.reaction-bubble {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  background: #f0f0f0;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.reaction-bubble:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}

.reaction-bubble.my-reaction {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-color: #2196f3;
}

.reaction-emoji {
  font-size: 16px;
  line-height: 1;
}

.reaction-count {
  font-size: 13px;
  font-weight: 500;
  color: #666;
}

.my-reaction .reaction-count {
  color: #1976d2;
}

.add-reaction-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px dashed #ccc;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
  color: #999;
}

.add-reaction-btn:hover {
  background: #f5f5f5;
  border-color: #999;
  color: #666;
  transform: scale(1.1);
}

.no-reactions {
  display: inline-flex;
}

/* 动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.2s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
