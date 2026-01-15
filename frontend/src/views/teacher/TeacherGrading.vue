<template>
  <div class="grading-page">
     <div class="header-bar mb-4">
        <el-page-header @back="goBack">
           <template #content>
               <span class="text-large font-600 mr-3"> 作业批改 </span>
               <span class="text-sm text-gray" v-if="assignment"> {{ assignment.title }} </span>
           </template>
           <template #extra>
               <el-tag type="info">总分: {{ assignment?.total_score || 100 }}</el-tag>
           </template>
        </el-page-header>
     </div>

     <el-row :gutter="20" class="grading-layout">
        <!-- Left: Student List -->
        <el-col :span="6">
            <el-card shadow="never" class="student-list-card">
                <template #header>
                    <div class="flex justify-between items-center">
                        <span>学生列表 ({{ students.length }})</span>
                        <el-select v-model="filterStatus" size="small" style="width: 100px" placeholder="筛选">
                            <el-option label="全部" value="all" />
                            <el-option label="待批改" value="submitted" />
                            <el-option label="未提交" value="unsubmitted" />
                        </el-select>
                    </div>
                </template>
                <div class="student-scroll">
                    <div 
                        v-for="student in filteredStudents" 
                        :key="student.student_id"
                        class="student-item"
                        :class="{'active': currentStudent?.student_id === student.student_id}"
                        @click="selectStudent(student)"
                    >
                        <div class="student-info">
                            <div class="name">{{ student.name }}</div>
                            <div class="code text-secondary text-xs">{{ student.student_no }}</div>
                        </div>
                        <div class="status">
                             <el-tag size="small" :type="getStatusType(student.status)">
                                 {{ getStatusText(student.status) }}
                             </el-tag>
                             <span v-if="student.status === 'graded'" class="score-badge">{{ student.score }}</span>
                        </div>
                    </div>
                </div>
            </el-card>
        </el-col>
        
        <!-- Right: Grading Area -->
        <el-col :span="18">
            <el-card shadow="never" class="grading-area" v-if="currentStudent" v-loading="submitting">
                <template #header>
                    <div class="flex justify-between items-center">
                         <div>
                             <span class="font-bold text-lg">{{ currentStudent.name }}</span>
                             <span class="text-secondary ml-2">提交时间: {{ currentStudent.submit_time ? formatTime(currentStudent.submit_time) : '未提交' }}</span>
                         </div>
                         <!-- Nav Buttons -->
                         <div class="nav-buttons">
                             <el-button-group>
                                 <el-button :disabled="!hasPrev" @click="prevStudent" size="small">上一位</el-button>
                                 <el-button :disabled="!hasNext" @click="nextStudent" size="small">下一位</el-button>
                             </el-button-group>
                         </div>
                    </div>
                </template>
                
                <div class="submission-content mb-4 p-4 bg-gray-50 rounded">
                    <div v-if="currentStudent.status === 'unsubmitted'">
                        <el-empty description="该学生尚未提交作业" :image-size="100" />
                    </div>
                    <div v-else>
                         <div class="file-link mb-2">
                             <span class="mr-2">📁 提交文件:</span>
                             <a v-if="currentStudent.file_url" :href="currentStudent.file_url" target="_blank" class="text-primary hover:underline">
                                 {{ currentStudent.file_name }}
                             </a>
                             <span v-else class="text-secondary">无文件 (纯文本提交)</span>
                         </div>
                         <div class="content-text p-3 border rounded bg-white" v-if="currentStudent.content">
                             {{ currentStudent.content }}
                         </div>
                    </div>
                </div>
                
                <div class="grid-form p-4 border-top">
                    <h3>评分与反馈</h3>
                    <el-form label-position="top">
                        <el-form-item label="分数">
                            <el-input-number v-model="currentGrade.score" :min="0" :max="assignment?.total_score || 100" />
                        </el-form-item>
                        <el-form-item label="评语">
                            <el-input 
                                v-model="currentGrade.feedback" 
                                type="textarea" 
                                rows="4" 
                                placeholder="输入评语建议..." 
                            />
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" @click="submitGrade">提交评分</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </el-card>
            <el-empty v-else description="请选择一位学生开始批改" />
        </el-col>
     </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'

