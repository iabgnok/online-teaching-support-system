<template>
  <div class="forum-management">
    <el-card>
      <template #header>
        <div class="header">
          <h2>💬 论坛管理</h2>
        </div>
      </template>

      <!-- 统计信息 -->
      <div class="stats-row">
        <div class="stat-item">
          <div class="stat-label">总帖子数</div>
          <div class="stat-value">{{ statistics.total_posts || 0 }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">隐藏帖子</div>
          <div class="stat-value">{{ statistics.hidden_posts || 0 }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">锁定帖子</div>
          <div class="stat-value">{{ statistics.locked_posts || 0 }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">标记审核</div>
          <div class="stat-value">{{ statistics.flagged_posts || 0 }}</div>
        </div>
      </div>

      <!-- 帖子列表 -->
      <div class="section" style="margin-top: 30px">
        <h3>帖子管理</h3>
        
        <div class="filter-bar">
          <el-form :inline="true" :model="filters">
            <el-form-item label="状态">
              <el-select v-model="filters.status" placeholder="全部" clearable @change="loadPosts">
                <el-option label="隐藏" value="hidden" />
                <el-option label="锁定" value="locked" />
                <el-option label="标记" value="flagged" />
              </el-select>
            </el-form-item>
            <el-form-item label="搜索">
              <el-input 
                v-model="filters.search" 
                placeholder="搜索标题..." 
                clearable
                @keyup.enter="loadPosts"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadPosts" icon="Search">搜索</el-button>
            </el-form-item>
          </el-form>
        </div>

        <el-table :data="postList" v-loading="loading" stripe>
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column prop="author_name" label="作者" width="120" />
          <el-table-column prop="course_name" label="课程" width="120" />
          
          <el-table-column label="状态" width="150">
            <template #default="scope">
              <div>
                <el-tag v-if="scope.row.is_hidden" type="warning" size="small">隐藏</el-tag>
                <el-tag v-if="scope.row.is_locked" type="danger" size="small">锁定</el-tag>
                <el-tag v-if="scope.row.is_pinned" type="success" size="small">置顶</el-tag>
                <el-tag v-if="scope.row.is_flagged" type="info" size="small">标记</el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="280">
            <template #default="scope">
              <el-button 
                v-if="!scope.row.is_pinned" 
                type="primary" 
                size="small" 
                @click="pinPost(scope.row)"
              >
                置顶
              </el-button>
              <el-button 
                v-else 
                size="small" 
                @click="unpinPost(scope.row)"
              >
                取消置顶
              </el-button>

              <el-button 
                v-if="!scope.row.is_hidden" 
                type="warning" 
                size="small" 
                @click="hidePost(scope.row)"
              >
                隐藏
              </el-button>
              <el-button 
                v-else 
                size="small" 
                @click="unhidePost(scope.row)"
              >
                显示
              </el-button>

              <el-popconfirm title="确定删除该帖子?" @confirm="deletePost(scope.row)">
                <template #reference>
                  <el-button type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
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
            @change="loadPosts"
          ></el-pagination>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const postList = ref([])
const statistics = ref({})
const loading = ref(false)

const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const filters = ref({ status: null, search: '' })

const loadStatistics = async () => {
  try {
    const response = await api.get('/forum-management/admin/statistics')
    statistics.value = response.data || {}
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const loadPosts = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value
    }
    if (filters.value.status) {
      params.status = filters.value.status
    }
    if (filters.value.search) {
      params.search = filters.value.search
    }
    const response = await api.get('/forum-management/admin/posts', { params })
    postList.value = response.data.posts || []
    totalCount.value = response.data.total || 0
  } catch (error) {
    ElMessage.error('加载帖子列表失败')
  } finally {
    loading.value = false
  }
}

const pinPost = async (post) => {
  try {
    await api.post(`/forum-management/admin/posts/${post.post_id}/pin`)
    ElMessage.success('置顶成功')
    loadPosts()
    loadStatistics()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const unpinPost = async (post) => {
  try {
    await api.post(`/forum-management/admin/posts/${post.post_id}/unpin`)
    ElMessage.success('取消置顶成功')
    loadPosts()
    loadStatistics()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const hidePost = async (post) => {
  try {
    await api.post(`/forum-management/admin/posts/${post.post_id}/hide`)
    ElMessage.success('隐藏成功')
    loadPosts()
    loadStatistics()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const unhidePost = async (post) => {
  try {
    await api.post(`/forum-management/admin/posts/${post.post_id}/unhide`)
    ElMessage.success('显示成功')
    loadPosts()
    loadStatistics()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deletePost = async (post) => {
  try {
    await api.delete(`/forum-management/admin/posts/${post.post_id}/delete`)
    ElMessage.success('删除成功')
    loadPosts()
    loadStatistics()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadStatistics()
  loadPosts()
})
</script>

<style scoped>
.forum-management {
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-item {
  padding: 20px;
  border-radius: 4px;
  background-color: #f5f7fa;
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
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
</style>
