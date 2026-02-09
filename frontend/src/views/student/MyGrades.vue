<template>
  <div class="my-grades-container">
    <div class="page-header mb-4">
      <span class="text-lg font-bold">我的成绩</span>
    </div>
    
    <el-card class="mb-4">
      <el-select 
        v-model="selectedClassId" 
        placeholder="选择课程" 
        @change="fetchGrades"
        style="width: 100%"
      >
        <el-option 
          v-for="course in courses" 
          :key="course.class_id" 
          :label="course.course_name + ' - ' + course.class_name"
          :value="course.class_id"
        />
      </el-select>
    </el-card>
    
    <div v-if="selectedClassId">
      <el-card v-if="grades.final_grade" class="mb-4 total-grade-card">
        <div class="total-grade-content">
          <div class="grade-main">
            <div class="grade-number">{{ grades.final_grade.total_score }}</div>
            <div class="grade-label">总评成绩</div>
          </div>
          <el-divider direction="vertical" style="height: 80px" />
          <div class="rank-info">
            <div class="rank-item">
              <span class="rank-label">班级排名</span>
              <span class="rank-value">{{ grades.final_grade.rank }}</span>
            </div>
            <div class="rank-item">
              <span class="rank-label">百分位</span>
              <span class="rank-value">前 {{ grades.final_grade.rank_percentage }}%</span>
            </div>
          </div>
        </div>
      </el-card>
      
      <el-card 
        v-for="category in grades.categories" 
        :key="category.name"
        class="mb-4 category-card"
        @click="showCategoryDetail(category)"
      >
        <template #header>
          <div class="flex justify-between items-center">
            <span class="category-name">{{ category.name }} ({{ category.weight }}%)</span>
            <div class="flex items-center">
              <span v-if="grades.final_grade" class="category-score mr-2">
                {{ getCategoryScore(category.name) }} 分
              </span>
              <el-icon class="text-secondary"><ArrowRight /></el-icon>
            </div>
          </div>
        </template>
        
        <el-table 
          :data="category.items" 
          :show-header="false" 
          @row-click="(row, column, event) => showItemDetail(row, category, event)"
          class="grade-item-table"
        >
          <el-table-column prop="name" label="项目" />
          <el-table-column label="得分" width="150" align="right">
            <template #default="scope">
              <span v-if="scope.row.score !== null" class="score-text">
                {{ scope.row.score }} / {{ scope.row.max_score }}
              </span>
              <span v-else class="text-secondary">未录入</span>
            </template>
          </el-table-column>
          <el-table-column label="百分制" width="100" align="center">
            <template #default="scope">
              <el-progress 
                v-if="scope.row.percentage !== null"
                :percentage="scope.row.percentage" 
                :color="getProgressColor(scope.row.percentage)"
              />
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="category.items.length === 0" class="text-center text-secondary p-4">
          暂无成绩项
        </div>
      </el-card>
      
      <div v-if="grades.categories && grades.categories.length === 0" class="text-center text-secondary p-4">
        教师暂未配置成绩结构
      </div>
    </div>
    
    <div v-else class="text-center text-secondary p-4">
      请选择课程查看成绩
    </div>
    
    <!-- 成绩详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      :title="currentCategory?.name + ' 详情'"
      width="700px"
    >
      <div v-if="currentCategory">
        <div class="detail-header mb-4">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="分类权重">{{ currentCategory.weight }}%</el-descriptions-item>
            <el-descriptions-item label="分类得分">
              <span class="text-primary font-bold">{{ getCategoryScore(currentCategory.name) }}</span> 分
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <el-divider content-position="left">成绩明细</el-divider>
        
        <el-table :data="currentCategory.items" border stripe>
          <el-table-column prop="name" label="项目名称" min-width="150" />
          <el-table-column label="满分" width="80" align="center">
            <template #default="scope">{{ scope.row.max_score }}</template>
          </el-table-column>
          <el-table-column label="得分" width="80" align="center">
            <template #default="scope">
              <span v-if="scope.row.score !== null" class="font-bold">{{ scope.row.score }}</span>
              <span v-else class="text-secondary">-</span>
            </template>
          </el-table-column>
          <el-table-column label="百分比" width="80" align="center">
            <template #default="scope">
              <span v-if="scope.row.percentage !== null">{{ scope.row.percentage }}%</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="完成度" width="150" align="center">
            <template #default="scope">
              <el-progress 
                v-if="scope.row.percentage !== null"
                :percentage="scope.row.percentage" 
                :color="getProgressColor(scope.row.percentage)"
                :stroke-width="8"
              />
              <span v-else class="text-secondary">未录入</span>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="currentCategory.items.length === 0" class="text-center text-secondary p-4">
          该分类下暂无成绩项
        </div>
        
        <div v-if="currentCategory.items.length > 0" class="mt-4">
          <el-alert type="info" :closable="false">
            <template #title>
              <div class="stat-summary">
                <span>已录入: {{ getEnteredCount(currentCategory.items) }} / {{ currentCategory.items.length }} 项</span>
                <span class="ml-4">平均分: {{ getAverageScore(currentCategory.items) }}</span>
              </div>
            </template>
          </el-alert>
        </div>
      </div>
    </el-dialog>
    
    <!-- 成绩项详情对话框 -->
    <el-dialog 
      v-model="itemDialogVisible" 
      :title="currentItem?.name + ' 详情'"
      width="600px"
    >
      <div v-if="currentItem">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="所属分类">
            {{ currentItemCategory?.name }} (权重: {{ currentItemCategory?.weight }}%)
          </el-descriptions-item>
          <el-descriptions-item label="项目名称">
            {{ currentItem.name }}
          </el-descriptions-item>
          <el-descriptions-item label="满分">
            <el-tag type="info">{{ currentItem.max_score }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="我的得分">
            <el-tag v-if="currentItem.score !== null" :type="currentItem.percentage >= 85 ? 'success' : currentItem.percentage >= 60 ? '' : 'danger'" size="large">
              <span class="text-xl font-bold">{{ currentItem.score }}</span>
            </el-tag>
            <el-tag v-else type="info">未录入</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="百分比">
            <span v-if="currentItem.percentage !== null" class="text-lg font-bold">
              {{ currentItem.percentage }}%
            </span>
            <span v-else class="text-secondary">-</span>
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="currentItem.score !== null" class="mt-4">
          <el-divider content-position="left">完成度</el-divider>
          <el-progress 
            :percentage="currentItem.percentage" 
            :color="getProgressColor(currentItem.percentage)"
            :stroke-width="20"
          >
            <template #default="{ percentage }">
              <span class="percentage-text">{{ percentage }}%</span>
            </template>
          </el-progress>
          
          <div class="mt-4">
            <el-alert 
              :type="currentItem.percentage >= 85 ? 'success' : currentItem.percentage >= 60 ? 'info' : 'warning'" 
              :closable="false"
            >
              <template #title>
                <span v-if="currentItem.percentage >= 85">✨ 优秀！继续保持！</span>
                <span v-else-if="currentItem.percentage >= 60">👍 良好，还有进步空间</span>
                <span v-else>💪 需要加油哦！</span>
              </template>
            </el-alert>
          </div>
        </div>
        
        <div v-else class="mt-4">
          <el-alert type="info" :closable="false">
            <template #title>该成绩项暂未录入分数</template>
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'
import api from '../../api'

const router = useRouter()
const courses = ref([])
const selectedClassId = ref(null)
const grades = ref({ categories: [], final_grade: null })
const detailDialogVisible = ref(false)
const currentCategory = ref(null)
const itemDialogVisible = ref(false)
const currentItem = ref(null)
const currentItemCategory = ref(null)

const fetchCourses = async () => {
  try {
    const res = await api.get('/classes/my')
    courses.value = res.data
    if (courses.value.length > 0) {
      selectedClassId.value = courses.value[0].class_id
      fetchGrades()
    }
  } catch (e) {
    ElMessage.error('加载课程失败')
  }
}

const fetchGrades = async () => {
  if (!selectedClassId.value) return
  
  try {
    const res = await api.get(`/grades/student/class/${selectedClassId.value}/my-grades`)
    grades.value = res.data
  } catch (e) {
    ElMessage.error('加载成绩失败')
    grades.value = { categories: [], final_grade: null }
  }
}

const getCategoryScore = (categoryName) => {
  if (!grades.value.final_grade || !grades.value.final_grade.category_scores) {
    return '-'
  }
  return grades.value.final_grade.category_scores[categoryName] || '-'
}

const getProgressColor = (percentage) => {
  if (percentage >= 85) return '#67C23A'
  if (percentage >= 60) return '#409EFF'
  return '#F56C6C'
}

const showCategoryDetail = (category) => {
  currentCategory.value = category
  detailDialogVisible.value = true
}

const showItemDetail = (item, category, event) => {
  // 阻止事件冒泡到卡片的点击事件
  event?.stopPropagation()
  currentItem.value = item
  currentItemCategory.value = category
  itemDialogVisible.value = true
}

const getEnteredCount = (items) => {
  return items.filter(item => item.score !== null).length
}

const getAverageScore = (items) => {
  const enteredItems = items.filter(item => item.score !== null && item.percentage !== null)
  if (enteredItems.length === 0) return '-'
  const sum = enteredItems.reduce((acc, item) => acc + item.percentage, 0)
  return (sum / enteredItems.length).toFixed(1) + '%'
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchCourses()
})
</script>

