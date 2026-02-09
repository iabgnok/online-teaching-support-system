<template>
  <div class="login-form">
    <div class="login-header">
      <h2>登录教学支持系统</h2>
    </div>

    <form @submit.prevent="handleSubmit" class="login-form-content">
      <div class="form-group">
        <label for="username">用户名</label>
        <BaseInput
          id="username"
          v-model="formData.username"
          placeholder="请输入用户名"
          :error="errors.username"
          @blur="validateField('username')"
        />
      </div>

      <div class="form-group">
        <label for="password">密码</label>
        <BaseInput
          id="password"
          v-model="formData.password"
          type="password"
          placeholder="请输入密码"
          :error="errors.password"
          @blur="validateField('password')"
        />
      </div>

      <div class="form-actions">
        <BaseButton
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!isFormValid"
          style="width: 100%;"
        >
          {{ loading ? '登录中...' : '登录' }}
        </BaseButton>
      </div>

      <div class="form-footer">
        <p>忘记密码？请联系管理员</p>
      </div>
    </form>
  </div>
</template>

<script>
import BaseInput from '../common/ui/BaseInput.vue'
import BaseButton from '../common/ui/BaseButton.vue'

export default {
  name: 'LoginForm',
  components: {
    BaseInput,
    BaseButton
  },
  emits: ['login'],
  data() {
    return {
      formData: {
        username: '',
        password: ''
      },
      errors: {
        username: '',
        password: ''
      },
      loading: false
    }
  },
  computed: {
    isFormValid() {
      return this.formData.username.trim() &&
             this.formData.password.trim() &&
             !this.errors.username &&
             !this.errors.password
    }
  },
  methods: {
    validateField(field) {
      const value = this.formData[field].trim()
      this.errors[field] = ''

      if (!value) {
        this.errors[field] = `${field === 'username' ? '用户名' : '密码'}不能为空`
        return false
      }

      if (field === 'username' && value.length < 3) {
        this.errors[field] = '用户名至少3个字符'
        return false
      }

      if (field === 'password' && value.length < 6) {
        this.errors[field] = '密码至少6个字符'
        return false
      }

      return true
    },

    validateForm() {
      const usernameValid = this.validateField('username')
      const passwordValid = this.validateField('password')
      return usernameValid && passwordValid
    },

    async handleSubmit() {
      if (!this.validateForm()) {
        return
      }

      this.loading = true
      try {
        await this.$emit('login', { ...this.formData })
      } catch (error) {
        console.error('Login error:', error)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 40px 20px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h2 {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.login-form-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #555;
}

.form-actions {
  margin-top: 8px;
}

.form-footer {
  text-align: center;
  margin-top: 16px;
}

.form-footer p {
  color: #666;
  font-size: 14px;
  margin: 0;
}
</style>