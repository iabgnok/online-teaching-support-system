<template>
  <el-container class="app-layout">
    <el-header class="main-header" height="60px">
      <div class="header-content">
        <h1 class="logo">在线教学支持系统</h1>
        <div class="nav-links">
           <!-- Student Links -->
           <template v-if="userRole !== 'teacher'">
               <router-link to="/" class="nav-link">首页</router-link>
               <router-link to="/courses" class="nav-link">课程</router-link>
               <router-link to="/schedule" class="nav-link">日程</router-link>
           </template>

           <!-- Teacher Links -->
           <template v-else>
               <router-link to="/teacher/dashboard" class="nav-link">工作台</router-link>
               <!-- Add more teacher specific links here -->
           </template>

           <!-- Common Links -->
           <router-link to="/forum" class="nav-link">论坛</router-link>
           <router-link to="/messages" class="nav-link">站内信</router-link>
           <a href="#" @click.prevent="logout" class="nav-link">退出</a>
        </div>
      </div>
    </el-header>
    <el-main class="main-content">
      <router-view :key="$route.fullPath"></router-view>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, watchEffect } from 'vue'
import api from './api'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const userRole = ref('')

// Simple way to keep role updated without a store: check on route change
watchEffect(() => {
    // Dependency on route.path ensures this runs on navigation
    const path = route.path 
    userRole.value = localStorage.getItem('user_role') || 'student'
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
