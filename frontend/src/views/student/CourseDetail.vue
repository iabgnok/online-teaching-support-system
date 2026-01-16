<template>
  <div class="course-detail-page">
    <el-page-header @back="goBack" content="课程详情" class="mb-4" />
    
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
           <el-alert v-if="attendanceRecords.length > 0" type="info" :closable="false" class="mb-3">
               今天日期: {{ new Date().toISOString().split('T')[0] }} | 
               可签到记录数: {{ attendanceRecords.filter(r => r.can_checkin).length }}
           </el-alert>
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
               <el-table-column label="操作" align="center" width="150">
                    <template #default="scope">
                        <el-button 
                            v-if="scope.row.can_checkin" 
                            type="primary" 
                            size="small" 
                            @click="handleCheckIn(scope.row.attendance_id)"
                        >
                            签到
                        </el-button>
                        <span v-else class="text-gray-400 text-xs">
                            {{ scope.row.status === 'present' ? '已签到' : (scope.row.date === new Date().toISOString().split('T')[0] ? '不可签' : '-') }}
                        </span>
                    </template>
               </el-table-column>
               <el-table-column prop="remarks" label="备注" />
           </el-table>
           <div v-if="attendanceRecords.length === 0" class="empty-text">暂无考勤记录</div>
       </el-tab-pane>

       <el-tab-pane label="统计分析" name="stats">
            <div v-if="assignmentStats" class="stats-container p-4">
                <!-- 作业和考试统计 -->
                <el-row :gutter="20" class="mb-4">
                    <el-col :span="12">
                        <el-card shadow="hover">
                            <template #header>
                                <div class="card-header font-bold">
                                    <span>📝 作业统计</span>
                                </div>
                            </template>
                            <div class="stats-content">
                                <el-row :gutter="16">
                                    <el-col :span="8">
                                        <div class="statistic-item">
                                            <div class="stat-value">{{ assignmentStats.homework.count }}</div>
                                            <div class="stat-label">总数</div>
                                        </div>
                                    </el-col>
                                    <el-col :span="8">
                                        <div class="statistic-item">
                                            <div class="stat-value text-success">{{ assignmentStats.homework.submitted }}</div>
                                            <div class="stat-label">已提交</div>
                                        </div>
                                    </el-col>
                                    <el-col :span="8">
                                        <div class="statistic-item">
                                            <div class="stat-value text-warning">{{ assignmentStats.homework.graded }}</div>
                                            <div class="stat-label">已批改</div>
                                        </div>
                                    </el-col>
                                </el-row>
                                
                                <el-divider style="margin: 16px 0;" />
                                
                                <div class="statistic-item mb-3">
                                    <div class="stat-value text-primary">
                                        {{ assignmentStats.homework.avgScore || '-' }}
                                        <span class="text-sm text-gray-500" v-if="assignmentStats.homework.graded > 0">分</span>
                                    </div>
                                    <div class="stat-label">平均分（已批改）</div>
                                </div>
                                
                                <div class="mb-2">
                                    <div class="stat-label mb-2">提交率</div>
                                    <el-progress 
                                        :percentage="assignmentStats.homework.rate" 
                                        :color="assignmentStats.homework.rate >= 90 ? '#67C23A' : assignmentStats.homework.rate >= 70 ? '#409EFF' : '#F56C6C'"
                                        :stroke-width="16"
                                    >
                                        <template #default="{ percentage }">
                                            <span class="percentage-value">{{ percentage }}%</span>
                                        </template>
                                    </el-progress>
                                </div>
                            </div>
                        </el-card>
                    </el-col>
                    <el-col :span="12">
                         <el-card shadow="hover">
                            <template #header>
                                <div class="card-header font-bold">
                                    <span>📄 考试统计</span>
                                </div>
                            </template>
                            <div class="stats-content">
                                <el-row :gutter="16">
                                    <el-col :span="8">
                                        <div class="statistic-item">
                                            <div class="stat-value">{{ assignmentStats.exam.count }}</div>
                                            <div class="stat-label">总数</div>
                                        </div>
                                    </el-col>
                                    <el-col :span="8">
                                        <div class="statistic-item">
                                            <div class="stat-value text-success">{{ assignmentStats.exam.submitted }}</div>
                                            <div class="stat-label">已提交</div>
                                        </div>
                                    </el-col>
                                    <el-col :span="8">
                                        <div class="statistic-item">
                                            <div class="stat-value text-primary">{{ assignmentStats.exam.graded }}</div>
                                            <div class="stat-label">已批改</div>
                                        </div>
                                    </el-col>
                                </el-row>
                                
                                <el-divider style="margin: 16px 0;" />
                                
                                <div class="statistic-item mb-3">
                                    <div class="stat-value text-success">
                                        {{ assignmentStats.exam.avgScore || '-' }}
                                        <span class="text-sm text-gray-500" v-if="assignmentStats.exam.graded > 0">分</span>
                                    </div>
                                    <div class="stat-label">平均分（已批改）</div>
                                </div>
                                
                                <div class="mb-2">
                                    <div class="stat-label mb-2">参与率</div>
                                    <el-progress 
                                        :percentage="assignmentStats.exam.rate" 
                                        :color="assignmentStats.exam.rate >= 90 ? '#67C23A' : assignmentStats.exam.rate >= 70 ? '#409EFF' : '#F56C6C'"
                                        :stroke-width="16"
                                    >
                                        <template #default="{ percentage }">
                                            <span class="percentage-value">{{ percentage }}%</span>
                                        </template>
                                    </el-progress>
                                </div>
                            </div>
                        </el-card>
                    </el-col>
                </el-row>
                
                <!-- 考勤统计 -->
                <el-row :gutter="20">
                    <el-col :span="24">
                        <el-card shadow="hover">
                            <template #header>
                                <div class="card-header font-bold">
                                    <span>📅 考勤统计</span>
                                </div>
                            </template>
                            <div class="stats-content" v-if="attendanceStats">
                                <el-row :gutter="20">
                                    <el-col :span="6">
                                        <div class="statistic-item">
                                            <div class="stat-value">{{ attendanceStats.total }}</div>
                                            <div class="stat-label">总考勤次数</div>
                                        </div>
                                    </el-col>
                                    <el-col :span="6">
                                        <div class="statistic-item">
                                            <div class="stat-value text-success">{{ attendanceStats.present }}</div>
                                            <div class="stat-label">出勤次数</div>
                                        </div>
                                    </el-col>
                                    <el-col :span="6">
                                        <div class="statistic-item">
                                            <div class="stat-value text-warning">{{ attendanceStats.late }}</div>
                                            <div class="stat-label">迟到次数</div>
                                        </div>
                                    </el-col>
                                    <el-col :span="6">
                                        <div class="statistic-item">
                                            <div class="stat-value text-danger">{{ attendanceStats.absent }}</div>
                                            <div class="stat-label">缺勤次数</div>
                                        </div>
                                    </el-col>
                                </el-row>
                                
                                <el-divider />
                                
                                <el-row :gutter="20">
                                    <el-col :span="12">
                                        <div class="mb-3">
                                            <div class="stat-label mb-2">出勤率</div>
                                            <el-progress 
                                                :percentage="attendanceStats.attendanceRate" 
                                                :color="attendanceStats.attendanceRate >= 90 ? '#67C23A' : attendanceStats.attendanceRate >= 80 ? '#E6A23C' : '#F56C6C'"
                                                :stroke-width="20"
                                            />
                                        </div>
                                    </el-col>
                                    <el-col :span="12">
                                        <div class="stats-item mb-3">
                                            <div class="label text-gray-600 mb-2">请假次数</div>
                                            <div class="value text-xl font-bold" style="color: #909399;">{{ attendanceStats.leave }}</div>
                                        </div>
                                    </el-col>
                                </el-row>
                            </div>
                            <div v-else class="empty-text">
                                暂无考勤数据
                            </div>
                        </el-card>
                    </el-col>
                </el-row>
            </div>
       </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document, Location, Clock, Calendar, Check, Close, Edit, Tickets } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
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

