// 简单的事件总线，用于组件间通信
import { ref } from 'vue'

// 创建事件处理器映射
const events = new Map()

export const eventBus = {
  // 触发事件
  emit(event, data) {
    const handlers = events.get(event)
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  },
  
  // 监听事件
  on(event, handler) {
    if (!events.has(event)) {
      events.set(event, new Set())
    }
    events.get(event).add(handler)
  },
  
  // 移除监听
  off(event, handler) {
    const handlers = events.get(event)
    if (handlers) {
      handlers.delete(handler)
    }
  }
}
