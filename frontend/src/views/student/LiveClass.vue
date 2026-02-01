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
        <button @click="showParticipants = !showParticipants" class="btn-secondary">{{ showParticipants ? '隐藏参与者' : '显示参与者' }}</button>
        <button @click="exitClass" class="btn-danger">退出课堂</button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 上方：屏幕共享区域 -->
      <div class="screen-share-section" v-if="isSharing">
        <div class="screen-preview">
          <video ref="screenVideo" autoplay muted></video>
        </div>
      </div>

      <!-- 下方：画板和聊天 -->
      <div class="bottom-section">
        <!-- 左侧：画板区域 -->
        <div class="canvas-section">
          <div class="canvas-container">
            <img v-if="backgroundImage" :src="backgroundImage" class="canvas-background">
            <canvas ref="canvas" readonly></canvas>
          </div>
        </div>

        <!-- 右侧：聊天区域 - Telegram风格 -->
        <div class="chat-section telegram-style">
          <!-- 聊天头部 -->
          <div class="chat-header">
            <div class="header-left">
              <h3>在线交流</h3>
              <span class="online-count">{{ participantsCount }} 人在线</span>
            </div>
            <div class="header-actions">
              <button class="icon-btn" @click="toggleMute" title="消息提示">
                <i>{{ isMuted ? '🔕' : '🔔' }}</i>
              </button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div 
            class="chat-messages" 
            ref="messagesContainer"
            @scroll="handleScroll"
          >
            <!-- 加载更多提示 -->
            <div v-if="hasMoreMessages" class="load-more-hint">
              <span @click="loadMoreMessages">📜 加载更早的消息</span>
            </div>

            <template v-for="(msg, index) in messages" :key="msg.id">
              <!-- 时间分隔线 -->
              <div v-if="shouldShowTimeDivider(msg, index)" class="time-divider">
                <span>{{ formatDateDivider(msg.timestamp) }}</span>
              </div>

              <!-- 系统消息 -->
              <div v-if="msg.message_type === 'system'" class="system-message">
                <span class="system-icon">ℹ️</span>
                <span>{{ msg.message }}</span>
              </div>

              <!-- 考勤卡片 -->
              <div v-else-if="msg.message_type === 'attendance'" class="special-card-wrapper">
                <div class="attendance-card">
                  <div class="card-header">
                    <span class="card-icon">📅</span>
                    <span class="card-title">{{ getJsonContent(msg.message).title || '考勤打卡' }}</span>
                    <span v-if="checkAttendanceStatus(msg)" class="status-badge active">已签到</span>
                  </div>
                  <div class="card-body">
                    <div class="progress-section">
                      <div class="progress-bar">
                        <div 
                          class="progress-fill" 
                          :class="{ success: checkAttendanceStatus(msg) }"
                          :style="{ width: getAttendanceProgress(msg) + '%' }"
                        ></div>
                      </div>
                      <div class="progress-text">
                        <span class="count-text">
                          已签到 <strong>{{ getJsonContent(msg.message).count || 0 }}</strong> 人
                        </span>
                        <span class="percentage">{{ getAttendanceProgress(msg) }}%</span>
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <button 
                      v-if="!checkAttendanceStatus(msg)" 
                      class="card-btn" 
                      @click="submitAttendance(msg)"
                    >
                      <i>📍</i> 立即签到
                    </button>
                    <button 
                      v-else 
                      class="card-btn" 
                      disabled
                      style="opacity: 0.6; cursor: not-allowed;"
                    >
                      <i>✅</i> 已完成签到
                    </button>
                  </div>
                </div>
              </div>

              <!-- 任务卡片 -->
              <div v-else-if="msg.message_type === 'task'" class="special-card-wrapper">
                <div class="task-card">
                  <div class="card-header">
                    <span class="card-icon">📝</span>
                    <span class="card-title">课堂任务</span>
                    <span class="author-badge">教师发布</span>
                  </div>
                  <div class="card-body">
                    <div class="task-content">{{ getJsonContent(msg.message).desc }}</div>
                    <div class="progress-section">
                      <div class="progress-bar">
                        <div 
                          class="progress-fill"
                          :class="{ success: checkTaskStatus(msg) }"
                          :style="{ width: getTaskProgress(msg) + '%' }"
                        ></div>
                      </div>
                      <div class="progress-text">
                        <span class="count-text">
                          已完成 <strong>{{ (getJsonContent(msg.message).completed_ids || []).length }}</strong> 人
                        </span>
                        <span class="percentage">{{ getTaskProgress(msg) }}%</span>
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <button 
                      v-if="!checkTaskStatus(msg)" 
                      class="card-btn" 
                      @click="completeTask(msg)"
                    >
                      <i>✅</i> 标记完成
                    </button>
                    <button 
                      v-else 
                      class="card-btn" 
                      disabled
                      style="opacity: 0.6; cursor: not-allowed;"
                    >
                      <i>🎉</i> 已完成
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- 用户消息气泡 -->
              <div
                v-else
                class="message-wrapper"
                :class="{ 'own-message': String(msg.user_id) === String(currentUserId) }"
                @contextmenu.prevent="showContextMenu($event, msg)"
              >
                <!-- 头像 -->
                <div class="message-avatar" :class="{ 'own': String(msg.user_id) === String(currentUserId) }">
                  <div class="avatar-circle small">
                    {{ msg.user_name.charAt(0).toUpperCase() }}
                  </div>
                </div>

                <!-- 消息内容 -->
                <div class="message-content">
                  <!-- 发送者名字（不是自己的消息才显示） -->
                  <div v-if="String(msg.user_id) !== String(currentUserId)" class="message-author">
                    {{ msg.user_name }}
                  </div>

                  <!-- 消息气泡 -->
                  <div class="message-bubble" :class="String(msg.user_id) === String(currentUserId) ? 'sent' : 'received'">
                    <div class="bubble-text">{{ msg.message }}</div>
                    <div class="bubble-meta">
                      <span class="bubble-time">{{ formatTime(msg.timestamp) }}</span>
                      <span v-if="String(msg.user_id) === String(currentUserId)" class="bubble-status">
                        ✓✓
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <!-- 正在输入提示 -->
            <div v-if="someoneTyping" class="typing-indicator">
              <div class="message-avatar">
                <div class="avatar-circle small">T</div>
              </div>
              <div class="typing-bubble">
                <div class="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
            
            <!-- 右键菜单 -->
            <div 
                v-if="contextMenu.visible" 
                class="context-menu telegram" 
                :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
                @click.stop
            >
                <div class="context-menu-item delete" @click="confirmDeleteMessage">
                    <i>🗑️</i> 撤回消息
                </div>
            </div>
          </div>

          <!-- 滚动到底部按钮 -->
          <transition name="fade">
            <div v-if="showScrollButton" class="scroll-to-bottom" @click="scrollToBottom">
              <i>⬇️</i>
              <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }}</span>
            </div>
          </transition>

          <!-- 输入区域 -->
          <div class="chat-input-container">
            <!-- 快捷互动栏 - 学生专属 -->
            <div class="student-toolbar">
              <button 
                class="tool-btn hand-btn" 
                :class="{ active: isRaiseHand }" 
                @click="toggleRaiseHand"
                title="举手"
              >
                <span>{{ isRaiseHand ? '🤚 已举手' : '✋ 举手' }}</span>
              </button>
              <div class="divider"></div>
              <button class="tool-btn emoji-btn" @click="sendQuickMessage('👍')" title="点赞">👍</button>
              <button class="tool-btn emoji-btn" @click="sendQuickMessage('👏')" title="鼓掌">👏</button>
              <button class="tool-btn emoji-btn" @click="sendQuickMessage('❓')" title="疑问">❓</button>
              <button class="tool-btn emoji-btn" @click="sendQuickMessage('🌹')" title="鲜花">🌹</button>
            </div>
            
            <!-- 消息输入区 -->
            <div class="input-area">
              <textarea
                v-model="newMessage"
                class="message-input"
                placeholder="输入消息..."
                @keydown.enter.exact.prevent="sendMessage"
                @input="handleTyping"
                rows="1"
              ></textarea>
              <button 
                class="send-button"
                :class="{ active: newMessage.trim() }"
                @click="sendMessage" 
                :disabled="!newMessage.trim()"
              >
                <i>➤</i>
              </button>
            </div>
          </div>
        </div>
      </div>
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

