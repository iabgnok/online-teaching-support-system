<template>
  <div class="dashboard-container">
    <div class="welcome-banner mb-4">
      <h2>👋 欢迎回来，{{ user.real_name || user.name || '同学' }}</h2>
      <div v-if="user.role === 'student' && user.student_no" class="text-secondary mb-2">
          <el-tag size="small" effect="plain" class="mr-2">{{ user.dept_name }}</el-tag>
          <span class="mr-2 font-bold">{{ user.major }}</span>
          <span class="mr-2">{{ user.class_name }}</span>
          <span>{{ user.student_no }}</span>
      </div>
      <p class="text-secondary text-sm">{{ currentDate }}</p>
    </div>

    <!-- Stats Row -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="8">
        <el-card shadow="hover">
           <div class="statistic-item">
             <div class="stat-value">{{ stats.total_courses }}</div>
             <div class="stat-label">📚 选修课程</div>
           </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
           <div class="statistic-item">
             <div class="stat-value text-danger">{{ stats.total_pending }}</div>
             <div class="stat-label">📝 待提交作业</div>
           </div>
        </el-card>
      </el-col>
      <el-col :span="8">
         <el-card shadow="hover">
           <div class="statistic-item">
             <div class="stat-value text-success">{{ stats.average_grade || '-' }}</div>
             <div class="stat-label">📊 平均成绩 ({{ stats.graded_count }}门)</div>
           </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- Left Column: My Courses -->
      <el-col :span="16">
        <el-card class="box-card mb-4" header="📚 我的课程">
             <div v-if="loadingClasses">
                <el-skeleton :rows="3" animated />
             </div>
             
             <div v-else>
               <el-row :gutter="20">
                 <el-col :span="12" v-for="course in classes" :key="course.class_id" class="mb-3">
                    <el-card shadow="hover" :body-style="{ padding: '15px' }" class="cursor-pointer" @click="goToCourse(course.class_id)">
                        <div class="course-header mb-2">
                            <h4 class="m-0 text-truncate">{{ course.course_name }}</h4>
                            <small class="text-secondary">{{ course.class_name }}</small>
                        </div>
                        <div class="course-info text-secondary text-sm mb-3">
                            <div class="mb-1"><el-icon><User /></el-icon> {{ course.teacher_name }}</div>
                            <div class="mb-1" v-if="course.classroom"><el-icon><Location /></el-icon> {{ course.classroom }}</div>
                        </div>
                        <div class="course-footer flex justify-between items-center text-sm border-t pt-2 mt-2">
                             <div>
                                <span class="text-secondary">待提交: </span>
                                <span :class="{'text-danger font-bold': course.pending_count > 0}">{{ course.pending_count || 0 }}</span>
                             </div>
                             <div>
                                <el-tag v-if="course.final_grade !== null && course.final_grade !== undefined" type="success" size="small">{{ Number(course.final_grade).toFixed(1) }}分</el-tag>
                                <span v-else class="text-secondary">-</span>
                             </div>
                        </div>
                    </el-card>
                 </el-col>
               </el-row>

               <div v-if="classes.length === 0" class="empty-text text-center text-secondary p-4">
                 暂无课程，请联系教务选课
               </div>
             </div>
        </el-card>

        <el-card class="box-card" header="近期任务 (Upcoming)">
            <div v-if="loadingEvents">
                <el-skeleton :rows="2" animated />
            </div>
            <div v-else>
               <el-table :data="upcomingEvents" style="width: 100%" stripe @row-click="handleEventClick">
                  <el-table-column prop="title" label="任务名称" min-width="200" show-overflow-tooltip />
                  <el-table-column prop="end" label="截止时间" width="160">
                      <template #default="scope">
                          {{ formatTime(scope.row.start) }}
                      </template>
                  </el-table-column>
                  <el-table-column prop="type" label="类型" width="80" align="center">
                      <template #default="scope">
                          <el-tag :type="scope.row.extendedProps.type === 'exam' ? 'warning' : 'danger'" size="small">
                              {{ scope.row.extendedProps.type === 'exam' ? '考试' : '作业' }}
                          </el-tag>
                      </template>
                  </el-table-column>
                   <el-table-column label="状态" width="100" align="center">
                       <template #default="scope">
                           <el-tag :type="getEventStatus(scope.row).type" size="small">
                               {{ getEventStatus(scope.row).text }}
                           </el-tag>
                       </template>
                   </el-table-column>
               </el-table>
               <div v-if="upcomingEvents.length === 0" class="text-center text-secondary p-4">
                   🎉 未来一周没有即将截止的任务
               </div>
            </div>
        </el-card>
      </el-col>

      <!-- Right Column: Announcements -->
      <el-col :span="8">
        <el-card class="box-card" header="📢 系统公告">
             <div v-if="announcements.length === 0" class="text-center text-secondary p-4">暂无公告</div>
             <ul v-else class="list-none p-0 m-0">
               <li v-for="anno in announcements" :key="anno.id" class="border-b py-3 last:border-0 cursor-pointer hover:bg-gray-50 transition-colors" @click="showAnnouncementDetail(anno.id)">
                  <div class="mb-1">
                      <span class="font-medium">{{ anno.title }}</span>
                  </div>
                  <div class="flex justify-between items-center text-xs text-secondary">
                      <p class="m-0 truncate w-2/3">{{ anno.content }}</p>
                      <span>{{ formatDateShort(anno.created_at) }}</span>
                  </div>
               </li>
             </ul>
        </el-card>
      </el-col>
    </el-row>

    <!-- 公告详情对话框 -->
    <el-dialog v-model="announcementDialogVisible" title="公告详情" width="600px" :close-on-click-modal="false">
      <div v-if="currentAnnouncement" class="announcement-detail">
        <h3 class="announcement-title">{{ currentAnnouncement.title }}</h3>
        <div class="announcement-meta text-secondary text-sm mb-4">
          <span>发布时间: {{ formatDateShort(currentAnnouncement.created_at) }}</span>
          <span class="ml-4">发布者: {{ currentAnnouncement.author_name }}</span>
          <span v-if="currentAnnouncement.target_class_name" class="ml-4">班级: {{ currentAnnouncement.target_class_name }}</span>
        </div>
        <div class="announcement-content" v-html="formatContent(currentAnnouncement.content)"></div>
      </div>
      <div v-else class="text-center p-4">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
      <template #footer>
        <el-button @click="announcementDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Location, User, Loading } from '@element-plus/icons-vue'
