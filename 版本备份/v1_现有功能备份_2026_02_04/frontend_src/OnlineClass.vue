<template>
  <div class="live-class-container">
    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <div class="toolbar-left" v-if="isTeacher">
        <button @click="goBack" class="btn-back" title="返回">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
        </button>
        <div class="class-info">
          <h2>{{ classInfo.title }}</h2>
          <span class="lesson-id">课堂ID: {{ lessonId }}</span>
          <span class="participants">参与者: {{ participantsCount }}</span>
        </div>
      </div>
      <div class="class-info" v-else>
        <h2>{{ classInfo.title }}</h2>
        <span class="lesson-id">课堂ID: {{ lessonId }}</span>
        <span class="participants">参与者: {{ participantsCount }}</span>
      </div>
      <div class="toolbar-actions">
        <!-- 教师特有按钮 -->
        <button v-if="isTeacher" @click="startScreenShare" class="btn-primary" :disabled="isSharing">
          {{ isSharing ? '共享中...' : '开始屏幕共享' }}
        </button>
        <button v-if="isTeacher" @click="endClass" class="btn-danger">结束授课</button>
        <!-- 学生退出按钮 -->
        <button v-else @click="exitClass" class="btn-danger">退出课堂</button>
        <!-- 显示/隐藏参与者 -->
        <button @click="showParticipants = !showParticipants" class="btn-secondary">
          {{ showParticipants ? '隐藏参与者' : '显示参与者' }}
        </button>
      </div>
    </div>

    <!-- 主要内容区域：画板和讨论区的父容器 -->
    <div class="main-content">
      <!-- 画板区域 -->
      <div class="canvas-section">
        <!-- 教师画板工具栏 -->
        <div v-if="isTeacher" class="canvas-toolbar">
          <button @click="setTool('pen')" :class="{ active: currentTool === 'pen' }">✏️ 画笔</button>
          <button @click="setTool('eraser')" :class="{ active: currentTool === 'eraser' }">🧽 橡皮</button>
          <input type="color" v-model="currentColor" @change="changeColor" title="颜色">
          <input type="range" min="1" max="20" v-model="brushSize" @input="changeBrushSize" title="笔刷大小">
          <button @click="clearCanvas" title="清空">🗑️</button>
          <button @click="undo" title="撤销">↶</button>
          <div class="divider-vertical"></div>
          <button @click="triggerFileUpload" title="上传板书图片">🖼️ 图片</button>
          <input type="file" ref="fileInput" @change="handleFileUpload" style="display: none" accept="image/*">
        </div>
        <div class="canvas-container">
          <img v-if="backgroundImage" :src="backgroundImage" class="canvas-background">
          <canvas
            ref="canvas"
            :readonly="!isTeacher"
            @mousedown="isTeacher && startDrawing"
            @mousemove="isTeacher && draw"
            @mouseup="isTeacher && stopDrawing"
            @mouseleave="isTeacher && stopDrawing"
            @touchstart="isTeacher && startDrawing"
            @touchmove="isTeacher && draw"
            @touchend="isTeacher && stopDrawing"
          ></canvas>
        </div>
      </div>

      <!-- 可折叠讨论区组件 -->
      <CollapsibleDiscussionPanel
        v-if="discussionConversationId"
        ref="discussionPanel"
        :discussion-conversation-id="discussionConversationId"
        :class-group-conversation-id="classGroupConversationId"
        :role="userRole"
        :current-user-id="currentUserId"
        :class-group-name="classGroupName"
        :total-participants="participantsCount"
        @send-message="handleSendMessage"
        @load-more="handleLoadMore"
        @view-attendance="isTeacher && viewAttendanceDetail"
        @view-task="isTeacher && viewTaskDetail"
        @remind-students="isTeacher && remindStudents"
        @start-attendance="isTeacher && startAttendance"
        @publish-task="isTeacher && publishTask"
        @share-board="isTeacher && shareBoard"
        @do-attendance="!isTeacher && doAttendance"
        @submit-task="!isTeacher && submitTask"
        @raise-hand="!isTeacher && handleRaiseHand"
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

    <!-- 教师特有：考勤对话框 -->
    <el-dialog v-if="isTeacher" title="发起考勤" v-model="showAttendanceDialog" width="400px">
      <el-form label-position="top">
        <el-form-item label="考勤标题">
          <el-input v-model="attendanceForm.title" placeholder="例如：课前签到"></el-input>
        </el-form-item>
        <el-form-item label="有效时长 (分钟)">
          <el-input-number v-model="attendanceForm.duration" :min="1" :max="30"></el-input-number>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAttendanceDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmAttendance">立即开始</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 教师特有：任务发布对话框 -->
    <el-dialog 
      v-if="isTeacher"
      title="📝 发布课堂任务" 
      v-model="showTaskDialog" 
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="taskForm" label-position="top" :rules="taskRules" ref="taskFormRef">
        <el-form-item label="任务标题" prop="title">
          <el-input 
            v-model="taskForm.title" 
            placeholder="例如：完成第3章练习题"
            maxlength="100"
            show-word-limit
          ></el-input>
        </el-form-item>

        <el-form-item label="任务类型" prop="type">
          <el-radio-group v-model="taskForm.type">
            <el-radio label="practice">课堂练习</el-radio>
            <el-radio label="homework">课后作业</el-radio>
            <el-radio label="discussion">讨论任务</el-radio>
            <el-radio label="quiz">随堂测试</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="任务描述" prop="content">
          <el-input 
            type="textarea" 
            v-model="taskForm.content" 
            :rows="5" 
            placeholder="请详细描述任务要求和完成标准..."
            maxlength="1000"
            show-word-limit
          ></el-input>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="截止时间" prop="deadline">
              <el-date-picker
                v-model="taskForm.deadline"
                type="datetime"
                placeholder="选择截止时间"
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                :disabled-date="disabledDate"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计时长" prop="estimatedTime">
              <el-input-number 
                v-model="taskForm.estimatedTime" 
                :min="5" 
                :max="300" 
                :step="5"
                controls-position="right"
                style="width: 100%"
              />
              <span style="margin-left: 8px; color: #999; font-size: 12px;">分钟</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="满分分值">
              <el-input-number 
                v-model="taskForm.totalScore" 
                :min="0" 
                :max="1000" 
                :step="10"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="提交方式">
              <el-select v-model="taskForm.submitType" placeholder="请选择" style="width: 100%">
                <el-option label="在线提交" value="online"></el-option>
                <el-option label="口头汇报" value="verbal"></el-option>
                <el-option label="课堂完成" value="inclass"></el-option>
                <el-option label="文件上传" value="upload"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="任务提示">
          <el-input 
            v-model="taskForm.hint" 
            placeholder="可选：给学生的提示或注意事项"
            maxlength="200"
            show-word-limit
          ></el-input>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="taskForm.allowLateSubmit">允许逾期提交（会有标记）</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="taskForm.notifyStudents">立即通知全体学生</el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cancelTask">取消</el-button>
          <el-button @click="saveDraft" :loading="isDraftSaving">保存草稿</el-button>
          <el-button type="primary" @click="confirmTask" :loading="isTaskPublishing">
            <i class="el-icon-upload"></i> 发布任务
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import io from 'socket.io-client'
import api from '../api'
import CollapsibleDiscussionPanel from '@/components/CollapsibleDiscussionPanel.vue'

