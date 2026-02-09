<template>
  <div 
    class="conversation-item" 
    :class="{ 'active': active, 'unread': conversation.unread_count > 0, 'pinned': conversation.is_pinned }"
    @click="$emit('click')"
    @contextmenu.prevent="showContextMenu($event)"
  >
    <div class="avatar">
      <img v-if="conversation.avatar" :src="conversation.avatar" :alt="conversation.title" />
      <div v-else class="avatar-placeholder" :class="`type-${conversation.type} subtype-${conversation.group_subtype || 'normal'}`">
        <!-- 频道图标 -->
        <i v-if="conversation.group_subtype === 'channel'" class="el-icon-message-solid channel-icon"></i>
        <!-- 普通群组图标 -->
        <i v-else-if="conversation.type === 'private'" class="el-icon-user"></i>
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
          <!-- 统一的标签样式 -->
          <!-- 频道标识 -->
          <span v-if="conversation.group_subtype === 'channel'" class="type-badge channel">
            <i class="el-icon-message-solid"></i> 频道
          </span>
          <!-- 讨论组标识 -->
          <span v-else-if="conversation.group_subtype === 'discussion'" class="type-badge discussion">
            <i class="el-icon-chat-dot-round"></i> 讨论组
          </span>
          <!-- 其他普通群组类型 -->
          <span v-else-if="conversation.type === 'group'" class="type-badge group">
            <i class="el-icon-s-comment"></i> 群聊
          </span>
          <span v-else-if="conversation.type === 'class_group'" class="type-badge class-group">
            <i class="el-icon-school"></i> 班级群
          </span>
          <span v-else-if="conversation.type === 'course_group'" class="type-badge course-group">
            <i class="el-icon-reading"></i> 课程群
          </span>
          <span v-else-if="conversation.type === 'live_class'" class="type-badge live-class">
            <i class="el-icon-video-camera"></i> 课堂
          </span>
        </div>
        <span class="conv-time">{{ formatTime(conversation.last_message?.created_at || conversation.updated_at) }}</span>
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
    
    <!-- 右键菜单 - Telegram风格 -->
    <teleport to="body">
      <transition name="telegram-fade">
        <div v-if="contextMenuVisible" 
          class="context-menu-container"
          :style="{ 
            top: menuPosition.y + 'px', 
            left: menuPosition.x + 'px'
          }"
          @click.stop
          @mouseenter="handleMenuEnter"
          @mouseleave="handleMenuLeave"
        >
          <!-- 功能菜单列表 -->
          <div class="tg-menu-list">
            <div class="tg-menu-item" @click="openInNewWindow">
              <i class="el-icon-full-screen"></i>
              <span>在新窗口中打开</span>
            </div>
            <div 
              class="tg-menu-item tg-submenu" 
              @mouseenter="handleSubmenuEnter"
              @mouseleave="handleSubmenuLeave"
            >
              <i class="el-icon-folder-add"></i>
              <span>加入文件夹</span>
              <i class="el-icon-arrow-right" style="margin-left: auto; font-size: 12px;"></i>
              
              <!-- 子菜单 -->
              <transition name="submenu-fade">
                <div 
                  v-if="showFolderSubmenu" 
                  class="tg-submenu-panel" 
                  @click.stop
                  @mouseenter="handleSubmenuEnter"
                  @mouseleave="handleSubmenuLeave"
                >
                  <div 
                    v-for="folder in folders" 
                    :key="folder.id"
                    class="tg-menu-item"
                    @click="addToFolderDirect(folder.id)"
                  >
                    <i class="el-icon-folder"></i>
                    <span>{{ folder.name }}</span>
                  </div>
                  <div v-if="folders.length > 0" class="tg-menu-divider"></div>
                  <div class="tg-menu-item" @click="openCreateFolderDialog">
                    <i class="el-icon-folder-add"></i>
                    <span>创建新文件夹</span>
                  </div>
                </div>
              </transition>
            </div>
            <div class="tg-menu-item" @click="togglePin">
              <i class="el-icon-top"></i>
              <span>{{ conversation.is_pinned ? '取消置顶' : '置顶' }}</span>
            </div>
            <div class="tg-menu-item" @click="toggleMute">
              <i :class="conversation.is_muted ? 'el-icon-bell' : 'el-icon-bell-slash'"></i>
              <span>{{ conversation.is_muted ? '取消免打扰' : '免打扰' }}</span>
            </div>
            <div class="tg-menu-item" @click="markAsRead">
              <i class="el-icon-check"></i>
              <span>标记为已读</span>
            </div>
            <div v-if="isInFolder" class="tg-menu-item" @click="removeFromFolder">
              <i class="el-icon-folder-remove"></i>
              <span>从文件夹中移除</span>
            </div>
            <div v-if="conversation.type === 'group' || conversation.type === 'class_group' || conversation.type === 'course_group'" 
              class="tg-menu-item tg-danger" @click="leaveGroup">
              <i class="el-icon-right"></i>
              <span>退出{{ conversation.type === 'class_group' ? '班级群' : conversation.type === 'course_group' ? '课程群' : '群组' }}</span>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatRelativeTime } from '@/utils/timeUtils'

