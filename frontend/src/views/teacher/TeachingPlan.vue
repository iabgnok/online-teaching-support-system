<template>
  <div class="teaching-plan-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span style="font-weight: bold; font-size: 18px;">📅 教学计划及日历</span>
          <div style="display: flex; gap: 10px; align-items: center;">
            <!-- 视图切换按钮 -->
            <el-button-group>
              <el-button 
                :type="viewMode === 'calendar' ? 'primary' : 'info'" 
                @click="viewMode = 'calendar'"
              >
                📆 日历视图
              </el-button>
              <el-button 
                :type="viewMode === 'list' ? 'primary' : 'info'" 
                @click="viewMode = 'list'"
              >
                📋 列表视图
              </el-button>
            </el-button-group>
            <!-- 添加计划按钮 -->
            <el-button type="success" @click="openAddDialog">➕ 添加计划</el-button>
          </div>
        </div>
      </template>

      <!-- 日历视图 -->
      <div v-if="viewMode === 'calendar'" class="calendar-view">
        <div style="margin-bottom: 20px;">
          <!-- 班级过滤 -->
          <el-select v-model="selectedClassId" placeholder="选择班级（不选为全部）" clearable style="width: 200px;">
            <el-option label="所有班级" :value="''"></el-option>
            <el-option 
              v-for="cls in teachingClasses" 
              :key="cls.class_id" 
              :label="cls.class_name" 
              :value="cls.class_id"
            ></el-option>
          </el-select>
        </div>

        <el-calendar v-model="currentDate">
          <template #date-cell="{ data }">
            <div class="date-cell-content" @click.stop>
              <p :class="{ 'is-selected': data.isSelected }">
                {{ data.day.split('-').slice(2).join('') }}
                <span v-if="data.isSelected">📌</span>
              </p>
              <div class="plans-list">
                <div 
                  v-for="plan in getPlansForDate(data.day)" 
                  :key="plan.id"
                  class="plan-item"
                  :style="{ borderLeft: `4px solid ${plan.color}`, backgroundColor: hexToRgba(plan.color, 0.1) }"
                  @click.stop="selectPlan(plan)"
                  :title="plan.title"
                >
                  <div class="plan-title">{{ plan.title }}</div>
                  <div class="plan-meta">{{ plan.duration_minutes }}分钟</div>
                </div>
              </div>
            </div>
          </template>
        </el-calendar>
      </div>

      <!-- 列表视图 -->
      <div v-else class="list-view">
        <div style="margin-bottom: 20px;">
          <!-- 班级过滤 -->
          <el-select v-model="selectedClassId" placeholder="选择班级（不选为全部）" clearable style="width: 200px; margin-right: 10px;">
            <el-option label="所有班级" :value="''"></el-option>
            <el-option 
              v-for="cls in teachingClasses" 
              :key="cls.class_id" 
              :label="cls.class_name" 
              :value="cls.class_id"
            ></el-option>
          </el-select>
          <!-- 刷新按钮 -->
          <el-button @click="fetchTeachingPlans" :loading="loading">🔄 刷新</el-button>
        </div>

        <el-table :data="displayedPlans" style="width: 100%;" :default-sort="{ prop: 'planned_date', order: 'ascending' }">
          <el-table-column prop="class_name" label="班级" width="120"></el-table-column>
          <el-table-column prop="title" label="计划标题" min-width="200"></el-table-column>
          <el-table-column label="计划日期" width="180">
            <template #default="{ row }">
              {{ formatDate(row.planned_date) }}
            </template>
          </el-table-column>
          <el-table-column prop="duration_minutes" label="时长(分钟)" width="100"></el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="row.sync_to_students ? 'success' : 'info'"
              >
                {{ row.sync_to_students ? '✓ 已同步' : '未同步' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button-group>
                <el-button type="primary" size="small" @click="editPlan(row)">编辑</el-button>
                <el-button 
                  v-if="!row.sync_to_students" 
                  type="warning" 
                  size="small" 
                  @click="syncToStudents(row.id)"
                >
                  同步
                </el-button>
                <el-popconfirm 
                  title="确定删除该计划吗？" 
                  @confirm="deletePlan(row.id)"
                >
                  <template #reference>
                    <el-button type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </el-button-group>
            </template>
          </el-table-column>
        </el-table>
      </div>

    </el-card>

    <!-- 详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="计划详情" 
      width="40%"
      @close="selectedPlan = null"
    >
      <div v-if="selectedPlan" style="line-height: 2;">
        <p><strong>标题:</strong> {{ selectedPlan.title }}</p>
        <p><strong>班级:</strong> {{ selectedPlan.class_name }}</p>
        <p><strong>计划日期:</strong> {{ formatDateTime(selectedPlan.planned_date) }}</p>
        <p><strong>预计时长:</strong> {{ selectedPlan.duration_minutes }} 分钟</p>
        <p v-if="selectedPlan.description"><strong>描述:</strong> {{ selectedPlan.description }}</p>
        <p><strong>同步状态:</strong> 
          <el-tag :type="selectedPlan.sync_to_students ? 'success' : 'info'">
            {{ selectedPlan.sync_to_students ? '✓ 已同步到学生端' : '未同步' }}
          </el-tag>
        </p>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="editPlan(selectedPlan)">编辑</el-button>
        <el-button 
          v-if="selectedPlan && !selectedPlan.sync_to_students" 
          type="warning" 
          @click="syncToStudents(selectedPlan.id); detailDialogVisible = false;"
        >
          同步到学生端
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog 
      v-model="editDialogVisible" 
      :title="isEditing ? '编辑计划' : '添加计划'" 
      width="50%"
      @close="resetForm"
    >
      <el-form :model="formData" ref="formRef" :rules="rules" label-width="100px">
        <el-form-item label="班级" prop="class_id">
          <el-select v-model="formData.class_id" placeholder="选择班级" :disabled="isEditing">
            <el-option 
              v-for="cls in teachingClasses" 
              :key="cls.class_id" 
              :label="cls.class_name" 
              :value="cls.class_id"
            ></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="计划标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入计划标题"></el-input>
        </el-form-item>

        <el-form-item label="计划日期" prop="planned_date">
          <el-date-picker 
            v-model="formData.planned_date" 
            type="datetime" 
            placeholder="选择计划日期和时间"
          ></el-date-picker>
        </el-form-item>

        <el-form-item label="预计时长(分钟)" prop="duration_minutes">
          <el-input-number v-model="formData.duration_minutes" :min="15" :step="15"></el-input-number>
        </el-form-item>

        <el-form-item label="描述">
          <el-input 
            v-model="formData.description" 
            type="textarea" 
            placeholder="请输入计划描述"
            rows="3"
          ></el-input>
        </el-form-item>

        <el-form-item label="同步到学生端">
          <el-switch v-model="formData.sync_to_students"></el-switch>
          <span style="margin-left: 10px; color: #909399;">开启后，学生端可查看此计划</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlan" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

// 数据
const plans = ref([])
const teachingClasses = ref([])
const currentDate = ref(new Date())
const selectedPlan = ref(null)
const loading = ref(false)
const saving = ref(false)

// 对话框状态
const detailDialogVisible = ref(false)
const editDialogVisible = ref(false)
const isEditing = ref(false)

// 视图模式
const viewMode = ref('calendar')

// 班级过滤
const selectedClassId = ref('')

// 表单数据
const formData = ref({
  class_id: null,
  title: '',
  planned_date: null,
  duration_minutes: 60,
  description: '',
  sync_to_students: false
})

// 表单引用
const formRef = ref(null)

// 表单规则
const rules = {
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  title: [{ required: true, message: '请输入计划标题', trigger: 'blur' }],
  planned_date: [{ required: true, message: '请选择计划日期', trigger: 'change' }]
}

// 计算属性：根据班级过滤的计划
const displayedPlans = computed(() => {
  if (selectedClassId.value === '') {
    return plans.value
  }
  return plans.value.filter(p => p.class_id === selectedClassId.value)
})

// 加载教学计划
const fetchTeachingPlans = async () => {
  loading.value = true
  try {
    const params = {}
    if (selectedClassId.value !== '') {
      params.class_id = selectedClassId.value
    }
    const res = await api.get('/teaching-plans', { params })
    plans.value = res.data || []
  } catch (err) {
    console.error('Failed to fetch teaching plans', err)
    ElMessage.error('加载教学计划失败')
  } finally {
    loading.value = false
  }
}

// 加载教师的班级列表
const fetchTeachingClasses = async () => {
  try {
    // 假设已有班级列表API，这里需要根据实际情况调整
    const res = await api.get('/classes/my-classes')
    teachingClasses.value = res.data || []
  } catch (err) {
    console.error('Failed to fetch teaching classes', err)
  }
}

// 获取指定日期的计划
const getPlansForDate = (dateStr) => {
  return plans.value.filter(p => {
    const planDate = new Date(p.planned_date).toISOString().split('T')[0]
    return planDate === dateStr && (selectedClassId.value === '' || p.class_id === selectedClassId.value)
  })
}

// 选择计划
const selectPlan = (plan) => {
  selectedPlan.value = plan
  detailDialogVisible.value = true
}

// 打开添加对话框
const openAddDialog = () => {
  isEditing.value = false
  resetForm()
  editDialogVisible.value = true
}

// 编辑计划
const editPlan = (plan) => {
  isEditing.value = true
  formData.value = {
    class_id: plan.class_id,
    title: plan.title,
    planned_date: new Date(plan.planned_date),
    duration_minutes: plan.duration_minutes,
    description: plan.description || '',
    sync_to_students: plan.sync_to_students
  }
  editDialogVisible.value = true
}

// 保存计划
const savePlan = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    saving.value = true
    
    const payload = {
      class_id: formData.value.class_id,
      title: formData.value.title,
      planned_date: formData.value.planned_date.toISOString(),
      duration_minutes: formData.value.duration_minutes,
      description: formData.value.description,
      sync_to_students: formData.value.sync_to_students
    }
    
    if (isEditing.value && selectedPlan.value) {
      await api.put(`/teaching-plans/${selectedPlan.value.id}`, payload)
      ElMessage.success('计划更新成功')
    } else {
      await api.post('/teaching-plans', payload)
      ElMessage.success('计划添加成功')
    }
    
    editDialogVisible.value = false
    await fetchTeachingPlans()
  } catch (err) {
    console.error('Failed to save plan', err)
    ElMessage.error('保存计划失败')
  } finally {
    saving.value = false
  }
}

