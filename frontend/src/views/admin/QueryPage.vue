<template>
  <div class="query-page">
    <el-card>
      <template #header>
        <h2>📊 数据查询与统计</h2>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 用户查询 -->
        <el-tab-pane label="用户查询" name="users">
          <el-form :inline="true" :model="userQuery">
            <el-form-item label="用户名">
              <el-input v-model="userQuery.username" placeholder="模糊搜索" />
            </el-form-item>
            <el-form-item label="真实姓名">
              <el-input v-model="userQuery.real_name" placeholder="模糊搜索" />
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="userQuery.role" clearable placeholder="全部">
                <el-option label="管理员" value="admin" />
                <el-option label="教师" value="teacher" />
                <el-option label="学生" value="student" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="queryUsers">查询</el-button>
              <el-button icon="Download" @click="exportUsers">导出</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="userResults" v-loading="loading" stripe max-height="500">
            <el-table-column prop="user_id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="real_name" label="真实姓名" width="120" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="scope">
                <el-tag :type="getRoleType(scope.row.role)">
                  {{ getRoleLabel(scope.row.role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="phone" label="电话" width="130" />
            <el-table-column prop="email" label="邮箱" min-width="180" />
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="scope">
                <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'" size="small">
                  {{ scope.row.status === 1 ? '激活' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 课程查询 -->
        <el-tab-pane label="课程查询" name="courses">
          <el-form :inline="true" :model="courseQuery">
            <el-form-item label="课程代码">
              <el-input v-model="courseQuery.course_code" placeholder="模糊搜索" />
            </el-form-item>
            <el-form-item label="课程名称">
              <el-input v-model="courseQuery.course_name" placeholder="模糊搜索" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="queryCourses">查询</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="courseResults" v-loading="loading" stripe max-height="500">
            <el-table-column prop="course_id" label="ID" width="80" />
            <el-table-column prop="course_code" label="课程代码" width="120" />
            <el-table-column prop="course_name" label="课程名称" min-width="200" />
            <el-table-column prop="credits" label="学分" width="80" align="center" />
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <!-- 统计报表 -->
        <el-tab-pane label="统计报表" name="stats">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-card shadow="hover">
                <template #header>
                  <span>👥 用户统计（按院系）</span>
                </template>
                <el-table :data="userStats" stripe max-height="400">
                  <el-table-column prop="dept_name" label="院系" />
                  <el-table-column prop="admin_count" label="管理员" width="90" align="center" />
                  <el-table-column prop="teacher_count" label="教师" width="90" align="center" />
                  <el-table-column prop="student_count" label="学生" width="90" align="center" />
                  <el-table-column label="合计" width="90" align="center">
                    <template #default="scope">
                      {{ scope.row.total_count }}
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>

            <el-col :span="12">
              <el-card shadow="hover">
                <template #header>
                  <span>📚 课程统计</span>
                </template>
                <el-table :data="courseStats" stripe max-height="400">
                  <el-table-column prop="course_name" label="课程名称" show-overflow-tooltip />
                  <el-table-column prop="teaching_class_count" label="教学班" width="90" align="center" />
                  <el-table-column prop="total_student_count" label="学生数" width="90" align="center" />
                  <el-table-column prop="assignment_count" label="作业数" width="90" align="center" />
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import api from '@/api'

const activeTab = ref('users')
const loading = ref(false)

const userQuery = reactive({
  username: '',
  real_name: '',
  role: '',
  status: null
})

const courseQuery = reactive({
  course_code: '',
  course_name: ''
})

const userResults = ref([])
const courseResults = ref([])
const userStats = ref([])
const courseStats = ref([])

// 查询用户
const queryUsers = async () => {
  loading.value = true
  try {
    const response = await api.post('/admin/query/users', userQuery)
    userResults.value = response.data.results
    ElMessage.success(`找到 ${userResults.value.length} 条记录`)
  } catch (error) {
    console.error('Failed to query users:', error)
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

// 查询课程
const queryCourses = async () => {
  loading.value = true
  try {
    const response = await api.post('/admin/query/courses', courseQuery)
    courseResults.value = response.data.results
    ElMessage.success(`找到 ${courseResults.value.length} 条记录`)
  } catch (error) {
    console.error('Failed to query courses:', error)
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

// 导出用户
const exportUsers = () => {
  const params = new URLSearchParams(userQuery).toString()
  window.open(`/api/v1/admin/export/users?${params}`, '_blank')
}

// 加载统计数据
const loadStats = async () => {
  try {
    const [userStatsRes, courseStatsRes] = await Promise.all([
      api.get('/admin/stats/users'),
      api.get('/admin/stats/courses')
    ])
    userStats.value = userStatsRes.data.stats
    courseStats.value = courseStatsRes.data.stats
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const getRoleLabel = (role) => {
  const labels = { admin: '管理员', teacher: '教师', student: '学生' }
  return labels[role] || role
}

const getRoleType = (role) => {
  const types = { admin: 'danger', teacher: 'warning', student: 'success' }
  return types[role] || 'info'
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.query-page {
  padding: 20px;
}

h2 {
  margin: 0;
  font-size: 20px;
}
</style>
