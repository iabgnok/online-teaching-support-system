<template>
  <div class="active-live-class">
    <div class="header">
      <h1>线上授课</h1>
      <p>选择要进入的课堂</p>
    </div>

    <div v-if="loading" class="loading">
      加载中...
    </div>

    <div v-else-if="activeClasses.length === 0" class="no-classes">
      <div class="empty-state">
        <h3>暂无活跃课堂</h3>
        <p>当前没有正在进行的线上授课</p>
        <button v-if="userRole === 'teacher'" @click="showStartClassDialog = true" class="btn-primary">
          开始新授课
        </button>
      </div>
    </div>

    <div v-else class="classes-list">
      <div class="class-card" v-for="classItem in activeClasses" :key="classItem.lesson_id" :class="{ 'ended': classItem.status === 'ended' }">
        <div class="class-info">
          <div class="title-row">
            <h3>{{ classItem.title }}</h3>
            <span v-if="classItem.status === 'ended'" class="status-badge ended">已结束</span>
            <span v-else class="status-badge active">进行中</span>
          </div>
          <p class="class-name">{{ classItem.class_name }}</p>
          <p class="teacher">教师: {{ classItem.teacher_name }}</p>
          <p class="time">开始时间: {{ formatTime(classItem.start_time) }}</p>
          <p class="participants">参与人数: {{ classItem.participants_count }}</p>
        </div>
        <div class="actions">
          <button v-if="classItem.status !== 'ended'" @click="joinClass(classItem.lesson_id, classItem.status)" class="btn-primary">
            进入课堂
          </button>
          <div v-else class="ended-text">课堂已结束</div>
        </div>
      </div>
    </div>

    <!-- 开始授课对话框 -->
    <div v-if="showStartClassDialog" class="modal-overlay" @click="showStartClassDialog = false">
      <div class="modal-content" @click.stop>
        <h3>开始线上授课</h3>
        <form @submit.prevent="startClass">
          <div class="form-group">
            <label>选择班级:</label>
            <select v-model="selectedClassId" required>
              <option value="">请选择班级</option>
              <option v-for="cls in myClasses" :key="cls.class_id" :value="cls.class_id">
                {{ cls.class_name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>授课标题:</label>
            <input v-model="classTitle" type="text" placeholder="例如：第1章 绪论" required>
          </div>
          <div class="form-actions">
            <button type="button" @click="showStartClassDialog = false">取消</button>
            <button type="submit" class="btn-primary" :disabled="starting">开始授课</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'ActiveLiveClass',
  data() {
    return {
      loading: true,
      activeClasses: [],
      userRole: sessionStorage.getItem('user_role'),
      showStartClassDialog: false,
      selectedClassId: '',
      classTitle: '',
      starting: false,
      myClasses: []
    }
  },
  mounted() {
    this.loadActiveClasses()
    if (this.userRole === 'teacher') {
      this.loadMyClasses()
    }
  },
  methods: {
    async loadActiveClasses() {
      try {
        const response = await api.get('/live-class/active')
        this.activeClasses = response.data
      } catch (error) {
        console.error('Failed to load active classes:', error)
        alert('加载活跃课堂失败')
      } finally {
        this.loading = false
      }
    },

    async loadMyClasses() {
      try {
        const response = await api.get('/classes/my-classes')
        this.myClasses = response.data
      } catch (error) {
        console.error('Failed to load my classes:', error)
      }
    },

    async joinClass(lessonId, status) {
      // 检查本地状态
      if (status === 'ended') {
        alert('课堂已结束，无法进入')
        return
      }
      
      // 调用API验证课堂状态
      try {
        const response = await api.get(`/live-class/${lessonId}/check`)
        if (response.data.status === 'ended') {
          alert('课堂已结束，无法进入')
          // 刷新课堂列表
          this.loadActiveClasses()
          return
        }
      } catch (error) {
        if (error.response?.status === 403) {
          alert(error.response.data.error || '课堂已结束')
          // 刷新课堂列表
          this.loadActiveClasses()
          return
        }
        console.error('检查课堂状态失败:', error)
      }
      
      // 跳转到课堂
      if (this.userRole === 'teacher') {
        this.$router.push(`/teacher/live-class/${lessonId}`)
      } else {
        this.$router.push(`/live-class/${lessonId}`)
      }
    },

    async startClass() {
      if (!this.selectedClassId || !this.classTitle.trim()) {
        alert('请填写完整信息')
        return
      }

      this.starting = true
      try {
        const response = await api.post('/live-class/start', {
          class_id: this.selectedClassId,
          title: this.classTitle.trim()
        })

        const lessonId = response.data.lesson_id
        this.showStartClassDialog = false
        this.$router.push(`/teacher/live-class/${lessonId}`)
      } catch (error) {
        console.error('Failed to start class:', error)
        alert('开始授课失败: ' + (error.response?.data?.error || '未知错误'))
      } finally {
        this.starting = false
      }
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleString()
    }
  }
}
</script>

<style scoped>
.active-live-class {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.header h1 {
  color: #333;
  margin-bottom: 0.5rem;
}

.header p {
  color: #666;
}

.loading {
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
}

.no-classes {
  text-align: center;
  padding: 3rem;
}

.empty-state h3 {
  color: #666;
  margin-bottom: 1rem;
}

.empty-state p {
  color: #999;
  margin-bottom: 2rem;
}

.btn-primary {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.classes-list {
  display: grid;
  gap: 1rem;
}

.class-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s;
}

.class-card.ended {
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  opacity: 0.8;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 0.5rem;
}

.class-info h3 {
  margin: 0;
  color: #333;
}

.class-card.ended .class-info h3 {
  color: #999;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
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

.class-info p {
  margin: 0.25rem 0;
  color: #666;
  font-size: 0.9rem;
}

.class-card.ended .class-info p {
  color: #999;
}

.actions {
  flex-shrink: 0;
}

.ended-text {
  padding: 0.75rem 1.5rem;
  color: #999;
  font-size: 1rem;
  font-weight: 500;
  text-align: center;
}

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
}

.modal-content h3 {
  margin-top: 0;
  color: #333;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.form-actions button {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.form-actions .btn-primary {
  background: #007bff;
  color: white;
  border-color: #007bff;
}
</style>