const route = useRoute()
const router = useRouter()
const assignmentId = route.params.assignmentId

const assignment = ref(null)
const students = ref([])
const currentStudent = ref(null)
const filterStatus = ref('all')
const submitting = ref(false)

const currentGrade = ref({
    score: 0,
    feedback: ''
})

const filteredStudents = computed(() => {
    if (filterStatus.value === 'all') return students.value
    return students.value.filter(s => s.status === filterStatus.value)
})

const currentIndex = computed(() => filteredStudents.value.findIndex(s => s.student_id === currentStudent.value?.student_id))
const hasPrev = computed(() => currentIndex.value > 0)
const hasNext = computed(() => currentIndex.value < filteredStudents.value.length - 1)

const getStatusType = (status) => {
    const map = { 'submitted': 'warning', 'graded': 'success', 'unsubmitted': 'info' }
    return map[status] || 'info'
}

const getStatusText = (status) => {
    const map = { 'submitted': '待批改', 'graded': '已批改', 'unsubmitted': '未提交' }
    return map[status] || status
}

const formatTime = (iso) => new Date(iso).toLocaleString()

const fetchData = async () => {
    try {
        const [aRes, sRes] = await Promise.all([
            api.get(`/assignments/${assignmentId}`),
            api.get(`/assignments/${assignmentId}/submissions`)
        ])
        assignment.value = aRes.data
        students.value = sRes.data
        
        // Auto select first submitted
        const firstSubmitted = students.value.find(s => s.status === 'submitted')
        if (firstSubmitted) selectStudent(firstSubmitted)
    } catch(e) {
        ElMessage.error("加载数据失败")
    }
}

const selectStudent = (student) => {
    currentStudent.value = student
    currentGrade.value = {
        score: student.score || 0,
        feedback: student.feedback || ''
    }
}

const prevStudent = () => {
    if (hasPrev.value) selectStudent(filteredStudents.value[currentIndex.value - 1])
}

const nextStudent = () => {
    if (hasNext.value) selectStudent(filteredStudents.value[currentIndex.value + 1])
}

const submitGrade = async () => {
    submitting.value = true
    try {
        await api.post(`/assignments/${assignmentId}/submissions/${currentStudent.value.student_id}`, {
            score: currentGrade.value.score,
            feedback: currentGrade.value.feedback
        })
        
        ElMessage.success("评分保存成功")
        
        // Update local state
        currentStudent.value.status = 'graded'
        currentStudent.value.score = currentGrade.value.score
        currentStudent.value.feedback = currentGrade.value.feedback
        
        // Optional: Auto move to next?
        // nextStudent()
    } catch(e) {
        ElMessage.error("保存失败")
    } finally {
        submitting.value = false
    }
}

const goBack = () => router.back()

onMounted(fetchData)
</script>

<style scoped>
.grading-page { padding: 20px; height: calc(100vh - 80px); }
.grading-layout { height: 100%; }
.student-list-card { height: 100%; display: flex; flex-direction: column; }
.student-scroll { overflow-y: auto; height: 600px; } /* Fixed height or flex */
.grading-area { height: 100%; overflow-y: auto; }

.student-item {
    padding: 10px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.student-item:hover { background-color: #f5f7fa; }
.student-item.active { background-color: #e6f7ff; border-left: 3px solid #1890ff; }

.score-badge { font-weight: bold; margin-left: 5px; color: #67C23A; }
.bg-gray-50 { background-color: #f9fafc; }
.rounded { border-radius: 4px; }
.border-top { border-top: 1px solid #ebeef5; margin-top: 20px; padding-top: 20px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.text-lg { font-size: 18px; }
.font-bold { font-weight: bold; }
.text-secondary { color: #909399; }
.text-xs { font-size: 12px; }
.ml-2 { margin-left: 8px; }
.mr-2 { margin-right: 8px; }
.mb-2 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 16px; }
</style>