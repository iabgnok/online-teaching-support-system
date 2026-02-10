<template>
  <div class="live-class-container">
    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <div class="class-info">
        <h2>{{ classInfo.title }}</h2>
        <span class="lesson-id">课堂ID: {{ lessonId }}</span>
        <span class="participants">参与者: {{ participantsCount }}</span>
      </div>
      <div class="toolbar-actions">
        <button @click="showParticipants = !showParticipants" class="btn-secondary">
          {{ showParticipants ? '隐藏参与者' : '显示参与者' }}
        </button>
        <button @click="exitClass" class="btn-danger">退出课堂</button>
      </div>
    </div>

    <!-- 主要内容区域：画板和讨论区的父容器 -->
    <div class="main-content">
      <!-- 画板区域 -->
      <div class="canvas-section">
        <div class="canvas-container">
          <img v-if="backgroundImage" :src="backgroundImage" class="canvas-background">
          <canvas ref="canvas" readonly></canvas>
        </div>
      </div>

      <!-- 可折叠讨论区组件 -->
      <CollapsibleDiscussionPanel
        v-if="discussionConversationId"
        ref="discussionPanel"
        :discussion-conversation-id="discussionConversationId"
        :class-group-conversation-id="classGroupConversationId"
        :role="'student'"
        :current-user-id="currentUserId"
        :class-group-name="classGroupName"
        :total-participants="participantsCount"
        @send-message="handleSendMessage"
        @load-more="handleLoadMore"
        @do-attendance="doAttendance"
        @submit-task="submitTask"
        @raise-hand="handleRaiseHand"
      />
    </div>

    <!-- 参与者列表 -->
    <div class="participants-panel" v-if="showParticipants">
      <h3>在线参与者</h3>
      <ul>
        <li v-for="participant in participants" :key="participant.user_id">
          {{ participant.user_name }} ({{ participant.role }})
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import io from 'socket.io-client'
import api from '../../api'
import CollapsibleDiscussionPanel from '../../components/forum/CollapsibleDiscussionPanel.vue'