import api from '../../api'

const router = useRouter()
const user = ref({})
const currentDate = ref(new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }))

const classes = ref([])
const announcements = ref([])
const upcomingEvents = ref([])
const stats = ref({ 
  total_courses: 0, 
  total_pending: 0, 
  average_grade: 0, 
  graded_count: 0 
})

const loadingClasses = ref(true)
const loadingEvents = ref(true)

// 公告详情相关
const announcementDialogVisible = ref(false)
const currentAnnouncement = ref(null)

const fetchClasses = async () => {
    console.log('Fetching classes...')
    try {
        const res = await api.get('/classes/my')
        console.log('Classes fetched:', res.data)
        classes.value = res.data || []
    } catch(e) { 
        console.error('Fetch classes error:', e)
        classes.value = [] // 确保为空数组，避免v-for报错
    }
    finally { 
        loadingClasses.value = false 
        console.log('loadingClasses set to false')
    }
}

const fetchStats = async () => {
    try {
        const res = await api.get('/classes/student/stats')
        stats.value = res.data || { 
          total_courses: 0, 
          total_pending: 0, 
          average_grade: 0, 
          graded_count: 0 
        }
    } catch(e) {
        stats.value = { 
          total_courses: 0, 
          total_pending: 0, 
          average_grade: 0, 
          graded_count: 0 
        }
    }
}

const fetchAnnouncements = async () => {
   try {
       const res = await api.get('/announcements')
       announcements.value = res.data
   } catch(e) {}
}

const fetchEvents = async () => {
    console.log('Fetching events...')
    try {
        const res = await api.get('/schedule/events')
        console.log('Events fetched:', res.data)
        const now = new Date()
        
        // 使用Map去重，避免重复显示相同的任务
        const uniqueEvents = new Map()
        
        ;(res.data || []).forEach(e => {
            const assignmentId = e.extendedProps?.assignment_id
            if (assignmentId && !uniqueEvents.has(assignmentId)) {
                uniqueEvents.set(assignmentId, {
                    ...e,
                    end: e.end || e.start // 确保有截止时间
                })
            }
        })
        
        upcomingEvents.value = Array.from(uniqueEvents.values())
            .filter(e => {
                const t = new Date(e.end)
                const isNotSubmitted = !e.extendedProps?.submitted && 
                                      e.extendedProps?.submission_status !== 'submitted' && 
                                      e.extendedProps?.submission_status !== 'graded'
                return t >= now && isNotSubmitted // 只显示未来且未提交的任务
            })
            .sort((a, b) => new Date(a.end) - new Date(b.end))
            .slice(0, 5)
    } catch(e) {
        console.error('Fetch events error:', e)
        upcomingEvents.value = []
    }
    finally { 
        loadingEvents.value = false 
        console.log('loadingEvents set to false')
    }
}