export default {
  name: 'StudentLiveClass',
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
      messages: [],
      newMessage: '',
      currentUserId: null,
      currentUserName: '',
      
      submittedAttendanceIds: [],

      // 画板相关
      canvas: null,
      ctx: null,

      // 屏幕共享
      isSharing: false,
      peerConnection: null,
      remoteStream: null,
      
      // Context Menu
      contextMenu: { visible: false, x: 0, y: 0, message: null },

      // UI状态
      isRaiseHand: false,
      showParticipants: false,
      backgroundImage: null,

      // Telegram风格UI状态
      showScrollButton: false,
      unreadCount: 0,
      hasMoreMessages: false,
      someoneTyping: false,
      typingTimer: null,
      isUserScrolling: false,
      isMuted: false
    }
  },
  mounted() {
    this.loadUserInfo()
    this.initSocket()
    this.initCanvas()
    this.loadClassInfo()
    document.addEventListener('click', this.closeContextMenu);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeContextMenu);
    if (this.socket) {
      this.socket.disconnect()
    }
    if (this.peerConnection) {
      this.peerConnection.close()
      this.peerConnection = null
    }
  },
  methods: {
    loadUserInfo() {
      // 从localStorage获取用户信息
      this.currentUserId = localStorage.getItem('user_id')
      this.currentUserName = localStorage.getItem('user_name') || localStorage.getItem('real_name') || '学生'
    },
    initSocket() {
      // 在开发环境中直接连接到后端服务器
      const socketUrl = import.meta.env.DEV ? 'http://localhost:5000' : '/'
      
      this.socket = io(socketUrl, {
        transports: ['websocket', 'polling'],
        forceNew: true
      })

      this.socket.on('connect', () => {
        console.log('Connected to server')
        // 加入课堂
        this.socket.emit('join_class', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          user_name: this.currentUserName
        })
      })

      this.socket.on('joined_class', (data) => {
        console.log('Joined class:', data.lesson_id)
        // 获取准确的参与者数量
        this.loadParticipantsCount()
      })

      this.socket.on('user_joined', (data) => {
        this.participantsCount++
        this.addMessage({
          user_name: '系统',
          message: `${data.user_name} 加入了课堂`,
          timestamp: data.timestamp,
          message_type: 'system'
        })
      })

      this.socket.on('user_left', (data) => {
        this.participantsCount--
      })

      this.socket.on('drawing_update', (data) => {
        this.drawFromServer(data)
      })

      this.socket.on('new_message', (data) => {
        console.log('Student received new_message:', data)
        this.addMessage(data)
      })

      this.socket.on('screen_share_started', (data) => {
        this.isSharing = true
      })

      this.socket.on('screen_share_stopped', (data) => {
        this.isSharing = false
        // 清理 WebRTC 连接
        if (this.peerConnection) {
          this.peerConnection.close()
          this.peerConnection = null
        }
        if (this.remoteStream) {
          this.remoteStream = null
        }
      })

      // WebRTC 事件处理
      this.socket.on('webrtc_offer', async (data) => {
        console.log('Student received webrtc_offer:', data)
        if (data.offer) {
          try {
            // 创建 RTCPeerConnection
            this.peerConnection = new RTCPeerConnection({
              iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
              ]
            })

            // 处理远程流
            this.peerConnection.ontrack = (event) => {
              console.log('Student received remote stream')
              this.remoteStream = event.streams[0]
              this.$nextTick(() => {
                if (this.$refs.screenVideo) {
                  this.$refs.screenVideo.srcObject = this.remoteStream
                }
              })
            }

            // 处理 ICE candidates
            this.peerConnection.onicecandidate = (event) => {
              if (event.candidate) {
                this.socket.emit('webrtc_ice_candidate', {
                  lesson_id: this.lessonId,
                  user_id: this.currentUserId,
                  candidate: event.candidate
                })
              }
            }

            // 设置远程描述
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer))

            // 创建 answer
            const answer = await this.peerConnection.createAnswer()
            await this.peerConnection.setLocalDescription(answer)

            // 发送 answer
            console.log('Student sending webrtc_answer')
            this.socket.emit('webrtc_answer', {
              lesson_id: this.lessonId,
              user_id: this.currentUserId,
              answer: answer
            })

            console.log('WebRTC answer sent from student')
          } catch (err) {
            console.error('Error handling WebRTC offer:', err)
          }
        }
      })

      this.socket.on('webrtc_ice_candidate', (data) => {
        if (this.peerConnection && data.candidate) {
          try {
            this.peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate))
          } catch (err) {
            console.error('Error adding ICE candidate:', err)
          }
        }
      })
      this.socket.on('background_image_update', (data) => {
        this.backgroundImage = data.imageUrl
      })

      this.socket.on('attendance_update', (data) => {
          const msg = this.messages.find(m => m.message_type === 'attendance' && this.getJsonContent(m.message).attendance_id === data.attendance_id);
          if (msg) {
              const content = this.getJsonContent(msg.message);
              content.count = data.count;
              msg.message = JSON.stringify(content);
          }
      })

      this.socket.on('task_update', (data) => {
           const target = this.messages.find(m => m.id === data.message_id);
           if (target) {
               const content = this.getJsonContent(target.message);
               content.completed_ids = data.completed_ids;
               target.message = JSON.stringify(content);
           }
      })

      this.socket.on('message_deleted', (data) => {
          this.messages = this.messages.filter(m => m.id !== data.message_id);
      })
      
      this.socket.on('class_ended', (data) => {
        alert(data.message)
        this.$router.push('/live-class/active')
      })

      this.socket.on('error', (error) => {
        console.error('Socket error:', error)
        alert('连接错误: ' + error.message)
      })
    },

    initCanvas() {
      this.canvas = this.$refs.canvas
      this.ctx = this.canvas.getContext('2d')
      this.resizeCanvas()
      window.addEventListener('resize', this.resizeCanvas)
    },

    resizeCanvas() {
      if (this.canvas) {
        const container = this.canvas.parentElement
        this.canvas.width = container.clientWidth
        this.canvas.height = container.clientHeight
      }
    },

    loadClassInfo() {
      // 使用配置好的 api 实例获取课堂信息
      api.get(`/live-class/${this.lessonId}/join`)
      .then(res => {
        this.classInfo = res.data
        // 加载历史消息
        if (res.data.history && Array.isArray(res.data.history)) {
          this.messages = res.data.history.map(m => ({
            ...m,
            id: m.id || Math.random()
          }))
          this.$nextTick(() => {
            this.scrollToBottom()
          })
        }
      })
      .catch(err => {
        console.error('Failed to load class info:', err)
        if (err.response && err.response.data && err.response.data.error) {
          alert(err.response.data.error)
        }
        this.$router.go(-1)
      })
    },

    loadParticipantsCount() {
      api.get(`/live-class/${this.lessonId}/participants`)
      .then(res => {
        // 只显示当前在线的参与者（没有离开时间的）
        this.participants = res.data.filter(p => !p.left_at)
        this.participantsCount = this.participants.length
      })
      .catch(err => {
        console.error('Failed to load participants:', err)
      })
    },

    // 滚动到底部
    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },

    // 画板方法（只接收绘制）
    drawFromServer(data) {
      if (!this.canvas) return
      const x = data.x * this.canvas.width
      const y = data.y * this.canvas.height
      const prevX = data.prevX ? data.prevX * this.canvas.width : x
      const prevY = data.prevY ? data.prevY * this.canvas.height : y

      this.ctx.beginPath()
      this.ctx.moveTo(prevX, prevY)
      this.ctx.lineTo(x, y)
      this.ctx.strokeStyle = data.color
      this.ctx.lineWidth = data.brush_size || 2
      this.ctx.lineCap = 'round'
      this.ctx.lineJoin = 'round'
      this.ctx.stroke()
    },

    // 聊天方法
    sendMessage() {
      if (!this.newMessage.trim()) return
      console.log('Student sending message:', this.newMessage.trim())

      this.socket.emit('chat_message', {
        lesson_id: this.lessonId,
        user_id: this.currentUserId,
        user_name: this.currentUserName,
        message: this.newMessage.trim()
      })

      this.newMessage = ''
    },

    sendQuickMessage(emoji) {
      this.socket.emit('chat_message', {
        lesson_id: this.lessonId,
        user_id: this.currentUserId,
        user_name: this.currentUserName,
        message: emoji,
        message_type: 'emoji'
      })
    },

    addMessage(msg) {
      this.messages.push({
        ...msg,
        id: Date.now() + Math.random()
      })

      this.$nextTick(() => {
        this.scrollToBottom()
      })
    },

    // 举手功能
    toggleRaiseHand() {
      this.isRaiseHand = !this.isRaiseHand
      const message = this.isRaiseHand ? '🙋 我有问题要问' : '🙋 问题已解决'
      this.sendQuickMessage(message)
    },

    // 退出课堂
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
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    },
    
    getJsonContent(str) {
        try { return JSON.parse(str); } catch (e) { return {}; }
    },
    
    checkAttendanceStatus(msg) {
        // Check if locally submitted
        if (this.submittedAttendanceIds.includes(msg.id)) return true;
        // In real app, check if server says "you are present"
        return false; 
    },
    
    checkTaskStatus(msg) {
        const content = this.getJsonContent(msg.message);
        const ids = content.completed_ids || [];
        // Check if user ID is in list (saved as strings)
        return ids.includes(String(this.currentUserId));
    },
    
    submitAttendance(msg) {
        const content = this.getJsonContent(msg.message);
        if (!content.attendance_id) return;
        
        this.socket.emit('submit_attendance', {
            attendance_id: content.attendance_id,
            lesson_id: this.lessonId,
            user_id: this.currentUserId
        });
        
        // Optimistic update
        this.submittedAttendanceIds.push(msg.id);
    },
    
    completeTask(msg) {
         this.socket.emit('complete_task', {
            message_id: msg.id,
            lesson_id: this.lessonId,
            user_id: this.currentUserId
        });
    },
    
    showContextMenu(e, msg) {
        // Students can only delete their own messages
        if (String(msg.user_id) === String(this.currentUserId)) {
            this.contextMenu.message = msg;
            this.contextMenu.x = e.clientX;
            this.contextMenu.y = e.clientY;
            this.contextMenu.visible = true;
        }
    },
    
    closeContextMenu() {
        this.contextMenu.visible = false;
        this.contextMenu.message = null;
    },
    
    confirmDeleteMessage() {
        if (this.contextMenu.message && confirm('确定要撤回这条消息吗？')) {
            this.socket.emit('delete_message', {
                message_id: this.contextMenu.message.id,
                user_id: this.currentUserId,
                lesson_id: this.lessonId
            });
        }
        this.closeContextMenu();
    },

    // ========== Telegram风格辅助方法 ==========
    handleScroll() {
      const container = this.$refs.messagesContainer
      if (!container) return

      const scrollTop = container.scrollTop
      const scrollHeight = container.scrollHeight
      const clientHeight = container.clientHeight

      // 判断是否显示滚动到底部按钮
      this.showScrollButton = scrollHeight - scrollTop - clientHeight > 100
      
      // 如果用户滚动到底部，清除未读计数
      if (scrollHeight - scrollTop - clientHeight < 10) {
        this.unreadCount = 0
        this.isUserScrolling = false
      } else {
        this.isUserScrolling = true
      }
    },

    shouldShowTimeDivider(msg, index) {
      if (index === 0) return true
      const prevMsg = this.messages[index - 1]
      const currentTime = new Date(msg.timestamp)
      const prevTime = new Date(prevMsg.timestamp)
      return (currentTime - prevTime) > 5 * 60 * 1000 // 5分钟
    },

    formatDateDivider(timestamp) {
      const date = new Date(timestamp)
      const now = new Date()
      const today = now.toDateString()
      const msgDate = date.toDateString()
      
      if (msgDate === today) {
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      return date.toLocaleString('zh-CN', { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    },

    getAttendanceProgress(msg) {
      const content = this.getJsonContent(msg.message)
      const count = content.count || 0
      const total = this.participantsCount || 1
      return Math.round((count / total) * 100)
    },

    getTaskProgress(msg) {
      const content = this.getJsonContent(msg.message)
      const completed = (content.completed_ids || []).length
      const total = this.participantsCount || 1
      return Math.round((completed / total) * 100)
    },

    handleTyping() {
      // 发送正在输入事件
      if (!this.typingTimer) {
        this.socket?.emit('typing', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          user_name: this.currentUserName
        })
      }
      
      // 清除之前的定时器
      clearTimeout(this.typingTimer)
      
      // 3秒后停止输入状态
      this.typingTimer = setTimeout(() => {
        this.socket?.emit('stop_typing', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId
        })
        this.typingTimer = null
      }, 3000)
    },

    loadMoreMessages() {
      // 加载更早的消息
      console.log('加载更早的消息...')
      // 这里可以实现分页加载
    },

    toggleMute() {
      this.isMuted = !this.isMuted
      this.$message({
        message: this.isMuted ? '已关闭消息提示' : '已开启消息提示',
        type: 'success'
      })
    }
  }
}
</script>

