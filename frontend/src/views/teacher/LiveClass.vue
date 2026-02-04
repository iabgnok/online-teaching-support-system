<template>
  <div class="live-class-container">
    <!-- 顶部工具栏 -->
    <div class="top-toolbar">
      <div class="toolbar-left">
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
      <div class="toolbar-actions">
        <button @click="startScreenShare" class="btn-primary" :disabled="isSharing">
          {{ isSharing ? '共享中...' : '开始屏幕共享' }}
        </button>
        <button @click="endClass" class="btn-danger">结束授课</button>
        <button @click="showParticipants = !showParticipants" class="btn-secondary">{{ showParticipants ? '隐藏参与者' : '显示参与者' }}</button>
      </div>
    </div>

    <!-- 主要内容区域：画板和讨论区的父容器 -->
    <div class="main-content">
      <!-- 画板区域 -->
      <div class="canvas-section">
        <div class="canvas-toolbar">
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
            @mousedown="startDrawing"
            @mousemove="draw"
            @mouseup="stopDrawing"
            @mouseleave="stopDrawing"
            @touchstart="startDrawing"
            @touchmove="draw"
            @touchend="stopDrawing"
          ></canvas>
        </div>
      </div>

      <!-- 可折叠讨论区组件 -->
      <CollapsibleDiscussionPanel
        v-if="discussionConversationId"
        ref="discussionPanel"
        :discussion-conversation-id="discussionConversationId"
        :class-group-conversation-id="classGroupConversationId"
        :role="'teacher'"
        :current-user-id="currentUserId"
        :class-group-name="classGroupName"
        :total-participants="participantsCount"
        @send-message="handleSendMessage"
        @load-more="handleLoadMore"
        @view-attendance="viewAttendanceDetail"
        @view-task="viewTaskDetail"
        @remind-students="remindStudents"
        @start-attendance="startAttendance"
        @publish-task="publishTask"
        @share-board="shareBoard"
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

    <!-- 考勤对话框 -->
    <el-dialog title="发起考勤" v-model="showAttendanceDialog" width="400px">
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

    <!-- 任务发布对话框 - 增强版 -->
    <el-dialog 
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
import api from '../../api'
import CollapsibleDiscussionPanel from '@/components/CollapsibleDiscussionPanel.vue'

