<template>
  <div class="forum-container">
    <!-- Navbar / Subheader -->
    <div class="forum-header-bar">
        <div class="header-left">
            <el-select v-model="classId" 
                       placeholder="选择班级" 
                       filterable 
                       style="width: 200px"
                       @change="loadPosts">
                 <el-option 
                    v-for="item in classList"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                 />
            </el-select>
        </div>
    </div>

    <!-- Main Layout -->
    <div class="forum-body">
        <!-- Feed Column -->
        <div class="feed-column">
             <!-- Reddit-style Create Post Input -->
             <div class="create-post-bar" @click="showCreateDialog">
                 <div class="user-avatar-placeholder">
                    <el-icon><User /></el-icon>
                 </div>
                 <input type="text" class="fake-input" placeholder="发布帖子..." readonly />
                 <el-button circle plain><el-icon><Picture /></el-icon></el-button>
                 <el-button circle plain><el-icon><Link /></el-icon></el-button>
             </div>

             <div v-if="loading" class="loading-state">
                 <el-skeleton :rows="5" animated />
             </div>
             
             <div v-else-if="posts.length > 0">
                 <PostListCard 
                    v-for="post in posts" 
                    :key="post.id" 
                    :post="post" 
                    :current-user="currentUser"
                    @click="viewPost(post.id)"
                    @edit="editPost(post)"
                    @delete="deletePost(post)"
                 />
             </div>
             
             <div v-else class="empty-state">
                 <h3>该班级讨论区暂时没有帖子</h3>
                 <p>来发布第一个话题吧！</p>
             </div>
        </div>
        
        <!-- Sidebar Column -->
        <div class="sidebar-column">
            <div class="sidebar-card">
                <div class="sidebar-header">
                    关于班级 {{ classId || '...' }}
                </div>
                <div class="sidebar-content">
                    <p>欢迎来到班级讨论区。请理智讨论，互帮互助。</p>
                    <div class="stat-row">
                        <div class="stat-item">
                            <div class="stat-num">{{ posts.length }}</div>
                            <div class="stat-label">帖子</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-num">--</div>
                            <div class="stat-label">在线</div>
                        </div>
                    </div>
                </div>
                <div class="sidebar-footer">
                    <el-button type="primary" style="width: 100%" round @click="showCreateDialog">发布帖子</el-button>
                </div>
            </div>
            
             <div class="sidebar-card">
                <div class="sidebar-header">版规</div>
                 <div class="sidebar-content" style="font-size: 13px;">
                     1. 禁止灌水<br>
                     2. 尊重老师和助教<br>
                     3. 注意文明用语<br>
                 </div>
             </div>
        </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showCreate" :title="isEditing ? '编辑帖子' : '发布新帖'" width="600px">
        <el-form>
            <el-form-item>
                <el-input 
                    v-model="newPost.title" 
                    placeholder="标题" 
                    maxlength="300" 
                    show-word-limit
                    class="reddit-title-input"
                ></el-input>
            </el-form-item>
            <el-form-item>
                <el-input 
                    type="textarea" 
                    v-model="newPost.content" 
                    :rows="8" 
                    placeholder="正文内容 (选填)"
                    class="reddit-text-input"
                ></el-input>
            </el-form-item>
            <el-form-item v-if="!isEditing">
                 <div class="file-upload-area">
                    <input type="file" @change="handleFileChange" id="fileUpload" style="display:none"/>
                    <label for="fileUpload" class="file-label">
                         <el-icon><Paperclip /></el-icon> {{ file ? file.name : '上传附件' }}
                    </label>
                 </div>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="resetForm" round>取消</el-button>
            <el-button type="primary" @click="submitPost" round :disabled="!newPost.title">发布</el-button>
        </template>
    </el-dialog>
    
    <!-- Post Detail Overlay (Large Dialog) -->
    <el-dialog 
        v-model="showDetail" 
        width="80%" 
        class="post-detail-dialog"
        :show-close="true"
        top="5vh"
        style="min-height: 80vh;"
    >
        <div v-if="currentPost" class="detail-container">
            <!-- Vote Column (Detail) -->
             <div class="detail-vote-column">
                <el-icon class="vote-btn"><ArrowUp /></el-icon>
                <span style="font-weight:bold; margin: 5px 0">{{ currentPost.view_count }}</span>
                <el-icon class="vote-btn"><ArrowDown /></el-icon>
             </div>
             
             <div class="detail-content">
                 <div class="post-header-detail">
                     <span class="subreddit-prefix">r/Class_{{ classId }}</span>
                     <span class="posted-by">发布者 u/{{ currentPost.author_name }} • {{ formatDate(currentPost.created_at) }}</span>
                 </div>
                 
                 <h2 class="detail-title">
                     {{ currentPost.title }}
                     <el-tag v-if="currentPost.is_solved" type="success" size="small">已解决</el-tag>
                 </h2>
                 
                 <div class="detail-body">
                     {{ currentPost.content }}
                 </div>
                 
                 <div v-if="currentPost.file_name" class="detail-attachment">
                     <a :href="currentPost.file_url" target="_blank" class="attachment-link">
                         <el-icon><Document /></el-icon> {{ currentPost.file_name }}
                     </a>
                 </div>
                 
                 <div class="detail-actions">
                     <div class="footer-btn"><el-icon><ChatSquare /></el-icon> {{ currentPost.comments ? currentPost.comments.length : 0 }} 评论</div>
                     <div class="footer-btn"><el-icon><Share /></el-icon> 分享</div>
                 </div>
                 
                 <el-divider v-if="currentUser"/>
                 
                 <!-- Comment Input -->
                 <div class="comment-input-area" v-if="currentUser">
                     <div class="comment-as">以 <span style="color: #409EFF">{{ currentUser.username }}</span> 的身份评论</div>
                     <el-input 
                        v-model="newComment" 
                        type="textarea" 
                        :rows="4" 
                        placeholder="谈谈你的看法..."
                        class="comment-textarea"
                     />
                     <div style="display: flex; justify-content: flex-end; margin-top: 5px;">
                         <el-button type="primary" round :disabled="!newComment" @click="submitComment">评论</el-button>
                     </div>
                 </div>
                 
                 <el-divider />
                 
                 <!-- Recursive Comments -->
                 <div class="comments-section">
                     <CommentItem 
                        v-for="comment in currentPost.comments" 
                        :key="comment.id" 
                        :comment="comment"
                        :current-user="currentUser"
                        @reply="handleReply"
                        @update="submitEditComment"
                        @delete="deleteExistingComment"
                     />
                 </div>
             </div>
        </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Paperclip, Document, ArrowUp, ArrowDown, ChatSquare, Share, User, Picture, Link } from '@element-plus/icons-vue'