// 删除计划
const deletePlan = async (planId) => {
  try {
    await api.delete(`/teaching-plans/${planId}`)
    ElMessage.success('计划删除成功')
    await fetchTeachingPlans()
  } catch (err) {
    console.error('Failed to delete plan', err)
    ElMessage.error('删除计划失败')
  }
}

// 同步到学生端
const syncToStudents = async (planId) => {
  try {
    await api.post(`/teaching-plans/sync-to-students/${planId}`)
    ElMessage.success('已同步到学生端')
    await fetchTeachingPlans()
  } catch (err) {
    console.error('Failed to sync plan', err)
    ElMessage.error('同步失败')
  }
}

// 重置表单
const resetForm = () => {
  formData.value = {
    class_id: null,
    title: '',
    planned_date: null,
    duration_minutes: 60,
    description: '',
    sync_to_students: false
  }
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 辅助函数：RGB颜色转RGBA
const hexToRgba = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// 初始化
onMounted(() => {
  fetchTeachingClasses()
  fetchTeachingPlans()
})
</script>

<style scoped>
.teaching-plan-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.calendar-view {
  padding: 20px 0;
}

.date-cell-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.date-cell-content p {
  margin: 0 0 5px 0;
  font-weight: bold;
  color: #333;
}

.date-cell-content p.is-selected {
  color: #409eff;
}

.plans-list {
  flex: 1;
  overflow-y: auto;
}

.plan-item {
  padding: 4px 6px;
  margin-bottom: 3px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.plan-item:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.plan-title {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.plan-meta {
  color: #909399;
  font-size: 11px;
}

.list-view {
  padding: 20px 0;
}
</style>