export default {
  name: 'OnlineClass',
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
      messages: [],
      newMessage: '',
      currentUserId: null,
      currentUserName: '',
      userRole: 'student', // 'teacher' 或 'student'
      
      // 新增：讨论区相关
      discussionConversationId: null,
      classGroupConversationId: null,
      classGroupName: '',
      
      showActionMenu: false,
      
      // Telegram风格新增状态
      showScrollButton: false,
      unreadCount: 0,
      hasMoreMessages: false,
      someoneTyping: null,
      typingTimer: null,
      isUserScrolling: false,
      lastMessageTime: null,
      
      // Context Menu
      contextMenu: {
          visible: false,
          x: 0,
          y: 0,
          message: null
      },
      
      // 教师特有：Dialogs
      showAttendanceDialog: false,
      attendanceForm: {
        title: '',
        duration: 5
      },
      
      showTaskDialog: false,
      taskForm: {
        title: '',
        type: 'practice',
        content: '',
        deadline: '',
        estimatedTime: 30,
        totalScore: 100,
        submitType: 'online',
        hint: '',
        allowLateSubmit: false,
        notifyStudents: true
      },
      taskRules: {
        title: [
          { required: true, message: '请输入任务标题', trigger: 'blur' },
          { min: 2, max: 100, message: '标题长度在2-100个字符', trigger: 'blur' }
        ],
        content: [
          { required: true, message: '请输入任务描述', trigger: 'blur' },
          { min: 10, message: '任务描述至少10个字符', trigger: 'blur' }
        ],
        deadline: [
          { required: true, message: '请选择截止时间', trigger: 'change' }
        ]
      },
      isTaskPublishing: false,
      isDraftSaving: false,

      // 画板相关
      canvas: null,
      ctx: null,
      isDrawing: false,
      currentTool: 'pen',
      currentColor: '#000000',
      brushSize: 2,
      lastX: 0,
      lastY: 0,

      backgroundImage: null,
      // 屏幕共享
      isSharing: false,
      screenStream: null,
      peerConnection: null,
      remoteVideo: null,
    }
  },
  
  computed: {
    isTeacher() {
      return this.userRole === 'teacher'
    },
    isStudent() {
      return this.userRole === 'student'
    }
  },
  
  mounted() {
    this.loadUserInfo()
    this.initSocket()
    this.initCanvas()
    this.loadClassInfo()
    this.loadDraft() // 加载草稿
    document.addEventListener('click', this.closeContextMenu);
  },
  
  beforeUnmount() {
    document.removeEventListener('click', this.closeContextMenu);
    if (this.socket) {
      this.socket.disconnect()
    }
    if (this.screenStream) {
      this.screenStream.getTracks().forEach(track => track.stop())
    }
  },
  
  methods: {
    // ========== 通用方法 ==========
    
    loadUserInfo() {
      this.currentUserId = parseInt(localStorage.getItem('user_id') || '0')
      this.currentUserName = localStorage.getItem('user_name') || localStorage.getItem('real_name') || localStorage.getItem('username') || '用户'
      
      // 确定用户角色
      const userRole = localStorage.getItem('user_role')
      this.userRole = userRole === 'teacher' ? 'teacher' : 'student'
    },
    
    initSocket() {
      const socketUrl = import.meta.env.DEV ? 'http://localhost:5000' : '/'
      
      this.socket = io(socketUrl, {
        transports: ['websocket', 'polling'],
        forceNew: true
      })

      this.socket.on('connect', () => {
        console.log('Connected to server')
        this.socket.emit('join_class', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          user_name: this.currentUserName,
          role: this.userRole
        })
      })

      this.socket.on('joined_class', (data) => {
        console.log('Joined class:', data.lesson_id)
        this.loadParticipants()
      })

      this.socket.on('user_joined', (data) => {
        this.participantsCount++
        this.addMessage({
          user_name: '系统',
          message: `${data.user_name} 加入了课堂`,
          timestamp: data.timestamp,
          message_type: 'system'
        })
        this.loadParticipants()
      })

      this.socket.on('user_left', (data) => {
        this.participantsCount--
        this.loadParticipants()
      })

      this.socket.on('drawing_update', (data) => {
        this.drawFromServer(data)
      })

      this.socket.on('chat:new_message', (data) => {
        console.log('Received chat:new_message:', data)
        if (this.$refs.discussionPanel && data.conversation_id) {
          this.$refs.discussionPanel.receiveMessage(data)
        }
        this.addMessage(data)
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

      this.socket.on('screen_share_started', (data) => {
        this.isSharing = true
      })

      this.socket.on('screen_share_stopped', (data) => {
        this.isSharing = false
      })
      
      this.socket.on('message_deleted', (data) => {
          this.messages = this.messages.filter(m => m.id !== data.message_id);
      })

      this.socket.on('webrtc_answer', async (data) => {
        if (this.peerConnection && data.answer) {
          try {
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer))
            console.log('Remote description set for teacher, screen sharing active')
            this.isSharing = true
          } catch (err) {
            console.error('Error setting remote description:', err)
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

      this.socket.on('error', (error) => {
        console.error('Socket error:', error)
        alert('连接错误: ' + error.message)
      })
    },

    initCanvas() {
      this.$nextTick(() => {
        this.canvas = this.$refs.canvas
        if (this.canvas) {
          this.ctx = this.canvas.getContext('2d')
          this.resizeCanvas()
          window.addEventListener('resize', this.resizeCanvas)
        }
      })
    },

    resizeCanvas() {
      if (this.canvas) {
        const container = this.canvas.parentElement
        this.canvas.width = container.clientWidth
        this.canvas.height = container.clientHeight
      }
    },

    loadParticipants() {
      api.get(`/live-class/${this.lessonId}/participants`)
      .then(res => {
        this.participants = res.data.filter(p => !p.left_at)
        this.participantsCount = this.participants.length
      })
      .catch(err => {
        console.error('Failed to load participants:', err)
      })
    },

    loadClassInfo() {
      api.get(`/live-class/${this.lessonId}/join`)
      .then(res => {
        this.classInfo = res.data
        this.discussionConversationId = res.data.conversation_id
        
        if (res.data.class_id) {
          this.loadClassGroupInfo(res.data.class_id)
        }
        
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
    
    loadClassGroupInfo(classId) {
      api.get(`/chat/class/${classId}/group`)
      .then(res => {
        this.classGroupConversationId = res.data.conversation_id
        this.classGroupName = res.data.name
      })
      .catch(err => {
        console.error('Failed to load class group info:', err)
      })
    },

    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) {
        try {
          this.isUserScrolling = false
          container.scrollTop = container.scrollHeight
          this.unreadCount = 0
          this.showScrollButton = false
        } catch (error) {
          console.error('Error scrolling to bottom:', error)
        }
      }
    },

    handleSendMessage({ conversationId, message, chatType, messageType }) {
      this.socket.emit('chat:send_message', {
        conversation_id: conversationId,
        user_id: this.currentUserId,
        content: message,
        message_type: messageType || 'text',
        lesson_id: chatType === 'discussion' ? this.lessonId : null
      })
    },
    
    handleLoadMore({ conversationId, chatType }) {
      console.log('Load more messages for:', conversationId, chatType)
    },

    closeContextMenu() {
        this.contextMenu.visible = false
        this.contextMenu.message = null
    },

    getJsonContent(str) {
        try {
            return JSON.parse(str)
        } catch (e) {
            return {}
        }
    },

    addMessage(data) {
      const messageData = {
        id: data.id || Date.now(),
        user_id: data.user_id,
        user_name: data.user_name,
        message: data.message,
        timestamp: data.timestamp || new Date().toISOString(),
        message_type: data.message_type || 'text'
      }
      
      this.messages.push(messageData)
      
      if (this.isUserScrolling && data.user_id !== this.currentUserId) {
        this.unreadCount++
      }
      
      this.$nextTick(() => {
        if (!this.isUserScrolling) {
          this.scrollToBottom()
        }
      })
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    },

    // ========== 教师特有方法 ==========
    
    goBack() {
      this.$router.push('/chat')
    },

    handleFileUpload(event) {
      const file = event.target.files[0]
      if (!file) return

      const formData = new FormData()
      formData.append('file', file)

      api.post('/live-class/upload-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      .then(res => {
        const imageUrl = res.data.url
        this.socket.emit('set_background_image', {
          lesson_id: this.lessonId,
          imageUrl: imageUrl
        })
      })
      .catch(err => {
        alert('Upload failed: ' + (err.response?.data?.error || err.message))
      })
    },

    triggerFileUpload() {
        this.$refs.fileInput.click()
    },

    startAttendance() {
        this.attendanceForm.title = '课堂签到 ' + new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'});
        this.attendanceForm.duration = 5;
        this.showAttendanceDialog = true;
        this.showActionMenu = false;
    },
    
    confirmAttendance() {
        this.socket.emit('start_attendance', {
            lesson_id: this.lessonId,
            user_id: this.currentUserId,
            title: this.attendanceForm.title,
            duration: this.attendanceForm.duration
        })
        this.showAttendanceDialog = false;
        this.$message.success('考勤已发起');
    },
    
    publishTask() {
        this.taskForm = {
          title: '',
          type: 'practice',
          content: '',
          deadline: this.getDefaultDeadline(),
          estimatedTime: 30,
          totalScore: 100,
          submitType: 'online',
          hint: '',
          allowLateSubmit: false,
          notifyStudents: true
        };
        this.showTaskDialog = true;
        this.showActionMenu = false;
    },

    getDefaultDeadline() {
      const now = new Date();
      now.setHours(now.getHours() + 2);
      return now.toISOString().slice(0, 19).replace('T', ' ');
    },

    disabledDate(time) {
      return time.getTime() < Date.now() - 8.64e7;
    },

    cancelTask() {
      this.$confirm('确定要取消发布任务吗？填写的内容将不会保存。', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '继续编辑',
        type: 'warning'
      }).then(() => {
        this.showTaskDialog = false;
      }).catch(() => {});
    },

    async saveDraft() {
      this.isDraftSaving = true;
      try {
        localStorage.setItem(`task_draft_${this.lessonId}`, JSON.stringify(this.taskForm));
        this.$message.success('草稿已保存');
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (error) {
        this.$message.error('保存草稿失败');
      } finally {
        this.isDraftSaving = false;
      }
    },

    loadDraft() {
      try {
        const draft = localStorage.getItem(`task_draft_${this.lessonId}`);
        if (draft) {
          this.taskForm = JSON.parse(draft);
          this.$message.info('已加载草稿');
        }
      } catch (error) {
        console.error('加载草稿失败', error);
      }
    },

    clearDraft() {
      localStorage.removeItem(`task_draft_${this.lessonId}`);
    },
    
    async confirmTask() {
      if (!this.$refs.taskFormRef) {
        this.$message.error('表单未初始化');
        return;
      }

      try {
        await this.$refs.taskFormRef.validate();
      } catch (error) {
        this.$message.warning('请完善必填信息');
        return;
      }

      this.$confirm('确定要发布此任务吗？发布后所有学生都将收到通知。', '确认发布', {
        confirmButtonText: '发布',
        cancelButtonText: '取消',
        type: 'info'
      }).then(async () => {
        this.isTaskPublishing = true;
        
        try {
          const taskData = {
            lesson_id: this.lessonId,
            user_id: this.currentUserId,
            title: this.taskForm.title.trim(),
            type: this.taskForm.type,
            content: this.taskForm.content.trim(),
            deadline: this.taskForm.deadline,
            estimated_time: this.taskForm.estimatedTime,
            total_score: this.taskForm.totalScore,
            submit_type: this.taskForm.submitType,
            hint: this.taskForm.hint.trim(),
            allow_late_submit: this.taskForm.allowLateSubmit,
            notify_students: this.taskForm.notifyStudents
          };

          this.socket.emit('publish_task', taskData);

          this.clearDraft();
          
          this.showTaskDialog = false;
          
          this.$message({
            message: '任务发布成功！学生将在聊天区看到任务卡片。',
            type: 'success',
            duration: 3000
          });

          this.$refs.taskFormRef.resetFields();
        } catch (error) {
          console.error('发布任务失败:', error);
          this.$message.error('发布任务失败，请重试');
        } finally {
          this.isTaskPublishing = false;
        }
      }).catch(() => {});
    },

    viewAttendanceDetail(msg) {
      console.log('查看考勤详情:', msg)
    },
    
    viewTaskDetail(msg) {
      const taskData = this.getJsonContent(msg.message);
      const completedIds = taskData.completed_ids || [];
      const completedCount = completedIds.length;
      
      this.$alert(`
        <div style="text-align: left;">
          <p><strong>任务标题：</strong>${taskData.title || '课堂任务'}</p>
          <p><strong>完成情况：</strong>${completedCount} / ${this.participantsCount - 1} 人</p>
          <p><strong>完成率：</strong>${Math.round((completedCount / (this.participantsCount - 1)) * 100)}%</p>
          <hr style="margin: 10px 0;">
          <p><strong>已完成学生：</strong></p>
          <ul style="margin: 5px 0; padding-left: 20px;">
            ${completedIds.length > 0 ? completedIds.map(id => `<li>学生ID: ${id}</li>`).join('') : '<li style="color: #999;">暂无</li>'}
          </ul>
        </div>
      `, '任务完成列表', {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '关闭'
      });
    },

    remindStudents(msg) {
      const taskData = this.getJsonContent(msg.message);
      const completedIds = taskData.completed_ids || [];
      const uncompletedCount = this.participantsCount - 1 - completedIds.length;

      if (uncompletedCount === 0) {
        this.$message.info('所有学生都已完成任务');
        return;
      }

      this.$confirm(`还有 ${uncompletedCount} 位学生未完成任务，确定要发送提醒吗？`, '提醒学生', {
        confirmButtonText: '发送提醒',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.socket.emit('chat_message', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          user_name: this.currentUserName,
          message: `⏰ 提醒：还有${uncompletedCount}位同学未完成任务「${taskData.title}」，请抓紧时间完成！`,
          message_type: 'system'
        });
        this.$message.success('提醒已发送');
      }).catch(() => {});
    },

    shareBoard() {
      console.log('分享板书快照')
      this.showActionMenu = false
    },

    // 画板方法
    setTool(tool) {
      this.currentTool = tool
    },

    changeColor() {
    },

    changeBrushSize() {
    },

    startDrawing(e) {
      if (!this.isTeacher) return
      this.isDrawing = true
      const rect = this.canvas.getBoundingClientRect()
      const clientX = e.clientX || (e.touches && e.touches[0].clientX)
      const clientY = e.clientY || (e.touches && e.touches[0].clientY)
      this.lastX = clientX - rect.left
      this.lastY = clientY - rect.top
    },

    draw(e) {
      if (!this.isDrawing || !this.isTeacher) return

      e.preventDefault()
      const rect = this.canvas.getBoundingClientRect()
      const clientX = e.clientX || (e.touches && e.touches[0].clientX)
      const clientY = e.clientY || (e.touches && e.touches[0].clientY)
      const x = clientX - rect.left
      const y = clientY - rect.top

      this.drawLine(this.lastX, this.lastY, x, y)

      const data = {
        lesson_id: this.lessonId,
        user_id: this.currentUserId,
        prevX: this.lastX / this.canvas.width,
        prevY: this.lastY / this.canvas.height,
        x: x / this.canvas.width,
        y: y / this.canvas.height,
        color: this.currentColor,
        brush_size: this.brushSize,
        action: this.currentTool
      }
      this.socket.emit('drawing', data)

      this.lastX = x
      this.lastY = y
    },

    stopDrawing() {
      this.isDrawing = false
    },

    drawLine(x1, y1, x2, y2, color, size) {
      if (!this.ctx) return
      this.ctx.beginPath()
      this.ctx.moveTo(x1, y1)
      this.ctx.lineTo(x2, y2)
      this.ctx.strokeStyle = color || this.currentColor
      this.ctx.lineWidth = size || this.brushSize
      this.ctx.lineCap = 'round'
      this.ctx.lineJoin = 'round'
      this.ctx.stroke()
    },

    drawFromServer(data) {
      if (!this.canvas) return
      const x = data.x * this.canvas.width
      const y = data.y * this.canvas.height
      const prevX = data.prevX ? data.prevX * this.canvas.width : x
      const prevY = data.prevY ? data.prevY * this.canvas.height : y

      this.drawLine(prevX, prevY, x, y, data.color, data.brush_size)
    },

    clearCanvas() {
      if (!this.isTeacher || !this.ctx) return
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
    },

    undo() {
      alert('撤销功能开发中')
    },

    async startScreenShare() {
      try {
        this.screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: { mediaSource: 'screen' },
          audio: false
        })

        this.peerConnection = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ]
        })

        this.screenStream.getTracks().forEach(track => {
          this.peerConnection.addTrack(track, this.screenStream)
        })

        this.$nextTick(() => {
          if (this.$refs.screenVideo) {
            this.$refs.screenVideo.srcObject = this.screenStream
          }
        })

        this.peerConnection.onicecandidate = (event) => {
          if (event.candidate) {
            this.socket.emit('webrtc_ice_candidate', {
              lesson_id: this.lessonId,
              user_id: this.currentUserId,
              candidate: event.candidate
            })
          }
        }

        const offer = await this.peerConnection.createOffer()
        await this.peerConnection.setLocalDescription(offer)

        this.socket.emit('webrtc_offer', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          offer: offer
        })

        this.screenStream.getVideoTracks()[0].addEventListener('ended', () => {
          this.stopScreenShare()
        })

        console.log('Screen sharing offer sent, waiting for answer...')
      } catch (err) {
        console.error('Error starting screen share:', err)
        alert('无法开始屏幕共享: ' + err.message)
      }
    },

    stopScreenShare() {
      if (this.screenStream) {
        this.screenStream.getTracks().forEach(track => track.stop())
        this.screenStream = null
      }
      if (this.peerConnection) {
        this.peerConnection.close()
        this.peerConnection = null
      }
      this.isSharing = false

      this.socket.emit('stop_screen_share', {
        lesson_id: this.lessonId,
        user_id: this.currentUserId
      })
    },

    endClass() {
      if (confirm('确定要结束授课吗？')) {
        api.post(`/live-class/${this.lessonId}/end`)
        .then(res => {
          alert('授课已结束')
          this.$router.push('/teacher/dashboard')
        })
        .catch(err => {
          console.error('Failed to end class:', err)
          alert('结束授课失败: ' + (err.response?.data?.error || err.message))
        })
      }
    },

    // ========== 学生特有方法 ==========
    
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
  background: #f5f5f5;
}

