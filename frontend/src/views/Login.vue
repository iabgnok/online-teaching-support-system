<template>
  <div class="login-wrapper">
    <div class="login-box">
      <div class="login-header">
        <h2>欢迎登录</h2>
        <p>在线教学支持系统</p>
      </div>
      
      <el-form :model="form" class="login-form" size="large">
        <el-form-item>
          <el-input 
            v-model="form.username" 
            placeholder="用户名 / 学号 / 工号"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item>
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" class="login-btn" @click="onSubmit" :loading="loading">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>首次登录? 请联系管理员获取账号</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import api from '../api'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  password: ''
})

const onSubmit = async () => {
  if (!form.username || !form.password) {
      alert('请输入用户名和密码')
      return
  }
  loading.value = true
  try {
    const res = await api.post('/login', form)
    const user = res.data.user
    const token = res.data.token
    
    // Store user data for global access
    localStorage.setItem('user_token', token)
    localStorage.setItem('user_role', user.role)
    localStorage.setItem('user_id', user.id)
    localStorage.setItem('user_name', user.real_name || user.username)
    localStorage.setItem('username', user.username)
    localStorage.setItem('real_name', user.real_name)
    
    if (user.role === 'teacher') {
      router.push('/teacher/dashboard')
    } else {
      router.push('/')
    }
  } catch (error) {
    loading.value = false
    console.error('Login error detail:', error)
    if (error.response && error.response.data && error.response.data.error) {
      alert('登录失败: ' + error.response.data.error)
    } else {
      alert('登录失败: 无法连接到服务器或发生未知错误。')
    }
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.login-box {
  width: 100%;
  max-width: 400px;
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.05);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.login-header p {
  margin: 10px 0 0;
  color: #909399;
  font-size: 14px;
}

.login-form {
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
  font-weight: 600;
  letter-spacing: 2px;
}

.login-footer {
  text-align: center;
  font-size: 13px;
  color: #C0C4CC;
}
</style>
