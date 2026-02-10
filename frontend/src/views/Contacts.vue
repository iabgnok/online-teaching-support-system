<template>
  <div class="contacts-page">
    <div class="contacts-header">
      <h3>联系人</h3>
      <div class="actions">
        <el-input v-model="searchQuery" placeholder="搜索用户或联系人" @keyup.enter="performSearch" clearable />
        <el-button type="primary" @click="performSearch">搜索</el-button>
        <el-button type="text" @click="loadContacts">刷新</el-button>
      </div>
    </div>

    <div class="contacts-grid">
      <div class="contacts-left">
        <el-tabs v-model="activeTab" type="border-card">
          <el-tab-pane label="联系人" name="contacts">
            <div v-if="contactsLoading" class="loading">加载中...</div>
            <div v-else>
              <div v-if="contacts.length === 0" class="empty">还没有联系人</div>
              <el-row :gutter="12">
                <el-col :span="24" v-for="c in contacts" :key="c.id">
                  <el-card class="contact-card" shadow="hover">
                    <div style="display:flex; align-items:center; justify-content:space-between">
                      <div style="display:flex; align-items:center; gap:12px" @click="viewProfile(c)">
                        <div style="position:relative">
                          <el-avatar :size="48" :style="{ background: '#f0f0f0' }" :src="c.avatar_url">{{ (c.real_name || c.username || '').slice(0,1) }}</el-avatar>
                          <span v-if="isOnline(c.id)" class="status-dot online"></span>
                          <span v-else class="status-dot offline" title="离线"></span>
                        </div>
                        <div>
                          <div style="font-weight:600">{{ c.display_name || c.real_name }}</div>
                          <div class="meta">@{{ c.username }} • {{ c.role }}</div>
                          <div class="meta" style="margin-top:6px; color:#909399">{{ c.last_message || '' }}</div>
                        </div>
                      </div>

                      <div>
                        <el-dropdown @command="handleContactCommand(c, $event)">
                          <el-button size="mini">•••</el-button>
                          <el-dropdown-menu slot="dropdown">
                            <el-dropdown-item command="profile">资料</el-dropdown-item>
                            <el-dropdown-item command="chat">私聊</el-dropdown-item>
                            <el-dropdown-item command="alias">备注名</el-dropdown-item>
                            <el-dropdown-item :command="c.is_blocked ? 'unblock' : 'block'">{{ c.is_blocked ? '解除屏蔽' : '屏蔽' }}</el-dropdown-item>
                            <el-dropdown-item command="remove">删除</el-dropdown-item>
                          </el-dropdown-menu>
                        </el-dropdown>
                      </div>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>

      <el-tab-pane label="请求" name="requests">
        <div class="requests-section">
          <h4>收到的请求</h4>
          <div v-if="incoming.length === 0">没有收到新的请求</div>
          <el-row :gutter="12">
            <el-col :span="24" v-for="r in incoming" :key="r.id">
              <el-card class="request-card" shadow="never">
                <div class="request-card-inner">
                  <div class="request-info">
                    <div><strong>From {{ r.requester_id }}</strong></div>
                    <div class="msg" v-if="r.message && r.message !== '我想添加你为联系人'">{{ r.message }}</div>
                  </div>

                  <div class="request-actions">
                    <el-button size="mini" type="primary" @click="confirmAcceptRequest(r.id)">接受</el-button>
                    <el-button size="mini" type="danger" plain @click="confirmDeclineRequest(r.id)">拒绝</el-button>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <h4 style="margin-top: 16px">我发送的请求</h4>
          <div v-if="outgoing.length === 0">没有未决的请求</div>
          <div v-for="r in outgoing" :key="r.id" class="request-item">
            <div class="r-left">
              <div><strong>To {{ r.target_id }} </strong></div>
              <div class="msg">{{ r.message }}</div>
            </div>
            <div class="r-actions">
              <span class="status">{{ r.status }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="查找用户" name="search">
        <div class="search-results">
          <div v-if="searching">搜索中...</div>
          <div v-else>
            <div v-if="searchResults.length === 0">请输入至少2个字符进行搜索</div>
            <div v-for="u in searchResults" :key="u.id" class="search-item">
              <div class="info">
                <strong>{{ u.real_name }}</strong>
                <div class="meta">@{{ u.username }} • {{ u.role }}</div>
              </div>
              <div class="actions">
                <el-button v-if="u.is_contact" size="mini" disabled>已是联系人</el-button>
                <el-button v-else size="mini" type="primary" @click="sendRequest(u.id)">添加联系人</el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

    </el-tabs>
  </div>

    <!-- Right side detail panel -->
    <div class="contacts-right" v-if="selectedContact">
      <el-card>
        <div style="display:flex; gap:16px; align-items:center">
          <div style="position:relative">
            <el-avatar :size="80">{{ (selectedContact.real_name || selectedContact.username || '').slice(0,1) }}</el-avatar>
            <span v-if="isOnline(selectedContact.id)" class="status-dot online" style="position:absolute; right:6px; bottom:6px"></span>
          </div>
          <div>
            <div style="font-size:18px; font-weight:700">{{ selectedContact.real_name }}</div>
            <div class="meta">@{{ selectedContact.username }} • {{ selectedContact.role }}</div>
            <div v-if="selectedContact.is_online" style="color: #13ce66; margin-top:6px">在线</div>
            <div v-else style="color: #909399; margin-top:6px">最后在线: {{ selectedContact.last_seen || '未知' }}</div>
            <div v-if="selectedContact.alias" style="color:#909399; margin-top:6px">备注名：{{ selectedContact.alias }}</div>
            <div v-if="selectedContact.is_blocked" style="color:#f56c6c; margin-top:6px">该联系人已被屏蔽</div>
          </div>
        </div>

        <div style="margin-top: 12px; display:flex; gap:8px">
          <el-button type="primary" @click="startPrivateChat(selectedContact.id)">私聊</el-button>
          <el-button type="warning" @click="viewProfile(selectedContact)">资料</el-button>
          <el-button type="danger" @click="confirmRemoveContact(selectedContact.id)">删除</el-button>
        </div>
      </el-card>
    </div>
  </div>

    <!-- Profile Dialog (Telegram-style profile panel) -->
    <el-dialog v-model="profileDialogVisible" title="用户资料" :close-on-click-modal="false">
      <div style="display:flex; gap:12px; align-items:center;">
        <el-avatar :size="64">{{ (selectedContact?.real_name || selectedContact?.username || '').slice(0,1) }}</el-avatar>
        <div>
          <div style="font-size:16px; font-weight:600">{{ selectedContact?.real_name }}</div>
          <div class="meta">@{{ selectedContact?.username }} • {{ selectedContact?.role }}</div>
        </div>
      </div>

      <template #footer>
        <el-button @click="profileDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="startPrivateChat(selectedContact.id)">私聊</el-button>
        <el-button type="danger" @click="confirmRemoveContact(selectedContact.id)">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { eventBus } from '../utils/eventBus'
import { useRouter } from 'vue-router'

const router = useRouter()
const activeTab = ref('contacts')
const contacts = ref([])
const contactsLoading = ref(false)
const incoming = ref([])
const outgoing = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)

