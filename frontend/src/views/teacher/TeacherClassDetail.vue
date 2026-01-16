<template>
  <div class="class-manage-container">
    <!-- Header Info -->
    <el-card shadow="never" class="mb-4" v-if="courseInfo">
        <template #header>
            <div class="flex justify-between items-center">
                <div>
                   <span class="text-lg font-bold mr-2">{{ courseInfo.course_name }}</span>
                   <el-tag>{{ courseInfo.class_name }}</el-tag>
                </div>
                <div class="text-secondary text-sm">
                    {{ courseInfo.semester }} | {{ courseInfo.student_count }} 人
                </div>
            </div>
        </template>
        <div class="info-row">
            <span class="mr-4"><el-icon><Location /></el-icon> {{ courseInfo.classroom || '未排课' }}</span>
            <span><el-icon><Clock /></el-icon> {{ courseInfo.time || '时间未定' }}</span>
        </div>
    </el-card>

    <el-tabs v-model="activeTab" class="manage-tabs" type="border-card">
        <!-- Tab 1: Student Roster -->
        <el-tab-pane label="学生名册" name="students">
            <div class="tab-actions mb-2">
                <el-button type="success" size="small" plain>导出名单</el-button>
            </div>
            <el-table :data="students" stripe style="width: 100%" v-loading="loadingStudents">
                <el-table-column prop="student_no" label="学号" width="120" sortable />
                <el-table-column prop="name" label="姓名" width="120" />
                <el-table-column prop="major" label="专业" />
                <el-table-column prop="dept_name" label="学院" />
                <!-- Placeholder for future functionality -->
                <el-table-column label="操作" width="150" align="center">
                    <template #default="scope">
                        <el-button link type="primary" size="small">详情</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-tab-pane>

        <!-- Tab 2: Assignments -->
        <el-tab-pane label="作业管理" name="assignments">
             <div class="tab-actions mb-3 flex justify-between">
                <span>共 {{ assignments.length }} 次作业</span>
                <el-button type="primary" size="small" @click="createAssignment">+ 发布作业</el-button>
            </div>
            <el-table :data="assignments" style="width: 100%" v-loading="loadingAssignments">
                <el-table-column prop="title" label="作业标题" min-width="200" />
                <el-table-column prop="deadline" label="截止时间" width="180">
                    <template #default="scope">{{ formatTime(scope.row.deadline) }}</template>
                </el-table-column>
                <el-table-column label="提交统计" width="250">
                    <template #default="scope">
                         <div class="stats-tags">
                             <el-tag type="success" size="small" effect="plain">已批: {{ scope.row.stats?.graded || 0 }}</el-tag>
                             <el-tag type="warning" size="small" effect="plain" class="ml-2">待批: {{ scope.row.stats?.pending || 0 }}</el-tag>
                             <el-tag type="info" size="small" effect="plain" class="ml-2">未交: {{ (scope.row.stats?.total || 0) - (scope.row.stats?.submitted || 0) - (scope.row.stats?.graded || 0) }}</el-tag>
                         </div>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="120" align="center">
                    <template #default="scope">
                        <el-button type="primary" size="small" @click="goToGrading(scope.row.id)">批改</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-tab-pane>

        <!-- Tab 3: Materials -->
        <el-tab-pane label="课件资料" name="materials">
             <div class="tab-actions mb-3 flex justify-between">
                <span></span>
                <el-button type="primary" size="small" @click="uploadMaterial">+ 上传资料</el-button>
            </div>
            <el-table :data="materials" style="width: 100%" v-loading="loadingMaterials">
                <el-table-column prop="title" label="名称" />
                <el-table-column prop="file_size" label="大小" width="100">
                     <template #default="scope">{{ formatSize(scope.row.file_size) }}</template>
                </el-table-column>
                <el-table-column prop="publish_time" label="发布时间" width="180">
                     <template #default="scope">{{ formatDate(scope.row.publish_time) }}</template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                    <template #default="scope">
                        <el-button link type="danger" size="small">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-tab-pane>
        
        <!-- Tab 4: Attendance -->
        <el-tab-pane label="考勤记录" name="attendance">
            <div class="tab-actions mb-3 flex justify-between">
                <span>共 {{ attendanceList.length }} 次考勤</span>
                <el-button type="primary" size="small" @click="createAttendance">+ 发起考勤</el-button>
            </div>
            
            <!-- Attendance History Table -->
            <el-table :data="attendanceList" style="width: 100%" v-if="!currentAttendanceId">
                <el-table-column prop="date" label="日期" width="150" sortable />
                <el-table-column label="出勤统计">
                     <template #default="scope">
                         <div class="stats-mini">
                             <el-tag type="success" size="small">出勤: {{ scope.row.stats.present }}</el-tag>
                             <el-tag type="danger" size="small" class="ml-2">缺勤: {{ scope.row.stats.absent }}</el-tag>
                             <el-tag type="warning" size="small" class="ml-2">迟到: {{ scope.row.stats.late }}</el-tag>
                             <el-tag type="info" size="small" class="ml-2">请假: {{ scope.row.stats.leave }}</el-tag>
                         </div>
                     </template>
                </el-table-column>
                <el-table-column label="操作" width="150" align="center">
                    <template #default="scope">
                        <el-button link type="primary" @click="viewAttendance(scope.row.attendance_id)">详情/修改</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- Active Attendance Detail (Inline Edit) -->
            <div v-else class="attendance-detail-view">
                 <div class="detail-header mb-4 flex justify-between items-center bg-gray-50 p-3 rounded">
                     <span class="font-bold">📅 {{ currentAttendanceDate }} 考勤表</span>
                     <div>
                         <el-button size="small" @click="closeAttendanceDetail">返回列表</el-button>
                         <el-button type="primary" size="small" @click="saveAttendanceChanges" :loading="savingAttendance">保存更改</el-button>
                     </div>
                 </div>
                 
                 <el-table :data="currentAttendanceRecords" height="500" border>
                     <el-table-column prop="student_no" label="学号" width="120" sortable />
                     <el-table-column prop="name" label="姓名" width="120" />
                     <el-table-column label="状态" width="300">
                         <template #default="scope">
                             <el-radio-group v-model="scope.row.status" size="small">
                                <el-radio-button label="present">出勤</el-radio-button>
                                <el-radio-button label="late">迟到</el-radio-button>
                                <el-radio-button label="leave">请假</el-radio-button>
                                <el-radio-button label="absent">缺勤</el-radio-button>
                              </el-radio-group>
                         </template>
                     </el-table-column>
                     <el-table-column label="备注">
                         <template #default="scope">
                             <el-input v-model="scope.row.remarks" size="small" placeholder="备注..." />
                         </template>
                     </el-table-column>
                 </el-table>
            </div>
        </el-tab-pane>

        <!-- Tab 5: Gradebook -->
        <el-tab-pane label="成绩管理" name="grades">
             <div class="tab-actions mb-3 flex justify-between">
                <span>成绩总览</span>
                <el-button type="primary" size="small" @click="fetchGrades">刷新</el-button>
            </div>
            
            <el-table :data="gradeTableData" style="width: 100%" v-loading="loadingGrades" border max-height="600">
                <el-table-column fixed prop="student_no" label="学号" width="120" sortable />
                <el-table-column fixed prop="name" label="姓名" width="100" />
                
                <!-- Dynamic Assignment Columns -->
                <el-table-column 
                    v-for="ass in gradeAssignments" 
                    :key="ass.id" 
                    :label="ass.title" 
                    width="150"
                    align="center"
                >
                    <template #header>
                        <div class="truncate" :title="ass.title">{{ ass.title }}</div>
                        <div class="text-xs text-gray-500">满分: {{ ass.total }}</div>
                    </template>
                    <template #default="scope">
                        <span :class="getScoreClass(scope.row.scores[ass.id], ass.total)">
                            {{ scope.row.scores[ass.id] !== null && scope.row.scores[ass.id] !== undefined ? scope.row.scores[ass.id] : '-' }}
                        </span>
                    </template>
                </el-table-column>
                
                <!-- Summary Columns -->
                <el-table-column label="平时分" align="center" width="100">
                     <template #default="scope">{{ scope.row.summary.homework_avg || '-' }}</template>
                </el-table-column>
                <el-table-column label="考试分" align="center" width="100">
                     <template #default="scope">{{ scope.row.summary.exam_avg || '-' }}</template>
                </el-table-column>
                <el-table-column label="总成绩" align="center" width="100" fixed="right">
                     <template #default="scope">
                         <strong class="text-lg" :class="getGradeClass(scope.row.summary.final)">
                             {{ scope.row.summary.final || '-' }}
                         </strong>
                     </template>
                </el-table-column>
            </el-table>
        </el-tab-pane>
    </el-tabs>

    <!-- Create Assignment Dialog -->
    <el-dialog v-model="dialogVisible" title="发布新作业" width="500px">
        <el-form :model="form" label-width="80px">
            <el-form-item label="标题">
                <el-input v-model="form.title" placeholder="如: 期中大作业" />
            </el-form-item>
            <el-form-item label="截止时间">
                <el-date-picker 
                    v-model="form.deadline" 
                    type="datetime" 
                    placeholder="选择截止日期" 
                    style="width: 100%" 
                    value-format="YYYY-MM-DD HH:mm:ss"
                />
            </el-form-item>
             <el-form-item label="满分">
                <el-input-number v-model="form.total_score" :min="1" :max="100" />
            </el-form-item>
            <el-form-item label="类型">
                <el-radio-group v-model="form.type">
                  <el-radio label="homework">普通作业</el-radio>
                  <el-radio label="exam">考试测验</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item label="说明">
                <el-input v-model="form.description" type="textarea" rows="3" />
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitAssignment" :loading="submitting">发布</el-button>
            </span>
        </template>
    </el-dialog>

    <!-- Upload Material Dialog -->
    <el-dialog v-model="uploadDialogVisible" title="上传课件资料" width="500px">
        <el-form label-width="80px">
            <el-form-item label="文件">
                <el-upload
                    class="upload-demo"
                    drag
                    action=""
                    :auto-upload="false"
                    :on-change="handleFileChange"
                    :limit="1"
                    style="width: 100%"
                >
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">
                         拖拽文件到此处或 <em>点击上传</em>
                    </div>
                </el-upload>
            </el-form-item>
             <el-form-item label="标题">
                <el-input v-model="uploadForm.title" placeholder="如果不填则使用文件名" />
            </el-form-item>
             <el-form-item label="描述">
                <el-input v-model="uploadForm.description" type="textarea" />
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="uploadDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitUpload" :loading="uploading">开始上传</el-button>
            </span>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Location, Clock, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../../api'

