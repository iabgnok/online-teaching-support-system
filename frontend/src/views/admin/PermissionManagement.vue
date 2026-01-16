<template>
  <div class="permission-management">
    <el-card>
      <template #header>
        <div class="header">
          <h2>🔑 权限管理</h2>
        </div>
      </template>

      <!-- 权限等级说明 -->
      <div class="section">
        <h3>权限等级说明</h3>
        <el-table :data="permissionLevels" stripe size="small">
          <el-table-column prop="level" label="等级" width="80"></el-table-column>
          <el-table-column prop="name" label="名称" width="120"></el-table-column>
          <el-table-column prop="description" label="描述"></el-table-column>
        </el-table>
      </div>

      <!-- 管理员列表 -->
      <div class="section" style="margin-top: 30px">
        <h3>管理员权限管理</h3>
        
        <div class="filter-bar">
          <el-form :inline="true" :model="filters">
            <el-form-item label="权限等级">
              <el-select 
                v-model="filters.permission_level" 
                placeholder="全部" 
                clearable 
                @change="loadAdmins"
              >
                <el-option label="1级 - 超级管理员" :value="1" />
                <el-option label="2级 - 系统管理员" :value="2" />
                <el-option label="3级 - 部门管理员" :value="3" />
                <el-option label="4级 - 内容审核员" :value="4" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadAdmins" icon="Search">搜索</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="adminList" v-loading="loading" stripe>
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="real_name" label="真实姓名" width="120" />
          
          <el-table-column label="权限等级" width="140">
            <template #default="scope">
              <el-tag :type="getLevelType(scope.row.permission_level)">
                {{ getLevelName(scope.row.permission_level) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="功能权限" min-width="200">
            <template #default="scope">
              <div class="permission-badges">
                <el-tag v-if="scope.row.can_manage_users" type="info" size="small">用户管理</el-tag>
                <el-tag v-if="scope.row.can_manage_forum" type="info" size="small">论坛管理</el-tag>
                <el-tag v-if="scope.row.can_manage_courses" type="info" size="small">课程管理</el-tag>
                <el-tag v-if="scope.row.can_manage_announcements" type="info" size="small">公告管理</el-tag>
                <el-tag v-if="scope.row.can_review_content" type="info" size="small">内容审核</el-tag>
                <el-tag v-if="scope.row.can_manage_grades" type="info" size="small">成绩管理</el-tag>
                <el-tag v-if="scope.row.can_manage_attendance" type="info" size="small">考勤管理</el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button type="primary" size="small" @click="openEdit(scope.row)">
                编辑
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div style="margin-top: 20px; text-align: right;">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
            @change="loadAdmins"
          ></el-pagination>
        </div>
      </div>
    </el-card>

    <!-- 编辑权限对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑权限" width="500px">
      <el-form v-if="editingAdmin" :model="editingAdmin" label-width="100px">
        <el-form-item label="用户名">
          <span>{{ editingAdmin.username }}</span>
        </el-form-item>
        
        <el-form-item label="权限等级">
          <el-radio-group v-model="editingAdmin.permission_level">
            <el-radio :label="1">1级 - 超级管理员</el-radio>
            <el-radio :label="2">2级 - 系统管理员</el-radio>
            <el-radio :label="3">3级 - 部门管理员</el-radio>
            <el-radio :label="4">4级 - 内容审核员</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="功能权限">
          <div class="permission-checkboxes">
            <el-checkbox v-model="editingAdmin.can_manage_users">用户管理</el-checkbox>
            <el-checkbox v-model="editingAdmin.can_manage_forum">论坛管理</el-checkbox>
            <el-checkbox v-model="editingAdmin.can_manage_courses">课程管理</el-checkbox>
            <el-checkbox v-model="editingAdmin.can_manage_announcements">公告管理</el-checkbox>
            <el-checkbox v-model="editingAdmin.can_review_content">内容审核</el-checkbox>
            <el-checkbox v-model="editingAdmin.can_manage_grades">成绩管理</el-checkbox>
            <el-checkbox v-model="editingAdmin.can_manage_attendance">考勤管理</el-checkbox>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="savePermissions" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const adminList = ref([])
const loading = ref(false)
const saving = ref(false)
const showEditDialog = ref(false)
const editingAdmin = ref(null)

const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const filters = ref({ permission_level: null })

const permissionLevels = [
  { level: 1, name: '超级管理员', description: '拥有系统的所有权限' },
  { level: 2, name: '系统管理员', description: '拥有几乎所有权限' },
  { level: 3, name: '部门管理员', description: '管理部门内容' },
  { level: 4, name: '内容审核员', description: '进行内容审核' }
]

const getLevelName = (level) => {
  const names = { 1: '超级管理员', 2: '系统管理员', 3: '部门管理员', 4: '内容审核员' }
  return names[level] || '-'
}

const getLevelType = (level) => {
  const types = { 1: 'danger', 2: 'warning', 3: 'primary', 4: 'info' }
  return types[level] || 'info'
}

const loadAdmins = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value
    }
    if (filters.value.permission_level) {
      params.permission_level = filters.value.permission_level
    }
    const response = await api.get('/admin/admins', { params })
    adminList.value = response.data.admins || []
    totalCount.value = response.data.total || 0
  } catch (error) {
    ElMessage.error('加载管理员列表失败')
  } finally {
    loading.value = false
  }
}

const openEdit = (admin) => {
  editingAdmin.value = { ...admin }
  showEditDialog.value = true
}

const savePermissions = async () => {
  saving.value = true
  try {
    await api.put(`/admin/admins/${editingAdmin.value.admin_id}/permissions`, editingAdmin.value)
    ElMessage.success('权限保存成功')
    showEditDialog.value = false
    loadAdmins()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadAdmins()
})
</script>

<style scoped>
.permission-management {
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
  font-weight: 600;
}

.section {
  margin-top: 20px;
}

.section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.filter-bar {
  margin-bottom: 20px;
}

.permission-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.permission-checkboxes {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
</style>
