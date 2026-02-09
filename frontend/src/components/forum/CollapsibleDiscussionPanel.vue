<template>
  <div class="collapsible-discussion-panel" :class="{ 'collapsed': isCollapsed }">
    <!-- 收起按钮：始终可见，固定在右边缘 -->
    <div class="collapse-toggle-wrapper">
      <button 
        class="collapse-toggle-btn" 
        @click="toggleCollapse" 
        :title="isCollapsed ? '展开讨论区' : '收起讨论区'"
      >
        <svg v-if="isCollapsed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      </button>
    </div>

    <!-- 主内容区域 -->
    <div class="panel-main-content">
      <!-- 聊天区域 - 完全参考Chat.vue设计 -->
      <div class="chat-section">
        <div class="chat-header">
          <div class="header-left">
            <h3 v-if="activeChat === 'discussion'">💬 课堂交流</h3>
            <h3 v-else>👥 {{ classGroupName }}</h3>
            <span class="online-count">{{ onlineCount }} 人在线</span>
          </div>
          <div class="header-actions">
            <button class="icon-btn switch-btn" @click="switchChat" :title="activeChat === 'discussion' ? '切换到班级群聊' : '切换到课堂讨论'">
              <svg v-if="activeChat === 'discussion'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </button>
            <button class="icon-btn" @click="scrollToBottom" title="滚动到底部">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 消息和输入区域统一容器 - 参考Chat.vue的chat-container -->
        <div class="chat-container">
          <div class="chat-messages" ref="messagesContainer" @scroll="handleScroll">
            <!-- 加载更多提示 -->
            <div v-if="hasMoreMessages" class="load-more-hint">
              <span @click="loadMoreMessages">加载更早的消息...</span>
            </div>
          
          <template v-for="(msg, index) in currentMessages" :key="msg.id">
            <!-- 时间分隔线 -->
            <div v-if="shouldShowTimeDivider(msg, index)" class="time-divider">
              <span>{{ formatDateDivider(msg.created_at) }}</span>
            </div>
            
            <!-- 系统消息 -->
            <div v-if="msg.message_type === 'system'" class="system-message">
              <span class="system-icon">ℹ️</span>
              {{ msg.content }}
            </div>

            <!-- 考勤卡片 - 仅在课堂讨论区显示，角色适配 -->
            <div v-else-if="msg.message_type === 'attendance' && activeChat === 'discussion'" class="special-card-wrapper">
              <div class="attendance-card">
                <div class="card-header">
                  <span class="card-icon">📅</span>
                  <span class="card-title">{{ getJsonContent(msg.content).title || '课堂考勤' }}</span>
                  <span class="status-badge active">进行中</span>
                </div>
                <div class="card-body">
                  <div class="progress-section">
                    <div class="progress-bar">
                      <div class="progress-fill" :style="{ width: getAttendanceProgress(msg) + '%' }"></div>
                    </div>
                    <div class="progress-text">
                      <span class="count-text">
                        <strong>{{ getJsonContent(msg.content).count || 0 }}</strong> / {{ totalParticipants }} 人已签到
                      </span>
                      <span class="percentage">{{ getAttendanceProgress(msg) }}%</span>
                    </div>
                  </div>
                </div>
                <div class="card-footer">
                  <!-- 教师端：查看详情 -->
                  <button v-if="role === 'teacher'" class="card-btn" @click="viewAttendanceDetail(msg)">
                    <i class="el-icon-view"></i> 查看详情
                  </button>
                  <!-- 学生端：签到按钮 -->
                  <button v-else class="card-btn primary" @click="doAttendance(msg)">
                    <i class="el-icon-check"></i> 立即签到
                  </button>
                </div>
              </div>
            </div>

            <!-- 任务卡片 - 仅在课堂讨论区显示，角色适配 -->
            <div v-else-if="msg.message_type === 'task' && activeChat === 'discussion'" class="special-card-wrapper">
              <div class="task-card">
                <div class="card-header">
                  <span class="card-icon">
                    {{ getTaskTypeIcon(getJsonContent(msg.content).type) }}
                  </span>
                  <span class="card-title">
                    {{ getJsonContent(msg.content).title || '课堂任务' }}
                  </span>
                  <span v-if="role === 'teacher'" class="author-badge">我发布</span>
                  <span class="type-badge" :class="getTaskTypeClass(getJsonContent(msg.content).type)">
                    {{ getTaskTypeLabel(getJsonContent(msg.content).type) }}
                  </span>
                </div>
                <div class="card-body">
                  <!-- 任务描述 -->
                  <div class="task-content">{{ getJsonContent(msg.content).content || getJsonContent(msg.content).desc }}</div>
                  
                  <!-- 任务详情 -->
                  <div class="task-meta">
                    <div class="meta-item">
                      <i class="el-icon-time"></i>
                      <span>截止: {{ formatDeadline(getJsonContent(msg.content).deadline) }}</span>
                    </div>
                    <div class="meta-item" v-if="getJsonContent(msg.content).estimated_time">
                      <i class="el-icon-clock"></i>
                      <span>预计 {{ getJsonContent(msg.content).estimated_time }} 分钟</span>
                    </div>
                    <div class="meta-item" v-if="getJsonContent(msg.content).total_score">
                      <i class="el-icon-medal"></i>
                      <span>{{ getJsonContent(msg.content).total_score }} 分</span>
                    </div>
                  </div>

                  <!-- 进度条 -->
                  <div class="progress-section">
                    <div class="progress-bar">
                      <div class="progress-fill success" :style="{ width: getTaskProgress(msg) + '%' }"></div>
                    </div>
                    <div class="progress-text">
                      <span class="count-text">
                        <i class="el-icon-check"></i> 
                        <strong>{{ (getJsonContent(msg.content).completed_ids || []).length }}</strong> 人已完成
                      </span>
                      <span class="percentage">{{ getTaskProgress(msg) }}%</span>
                    </div>
                  </div>
                </div>
                <div class="card-footer">
                  <!-- 教师端 -->
                  <template v-if="role === 'teacher'">
                    <button class="card-btn secondary" @click="viewTaskDetail(msg)">
                      <i class="el-icon-tickets"></i> 完成列表
                    </button>
                    <button class="card-btn primary" @click="remindStudents(msg)">
                      <i class="el-icon-bell"></i> 提醒未完成
                    </button>
                  </template>
                  <!-- 学生端 -->
                  <template v-else>
                    <button class="card-btn primary" @click="submitTask(msg)">
                      <i class="el-icon-upload2"></i> 提交任务
                    </button>
                  </template>
                </div>
              </div>
            </div>
            
            <!-- 用户消息 - Telegram风格 -->
            <div
              v-else
              class="message-wrapper"
              :class="{ 'own-message': String(msg.sender_id) === String(currentUserId) }"
              @contextmenu.prevent="showContextMenu($event, msg)"
            >
              <!-- 对方消息：左侧显示头像和名字 -->
              <template v-if="String(msg.sender_id) !== String(currentUserId)">
                <div class="message-avatar">
                  <div class="avatar-circle">{{ (msg.sender_name || 'U').charAt(0).toUpperCase() }}</div>
                </div>
                <div class="message-content">
                  <div class="message-author">{{ msg.sender_name || '未知用户' }}</div>
                  <div class="message-bubble received">
                    <div class="bubble-text">{{ msg.content }}</div>
                    <div class="bubble-meta">
                      <span class="bubble-time">{{ formatTime(msg.created_at) }}</span>
                    </div>
                  </div>
                </div>
              </template>
              
              <!-- 自己的消息：右侧，蓝色气泡 -->
              <template v-else>
                <div class="message-content">
                  <div class="message-bubble sent">
                    <div class="bubble-text">{{ msg.content }}</div>
                    <div class="bubble-meta">
                      <span class="bubble-time">{{ formatTime(msg.created_at) }}</span>
                      <span class="bubble-status">
                        <i class="el-icon-check"></i>
                        <i class="el-icon-check"></i>
                      </span>
                    </div>
                  </div>
                </div>
                <div class="message-avatar own">
                  <div class="avatar-circle">{{ role === 'teacher' ? '教' : '学' }}</div>
                </div>
              </template>
            </div>
          </template>
          
          <!-- 正在输入提示 -->
          <div v-if="someoneTyping" class="typing-indicator">
            <div class="typing-avatar">
              <div class="avatar-circle small">{{ someoneTyping.charAt(0) }}</div>
            </div>
            <div class="typing-bubble">
              <div class="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 滚动到底部按钮 -->
        <transition name="fade-scale">
          <div v-if="showScrollButton" class="scroll-to-bottom" @click="scrollToBottom">
            <div v-if="unreadCount > 0" class="unread-bubble">{{ unreadCount }}</div>
            <div class="down-button">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
          </div>
        </transition>
        
        <!-- 输入区域 -->
        <div class="input-container-wrapper">
          <!-- 使用MessageInput组件 -->
          <MessageInput 
            v-if="currentConversationId"
            ref="messageInputRef"
            :conversation-id="currentConversationId"
            :conversation-subtype="activeChat === 'discussion' ? 'live_class_discussion' : 'normal'"
            :reply-to="replyToMessage"
            :editing-message="editingMessage"
            :show-classroom-features="true"
            @send="handleSendMessageFromInput"
            @cancel-reply="replyToMessage = null"
            @cancel-edit="editingMessage = null"
            @typing="handleTyping"
            @start-attendance="startAttendance"
            @publish-task="publishTask"
            @share-board="shareBoard"
            @raise-hand="raiseHand"
          />
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue';
import MessageInput from '../chat/MessageInput.vue';
import { formatTime, formatDateDivider, shouldShowDateDivider } from '@/utils/timeUtils';
import MessageList from '../chat/MessageList.vue';
import api from '../../api';