const route = useRoute()
const router = useRouter()
const classId = route.params.id

const courseInfo = ref(null)
const students = ref([])
const assignments = ref([])
const materials = ref([])
const activeTab = ref('students')

const loadingStudents = ref(false)
const loadingAssignments = ref(false)
const loadingMaterials = ref(false)

// Dialog State
const dialogVisible = ref(false)
const submitting = ref(false)
const form = ref({
    title: '',
    deadline: '',
    total_score: 100,
    description: '',
    type: 'homework'
})

// Upload Dialog State
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadForm = ref({
    title: '',
    description: '',
    file: null
})

const fetchClassInfo = async () => {
    try {
        // Reuse my classes to get info (optimized would be single get)
        const res = await api.get('/classes/my')
        courseInfo.value = res.data.find(c => c.class_id == classId)
    } catch(e) {}
}

const fetchStudents = async () => {
    loadingStudents.value = true
    try {
        const res = await api.get(`/classes/${classId}/students`)
        students.value = res.data
    } catch(e) {}
    finally { loadingStudents.value = false }
}

const fetchAssignments = async () => {
    loadingAssignments.value = true
    try {
        const res = await api.get(`/classes/${classId}/assignments`)
        assignments.value = res.data
    } catch(e) {}
    finally { loadingAssignments.value = false }
}

