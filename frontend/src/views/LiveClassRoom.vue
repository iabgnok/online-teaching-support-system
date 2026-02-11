<template>
  <div class="live-class-room" :class="{ 'is-teacher': isTeacher }">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>正在加载课堂...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-overlay">
      <div class="error-icon">⚠️</div>
      <h3>加载失败</h3>
      <p>{{ error }}</p>
      <button class="retry-btn" @click="loadLessonInfo">重试</button>
      <button class="back-btn" @click="exitClass">返回</button>
    </div>
    
    <!-- 主内容 -->
    <template v-else>
      <!-- 顶部工具栏 -->
      <LiveClassToolbar
        :role="userRole"
        :lesson-info="lessonInfo"
        :participant-count="onlineCount"
        :show-participants="showParticipants"
        :is-screen-sharing="isScreenSharing"
        @toggle-participants="showParticipants = !showParticipants"
        @toggle-screen-share="handleScreenShare"
        @start-attendance="handleStartAttendance"
        @publish-task="handlePublishTask"
        @start-quiz="handleStartQuiz"
        @exit="handleExit"
      />
      
      <!-- 课堂工具栏 -->
      <ClassroomToolbar
        :lesson-info="lessonInfo"
        :classroom-status="classroomStatus"
        :participant-count="onlineCount"
        :show-participants="showParticipants"
        :is-teacher="isTeacher"
        :is-student="isStudent"
        @toggle-participants="showParticipants = !showParticipants"
        @start-attendance="handleStartAttendance"
        @publish-task="handlePublishTask"
        @start-quiz="handleStartQuiz"
        @raise-hand="handleRaiseHand"
        @share-board="handleShareBoard"
        @exit="handleExit"
      />
      
      <!-- 主要内容区域 -->
      <div class="main-content">
        <!-- 左侧：画板区域 -->
        <div class="whiteboard-wrapper">
          <!-- 画板组件 (延迟挂载直到课堂信息加载完，避免初始只读导致 UI 不一致) -->
          <WhiteBoard
            v-if="lessonInfo"
            ref="whiteboardRef"
            :lesson-id="lessonId"
            :readonly="whiteboardReadonly"
            :socket="socket"
          />
          
          <!-- 屏幕共享显示区域 -->
          <div v-if="isScreenSharing && !isTeacher" class="screen-share-view">
            <video ref="screenShareVideo" autoplay playsinline></video>
          </div>
        </div>
        
        <!-- 右侧：聊天面板 -->
        <LiveClassChat
          ref="chatRef"
          :discussion-conversation-id="discussionConversationId"
          :class-group-conversation-id="classGroupConversationId"
          :role="userRole"
          :socket="socket"
          :initial-collapsed="false"
          @collapse-change="handleChatCollapse"
          @start-attendance="handleStartAttendance"
          @publish-task="handlePublishTask"
          @share-board="handleShareBoard"
          @raise-hand="handleRaiseHand"
        />
      </div>
      
      <!-- 参与者面板 -->
      <ParticipantsPanel
        :visible="showParticipants"
        :participants="participants"
        :role="userRole"
        @close="showParticipants = false"
        @allow-speak="handleAllowSpeak"
        @focus-student="handleFocusStudent"
        @answer-student="handleAnswerStudent"
        @dismiss-hand="handleDismissHand"
      />
      
      <!-- 连接状态提示 -->
      <transition name="fade">
        <div v-if="reconnecting" class="connection-status">
          <div class="status-content">
            <div class="reconnect-spinner"></div>
            <span>正在重新连接...</span>
          </div>
        </div>
      </transition>
    </template>
  </div>
</template>

<script>
import { ref, watch, provide } from 'vue'
import { useLiveClass } from '../composables/useLiveClass'
import WhiteBoard from '../components/live-class/WhiteBoard.vue'
import LiveClassToolbar from '../components/live-class/LiveClassToolbar.vue'
import ClassroomToolbar from '../components/live-class/ClassroomToolbar.vue'
import LiveClassChat from '../components/live-class/LiveClassChat.vue'
import ParticipantsPanel from '../components/live-class/ParticipantsPanel.vue'

