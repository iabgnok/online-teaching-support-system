<template>
  <div class="message-list" ref="messageContainer" @scroll="handleScroll">
    <div v-if="loading" class="loading">
      <i class="el-icon-loading"></i> 加载更多消息...
    </div>
    
    <div class="messages">
      <template v-for="(message, index) in messages" :key="message.id">
        <!-- 时间分隔线 -->
        <div v-if="shouldShowDateDividerLocal(message, index)" class="date-divider">
          <span>{{ formatDateDivider(message.created_at) }}</span>
        </div>
        
        <!-- 消息项 -->
        <div 
          :class="['message-item', message.sender_id == currentUserId ? 'sent' : 'received']"
          :data-message-id="message.id"
          @contextmenu.prevent="showContextMenu($event, message)"
        >
          <div v-if="message.sender_id != currentUserId" class="avatar">
            {{ message.sender_name?.substring(0, 1) }}
          </div>
          
          <div class="message-content">
            <div v-if="message.sender_id != currentUserId" class="sender-name">
              {{ message.sender_name }}
            </div>
            
            <!-- 回复的消息引用 -->
            <div v-if="message.reply_to" class="reply-reference" @click="scrollToMessage(message.reply_to.id)">
              <div class="reply-line"></div>
              <div class="reply-content">
                <div class="reply-sender">{{ message.reply_to.sender_name }}</div>
                <div class="reply-text">{{ message.reply_to.content }}</div>
              </div>
            </div>
            
            <div class="message-bubble" :title="formatFullTime(message.created_at)">
              <div v-if="message.message_type === 'text'" class="text-message">
                {{ message.content }}
              </div>
              <div v-else-if="message.message_type === 'image'" class="image-message">
                <img :src="message.media_url" @click="previewImage(message.media_url)" />
              </div>
              <div v-else-if="message.message_type === 'file'" class="file-message">
                <i class="el-icon-document"></i>
                <span>{{ message.file_name }}</span>
              </div>
              <div v-else-if="message.message_type === 'live_class_entry'" class="live-class-entry" :class="{ 'class-ended': getClassEntryData(message).status === 'ended' }" @click="handleClassEntryClick(message, getClassEntryData(message))">
                <div class="entry-header">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"></polygon>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
                  </svg>
                  <span class="entry-title">{{ getClassEntryData(message).title }}</span>
                  <span v-if="getClassEntryData(message).status === 'ended'" class="status-badge ended">已结束</span>
                  <span v-else-if="getClassEntryData(message).status === 'active'" class="status-badge active">进行中</span>
                </div>
                <div v-if="getClassEntryData(message).description" class="entry-description">
                  {{ getClassEntryData(message).description }}
                </div>
                <div class="entry-footer">
                  <span class="entry-duration">预计 {{ getClassEntryData(message).duration }} 分钟</span>
                  <span v-if="getClassEntryData(message).status !== 'ended'" class="entry-hint">点击卡片进入课堂</span>
                  <span v-else class="entry-hint-ended">课堂已结束</span>
                </div>
              </div>
              <div v-else-if="message.message_type === 'system'" class="system-message">
                {{ message.content }}
              </div>
              
              <div class="message-meta">
                <span class="time">{{ formatTime(message.created_at) }}</span>
                <span v-if="message.is_edited" class="edited">已编辑</span>
                <span v-if="message.sender_id == currentUserId" class="status">
                  <i v-if="message.pending" class="el-icon-loading"></i>
                  <i v-else-if="message.failed" class="el-icon-warning" style="color: #f56c6c"></i>
                  <i v-else-if="(message.read_count && message.read_count > 0) || (message.read_by && message.read_by.length > 0)" class="el-icon-check read" style="color: #409eff" :title="`${message.read_count} 人已读`"></i>
                  <i v-else class="el-icon-check"></i>
                </span>
              </div>
            </div>
            
            <!-- 表情回复显示 -->
            <div v-if="message.reactions && message.reactions.length > 0" class="message-reactions-display">
              <button
                v-for="(reactionItem, idx) in message.reactions"
                :key="idx"
                class="reaction-bubble"
                :class="{ 'my-reaction': reactionItem.i_reacted }"
                @click="toggleReaction(message, reactionItem.reaction)"
                :title="getReactionTooltip(reactionItem)"
              >
                <span class="reaction-emoji">{{ reactionItem.reaction }}</span>
                <span class="reaction-count">{{ reactionItem.count }}</span>
              </button>
            </div>
            
            <!-- ===== Telegram 式频道评论入口 ===== -->
            <div 
              v-if="isChannelMessage(message)" 
              class="comment-bar"
              @click="openComments(message)"
            >
              <svg class="comment-icon" viewBox="0 0 24 24" width="16" height="16">
                <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3 .97 4.29L2 22l5.71-.97C9 21.64 10.46 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.38 0-2.68-.32-3.85-.89l-.27-.15-2.83.48.48-2.83-.15-.27C4.82 14.68 4.5 13.38 4.5 12 4.5 7.86 7.86 4.5 12 4.5S19.5 7.86 19.5 12 16.14 19.5 12 19.5z"/>
              </svg>
              <span v-if="message.comment_count > 0" class="comment-count">
                {{ message.comment_count }} 条评论
              </span>
              <span v-else class="comment-hint">发表评论...</span>
            </div>
          </div>
          
          <div v-if="message.sender_id == currentUserId" class="avatar">
            {{ currentUserName?.substring(0, 1) }}
          </div>
        </div>
      </template>
    </div>
    
    <!-- 正在输入指示器 -->
    <div v-if="typingUsers.length > 0" class="typing-indicator">
      <div class="typing-avatar"></div>
      <div class="typing-bubble">
        <div class="typing-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
      <span class="typing-text">{{ typingUsers[0] }} 正在输入...</span>
    </div>
    
    <!-- 右键菜单 - Telegram风格完全分离布局 -->
    <!-- 使用 Teleport 将菜单挂载到 body，彻底解决遮挡问题 -->
    <teleport to="body">
      <transition name="telegram-fade">
        <div v-if="contextMenu.visible" 
          class="context-menu-container" 
          :class="{ 'is-reverse': contextMenu.reverseLayout }"
          :style="{ 
            top: contextMenu.y + 'px', 
            left: contextMenu.x + 'px'
          }"
          @click.stop
        >
          <!-- 表情栏：独立的圆角背景 -->
          <div class="tg-reaction-bar">
            <span 
              v-for="emoji in quickReactions" 
              :key="emoji" 
              class="tg-emoji-item"
              @click="addReaction(contextMenu.message, emoji)"
            >
              {{ emoji }}
            </span>
            <button 
              class="tg-expand-btn" 
              :class="{ 'is-active': showMoreMenu }"
              @click.stop="showMoreReactions"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="m6 9 6 6 6-6"/>
              </svg>
            </button>

            <!-- 更多表情面板 - 从快捷栏内部展开覆盖 -->
            <transition name="tg-pop-in">
              <div v-if="showMoreMenu" class="tg-full-emoji-panel">
                <div class="emoji-grid">
                  <span 
                    v-for="emoji in allReactions" 
                    :key="emoji" 
                    class="tg-emoji-item-large"
                    @click="addReaction(contextMenu.message, emoji)"
                    :title="emoji"
                  >
                    {{ emoji }}
                  </span>
                </div>
              </div>
            </transition>
          </div>

          <!-- 功能菜单：当表情面板打开时隐藏 -->
          <div v-if="!showMoreMenu" class="tg-menu-list">
            <div class="tg-menu-item" @click="replyMessage(contextMenu.message)">
              <i class="el-icon-chat-line-round"></i>
              <span>回复</span>
            </div>
            <div class="tg-menu-item" @click="copyMessage(contextMenu.message)">
              <i class="el-icon-document-copy"></i>
              <span>复制文本</span>
            </div>
            <div v-if="['teacher', 'admin'].includes(userRole)" 
              class="tg-menu-item" @click="pinMessage(contextMenu.message)">
              <i class="el-icon-top"></i>
              <span>置顶消息</span>
            </div>
            <div v-if="contextMenu.message?.sender_id == currentUserId" 
              class="tg-menu-item" @click="editMessage(contextMenu.message)">
              <i class="el-icon-edit"></i>
              <span>编辑</span>
            </div>
            <div v-if="contextMenu.message?.sender_id == currentUserId" 
              class="tg-menu-item tg-danger" @click="deleteMessage(contextMenu.message)">
              <i class="el-icon-delete"></i>
              <span>删除消息</span>
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'
import { 
  formatTime, 
  formatFullTime, 
  formatDateDivider,
  shouldShowDateDivider
} from '@/utils/timeUtils'

