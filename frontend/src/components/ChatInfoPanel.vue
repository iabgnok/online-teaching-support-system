<template>
  <div class="chat-info-panel">
    <div class="panel-header">
      <h3>对话信息</h3>
      <button class="btn-close" @click="$emit('close')" title="关闭">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    
    <div class="panel-content">
      <!-- 头像和标题 -->
      <div class="section profile-section">
        <div class="avatar-large">
          {{ conversation.title?.substring(0, 2) || '?' }}
        </div>
        <h2>{{ conversation.title || '未命名对话' }}</h2>
        <p v-if="conversation.type === 'private' && conversation.other_user" class="user-status">
          <span v-if="conversation.other_user.is_online" class="online-badge">在线</span>
          <span v-else class="offline-text">{{ formatLastSeen(conversation.other_user.last_seen) }}</span>
        </p>
        <p v-else-if="conversation.member_count" class="member-count">
          {{ conversation.member_count }} 名成员
        </p>
      </div>
      
      <!-- 操作按钮 -->
      <div class="section actions-section">
        <div class="action-item" @click="togglePin">
          <i :class="conversation.is_pinned ? 'el-icon-pushpin' : 'el-icon-pushpin'" 
            :style="{ color: conversation.is_pinned ? '#ff9800' : '#666' }"></i>
          <span>{{ conversation.is_pinned ? '取消置顶' : '置顶对话' }}</span>
        </div>
        
        <div class="action-item" @click="toggleMute">
          <i :class="conversation.is_muted ? 'el-icon-bell' : 'el-icon-bell-slash'" 
            :style="{ color: conversation.is_muted ? '#409eff' : '#666' }"></i>
          <span>{{ conversation.is_muted ? '开启通知' : '静音通知' }}</span>
        </div>
        
        <div class="action-item" @click="$emit('search')">
          <i class="el-icon-search"></i>
          <span>搜索消息</span>
        </div>
        
        <div class="action-item danger" @click="leaveConversation">
          <i class="el-icon-delete"></i>
          <span>删除对话</span>
        </div>
      </div>
      
      <!-- Shared Content -->
      <div class="section media-section">
        <h4>查找聊天记录</h4>
        <div class="media-actions">
           <div class="media-btn" @click="$emit('filter', 'image')">
             <i class="el-icon-picture-outline"></i>
             <span>图片</span>
           </div>
           <div class="media-btn" @click="$emit('filter', 'file')">
             <i class="el-icon-document"></i>
             <span>文件</span>
           </div>
           <div class="media-btn" @click="$emit('filter', 'link')">
             <i class="el-icon-link"></i>
             <span>链接</span>
           </div>
        </div>
      </div>

      <!-- 成员列表（群聊） -->
      <div v-if="conversation.type !== 'private' && conversation.members" class="section members-section">
        <h4>成员 ({{ conversation.members.length }})</h4>
        <div class="member-list">
          <div v-for="member in conversation.members" :key="member.user_id" class="member-item">
            <div class="member-avatar">
              {{ member.real_name?.substring(0, 1) }}
              <span v-if="member.is_online" class="online-dot"></span>
            </div>
            <div class="member-info">
              <div class="member-name">{{ member.real_name }}</div>
              <div class="member-status">{{ member.role === 'owner' ? '群主' : '成员' }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const props = defineProps({
  conversation: Object
})

const emit = defineEmits(['close', 'search', 'updated'])

const formatLastSeen = (lastSeen) => {
  if (!lastSeen) return '离线'
  
  const date = new Date(lastSeen)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 5) return '刚刚在线'
  if (diffMins < 60) return `${diffMins}分钟前在线`
  
  const diffHours = Math.floor(diffMs / 3600000)
  if (diffHours < 24) return `${diffHours}小时前在线`
  
  return '离线'
}

const togglePin = async () => {
  try {
    const action = props.conversation.is_pinned ? 'unpin' : 'pin'
    await api.post(`/chat/conversations/${props.conversation.id}/${action}`)
    ElMessage.success(props.conversation.is_pinned ? '已取消置顶' : '已置顶')
    emit('updated')
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

const toggleMute = async () => {
  try {
    const action = props.conversation.is_muted ? 'unmute' : 'mute'
    await api.post(`/chat/conversations/${props.conversation.id}/${action}`)
    ElMessage.success(props.conversation.is_muted ? '已开启通知' : '已静音')
    emit('updated')
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

const leaveConversation = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post(`/chat/conversations/${props.conversation.id}/leave`)
    ElMessage.success('已删除对话')
    emit('close')
    emit('updated')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.chat-info-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
  background: #fff;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.btn-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #f5f7fa;
  color: #909399;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f56c6c;
  color: white;
  transform: rotate(90deg);
}

.btn-close svg {
  display: block;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

.section {
  background: #fff;
  margin-bottom: 10px;
  padding: 20px;
}

/* 个人资料区域 */
.profile-section {
  text-align: center;
  padding: 30px 20px;
}

.avatar-large {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 600;
  margin: 0 auto 16px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.profile-section h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.user-status {
  margin: 0;
  font-size: 14px;
}

.online-badge {
  color: #4caf50;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.online-badge::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #4caf50;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.offline-text {
  color: #95a5a6;
}

.member-count {
  margin: 0;
  font-size: 14px;
  color: #7f8c8d;
}

/* 操作区域 */
.actions-section {
  padding: 10px 0;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.action-item:hover {
  background: #f5f7fa;
}

.action-item:last-child {
  border-bottom: none;
}

.action-item i {
  font-size: 18px;
  color: #666;
}

.action-item span {
  font-size: 14px;
  color: #2c3e50;
}

.action-item.danger {
  color: #f56c6c;
}

.action-item.danger i,
.action-item.danger span {
  color: #f56c6c;
}

/* 成员列表 */
.members-section h4 {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: #666;
  font-weight: 600;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.member-item:hover {
  background: #f5f7fa;
}

.member-avatar {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.online-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 12px;
  height: 12px;
  background: #4caf50;
  border: 2px solid #fff;
  border-radius: 50%;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-status {
  font-size: 12px;
  color: #95a5a6;
  margin-top: 2px;
}

/* 滚动条 */
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>

<style scoped>
.media-actions {
  display: flex;
  justify-content: space-around;
  margin-top: 10px;
}
.media-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.2s;
}
.media-btn:hover {
  background-color: #f5f7fa;
}
.media-btn i {
  font-size: 20px;
  margin-bottom: 4px;
  color: #606266;
}
.media-btn span {
    font-size: 12px;
    color: #606266;
}
</style>
