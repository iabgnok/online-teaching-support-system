<template>
  <el-popover
    placement="bottom"
    :width="300"
    trigger="click"
    @show="loadStatus"
  >
    <template #reference>
      <span class="read-status" @click.stop>
        <el-icon v-if="loading"><Loading /></el-icon>
        <template v-else>
          <el-icon v-if="readCount === totalCount" color="#67c23a"><CircleCheck /></el-icon>
          <el-icon v-else color="#909399"><CircleCheck /></el-icon>
          <span class="status-text">{{ readCount }}/{{ totalCount }}已读</span>
        </template>
      </span>
    </template>

    <div v-loading="loading" class="status-container">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="已读" :name="'read'">
          <div v-if="readUsers.length === 0" class="empty-state">
            <el-empty description="暂无已读" :image-size="60" />
          </div>
          <div v-else class="user-list">
            <div 
              v-for="user in readUsers" 
              :key="user.user_id"
              class="user-item"
            >
              <div class="user-info">
                <el-avatar :size="32">{{ user.real_name[0] }}</el-avatar>
                <div class="user-name">
                  <div>{{ user.real_name }}</div>
                  <div class="user-role">{{ getRoleText(user.role) }}</div>
                </div>
              </div>
              <div class="read-time">{{ formatTime(user.read_at) }}</div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="`未读(${unreadUsers.length})`" :name="'unread'">
          <div v-if="unreadUsers.length === 0" class="empty-state">
            <el-empty description="全部已读" :image-size="60" />
          </div>
          <div v-else class="user-list">
            <div 
              v-for="user in unreadUsers" 
              :key="user.user_id"
              class="user-item"
            >
              <div class="user-info">
                <el-avatar :size="32">{{ user.real_name[0] }}</el-avatar>
                <div class="user-name">
                  <div>{{ user.real_name }}</div>
                  <div class="user-role">{{ getRoleText(user.role) }}</div>
                </div>
              </div>
              <el-tag size="small" type="warning">未读</el-tag>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-popover>
</template>

<script>
import api from '../../api'
import { CircleCheck, Loading } from '@element-plus/icons-vue'

export default {
  name: 'MessageStatusPopover',
  components: {
    CircleCheck,
    Loading
  },
  props: {
    messageId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      loading: false,
      activeTab: 'read',
      readUsers: [],
      unreadUsers: [],
      readCount: 0,
      totalCount: 0
    }
  },
  methods: {
    async loadStatus() {
      this.loading = true
      try {
        const response = await api.get(`/chat/messages/${this.messageId}/status`)
        if (response.data.code === 200) {
          const data = response.data.data
          this.readUsers = data.read_users || []
          this.unreadUsers = data.unread_users || []
          this.readCount = data.read_count || 0
          this.totalCount = this.readCount + (data.unread_count || 0)
        }
      } catch (error) {
        this.$message.error('获取消息状态失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    getRoleText(role) {
      const roleMap = {
        'teacher': '教师',
        'student': '学生',
        'admin': '管理员'
      }
      return roleMap[role] || role
    },
    formatTime(timeStr) {
      if (!timeStr) return ''
      const time = new Date(timeStr)
      const now = new Date()
      const diff = now - time
      
      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
      
      return time.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.read-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #909399;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
}

.read-status:hover {
  background-color: #f5f7fa;
  color: #606266;
}

.status-text {
  margin-left: 2px;
}

.status-container {
  min-height: 200px;
}

.user-list {
  max-height: 300px;
  overflow-y: auto;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.user-item:last-child {
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.user-name {
  font-size: 13px;
}

.user-role {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.read-time {
  font-size: 11px;
  color: #c0c4cc;
}

.empty-state {
  padding: 20px 0;
  text-align: center;
}
</style>
