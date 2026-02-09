<template>
  <div class="login-wrapper">
    <div class="login-container">
      <div class="login-brand">
        <h1>在线教学支持系统</h1>
        <p>让学习更高效，让教学更便捷</p>
      </div>

      <div class="login-form">
        <el-form
          :model="loginForm"
          :rules="loginRules"
          ref="loginFormRef"
          label-width="0px"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名"
              prefix-icon="el-icon-user"
              clearable
              size="large"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              prefix-icon="el-icon-lock"
              clearable
              size="large"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              @click="handleLogin"
              style="width: 100%"
            >
              {{ loading ? '登录中...' : '登录' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const loginFormRef = ref(null)
    const loading = ref(false)

    const loginForm = reactive({
      username: '',
      password: ''
    })

    const loginRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }

    const handleLogin = async () => {
      if (!loginFormRef.value) return

      try {
        await loginFormRef.value.validate()
      } catch (error) {
        return
      }

      loading.value = true

      try {
        const res = await api.post('/login', loginForm)
        const user = res.data.user
        const token = res.data.token

        // Store user data for global access
        localStorage.setItem('user_token', token)
        localStorage.setItem('user_role', user.role)
        localStorage.setItem('user_id', user.id)
        localStorage.setItem('user_name', user.real_name || user.username)
        localStorage.setItem('username', user.username)
        localStorage.setItem('real_name', user.real_name)

        ElMessage.success('登录成功')

        if (user.role === 'teacher') {
          router.push('/teacher/dashboard')
        } else {
          router.push('/')
        }
      } catch (error) {
        console.error('Login error detail:', error)
        if (error.response && error.response.data && error.response.data.error) {
          ElMessage.error('登录失败: ' + error.response.data.error)
        } else {
          ElMessage.error('登录失败: 无法连接到服务器或发生未知错误。')
        }
      } finally {
        loading.value = false
      }
    }

    return {
      loginFormRef,
      loading,
      loginForm,
      loginRules,
      handleLogin
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
  padding: 20px;
}

.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  max-width: 420px;
  width: 100%;
  background: rgba(255, 255, 255, 0.98);
  padding: 48px 40px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-brand {
  text-align: center;
  color: #1a365d;
}

.login-brand h1 {
  margin: 0 0 12px 0;
  font-size: 2.4rem;
  font-weight: 700;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.login-brand p {
  margin: 0;
  font-size: 1.1rem;
  color: #64748b;
  font-weight: 400;
  opacity: 0.9;
}

.login-form {
  width: 100%;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 24px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.08);
  border: 2px solid rgba(37, 99, 235, 0.1);
  background: rgba(255, 255, 255, 0.95);
  transition: all 0.3s ease;
  padding: 12px 16px;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.login-form :deep(.el-input__inner) {
  font-size: 16px;
  color: #1e293b;
  font-weight: 500;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #94a3b8;
  font-weight: 400;
}

.login-form :deep(.el-button--primary) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border: none;
  border-radius: 12px;
  height: 52px;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.login-form :deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.35);
}

.login-form :deep(.el-button--primary:active) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
}

.login-form :deep(.el-button--primary.is-loading) {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  box-shadow: 0 2px 8px rgba(100, 116, 139, 0.25);
}

/* 图标样式 */
.login-form :deep(.el-input__prefix) {
  margin-right: 8px;
}

.login-form :deep(.el-input__prefix svg) {
  color: #64748b;
  width: 20px;
  height: 20px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-container {
    padding: 32px 24px;
    margin: 16px;
    border-radius: 12px;
  }

  .login-brand h1 {
    font-size: 2rem;
  }

  .login-brand p {
    font-size: 1rem;
  }

  .login-form :deep(.el-button--primary) {
    height: 48px;
    font-size: 15px;
  }
}

/* 动画效果 */
.login-container {
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-form :deep(.el-input__wrapper) {
  animation: fadeInScale 0.4s ease-out 0.2s both;
}

.login-form :deep(.el-button--primary) {
  animation: fadeInScale 0.4s ease-out 0.4s both;
}

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
