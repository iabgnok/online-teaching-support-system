<template>
  <div class="raise-hand-container">
    <!-- 学生端：举手按钮 -->
    <div v-if="isStudent" class="student-raise-hand">
      <el-button
        v-if="!hasRaised"
        type="warning"
        :icon="Pointer"
        @click="raiseHand"
        :loading="loading"
        size="large"
        round
      >
        举手提问
      </el-button>
      <el-button
        v-else
        type="info"
        :icon="Clock"
        disabled
        size="large"
        round
      >
        等待老师回应...
      </el-button>
    </div>

    <!-- 老师端：举手列表 -->
    <div v-if="isTeacher" class="teacher-raise-hands">
      <el-badge :value="pendingHands.length" :hidden="pendingHands.length === 0">
        <el-button @click="showHandsDialog = true" :icon="Notification">
          举手列表
        </el-button>
      </el-badge>
    </div>

    <!-- 举手列表对话框 -->
    <el-dialog
      v-model="showHandsDialog"
      title="学生举手列表"
      width="600px"
    >
      <div v-loading="loading" class="hands-list">
        <el-empty v-if="pendingHands.length === 0" description="暂无学生举手" />
        
        <div v-else>
          <div 
            v-for="hand in pendingHands" 
            :key="hand.id"
            class="hand-item"
          >
            <div class="hand-info">
              <div class="student-info">
                <el-avatar :size="40">{{ hand.student_name[0] }}</el-avatar>
                <div class="student-details">
                  <div class="student-name">{{ hand.student_name }}</div>
                  <div class="waiting-time">
                    <el-icon><Clock /></el-icon>
                    等待 {{ formatWaitingTime(hand.waiting_time) }}
                  </div>
                </div>
              </div>
              <div v-if="hand.question" class="question">
                <el-icon><QuestionFilled /></el-icon>
                <span>{{ hand.question }}</span>
              </div>
            </div>
            <div class="hand-actions">
              <el-button
                type="success"
                size="small"
                @click="handleHand(hand.id)"
                :loading="handlingId === hand.id"
              >
                已处理
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 举手对话框（学生） -->
    <el-dialog
      v-model="showRaiseDialog"
      title="举手提问"
      width="400px"
    >
      <el-form>
        <el-form-item label="问题（可选）">
          <el-input
            v-model="question"
            type="textarea"
            :rows="3"
            placeholder="简单描述您的问题..."
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showRaiseDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRaiseHand" :loading="loading">
          确认举手
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import api from '../../api'
import { Pointer, Clock, Notification, QuestionFilled } from '@element-plus/icons-vue'

export default {
  name: 'RaiseHandComponent',
  components: {
    Pointer,
    Clock,
    Notification,
    QuestionFilled
  },
  props: {
    liveClassId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      loading: false,
      hasRaised: false,
      pendingHands: [],
      showHandsDialog: false,
      showRaiseDialog: false,
      question: '',
      handlingId: null,
      pollTimer: null
    }
  },
  computed: {
    userRole() {
      return sessionStorage.getItem('user_role')
    },
    isStudent() {
      return this.userRole === 'student'
    },
    isTeacher() {
      return this.userRole === 'teacher' || this.userRole === 'admin'
    }
  },
  mounted() {
    if (this.isTeacher) {
      this.loadRaiseHands()
      this.pollTimer = setInterval(this.loadRaiseHands, 5000)
    }
  },
  beforeUnmount() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer)
    }
  },
  methods: {
    raiseHand() {
      this.showRaiseDialog = true
    },
    async submitRaiseHand() {
      this.loading = true
      try {
        const response = await api.post(`/chat/live/${this.liveClassId}/raise_hand`, {
          question: this.question
        })
        
        if (response.data.code === 200) {
          this.$message.success('举手成功！请等待老师回应')
          this.hasRaised = true
          this.showRaiseDialog = false
          this.question = ''
        } else {
          this.$message.warning(response.data.message)
        }
      } catch (error) {
        this.$message.error('举手失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    async loadRaiseHands() {
      if (!this.isTeacher) return
      
      try {
        const response = await api.get(`/chat/live/${this.liveClassId}/raise_hands`)
        if (response.data.code === 200) {
          this.pendingHands = response.data.data || []
          
          // 提示新的举手
          if (this.pendingHands.length > 0) {
            this.$emit('hands-update', this.pendingHands.length)
          }
        }
      } catch (error) {
        console.error('加载举手列表失败:', error)
      }
    },
    async handleHand(handId) {
      this.handlingId = handId
      try {
        const response = await api.post(
          `/chat/live/${this.liveClassId}/raise_hands/${handId}/handle`
        )
        
        if (response.data.code === 200) {
          this.$message.success('已处理')
          this.pendingHands = this.pendingHands.filter(h => h.id !== handId)
        }
      } catch (error) {
        this.$message.error('处理失败')
        console.error(error)
      } finally {
        this.handlingId = null
      }
    },
    formatWaitingTime(seconds) {
      if (seconds < 60) return `${seconds}秒`
      const minutes = Math.floor(seconds / 60)
      if (minutes < 60) return `${minutes}分钟`
      const hours = Math.floor(minutes / 60)
      return `${hours}小时${minutes % 60}分钟`
    }
  }
}
</script>

<style scoped>
.raise-hand-container {
  position: relative;
}

.student-raise-hand {
  display: flex;
  justify-content: center;
  padding: 12px;
}

.teacher-raise-hands {
  position: relative;
}

.hands-list {
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
}

.hand-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.hand-item:hover {
  background-color: #f5f7fa;
}

.hand-item:last-child {
  border-bottom: none;
}

.hand-info {
  flex: 1;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.student-details {
  flex: 1;
}

.student-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.waiting-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
}

.question {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  margin-top: 8px;
}

.hand-actions {
  margin-left: 16px;
}
</style>