const props = defineProps({
  conversation: {
    type: Object,
    required: true
  },
  active: {
    type: Boolean,
    default: false
  },
  contextMenuVisible: {
    type: Boolean,
    default: false
  },
  folders: {
    type: Array,
    default: () => []
  },
  activeFolderId: {
    type: [String, Number],
    default: 'all'
  }
})

const emit = defineEmits(['click', 'pin', 'mute', 'read', 'add-to-folder', 'leave', 'show-context-menu', 'hide-context-menu', 'open-create-folder', 'remove-from-folder'])

// 本地菜单位置状态
const menuPosition = ref({ x: 0, y: 0 })
const showFolderSubmenu = ref(false)
let submenuCloseTimer = null
let menuCloseTimer = null

// 判断是否在当前文件夹中
const isInFolder = computed(() => {
  if (!props.activeFolderId || props.activeFolderId === 'all' || props.activeFolderId === 'unread') {
    return false
  }
  const folder = props.folders.find(f => f.id === props.activeFolderId)
  return folder && folder.conversations && folder.conversations.includes(props.conversation.id)
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

// formatTime 函数从 timeUtils 导入为 formatRelativeTime
const formatTime = formatRelativeTime

// 右键菜单功能 - 显示群组右键菜单
const showContextMenu = (event) => {
  event.preventDefault()
  event.stopPropagation()
  
  // 计算菜单尺寸
  const menuItemHeight = 36
  const menuPadding = 6
  let menuItemsCount = 6 // 基础菜单项数量
  
  // 如果是群组类型，增加"退出群组"选项
  if (['group', 'class_group', 'course_group'].includes(props.conversation.type)) {
    menuItemsCount++
  }
  
  const menuHeight = (menuItemsCount * menuItemHeight) + menuPadding
  const menuWidth = 180
  const edgeMargin = 20
  
  // 初始坐标
  let x = event.clientX
  let y = event.clientY
  
  // 水平边界检测
  const maxX = window.innerWidth - menuWidth - edgeMargin
  const minX = edgeMargin
  
  if (x > maxX) {
    x = maxX
  }
  if (x < minX) {
    x = minX
  }
  
  // 垂直边界检测
  const maxY = window.innerHeight - menuHeight - edgeMargin
  const minY = edgeMargin
  
  if (y > maxY) {
    y = maxY
  }
  if (y < minY) {
    y = minY
  }
  
  // 保存菜单位置
  menuPosition.value = { x, y }
  
  // 通知父组件显示菜单
  emit('show-context-menu')
}

const hideContextMenu = () => {
  emit('hide-context-menu')
}

const openInNewWindow = () => {
  // 在新窗口中打开对话
  const url = `/chat?conversation=${props.conversation.id}`
  window.open(url, '_blank', 'width=1200,height=800')
  hideContextMenu()
}

const addToFolder = () => {
  emit('add-to-folder', props.conversation.id)
  hideContextMenu()
}

const handleSubmenuEnter = () => {
  if (submenuCloseTimer) {
    clearTimeout(submenuCloseTimer)
    submenuCloseTimer = null
  }
  showFolderSubmenu.value = true
}

const handleSubmenuLeave = () => {
  submenuCloseTimer = setTimeout(() => {
    showFolderSubmenu.value = false
  }, 200) // 200ms延迟，避免鼠标移动时菜单立即消失
}

const handleMenuEnter = () => {
  if (menuCloseTimer) {
    clearTimeout(menuCloseTimer)
    menuCloseTimer = null
  }
}

const handleMenuLeave = () => {
  menuCloseTimer = setTimeout(() => {
    hideContextMenu()
  }, 200) // 200ms延迟，避免鼠标移动时菜单立即消失
}

const addToFolderDirect = (folderId) => {
  // 确保传递conversationId和folderId两个参数
  emit('add-to-folder', { conversationId: props.conversation.id, folderId })
  hideContextMenu()
}

const openCreateFolderDialog = () => {
  emit('open-create-folder', props.conversation.id)
  hideContextMenu()
}

const removeFromFolder = () => {
  emit('remove-from-folder', props.conversation.id)
  hideContextMenu()
}

const togglePin = () => {
  emit('pin', props.conversation.id)
  hideContextMenu()
}

const toggleMute = () => {
  emit('mute', props.conversation.id)
  hideContextMenu()
}

const markAsRead = () => {
  emit('read', props.conversation.id)
  hideContextMenu()
}

const leaveGroup = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要退出${props.conversation.type === 'class_group' ? '班级群' : props.conversation.type === 'course_group' ? '课程群' : '群组'}吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    emit('leave', props.conversation.id)
    hideContextMenu()
  } catch {
    // 用户取消
    hideContextMenu()
  }
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

/* 统一的群组标签样式 */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  white-space: nowrap;
}