// Profile dialog
const profileDialogVisible = ref(false)
const selectedContact = ref(null)

const loadContacts = async () => {
  contactsLoading.value = true
  try {
    const res = await api.get('/contacts')
    contacts.value = res.data
    // 更新在线地图
    contacts.value.forEach(c => {
      onlineMap.value[String(c.id)] = !!c.is_online
    })
  } catch (e) {
    console.error('加载联系人失败', e)
    ElMessage.error('加载联系人失败')
  } finally {
    contactsLoading.value = false
  }
}

const loadRequests = async () => {
  try {
    const res = await api.get('/contacts/requests')
    incoming.value = res.data.incoming || []
    outgoing.value = res.data.outgoing || []
  } catch (e) {
    console.error('加载请求失败', e)
  }
}

const performSearch = async () => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    ElMessage.warning('请输入至少2个字符')
    return
  }
  searching.value = true
  try {
    const res = await api.get('/users/search', { params: { q: searchQuery.value } })
    searchResults.value = res.data
    activeTab.value = 'search'
  } catch (e) {
    console.error('搜索失败', e)
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

const sendRequest = async (targetId) => {
  try {
    const res = await api.post('/contacts/requests', { target_id: targetId })
    ElMessage.success('好友请求已发送')
    loadRequests()
  } catch (e) {
    console.error('发送请求失败', e)
    ElMessage.error(e.response?.data?.error || '发送请求失败')
  }
}

const acceptRequest = async (requestId) => {
  try {
    const res = await api.post(`/contacts/requests/${requestId}/accept`)
    ElMessage.success('已接受')
    // 刷新数据
    await loadContacts()
    await loadRequests()

    // 如果返回了 conversation_id，延迟导航以避免渲染竞态
    if (res.data.conversation_id) {
      setTimeout(() => {
        // 只有当路由参数不一致时才导航
        const curId = parseInt(router.currentRoute.value.query.id)
        if (curId !== res.data.conversation_id) {
          router.push({ path: '/chat', query: { id: res.data.conversation_id } })
        }
      }, 50)
    }
  } catch (e) {
    console.error('接收失败', e)
    ElMessage.error('接收失败')
  }
}

// Confirm wrappers
const confirmAcceptRequest = (requestId) => {
  ElMessageBox.confirm('接受该好友请求吗？', '确认', { confirmButtonText: '接受', cancelButtonText: '取消', type: 'info' })
    .then(() => acceptRequest(requestId))
    .catch(() => {})
}

const confirmDeclineRequest = (requestId) => {
  ElMessageBox.confirm('拒绝该好友请求吗？', '确认', { confirmButtonText: '拒绝', cancelButtonText: '取消', type: 'warning' })
    .then(() => declineRequest(requestId))
    .catch(() => {})
}

const confirmRemoveContact = (contactId) => {
  ElMessageBox.confirm('删除联系人？该操作将移除对方关系。', '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    .then(() => removeContact(contactId))
    .catch(() => {})
}
const declineRequest = async (requestId) => {
  try {
    await api.post(`/contacts/requests/${requestId}/decline`)
    ElMessage.success('已拒绝')
    loadRequests()
  } catch (e) {
    console.error('拒绝失败', e)
    ElMessage.error('拒绝失败')
  }
}

const removeContact = async (contactId) => {
  try {
    await api.delete(`/contacts/${contactId}`)
    ElMessage.success('已删除联系人')
    loadContacts()
  } catch (e) {
    console.error('删除联系人失败', e)
    ElMessage.error('删除联系人失败')
  }
}

const startPrivateChat = async (contactId) => {
  try {
    const res = await api.post('/contacts/private-conversation', { target_id: contactId })
    const convId = res.data.conversation_id
    if (convId) {
      router.push({ path: '/chat', query: { id: convId } })
    } else {
      ElMessage.error('无法创建私聊')
    }
  } catch (e) {
    console.error('创建私聊失败', e)
    ElMessage.error(e.response?.data?.error || '创建私聊失败')
  }
}

const onlineMap = ref({})

const isOnline = (userId) => {
  return !!onlineMap.value[String(userId)]
}

const handleContactCommand = (contact, cmd) => {
  if (cmd === 'profile') return viewProfile(contact)
  if (cmd === 'chat') return startPrivateChat(contact.id)
  if (cmd === 'remove') return confirmRemoveContact(contact.id)
  if (cmd === 'alias') return editAlias(contact)
  if (cmd === 'block') return confirmBlock(contact.id)
  if (cmd === 'unblock') return confirmUnblock(contact.id)
}

const viewProfile = (contact) => {
  selectedContact.value = contact
  profileDialogVisible.value = true
}

const editAlias = async (contact) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入备注名', '备注名', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: contact.alias || contact.real_name || ''
    })
    // 调接口保存
    const res = await api.put(`/contacts/${contact.id}/alias`, { alias: value })
    ElMessage.success('备注名已保存')
    // 刷新联系人列表
    await loadContacts()
  } catch (e) {
    // 用户取消或失败
    if (e && e !== 'cancel') console.error('保存备注失败', e)
  }
}