const router = useRouter()

const props = defineProps({
  conversationId: {
    type: Number,
    default: null
  },
  messages: {
    type: Array,
    default: () => []
  },
  conversationSubtype: {
    type: String,
    default: null
  },
  role: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['load-more', 'reply', 'edit', 'delete', 'pin', 'reaction-changed', 'open-comments', 'scroll-button-change', 'unread-count-change'])

const messageContainer = ref(null)
const loading = ref(false)
const lastMsgRef = ref(null)
const currentUserId = localStorage.getItem('user_id')
const userRole = localStorage.getItem('user_role')
const currentUserName = localStorage.getItem('user_name') || localStorage.getItem('real_name') || localStorage.getItem('username')
const showScrollButton = ref(false)
watch(showScrollButton, (val) => emit('scroll-button-change', val))
const unreadCount = ref(0)
watch(unreadCount, (val) => emit('unread-count-change', val))
const typingUsers = ref([])
// 快捷表情栏（显示6个常用表情）
const quickReactions = ref(['👍', '❤️', '😂', '😮', '😢', '🙏'])

// 新增：动态计算输入框高度


// 所有支持的表情（包括更多选项）- 扩展到24个
const allReactions = ref([
  '👍', '❤️', '😂', '😮', '😢', '🙏',
  '🔥', '👏', '🎉', '💯', '🤔', '😊',
  '😍', '🥰', '😭', '😡', '🤩', '😎',
  '🙌', '✨', '💪', '🎊', '👌', '❤️‍🔥'
])

// 更多表情菜单的显示状态
const showMoreMenu = ref(false)
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  message: null,
  reverseLayout: false // 标记是否需要表情在下，菜单在上
})

