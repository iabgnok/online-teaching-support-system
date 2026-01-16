<template>
  <div class="statistics-container">
    <el-page-header @back="goBack" content="成绩统计" class="mb-4" />
    
    <template v-if="loading">
      <el-skeleton :rows="6" animated />
    </template>
    
    <template v-else>
      <div v-if="!stats.has_data" class="empty-state">
        <el-empty :description="stats.message || '暂无成绩数据'">
          <template #default>
            <div v-if="!stats.has_config">
              <p>您还没有配置成绩结构</p>
              <el-button type="primary" @click="goToConfig">前往成绩配置</el-button>
            </div>
            <div v-else>
              <p>成绩结构已配置，但还没有计算总评成绩</p>
              <p class="hint-text">请按以下步骤操作：</p>
              <ol class="steps-list">
                <li>在"成绩配置"页面，点击各成绩项的"录入成绩"</li>
                <li>为所有学生录入分数</li>
                <li>如有考勤项，点击"计算考勤"自动生成考勤成绩</li>
                <li>返回并点击"计算总评成绩"按钮</li>
              </ol>
              <el-button type="primary" @click="goToConfig">前往成绩配置</el-button>
            </div>
          </template>
        </el-empty>
      </div>
      
      <div v-else>
        <el-row :gutter="20" class="mb-4">
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-value">{{ stats.average || '-' }}</div>
                <div class="stat-label">平均分</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-value text-success">{{ stats.highest || '-' }}</div>
                <div class="stat-label">最高分</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-value text-warning">{{ stats.lowest || '-' }}</div>
                <div class="stat-label">最低分</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover">
              <div class="stat-item">
                <div class="stat-value text-primary">{{ stats.pass_rate || '-' }}%</div>
                <div class="stat-label">及格率</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <el-card class="mb-4" v-if="stats.distribution">
          <template #header>分数分布</template>
          <div class="distribution-chart">
            <div v-for="(count, range) in stats.distribution" :key="range" class="distribution-item">
              <div class="range-label">{{ range }}分</div>
              <el-progress :percentage="calculatePercentage(count)" :color="getProgressColor(range)" />
              <div class="count-label">{{ count }}人</div>
            </div>
          </div>
        </el-card>
        
        <el-card v-if="stats.rankings && stats.rankings.length > 0">
          <template #header>
            <div class="flex justify-between">
              <span>成绩排名</span>
              <el-button @click="exportRankings">导出</el-button>
            </div>
          </template>
          <el-table :data="stats.rankings" border stripe>
            <el-table-column prop="rank" label="排名" width="80" align="center" />
            <el-table-column prop="student_no" label="学号" width="120" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="total_score" label="总分" width="100" align="center">
              <template #default="scope">
                <span class="font-bold">{{ scope.row.total_score }}</span>
              </template>
            </el-table-column>
            <el-table-column label="分类得分">
              <template #default="scope">
                <el-tag 
                  v-for="(score, name) in scope.row.category_scores" 
                  :key="name"
                  class="mr-2"
                  size="small"
                >
                  {{ name }}: {{ score }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </template>
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

const loading = ref(true)
const stats = ref({
  has_data: false,
  has_config: false,
  distribution: {},
  rankings: [],
  total_students: 0,
  average: 0,
  highest: 0,
  lowest: 0,
  pass_rate: 0,
  excellent_rate: 0
})

const fetchStatistics = async () => {
  loading.value = true
  try {
    const res = await api.get(`/grades/class/${classId.value}/statistics`)
    stats.value = res.data
  } catch (e) {
    console.error(e)
    ElMessage.error('加载失败')
    stats.value = { has_data: false }
  } finally {
    loading.value = false
  }
}

const calculatePercentage = (count) => {
  if (!stats.value.total_students || stats.value.total_students === 0) return 0
  return Math.round((count / stats.value.total_students) * 100)
}

const getProgressColor = (range) => {
  if (range === '90-100') return '#67C23A'
  if (range === '80-89') return '#409EFF'
  if (range === '70-79') return '#E6A23C'
  if (range === '60-69') return '#F56C6C'
  return '#909399'
}

const exportRankings = () => {
  ElMessage.info('导出功能开发中')
}

const goToConfig = () => {
  router.push(`/teacher/class/${classId.value}/grade-config`)
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  fetchStatistics()
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
}

.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.hint-text {
  color: #606266;
  margin: 16px 0 8px 0;
  font-size: 14px;
}

.steps-list {
  text-align: left;
  display: inline-block;
  margin: 16px 0;
  padding-left: 24px;
}

.steps-list li {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.distribution-chart {
  padding: 20px;
}

.distribution-item {
  margin-bottom: 20px;
}

.range-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.count-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.text-success { color: #67C23A; }
.text-warning { color: #E6A23C; }
.text-primary { color: #409EFF; }

.flex {
  display: flex;
}

.justify-between {
  justify-content: space-between;
}

.mb-4 { margin-bottom: 16px; }
.mr-2 { margin-right: 8px; }
.font-bold { font-weight: bold; }
</style>
