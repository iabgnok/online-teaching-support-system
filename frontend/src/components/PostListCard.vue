<template>
  <div class="post-card" @click="$emit('click')">
    <!-- Vote Column (Mock) -->
    <div class="vote-column" @click.stop>
        <el-icon class="vote-btn" :size="20"><ArrowUp /></el-icon>
        <div class="vote-count">{{ getRandomVotes(post.view_count) }}</div>
        <el-icon class="vote-btn" :size="20"><ArrowDown /></el-icon>
    </div>
    
    <!-- Content Column -->
    <div class="content-column">
        <div class="post-header">
            <span class="subreddit-prefix">r/Class_{{ post.class_id || 'General' }}</span>
            <span class="posted-by">发布者 u/{{ post.author_name }}</span>
            <el-tag v-if="post.author_role" size="small" :type="getRoleTagType(post.author_role)" effect="plain" style="margin-left: 4px">{{ getRoleName(post.author_role) }}</el-tag>
            <span class="post-time">{{ formatDate(post.created_at) }}</span>
        </div>
        
        <h3 class="post-title">{{ post.title }} 
            <el-tag v-if="post.is_pinned" size="small" type="danger" effect="dark">置顶</el-tag>
            <el-tag v-if="post.is_solved" size="small" type="success" effect="dark">已解决</el-tag>
        </h3>
        
        <div class="post-preview">
            {{ getPreview(post.content) }}
        </div>
        
        <div class="post-footer" @click.stop>
            <div class="footer-btn">
                <el-icon><ChatSquare /></el-icon>
                <span>{{ post.reply_count }} 评论</span>
            </div>
            <div class="footer-btn">
                <el-icon><Star /></el-icon>
                <span>点赞</span>
            </div>
             <div class="footer-btn" v-if="post.has_attachment">
                <el-icon><Paperclip /></el-icon>
                <span>附件</span>
            </div>
            <div class="footer-spacer"></div>
             <!-- Mod Actions -->
             <el-dropdown v-if="canManage" trigger="click" @command="handleCommand">
                <span class="el-dropdown-link footer-btn">
                     <el-icon><More /></el-icon>
                </span>
                <template #dropdown>
                <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑帖子</el-dropdown-item>
                    <el-dropdown-item command="delete" style="color: red">删除</el-dropdown-item>
                </el-dropdown-menu>
                </template>
            </el-dropdown>
        </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowUp, ArrowDown, ChatSquare, Star, Paperclip, More } from '@element-plus/icons-vue'

const props = defineProps({
    post: Object,
    currentUser: Object
})

const emit = defineEmits(['click', 'edit', 'delete'])

const canManage = computed(() => {
    if (!props.currentUser) return false
    if (props.currentUser.role === 'admin') return true
    if (props.currentUser.id === props.post.author_id) return true
    if (props.currentUser.role === 'teacher') return true 
    return false
})

const getRandomVotes = (views) => {
    // Just a mock function to make it look alive, using view_count as base
    return views || 0
}

const formatDate = (dateStr) => {
    if(!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diff = (now - date) / 1000 // seconds
    
    if (diff < 60) return '刚刚'
    if (diff < 3600) return `${Math.floor(diff/60)} 分钟前`
    if (diff < 86400) return `${Math.floor(diff/3600)} 小时前`
    return date.toLocaleDateString()
}

const getPreview = (content) => {
    if (!content) return ''
    return content.length > 150 ? content.substring(0, 150) + '...' : content
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

const handleCommand = (cmd) => {
    if (cmd === 'edit') emit('edit')
    if (cmd === 'delete') emit('delete')
}
</script>

<style scoped>
.post-card {
    display: flex;
    background: #fff;
    border: none;
    border-radius: 8px;
    margin-bottom: 16px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
}
.post-card:hover {
    box-shadow: 0 14px 28px rgba(0,0,0,0.25), 0 10px 10px rgba(0,0,0,0.22);
    transform: translateY(-2px);
}

.vote-column {
    width: 40px;
    background: #f8f9fa;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 8px 0;
    border-right: none;
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
}
.vote-btn {
    cursor: pointer;
    color: #878a8c;
    padding: 2px;
}
.vote-btn:hover {
    background: #e0e0e0;
    border-radius: 2px;
    color: #cc3700; /* Reddit orange on hover */
}
.vote-count {
    font-weight: bold;
    font-size: 12px;
    margin: 4px 0;
}

.content-column {
    flex: 1;
    padding: 8px;
    display: flex;
    flex-direction: column;
}

.post-header {
    font-size: 12px;
    color: #787c7e;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 5px;
}
.subreddit-prefix {
    font-weight: bold;
    color: #1c1c1c;
}

.post-title {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 500;
    line-height: 22px;
    color: #222;
}

.post-preview {
    font-size: 14px;
    line-height: 21px;
    color: #1c1c1c;
    margin-bottom: 8px;
    
    /* Fade out long text */
    max-height: 100px;
    overflow: hidden;
    position: relative;
}

.post-footer {
    display: flex;
    align-items: center;
    gap: 4px;
}

.footer-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 8px;
    color: #878a8c;
    font-size: 12px;
    font-weight: 700;
    border-radius: 2px;
    cursor: pointer;
}
.footer-btn:hover {
    background-color: #e8e8e8;
}

.footer-spacer {
    flex: 1;
}
</style>
