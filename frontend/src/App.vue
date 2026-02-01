<template>
  <div v-if="showLayout">
    <el-container class="app-layout">
      <el-header class="main-header" height="60px">
        <div class="header-content">
          <h1 class="logo">在线教学支持系统</h1>
          <div class="nav-links">
            <router-link 
              v-for="link in navigationLinks" 
              :key="link.path" 
              :to="link.path" 
              class="nav-link"
              :class="{ 'has-badge': link.badge && link.badge > 0 }"
            >
              <span class="link-text">
                <i v-if="link.icon" :class="link.icon"></i>
                {{ link.label }}
              </span>
              <span v-if="link.badge && link.badge > 0" class="nav-badge">
                {{ link.badge > 99 ? '99+' : link.badge }}
              </span>
            </router-link>
            <a href="#" @click.prevent="logout" class="nav-link">
              <i class="el-icon-switch-button"></i> 退出
            </a>
          </div>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view></router-view>
      </el-main>
    </el-container>
  </div>
  <router-view v-else></router-view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from './api'

const router = useRouter()
const route = useRoute()
const userRole = ref(localStorage.getItem('user_role') || 'student')
const unreadCount = ref(0)

// 监听路由变化，实时更新用户角色
watch(() => route.path, () => {
  const storedRole = localStorage.getItem('user_role')
  if (storedRole) {
    userRole.value = storedRole
  }
})

// 获取未读消息数
const fetchUnreadCount = async () => {
  try {
    // 检查是否已登录
    const token = localStorage.getItem('user_token')
    const userId = localStorage.getItem('user_id')
    
    // 如果未登录或在登录页，不执行请求
    if (!token || !userId || route.path === '/login') {
      unreadCount.value = 0
      return
    }
    
    // 调用API获取未读消息总数
    const response = await api.get('/chat/conversations')
    const conversations = response.data || []
    
    // 计算未读总数
    let total = 0
    conversations.forEach(conv => {
      if (conv.unread_count) {
        total += conv.unread_count
      }
    })
    unreadCount.value = total
  } catch (error) {
    // 如果是401错误，说明token失效，停止轮询并清空数据
    if (error.response?.status === 401) {
      unreadCount.value = 0
      // 停止轮询
      if (unreadCountInterval) {
        clearInterval(unreadCountInterval)
        unreadCountInterval = null
      }
      // 清空localStorage并跳转登录页
      console.warn('Token失效，停止未读消息轮询')
      localStorage.clear()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      return
    }
    console.error('获取未读消息数失败:', error)
    // 出错时重置未读数
    unreadCount.value = 0
  }
}

// 定时器引用
let unreadCountInterval = null

onMounted(() => {
  // 页面加载时获取未读数
  fetchUnreadCount()
  
  // 每30秒更新一次未读数
  unreadCountInterval = setInterval(fetchUnreadCount, 30000)
})

// 监听路由变化，在登录页时停止轮询
watch(() => route.path, (newPath) => {
  if (newPath === '/login') {
    // 清空未读数
    unreadCount.value = 0
    // 清除定时器
    if (unreadCountInterval) {
      clearInterval(unreadCountInterval)
      unreadCountInterval = null
    }
  } else if (!unreadCountInterval) {
    // 离开登录页时重新启动定时器
    fetchUnreadCount()
    unreadCountInterval = setInterval(fetchUnreadCount, 30000)
  }
})

const showLayout = computed(() => {
  return route.path !== '/login'
})

const navigationLinks = computed(() => {
  if (userRole.value === 'admin') {
    return [
      { path: '/admin/dashboard', label: '管理员控制台', icon: 'el-icon-menu' },
      { path: '/chat', label: '消息中心', icon: 'el-icon-chat-dot-round', badge: unreadCount.value },
      { path: '/messages', label: '站内信', icon: 'el-icon-message' },
      { path: '/profile', label: '账户信息', icon: 'el-icon-user' }
    ]
  } else if (userRole.value === 'teacher') {
    return [
      { path: '/teacher/dashboard', label: '工作台', icon: 'el-icon-s-home' },
      { path: '/teacher/teaching-plan', label: '教学计划', icon: 'el-icon-document' },
      { path: '/chat', label: '消息中心', icon: 'el-icon-chat-dot-round', badge: unreadCount.value },
      { path: '/forum', label: '论坛', icon: 'el-icon-chat-line-square' },
      { path: '/messages', label: '站内信', icon: 'el-icon-message' },
      { path: '/profile', label: '账户信息', icon: 'el-icon-user' }
    ]
  } else {
    return [
      { path: '/', label: '首页', icon: 'el-icon-s-home' },
      { path: '/schedule', label: '日程', icon: 'el-icon-calendar' },
      { path: '/my-grades', label: '我的成绩', icon: 'el-icon-document' },
      { path: '/chat', label: '消息中心', icon: 'el-icon-chat-dot-round', badge: unreadCount.value },
      { path: '/forum', label: '论坛', icon: 'el-icon-chat-line-square' },
      { path: '/messages', label: '站内信', icon: 'el-icon-message' },
      { path: '/profile', label: '账户信息', icon: 'el-icon-user' }
    ]
  }
})

const logout = async () => {
  // 清除定时器
  if (unreadCountInterval) {
    clearInterval(unreadCountInterval)
    unreadCountInterval = null
  }
  
  try {
    await api.post('/logout')
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_name')
    localStorage.removeItem('real_name')
    userRole.value = ''
    router.push('/login')
  } catch(e) {
    localStorage.removeItem('user_role')
    localStorage.removeItem('user_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_name')
    localStorage.removeItem('real_name')
    router.push('/login')
  }
}

// 组件卸载时清理定时器
onUnmounted(() => {
  if (unreadCountInterval) {
    clearInterval(unreadCountInterval)
  }
})
</script>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  background-color: #f5f7fa;
  color: #303133;
}

.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  height: 100%;
  padding: 0 20px;
}

.logo {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #409EFF;
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  gap: 8px;
  align-items: center;
}

.nav-link {
  text-decoration: none;
  color: #606266;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
  position: relative;
  padding: 8px 16px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link .link-text {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link i {
  font-size: 16px;
}

.nav-link:hover {
  background-color: #f5f7fa;
  color: #409EFF;
}

.nav-link.router-link-active {
  background-color: #ecf5ff;
  color: #409EFF;
  font-weight: 600;
}

/* 移除底部线条样式 */
.nav-link.router-link-active::after {
  display: none;
}

/* 未读徽章样式 */
.nav-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  background: linear-gradient(135deg, #f56c6c 0%, #ff8c8c 100%);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 5px;
  border-radius: 10px;
  min-width: 16px;
  height: 16px;
  line-height: 12px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(245, 108, 108, 0.4);
  animation: badgePulse 2s ease-in-out infinite;
}

@keyframes badgePulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 2px 4px rgba(245, 108, 108, 0.4);
  }
  50% {
    transform: scale(1.1);
    box-shadow: 0 2px 8px rgba(245, 108, 108, 0.6);
  }
}

.nav-link.has-badge {
  padding-right: 32px; /* 为徽章留出空间 */
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 20px;
  flex: 1;
}
</style>