export default {
  name: 'CollapsibleDiscussionPanel',
  components: {
    MessageInput,
    MessageList
  },
  props: {
    // 课堂讨论区对话ID
    discussionConversationId: {
      type: [Number, String],
      required: true
    },
    // 班级群聊对话ID
    classGroupConversationId: {
      type: [Number, String],
      required: false
    },
    // 角色：teacher 或 student
    role: {
      type: String,
      required: true,
      validator: (value) => ['teacher', 'student'].includes(value)
    },
    // 当前用户ID
    currentUserId: {
      type: [Number, String],
      required: true
    },
    // 班级群聊名称
    classGroupName: {
      type: String,
      default: '班级群聊'
    },
    // 总参与者数量
    totalParticipants: {
      type: Number,
      default: 0
    }
  },
  emits: [
    'send-message',
    'load-more',
    'view-attendance',
    'view-task',
    'remind-students',
    'start-attendance',
    'publish-task',
    'share-board',
    'do-attendance',
    'submit-task',
    'collapse-changed',
    'raise-hand',
    'typing'
  ],
  setup(props, { emit }) {
    // ========== 状态管理 ==========
    const isCollapsed = ref(false);
    const activeChat = ref('discussion'); // 'discussion' 或 'classGroup'
    const showScrollButton = ref(false);
    const unreadCount = ref(0);
    const someoneTyping = ref('');
    const isHandRaised = ref(false);
    const replyToMessage = ref(null);
    const editingMessage = ref(null);

    // 引用
    const messagesContainer = ref(null);
    const messageInputRef = ref(null);

    // 消息数据
    const discussionMessages = ref([]);
    const classGroupMessages = ref([]);
    const hasMoreMessages = ref(false);
    const onlineCount = ref(0);
    const loading = ref(false);

    // Socket连接
    let socket = null;

    // 当前对话ID
    const currentConversationId = computed(() => {
      return activeChat.value === 'discussion' 
        ? props.discussionConversationId 
        : props.classGroupConversationId;
    });

    // 当前显示的消息
    const currentMessages = computed(() => {
      return activeChat.value === 'discussion' 
        ? discussionMessages.value 
        : classGroupMessages.value;
    });

    // ========== 方法 ==========
    
    // 切换折叠状态
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value;
      emit('collapse-changed', isCollapsed.value);
    };

    // 从API加载消息
    const loadMessages = async (conversationId, chatType) => {
      if (loading.value || !conversationId) {
        console.log(`Skipping load messages for ${chatType}: conversationId=${conversationId}`);
        return;
      }
      
      try {
        loading.value = true;
        console.log(`Loading messages for conversation ${conversationId} (${chatType})`);
        const response = await api.get(`/chat/conversations/${conversationId}/messages`);
        const messages = response.data.messages || [];
        
        if (chatType === 'discussion') {
          discussionMessages.value = messages;
        } else {
          classGroupMessages.value = messages;
        }
        
        console.log(`Loaded ${messages.length} messages for ${chatType}`);
        await nextTick();
        // 延迟滚动，确保DOM已完全更新
        setTimeout(() => scrollToBottom(), 100);
      } catch (error) {
        console.error(`Failed to load messages for ${chatType}:`, error);
        // 404错误说明对话不存在，这是正常情况
        if (error.response?.status === 404) {
          console.log(`Conversation ${conversationId} not found, will create when first message is sent`);
        }
      } finally {
        loading.value = false;
      }
    };

    // 切换聊天类型（一个按钮切换）
    const switchChat = async () => {
      const newChatType = activeChat.value === 'discussion' ? 'classGroup' : 'discussion';
      activeChat.value = newChatType;
      
      // 切换后滚动到底部
      await nextTick();
      setTimeout(() => scrollToBottom(), 50);
      
      // 通知父组件加载对应的消息
      if (newChatType === 'classGroup' && classGroupMessages.value.length === 0) {
        loadClassGroupMessages();
      }
    };

    // 从MessageInput组件接收消息
    const handleSendMessageFromInput = (messageData) => {
      const conversationId = currentConversationId.value;
      
      // 乐观更新：立即在本地显示消息
      const tempMessage = {
        id: 'temp_' + Date.now(), // 临时ID
        conversation_id: conversationId,
        sender_id: props.currentUserId,
        sender_name: localStorage.getItem('username') || '我',
        content: messageData.content,
        created_at: new Date().toISOString(),
        message_type: messageData.message_type || 'text'
      };
      
      // 添加到对应的消息数组
      const targetArray = activeChat.value === 'discussion' 
        ? discussionMessages.value 
        : classGroupMessages.value;
      targetArray.push(tempMessage);
      
      console.log('Optimistically added message:', tempMessage);
      
      // 滚动到底部
      nextTick(() => {
        setTimeout(() => scrollToBottom(), 50);
      });
      
      // 发送给服务器
      emit('send-message', {
        conversationId,
        message: messageData.content,
        chatType: activeChat.value,
        replyTo: replyToMessage.value?.id,
        editingId: editingMessage.value?.id
      });
      
      // 清除回复和编辑状态
      replyToMessage.value = null;
      editingMessage.value = null;
    };

    // 取消回复
    const handleCancelReply = () => {
      replyToMessage.value = null;
    };

    // 取消编辑
    const handleCancelEdit = () => {
      editingMessage.value = null;
    };

    // 处理输入（打字中）
    const handleTyping = () => {
      emit('typing');
    };

    // 滚动到底部
    const scrollToBottom = () => {
      if (!messagesContainer.value) {
        console.warn('messagesContainer is not available');
        return;
      }
      try {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
        showScrollButton.value = false;
        unreadCount.value = 0;
      } catch (error) {
        console.error('Error scrolling to bottom:', error);
      }
    };

    // 处理滚动
    const handleScroll = () => {
      if (!messagesContainer.value) return;
      
      const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
      
      // 距离底部超过100px时显示按钮
      showScrollButton.value = distanceFromBottom > 100;
    };

    // 加载更多消息
    const loadMoreMessages = () => {
      const conversationId = activeChat.value === 'discussion' 
        ? props.discussionConversationId 
        : props.classGroupConversationId;
      
      emit('load-more', {
        conversationId,
        chatType: activeChat.value
      });
    };

    // 加载班级群聊消息
    const loadClassGroupMessages = () => {
      if (props.classGroupConversationId) {
        loadMessages(props.classGroupConversationId, 'classGroup');
      }
    };

    // 显示时间分隔线
    const shouldShowTimeDivider = (msg, index) => {
      if (index === 0) return true;
      const messages = currentMessages.value;
      const prevMsg = messages[index - 1];
      return shouldShowDateDivider(msg, prevMsg);
    };

    // formatDateDivider 已从 @/utils/timeUtils 导入

    // formatTime 已从 @/utils/timeUtils 导入

    // 解析JSON内容
    const getJsonContent = (message) => {
      try {
        return typeof message === 'string' ? JSON.parse(message) : message;
      } catch {
        return {};
      }
    };

    // 获取考勤进度
    const getAttendanceProgress = (msg) => {
      const content = getJsonContent(msg.content);
      const count = content.count || 0;
      return props.totalParticipants > 0 
        ? Math.round((count / props.totalParticipants) * 100) 
        : 0;
    };

    // 获取任务进度
    const getTaskProgress = (msg) => {
      const content = getJsonContent(msg.content);
      const completed = (content.completed_ids || []).length;
      return props.totalParticipants > 0 
        ? Math.round((completed / props.totalParticipants) * 100) 
        : 0;
    };

    // 任务类型相关
    const getTaskTypeIcon = (type) => {
      const icons = {
        practice: '✏️',
        homework: '📚',
        discussion: '💭',
        quiz: '📝'
      };
      return icons[type] || '📄';
    };

    const getTaskTypeLabel = (type) => {
      const labels = {
        practice: '课堂练习',
        homework: '课后作业',
        discussion: '讨论任务',
        quiz: '随堂测试'
      };
      return labels[type] || '任务';
    };

    const getTaskTypeClass = (type) => {
      return `type-${type}`;
    };

    // 格式化截止时间
    const formatDeadline = (deadline) => {
      if (!deadline) return '无限期';
      const date = new Date(deadline);
      return date.toLocaleString('zh-CN', { 
        month: 'long', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    };

    // 事件转发
    const viewAttendanceDetail = (msg) => {
      emit('view-attendance', msg);
    };

    const viewTaskDetail = (msg) => {
      emit('view-task', msg);
    };

    const remindStudents = (msg) => {
      emit('remind-students', msg);
    };

    const startAttendance = () => {
      emit('start-attendance');
    };

    const publishTask = () => {
      emit('publish-task');
    };

    const shareBoard = () => {
      emit('share-board');
    };

    const doAttendance = (msg) => {
      emit('do-attendance', msg);
    };

    const submitTask = (msg) => {
      emit('submit-task', msg);
    };

    const raiseHand = () => {
      isHandRaised.value = !isHandRaised.value;
      emit('raise-hand', isHandRaised.value);
    };

    const showContextMenu = (event, msg) => {
      // 实现右键菜单
      console.log('Context menu for message:', msg);
    };

    // 接收新消息
    const receiveMessage = (message) => {
      console.log('receiveMessage called with:', message);
      
      const targetArray = message.conversation_id === props.discussionConversationId 
        ? discussionMessages.value 
        : classGroupMessages.value;
      
      // 检查是否已经存在该消息（避免重复）
      const exists = targetArray.some(msg => msg.id === message.id);
      
      if (!exists) {
        targetArray.push(message);
        console.log('Message added, total messages:', targetArray.length);
        
        // 如果是当前显示的聊天，滚动到底部
        if (message.conversation_id === currentConversationId.value) {
          nextTick(() => {
            setTimeout(() => {
              if (!showScrollButton.value) {
                scrollToBottom();
              } else {
                unreadCount.value++;
              }
            }, 100);
          });
        }
      } else {
        console.log('Message already exists, skipping');
      }
    };

    // ========== 生命周期 ==========
    onMounted(async () => {
      // 加载课堂讨论消息
      await loadMessages(props.discussionConversationId, 'discussion');
      
      // 如果有班级群聊ID，预加载班级群聊消息
      if (props.classGroupConversationId) {
        await loadMessages(props.classGroupConversationId, 'classGroup');
      }
    });

    onBeforeUnmount(() => {
      // 清理socket连接
      if (socket) {
        socket.disconnect();
      }
    });

    // 监听当前消息变化，自动滚动
    watch(currentMessages, () => {
      nextTick(() => {
        if (!showScrollButton.value) {
          scrollToBottom();
        }
      });
    }, { deep: true });

    // 监听conversationId变化，重新加载消息
    watch(() => props.discussionConversationId, (newId) => {
      if (newId && activeChat.value === 'discussion') {
        loadMessages(newId, 'discussion');
      }
    });

    watch(() => props.classGroupConversationId, (newId) => {
      if (newId && activeChat.value === 'classGroup') {
        loadMessages(newId, 'classGroup');
      }
    });

    return {
      // 状态
      isCollapsed,
      activeChat,
      showScrollButton,
      unreadCount,
      someoneTyping,
      isHandRaised,
      hasMoreMessages,
      onlineCount,
      currentMessages,
      currentConversationId,
      replyToMessage,
      editingMessage,
      loading,
      
      // 引用
      messagesContainer,
      messageInputRef,
      
      // 方法
      toggleCollapse,
      switchChat,
      loadMessages,
      loadClassGroupMessages,
      receiveMessage,
      handleSendMessageFromInput,
      handleCancelReply,
      handleCancelEdit,
      handleTyping,
      scrollToBottom,
      handleScroll,
      loadMoreMessages,
      shouldShowTimeDivider,
      formatDateDivider,
      formatTime,
      getJsonContent,
      getAttendanceProgress,
      getTaskProgress,
      getTaskTypeIcon,
      getTaskTypeLabel,
      getTaskTypeClass,
      formatDeadline,
      viewAttendanceDetail,
      viewTaskDetail,
      remindStudents,
      startAttendance,
      publishTask,
      shareBoard,
      doAttendance,
      submitTask,
      raiseHand,
      showContextMenu
    };
  }
};
</script>

<style scoped>
/* 主容器 - 收起时只显示按钮 */
.collapsible-discussion-panel {
  position: relative;
  display: flex;
  flex-direction: row;
  height: calc(100vh - 60px); /* 固定高度：视口高度减去顶部工具栏 */
  max-height: calc(100vh - 60px);
  width: 400px;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.collapsible-discussion-panel.collapsed {
  width: 40px;
}

/* 收起按钮包装器 - 绝对定位在边缘 */
.collapse-toggle-wrapper {
  position: absolute;
  right: -1px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1000;
}

.collapsed .collapse-toggle-wrapper {
  left: -1px;
  right: auto;
}

.collapse-toggle-btn {
  width: 28px;
  height: 56px;
  border: 1px solid #e4e7ed;
  border-right: none;
  background: #fff;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #909399;
  box-shadow: -3px 0 10px rgba(0,0,0,0.08);
}

.collapsed .collapse-toggle-btn {
  border-right: 1px solid #e4e7ed;
  border-left: none;
  border-radius: 0 8px 8px 0;
  box-shadow: 3px 0 10px rgba(0,0,0,0.08);
}

.collapse-toggle-btn:hover {
  background: #ecf5ff;
  color: #409eff;
  box-shadow: -3px 0 15px rgba(64,158,255,0.2);
}

.collapsed .collapse-toggle-btn:hover {
  box-shadow: 3px 0 15px rgba(64,158,255,0.2);
}

/* 主内容区域 */
.panel-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  opacity: 1;
  visibility: visible;
  transition: opacity 0.3s, visibility 0.3s;
  overflow: hidden;
}

.collapsed .panel-main-content {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}

/* 聊天区域 - 完全参照Chat.vue的chat-main结构 */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  background: #fff;
  position: relative;
}