<style scoped>
.live-class-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.top-toolbar {
  background: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.class-info h2 {
  margin: 0;
  color: #333;
}

.lesson-id, .participants {
  margin-left: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.toolbar-actions {
  display: flex;
  gap: 1rem;
}

.btn-danger {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  background: #dc3545;
  color: white;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  gap: 1rem;
}

.screen-share-section {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  flex-shrink: 0;
}

.screen-preview {
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  max-height: 400px;
}

.screen-preview video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.bottom-section {
  flex: 1;
  display: flex;
  gap: 1rem;
  min-height: 0; /* 允许子元素缩小 */
}

.canvas-section {
  flex: 2;
  background: white;
  border-radius: 8px;
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

.canvas-container {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

canvas {
  width: 100%;
  height: 100%;
  cursor: default;
  position: relative;
  z-index: 10;
}

.canvas-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    pointer-events: none;
    z-index: 0;
}

/* ========== Telegram风格聊天区域样式 - 学生端 ========== */

.chat-section.telegram-style {
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  overflow: hidden;
  position: relative;
  min-height: 0;
}

/* 聊天头部 */
.chat-header {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.online-count {
  font-size: 12px;
  opacity: 0.9;
  padding: 2px 8px;
  background: rgba(255,255,255,0.2);
  border-radius: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.2);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 16px;
}

.icon-btn:hover {
  background: rgba(255,255,255,0.3);
  transform: scale(1.05);
}

/* 消息列表区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: linear-gradient(180deg, #f5f7fa 0%, #ffffff 100%);
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}

/* 加载更多 */
.load-more-hint {
  text-align: center;
  padding: 8px;
}

.load-more-hint span {
  color: #667eea;
  cursor: pointer;
  font-size: 13px;
}

.load-more-hint span:hover {
  text-decoration: underline;
}

/* 时间分隔线 */
.time-divider {
  text-align: center;
  margin: 8px 0;
}

.time-divider span {
  background: rgba(0,0,0,0.05);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  color: #666;
  display: inline-block;
}

/* 系统消息 */
.system-message {
  align-self: center;
  background: #e3f2fd;
  color: #1976d2;
  padding: 6px 14px;
  border-radius: 14px;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 80%;
  text-align: center;
}

.system-icon {
  font-size: 14px;
}

/* 特殊卡片容器 */
.special-card-wrapper {
  align-self: center;
  width: 90%;
  max-width: 400px;
}

/* 考勤和任务卡片 */
.attendance-card, .task-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  border: 1px solid #e3e8ef;
}

.card-header {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #e3e8ef;
}

.card-icon {
  font-size: 20px;
}

.card-title {
  flex: 1;
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.status-badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.status-badge.active {
  background: #4caf50;
  color: white;
}

.author-badge {
  background: #667eea;
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.card-body {
  padding: 16px;
}

.task-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin-bottom: 12px;
}

.progress-section {
  margin-bottom: 12px;
}

.progress-bar {
  height: 8px;
  background: #e3e8ef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s;
}

.progress-fill.success {
  background: linear-gradient(90deg, #4caf50 0%, #81c784 100%);
}

.progress-text {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.count-text {
  color: #666;
}

.count-text strong {
  color: #333;
  font-size: 14px;
}

.percentage {
  color: #667eea;
  font-weight: 600;
}

.card-footer {
  padding: 12px 16px;
  border-top: 1px solid #e3e8ef;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.card-btn {
  padding: 6px 16px;
  background: transparent;
  border: 1px solid #667eea;
  color: #667eea;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.card-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

/* 消息气泡 */
.message-wrapper {
  display: flex;
  gap: 8px;
  max-width: 75%;
  animation: messageSlideIn 0.2s ease-out;
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
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.avatar-circle.small {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.message-avatar.own .avatar-circle {
  background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
}

.message-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-author {
  font-size: 12px;
  color: #667eea;
  font-weight: 600;
  padding-left: 4px;
}

.message-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  position: relative;
  word-wrap: break-word;
  transition: all 0.2s;
}

.message-bubble:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.12);
}

.message-bubble.received {
  background: white;
  border-bottom-left-radius: 4px;
}

.message-bubble.sent {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.bubble-text {
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.bubble-meta {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}

.bubble-time {
  font-size: 11px;
  opacity: 0.7;
}

.bubble-status {
  font-size: 12px;
  opacity: 0.8;
}

/* 正在输入提示 */
.typing-indicator {
  display: flex;
  gap: 8px;
  max-width: 75%;
  animation: messageSlideIn 0.3s ease-out;
}

.typing-bubble {
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  background: #999;
  border-radius: 50%;
  animation: typingBounce 1.4s infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* 滚动到底部按钮 */
.scroll-to-bottom {
  position: absolute;
  bottom: 80px;
  right: 20px;
  width: 44px;
  height: 44px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: all 0.3s;
}

.scroll-to-bottom:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}

.scroll-to-bottom .unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ff3b30;
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
  min-width: 18px;
  text-align: center;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 输入区域 */
.chat-input-container {
  background: white;
  border-top: 1px solid #e3e8ef;
  padding: 12px 16px;
}

/* 学生工具栏 */
.student-toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.tool-btn {
  background: white;
  border: 1px solid #e3e8ef;
  border-radius: 18px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tool-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
  transform: scale(1.05);
}

.tool-btn.hand-btn {
  background: white;
}

.tool-btn.hand-btn.active {
  background: #4caf50;
  color: white;
  border-color: #4caf50;
}

.tool-btn.emoji-btn {
  min-width: unset;
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: 50%;
  font-size: 18px;
}

.divider {
  width: 1px;
  height: 24px;
  background: #e3e8ef;
}

/* 输入区 */
.input-area {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  border: 1px solid #e3e8ef;
  border-radius: 20px;
  padding: 10px 16px;
  font-family: inherit;
  font-size: 14px;
  resize: none;
  outline: none;
  background: #f5f7fa;
  transition: all 0.2s;
  max-height: 120px;
  overflow-y: auto;
  line-height: 1.5;
}

.message-input:focus {
  background: white;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
}

.send-button {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: none;
  background: #e3e8ef;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
}

.send-button.active:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(102,126,234,0.4);
}

.send-button:disabled {
  cursor: not-allowed;
}

/* 右键菜单 */
.context-menu.telegram {
  position: fixed;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  z-index: 1000;
  min-width: 140px;
  padding: 6px;
  animation: contextMenuShow 0.2s ease-out;
}

@keyframes contextMenuShow {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.context-menu-item {
  padding: 10px 14px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.context-menu-item:hover {
  background: #f5f7fa;
}

.context-menu-item.delete {
  color: #ff3b30;
}

.context-menu-item.delete:hover {
  background: #ffebee;
}

.context-menu-item i {
  font-size: 16px;
}

/* 滚动条美化 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.2);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.3);
}

/* ========== 其他区域样式保持不变 ========== */

.chat-section {
  flex: 1;
  background: #f0f2f5;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid #dcdfe6;
}
</style>