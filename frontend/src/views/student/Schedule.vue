<template>
  <div class="schedule-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span style="font-weight: bold; font-size: 18px;">📅 我的日程</span>
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
            <!-- 添加个人任务按钮 -->
            <el-button type="success" @click="openAddTaskDialog">➕ 添加任务</el-button>
          </div>
        </div>
      </template>

      <!-- 日历视图 -->
      <div v-if="viewMode === 'calendar'" class="calendar-view">
        <!-- 图例说明 -->
        <div class="legend">
          <span class="legend-item">
            <span class="legend-color" style="background-color: #5cb85c;"></span>
            <span>&gt; 2周</span>
          </span>
          <span class="legend-item">
            <span class="legend-color" style="background-color: #f0ad4e;"></span>
            <span>1-2周</span>
          </span>
          <span class="legend-item">
            <span class="legend-color" style="background-color: #d58a2d;"></span>
            <span>&lt; 1周</span>
          </span>
          <span class="legend-item">
            <span class="legend-color" style="background-color: #d9534f;"></span>
            <span>1天内</span>
          </span>
          <el-divider direction="vertical"></el-divider>
          <el-checkbox v-model="showTeacherTasks" @change="refreshCalendar">显示教师任务</el-checkbox>
          <el-checkbox v-model="showPersonalTasks" @change="refreshCalendar">显示个人任务</el-checkbox>
        </div>

        <el-calendar v-model="currentDate">
          <template #date-cell="{ data }">
            <div class="date-cell-content" @click.stop>
              <p :class="{ 'is-today': data.isSelected }">
                {{ data.day.split('-').slice(2).join('') }}
                <span v-if="data.isSelected">📌</span>
              </p>
              <div class="events-list">
                <!-- 教师任务 -->
                <div 
                  v-if="showTeacherTasks"
                  v-for="event in getTeacherTasksForDate(data.day)" 
                  :key="`teacher-${event.id}`"
                  class="event-item teacher-task"
                  :style="{ backgroundColor: event.color }"
                  @click.stop="openTaskDetail(event, 'teacher')"
                  :title="`📚 ${event.title}`"
                >
                  <span class="task-icon">📚</span>
                  <span class="task-text">{{ event.title }}</span>
                </div>

                <!-- 个人任务 -->
                <div 
                  v-if="showPersonalTasks"
                  v-for="task in getPersonalTasksForDate(data.day)" 
                  :key="`personal-${task.id}`"
                  class="event-item personal-task"
                  :style="{ backgroundColor: task.color }"
                  @click.stop="openTaskDetail(task, 'personal')"
                  :title="`${task.is_completed ? '✓' : '○'} ${task.title}`"
                >
                  <span class="task-icon">{{ task.is_completed ? '✅' : '📝' }}</span>
                  <span class="task-text" :style="{ textDecoration: task.is_completed ? 'line-through' : 'none' }">
                    {{ task.title }}
                  </span>
                </div>
              </div>
            </div>
          </template>
        </el-calendar>
      </div>

      <!-- 列表视图 -->
      <div v-else class="list-view">
        <div style="margin-bottom: 20px; display: flex; gap: 10px;">
          <!-- 任务类型过滤 -->
          <el-radio-group v-model="taskTypeFilter">
            <el-radio label="all">全部任务</el-radio>
            <el-radio label="teacher">教师任务</el-radio>
            <el-radio label="personal">个人任务</el-radio>
          </el-radio-group>
          <!-- 完成状态过滤 -->
          <el-select v-model="completionFilter" placeholder="筛选完成状态" style="width: 150px;">
            <el-option label="全部" value="all"></el-option>
            <el-option label="未完成" value="incomplete"></el-option>
            <el-option label="已完成" value="completed"></el-option>
          </el-select>
          <!-- 刷新按钮 -->
          <el-button @click="fetchAllTasks" :loading="loading">🔄 刷新</el-button>
        </div>

        <!-- 任务列表 -->
        <div class="tasks-list">
          <div
            v-for="(task, index) in filteredTasksList"
            :key="`${task.type}-${task.id}-${index}`"
            class="task-item-wrapper"
          >
            <div class="task-date-label">
              {{ formatDate(task.planned_date) }}
            </div>
            <el-card class="task-card" @click="openTaskDetail(task, task.type)">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                  <div style="display: flex; gap: 10px; align-items: center;">
                    <span 
                      :style="{ 
                        backgroundColor: task.color,
                        width: '12px',
                        height: '12px',
                        borderRadius: '50%'
                      }"
                    ></span>
                    <h4 style="margin: 0;">
                      {{ task.type === 'teacher' ? '📚' : '📝' }} 
                      {{ task.title }}
                      <el-tag 
                        v-if="task.type === 'personal' && task.priority"
                        :type="getPriorityType(task.priority)"
                        style="margin-left: 10px;"
                        size="small"
                      >
                        {{ getPriorityText(task.priority) }}
                      </el-tag>
                      <el-tag 
                        v-if="task.type === 'personal' && task.is_completed"
                        type="success"
                        style="margin-left: 5px;"
                        size="small"
                      >
                        ✓ 已完成
                      </el-tag>
                    </h4>
                  </div>
                  <p style="margin: 8px 0 0 0; color: #606266;">
                    ⏱️ 预计时长: {{ task.duration_minutes }} 分钟
                    <span v-if="task.type === 'teacher' && task.submission_status" style="margin-left: 20px;">
                      📤 状态: {{ formatSubmissionStatus(task.submission_status) }}
                    </span>
                  </p>
                  <p v-if="task.description" style="margin: 5px 0 0 0; color: #909399; font-size: 13px;">
                    {{ task.description }}
                  </p>
                </div>
                <div style="text-align: right; margin-left: 20px;">
                  <el-button 
                    v-if="task.type === 'personal'"
                    type="primary" 
                    link 
                    size="small"
                    @click.stop="toggleTaskComplete(task)"
                  >
                    {{ task.is_completed ? '取消完成' : '标记完成' }}
                  </el-button>
                  <el-button 
                    type="danger" 
                    link 
                    size="small"
                    @click.stop="deleteTask(task)"
                    v-if="task.type === 'personal'"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>

    </el-card>

    <!-- 任务详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      :title="`${selectedTaskType === 'teacher' ? '教师任务' : '个人任务'}详情`"
      width="45%"
      @close="selectedTask = null; selectedTaskType = null"
    >
      <div v-if="selectedTask" style="line-height: 2;">
        <p><strong>标题:</strong> {{ selectedTask.title }}</p>
        <p><strong>计划日期:</strong> {{ formatDateTime(selectedTask.planned_date) }}</p>
        <p><strong>预计时长:</strong> {{ selectedTask.duration_minutes }} 分钟</p>
        <p v-if="selectedTask.description"><strong>描述:</strong> {{ selectedTask.description }}</p>
        
        <!-- 教师任务特有信息 -->
        <template v-if="selectedTaskType === 'teacher'">
          <p v-if="selectedTask.class_name"><strong>班级:</strong> {{ selectedTask.class_name }}</p>
          <p v-if="selectedTask.assignment_type"><strong>类型:</strong> {{ formatTaskType(selectedTask.assignment_type) }}</p>
          <p v-if="selectedTask.submission_status"><strong>提交状态:</strong> {{ formatSubmissionStatus(selectedTask.submission_status) }}</p>
        </template>

        <!-- 个人任务特有信息 -->
        <template v-if="selectedTaskType === 'personal'">
          <p><strong>优先级:</strong> 
            <el-tag :type="getPriorityType(selectedTask.priority)" size="small">
              {{ getPriorityText(selectedTask.priority) }}
            </el-tag>
          </p>
          <p><strong>完成状态:</strong> 
            <el-tag :type="selectedTask.is_completed ? 'success' : 'info'" size="small">
              {{ selectedTask.is_completed ? '✓ 已完成' : '未完成' }}
            </el-tag>
          </p>
          <p v-if="selectedTask.completed_at"><strong>完成时间:</strong> {{ formatDateTime(selectedTask.completed_at) }}</p>
        </template>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button 
          v-if="selectedTaskType === 'personal'"
          type="primary" 
          @click="toggleTaskComplete(selectedTask)"
        >
          {{ selectedTask?.is_completed ? '取消完成' : '标记完成' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加个人任务对话框 -->
    <el-dialog 
      v-model="addTaskDialogVisible" 
      title="添加个人任务"
      width="50%"
      @close="resetForm"
    >
      <el-form :model="newTaskForm" ref="formRef" :rules="rules" label-width="100px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="newTaskForm.title" placeholder="请输入任务标题"></el-input>
        </el-form-item>

        <el-form-item label="计划日期" prop="planned_date">
          <el-date-picker 
            v-model="newTaskForm.planned_date" 
            type="datetime" 
            placeholder="选择计划完成日期"
          ></el-date-picker>
        </el-form-item>

        <el-form-item label="预计时长(分钟)" prop="duration_minutes">
          <el-input-number v-model="newTaskForm.duration_minutes" :min="15" :step="15"></el-input-number>
        </el-form-item>

        <el-form-item label="优先级" prop="priority">
          <el-select v-model="newTaskForm.priority" placeholder="选择优先级">
            <el-option label="低" value="low"></el-option>
            <el-option label="普通" value="normal"></el-option>
            <el-option label="高" value="high"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="任务描述">
          <el-input 
            v-model="newTaskForm.description" 
            type="textarea" 
            placeholder="请输入任务描述"
            rows="3"
          ></el-input>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addTaskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createPersonalTask" :loading="savingTask">保存</el-button>
      </template>
    </el-dialog>

    <!-- 临期任务通知（右下角） -->
    <div class="upcoming-alert" v-if="upcomingTasks.length > 0">
      <div class="alert-header">
        <span>🔔 即将到期的任务</span>
        <el-button type="text" size="small" @click="showUpcomingAlert = false">×</el-button>
      </div>
      <div class="alert-content">
        <div v-for="task in upcomingTasks.slice(0, 3)" :key="`${task.type}-${task.id}`" class="alert-item">
          <span style="color: #d9534f; font-weight: bold;">⚠️</span>
          <span>{{ task.title }}</span>
          <span style="color: #909399; font-size: 12px;">还有 {{ getRemainingDays(task.planned_date) }} 天</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

// 数据
const teacherTasks = ref([])
const personalTasks = ref([])
const currentDate = ref(new Date())
const selectedTask = ref(null)
const selectedTaskType = ref(null)
const loading = ref(false)
const savingTask = ref(false)

// 对话框状态
const detailDialogVisible = ref(false)
const addTaskDialogVisible = ref(false)

// 视图模式
const viewMode = ref('calendar')

// 过滤选项
const showTeacherTasks = ref(true)
const showPersonalTasks = ref(true)
const taskTypeFilter = ref('all')
const completionFilter = ref('all')
const showUpcomingAlert = ref(true)

// 表单数据
const newTaskForm = ref({
  title: '',
  planned_date: null,
  duration_minutes: 60,
  priority: 'normal',
  description: ''
})

// 表单引用
const formRef = ref(null)

// 表单规则
const rules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  planned_date: [{ required: true, message: '请选择计划日期', trigger: 'change' }]
}

// 计算属性：计算即将到期的任务
const upcomingTasks = computed(() => {
  const now = new Date()
  const oneDay = 24 * 60 * 60 * 1000
  
  const allTasks = [
    ...teacherTasks.value.map(t => ({ 
      ...t, 
      type: 'teacher',
      planned_date: t.start || t.planned_date
    })),
    ...personalTasks.value.filter(t => !t.is_completed).map(t => ({ ...t, type: 'personal' }))
  ]
  
  return allTasks.filter(t => {
    try {
      const taskDate = new Date(t.planned_date)
      const daysUntil = (taskDate - now) / oneDay
      return daysUntil >= 0 && daysUntil <= 1
    } catch (e) {
      return false
    }
  }).sort((a, b) => new Date(a.planned_date) - new Date(b.planned_date))
})

// 计算属性：过滤后的任务列表
const filteredTasksList = computed(() => {
  let tasks = []
  const seen = new Set()
  
  if (taskTypeFilter.value === 'all' || taskTypeFilter.value === 'teacher') {
    teacherTasks.value.forEach(t => {
      // 使用更稳健的key生成方式
      const uniqueKey = `teacher-${t.id}-${String(t.start || t.planned_date).slice(0, 10)}`
      if (!seen.has(uniqueKey)) {
        // 规范化教师任务字段
        const normalized = {
          ...t,
          type: 'teacher',
          id: t.id || `teacher-${Math.random()}`,
          title: t.title || '',
          planned_date: t.start || t.planned_date,
          is_completed: false,
          color: t.color || '#909399',
          duration_minutes: t.extendedProps?.duration_minutes || t.duration_minutes || 0,
          description: t.extendedProps?.description || t.description || '',
          submission_status: t.extendedProps?.submission_status,
          class_name: t.extendedProps?.class_name,
          assignment_type: t.extendedProps?.type || 'deadline'
        }
        tasks.push(normalized)
        seen.add(uniqueKey)
      }
    })
  }
  
  if (taskTypeFilter.value === 'all' || taskTypeFilter.value === 'personal') {
    personalTasks.value.forEach(t => {
      // 使用更稳健的key生成方式
      const uniqueKey = `personal-${t.id}-${String(t.planned_date).slice(0, 10)}`
      if (!seen.has(uniqueKey)) {
        tasks.push({ ...t, type: 'personal' })
        seen.add(uniqueKey)
      }
    })
  }
  
  if (completionFilter.value === 'completed') {
    tasks = tasks.filter(t => t.is_completed)
  } else if (completionFilter.value === 'incomplete') {
    tasks = tasks.filter(t => !t.is_completed)
  }
  
  return tasks.sort((a, b) => new Date(a.planned_date) - new Date(b.planned_date))
})

// 加载教师任务
const fetchTeacherTasks = async () => {
  try {
    const res = await api.get('/schedule/events')
    // 过滤出只有教师相关的任务（排除个人任务）
    teacherTasks.value = (res.data || []).filter(task => {
      const type = task.extendedProps?.type || task.type
      return type !== 'personal_task' && !task.id?.startsWith('personal_task_')
    })
  } catch (err) {
    console.error('Failed to fetch teacher tasks', err)
  }
}

// 加载个人任务
const fetchPersonalTasks = async () => {
  try {
    const res = await api.get('/personal-tasks')
    personalTasks.value = res.data || []
  } catch (err) {
    console.error('Failed to fetch personal tasks', err)
  }
}

// 加载所有任务
const fetchAllTasks = async () => {
  loading.value = true
  try {
    await Promise.all([fetchTeacherTasks(), fetchPersonalTasks()])
  } finally {
    loading.value = false
  }
}

// 刷新日历显示
const refreshCalendar = () => {
  currentDate.value = new Date(currentDate.value)
}

// 获取指定日期的教师任务
const getTeacherTasksForDate = (dateStr) => {
  return teacherTasks.value.filter(t => {
    try {
      const taskDate = new Date(t.start).toISOString().split('T')[0]
      return taskDate === dateStr
    } catch (e) {
      return false
    }
  }).map(t => ({
    ...t,
    type: 'teacher',
    color: t.color || '#909399',
    title: t.title || '',
    id: t.id || `teacher-${Math.random()}`,
    planned_date: t.start || t.planned_date,
    is_completed: false,
    duration_minutes: t.extendedProps?.duration_minutes || t.duration_minutes || 0,
    description: t.extendedProps?.description || t.description || '',
    submission_status: t.extendedProps?.submission_status,
    class_name: t.extendedProps?.class_name,
    // 任务类型从 extendedProps 获取
    assignment_type: t.extendedProps?.type || 'deadline'
  }))
}

// 获取指定日期的个人任务
const getPersonalTasksForDate = (dateStr) => {
  return personalTasks.value.filter(t => {
    const taskDate = new Date(t.planned_date).toISOString().split('T')[0]
    return taskDate === dateStr
  })
}

// 打开任务详情
const openTaskDetail = (task, type) => {
  selectedTask.value = task
  selectedTaskType.value = type
  detailDialogVisible.value = true
}

// 打开添加任务对话框
const openAddTaskDialog = () => {
  resetForm()
  addTaskDialogVisible.value = true
}

// 创建个人任务
const createPersonalTask = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    savingTask.value = true
    
    const payload = {
      title: newTaskForm.value.title,
      planned_date: newTaskForm.value.planned_date.toISOString(),
      duration_minutes: newTaskForm.value.duration_minutes,
      priority: newTaskForm.value.priority,
      description: newTaskForm.value.description
    }
    
    await api.post('/personal-tasks', payload)
    ElMessage.success('任务添加成功')
    addTaskDialogVisible.value = false
    await fetchPersonalTasks()
  } catch (err) {
    console.error('Failed to create personal task', err)
    ElMessage.error('添加任务失败')
  } finally {
    savingTask.value = false
  }
}

