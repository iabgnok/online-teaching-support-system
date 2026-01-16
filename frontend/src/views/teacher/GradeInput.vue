<template>
  <div class="grade-input-container">
    <el-page-header @back="goBack" :content="`成绩录入 - ${itemName}`" class="mb-4" />
    
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <div>
            <span>{{ itemName }}</span>
            <el-tag class="ml-2" size="small">满分: {{ maxScore }}</el-tag>
          </div>
          <div>
            <el-button @click="exportGrades">导出</el-button>
            <el-button type="primary" @click="saveGrades" :loading="saving">保存</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="students" border stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="student_no" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="得分" width="150">
          <template #default="scope">
            <el-input-number 
              v-model="scope.row.score" 
              :min="0" 
              :max="maxScore"
              :precision="1"
              size="small"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="百分制" width="100">
          <template #default="scope">
            {{ calculatePercentage(scope.row.score) }}
          </template>
        </el-table-column>
        <el-table-column prop="remarks" label="备注">
          <template #default="scope">
            <el-input v-model="scope.row.remarks" size="small" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const classId = ref(route.params.id)
const itemId = ref(route.params.itemId)

const itemName = ref('')
const maxScore = ref(100)
const students = ref([])
const saving = ref(false)

const fetchScores = async () => {
  try {
    const res = await api.get(`/grades/items/${itemId.value}/scores`)
    students.value = res.data
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const calculatePercentage = (score) => {
  if (score === null || score === undefined) return '-'
  return ((score / maxScore.value) * 100).toFixed(1) + '%'
}

const saveGrades = async () => {
  try {
    saving.value = true
    const scores = students.value.map(s => ({
      student_id: s.student_id,
      score: s.score
    }))
    
    await api.post(`/grades/items/${itemId.value}/scores`, { scores })
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const exportGrades = () => {
  ElMessage.info('导出功能开发中')
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchScores()
})
</script>

<style scoped>
.grade-input-container {
  padding: 20px;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}

.mb-4 { margin-bottom: 16px; }
.ml-2 { margin-left: 8px; }
</style>