const fetchMaterials = async () => {
    loadingMaterials.value = true
    try {
        const res = await api.get(`/classes/${classId}/materials`)
        materials.value = res.data
    } catch(e) {}
    finally { loadingMaterials.value = false }
}

const createAssignment = () => {
    form.value = { title: '', deadline: '', total_score: 100, description: '', type: 'homework' }
    dialogVisible.value = true
}

const submitAssignment = async () => {
    if(!form.value.title || !form.value.deadline) {
        ElMessage.warning('请填写完整信息')
        return
    }
    submitting.value = true
    try {
        await api.post('/assignments/', {
            ...form.value,
            class_id: classId
        })
        ElMessage.success('发布成功')
        dialogVisible.value = false
        fetchAssignments() // Refresh list
    } catch(e) {
        ElMessage.error('发布失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        submitting.value = false
    }
}

const goToGrading = (assignmentId) => {
    // alert(`跳转到批改界面 (ID: ${assignmentId})`)
    router.push(`/teacher/grading/${assignmentId}`)
}

const uploadMaterial = () => {
    uploadDialogVisible.value = true
    uploadForm.value = { title: '', description: '', file: null }
}

const handleFileChange = (uploadFile) => {
    uploadForm.value.file = uploadFile.raw
}

const submitUpload = async () => {
    if (!uploadForm.value.file) {
        ElMessage.warning('请选择文件')
        return
    }
    
    uploading.value = true
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('title', uploadForm.value.title || uploadForm.value.file.name)
    formData.append('description', uploadForm.value.description)
    
    try {
        await api.post(`/classes/${classId}/materials`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        ElMessage.success('上传成功')
        uploadDialogVisible.value = false
        fetchMaterials()
    } catch(e) {
        ElMessage.error('上传失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        uploading.value = false
    }
}

// Attendance Logic
const attendanceList = ref([])
const currentAttendanceId = ref(null)
const currentAttendanceDate = ref('')
const currentAttendanceRecords = ref([])
const savingAttendance = ref(false)

const fetchAttendanceList = async () => {
    try {
        const res = await api.get(`/attendance/class/${classId}`)
        attendanceList.value = res.data
    } catch(e) { console.error(e) }
}

const createAttendance = async () => {
    try {
        await api.post(`/attendance/class/${classId}`)
        ElMessage.success('考勤已发起')
        fetchAttendanceList()
    } catch(e) {
        ElMessage.error('发起失败: ' + (e.response?.data?.error || '未知错误'))
    }
}

const viewAttendance = async (id) => {
    try {
        const res = await api.get(`/attendance/${id}`)
        currentAttendanceId.value = id
        currentAttendanceDate.value = formatDate(res.data.date)
        currentAttendanceRecords.value = res.data.records
    } catch(e) {
        ElMessage.error('无法加载详情')
    }
}

const closeAttendanceDetail = () => {
    currentAttendanceId.value = null
    currentAttendanceRecords.value = []
    fetchAttendanceList() // Refresh stats
}

const saveAttendanceChanges = async () => {
    savingAttendance.value = true
    try {
        const payload = {
            records: currentAttendanceRecords.value.map(r => ({
                record_id: r.record_id,
                status: r.status,
                remarks: r.remarks
            }))
        }
        await api.put(`/attendance/${currentAttendanceId.value}/records`, payload)
        ElMessage.success('保存成功')
    } catch(e) {
        ElMessage.error('保存失败')
    } finally {
        savingAttendance.value = false
    }
}

// Grades Logic
const loadingGrades = ref(false)
const gradeTableData = ref([])
const gradeAssignments = ref([])

const fetchGrades = async () => {
    loadingGrades.value = true
    try {
        const res = await api.get(`/classes/${classId}/grades`)
        gradeAssignments.value = res.data.assignments
        gradeTableData.value = res.data.students
    } catch (err) {
        console.error(err)
        // ElMessage.error('无法获取成绩数据')
    } finally {
        loadingGrades.value = false
    }
}

const getScoreClass = (score, total) => {
    if (score === null || score === undefined) return 'text-gray-400'
    const ratio = score / total
    if (ratio < 0.6) return 'text-red-500 font-bold'
    if (ratio >= 0.9) return 'text-green-600 font-bold'
    return ''
}

const getGradeClass = (score) => {
    if (!score) return ''
    if (score < 60) return 'text-red-600'
    if (score >= 90) return 'text-green-600'
    return ''
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
    fetchClassInfo()
    fetchStudents()
    fetchAssignments()
    fetchMaterials()
    fetchAttendanceList()
    fetchGrades()
})
</script>

<style scoped>
.class-manage-container {
    padding: 20px;
}
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.text-lg { font-size: 18px; }
.font-bold { font-weight: bold; }
.text-secondary { color: #909399; }
.text-sm { font-size: 13px; }
.mr-2 { margin-right: 8px; }
.mr-4 { margin-right: 16px; }
.ml-2 { margin-left: 8px; }
.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }

.info-row {
    margin-top: 10px;
    color: #606266;
    font-size: 14px;
}

.truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