.type-badge i {
  font-size: 11px;
}

/* 频道 - 紫色渐变 */
.type-badge.channel {
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 讨论组 - 粉色渐变 */
.type-badge.discussion {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(240, 147, 251, 0.3);
}

/* 群聊 - 绿色 */
.type-badge.group {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
}

/* 班级群 - 橙色 */
.type-badge.class-group {
  background: linear-gradient(135deg, #e6a23c 0%, #f0a020 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(230, 162, 60, 0.3);
}

/* 课程群 - 蓝色 */
.type-badge.course-group {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

/* 课堂 - 红色动画 */
.type-badge.live-class {
  background: linear-gradient(135deg, #f56c6c 0%, #ff5722 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 87, 34, 0.3);
  animation: live-pulse 2s infinite;
}

@keyframes live-pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 2px 8px rgba(255, 87, 34, 0.3);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 3px 12px rgba(255, 87, 34, 0.5);
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

/* 右键菜单样式 - Telegram风格 */
.context-menu-container {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: fit-content;
  pointer-events: none;
  filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.25)) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.12));
}

/* 功能菜单列表 */
.tg-menu-list {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(15px) saturate(180%);
  -webkit-backdrop-filter: blur(15px) saturate(180%);
  border-radius: 10px;
  padding: 3px 0;
  min-width: 180px;
  max-width: 200px;
  pointer-events: auto;
  border: 1px solid rgba(64, 158, 255, 0.2);
  overflow: visible;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
}

/* 子菜单容器 */
.tg-submenu {
  position: relative;
}

/* 子菜单面板 */
.tg-submenu-panel {
  position: absolute;
  left: 100%;
  top: 0;
  margin-left: 4px;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(15px) saturate(180%);
  -webkit-backdrop-filter: blur(15px) saturate(180%);
  border-radius: 8px;
  padding: 4px 0;
  min-width: 180px;
  max-width: 220px;
  border: 1px solid rgba(64, 158, 255, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  max-height: 300px;
  overflow-y: auto;
}

/* 子菜单中的菜单项 */
.tg-submenu-panel .tg-menu-item {
  color: #303133;
  padding: 10px 16px;
}

.tg-submenu-panel .tg-menu-item:hover {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.tg-submenu-panel .tg-menu-item i {
  color: #606266;
  font-size: 16px;
}

.tg-submenu-panel .tg-menu-item:hover i {
  color: #409eff;
}

/* 子菜单空状态 */
.submenu-empty {
  padding: 12px 16px;
  text-align: center;
  color: #909399;
  font-size: 12px;
}

.tg-submenu-panel .submenu-empty {
  color: #909399;
}

/* 菜单分割线 */
.tg-menu-divider {
  height: 1px;
  background: rgba(64, 158, 255, 0.1);
  margin: 3px 0;
}

.tg-submenu-panel .tg-menu-divider {
  background: rgba(64, 158, 255, 0.15);
  margin: 4px 8px;
}

/* 子菜单淡入淡出动画 */
.submenu-fade-enter-active {
  transition: all 0.15s ease;
}

.submenu-fade-leave-active {
  transition: all 0.1s ease;
}

.submenu-fade-enter-from,
.submenu-fade-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}

/* 菜单项 */
.tg-menu-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #303133;
  transition: all 0.18s;
  position: relative;
  user-select: none;
  min-height: 36px;
  box-sizing: border-box;
}

.tg-menu-item:hover {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.tg-menu-item:active {
  background: rgba(64, 158, 255, 0.2);
  transform: scale(0.98);
}

.tg-menu-item i {
  font-size: 14px;
  width: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.85;
}

.tg-menu-item span {
  flex: 1;
}

/* 危险操作 */
.tg-menu-item.tg-danger {
  color: #ff6b6b;
}

.tg-menu-item.tg-danger:hover {
  background: rgba(255, 107, 107, 0.15);
}

.tg-menu-item.tg-danger i {
  color: #ff6b6b;
  opacity: 1;
}

/* Telegram 风格的渐变动画 */
.telegram-fade-enter-active {
  transition: opacity 0.15s ease;
}

.telegram-fade-leave-active {
  transition: opacity 0.1s ease;
}

.telegram-fade-enter-from,
.telegram-fade-leave-to {
  opacity: 0;
}

/* ===== Telegram 式频道样式 ===== */

/* 频道图标 */
.channel-icon {
  color: #409eff;
  font-size: 22px;
}

.subtype-channel {
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
}

.subtype-channel i {
  color: white;
}

/* 频道标识徽章 */
.badge-channel {
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  color: white !important;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.badge-channel i {
  font-size: 12px;
}

/* 讨论组标识徽章 */
.badge-discussion {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white !important;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 8px rgba(240, 147, 251, 0.3);
}

.badge-discussion i {
  font-size: 12px;
}

/* 讨论组样式 */
.subtype-discussion {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.subtype-discussion i {
  color: white;
}
</style>