const handleCheckIn = async (attendanceId) => {
    try {
        await api.post(`/attendance/${attendanceId}/checkin`)
        ElMessage.success('签到成功')
        // Refresh data
        const resAtt = await api.get(`/attendance/class/${classId}/me`)
        attendanceRecords.value = resAtt.data || []
    } catch (e) {
        ElMessage.error(e.response?.data?.error || '签到失败')
    }
}

const assignmentStats = computed(() => {
    if (!assignments.value) return null;
    
    const stats = {
        homework: { count: 0, submitted: 0, graded: 0, totalScore: 0, avgScore: 0, rate: 0 },
        exam: { count: 0, submitted: 0, graded: 0, totalScore: 0, avgScore: 0, rate: 0 }
    };

    assignments.value.forEach(a => {
        const type = a.type === 'exam' ? 'exam' : 'homework';
        stats[type].count++;

        if (a.submission_status === 'submitted' || a.submission_status === 'graded') {
            stats[type].submitted++;
        }
        
        if (a.submission_status === 'graded' && a.my_score != null) {
            stats[type].graded++;
            stats[type].totalScore += parseFloat(a.my_score);
        }
    });

    // Calc Avg
    if (stats.homework.graded > 0) stats.homework.avgScore = (stats.homework.totalScore / stats.homework.graded).toFixed(1);
    if (stats.exam.graded > 0) stats.exam.avgScore = (stats.exam.totalScore / stats.exam.graded).toFixed(1);
    
    // Calc Rate
    if (stats.homework.count > 0) stats.homework.rate = Math.round((stats.homework.submitted / stats.homework.count) * 100);
    if (stats.exam.count > 0) stats.exam.rate = Math.round((stats.exam.submitted / stats.exam.count) * 100);

    return stats;
})

