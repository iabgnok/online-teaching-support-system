<template>
  <div class="user-table">
    <div class="table-header">
      <div class="table-title">
        <h3>用户管理</h3>
        <span class="user-count">共 {{ users.length }} 个用户</span>
      </div>
      <div class="table-actions">
        <BaseInput
          v-model="searchQuery"
          placeholder="搜索用户..."
          style="width: 200px;"
        />
        <BaseButton type="primary" @click="$emit('add-user')">
          添加用户
        </BaseButton>
      </div>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>用户名</th>
            <th>姓名</th>
            <th>角色</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.name }}</td>
            <td>
              <span class="role-badge" :class="`role-${user.role}`">
                {{ getRoleName(user.role) }}
              </span>
            </td>
            <td>{{ user.email || '-' }}</td>
            <td>
              <span class="status-badge" :class="`status-${user.status}`">
                {{ getStatusName(user.status) }}
              </span>
            </td>
            <td>{{ formatDate(user.createdAt) }}</td>
            <td class="actions">
              <BaseButton
                size="small"
                type="secondary"
                @click="$emit('edit-user', user)"
              >
                编辑
              </BaseButton>
              <BaseButton
                size="small"
                :type="user.status === 'active' ? 'danger' : 'success'"
                @click="toggleUserStatus(user)"
              >
                {{ user.status === 'active' ? '禁用' : '启用' }}
              </BaseButton>
              <BaseButton
                size="small"
                type="danger"
                @click="$emit('delete-user', user)"
              >
                删除
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="filteredUsers.length === 0" class="empty-state">
      <p>暂无用户数据</p>
    </div>
  </div>
</template>

<script>
import BaseInput from '../common/ui/BaseInput.vue'
import BaseButton from '../common/ui/BaseButton.vue'

export default {
  name: 'UserTable',
  components: {
    BaseInput,
    BaseButton
  },
  props: {
    users: {
      type: Array,
      default: () => []
    }
  },
  emits: ['add-user', 'edit-user', 'delete-user', 'toggle-status'],
  data() {
    return {
      searchQuery: ''
    }
  },
  computed: {
    filteredUsers() {
      if (!this.searchQuery.trim()) {
        return this.users
      }

      const query = this.searchQuery.toLowerCase()
      return this.users.filter(user =>
        user.username.toLowerCase().includes(query) ||
        user.name.toLowerCase().includes(query) ||
        user.email?.toLowerCase().includes(query)
      )
    }
  },
  methods: {
    getRoleName(role) {
      const roleMap = {
        admin: '管理员',
        teacher: '教师',
        student: '学生'
      }
      return roleMap[role] || role
    },

    getStatusName(status) {
      const statusMap = {
        active: '正常',
        inactive: '禁用',
        pending: '待激活'
      }
      return statusMap[status] || status
    },

    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN')
    },

    toggleUserStatus(user) {
      const newStatus = user.status === 'active' ? 'inactive' : 'active'
      this.$emit('toggle-status', { user, newStatus })
    }
  }
}
</script>

<style scoped>
.user-table {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.table-title h3 {
  margin: 0 0 4px 0;
  color: #333;
}

.user-count {
  color: #666;
  font-size: 14px;
}

.table-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background-color: #f8f9fa;
}

th, td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

td {
  font-size: 14px;
  color: #555;
}

.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-admin {
  background-color: #dc3545;
  color: white;
}

.role-teacher {
  background-color: #28a745;
  color: white;
}

.role-student {
  background-color: #007bff;
  color: white;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background-color: #28a745;
  color: white;
}

.status-inactive {
  background-color: #dc3545;
  color: white;
}

.status-pending {
  background-color: #ffc107;
  color: #212529;
}

.actions {
  display: flex;
  gap: 6px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state p {
  margin: 0;
  font-size: 16px;
}
</style>