<style scoped>
.my-grades-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.total-grade-card {
  background: linear-gradient(135deg, #409eff 0%, #66b3ff 100%);
  color: white;
}

.total-grade-card :deep(.el-card__body) {
  padding: 30px;
}

.total-grade-content {
  display: flex;
  align-items: center;
  justify-content: space-around;
}

.grade-main {
  text-align: center;
}

.grade-number {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 8px;
}

.grade-label {
  font-size: 16px;
  opacity: 0.9;
}

.rank-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.rank-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.rank-label {
  font-size: 14px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.category-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.category-card :deep(.el-card__header) {
  transition: background-color 0.3s ease;
}

.category-card:hover :deep(.el-card__header) {
  background-color: #f5f7fa;
}

.score-text {
  font-size: 16px;
  font-weight: 500;
}

.detail-header {
  margin-bottom: 20px;
}

.stat-summary {
  font-size: 14px;
}

.grade-item-table :deep(.el-table__row) {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.grade-item-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}

.percentage-text {
  font-size: 16px;
  font-weight: bold;
}

.text-xl {
  font-size: 20px;
}

.text-lg {
  font-size: 18px;
}

.flex {
  display: flex;
}

.justify-between {
  justify-content: space-between;
}

.items-center {
  align-items: center;
}

.mb-4 { margin-bottom: 16px; }
.mb-2 { margin-bottom: 8px; }
.mr-2 { margin-right: 8px; }
.mt-4 { margin-top: 16px; }
.ml-4 { margin-left: 16px; }
.p-4 { padding: 16px; }
.text-center { text-align: center; }
.text-secondary { color: #909399; }
.text-primary { color: #409EFF; }
.font-bold { font-weight: bold; }
</style>