const fetchMe = async () => {
    try {
        const res = await api.get('/me')
        user.value = res.data
    } catch(e) {}
}

const formatTime = (timeStr) => {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const formatDateShort = (timeStr) => {
    if (!timeStr) return ''
    const date = new Date(timeStr)
    return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

const goToCourse = (classId) => {
    console.log('Navigating to course:', classId)
    if (!classId) {
        ElMessage.warning('课程ID无效')
        return
    }
    router.push(`/course/${classId}`)
}

const handleEventClick = (row) => {
  if (row.extendedProps && row.extendedProps.assignment_id) {
    router.push(`/student/assignment/${row.extendedProps.assignment_id}`)
  }
}

const getEventStatus = (event) => {
  // 优先检查批改状态
  if (event.extendedProps?.graded || event.extendedProps?.submission_status === 'graded') {
    return { type: 'success', text: '已批改' }
  }
  // 检查提交状态
  if (event.extendedProps?.submitted || event.extendedProps?.submission_status === 'submitted') {
    return { type: 'info', text: '已提交' }
  }
  // 检查截止时间
  const now = new Date()
  const endDate = event.end ? new Date(event.end) : null
  if (endDate && now > endDate) {
    return { type: 'danger', text: '已截止' }
  }
  return { type: 'warning', text: '待提交' }
}

// 公告详情相关方法
const showAnnouncementDetail = async (announcementId) => {
  try {
    announcementDialogVisible.value = true
    currentAnnouncement.value = null
    
    const response = await api.get(`/announcements/${announcementId}`)
    currentAnnouncement.value = response.data
  } catch (error) {
    console.error('Failed to load announcement detail:', error)
    ElMessage.error('加载公告详情失败')
    announcementDialogVisible.value = false
  }
}

const formatContent = (content) => {
  if (!content) return ''
  // 将换行符转换为<br>，简单处理HTML
  return content.replace(/\n/g, '<br>')
}

onMounted(async () => {
  console.log('Dashboard mounted')
  currentDate.value = new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
  
  // 并行加载，避免阻塞
  Promise.allSettled([
      fetchClasses(),
      fetchStats(),
      fetchAnnouncements(),
      fetchEvents(),
      fetchMe()
  ]).then(() => {
      console.log('All fetches completed (settled)')
  })
})
</script>

<style scoped>
.dashboard-container {
    padding: 20px;
}
.statistic-item {
    text-align: center;
}
.stat-value {
    font-size: 24px;
    font-weight: bold;
    line-height: 1.5;
}
.stat-label {
    font-size: 13px;
    color: #909399;
}
/* Utilities */
.text-secondary { color: #909399; }
.text-danger { color: #F56C6C; }
.text-success { color: #67C23A; }
.mb-1 { margin-bottom: 4px; }
.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }
.m-0 { margin: 0; }
.p-4 { padding: 16px; }
.border-b { border-bottom: 1px solid #ebeef5; }
.border-t { border-top: 1px solid #ebeef5; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.cursor-pointer { cursor: pointer; }
.text-sm { font-size: 13px; }
.text-xs { font-size: 12px; }
.font-medium { font-weight: 500; }
.font-bold { font-weight: bold; }
.text-truncate, .truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.w-2\/3 { width: 66.66%; }
.list-none { list-style: none; padding: 0; margin: 0; }
.py-3 { padding-top: 12px; padding-bottom: 12px; }
.pt-2 { padding-top: 8px; }
.mt-2 { margin-top: 8px; }
.ml-4 { margin-left: 16px; }
.transition-colors { transition: background-color 0.2s; }
.hover\:bg-gray-50:hover { background-color: #f9fafb; }

/* 公告详情样式 */
.announcement-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.announcement-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.announcement-meta {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
}

.announcement-content {
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
}
</style>