import PostListCard from '../components/PostListCard.vue'
import CommentItem from '../components/CommentItem.vue'

const classId = ref('')
const classList = ref([])
const posts = ref([])
const loading = ref(false)
const showCreate = ref(false)
const showDetail = ref(false)
const currentPost = ref(null)
const newComment = ref('')
const currentUser = ref(null)

const isEditing = ref(false)
const editingId = ref(null)
const file = ref(null)

const newPost = reactive({
    title: '',
    content: ''
})

onMounted(async () => {
    try {
        const res = await api.get('/me')
        currentUser.value = res.data
        
        const classesRes = await api.get('/my-classes')
        classList.value = classesRes.data
        if(classList.value.length > 0) {
            classId.value = classList.value[0].id
            loadPosts()
        }
    } catch (e) {
        console.error('Failed to get user info or classes')
    }
})

const formatDate = (dateStr) => {
    if(!dateStr) return ''
    return new Date(dateStr).toLocaleString()
}

const loadPosts = async () => {
    if(!classId.value) return;
    loading.value = true
    try {
        const res = await api.get(`/classes/${classId.value}/forum/posts`)
        posts.value = res.data
    } catch(e) {
        posts.value = []
        if (e.response && e.response.status === 404) {
             ElMessage.error('未找到该班级')
        } else {
             ElMessage.error('加载帖子失败')
        }
    } finally {
        loading.value = false
    }
}

const showCreateDialog = () => {
    if(!classId.value) {
        ElMessage.warning('请先选择一个班级')
        return;
    }
    resetForm()
    showCreate.value = true
}

const handleFileChange = (e) => {
    file.value = e.target.files[0]
}

const resetForm = () => {
    showCreate.value = false
    isEditing.value = false
    newPost.title = ''
    newPost.content = ''
    file.value = null
    editingId.value = null
}

