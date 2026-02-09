<template>
  <div class="chat-switch-button" :class="{ active: isActive }">
    <button
      class="switch-btn"
      @click="$emit('switch', tabType)"
      :class="{ active: isActive }"
    >
      <div class="btn-content">
        <div class="icon-wrapper">
          <slot name="icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path v-if="tabType === 'discussion'" d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              <path v-else d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle v-if="tabType !== 'discussion'" cx="9" cy="7" r="4"></circle>
              <path v-if="tabType !== 'discussion'" d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path v-if="tabType !== 'discussion'" d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </slot>
        </div>
        <div class="text-content">
          <span class="label">{{ label }}</span>
          <span v-if="unreadCount > 0" class="unread-indicator">{{ formattedUnread }}</span>
        </div>
      </div>
      <div v-if="isActive" class="active-indicator"></div>
    </button>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'ChatSwitchButton',
  props: {
    tabType: {
      type: String,
      required: true,
      validator: (value) => ['discussion', 'classGroup', 'private'].includes(value)
    },
    label: {
      type: String,
      required: true
    },
    unreadCount: {
      type: Number,
      default: 0
    },
    isActive: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['switch'],
  computed: {
    formattedUnread() {
      return this.unreadCount > 99 ? '99+' : this.unreadCount
    }
  }
}
</script>

<style scoped>
.chat-switch-button {
  position: relative;
}

.switch-btn {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.switch-btn:hover {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.switch-btn.active {
  background: #409eff;
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.switch-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.2);
  transition: all 0.2s ease;
}

.switch-btn:not(.active) .icon-wrapper {
  background: rgba(0, 0, 0, 0.05);
}

.switch-btn.active .icon-wrapper {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.text-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
}

.label {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.unread-indicator {
  background: #ff4d4f;
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 10px;
  min-width: 16px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(255, 77, 79, 0.3);
}

.switch-btn.active .unread-indicator {
  background: rgba(255, 255, 255, 0.9);
  color: #409eff;
}

.active-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: white;
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .switch-btn {
    padding: 10px 12px;
  }

  .btn-content {
    gap: 8px;
  }

  .icon-wrapper {
    width: 28px;
    height: 28px;
  }

  .label {
    font-size: 13px;
  }
}

/* 动画效果 */
.switch-btn {
  transform: translateX(0);
}

.switch-btn:active {
  transform: translateX(1px);
}

.unread-indicator {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}
</style>