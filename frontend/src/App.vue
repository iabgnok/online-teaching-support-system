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
            >
              {{ link.label }}
            </router-link>
            <a href="#" @click.prevent="logout" class="nav-link">退出</a>
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
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from './api'

const router = useRouter()
const route = useRoute()
const userRole = ref(localStorage.getItem('user_role') || 'student')

// 监听路由变化，实时更新用户角色 (Login.vue 登录后会跳转，触发此更新)
import { watch } from 'vue'
watch(() => route.path, () => {
  const storedRole = localStorage.getItem('user_role')
  if (storedRole) {
    userRole.value = storedRole
  }
})

const showLayout = computed(() => {
  return route.path !== '/login'
})

const navigationLinks = computed(() => {
  if (userRole.value === 'admin') {
    return [
      { path: '/admin/dashboard', label: '管理员控制台' },
      { path: '/messages', label: '站内信' },
      { path: '/profile', label: '账户信息' }
    ]
  } else if (userRole.value === 'teacher') {
    return [
      { path: '/teacher/dashboard', label: '工作台' },
      { path: '/forum', label: '论坛' },
      { path: '/messages', label: '站内信' },
      { path: '/profile', label: '账户信息' }
    ]
  } else {
    return [
      { path: '/', label: '首页' },
      { path: '/schedule', label: '日程' },
      { path: '/my-grades', label: '我的成绩' },
      { path: '/forum', label: '论坛' },
      { path: '/messages', label: '站内信' },
      { path: '/profile', label: '账户信息' }
    ]
  }
})

const logout = async () => {
  try {
    await api.post('/logout')
    localStorage.removeItem('user_role')
    userRole.value = ''
    router.push('/login')
  } catch(e) {
    localStorage.removeItem('user_role')
    router.push('/login')
  }
}
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
  gap: 30px;
  align-items: center;
}

.nav-link {
  text-decoration: none;
  color: #606266;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s;
  position: relative;
}

.nav-link:hover, .nav-link.router-link-active {
  color: #409EFF;
}

.nav-link.router-link-active::after {
  content: '';
  position: absolute;
  bottom: -21px; /* Adjust based on header height 60px / 2 approx */
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #409EFF;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 20px;
  flex: 1;
}
</style>
