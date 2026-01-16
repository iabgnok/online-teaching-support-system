<template>
  <div class="comment-item">
    <div class="comment-main">
      <div class="thread-line" v-if="depth > 0" @click="toggleCollapse"></div>
      
      <div class="comment-content-wrapper">
        <div class="comment-header">
           <span class="author">{{ comment.author_name }}</span>
           <el-tag v-if="comment.author_role" size="small" :type="getRoleTagType(comment.author_role)" effect="plain" style="margin-left: 4px">{{ getRoleName(comment.author_role) }}</el-tag>
           <span class="meta" v-if="comment.is_accepted">
             <el-tag size="small" type="success" effect="plain">OP</el-tag>
           </span>
           <span class="date">{{ formatDate(comment.created_at) }}</span>
        </div>

        <!-- Edit Mode -->
        <div v-if="isEditing" class="edit-box">
             <el-input 
                v-model="editContent" 
                type="textarea" 
                :rows="3" 
             />
             <div class="action-buttons" style="margin-top:5px">
                 <el-button size="small" type="primary" @click="saveEdit">保存</el-button>
                 <el-button size="small" @click="cancelEdit">取消</el-button>
             </div>
        </div>
        
        <!-- Display Mode -->
        <div v-else class="comment-body">
            {{ comment.content }}
        </div>

        <div class="comment-actions">
            <el-button link size="small" @click="toggleReply">
                <el-icon><ChatLineSquare /></el-icon> 回复
            </el-button>
            
            <template v-if="canEdit">
                <el-button link size="small" @click="startEdit">
                    编辑
                </el-button>
                <el-button link size="small" type="danger" @click="handleDelete">
                    删除
                </el-button>
            </template>
        </div>

        <!-- Reply Input -->
        <div v-if="showReply" class="reply-box">
            <el-input 
                v-model="replyContent" 
                type="textarea" 
                :rows="3" 
                placeholder="你的想法是什么？"
            />
            <div class="action-buttons">
                <el-button size="small" type="primary" @click="submitReply">评论</el-button>
                <el-button size="small" @click="showReply = false">取消</el-button>
            </div>
        </div>
      </div>
    </div>

    <!-- Recursive Children -->
    <div class="comment-children" v-if="comment.replies && comment.replies.length">
        <CommentItem 
            v-for="child in comment.replies" 
            :key="child.id" 
            :comment="child" 
            :depth="depth + 1"
            :current-user="currentUser"
            @reply="$emit('reply', $event)"
            @update="$emit('update', $event)"
            @delete="$emit('delete', $event)"
        />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ChatLineSquare } from '@element-plus/icons-vue'

const props = defineProps({
    comment: Object,
    depth: {
        type: Number,
        default: 0
    },
    currentUser: Object
})

const emit = defineEmits(['reply', 'update', 'delete'])

const showReply = ref(false)
const replyContent = ref('')
const isEditing = ref(false)
const editContent = ref('')
const collapsed = ref(false)

const canEdit = computed(() => {
    if (!props.currentUser) return false
    if (props.currentUser.role === 'admin') return true
    if (props.currentUser.id === props.comment.author_id) return true
    // Basic teacher check (imperfect without class context, but consistent with parent view)
    if (props.currentUser.role === 'teacher') return true 
    return false
})

const formatDate = (dateStr) => {
    if(!dateStr) return ''
    return new Date(dateStr).toLocaleString()
}

const getRoleName = (role) => {
    const roleMap = {
        'teacher': '教师',
        'student': '学生',
        'admin': '管理员'
    }
    return roleMap[role] || role
}

const getRoleTagType = (role) => {
    const typeMap = {
        'teacher': 'warning',
        'student': '',
        'admin': 'danger'
    }
    return typeMap[role] || ''
}

const toggleReply = () => {
    showReply.value = !showReply.value
}

const submitReply = () => {
    if(!replyContent.value) return
    emit('reply', {
        parentId: props.comment.id,
        content: replyContent.value
    })
    replyContent.value = ''
    showReply.value = false
}

const startEdit = () => {
    editContent.value = props.comment.content
    isEditing.value = true
}

const saveEdit = () => {
    emit('update', {
        commentId: props.comment.id,
        content: editContent.value
    })
    isEditing.value = false
}

const cancelEdit = () => {
    isEditing.value = false
}

const handleDelete = () => {
    emit('delete', props.comment.id)
}

const toggleCollapse = () => {
    collapsed.value = !collapsed.value
}
</script>

<style scoped>
.comment-item {
    margin-top: 10px;
}

.comment-main {
    display: flex;
}

.thread-line {
    width: 2px;
    background-color: #eee;
    margin-right: 10px;
    cursor: pointer;
    transition: background-color 0.2s;
}
.thread-line:hover {
    background-color: #ddd;
}

.comment-content-wrapper {
    flex: 1;
}

.comment-header {
    font-size: 12px;
    color: #787c7e;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.author {
    font-weight: bold;
    color: #1c1c1c;
}

.comment-body {
    font-size: 14px;
    line-height: 21px;
    color: #1a1a1b;
    margin-bottom: 4px;
}

.comment-actions {
    display: flex;
    gap: 5px;
    margin-bottom: 5px;
}

.action-buttons {
    margin-top: 8px;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
}

.comment-children {
    margin-left: 20px; /* Indent style */
}

/* Specific styling for nested levels */
</style>