const submitPost = async () => {
    try {
        if (isEditing.value) {
            await api.put(`/forum/posts/${editingId.value}`, {
                title: newPost.title,
                content: newPost.content
            })
            ElMessage.success('更新成功')
        } else {
            const formData = new FormData()
            formData.append('title', newPost.title)
            formData.append('content', newPost.content)
            if (file.value) {
                formData.append('file', file.value)
            }
            await api.post(`/classes/${classId.value}/forum/posts`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            ElMessage.success('发布成功')
        }
        resetForm()
        loadPosts()
    } catch(e) {
        ElMessage.error(e.response?.data?.error || '发布失败')
    }
}

const editPost = (post) => {
    isEditing.value = true
    editingId.value = post.id
    newPost.title = post.title
    newPost.content = post.content
    showCreate.value = true
}

const deletePost = async (post) => {
    try {
        await ElMessageBox.confirm('确定要删除这个帖子吗？')
        await api.delete(`/forum/posts/${post.id}`)
        ElMessage.success('删除成功')
        loadPosts()
    } catch (e) {
        if (e !== 'cancel') ElMessage.error(e.response?.data?.error || '删除失败')
    }
}

const viewPost = async (postId) => {
    try {
        const res = await api.get(`/forum/posts/${postId}`)
        currentPost.value = res.data
        showDetail.value = true
    } catch(e) {
        ElMessage.error('加载帖子详情失败')
    }
}

const submitComment = async () => {
    if(!newComment.value || !currentPost.value) return;
    try {
        await api.post(`/forum/posts/${currentPost.value.id}/comments`, {
            content: newComment.value
        })
        newComment.value = ''
        viewPost(currentPost.value.id)
    } catch (e) {
        ElMessage.error('评论失败')
    }
}

const handleReply = async (payload) => {
    try {
         await api.post(`/forum/posts/${currentPost.value.id}/comments`, {
            content: payload.content,
            parent_id: payload.parentId
        })
        viewPost(currentPost.value.id)
    } catch(e) {
         ElMessage.error('回复失败')
    }
}

const submitEditComment = async (payload) => {
    try {
        await api.put(`/forum/comments/${payload.commentId}`, {
            content: payload.content
        })
        viewPost(currentPost.value.id)
    } catch(e) {
        ElMessage.error('更新评论失败')
    }
}

const deleteExistingComment = async (commentId) => {
    try {
        await ElMessageBox.confirm('确定要删除这条评论吗？')
        await api.delete(`/forum/comments/${commentId}`)
        viewPost(currentPost.value.id)
    } catch (e) {
        if (e!=='cancel') ElMessage.error('删除评论失败')
    }
}
</script>

<style scoped>
.forum-container {
    background-color: #dae0e6; /* Reddit gray */
    min-height: 100vh;
    padding-top: 10px;
}

.forum-header-bar {
    background: transparent;
    padding: 10px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0px;
}

.forum-body {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    gap: 24px;
} 
    /* .feed-column ... */

.feed-column {
    flex: 1;
}

.create-post-bar {
    background: white;
    border-radius: 4px;
    padding: 8px 12px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    border: 1px solid #ccc;
    transition: border 0.2s ease;
}
.create-post-bar:hover {
    border-color: #898989;
}
.user-avatar-placeholder {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background-color: #eee;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #878a8c;
}
.fake-input {
    flex: 1;
    background-color: #f6f7f8;
    border: 1px solid #edeff1;
    border-radius: 4px;
    height: 38px;
    padding: 0 16px;
    font-size: 14px;
    color: #1c1c1c; /* Text darker */
    cursor: pointer;
    outline: none;
}
.fake-input:hover {
    background-color: white;
    border-color: #0079d3;
}

.sidebar-column {
    width: 312px;
    display: none; /* Hide on small screens */
}
@media (min-width: 900px) {
    .sidebar-column {
        display: block;
    }
}

.sidebar-card {
    background: white;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
    border: none;
    border-radius: 8px;
    margin-bottom: 20px;
    overflow: hidden;
}
.sidebar-header {
    background: #0079D3; /* Reddit Blue */
    color: white;
    padding: 12px;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 0.5px;
}
.sidebar-content {
    padding: 12px;
    font-size: 14px;
    line-height: 21px;
}
.sidebar-footer {
    padding: 12px;
}
.stat-row {
    display: flex;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.stat-item {
    flex: 1;
}
.stat-num {
    font-size: 16px;
    font-weight: 500;
}
.stat-label {
    font-size: 12px;
    color: #666;
}

.empty-state {
    background: white;
    padding: 50px;
    text-align: center;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
    border-radius: 8px;
    color: #909399;
}

/* Detail Styling */
.detail-container {
    display: flex;
    background: white;
}
.detail-vote-column {
    width: 40px;
    padding-top: 10px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.detail-content {
    flex: 1;
    padding: 10px 20px;
}
.post-header-detail {
    font-size: 12px;
    color: #787c7e;
    margin-bottom: 10px;
}
.detail-title {
    font-size: 24px;
    margin-bottom: 10px;
    font-weight: 500;
}
.detail-body {
    font-size: 16px;
    line-height: 1.5;
    margin-bottom: 20px;
    color: #1a1a1b;
}
.detail-attachment {
    background: #f0f2f5;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 20px;
    display: inline-block;
}
.attachment-link {
    text-decoration: none;
    color: #0079d3;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 5px;
}
.detail-actions {
    color: #878a8c;
    font-weight: 700;
    font-size: 12px;
    display: flex;
    gap: 15px;
}

.comment-input-area {
    margin: 20px 0;
}
.comment-as {
    font-size: 12px;
    margin-bottom: 5px;
}

.reddit-title-input :deep(.el-input__inner) {
    font-size: 16px;
    font-weight: 500;
}
.file-upload-area {
    border: 1px dashed #ccc;
    padding: 10px;
    text-align: center;
    border-radius: 4px;
    margin-top: 10px;
    cursor: pointer;
}
.file-label {
    cursor: pointer;
    color: #0079d3;
    font-weight: bold;
}
</style>

