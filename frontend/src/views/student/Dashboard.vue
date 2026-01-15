<template>
  <div class="dashboard-container">
    <div class="welcome-banner mb-4">
      <h2>👋 欢迎回来，{{ user.name || '同学' }}</h2>
      <p class="text-secondary">{{ currentDate }}</p>
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
                                <span :class="{'text-danger font-bold': course.pending_count > 0}">{{ course.pending_count }}</span>
                             </div>
                             <div>
                                <el-tag v-if="course.final_grade !== null" type="success" size="small">{{ course.final_grade.toFixed(1) }}分</el-tag>
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
               <el-table :data="upcomingEvents" style="width: 100%" stripe>
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
               <li v-for="anno in announcements" :key="anno.id" class="border-b py-3 last:border-0">
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Clock, Location, Calendar } from '@element-plus/icons-vue'
import api from '../../api'

const router = useRouter()
const user = ref({ name: '' }) 
const currentDate = new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

const classes = ref([])
const announcements = ref([])
const upcomingEvents = ref([])
const stats = ref({ total_courses: 0, total_pending: 0, average_grade: 0, graded_count: 0 })

const loadingClasses = ref(true)
const loadingEvents = ref(true)

const fetchClasses = async () => {
    try {
        const res = await api.get('/classes/my')
        classes.value = res.data
    } catch(e) { console.error(e)}
    finally { loadingClasses.value = false }
}

const fetchStats = async () => {
    try {
        const res = await api.get('/classes/student/stats')
        stats.value = res.data
    } catch(e) {}
}

const fetchAnnouncements = async () => {
   try {
       const res = await api.get('/announcements?scope=global')
       announcements.value = res.data
   } catch(e) {}
}

const fetchEvents = async () => {
    try {
        const res = await api.get('/schedule/events')
        const now = new Date()
        const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
        
        upcomingEvents.value = res.data.filter(e => {
            const t = new Date(e.start)
            return t >= now && t <= nextWeek
        }).slice(0, 5)
    } catch(e) {}
    finally { loadingEvents.value = false }
}

const fetchMe = async () => {
    // In a real app, this should be in Pinia store
}

const goToCourse = (id) => {
    router.push(`/course/${id}`)
}

const formatTime = (iso) => new Date(iso).toLocaleString('zh-CN', { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})
const formatDateShort = (iso) => new Date(iso).toLocaleDateString('zh-CN', { month:'numeric', day:'numeric' })

onMounted(() => {
    fetchClasses()
    fetchStats()
    fetchAnnouncements()
    fetchEvents()
    fetchMe()
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
</style>