/* 消息和输入区域统一容器 - 完全参照Chat.vue的chat-container */
.chat-container {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

/* 聊天头部 - 参考Chat.vue */
.chat-header {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.header-left h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.online-count {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
  transition: all 0.2s;
  padding: 0;
}

.icon-btn:hover {
  background: #f5f7fa;
  color: #409eff;
}

.icon-btn.switch-btn:hover {
  background: #ecf5ff;
}

/* 消息列表容器 - 参考MessageList.vue */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 100px;
  background: linear-gradient(to bottom, #f0f2f5 0%, #e8eaed 100%);
  position: relative;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.load-more-hint {
  text-align: center;
  padding: 12px;
  color: #409eff;
  cursor: pointer;
  font-size: 13px;
}

.load-more-hint:hover {
  text-decoration: underline;
}

/* 时间分隔线 */
.time-divider {
  text-align: center;
  margin: 20px 0;
}

.time-divider span {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  font-size: 12px;
  color: #666;
}

/* 系统消息 */
.system-message {
  text-align: center;
  padding: 8px 16px;
  margin: 8px 0;
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* 特殊卡片 */
.special-card-wrapper {
  max-width: 90%;
  margin: 12px auto;
}

.attendance-card,
.task-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  padding: 12px 16px;
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  font-size: 20px;
}

.card-title {
  flex: 1;
  font-weight: 600;
  font-size: 15px;
}

.status-badge,
.author-badge,
.type-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.2);
}

.card-body {
  padding: 16px;
}

.task-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.progress-section {
  margin-top: 12px;
}

.progress-bar {
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: #409eff;
  transition: width 0.3s;
}

.progress-fill.success {
  background: #67c23a;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
}

.card-footer {
  padding: 12px 16px;
  background: #f5f7fa;
  display: flex;
  gap: 8px;
}

.card-btn {
  flex: 1;
  padding: 8px 16px;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.2s;
}

.card-btn:hover {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.card-btn.primary {
  background: #409eff;
  border-color: #409eff;
  color: #fff;
}

.card-btn.primary:hover {
  background: #66b1ff;
}

/* 用户消息 */
.message-wrapper {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  align-items: flex-end;
  animation: messageSlideIn 0.3s ease-out;
  max-width: 65%;
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

.message-wrapper.own-message {
  align-self: flex-end;
  flex-direction: row;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.avatar-circle.small {
  width: 24px;
  height: 24px;
  font-size: 12px;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-width: 100%;
}

.message-author {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
  padding-left: 4px;
  font-weight: 500;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 18px;
  word-wrap: break-word;
  transition: all 0.2s;
  position: relative;
}

.message-bubble.received {
  background: #fff;
  color: #333;
  border-radius: 18px 18px 18px 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-bubble.sent {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.3);
}

.bubble-text {
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  margin-top: 2px;
}

.message-bubble.received .bubble-meta {
  color: rgba(0, 0, 0, 0.4);
}

.message-bubble.sent .bubble-meta {
  color: rgba(255, 255, 255, 0.8);
  justify-content: flex-end;
}

/* 正在输入 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  margin-bottom: 12px;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
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

/* 滚动到底部按钮 */
.scroll-to-bottom {
  position: absolute;
  bottom: 80px;
  right: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  z-index: 100;
  pointer-events: auto;
}

.unread-bubble {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 12px;
  margin-bottom: -10px;
  z-index: 2;
  min-width: 20px;
  text-align: center;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.4);
  animation: bounceIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.down-button {
  background: rgba(64, 158, 255, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  z-index: 1;
}

.down-button svg {
  color: white;
  transition: color 0.2s;
}

.scroll-to-bottom:hover .down-button {
  background: rgba(64, 158, 255, 1);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

/* 输入区域 */
.chat-input-container {
  background: #fff;
  border-top: 1px solid #e4e7ed;
  padding: 12px;
}

.input-toolbar {
  margin-bottom: 8px;
  position: relative;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.tool-button {
  width: 32px;
  height: 32px;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
  transition: all 0.2s;
}

.tool-button:hover {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.tool-button.raise-hand {
  width: auto;
  padding: 0 12px;
  gap: 4px;
}

.tool-button.raise-hand.active {
  background: #67c23a;
  border-color: #67c23a;
  color: #fff;
}

/* 输入容器包装器 */
.input-container-wrapper {
  background: #fff;
  border-top: 1px solid #e4e7ed;
  padding: 8px 12px 12px;
  flex-shrink: 0;
}

/* 输入区操作菜单（上下文菜单） */
.action-menu {
  position: absolute;
  bottom: 40px;
  left: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 100;
}

.menu-item {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.menu-item:hover {
  background: #f5f7fa;
}

.input-area {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  min-height: 36px;
  max-height: 120px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
  transition: border-color 0.2s;
}

.message-input:focus {
  outline: none;
  border-color: #409eff;
}

.send-button {
  width: 36px;
  height: 36px;
  border: none;
  background: #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  transition: all 0.2s;
}

.send-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.send-button.active {
  background: #409eff;
}

.send-button.active:hover {
  background: #66b1ff;
  transform: translateY(-1px);
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(10px);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}
</style>