export default {
  name: 'StudentLiveClass',
  components: {
    CollapsibleDiscussionPanel
  },
  props: {
    lessonId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      socket: null,
      classInfo: {},
      participantsCount: 0,
      participants: [],
      showParticipants: false,
      currentUserId: null,
      currentUserName: '',
      backgroundImage: null,
      
      // 新增：讨论区相关
      discussionConversationId: null,
      classGroupConversationId: null,
      classGroupName: ''
    }
  },
  
  mounted() {
    this.currentUserId = parseInt(localStorage.getItem('user_id') || '0')
    this.currentUserName = localStorage.getItem('username') || '学生'
    this.initSocket()
    this.loadClassInfo()
    this.initCanvas()
  },
  
  beforeUnmount() {
    if (this.socket) {
      this.socket.disconnect()
    }
  },
  
  methods: {
    initSocket() {
      const socketUrl = import.meta.env.DEV 
        ? 'http://localhost:5000'
        : window.location.origin
        
      this.socket = io(socketUrl, {
        transports: ['websocket', 'polling']
      })
      
      this.socket.on('connect', () => {
        console.log('Socket connected')
        this.socket.emit('join_class', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          user_name: this.currentUserName,
          role: 'student'
        })
      })
      
      this.socket.on('participant_update', (data) => {
        this.participantsCount = data.participant_count
        if (data.participants) {
          this.participants = data.participants
        }
      })
      
      this.socket.on('board_update', (data) => {
        if (data.type === 'draw') {
          this.drawFromRemote(data)
        } else if (data.type === 'clear') {
          this.clearCanvas()
        } else if (data.type === 'image') {
          this.backgroundImage = data.image
        }
      })
      
      this.socket.on('chat:new_message', (data) => {
        console.log('Student received chat:new_message:', data)
        // 将消息传递给CollapsibleDiscussionPanel组件
        if (this.$refs.discussionPanel && data.conversation_id) {
          this.$refs.discussionPanel.receiveMessage(data)
        }
      })

      // 当服务器删除了与课堂相关的对话时，通知全局聊天界面刷新
      this.socket.on('chat:conversation_deleted', (data) => {
        console.log('Received conversation deleted:', data)
        try {
          const eventBus = require('../../utils/eventBus').eventBus
          eventBus.emit('conversation_deleted', data)
        } catch (e) {
          console.warn('eventBus unavailable', e)
        }
      })
      
      this.socket.on('disconnect', () => {
        console.log('Socket disconnected')
      })
    },
    
    async loadClassInfo() {
      try {
        const response = await api.get(`/live-class/${this.lessonId}/join`)
        this.classInfo = response.data
        this.discussionConversationId = response.data.conversation_id
        
        if (response.data.class_id) {
          this.loadClassGroupInfo(response.data.class_id)
        }
      } catch (error) {
        console.error('加载课堂信息失败:', error)
        this.$message.error(error.response?.data?.error || '加载课堂信息失败')
        // 如果加载失败，返回上一页
        this.$router.go(-1)
      }
    },
    
    async loadClassGroupInfo(classId) {
      try {
        const response = await api.get(`/chat/class/${classId}/group`)
        this.classGroupConversationId = response.data.conversation_id
        this.classGroupName = response.data.name
      } catch (error) {
        console.error('加载班级群组信息失败:', error)
      }
    },
    
    initCanvas() {
      this.$nextTick(() => {
        const canvas = this.$refs.canvas
        if (canvas) {
          const container = canvas.parentElement
          canvas.width = container.clientWidth
          canvas.height = container.clientHeight
        }
      })
    },
    
    drawFromRemote(data) {
      const canvas = this.$refs.canvas
      if (!canvas) return
      
      const ctx = canvas.getContext('2d')
      ctx.strokeStyle = data.color || '#000000'
      ctx.lineWidth = data.width || 2
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      
      if (data.tool === 'eraser') {
        ctx.globalCompositeOperation = 'destination-out'
        ctx.lineWidth = data.width * 2
      } else {
        ctx.globalCompositeOperation = 'source-over'
      }
      
      const points = data.points
      if (points && points.length > 0) {
        ctx.beginPath()
        ctx.moveTo(points[0].x * canvas.width, points[0].y * canvas.height)
        for (let i = 1; i < points.length; i++) {
          ctx.lineTo(points[i].x * canvas.width, points[i].y * canvas.height)
        }
        ctx.stroke()
      }
    },
    
    clearCanvas() {
      const canvas = this.$refs.canvas
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    },
    
    handleSendMessage(messageData) {
      // 参考Chat.vue的实现，使用chat:send_message事件
      this.socket.emit('chat:send_message', {
        conversation_id: messageData.conversationId,
        user_id: this.currentUserId,
        content: messageData.message,
        message_type: messageData.messageType || 'text',
        lesson_id: this.lessonId
      })
    },
    
    handleLoadMore(conversationId) {
      // 加载更多消息的逻辑
      console.log('Load more messages for conversation:', conversationId)
    },
    
    doAttendance(attendanceId) {
      this.socket.emit('do_attendance', {
        attendance_id: attendanceId,
        lesson_id: this.lessonId,
        user_id: this.currentUserId
      })
    },
    
    submitTask(taskData) {
      this.socket.emit('submit_task', {
        task_id: taskData.taskId,
        lesson_id: this.lessonId,
        user_id: this.currentUserId,
        content: taskData.content
      })
    },
    
    handleRaiseHand(isRaised) {
      const message = isRaised ? '🙋 我有问题要问' : '🙋 问题已解决'
      this.socket.emit('chat_message', {
        lesson_id: this.lessonId,
        user_id: this.currentUserId,
        user_name: this.currentUserName,
        message: message,
        message_type: 'system'
      })
    },
    
    exitClass() {
      if (confirm('确定要退出课堂吗？')) {
        if (this.socket) {
          this.socket.emit('leave_class', {
            lesson_id: this.lessonId,
            user_id: this.currentUserId
          })
          this.socket.disconnect()
        }
        this.$router.push('/live-class/active')
      }
    }
  }
}
</script>

<style scoped>
.live-class-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 顶部工具栏 */
.top-toolbar {
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  color: white;
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.class-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.class-info h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.class-info span {
  font-size: 14px;
  opacity: 0.9;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
}

.btn-secondary, .btn-danger {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-danger {
  background: #ff4757;
  color: white;
}

.btn-danger:hover {
  background: #ee2f3c;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: row;
  gap: 0;
  min-height: 0;
  overflow: hidden;
}

/* 画板区域 */
.canvas-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  margin: 16px 0 16px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 0;
  overflow: hidden;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.canvas-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  pointer-events: none;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
  cursor: default;
}

/* 参与者面板 */
.participants-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 250px;
  background: white;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  z-index: 100;
}

.participants-panel h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
}

.participants-panel ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.participants-panel li {
  padding: 8px;
  border-bottom: 1px solid #eee;
}
</style>
