<template>
  <div 
    class="conversation-item" 
    :class="{ 'active': active, 'unread': conversation.unread_count > 0, 'pinned': conversation.is_pinned }"
    @click="$emit('click')"
  >
    <div class="avatar">
      <img v-if="conversation.avatar" :src="conversation.avatar" :alt="conversation.title" />
      <div v-else class="avatar-placeholder" :class="`type-${conversation.type}`">
        <i v-if="conversation.type === 'private'" class="el-icon-user"></i>
        <i v-else-if="conversation.type === 'group'" class="el-icon-s-comment"></i>
        <i v-else-if="conversation.type === 'class_group'" class="el-icon-school"></i>
        <i v-else-if="conversation.type === 'course_group'" class="el-icon-reading"></i>
        <i v-else-if="conversation.type === 'live_class'" class="el-icon-video-camera"></i>
        <span v-else>{{ getAvatarText() }}</span>
      </div>
      <span v-if="isOnline" class="online-indicator"></span>
    </div>
    
    <div class="conversation-info">
      <div class="conv-header">
        <div class="title-container">
          <span class="conv-title">{{ conversation.title || '未命名对话' }}</span>
          <span v-if="conversation.type !== 'private'" class="type-badge" :class="`badge-${conversation.type}`">
            <template v-if="conversation.type === 'group'">群聊</template>
            <template v-else-if="conversation.type === 'class_group'">班级群</template>
            <template v-else-if="conversation.type === 'course_group'">课程群</template>
            <template v-else-if="conversation.type === 'live_class'">课堂直播</template>
          </span>
        </div>
        <span class="conv-time">{{ formatTime(conversation.updated_at) }}</span>
      </div>
      
      <div class="conv-footer">
        <span class="last-message">
          <template v-if="conversation.last_message">
            <span v-if="conversation.last_message.sender_name" class="sender">
              {{ conversation.last_message.sender_name }}:
            </span>
            {{ getLastMessagePreview() }}
          </template>
          <span v-else class="no-message">暂无消息</span>
        </span>
        
        <span v-if="conversation.unread_count > 0" class="unread-badge">
          {{ conversation.unread_count > 99 ? '99+' : conversation.unread_count }}
        </span>
        
        <i v-if="conversation.is_muted" class="el-icon-bell-slash mute-icon"></i>
      </div>
    </div>
    
    <i v-if="conversation.is_pinned" class="el-icon-pushpin pin-icon"></i>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  conversation: {
    type: Object,
    required: true
  },
  active: {
    type: Boolean,
    default: false
  }
})

const isOnline = computed(() => {
  return props.conversation.other_user?.is_online || false
})

const getAvatarText = () => {
  const title = props.conversation.title || ''
  return title.substring(0, 2) || '?'
}

const getLastMessagePreview = () => {
  const lastMsg = props.conversation.last_message
  if (!lastMsg) return ''
  
  // 根据消息类型显示不同内容
  switch (lastMsg.message_type) {
    case 'image':
      return '[图片]'
    case 'file':
      return '[文件]'
    case 'voice':
      return '[语音]'
    case 'video':
      return '[视频]'
    case 'system':
      return lastMsg.content
    default:
      // 文本消息，限制长度
      const content = lastMsg.content || ''
      return content.length > 30 ? content.substring(0, 30) + '...' : content
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  // 超过一周显示日期
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  
  if (year === now.getFullYear()) {
    return `${month}/${day}`
  }
  
  return `${year}/${month}/${day}`
}
</script>

<style scoped>
.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.active {
  background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%);
  border-left: 3px solid #409eff;
}

.conversation-item.unread {
  background: #fafafa;
}

.conversation-item.unread .conv-title {
  font-weight: 600;
}

.conversation-item.unread .last-message {
  font-weight: 500;
  color: #333;
}

.conversation-item.pinned {
  background: linear-gradient(90deg, #fff9e6 0%, #fffaf0 100%);
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  margin-right: 12px;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  font-size: 20px;
  font-weight: 600;
}

/* 不同类型的对话颜色 */
.avatar-placeholder.type-private {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.avatar-placeholder.type-group {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.avatar-placeholder.type-class_group {
  background: linear-gradient(135deg, #e6a23c 0%, #f0c78a 100%);
}

.avatar-placeholder.type-course_group {
  background: linear-gradient(135deg, #9c27b0 0%, #ba68c8 100%);
}

.avatar-placeholder.type-live_class {
  background: linear-gradient(135deg, #ff5722 0%, #ff8a65 100%);
}

.avatar-placeholder i {
  font-size: 24px;
}

.online-indicator {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  background: #4caf50;
  border: 3px solid #fff;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(76, 175, 80, 0);
  }
}

.conversation-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.title-container {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 15px;
  font-weight: 500;
  color: #2c3e50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: 0.3px;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.badge-group {
  background: rgba(103, 194, 58, 0.2);
  color: #67c23a;
  border: 1px solid rgba(103, 194, 58, 0.3);
}

.badge-class_group {
  background: rgba(230, 162, 60, 0.2);
  color: #d68910;
  border: 1px solid rgba(230, 162, 60, 0.4);
  font-weight: 700;
}

.badge-course_group {
  background: rgba(156, 39, 176, 0.2);
  color: #7b1fa2;
  border: 1px solid rgba(156, 39, 176, 0.3);
}

.badge-live_class {
  background: rgba(255, 87, 34, 0.15);
  color: #ff5722;
  animation: live-pulse 2s infinite;
}

@keyframes live-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

.conv-time {
  font-size: 12px;
  color: #95a5a6;
  flex-shrink: 0;
  margin-left: 8px;
  font-weight: 400;
}

.conversation-item.unread .conv-time {
  color: #409eff;
  font-weight: 600;
}

.conv-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.last-message {
  font-size: 13px;
  color: #7f8c8d;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  line-height: 1.4;
}

.sender {
  color: #409eff;
  margin-right: 4px;
  font-weight: 500;
}

.no-message {
  color: #bdc3c7;
  font-style: italic;
}

.unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: linear-gradient(135deg, #ff3b30 0%, #ff5e57 100%);
  color: white;
  font-size: 11px;
  font-weight: 700;
  border-radius: 10px;
  text-align: center;
  margin-left: auto;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(255, 59, 48, 0.3);
}

.mute-icon {
  color: #95a5a6;
  font-size: 16px;
  margin-left: 8px;
  flex-shrink: 0;
}

.pin-icon {
  position: absolute;
  top: 10px;
  right: 10px;
  color: #ff9800;
  font-size: 16px;
  transform: rotate(45deg);
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1));
}

/* 动画效果 */
.conversation-item {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