export default {
  name: 'LiveClassRoom',
  components: {
    WhiteBoard,
    LiveClassToolbar,
    ClassroomToolbar,
    LiveClassChat,
    ParticipantsPanel
  },
  setup() {
    // 使用 composable
    const {
      lessonId,
      lessonInfo,
      loading,
      error,
      userRole,
      socket,
      connected,
      reconnecting,
      participants,
      onlineCount,
      classroomStatus,
      duration,
      formattedDuration,
      whiteboardReadonly,
      isScreenSharing,
      screenShareStream,
      discussionConversationId,
      classGroupConversationId,
      isTeacher,
      isStudent,
      isLive,
      isEnded,
      loadLessonInfo,
      exitClass,
      startClass,
      endClass,
      startAttendance,
      publishTask,
      startScreenShare,
      stopScreenShare,
      raiseHand
    } = useLiveClass()
    
    // ========== Refs ==========
    const whiteboardRef = ref(null)
    const chatRef = ref(null)
    const screenShareVideo = ref(null)
    
    // ========== State ==========
    const showParticipants = ref(false)
    
    // ========== Provide ==========
    provide('socket', socket)
    provide('lessonId', lessonId)
    provide('userRole', userRole)
    
    // ========== Handlers ==========
    const handleStartClass = async () => {
      try {
        await startClass()
      } catch (err) {
        alert('开始课堂失败：' + (err.message || '请重试'))
      }
    }
    
    const handleExit = async () => {
      if (isTeacher.value && isLive.value) {
        const confirmEnd = confirm('课堂正在进行中，是否结束课堂并退出？')
        if (confirmEnd) {
          try {
            await endClass()
          } catch (err) {
            console.error('End class failed:', err)
          }
        } else {
          return
        }
      }
      exitClass()
    }
    
    const handleScreenShare = async () => {
      if (isScreenSharing.value) {
        stopScreenShare()
      } else {
        try {
          await startScreenShare()
        } catch (err) {
          if (err.name !== 'NotAllowedError') {
            alert('屏幕共享失败：' + err.message)
          }
        }
      }
    }
    
    const handleStartAttendance = () => {
      console.log('Start attendance')
    }
    
    const handlePublishTask = () => {
      console.log('Publish task')
    }
    
    const handleStartQuiz = () => {
      console.log('Start quiz')
    }
    
    const handleShareBoard = () => {
      if (whiteboardRef.value) {
        const dataUrl = whiteboardRef.value.toDataURL?.()
        console.log('Share board:', dataUrl)
      }
    }
    
    const handleRaiseHand = (raised) => {
      raiseHand(raised)
    }
    
    const handleAllowSpeak = (student) => {
      socket.value?.emit('classroom:allow_speak', {
        lesson_id: lessonId.value,
        student_id: student.id,
        allow: !student.can_speak
      })
    }
    
    const handleFocusStudent = (student) => {
      console.log('Focus student:', student)
    }
    
    const handleAnswerStudent = (student) => {
      socket.value?.emit('classroom:answer_hand', {
        lesson_id: lessonId.value,
        student_id: student.id
      })
    }
    
    const handleDismissHand = (student) => {
      socket.value?.emit('classroom:dismiss_hand', {
        lesson_id: lessonId.value,
        student_id: student.id
      })
    }
    
    const handleChatCollapse = (collapsed) => {
      console.log('Chat collapsed:', collapsed)
    }
    
    // 监听屏幕共享流
    watch(screenShareStream, (stream) => {
      if (screenShareVideo.value && stream) {
        screenShareVideo.value.srcObject = stream
      }
    })
    
    return {
      // Refs
      whiteboardRef,
      chatRef,
      screenShareVideo,
      
      // Composable state
      lessonId,
      lessonInfo,
      loading,
      error,
      userRole,
      socket,
      connected,
      reconnecting,
      participants,
      onlineCount,
      classroomStatus,
      duration,
      formattedDuration,
      whiteboardReadonly,
      isScreenSharing,
      discussionConversationId,
      classGroupConversationId,
      isTeacher,
      isStudent,
      isLive,
      isEnded,
      
      // Local state
      showParticipants,
      
      // Methods
      loadLessonInfo,
      exitClass,
      handleStartClass,
      handleExit,
      handleScreenShare,
      handleStartAttendance,
      handlePublishTask,
      handleStartQuiz,
      handleShareBoard,
      handleRaiseHand,
      handleAllowSpeak,
      handleFocusStudent,
      handleAnswerStudent,
      handleDismissHand,
      handleChatCollapse
    }
  }
}
</script>

<style scoped>
.live-class-room {
  position: fixed;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

/* 加载状态 */
.loading-overlay,
.error-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fff;
  z-index: 1000;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f0f0f0;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay p {
  margin-top: 16px;
  color: #666;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-overlay h3 {
  margin: 0 0 8px;
  color: #333;
}

.error-overlay p {
  margin: 0 0 24px;
  color: #666;
}

.retry-btn,
.back-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: #fff;
  margin-right: 12px;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.back-btn {
  background: #f0f0f0;
  color: #666;
}

.back-btn:hover {
  background: #e0e0e0;
}

/* 主内容 */
.main-content {
  flex: 1;
  display: flex;  position: relative;  min-height: 0;
  padding: 12px;
  gap: 12px;
}

/* 画板容器 */
.whiteboard-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  min-height: 400px;
}

/* 屏幕共享视图 */
.screen-share-view {
  position: absolute;
  inset: 0;
  background: #000;
  z-index: 5;
}

.screen-share-view video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 学生操作区 */
.student-actions {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
}

.raise-hand-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #fff;
  border: 2px solid #ddd;
  border-radius: 24px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.raise-hand-btn:hover {
  border-color: #ffc107;
  background: #fffbeb;
}

.raise-hand-btn.active {
  background: #ffc107;
  border-color: #ffc107;
  color: #fff;
}

.raise-hand-btn.active .hand-emoji {
  animation: wave 1s infinite;
}

@keyframes wave {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(20deg); }
  75% { transform: rotate(-20deg); }
}

.hand-emoji {
  font-size: 20px;
}

/* 连接状态 */
.connection-status {
  position: fixed;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
}

.status-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #ff9800;
  color: #fff;
  border-radius: 20px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
}

.reconnect-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