// 标记任务完成/未完成
const toggleTaskComplete = async (task) => {
  // 使用 selectedTaskType 来判断任务类型（更可靠）
  // 或者检查 task.type 字段
  const taskType = selectedTaskType.value || task.type
  if (taskType !== 'personal') {
    ElMessage.warning('只能标记个人任务为完成')
    return
  }
  
  try {
    const payload = {
      is_completed: !task.is_completed
    }
    
    await api.put(`/personal-tasks/${task.id}`, payload)
    ElMessage.success(task.is_completed ? '已取消完成' : '已标记完成')
    
    // 更新两个数组中的任务状态，确保日历和列表都会更新
    const idx = personalTasks.value.findIndex(t => t.id === task.id)
    if (idx !== -1) {
      personalTasks.value[idx].is_completed = !personalTasks.value[idx].is_completed
      if (personalTasks.value[idx].is_completed) {
        personalTasks.value[idx].completed_at = new Date().toISOString()
      } else {
        personalTasks.value[idx].completed_at = null
      }
      // 更新选中的任务对象
      if (selectedTask.value && selectedTask.value.id === task.id) {
        selectedTask.value.is_completed = !selectedTask.value.is_completed
        selectedTask.value.completed_at = personalTasks.value[idx].completed_at
      }
    }
    
    // 关闭对话框后刷新一下，确保UI更新
    setTimeout(() => {
      detailDialogVisible.value = false
    }, 100)
  } catch (err) {
    console.error('Failed to toggle task', err)
    ElMessage.error('更新任务失败')
  }
}