export default {
  name: 'TeacherLiveClass',
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
      
      // Dialogs
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
    // 返回按钮
    goBack() {
      this.$router.push('/chat')
    },
    
    loadUserInfo() {
      // 从localStorage获取用户信息
      this.currentUserId = localStorage.getItem('user_id')
      this.currentUserName = localStorage.getItem('user_name') || localStorage.getItem('real_name') || '教师'
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
        // 加载参与者列表
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
        // 重新获取参与者列表
        this.loadParticipants()
      })

      this.socket.on('user_left', (data) => {
        this.participantsCount--
        // 重新获取参与者列表
        this.loadParticipants()
      })

      this.socket.on('drawing_update', (data) => {
        this.drawFromServer(data)
      })

      this.socket.on('chat:new_message', (data) => {
        console.log('Teacher received chat:new_message:', data)
        // 将消息传递给CollapsibleDiscussionPanel组件
        if (this.$refs.discussionPanel && data.conversation_id) {
          this.$refs.discussionPanel.receiveMessage(data)
        }
        // 也添加到旧的messages数组（如果还在使用）
        this.addMessage(data)
      })

      this.socket.on('screen_share_started', (data) => {
        this.isSharing = true
      })

      this.socket.on('background_image_update', (data) => {
        this.backgroundImage = data.imageUrl
      })
      
      this.socket.on('attendance_update', (data) => {
          // Find message and update
          const msg = this.messages.find(m => m.message_type === 'attendance' && this.getJsonContent(m.message).attendance_id === data.attendance_id);
          if (msg) {
              const content = this.getJsonContent(msg.message);
              content.count = data.count;
              msg.message = JSON.stringify(content); // Update local state
          }
      })

      this.socket.on('task_update', (data) => {
          const msg = this.messages.find(m => m.id === data.message_id || (m.message_type === 'task' && m.id === data.message_id));
           // Note: msg.id might differ if we use temp IDs. but socket returns DB id.
           // We reload messages or try to match.
           // Simpler: iterate and check if content matches task_id if possible, or just trust ID if synced
           // In loadClassInfo we map history.
           // Let's assume ID match works if we use the one from server.
           const target = this.messages.find(m => m.id === data.message_id);
           if (target) {
               const content = this.getJsonContent(target.message);
               content.completed_ids = data.completed_ids;
               target.message = JSON.stringify(content);
           }
      })

      this.socket.on('screen_share_stopped', (data) => {
        this.isSharing = false
      })
      
      this.socket.on('message_deleted', (data) => {
          this.messages = this.messages.filter(m => m.id !== data.message_id);
      })

      // WebRTC 事件处理
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

    loadParticipants() {
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
        // 重置表单为默认值
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
      // 默认截止时间：当前时间 + 2小时
      const now = new Date();
      now.setHours(now.getHours() + 2);
      return now.toISOString().slice(0, 19).replace('T', ' ');
    },

    disabledDate(time) {
      // 禁用今天之前的日期
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
      // 保存草稿到本地存储
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
      // 加载草稿
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
      // 清除草稿
      localStorage.removeItem(`task_draft_${this.lessonId}`);
    },
    
    async confirmTask() {
      // 表单验证
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

      // 确认发布
      this.$confirm('确定要发布此任务吗？发布后所有学生都将收到通知。', '确认发布', {
        confirmButtonText: '发布',
        cancelButtonText: '取消',
        type: 'info'
      }).then(async () => {
        this.isTaskPublishing = true;
        
        try {
          // 构建任务数据
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

          // 通过Socket发送任务
          this.socket.emit('publish_task', taskData);

          // 清除草稿
          this.clearDraft();
          
          // 关闭对话框
          this.showTaskDialog = false;
          
          // 成功提示
          this.$message({
            message: '任务发布成功！学生将在聊天区看到任务卡片。',
            type: 'success',
            duration: 3000
          });

          // 重置表单
          this.$refs.taskFormRef.resetFields();
        } catch (error) {
          console.error('发布任务失败:', error);
          this.$message.error('发布任务失败，请重试');
        } finally {
          this.isTaskPublishing = false;
        }
      }).catch(() => {
        // 用户取消
      });
    },

    toggleActionMenu() {
        this.showActionMenu = !this.showActionMenu;
    },
    
    showContextMenu(e, msg) {
        // Teacher can delete any message
        this.contextMenu.message = msg;
        this.contextMenu.x = e.clientX;
        this.contextMenu.y = e.clientY;
        this.contextMenu.visible = true;
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
    
    getJsonContent(str) {
        try {
            return JSON.parse(str);
        } catch (e) {
            return {};
        }
    },

    loadClassInfo() {
      // 使用配置好的 api 实例获取课堂信息
      api.get(`/live-class/${this.lessonId}/join`)
      .then(res => {
        this.classInfo = res.data
        // 保存课堂讨论区conversation_id
        this.discussionConversationId = res.data.conversation_id
        
        // 加载班级群聊信息
        if (res.data.class_id) {
          this.loadClassGroupInfo(res.data.class_id)
        }
        
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
    
    loadClassGroupInfo(classId) {
      api.get(`/chat/class/${classId}/group`)
      .then(res => {
        this.classGroupConversationId = res.data.conversation_id
        this.classGroupName = res.data.name
      })
      .catch(err => {
        console.error('Failed to load class group info:', err)
        // 班级群聊可选，加载失败不影响课堂讨论区
      })
    },

    // 滚动到底部
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
    
    // ========== Telegram风格新增方法 ==========
    
    // 处理滚动事件
    handleScroll(e) {
      const container = e.target
      if (!container) return
      
      try {
        const scrollTop = container.scrollTop
        const scrollHeight = container.scrollHeight
        const clientHeight = container.clientHeight
        
        // 检查是否滚动到底部
        const isAtBottom = scrollHeight - scrollTop - clientHeight < 100
      
      if (isAtBottom) {
        this.showScrollButton = false
        this.unreadCount = 0
        this.isUserScrolling = false
      } else {
        this.showScrollButton = true
        this.isUserScrolling = true
      }
      
      // 检查是否需要加载更多消息
      if (scrollTop < 200 && this.hasMoreMessages) {
        this.loadMoreMessages()
      }
      } catch (error) {
        console.error('Error in handleScroll:', error)
      }
    },
    
    // 加载更多历史消息
    loadMoreMessages() {
      console.log('加载更多消息...')
      // TODO: 实现历史消息加载
    },
    
    // 判断是否显示时间分隔线
    shouldShowTimeDivider(msg, index) {
      if (index === 0) return true
      
      const prevMsg = this.messages[index - 1]
      if (!prevMsg) return false
      
      const currentTime = new Date(msg.timestamp)
      const prevTime = new Date(prevMsg.timestamp)
      
      // 超过5分钟显示时间
      return (currentTime - prevTime) > 5 * 60 * 1000
    },
    
    // 格式化时间分隔线
    formatDateDivider(timestamp) {
      const date = new Date(timestamp)
      const now = new Date()
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      const messageDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
      
      const diffDays = Math.floor((today - messageDate) / (1000 * 60 * 60 * 24))
      
      if (diffDays === 0) {
        return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      } else if (diffDays === 1) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      } else if (diffDays < 7) {
        return `${diffDays}天前 ` + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      } else {
        return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
    },
    
    // 获取考勤进度
    getAttendanceProgress(msg) {
      const content = this.getJsonContent(msg.message)
      const count = content.count || 0
      const total = this.participantsCount || 1
      return Math.round((count / total) * 100)
    },
    
    // 获取任务进度
    getTaskProgress(msg) {
      const content = this.getJsonContent(msg.message)
      const completed = (content.completed_ids || []).length
      const total = this.participantsCount || 1
      return Math.round((completed / total) * 100)
    },
    
    // 查看考勤详情
    viewAttendanceDetail(msg) {
      console.log('查看考勤详情:', msg)
      // TODO: 打开考勤详情对话框
    },
    
    // 查看任务详情
    viewTaskDetail(msg) {
      const taskData = this.getJsonContent(msg.message);
      const completedIds = taskData.completed_ids || [];
      const completedCount = completedIds.length;
      
      this.$alert(`
        <div style="text-align: left;">
          <p><strong>任务标题：</strong>${taskData.title || '课堂任务'}</p>
          <p><strong>完成情况：</strong>${completedCount} / ${this.participantsCount - 1} 人</p>
          <p><strong>完成率：</strong>${this.getTaskProgress(msg)}%</p>
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
        // 发送系统消息提醒
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

    // 获取任务类型图标
    getTaskTypeIcon(type) {
      const icons = {
        practice: '✏️',
        homework: '📚',
        discussion: '💬',
        quiz: '📝'
      };
      return icons[type] || '📝';
    },

    // 获取任务类型标签
    getTaskTypeLabel(type) {
      const labels = {
        practice: '课堂练习',
        homework: '课后作业',
        discussion: '讨论任务',
        quiz: '随堂测试'
      };
      return labels[type] || '任务';
    },

    // 获取任务类型样式类
    getTaskTypeClass(type) {
      return `task-type-${type}`;
    },

    // 获取提交方式标签
    getSubmitTypeLabel(type) {
      const labels = {
        online: '在线提交',
        verbal: '口头汇报',
        inclass: '课堂完成',
        upload: '文件上传'
      };
      return labels[type] || '在线提交';
    },

    // 格式化截止时间
    formatDeadline(deadline) {
      if (!deadline) return '未设置';
      const date = new Date(deadline);
      const now = new Date();
      const diff = date - now;
      
      if (diff < 0) {
        return '已截止';
      } else if (diff < 3600000) { // 1小时内
        return `${Math.floor(diff / 60000)}分钟后`;
      } else if (diff < 86400000) { // 24小时内
        return `${Math.floor(diff / 3600000)}小时后`;
      } else {
        return date.toLocaleString('zh-CN', { 
          month: 'short', 
          day: 'numeric', 
          hour: '2-digit', 
          minute: '2-digit' 
        });
      }
    },
    
    // 处理输入（正在输入提示）
    handleTyping() {
      if (this.typingTimer) {
        clearTimeout(this.typingTimer)
      }
      
      // 发送正在输入信号
      if (this.socket) {
        this.socket.emit('user_typing', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          user_name: this.currentUserName
        })
      }
      
      // 3秒后自动取消
      this.typingTimer = setTimeout(() => {
        if (this.socket) {
          this.socket.emit('user_stop_typing', {
            lesson_id: this.lessonId,
            user_id: this.currentUserId
          })
        }
      }, 3000)
    },
    
    // 处理Shift+Enter换行
    handleShiftEnter(e) {
      // textarea默认支持Shift+Enter换行，不需要额外处理
    },
    
    // 回复消息
    replyToMessage() {
      if (this.contextMenu.message) {
        console.log('回复消息:', this.contextMenu.message)
        // TODO: 实现消息引用功能
        this.newMessage = `回复 @${this.contextMenu.message.user_name}: `
        this.$refs.messageInput?.focus()
      }
      this.closeContextMenu()
    },
    
    // 分享板书
    shareBoard() {
      console.log('分享板书快照')
      // TODO: 实现板书快照分享功能
      this.showActionMenu = false
    },
    
    // 重写addMessage以支持未读计数
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
      
      // 如果用户正在浏览历史消息，增加未读计数
      if (this.isUserScrolling && data.user_id !== this.currentUserId) {
        this.unreadCount++
      }
      
      // 如果在底部，自动滚动
      this.$nextTick(() => {
        if (!this.isUserScrolling) {
          this.scrollToBottom()
        }
      })
    },
    
    // ========== 原有方法保持不变 ==========


    // 画板方法
    setTool(tool) {
      this.currentTool = tool
    },

    changeColor() {
      // 颜色已通过v-model绑定
    },

    changeBrushSize() {
      // 大小已通过v-model绑定
    },

    startDrawing(e) {
      this.isDrawing = true
      const rect = this.canvas.getBoundingClientRect()
      const clientX = e.clientX || (e.touches && e.touches[0].clientX)
      const clientY = e.clientY || (e.touches && e.touches[0].clientY)
      this.lastX = clientX - rect.left
      this.lastY = clientY - rect.top
    },

    draw(e) {
      if (!this.isDrawing) return

      e.preventDefault()
      const rect = this.canvas.getBoundingClientRect()
      const clientX = e.clientX || (e.touches && e.touches[0].clientX)
      const clientY = e.clientY || (e.touches && e.touches[0].clientY)
      const x = clientX - rect.left
      const y = clientY - rect.top

      // 本地绘制
      this.drawLine(this.lastX, this.lastY, x, y)

      // 发送到服务器
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
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)
      // 可以发送清空命令到服务器
    },

    undo() {
      // 撤销功能需要更复杂的实现
      alert('撤销功能开发中')
    },

    // 屏幕共享 - WebRTC 实现
    async startScreenShare() {
      try {
        // 获取屏幕共享流
        this.screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: { mediaSource: 'screen' },
          audio: false
        })

        // 创建 RTCPeerConnection
        this.peerConnection = new RTCPeerConnection({
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
          ]
        })

        // 添加流到连接
        this.screenStream.getTracks().forEach(track => {
          this.peerConnection.addTrack(track, this.screenStream)
        })

        // 设置本地视频显示
        this.$nextTick(() => {
          if (this.$refs.screenVideo) {
            this.$refs.screenVideo.srcObject = this.screenStream
          }
        })

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

        // 创建 offer
        const offer = await this.peerConnection.createOffer()
        await this.peerConnection.setLocalDescription(offer)

        // 发送 offer 给服务器
        this.socket.emit('webrtc_offer', {
          lesson_id: this.lessonId,
          user_id: this.currentUserId,
          offer: offer
        })

        // 监听用户停止共享
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

    // 聊天方法
    sendMessage() {
      if (!this.newMessage.trim()) return
      console.log('Teacher sending message:', this.newMessage.trim())

      this.socket.emit('chat_message', {
        lesson_id: this.lessonId,
        user_id: this.currentUserId,
        user_name: this.currentUserName,
        message: this.newMessage.trim()
      })

      this.newMessage = ''
    },

    addMessage(msg) {
      this.messages.push({
        ...msg,
        id: Date.now() + Math.random()
      })

      this.$nextTick(() => {
        const container = this.$refs.messagesContainer
        if (container) {
          try {
            container.scrollTop = container.scrollHeight
          } catch (error) {
            console.error('Error scrolling after new message:', error)
          }
        }
      })
    },

    // ========== CollapsibleDiscussionPanel事件处理 ==========
    
    handleSendMessage({ conversationId, message, chatType, messageType }) {
      // 参考Chat.vue的实现，使用chat:send_message事件
      this.socket.emit('chat:send_message', {
        conversation_id: conversationId,
        user_id: this.currentUserId,
        content: message,
        message_type: messageType || 'text',
        lesson_id: chatType === 'discussion' ? this.lessonId : null
      })
    },
    
    handleLoadMore({ conversationId, chatType }) {
      // 加载更多消息 - 待实现
      console.log('Load more messages for:', conversationId, chatType)
    },
    
    // 其他方法
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

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
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

/* 顶部工具栏 - Telegram风格 */
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

.teacher-tools {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding: 0.5rem;
    background: white;
    border-radius: 8px;
    margin-bottom: 1rem;
}

.tool-btn {
    padding: 0.5rem 1rem;
    background: #f8f9fa;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
}

.tool-btn:hover {
    background: #e2e6ea;
}

/* ========== 移除旧的右侧面板样式 ==========  */
/* CollapsibleDiscussionPanel组件现在直接在main-content中，不需要额外的right-panel包装 */

/* ========== Telegram风格聊天区域样式 ========== */

.chat-section.telegram-style {
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e5e5e5;
  overflow: hidden;
  position: relative;
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

/* 加载更多提示 */
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
  position: relative;
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

/* 考勤卡片 */
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
  word-break: break-word;
}

/* 任务元数据 */
.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.meta-item i {
  font-size: 14px;
  color: #667eea;
}

/* 任务提示 */
.task-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: #fff3e0;
  border-left: 3px solid #ff9800;
  border-radius: 4px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #e65100;
}

.task-hint i {
  margin-top: 2px;
  flex-shrink: 0;
}

/* 任务类型徽章 */
.type-badge {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  margin-left: auto;
}

.task-type-practice {
  background: #e3f2fd;
  color: #1976d2;
}

.task-type-homework {
  background: #f3e5f5;
  color: #7b1fa2;
}

.task-type-discussion {
  background: #e8f5e9;
  color: #388e3c;
}

.task-type-quiz {
  background: #fff3e0;
  color: #f57c00;
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

.card-btn.secondary {
  border-color: #999;
  color: #999;
}

.card-btn.primary {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.card-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102,126,234,0.3);
}

.card-btn.secondary:hover {
  background: #f5f7fa;
  border-color: #667eea;
  color: #667eea;
}

.card-btn.primary:hover {
  background: #5568d3;
  box-shadow: 0 2px 8px rgba(102,126,234,0.5);
}

/* 消息气泡 - Telegram风格 */
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
  display: flex;
  gap: -2px;
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

.input-toolbar {
  margin-bottom: 8px;
}

.toolbar-left {
  position: relative;
}

.tool-button {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: #f5f7fa;
  color: #667eea;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}

.tool-button:hover {
  background: #667eea;
  color: white;
  transform: rotate(90deg);
}

.action-menu {
  position: absolute;
  bottom: 45px;
  left: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  padding: 8px;
  min-width: 160px;
  z-index: 100;
}

.action-menu .menu-item {
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.action-menu .menu-item:hover {
  background: #f5f7fa;
  color: #667eea;
}

.action-menu .menu-item i {
  font-size: 16px;
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s;
}

.slide-up-enter-from, .slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

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

/* ========== 参与者面板样式 ========== */
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