const confirmBlock = (contactId) => {
  ElMessageBox.confirm('屏蔽该联系人？屏蔽后您不会收到其消息', '确认屏蔽', { confirmButtonText: '屏蔽', cancelButtonText: '取消', type: 'warning' })
    .then(async () => {
      await api.post(`/contacts/${contactId}/block`)
      ElMessage.success('已屏蔽')
      await loadContacts()
    }).catch(() => {})
}

const confirmUnblock = (contactId) => {
  ElMessageBox.confirm('解除对该联系人的屏蔽吗？', '解除屏蔽', { confirmButtonText: '解除', cancelButtonText: '取消', type: 'info' })
    .then(async () => {
      await api.post(`/contacts/${contactId}/unblock`)
      ElMessage.success('已解除屏蔽')
      await loadContacts()
    }).catch(() => {})
}

// Lifecycle event handlers (define once so they can be removed reliably)
const onContactsRequest = (payload) => {
  ElMessage.info(`收到好友请求：来自 ${payload.from_name || payload.from}`)
  loadRequests()
  activeTab.value = 'requests'
}

const onContactsAccepted = (payload) => {
  ElMessage.success('您的好友请求已被接受')
  loadContacts()
  if (payload.conversation_id) {
    // 延迟导航避免竞态
    setTimeout(() => {
      const curId = parseInt(router.currentRoute.value.query.id)
      if (curId !== payload.conversation_id) router.push({ path: '/chat', query: { id: payload.conversation_id } })
    }, 50)
  }
}

