<template>
  <div class="admin-dashboard">
    <!-- 头部欢迎区 -->
    <el-card class="welcome-card" shadow="hover">
      <div class="welcome-content">
        <div class="welcome-text">
          <h2>🛡️ 管理员控制台</h2>
          <p>欢迎回来，{{ currentUser?.real_name }}</p>
          <p class="time">{{ currentTime }}</p>
        </div>
        <div class="quick-actions">
          <el-button type="primary" icon="Plus" @click="$router.push('/admin/users')">
            用户管理
          </el-button>
          <el-button type="success" icon="Upload" @click="showImportDialog = true">
            批量导入
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 主要功能区 -->
    <el-row :gutter="20" class="main-section">
      <el-col :span="8">
        <el-card shadow="hover" class="function-card" @click="$router.push('/admin/users')">
          <div class="card-icon">👥</div>
          <h3>用户管理</h3>
          <p>管理所有学生、教师和管理员账户</p>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover" class="function-card" @click="$router.push('/admin/query')">
          <div class="card-icon">📊</div>
          <h3>数据查询</h3>
          <p>查询和统计系统中的各类数据</p>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover" class="function-card" @click="showImportDialog = true">
          <div class="card-icon">📄</div>
          <h3>批量导入</h3>
          <p>导入用户、院系、课程等数据</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 权限和论坛管理 -->
    <el-row :gutter="20" class="main-section">
      <el-col :span="8">
        <el-card shadow="hover" class="function-card" @click="$router.push('/admin/permissions')">
          <div class="card-icon">🔑</div>
          <h3>权限管理</h3>
          <p>管理系统管理员的权限设置</p>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="hover" class="function-card" @click="$router.push('/admin/forum-management')">
          <div class="card-icon">💬</div>
          <h3>论坛管理</h3>
          <p>管理系统论坛的帖子和评论</p>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统公告区 -->
    <el-row :gutter="20" class="main-section">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>📢 系统公告</span>
              <el-button text type="primary" @click="showAnnouncementDialog = true">
                发布公告
              </el-button>
            </div>
          </template>
          
          <div v-if="stats.announcements && stats.announcements.length > 0" class="announcements-list">
            <div v-for="announcement in stats.announcements.slice(0, 5)" :key="announcement.id" class="announcement-item">
              <h4>{{ announcement.title }}</h4>
              <p>{{ announcement.content }}</p>
              <span class="announcement-time">{{ formatDate(announcement.created_at) }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无系统公告" :image-size="100" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据导入对话框 -->
    <el-dialog v-model="showImportDialog" title="批量数据导入" width="600px">
      <el-tabs v-model="importTab">
        <el-tab-pane label="用户" name="users">
          <el-upload
            drag
            action="/api/v1/admin/import/users"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
            accept=".csv"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽CSV文件到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                CSV格式：username, password, real_name, role, phone, email, 
                admin_no/teacher_no/student_no, department, major/title
              </div>
            </template>
          </el-upload>
        </el-tab-pane>

        <el-tab-pane label="院系" name="departments">
          <el-upload
            drag
            action="/api/v1/admin/import/departments"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
            accept=".csv"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽CSV文件到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">CSV格式：dept_name</div>
            </template>
          </el-upload>
        </el-tab-pane>

        <el-tab-pane label="课程" name="courses">
          <el-upload
            drag
            action="/api/v1/admin/import/courses"
            :on-success="handleImportSuccess"
            :on-error="handleImportError"
            accept=".csv"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽CSV文件到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                CSV格式：course_code, course_name, credits, description
              </div>
            </template>
          </el-upload>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 发布公告对话框 -->
    <el-dialog v-model="showAnnouncementDialog" title="发布系统公告" width="600px">
      <el-form :model="announcementForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="announcementForm.title" placeholder="请输入公告标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="announcementForm.content"
            type="textarea"
            :rows="6"
            placeholder="请输入公告内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAnnouncementDialog = false">取消</el-button>
        <el-button type="primary" @click="publishAnnouncement" :loading="publishing">
          发布
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Reading, Document, Clock, Plus, Upload, UploadFilled } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const currentUser = ref(null)
const currentTime = ref('')
const stats = ref({
  users: {},
  courses: {},
  activities: {},
  announcements: [],
  user_stats_by_dept: []
})

const showImportDialog = ref(false)
const importTab = ref('users')
const showAnnouncementDialog = ref(false)
const importing = ref(false)
const publishing = ref(false)
const announcementForm = ref({ title: '', content: '' })

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', { 
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const handleImportSuccess = (response) => {
  ElMessage.success(response.message || '导入成功')
  showImportDialog.value = false
}

// 导入失败处理
const handleImportError = (error) => {
  console.error('Import error:', error)
  ElMessage.error('导入失败，请检查文件格式')
}

// 加载公告列表
const loadAnnouncements = async () => {
  try {
    const response = await api.get('/announcements')
    stats.value.announcements = response.data || []
  } catch (error) {
    console.error('Failed to load announcements:', error)
  }
}

// 发布公告
const publishAnnouncement = async () => {
  if (!announcementForm.value.title || !announcementForm.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }

  publishing.value = true
  try {
    await api.post('/announcements', {
      ...announcementForm.value,
      scope_type: 'global'
    })
    ElMessage.success('公告发布成功')
    showAnnouncementDialog.value = false
    announcementForm.value = { title: '', content: '' }
    loadAnnouncements() // 重新加载公告列表
  } catch (error) {
    console.error('Failed to publish announcement:', error)
    ElMessage.error('发布失败')
  } finally {
    publishing.value = false
  }
}

onMounted(() => {
  currentUser.value = JSON.parse(localStorage.getItem('user') || '{}')
  updateTime()
  setInterval(updateTime, 60000) // 每分钟更新时间
  loadAnnouncements() // 初始化加载公告
})
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-text h2 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 24px;
}

.welcome-text p {
  margin: 5px 0;
  color: #606266;
}

.welcome-text .time {
  font-size: 14px;
  color: #909399;
}

.quick-actions {
  display: flex;
  gap: 10px;
}

.main-section {
  margin-top: 20px;
}

.function-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  padding: 30px 20px;
}

.function-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.card-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.function-card h3 {
  margin: 10px 0;
  font-size: 18px;
  color: #303133;
}

.function-card p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.user-stats-by-dept {
  margin-bottom: 15px;
}

.card-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #EBEEF5;
}

.announcements-list {
  max-height: 350px;
  overflow-y: auto;
}

.announcement-item {
  padding: 12px;
  border-bottom: 1px solid #EBEEF5;
  cursor: pointer;
  transition: background 0.3s;
}

.announcement-item:hover {
  background: #F5F7FA;
}

.announcement-item:last-child {
  border-bottom: none;
}

.announcement-title {
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.announcement-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  justify-content: space-between;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 10px;
}
</style>