// 计算考勤统计
const attendanceStats = computed(() => {
    if (!attendanceRecords.value || attendanceRecords.value.length === 0) return null;
    
    const stats = {
        total: attendanceRecords.value.length,
        present: 0,
        absent: 0,
        late: 0,
        leave: 0,
        attendanceRate: 0
    };
    
    attendanceRecords.value.forEach(record => {
        if (record.status === 'present') {
            stats.present++;
        } else if (record.status === 'absent') {
            stats.absent++;
        } else if (record.status === 'late') {
            stats.late++;
        } else if (record.status === 'leave') {
            stats.leave++;
        }
    });
    
    // 计算出勤率 = (出勤 + 迟到) / 总次数 * 100
    if (stats.total > 0) {
        stats.attendanceRate = Math.round(((stats.present + stats.late) / stats.total) * 100);
    }
    
    return stats;
})

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
    router.push(`/student/assignment/${id}`)
}

const goBack = () => {
    router.back()
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
.mb-3 { margin-bottom: 0.75rem; }
.mb-2 { margin-bottom: 0.5rem; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.text-lg { font-size: 18px; }
.text-xl { font-size: 1.25rem; line-height: 1.75rem; }
.text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
.text-sm { font-size: 0.875rem; line-height: 1.25rem; }
.font-bold { font-weight: bold; }
.text-danger { color: #F56C6C; }
.text-primary { color: #409EFF; }
.text-success { color: #67C23A; }
.text-warning { color: #E6A23C; }
.text-2xl { font-size: 1.5rem; line-height: 2rem; }
.text-gray-600 { color: #606266; }
.text-gray-400 { color: #909399; }
.text-gray-500 { color: #909399; }
.text-xs { font-size: 0.75rem; }
.font-bold { font-weight: bold; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.p-4 { padding: 1rem; }
.empty-text {
    padding: 20px;
    text-align: center;
    color: #909399;
}

/* 统计卡片样式 - 与Dashboard保持一致 */
.statistic-item {
    text-align: center;
    padding: 10px 0;
}

.stat-label {
    font-size: 13px;
    color: #909399;
    margin-bottom: 4px;
}

.stat-value {
    font-size: 24px;
    font-weight: bold;
    line-height: 1.5;
    color: #303133;
}

.stats-content {
    padding: 10px 0;
}

.percentage-value {
    font-size: 14px;
    font-weight: bold;
}
</style>