// 删除个人任务
const deleteTask = async (task) => {
  if (task.type !== 'personal') return
  
  try {
    await ElMessageBox.confirm(
      '确定删除此任务吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.delete(`/personal-tasks/${task.id}`)
    ElMessage.success('任务已删除')
    await fetchPersonalTasks()
  } catch (err) {
    if (err?.message !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

// 重置表单
const resetForm = () => {
  newTaskForm.value = {
    title: '',
    planned_date: null,
    duration_minutes: 60,
    priority: 'normal',
    description: ''
  }
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      return '日期格式错误'
    }
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return '日期格式错误'
  }
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      return '日期格式错误'
    }
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (e) {
    return '日期格式错误'
  }
}

// 格式化任务类型
const formatTaskType = (type) => {
  const map = { 
    homework: '作业', 
    exam: '考试',
    deadline: '截止日期',
    teaching_plan: '教学计划'
  }
  return map[type] || type
}

// 格式化提交状态
const formatSubmissionStatus = (status) => {
  const map = {
    submitted: '已提交',
    graded: '已批改',
    unsubmitted: '未提交'
  }
  return map[status] || status
}

// 获取优先级的UI类型
const getPriorityType = (priority) => {
  const map = { low: 'info', normal: 'warning', high: 'danger' }
  return map[priority] || 'info'
}

// 获取优先级的文本
const getPriorityText = (priority) => {
  const map = { low: '低优先级', normal: '普通', high: '高优先级' }
  return map[priority] || priority
}

// 计算剩余天数
const getRemainingDays = (dateStr) => {
  const now = new Date()
  const taskDate = new Date(dateStr)
  const diff = Math.ceil((taskDate - now) / (1000 * 60 * 60 * 24))
  return diff
}

// 初始化
onMounted(() => {
  fetchAllTasks()
  setInterval(() => {
    if (upcomingTasks.value.length > 0) {
      showUpcomingAlert.value = true
    }
  }, 60000)
})
</script>

<style scoped>
.schedule-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.legend {
  display: flex;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.legend-item {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 2px;
}

.calendar-view {
  padding: 20px 0;
}

.date-cell-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 4px;
}

.date-cell-content p {
  margin: 0 0 5px 0;
  font-weight: bold;
  color: #333;
  font-size: 13px;
}

.date-cell-content p.is-today {
  color: #409eff;
}

.events-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-item {
  padding: 4px 6px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
  display: flex;
  gap: 4px;
  align-items: center;
  transition: all 0.3s;
  color: white;
}

.event-item:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.event-item.teacher-task {
  border-left: 2px solid rgba(255, 255, 255, 0.5);
}

.event-item.personal-task {
  border-left: 2px dashed rgba(255, 255, 255, 0.7);
}

.task-icon {
  flex-shrink: 0;
}

.task-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-view {
  padding: 20px 0;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-item-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.task-date-label {
  min-width: 100px;
  padding-top: 12px;
  color: #909399;
  font-size: 12px;
  font-weight: 600;
  text-align: right;
}

.task-card {
  flex: 1;
  cursor: pointer;
  transition: all 0.3s;
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.upcoming-alert {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 300px;
  background-color: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(350px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  font-weight: bold;
  color: #d9534f;
}

.alert-content {
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  gap: 8px;
  padding: 8px;
  margin-bottom: 8px;
  background-color: #fef0f0;
  border-radius: 4px;
  font-size: 13px;
  align-items: center;
}

.alert-item span:nth-child(2) {
  flex: 1;
}

.alert-item span:nth-child(3) {
  text-align: right;
}
</style>
