<template>
  <transition name="fade-scale">
    <div 
      v-if="show" 
      class="scroll-down-button-container" 
      @click="$emit('click')"
    >
      <!-- 未读消息数气泡 -->
      <div v-if="unreadCount > 0" class="unread-bubble">
        {{ formattedUnreadCount }}
      </div>
      <!-- 圆形按钮 -->
      <div class="down-button">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="7 10 12 15 17 10"></polyline>
        </svg>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  unreadCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['click'])

const formattedUnreadCount = computed(() => {
  return props.unreadCount > 99 ? '99+' : props.unreadCount
})
</script>

<style scoped>
.scroll-down-button-container {
  position: absolute;
  bottom: 78px;
  right: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  z-index: 1000; /* 调高 z-index 确保不被覆盖 */
  pointer-events: auto;
}

.unread-bubble {
  background: linear-gradient(135deg, #409eff, #66b1ff);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 12px;
  margin-bottom: -10px;
  z-index: 2;
  min-width: 18px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.4);
  animation: bounceIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.down-button {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.down-button svg {
  color: #409eff;
  transition: transform 0.2s;
}

.scroll-down-button-container:hover .down-button {
  background: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.scroll-down-button-container:active .down-button {
  transform: translateY(0) scale(0.95);
}

/* 动画 */
.fade-scale-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.fade-scale-leave-active {
  transition: all 0.2s ease;
}

.fade-scale-enter-from {
  opacity: 0;
  transform: scale(0.5) translateY(20px);
}

.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.5) translateY(20px);
}

@keyframes bounceIn {
  0% { opacity: 0; transform: scale(0.3); }
  50% { transform: scale(1.05); }
  100% { opacity: 1; transform: scale(1); }
}
</style>
