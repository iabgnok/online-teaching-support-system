<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="header">
          <h2>👥 用户管理</h2>
          <el-button type="primary" icon="Plus" @click="showCreateDialog = true">
            创建用户
          </el-button>
        </div>
      </template>

      <!-- 筛选搜索栏 -->
      <div class="filter-bar">
        <el-form :inline="true" :model="filters">
          <el-form-item label="角色">
            <el-select v-model="filters.role" placeholder="全部角色" clearable @change="loadUsers">
              <el-option label="管理员" value="admin" />
              <el-option label="教师" value="teacher" />
              <el-option label="学生" value="student" />
            </el-select>
          </el-form-item>

          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="全部状态" clearable @change="loadUsers">
              <el-option label="激活" :value="1" />
              <el-option label="禁用" :value="0" />
            </el-select>
          </el-form-item>

          <el-form-item label="姓名">
            <el-input
              v-model="filters.search_name"
              placeholder="搜索姓名"
              clearable
              @clear="loadUsers"
              @keyup.enter="loadUsers"
            />
          </el-form-item>

          <el-form-item label="用户名">
            <el-input
              v-model="filters.search_username"
              placeholder="搜索用户名"
              clearable
              @clear="loadUsers"
              @keyup.enter="loadUsers"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" icon="Search" @click="loadUsers">搜索</el-button>
            <el-button icon="Refresh" @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 用户表格 -->
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="user_id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="真实姓名" width="120" />
        
        <el-table-column label="角色" width="100">
          <template #default="scope">
            <el-tag :type="getRoleType(scope.row.role)">
              {{ getRoleLabel(scope.row.role) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="角色信息" min-width="180">
          <template #default="scope">
            <div v-if="scope.row.role === 'admin' && scope.row.admin">
              编号: {{ scope.row.admin.admin_no }} | 
              权限: Level {{ scope.row.admin.permission_level }}
              <div v-if="scope.row.admin.dept_name" class="dept-info">
                {{ scope.row.admin.dept_name }}
              </div>
            </div>
            <div v-else-if="scope.row.role === 'teacher' && scope.row.teacher">
              工号: {{ scope.row.teacher.teacher_no }}
              <span v-if="scope.row.teacher.title"> | {{ scope.row.teacher.title }}</span>
              <div v-if="scope.row.teacher.dept_name" class="dept-info">
                {{ scope.row.teacher.dept_name }}
              </div>
            </div>
            <div v-else-if="scope.row.role === 'student' && scope.row.student">
              学号: {{ scope.row.student.student_no }}
              <span v-if="scope.row.student.major"> | {{ scope.row.student.major }}</span>
              <div v-if="scope.row.student.dept_name" class="dept-info">
                {{ scope.row.student.dept_name }}
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'" size="small">
              {{ scope.row.status === 1 ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="email" label="邮箱" width="180" show-overflow-tooltip />

        <el-table-column label="操作" width="260" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" text @click="editUser(scope.row)">
              编辑
            </el-button>
            <el-button 
              size="small" 
              :type="scope.row.status === 1 ? 'warning' : 'success'" 
              text
              @click="toggleStatus(scope.row)"
            >
              {{ scope.row.status === 1 ? '禁用' : '激活' }}
            </el-button>
            <el-popconfirm
              title="确定要删除此用户吗？此操作不可恢复！"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="deleteUser(scope.row.user_id)"
            >
              <template #reference>
                <el-button size="small" type="danger" text>
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingUser ? '编辑用户' : '创建用户'" 
      width="600px"
      @close="resetForm"
    >
      <el-form :model="userForm" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码" :prop="editingUser ? '' : 'password'">
          <el-input 
            v-model="userForm.password" 
            type="password" 
            :placeholder="editingUser ? '留空则不修改' : '请输入密码'" 
            show-password
          />
        </el-form-item>

        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="userForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" :disabled="!!editingUser">
            <el-option label="管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>

        <!-- 管理员特定字段 -->
        <template v-if="userForm.role === 'admin'">
          <el-form-item label="管理员编号" prop="admin_no">
            <el-input v-model="userForm.admin_no" placeholder="请输入管理员编号" />
          </el-form-item>
          <el-form-item label="权限等级" prop="permission_level">
            <el-select v-model="userForm.permission_level" placeholder="请选择权限等级">
              <el-option label="一级（最高）" :value="1" />
              <el-option label="二级（中等）" :value="2" />
              <el-option label="三级（普通）" :value="3" />
            </el-select>
          </el-form-item>
        </template>

        <!-- 教师特定字段 -->
        <template v-if="userForm.role === 'teacher'">
          <el-form-item label="教师工号" prop="teacher_no">
            <el-input v-model="userForm.teacher_no" placeholder="请输入教师工号" />
          </el-form-item>
          <el-form-item label="职称">
            <el-input v-model="userForm.title" placeholder="如：教授、副教授等" />
          </el-form-item>
        </template>

        <!-- 学生特定字段 -->
        <template v-if="userForm.role === 'student'">
          <el-form-item label="学生学号" prop="student_no">
            <el-input v-model="userForm.student_no" placeholder="请输入学生学号" />
          </el-form-item>
          <el-form-item label="专业">
            <el-input v-model="userForm.major" placeholder="请输入专业" />
          </el-form-item>
        </template>

        <el-form-item label="院系">
          <el-select v-model="userForm.dept_id" placeholder="请选择院系" filterable clearable>
            <el-option 
              v-for="dept in departments" 
              :key="dept.dept_id" 
              :label="dept.dept_name" 
              :value="dept.dept_id" 
            />
          </el-select>
        </el-form-item>

        <el-form-item label="电话">
          <el-input v-model="userForm.phone" placeholder="请输入电话号码" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="请输入邮箱地址" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ editingUser ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import api from '@/api'

const loading = ref(false)
const users = ref([])
const departments = ref([])
const showCreateDialog = ref(false)
const editingUser = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const filters = reactive({
  role: '',
  status: '',
  search_name: '',
  search_username: ''
})

const pagination = reactive({
  page: 1,
  per_page: 20,
  total: 0
})

const userForm = reactive({
  username: '',
  password: '',
  real_name: '',
  role: '',
  phone: '',
  email: '',
  dept_id: null,
  admin_no: '',
  permission_level: 3,
  teacher_no: '',
  title: '',
  student_no: '',
  major: ''
})

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  admin_no: [{ required: true, message: '请输入管理员编号', trigger: 'blur' }],
  teacher_no: [{ required: true, message: '请输入教师工号', trigger: 'blur' }],
  student_no: [{ required: true, message: '请输入学生学号', trigger: 'blur' }]
}

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.per_page,
      ...filters
    }
    const response = await api.get('/admin/users', { params })
    users.value = response.data.users
    pagination.total = response.data.pagination.total
  } catch (error) {
    console.error('Failed to load users:', error)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 加载院系列表
const loadDepartments = async () => {
  try {
    const response = await api.get('/admin/departments')
    departments.value = response.data.departments
  } catch (error) {
    console.error('Failed to load departments:', error)
  }
}

// 重置筛选
const resetFilters = () => {
  filters.role = ''
  filters.status = ''
  filters.search_name = ''
  filters.search_username = ''
  pagination.page = 1
  loadUsers()
}

// 获取角色标签
const getRoleLabel = (role) => {
  const labels = { admin: '管理员', teacher: '教师', student: '学生' }
  return labels[role] || role
}

// 获取角色类型
const getRoleType = (role) => {
  const types = { admin: 'danger', teacher: 'warning', student: 'success' }
  return types[role] || 'info'
}

// 编辑用户
const editUser = (user) => {
  editingUser.value = user
  
  let deptId = null
  if (user.role === 'admin' && user.admin) {
    deptId = user.admin.dept_id
  } else if (user.role === 'teacher' && user.teacher) {
    deptId = user.teacher.dept_id
  } else if (user.role === 'student' && user.student) {
    deptId = user.student.dept_id
  }
  
  Object.assign(userForm, {
    username: user.username,
    password: '',
    real_name: user.real_name,
    role: user.role,
    phone: user.phone || '',
    email: user.email || '',
    dept_id: deptId,
    admin_no: user.admin?.admin_no || '',
    permission_level: user.admin?.permission_level || 3,
    teacher_no: user.teacher?.teacher_no || '',
    title: user.teacher?.title || '',
    student_no: user.student?.student_no || '',
    major: user.student?.major || ''
  })
  
  showCreateDialog.value = true
}

// 切换用户状态
const toggleStatus = async (user) => {
  try {
    await api.post(`/admin/users/${user.user_id}/toggle-status`)
    ElMessage.success(user.status === 1 ? '已禁用用户' : '已激活用户')
    loadUsers()
  } catch (error) {
    console.error('Failed to toggle user status:', error)
    ElMessage.error(error.response?.data?.error || '操作失败')
  }
}

// 删除用户
const deleteUser = async (userId) => {
  try {
    await api.delete(`/admin/users/${userId}`)
    ElMessage.success('用户已删除')
    loadUsers()
  } catch (error) {
    console.error('Failed to delete user:', error)
    ElMessage.error(error.response?.data?.error || '删除失败')
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (editingUser.value) {
        // 更新用户
        await api.put(`/admin/users/${editingUser.value.user_id}`, userForm)
        ElMessage.success('用户信息已更新')
      } else {
        // 创建用户
        await api.post('/admin/users', userForm)
        ElMessage.success('用户创建成功')
      }
      
      showCreateDialog.value = false
      loadUsers()
    } catch (error) {
      console.error('Failed to submit form:', error)
      ElMessage.error(error.response?.data?.error || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  editingUser.value = null
  Object.assign(userForm, {
    username: '',
    password: '',
    real_name: '',
    role: '',
    phone: '',
    email: '',
    dept_id: null,
    admin_no: '',
    permission_level: 3,
    teacher_no: '',
    title: '',
    student_no: '',
    major: ''
  })
  formRef.value?.resetFields()
}

onMounted(() => {
  loadUsers()
  loadDepartments()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h2 {
  margin: 0;
  font-size: 20px;
}

.filter-bar {
  margin-bottom: 20px;
  padding: 15px;
  background: #F5F7FA;
  border-radius: 4px;
}

.dept-info {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
