<template>
  <div class="dashboard-container">
    <div class="welcome-banner mb-4">
      <h2>👋 欢迎回来，{{ user.name || '老师' }}</h2>
      <p class="text-secondary">{{ currentDate }}</p>
    </div>

    <!-- Stats Row -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="8">
        <el-card shadow="hover">
           <div class="statistic-item">
             <div class="stat-value text-primary">{{ stats.active_courses }}</div>
             <div class="stat-label">📚 执教课程</div>
           </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
           <div class="statistic-item">
             <div class="stat-value text-danger">{{ stats.pending_grading }}</div>
             <div class="stat-label">📝 待批改作业</div>
           </div>
        </el-card>
      </el-col>
      <el-col :span="8">
         <el-card shadow="hover">
           <div class="statistic-item">
             <div class="stat-value text-success">{{ stats.total_students }}</div>
             <div class="stat-label">👥 学生总数</div>
           </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Teaching Classes -->
    <el-card class="box-card mb-4" header="🏫 我的教学班">
        <div v-if="loadingClasses">
            <el-skeleton :rows="3" animated />
        </div>
        <div v-else>
            <el-table :data="classes" style="width: 100%" stripe>
                <el-table-column prop="course_name" label="课程名称" min-width="150" />
                <el-table-column prop="class_name" label="班级名称" min-width="150" />
                <el-table-column prop="student_count" label="人数" width="80" align="center" />
                <el-table-column prop="pending_grading" label="待批改" width="100" align="center">
                    <template #default="scope">
                        <span :class="{'text-danger font-bold': scope.row.pending_grading > 0}">
                            {{ scope.row.pending_grading }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column label="上课时间/地点" min-width="200">
                     <template #default="scope">
                         <div class="text-xs text-secondary">
                             <div v-if="scope.row.time"><el-icon><Clock /></el-icon> {{ scope.row.time }}</div>
                             <div v-if="scope.row.classroom"><el-icon><Location /></el-icon> {{ scope.row.classroom }}</div>
                         </div>
                     </template>
                </el-table-column>
                <el-table-column label="操作" width="150" align="center">
                    <template #default="scope">
                        <el-button type="primary" size="small" plian @click="manageClass(scope.row.class_id)">进入管理</el-button>
                    </template>
                </el-table-column>
            </el-table>
             <div v-if="classes.length === 0" class="empty-text text-center text-secondary p-4">
                 暂无执教课程
               </div>
        </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Location } from '@element-plus/icons-vue'
import api from '../../api'

const router = useRouter()
const user = ref({ name: '' }) 
const currentDate = new Date().toLocaleDateString('zh-CN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
const stats = ref({ active_courses: 0, pending_grading: 0, total_students: 0 })
const classes = ref([])
const loadingClasses = ref(true)

const fetchStats = async () => {
    try {
        const res = await api.get('/classes/teacher/stats')
        stats.value = res.data
    } catch(e) {}
}

const fetchClasses = async () => {
    try {
        const res = await api.get('/classes/my')
        classes.value = res.data
    } catch(e) {}
    finally { loadingClasses.value = false }
}

const fetchMe = async () => {
   // user.value.name = '老师' // Mock or fetch from store
}

const manageClass = (id) => {
    router.push(`/teacher/class/${id}`)
}

onMounted(() => {
    fetchStats()
    fetchClasses()
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
.text-secondary { color: #909399; }
.text-danger { color: #F56C6C; }
.text-success { color: #67C23A; }
.text-primary { color: #409EFF; }
.mb-4 { margin-bottom: 20px; }
.font-bold { font-weight: bold; }
.text-xs { font-size: 12px; }
</style>