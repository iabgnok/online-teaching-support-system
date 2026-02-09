/**
 * useLiveClass composable
 * 线上课堂统一逻辑封装
 * 
 * 功能：
 * - Socket连接管理
 * - 课堂信息加载
 * - 参与者管理
 * - 画板状态同步
 * - 课堂事件处理
 */

import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { io } from 'socket.io-client'
import api from '../api'

export function useLiveClass(options = {}) {
  const route = useRoute()
  const router = useRouter()
  
  // ==================== 配置 ====================
  const {
    autoConnect = true,
    autoLoadLesson = true
  } = options
  
  // ==================== 响应式状态 ====================
  // 课程信息
  const lessonId = ref(route.params.lessonId || route.params.id || null)
  const lessonInfo = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  // 用户角色
  const userRole = ref(null)
  const userId = ref(parseInt(localStorage.getItem('user_id')))
  const userName = ref(localStorage.getItem('real_name') || localStorage.getItem('username') || '')
  
  // Socket连接
  const socket = ref(null)
  const connected = ref(false)
  const reconnecting = ref(false)
  
  // 参与者
  const participants = ref([])
  const onlineCount = computed(() => participants.value.filter(p => p.online).length)
  
  // 课堂状态
  const classroomStatus = ref('not_started') // not_started, in_progress, ended
  const startTime = ref(null)
  const duration = ref(0) // 秒
  let durationTimer = null
  
  // 画板状态
  const whiteboardData = ref(null)
  const whiteboardReadonly = ref(true)
  
  // 屏幕共享
  const isScreenSharing = ref(false)
  const screenShareStream = ref(null)
  
  // 对话ID
  const discussionConversationId = ref(null)
  const classGroupConversationId = ref(null)
  
  // ==================== 计算属性 ====================
  const isTeacher = computed(() => userRole.value === 'teacher')
  const isStudent = computed(() => userRole.value === 'student')
  const isLive = computed(() => classroomStatus.value === 'in_progress')
  const isEnded = computed(() => classroomStatus.value === 'ended')
  
  const formattedDuration = computed(() => {
    const hours = Math.floor(duration.value / 3600)
    const minutes = Math.floor((duration.value % 3600) / 60)
    const seconds = duration.value % 60
    
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
    }
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  })
  
  // ==================== 方法 ====================
  
  // 加载课程信息
  const loadLessonInfo = async () => {
    if (!lessonId.value) {
      error.value = '课程ID无效'
      return
    }
    
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get(`/live-class/${lessonId.value}/join`)
      const data = response.data
      
      // 解析后端返回的数据
      lessonInfo.value = {
        id: data.live_class_id,
        lesson_id: lessonId.value,
        title: data.title,
        class_id: data.class_id,
        teacher_name: data.teacher_name,
        participants_count: data.participants_count
      }
      
      // 使用后端返回的用户角色（如果有的话）
      userRole.value = data.user_role || localStorage.getItem('role') || 'student'
      
      // 课堂状态：如果能加入就是活跃的
      classroomStatus.value = 'in_progress'
      discussionConversationId.value = data.conversation_id
      classGroupConversationId.value = data.class_group_conversation_id
      
      // 设置开始时间
      if (data.start_time) {
        startTime.value = new Date(data.start_time)
        startDurationTimer()
      }
      
      // 画板只读状态（学生只读，教师可编辑）
      whiteboardReadonly.value = userRole.value !== 'teacher'
      
      // 加载参与者列表
      if (data.participants) {
        participants.value = data.participants
      }
      
    } catch (err) {
      console.error('Failed to load lesson info:', err)
      error.value = err.response?.data?.message || '加载课程信息失败'
    } finally {
      loading.value = false
    }
  }
  
  // 连接Socket
  const connectSocket = () => {
    if (socket.value?.connected) return
    
    const token = localStorage.getItem('access_token')
    const socketUrl = import.meta.env.VITE_SOCKET_URL || window.location.origin
    
    socket.value = io(socketUrl, {
      auth: { token },
      query: {
        lesson_id: lessonId.value,
        user_id: userId.value,
        role: userRole.value
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    })
    
    setupSocketListeners()
  }
  
  // 设置Socket监听器
  const setupSocketListeners = () => {
    if (!socket.value) return
    
    // 连接事件
    socket.value.on('connect', () => {
      console.log('Socket connected')
      connected.value = true
      reconnecting.value = false
      
      // 加入课堂房间
      socket.value.emit('classroom:join', {
        lesson_id: lessonId.value,
        user_id: userId.value,
        user_name: userName.value,
        role: userRole.value
      })
    })
    
    socket.value.on('disconnect', () => {
      console.log('Socket disconnected')
      connected.value = false
    })
    
    socket.value.on('reconnecting', () => {
      console.log('Socket reconnecting...')
      reconnecting.value = true
    })
    
    socket.value.on('reconnect_failed', () => {
      console.error('Socket reconnection failed')
      reconnecting.value = false
      error.value = '连接失败，请刷新页面重试'
    })
    
    // 课堂事件
    socket.value.on('classroom:started', (data) => {
      classroomStatus.value = 'in_progress'
      startTime.value = new Date(data.start_time || Date.now())
      startDurationTimer()
    })
    
    socket.value.on('classroom:ended', () => {
      classroomStatus.value = 'ended'
      stopDurationTimer()
    })
    
    // 参与者事件
    socket.value.on('classroom:participant_joined', (participant) => {
      const index = participants.value.findIndex(p => p.id === participant.id)
      if (index > -1) {
        participants.value[index] = { ...participants.value[index], ...participant, online: true }
      } else {
        participants.value.push({ ...participant, online: true })
      }
    })
    
    socket.value.on('classroom:participant_left', (data) => {
      const index = participants.value.findIndex(p => p.id === data.user_id)
      if (index > -1) {
        participants.value[index].online = false
      }
    })
    
    socket.value.on('classroom:participant_count', ({ count }) => {
      // 更新在线人数
    })
    
    // 画板同步事件
    socket.value.on('whiteboard:draw', (data) => {
      // 由WhiteBoard组件直接处理
    })
    
    socket.value.on('whiteboard:sync', (data) => {
      whiteboardData.value = data
    })
    
    socket.value.on('whiteboard:clear', () => {
      whiteboardData.value = null
    })
    
    // 举手事件
    socket.value.on('classroom:hand_raised', (data) => {
      const index = participants.value.findIndex(p => p.id === data.user_id)
      if (index > -1) {
        participants.value[index].hand_raised = true
        participants.value[index].hand_raised_at = data.time
      }
    })
    
    socket.value.on('classroom:hand_lowered', (data) => {
      const index = participants.value.findIndex(p => p.id === data.user_id)
      if (index > -1) {
        participants.value[index].hand_raised = false
      }
    })
    
    // 屏幕共享事件
    socket.value.on('classroom:screen_share_started', (data) => {
      isScreenSharing.value = true
    })
    
    socket.value.on('classroom:screen_share_stopped', () => {
      isScreenSharing.value = false
    })
  }
  
  // 断开Socket
  const disconnectSocket = () => {
    if (socket.value) {
      socket.value.emit('classroom:leave', {
        lesson_id: lessonId.value,
        user_id: userId.value
      })
      socket.value.disconnect()
      socket.value = null
    }
    connected.value = false
  }
  
  // 计时器
  const startDurationTimer = () => {
    if (durationTimer) return
    
    const updateDuration = () => {
      if (startTime.value) {
        duration.value = Math.floor((Date.now() - startTime.value.getTime()) / 1000)
      }
    }
    
    updateDuration()
    durationTimer = setInterval(updateDuration, 1000)
  }
  
  const stopDurationTimer = () => {
    if (durationTimer) {
      clearInterval(durationTimer)
      durationTimer = null
    }
  }
  
  // ==================== 课堂控制方法（教师） ====================
  
  // 开始课堂
  const startClass = async () => {
    if (!isTeacher.value) return
    
    try {
      await api.post(`/live-class/${lessonId.value}/start`)
      socket.value?.emit('classroom:start', { lesson_id: lessonId.value })
      classroomStatus.value = 'in_progress'
      startTime.value = new Date()
      startDurationTimer()
    } catch (err) {
      console.error('Failed to start class:', err)
      throw err
    }
  }
  
  // 结束课堂
  const endClass = async () => {
    if (!isTeacher.value) return
    
    try {
      await api.post(`/live-class/${lessonId.value}/end`)
      socket.value?.emit('classroom:end', { lesson_id: lessonId.value })
      classroomStatus.value = 'ended'
      stopDurationTimer()
    } catch (err) {
      console.error('Failed to end class:', err)
      throw err
    }
  }
  
  // 发起签到
  const startAttendance = async (options = {}) => {
    if (!isTeacher.value) return
    
    try {
      const response = await api.post(`/live-class/${lessonId.value}/attendance`, options)
      socket.value?.emit('classroom:attendance_started', {
        lesson_id: lessonId.value,
        attendance: response.data
      })
      return response.data
    } catch (err) {
      console.error('Failed to start attendance:', err)
      throw err
    }
  }
  
  // 发布课堂任务
  const publishTask = async (taskData) => {
    if (!isTeacher.value) return
    
    try {
      const response = await api.post(`/live-class/${lessonId.value}/task`, taskData)
      socket.value?.emit('classroom:task_published', {
        lesson_id: lessonId.value,
        task: response.data
      })
      return response.data
    } catch (err) {
      console.error('Failed to publish task:', err)
      throw err
    }
  }
  
  // 开始屏幕共享
  const startScreenShare = async () => {
    if (!isTeacher.value) return
    
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true
      })
      
      screenShareStream.value = stream
      isScreenSharing.value = true
      
      // 通知其他参与者
      socket.value?.emit('classroom:screen_share_start', {
        lesson_id: lessonId.value
      })
      
      // 监听停止共享
      stream.getVideoTracks()[0].onended = () => {
        stopScreenShare()
      }
      
      return stream
    } catch (err) {
      console.error('Failed to start screen share:', err)
      throw err
    }
  }
  
  // 停止屏幕共享
  const stopScreenShare = () => {
    if (screenShareStream.value) {
      screenShareStream.value.getTracks().forEach(track => track.stop())
      screenShareStream.value = null
    }
    isScreenSharing.value = false
    
    socket.value?.emit('classroom:screen_share_stop', {
      lesson_id: lessonId.value
    })
  }
  
  // ==================== 学生方法 ====================
  
  // 举手
  const raiseHand = (raised = true) => {
    socket.value?.emit(raised ? 'classroom:raise_hand' : 'classroom:lower_hand', {
      lesson_id: lessonId.value,
      user_id: userId.value
    })
  }
  
  // 签到
  const checkIn = async (code) => {
    try {
      const response = await api.post(`/live-class/${lessonId.value}/checkin`, { code })
      return response.data
    } catch (err) {
      console.error('Failed to check in:', err)
      throw err
    }
  }
  
  // ==================== 导航方法 ====================
  
  // 退出课堂
  const exitClass = () => {
    disconnectSocket()
    router.back()
  }
  
  // ==================== 生命周期 ====================
  
  onMounted(async () => {
    if (autoLoadLesson && lessonId.value) {
      await loadLessonInfo()
    }
    
    if (autoConnect && lessonId.value) {
      connectSocket()
    }
  })
  
  onBeforeUnmount(() => {
    disconnectSocket()
    stopDurationTimer()
    stopScreenShare()
  })
  
  // 监听路由变化
  watch(() => route.params.lessonId, (newId) => {
    if (newId && newId !== lessonId.value) {
      lessonId.value = newId
      disconnectSocket()
      stopDurationTimer()
      loadLessonInfo().then(() => connectSocket())
    }
  })
  
  // ==================== 返回 ====================
  return {
    // 状态
    lessonId,
    lessonInfo,
    loading,
    error,
    userRole,
    userId,
    userName,
    socket,
    connected,
    reconnecting,
    participants,
    onlineCount,
    classroomStatus,
    startTime,
    duration,
    formattedDuration,
    whiteboardData,
    whiteboardReadonly,
    isScreenSharing,
    screenShareStream,
    discussionConversationId,
    classGroupConversationId,
    
    // 计算属性
    isTeacher,
    isStudent,
    isLive,
    isEnded,
    
    // 通用方法
    loadLessonInfo,
    connectSocket,
    disconnectSocket,
    exitClass,
    
    // 教师方法
    startClass,
    endClass,
    startAttendance,
    publishTask,
    startScreenShare,
    stopScreenShare,
    
    // 学生方法
    raiseHand,
    checkIn
  }
}

export default useLiveClass
