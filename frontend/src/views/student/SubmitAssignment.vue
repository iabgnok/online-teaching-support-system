<template>
  <div class="submit-assignment-container">
    <el-page-header @back="goBack" content="作业详情"></el-page-header>
    
    <el-card v-if="assignment" class="assignment-card">
      <template #header>
        <div class="card-header">
          <span>{{ assignment.title }}</span>
          <el-tag :type="statusTag.type">{{ statusTag.text }}</el-tag>
        </div>
      </template>
      
      <p><strong>课程:</strong> {{ assignment.course_name }}</p>
      <p><strong>截止日期:</strong> {{ formattedDueDate }}</p>
      <p><strong>详情:</strong> {{ assignment.content }}</p>

      <div v-if="assignment.material_url" class="assignment-material">
        <strong>附件:</strong>
        <a :href="assignment.material_url" target="_blank" class="material-link">
          <i class="el-icon-document"></i>
          {{ getFileName(assignment.material_url) }}
        </a>
      </div>

      <el-divider></el-divider>

      <div class="submission-section">
        <h4>提交作业</h4>
        <div v-if="submission">
          <p>你已于 {{ new Date(submission.submitted_at).toLocaleString() }} 提交了作业。</p>
          <p><strong>内容:</strong> {{ submission.content }}</p>
          <div v-if="submission.file_url">
            <strong>文件:</strong>
            <a :href="submission.file_url" target="_blank">{{ getFileName(submission.file_url) }}</a>
          </div>
           <p v-if="submission.grade"><strong>成绩:</strong> {{ submission.grade }}</p>
          <p v-if="submission.feedback"><strong>教师评语:</strong> {{ submission.feedback }}</p>
        </div>

        <div v-else-if="!isPastDue">
          <el-form @submit.prevent="submitAssignment">
            <el-form-item label="提交内容">
              <el-input type="textarea" v-model="submissionContent" rows="4"></el-input>
            </el-form-item>
            <el-form-item label="上传文件">
              <input type="file" @change="handleFileChange" />
            </el-form-item>
            <el-button type="primary" @click="submitAssignment">提交</el-button>
          </el-form>
        </div>
        <div v-else>
          <p>已超过提交截止日期。</p>
        </div>
      </div>
    </el-card>
    <el-skeleton v-else :rows="5" animated />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const assignment = ref(null)
const submission = ref(null)
const submissionContent = ref('')
const submissionFile = ref(null)

const assignmentId = route.params.assignmentId

const fetchAssignmentDetails = async () => {
  try {
    const response = await api.get(`/student/assignment/${assignmentId}`)
    assignment.value = response.data.assignment
    submission.value = response.data.submission
  } catch (error) {
    console.error('Failed to fetch assignment details:', error)
    ElMessage.error('加载作业详情失败')
  }
}

const handleFileChange = (event) => {
  submissionFile.value = event.target.files[0]
}

const submitAssignment = async () => {
  if (!submissionContent.value && !submissionFile.value) {
    ElMessage.warning('请填写内容或上传文件')
    return
  }

  const formData = new FormData()
  formData.append('assignment_id', assignmentId)
  formData.append('content', submissionContent.value)
  if (submissionFile.value) {
    formData.append('file', submissionFile.value)
  }

  try {
    await api.post('/student/submit_assignment', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    ElMessage.success('作业提交成功')
    fetchAssignmentDetails() // Refresh details
  } catch (error) {
    console.error('Failed to submit assignment:', error)
    ElMessage.error('作业提交失败')
  }
}

const isPastDue = computed(() => {
  if (!assignment.value) return false
  return new Date() > new Date(assignment.value.due_date)
})

const statusTag = computed(() => {
  if (submission.value) {
    return { type: 'success', text: '已提交' }
  }
  if (isPastDue.value) {
    return { type: 'danger', text: '已截止' }
  }
  return { type: 'warning', text: '待提交' }
})

const formattedDueDate = computed(() => {
    if (!assignment.value) return ''
    return new Date(assignment.value.due_date).toLocaleString()
})

const getFileName = (url) => {
    if (!url) return ''
    return url.split('/').pop()
}

const goBack = () => {
  router.push('/')
}

onMounted(fetchAssignmentDetails)
</script>

<style scoped>
.submit-assignment-container {
  max-width: 800px;
  margin: auto;
}
.assignment-card {
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.submission-section {
  margin-top: 20px;
}
.material-link {
    margin-left: 10px;
}
</style>