/* 顶部工具栏 */
.top-toolbar {
  background: #ffffff;
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e5e5e5;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  min-height: 56px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.btn-back {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #8e8e93;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  padding: 0;
  flex-shrink: 0;
}

.btn-back:hover {
  background: rgba(0, 0, 0, 0.05);
}

.btn-back:active {
  transform: scale(0.95);
}

.btn-back svg {
  width: 20px;
  height: 20px;
}

.class-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.class-info h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lesson-id, .participants {
  margin: 0;
  color: #8e8e93;
  font-size: 13px;
  display: inline;
}

.lesson-id::after {
  content: '  •  ';
  margin: 0 4px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 按钮统一样式 */
.btn-primary, .btn-danger, .btn-secondary {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}

.btn-primary {
  background: #409eff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #66b1ff;
}

.btn-primary:disabled {
  background: #e4e7ed;
  color: #c0c4cc;
  cursor: not-allowed;
}

.btn-danger {
  background: #f56c6c;
  color: white;
}

.btn-danger:hover {
  background: #f78989;
}

.btn-secondary {
  background: #f5f5f7;
  color: #606266;
}

.btn-secondary:hover {
  background: #ebebed;
}

.main-content {
  flex: 1;
  display: flex;
  padding: 16px;
  gap: 0;
  background: #f5f7fa;
  position: relative;
}

.canvas-section {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e5e5;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-right: 0;
}

.canvas-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: center;
  padding: 12px;
  background: #f5f5f7;
  border-radius: 12px;
  border: 1px solid #e5e5e5;
}

.divider-vertical {
  width: 1px;
  height: 24px;
  background-color: #dcdfe6;
  margin: 0 4px;
}

.canvas-toolbar button {
  padding: 8px 12px;
  border: none;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  color: #606266;
  font-weight: 500;
}

.canvas-toolbar button:hover {
  background: #ebebed;
  transform: translateY(-1px);
}

.canvas-toolbar button.active {
  background: #409eff;
  color: white;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.3);
}

.canvas-toolbar input[type="color"],
.canvas-toolbar input[type="range"] {
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
}

.canvas-container {
  flex: 1;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  background: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

canvas {
  width: 100%;
  height: 100%;
  cursor: crosshair;
  position: relative;
  z-index: 10;
}

canvas[readonly] {
  cursor: default;
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

/* 参与者面板 */
.participants-panel {
  position: fixed;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  max-width: 200px;
}

.participants-panel ul {
  list-style: none;
  padding: 0;
}

.participants-panel li {
  padding: 0.25rem 0;
  border-bottom: 1px solid #eee;
}
</style>
