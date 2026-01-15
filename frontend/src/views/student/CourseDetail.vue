<template>
  <div class="course-detail-page">
    <!-- Course Info Header -->
    <el-card shadow="never" class="mb-4" v-if="courseInfo">
        <template #header>
            <div class="flex justify-between items-center">
                <span class="text-lg font-bold">{{ courseInfo.course_name }}</span>
                <el-tag type="info">{{ courseInfo.class_name }}</el-tag>
            </div>
        </template>
        <el-descriptions border :column="3">
            <el-descriptions-item label="任课教师">{{ courseInfo.teacher_name }}</el-descriptions-item>
            <el-descriptions-item label="学期">{{ courseInfo.semester }}</el-descriptions-item>
            <el-descriptions-item label="学分">{{ courseInfo.credit || '-' }}</el-descriptions-item>
            <el-descriptions-item label="教室">
                <el-icon><Location /></el-icon> {{ courseInfo.classroom || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="上课时间">
                <el-icon><Clock /></el-icon> {{ courseInfo.time || '-' }}
            </el-descriptions-item>
        </el-descriptions>
    </el-card>

    <el-tabs v-model="activeTab" class="course-tabs" v-loading="loading">
       <el-tab-pane label="课程资料" name="materials">
           <el-table :data="materials" style="width: 100%" stripe>
               <el-table-column width="50" align="center">
                   <template #default><el-icon><Document /></el-icon></template>
               </el-table-column>
               <el-table-column prop="title" label="文件名称" />
               <el-table-column prop="file_size" label="大小" width="120">
                    <template #default="scope">
                        {{ formatSize(scope.row.file_size) }}
                    </template>
               </el-table-column>
               <el-table-column prop="publish_time" label="发布日期" width="150">
                   <template #default="scope">{{ formatDate(scope.row.publish_time) }}</template>
               </el-table-column>
               <el-table-column label="操作" width="100" align="center">
                   <template #default="scope">
                       <el-link type="primary" :href="scope.row.url" target="_blank" :underline="false">
                           <el-button link type="primary">下载</el-button>
                       </el-link>
                   </template>
               </el-table-column>
           </el-table>
           <div v-if="materials.length === 0" class="empty-text">暂无资料</div>
       </el-tab-pane>

       <el-tab-pane label="作业与考试" name="assignments">
            <el-table :data="assignments" style="width: 100%" stripe>
               <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip/>
               <el-table-column prop="type" label="类型" width="80" align="center">
                   <template #default="scope">
                       <el-tag :type="scope.row.type === 'exam' ? 'warning' : ''" size="small">
                            {{ scope.row.type === 'exam' ? '考试' : '作业' }}
                       </el-tag>
                   </template>
               </el-table-column>
               <el-table-column prop="deadline" label="截止时间" width="180">
                   <template #default="scope">
                       <span :class="{'text-danger': scope.row.is_overdue}">{{ formatTime(scope.row.deadline) }}</span>
                   </template>
               </el-table-column>
               <el-table-column prop="score" label="总分" width="80" align="center" />
               <el-table-column label="状态" width="120" align="center">
                    <template #default="scope">
                        <div v-if="scope.row.submission_status === 'graded'">
                            <el-tag type="success">已批改: {{ scope.row.my_score }}</el-tag>
                        </div>
                        <div v-else-if="scope.row.submission_status === 'submitted'">
                            <el-tag>已提交</el-tag>
                        </div>
                        <div v-else>
                            <el-tag type="info" v-if="!scope.row.is_overdue">未提交</el-tag>
                            <el-tag type="danger" v-else>逾期</el-tag>
                        </div>
                    </template>
               </el-table-column>
               <el-table-column label="操作" width="120" align="center">
                   <template #default="scope">
                       <el-button 
                           v-if="!scope.row.is_overdue || scope.row.submission_status === 'submitted'" 
                           size="small" 
                           type="primary"
                           plain
                           @click="viewAssignment(scope.row.id)"
                       >
                           {{ scope.row.submission_status === 'unsubmitted' ? '去提交' : '详情' }}
                       </el-button>
                   </template>
               </el-table-column>
           </el-table>
           <div v-if="assignments.length === 0" class="empty-text">暂无作业</div>
       </el-tab-pane>

       <el-tab-pane label="我的考勤" name="attendance">
           <el-table :data="attendanceRecords" style="width: 100%" stripe>
               <el-table-column prop="date" label="日期" sortable>
                   <template #default="scope">{{ formatDate(scope.row.date) }}</template>
               </el-table-column>
               <el-table-column prop="status" label="状态" align="center">
                   <template #default="scope">
                       <el-tag v-if="scope.row.status === 'present'" type="success">出勤</el-tag>
                       <el-tag v-else-if="scope.row.status === 'late'" type="warning">迟到</el-tag>
                       <el-tag v-else-if="scope.row.status === 'leave'" type="info">请假</el-tag>
                       <el-tag v-else type="danger">缺勤</el-tag>
                   </template>
               </el-table-column>
               <el-table-column prop="remarks" label="备注" />
           </el-table>
           <div v-if="attendanceRecords.length === 0" class="empty-text">暂无考勤记录</div>
       </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document, Location, Clock } from '@element-plus/icons-vue'
import api from '../../api'

const route = useRoute()
const router = useRouter()
const classId = route.params.id
const activeTab = ref('materials')

const courseInfo = ref(null)
const materials = ref([])
const assignments = ref([])
const attendanceRecords = ref([])
const loading = ref(true)

const fetchData = async () => {
    try {
        const resClass = await api.get('/classes/my')
        courseInfo.value = resClass.data.find(c => c.class_id == classId)

        const resMat = await api.get(`/classes/${classId}/materials`)
        materials.value = resMat.data

        const resAss = await api.get(`/classes/${classId}/assignments`)
        assignments.value = resAss.data

        const resAtt = await api.get(`/attendance/class/${classId}/me`)
        attendanceRecords.value = resAtt.data || []

    } catch(e) { console.error(e) }
    finally { loading.value = false }
}

const viewAssignment = (id) => {
    alert("作业详情页施工中 (ID: " + id + ")")
}

const formatTime = (iso) => new Date(iso).toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' })
const formatDate = (iso) => new Date(iso).toLocaleDateString('zh-CN')
const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

onMounted(() => {
    fetchData()
})
</script>

<style scoped>
.course-detail-page {
    padding: 20px;
}
.mb-4 { margin-bottom: 20px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.text-lg { font-size: 18px; }
.font-bold { font-weight: bold; }
.text-danger { color: #F56C6C; }
.empty-text {
    padding: 20px;
    text-align: center;
    color: #909399;
}
</style>