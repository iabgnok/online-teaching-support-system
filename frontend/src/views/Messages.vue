<template>
  <div>
    <h2>站内信</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="收件箱" name="inbox">
        <el-table :data="inbox" style="width: 100%">
          <el-table-column prop="sender_name" label="发件人" width="180" />
          <el-table-column prop="content" label="内容" />
          <el-table-column prop="created_at" label="时间" width="180" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-tag v-if="scope.row.is_read" type="success">已读</el-tag>
              <el-button v-else size="small" @click="markAsRead(scope.row)">标记已读</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="发件箱" name="sent">
        <el-table :data="sent" style="width: 100%">
           <el-table-column prop="recipient_name" label="收件人" width="180" />
           <el-table-column prop="content" label="内容" />
           <el-table-column prop="created_at" label="时间" width="180" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="写信" name="compose">
        <el-form label-width="100px">
          <el-form-item label="收件人">
             <el-select 
               v-model="newMessage.recipient_id" 
               filterable 
               remote
               reserve-keyword
               placeholder="输入姓名或用户名搜索"
               :remote-method="searchUsers"
               :loading="searchLoading"
               style="width: 100%"
             >
               <el-option
                 v-for="user in userList"
                 :key="user.id"
                 :label="`${user.real_name} (${user.username})`"
                 :value="user.id"
               >
                 <span style="float: left">{{ user.real_name }}</span>
                 <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                   {{ user.username }} 
                   <el-tag size="small" :type="user.role === 'teacher' ? 'success' : 'info'">
                     {{ user.role === 'teacher' ? '教师' : user.role === 'student' ? '学生' : '管理员' }}
                   </el-tag>
                 </span>
               </el-option>
             </el-select>
          </el-form-item>
          <el-form-item label="内容">
             <el-input type="textarea" v-model="newMessage.content" :rows="6" placeholder="请输入消息内容"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="sendMessage">发送</el-button>
            <el-button @click="resetForm">清空</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const activeTab = ref('inbox')
const inbox = ref([])
const sent = ref([])
const newMessage = ref({ recipient_id: '', content: '' })
const userList = ref([])
const searchLoading = ref(false)

const fetchMessages = async () => {
  try {
    const resInbox = await api.get('/messages')
    inbox.value = resInbox.data
    const resSent = await api.get('/messages/sent')
    sent.value = resSent.data
  } catch (e) {
    console.error(e)
  }
}

const searchUsers = async (query) => {
  if (query && query.length >= 2) {
    searchLoading.value = true
    try {
      const res = await api.get('/users/search', { params: { q: query } })
      userList.value = res.data
    } catch (e) {
      console.error('Search users error:', e)
      userList.value = []
    } finally {
      searchLoading.value = false
    }
  } else {
    userList.value = []
  }
}

const markAsRead = async (msg) => {
  try {
    await api.put(`/messages/${msg.id}/read`)
    msg.is_read = true
  } catch(e) {
    ElMessage.error('标记失败')
  }
}

const resetForm = () => {
  newMessage.value.recipient_id = ''
  newMessage.value.content = ''
  userList.value = []
}

const sendMessage = async () => {
    if (!newMessage.value.recipient_id || !newMessage.value.content) {
        ElMessage.warning('请选择收件人并填写内容')
        return
    }
    
    try {
        await api.post('/messages', {
            recipient_id: newMessage.value.recipient_id,
            content: newMessage.value.content
        })
        ElMessage.success('发送成功!')
        resetForm()
        fetchMessages()
        activeTab.value = 'sent'
    } catch(e) {
        const errorMsg = e.response?.data?.error || '发送失败'
        ElMessage.error(errorMsg)
        console.error('Send message error:', e.response?.data)
    }
}

onMounted(fetchMessages)
</script>
