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
        <el-form label-width="80px">
          <el-form-item label="收件人ID">
             <el-input v-model="newMessage.recipient_id" placeholder="用户ID"></el-input>
          </el-form-item>
          <el-form-item label="内容">
             <el-input type="textarea" v-model="newMessage.content"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="sendMessage">发送</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '../api'

const activeTab = ref('inbox')
const inbox = ref([])
const sent = ref([])
const newMessage = reactive({ recipient_id: '', content: '' })

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

const markAsRead = async (msg) => {
  await api.put(`/messages/${msg.id}/read`)
  msg.is_read = true
}

const sendMessage = async () => {
    try {
        await api.post('/messages', newMessage)
        alert('发送成功!')
        newMessage.content = ''
        newMessage.recipient_id = ''
        fetchMessages()
        activeTab.value = 'sent'
    } catch(e) {
        alert('发送失败')
    }
}

onMounted(fetchMessages)
</script>
