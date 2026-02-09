<template>
  <div class="conversation-area">
    <div v-if="!hideHeader" class="sidebar-header">
      <h2>{{ title }}</h2>
      <button class="btn-new-chat" @click="$emit('new-chat')" title="新建群组">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
          <circle cx="9" cy="7" r="4"></circle>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
        </svg>
      </button>
    </div>
    
    <div class="search-box">
      <el-input 
        v-model="localSearchQuery" 
        placeholder="搜索对话或消息..." 
        prefix-icon="el-icon-search"
        clearable
      />
    </div>
    
    <!-- 分类栏 -->
    <div class="category-bar">
      <div class="category-tabs">
        <div 
          class="category-tab" 
          :class="{ active: activeFolderId === 'all' }"
          @click="handleFolderChange('all')"
        >
          全部
        </div>
        <div 
          v-if="totalUnreadCount > 0"
          class="category-tab" 
          :class="{ active: activeFolderId === 'unread' }"
          @click="handleFolderChange('unread')"
        >
          未读
          <span v-if="totalUnreadCount > 0" class="category-badge">{{ totalUnreadCount > 99 ? '99+' : totalUnreadCount }}</span>
        </div>
        <div 
          v-for="folder in folders" 
          :key="folder.id"
          class="category-tab folder-tab"
          :class="{ active: activeFolderId === folder.id }"
          @click="handleFolderChange(folder.id)"
        >
          {{ folder.name }}
          <button class="tab-delete-btn" @click.stop="$emit('delete-folder', folder.id)" title="删除">
            <i class="el-icon-close"></i>
          </button>
        </div>
      </div>
      <button class="btn-add-folder" @click="$emit('add-folder')" title="新建文件夹">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
      </button>
    </div>
    
    <div class="conversation-list">
      <ConversationItem 
        v-for="conv in filteredConversations" 
        :key="conv.id"
        :conversation="conv"
        :active="currentConversationId === conv.id"
        :context-menu-visible="activeContextMenu === conv.id"
        :folders="folders"
        :active-folder-id="activeFolderId"
        @click="$emit('select', conv.id)"
        @show-context-menu="$emit('show-context-menu', conv.id, $event)"
        @hide-context-menu="$emit('hide-context-menu')"
        @pin="$emit('pin', $event)"
        @mute="$emit('mute', $event)"
        @read="$emit('read', $event)"
        @add-to-folder="$emit('add-to-folder', $event)"
        @open-create-folder="$emit('open-create-folder', $event)"
        @remove-from-folder="$emit('remove-from-folder', $event)"
        @leave="$emit('leave', $event)"
      />
      
      <div v-if="conversations.length === 0" class="empty-state">
        <p>暂无对话</p>
        <el-button type="primary" size="small" @click="$emit('new-chat')">
          开始聊天
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import ConversationItem from './ConversationItem.vue'

const props = defineProps({
  hideHeader: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '教学群组'
  },
  conversations: {
    type: Array,
    default: () => []
  },
  currentConversationId: {
    type: [Number, String],
    default: null
  },
  activeFolderId: {
    type: [String, Number],
    default: 'all'
  },
  folders: {
    type: Array,
    default: () => []
  },
  totalUnreadCount: {
    type: Number,
    default: 0
  },
  activeContextMenu: {
    type: [Number, String],
    default: null
  },
  searchQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'update:searchQuery',
  'select',
  'new-chat',
  'folder-change',
  'add-folder',
  'delete-folder',
  'show-context-menu',
  'hide-context-menu',
  'pin',
  'mute',
  'read',
  'add-to-folder',
  'open-create-folder',
  'remove-from-folder',
  'leave'
])

const localSearchQuery = ref(props.searchQuery)
watch(() => props.searchQuery, (newVal) => localSearchQuery.value = newVal)
watch(localSearchQuery, (newVal) => emit('update:searchQuery', newVal))

const filteredConversations = computed(() => {
  let list = props.conversations
  
  if (props.activeFolderId === 'unread') {
    list = list.filter(c => c.unread_count > 0)
  } else if (props.activeFolderId !== 'all') {
    list = list.filter(c => c.folder_id == props.activeFolderId)
  }
  
  if (localSearchQuery.value) {
    const q = localSearchQuery.value.toLowerCase()
    list = list.filter(c => 
      c.title.toLowerCase().includes(q) || 
      (c.last_message && c.last_message.toLowerCase().includes(q))
    )
  }
  
  return list
})

const handleFolderChange = (id) => {
  emit('folder-change', id)
}
</script>

<style scoped>
.sidebar-header {
  height: 60px;
  max-height: 60px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f0f2f5;
  background: #fff;
}

.sidebar-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.btn-new-chat {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: #f0f7ff;
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-new-chat:hover {
  background: #409eff;
  color: #fff;
}

.search-box {
  padding: 12px 16px;
  background: #fff;
}

:deep(.el-input__inner) {
  background: #f5f7fa;
  border: 1px solid transparent;
  border-radius: 8px;
}

:deep(.el-input__inner:focus) {
  background: #fff;
  border-color: #409eff;
}

.category-bar {
  display: flex;
  align-items: center;
  padding: 4px 12px 8px;
  background: #fff;
  border-bottom: 1px solid #f0f2f5;
  gap: 8px;
}

.category-tabs {
  flex: 1;
  display: flex;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.category-tabs::-webkit-scrollbar {
  display: none;
}

.category-tab {
  padding: 6px 12px;
  font-size: 13px;
  color: #64748b;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.category-tab:hover {
  background: #f1f5f9;
  color: #1a1a1a;
}

.category-tab.active {
  background: #f0f7ff;
  color: #409eff;
  font-weight: 600;
}

.category-badge {
  background: #ff4757;
  color: #fff;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 8px;
  min-width: 14px;
  text-align: center;
}

.btn-add-folder {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #94a3b8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-add-folder:hover {
  background: #f1f5f9;
  color: #409eff;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  background: #fff;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
}

.empty-state p {
  margin-bottom: 16px;
  font-size: 14px;
}

.folder-tab {
  position: relative;
  padding-right: 28px !important;
}

.tab-delete-btn {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  display: none;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(0,0,0,0.1);
  color: #666;
  border-radius: 50%;
  font-size: 10px;
  cursor: pointer;
}

.folder-tab:hover .tab-delete-btn {
  display: flex;
}
</style>