// 格式化未读消息数：超过999显示999+
const formattedUnreadCount = computed(() => {
  return unreadCount.value > 999 ? '999+' : unreadCount.value
})

let isNearBottom = true

// 防抖函数（优化滚动性能）
const throttle = (fn, delay) => {
  let timer = null
  return function(...args) {
    if (timer) return
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

const handleScroll = () => {
  if (!messageContainer.value) return
  
  const el = messageContainer.value
  const { scrollTop, scrollHeight, clientHeight } = el
  
  // 只在用户主动滚动到顶部时加载更多（scrollTop非常接近0）
  // 避免在初始加载或消息动态增加时频繁触发
  if (scrollTop === 0 && scrollHeight > clientHeight && !loading.value) {
    loading.value = true
    emit('load-more')
    setTimeout(() => loading.value = false, 1000)
  }
  
  // 精确检测：判断最后一条消息是否被完全遮挡
  if (lastMsgRef.value) {
    const lastMsg = lastMsgRef.value
    // 最后一条消息的底部位置（相对于容器顶部）
    const lastMsgBottom = lastMsg.offsetTop + lastMsg.offsetHeight
    // 容器当前可视区域的底部位置
    const viewPortBottom = scrollTop + clientHeight
    
    /**
     * 核心判定逻辑：
     * 如果最后一条消息的底部 > 视口底部 + 预留量（5px）
     * 说明最后一条消息至少有一部分在视口外（被遮挡）
     */
    const hasHiddenMessage = lastMsgBottom > (viewPortBottom + 5)
    
    // 距离底部很近（50px内）认为在底部
    isNearBottom = lastMsgBottom - viewPortBottom < 50
    
    // 显示按钮：有消息被遮挡时才显示
    showScrollButton.value = hasHiddenMessage
  } else {
    // 降级方案：没有最后一条消息引用时使用原有逻辑
    const scrollBottom = scrollHeight - scrollTop - clientHeight
    isNearBottom = scrollBottom < 50
    showScrollButton.value = scrollBottom > 150
  }
  
  // 如果在底部，清空未读数
  if (isNearBottom) {
    unreadCount.value = 0
  }
}

// 创建防抖版本的滚动处理函数
const throttledScroll = throttle(handleScroll, 100)

const shouldShowDateDividerLocal = (message, index) => {
  if (index === 0) return true
  
  const prevMessage = props.messages[index - 1]
  return shouldShowDateDivider(message, prevMessage)
}

// formatTime, formatFullTime, formatDateDivider 函数从 timeUtils 导入，不再在此定义

const getClassEntryData = (message) => {
  try {
    return JSON.parse(message.content)
  } catch {
    return {
      lesson_id: '',
      title: '在线授课',
      description: '',
      duration: 45,
      status: 'active'
    }
  }
}

const joinClass = async (lessonId, status) => {
  // 如果状态已标记为结束，阻止进入
  if (status === 'ended') {
    ElMessage.warning('课堂已结束，无法进入')
    return
  }
  
  // 再次验证课堂状态
  try {
    const response = await api.get(`/live-class/${lessonId}/check`)
    if (response.data.status === 'ended') {
      ElMessage.warning('课堂已结束，无法进入')
      return
    }
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error(error.response.data.error || '课堂已结束')
      return
    }
    console.error('检查课堂状态失败:', error)
  }
  
  const userRole = localStorage.getItem('user_role')
  if (userRole === 'teacher') {
    router.push(`/teacher/live-class/${lessonId}`)
  } else {
    router.push(`/live-class/${lessonId}`)
  }
}

// 处理课堂卡片点击进入
const handleClassEntryClick = (message, classEntryData) => {
  if (classEntryData.status === 'ended') {
    // 课堂已结束，不允许点击进入
    return
  }
  // 触发进入课堂逻辑
  joinClass(classEntryData.lesson_id, classEntryData.status)
}

const previewImage = (url) => {
  window.open(url, '_blank')
}

const scrollToBottom = (smooth = true) => {
  nextTick(() => {
    if (messageContainer.value) {
      const el = messageContainer.value
      el.scrollTo({
        top: el.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
      // 立即清空未读数
      unreadCount.value = 0
      // 更新底部状态
      isNearBottom = true
      showScrollButton.value = false
    }
  })
}

const scrollToMessage = (messageId) => {
  const messageElement = document.querySelector(`[data-message-id="${messageId}"]`)
  if (messageElement) {
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    messageElement.classList.add('highlight')
    setTimeout(() => messageElement.classList.remove('highlight'), 2000)
  }
}

// 右键菜单 - 智能定位与自动翻转
const showContextMenu = (e, message) => {
  e.preventDefault()
  e.stopPropagation()
  
  // 先关闭之前的菜单
  if (contextMenu.value.visible) {
    hideContextMenu()
    // 等待关闭动画完成再打开新的
    setTimeout(() => {
      showContextMenu(e, message)
    }, 200)
    return
  }
  
  const menuWidth = 180;
  const menuHeight = 240;
  const { clientX: x, clientY: y } = e;
  const { innerWidth: windowWidth, innerHeight: windowHeight } = window;

  // 防遮挡计算逻辑
  let finalX = x;
  let finalY = y;
  let reverseLayout = false;

  // 如果右侧空间不足，向左弹出
  if (x + menuWidth > windowWidth) {
    finalX = x - menuWidth;
  }
  
  // 如果下方空间不足，向上弹出
  if (y + menuHeight > windowHeight) {
    finalY = y - menuHeight;
    reverseLayout = true; // 标记需要反向布局（例如表情在下，菜单在上）
  }

  contextMenu.value = {
    visible: true,
    x: finalX,
    y: finalY,
    message,
    reverseLayout
  };
  
  // 延迟绑定关闭事件
  nextTick(() => {
    const closeHandler = (e) => {
      // 如果点击的是菜单内部，不关闭
      if (e.target.closest('.context-menu-container')) {
        return
      }
      hideContextMenu()
      document.removeEventListener('click', closeHandler, true)
    }
    // 使用捕获阶段监听
    document.addEventListener('click', closeHandler, true)
  })
}

const hideContextMenu = () => {
  contextMenu.value.visible = false
  showMoreMenu.value = false
}

const showMoreReactions = () => {
  // 切换更多表情菜单的显示状态
  showMoreMenu.value = !showMoreMenu.value
}

const addReaction = async (message, emoji) => {
  try {
    // 确保emoji是字符串格式而不是Unicode转义
    const emojiString = String(emoji)
    
    // 检测是否为问号
    if (emojiString === '??' || emojiString.includes('?')) {
      console.error('检测到损坏的表情数据:', emojiString)
      ElMessage.error('表情数据异常，请刷新页面后重试')
      return
    }
    
    const response = await api.post(`/chat/messages/${message.id}/reactions`, {
      reaction: emojiString
    })
    
    // 立即更新本地消息的表情数据
    if (response.data.reactions) {
      message.reactions = response.data.reactions
    }
    
    ElMessage.success('已添加表情回复')
    emit('reaction-changed')
  } catch (error) {
    console.error('添加表情失败:', error)
    ElMessage.error(error.response?.data?.error || '添加表情回复失败')
  }
  
  // 关闭更多表情菜单和右键菜单
  showMoreMenu.value = false
  hideContextMenu()
}

const toggleReaction = async (message, emoji) => {
  try {
    const emojiString = String(emoji)
    const response = await api.post(`/chat/messages/${message.id}/reactions`, {
      reaction: emojiString
    })
    
    // 立即更新本地消息的表情数据
    if (response.data.reactions) {
      message.reactions = response.data.reactions
    }
    
    emit('reaction-changed')
  } catch (error) {
    console.error('表情操作失败:', error)
    ElMessage.error('操作失败')
  }
}

const getReactionTooltip = (reaction) => {
  if (!reaction) return ''
  
  // 处理用户列表显示
  if (reaction.users && Array.isArray(reaction.users) && reaction.users.length > 0) {
    return reaction.users.join(', ')
  }
  
  // 显示数量
  const count = reaction.count || 0
  return `${count} 人回复`
}

const replyMessage = (message) => {
  emit('reply', message)
  hideContextMenu()
}

const copyMessage = (message) => {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(message.content)
    ElMessage.success('已复制到剪贴板')
  }
  hideContextMenu()
}

const pinMessage = (message) => {
  emit('pin', message)
  hideContextMenu()
}

const editMessage = (message) => {
  emit('edit', message)
  hideContextMenu()
}

const deleteMessage = async (message) => {
  hideContextMenu()
  try {
    await ElMessageBox.confirm('确定要删除这条消息吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    emit('delete', message)
  } catch {
    // 用户取消
  }
}

const handleReactionChanged = (data) => {
  // 通知父组件更新消息的reactions
  emit('reaction-changed', data)
}

// 生命周期钩子
// 监听消息变化，更新lastMsgRef
watch(() => props.messages, () => {
  nextTick(() => {
    if (messageContainer.value) {
      const messageItems = messageContainer.value.querySelectorAll('.message-item')
      if (messageItems.length > 0) {
        lastMsgRef.value = messageItems[messageItems.length - 1]
      } else {
        lastMsgRef.value = null
      }
    }
  })
}, { immediate: true })

onMounted(() => {
  // 监听滚动事件（使用防抖版本）
  const messageList = messageContainer.value
  if (messageList) {
    messageList.addEventListener('scroll', throttledScroll)
    // 滚动时隐藏右键菜单
    messageList.addEventListener('scroll', hideContextMenu)
  }
  // 初始化执行一次，检查初始状态
  handleScroll()
})

onUnmounted(() => {
  const messageList = messageContainer.value
  if (messageList) {
    messageList.removeEventListener('scroll', throttledScroll)
    messageList.removeEventListener('scroll', hideContextMenu)
    // 清理 ResizeObserver
    if (messageList.__resizeObserverCleanup) {
      messageList.__resizeObserverCleanup()
    }
  }
})

// 监听消息变化
watch(() => props.messages.length, (newLen, oldLen) => {
  if (newLen > oldLen) {
    // 有新消息进来
    const newMessage = props.messages[props.messages.length - 1]
    
    if (isNearBottom) {
      // 用户在底部：自动滚动到底部，不增加未读数
      nextTick(() => {
        scrollToBottom(false) // 使用非平滑滚动，更快响应
      })
    } else {
      // 用户不在底部：增加未读数（排除自己发送的消息）
      if (newMessage && newMessage.sender_id != currentUserId) {
        unreadCount.value++
      }
    }
  }
  
  // 消息数量变化后，延迟检测按钮状态（避免频繁触发）
  nextTick(() => {
    // 仅检测滚动按钮状态，不触发加载逻辑
    if (lastMsgRef.value) {
      const lastMsg = lastMsgRef.value
      const el = messageContainer.value
      if (!el) return
      const { scrollTop, scrollHeight, clientHeight } = el
      const lastMsgBottom = lastMsg.offsetTop + lastMsg.offsetHeight
      const viewPortBottom = scrollTop + clientHeight
      const hasHiddenMessage = lastMsgBottom > (viewPortBottom + 5)
      showScrollButton.value = hasHiddenMessage
      isNearBottom = lastMsgBottom - viewPortBottom < 50
    }
  })
})

// ===== Telegram 式频道评论功能 =====
const isChannelMessage = (message) => {
  // 判断是否为频道消息（没有 root_message_id 且对话是频道类型）
  return props.conversationSubtype === 'channel' &&
         !message.root_message_id
}

const openComments = (message) => {
  // 触发事件，由父组件处理（切换到讨论模式）
  // 确保传递正确的消息对象和标记
  const eventData = {
    ...message,
    isFromDiscussionMode: false // 标记来自非讨论模式
  }
  emit('open-comments', eventData)
}

// 暴露方法和状态给父组件
defineExpose({
  scrollToBottom,
  scrollToMessage,
  setTypingUsers: (users) => { typingUsers.value = users },
  showScrollButton,
  unreadCount,
  formattedUnreadCount
})
</script>

<style scoped>
.message-list {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 120px; /* 固定距离，避免被输入框覆盖 */
  background: linear-gradient(to bottom, #f0f2f5 0%, #e8eaed 100%);
  position: relative;
}

.loading {
  text-align: center;
  padding: 10px;
  color: #409eff;
  font-size: 14px;
}

.messages {
  padding-bottom: 100px; /* 减少底部padding，允许输入框更靠近最后一条消息 */
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 100%;
}

/* 日期分隔线 */
.date-divider {
  text-align: center;
  margin: 20px 0;
}

.date-divider span {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  font-size: 12px;
  color: #666;
}

/* 消息项 */
.message-item {
  display: flex;
  gap: 8px;
  max-width: 65%;
  align-items: flex-end;
  animation: messageSlideIn 0.2s ease-out;
  margin-bottom: 16px; /* 增加消息间距 */
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.sent {
  align-self: flex-end;
  flex-direction: row;
}

.message-item.received {
  align-self: flex-start;
}

.message-item:hover .message-bubble {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-item.highlight .message-bubble {
  animation: highlight 1s ease;
}

@keyframes highlight {
  0%, 100% { background-color: inherit; }
  50% { background-color: #fff3cd; }
}

/* 头像 */
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 消息内容 */
.message-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-width: 100%;
  position: relative; /* 为表情回复提供定位基准 */
}

.sender-name {
  font-size: 12px; /* 保持 */
  color: #409eff;
  font-weight: 600;
  padding-left: 12px;
  margin-bottom: 2px;
}

/* 回复引用 */
.reply-reference {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px 8px 0 0;
  margin-bottom: -2px;
  cursor: pointer;
  transition: background 0.2s;
}

.reply-reference:hover {
  background: rgba(0, 0, 0, 0.08);
}

.reply-line {
  width: 3px;
  background: #409eff;
  border-radius: 2px;
}

.reply-content {
  flex: 1;
  overflow: hidden;
}

.reply-sender {
  font-size: 12px;
  color: #409eff;
  font-weight: 600;
  margin-bottom: 2px;
}

.reply-text {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 消息气泡 */
.message-bubble {
  padding: 10px 14px;
  border-radius: 18px;
  word-wrap: break-word;
  transition: all 0.2s;
  position: relative;
}

.message-item.received .message-bubble {
  background: #fff;
  color: #333;
  border-radius: 18px 18px 18px 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-item.sent .message-bubble {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.3);
}

.text-message {
  line-height: 1.5;
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 13px; /* 从默认大小调整为13px */
}

.image-message img {
  max-width: 100%;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.2s;
}

.image-message img:hover {
  transform: scale(1.02);
}

.file-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.system-message {
  font-size: 13px;
  font-style: italic;
  color: #888;
}

/* 课堂入口消息 */
.live-class-entry {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
  padding: 14px;
  border-radius: 12px;
  width: 100%;
  max-width: 320px;
  box-sizing: border-box;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  cursor: pointer; /* 添加点击光标 */
  transition: all 0.2s ease; /* 添加平滑过渡 */
}

.live-class-entry:hover {
  transform: translateY(-2px); /* 悬停时上移 */
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

/* 已结束的课堂样式 */
.live-class-entry.class-ended {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  opacity: 0.8;
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
  cursor: not-allowed; /* 已结束时禁止点击光标 */
  pointer-events: none; /* 禁止点击事件 */
}

.live-class-entry.class-ended:hover {
  transform: none; /* 已结束时不产生悬停效果 */
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
}

.entry-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.entry-header svg {
  flex-shrink: 0;
}

.entry-title {
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

/* 状态标签 */
.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.status-badge.ended {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
}

.entry-description {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 12px;
  line-height: 1.5;
}

.entry-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.entry-duration {
  font-size: 13px;
  opacity: 0.8;
}

.entry-hint {
  font-size: 12px;
  opacity: 0.9;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.entry-hint-ended {
  font-size: 12px;
  opacity: 0.8;
  color: rgba(255, 255, 255, 0.8);
}

/* 消息元信息 */
.message-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px; /* 略微减小 */
  margin-top: 2px;
}

.message-item.received .message-meta {
  color: rgba(0, 0, 0, 0.4);
}

.message-item.sent .message-meta {
  color: rgba(255, 255, 255, 0.8);
  justify-content: flex-end;
}

.edited {
  font-style: italic;
}

.status {
  display: flex;
  align-items: center;
}

.status .read {
  font-weight: bold;
}

/* 表情回复显示 */
.message-reactions-display {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.reaction-bubble {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  outline: none; /* 移除焦点轮廓 */
  user-select: none; /* 防止选中 */
}

.reaction-bubble:hover {
  background: rgba(0, 0, 0, 0.1);
  transform: scale(1.05);
}

.reaction-bubble.my-reaction {
  background: rgba(64, 158, 255, 0.15);
  border-color: rgba(64, 158, 255, 0.3);
}

.reaction-emoji {
  font-size: 16px;
  line-height: 1;
  /* 优先使用各平台原生的表情字体 */
  font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", 
               "Segoe UI Symbol", "Android Emoji", "EmojiSymbols", sans-serif !important;
  display: inline-block;
  vertical-align: middle;
  /* 确保字符不被压缩 */
  font-variant-numeric: tabular-nums;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.reaction-count {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  min-width: 12px;
  text-align: center;
}

.my-reaction .reaction-count {
  color: #409eff;
}

/* 正在输入指示器 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  animation: fadeIn 0.3s;
}

.typing-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #ddd;
}

.typing-bubble {
  padding: 10px 14px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #999;
  animation: typingDot 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingDot {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-8px);
  }
}

.typing-text {
  font-size: 13px;
  color: #666;
}

/* 右键菜单 - 外层容器 */
.context-menu-container {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: fit-content;
  pointer-events: none;
  /* 移除动画，减少闪烁 */
  filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.25)) drop-shadow(0 2px 4px rgba(0, 0, 0, 0.12));
}

/* 反向布局：当上方空间不足时，表情在下 */
.context-menu-container.is-reverse {
  flex-direction: column-reverse;
}

/* 表情栏：独立的背景和圆角 */
.tg-reaction-bar {
  position: relative; /* 为内部面板提供定位基准 */
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(15px) saturate(180%); /* Telegram 的毛玻璃感 */
  -webkit-backdrop-filter: blur(15px) saturate(180%);
  border-radius: 14px;
  padding: 6px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  min-width: 200px;
  pointer-events: auto; /* 子块响应点击 */
  border: 1px solid rgba(64, 158, 255, 0.2);
  z-index: 10; /* 确保在功能菜单上方 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  /* box-shadow 移到父容器的 drop-shadow */
}

/* 表情项 */
.tg-emoji-item {
  font-size: 20px; /* 缩小表情尺寸 */
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  user-select: none;
  /* 优先使用各平台原生的表情字体 */
  font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", 
               "Segoe UI Symbol", "Android Emoji", "EmojiSymbols", sans-serif !important;
  padding: 3px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  min-height: 28px;
  position: relative;
  /* 确保字符不被压缩 */
  font-variant-numeric: tabular-nums;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.tg-emoji-item:hover {
  transform: scale(1.35) translateY(-2px);
  background: rgba(64, 158, 255, 0.15);
}

.tg-emoji-item:active {
  transform: scale(1.2) translateY(-1px);
  background: rgba(64, 158, 255, 0.25);
}

/* 下拉按钮 - Telegram 风格圆形按钮 */
.tg-expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 50%; /* 正圆形 */
  border: none;
  background: transparent;
  color: rgba(96, 98, 102, 0.6);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: 2px;
  outline: none;
  padding: 0;
}

/* 鼠标悬停时的浅蓝色圆形背景 */
.tg-expand-btn:hover {
  background-color: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

/* 当菜单打开时，按钮保持高亮并旋转箭头 */
.tg-expand-btn.is-active {
  background-color: rgba(64, 158, 255, 0.15);
  color: #409eff;
  transform: rotate(180deg); /* 箭头反转 */
}

.tg-expand-btn svg {
  display: block;
}

/* 完整表情面板 - 从快捷栏内部展开覆盖 */
.tg-full-emoji-panel {
  position: absolute;
  top: 0;   /* 从快捷栏顶部开始覆盖 */
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.98); /* 稍微不透明一点，覆盖效果更好 */
  backdrop-filter: blur(15px) saturate(180%);
  -webkit-backdrop-filter: blur(15px) saturate(180%);
  border-radius: 14px;
  z-index: 100; /* 足够高，遮盖下方的功能菜单 */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(64, 158, 255, 0.2);
  pointer-events: auto;
  overflow: hidden;
  box-sizing: border-box;
}

/* 隐藏滚动条但保留功能 */
.tg-full-emoji-panel::-webkit-scrollbar {
  width: 4px;
}

.tg-full-emoji-panel::-webkit-scrollbar-track {
  background: transparent;
}

.tg-full-emoji-panel::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

/* 表情网格布局 */
.emoji-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
  padding: 8px;
  width: 100%;
  box-sizing: border-box;
  grid-auto-rows: minmax(auto, max-content);
}

.tg-emoji-item-large {
  font-size: 20px;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.15s cubic-bezier(0.2, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  aspect-ratio: 1;
  box-sizing: border-box;
  font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", 
               "Segoe UI Symbol", "Android Emoji", "EmojiSymbols", sans-serif !important;
  user-select: none;
  flex-shrink: 0;
}

.tg-emoji-item-large:hover {
  background: rgba(64, 158, 255, 0.15);
  transform: scale(1.2);
}

/* Telegram 风格的轻盈弹出动画 */
.tg-pop-in-enter-active {
  transition: all 0.2s cubic-bezier(0.2, 0, 0.2, 1);
}

.tg-pop-in-leave-active {
  transition: all 0.15s cubic-bezier(0.4, 0, 1, 1);
}

.tg-pop-in-enter-from {
  opacity: 0;
  transform: scale(0.95) translateY(8px);
}

.tg-pop-in-leave-to {
  opacity: 0;
  transform: scale(0.98) translateY(-4px);
}

/* 功能菜单列表：独立的背景和圆角 */
.tg-menu-list {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(15px) saturate(180%); /* Telegram 的毛玻璃感 */
  -webkit-backdrop-filter: blur(15px) saturate(180%);
  border-radius: 10px;
  padding: 3px 0;
  min-width: 140px;
  max-width: 160px;
  pointer-events: auto; /* 子块响应点击 */
  border: 1px solid rgba(64, 158, 255, 0.2);
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  /* box-shadow 移到父容器的 drop-shadow */
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
  min-height: 36px; /* 确保与动态计算的高度一致 */
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

/* 简化的过渡动画 */
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

/* 原有动画保留 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

/* 评论栏样式 */
.comment-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  color: #409eff;
  user-select: none;
}

.comment-bar:hover {
  background: rgba(64, 158, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.2);
  transform: scale(1.02);
}

.comment-icon {
  fill: #409eff;
  flex-shrink: 0;
  opacity: 0.8;
}

/* 滚动条样式 */
.message-list::-webkit-scrollbar {
  width: 8px;
}

.message-list::-webkit-scrollbar-track {
  background: transparent;
}

.message-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}
</style>