const onUserOnline = (payload) => {
  onlineMap.value[String(payload.user_id)] = true
}

const onUserOffline = (payload) => {
  onlineMap.value[String(payload.user_id)] = false
}

onMounted(() => {
  loadContacts()
  loadRequests()

  eventBus.on('contacts:request', onContactsRequest)
  eventBus.on('contacts:request_accepted', onContactsAccepted)
  eventBus.on('user_online', onUserOnline)
  eventBus.on('user_offline', onUserOffline)
})

onUnmounted(() => {
  eventBus.off('contacts:request', onContactsRequest)
  eventBus.off('contacts:request_accepted', onContactsAccepted)
  eventBus.off('user_online', onUserOnline)
  eventBus.off('user_offline', onUserOffline)
})

// Profile Dialog UI
</script>

<style scoped>
.contacts-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px }
.actions { display:flex; gap:8px; align-items:center }
.request-item { display:flex; justify-content:space-between; align-items:center; padding:8px 0 }
.search-item { display:flex; justify-content:space-between; align-items:center; padding:8px 0 }
.item-left .meta, .info .meta { color: #909399; font-size: 12px }

.contact-card { cursor: pointer; margin-bottom: 8px }
.contact-card:hover { background: #f7fbff }
.request-card { margin-bottom: 8px }
.contact-card .el-avatar { background: #f0f2f6 }

.contacts-grid { display:flex; gap:16px }
.contacts-left { flex: 0 0 42% }
.contacts-right { flex: 1 }

.status-dot { width:12px; height:12px; border-radius:50%; display:inline-block; border: 2px solid #fff; box-shadow: 0 0 0 2px rgba(0,0,0,0.06) }
.status-dot.online { background: #13ce66 }
.status-dot.offline { background: #c0c4cc }

</style>
