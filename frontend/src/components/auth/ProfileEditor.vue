<template>
  <div class="profile-editor">
    <div class="profile-header">
      <div class="avatar-section">
        <img :src="avatarUrl" alt="头像" class="avatar" />
        <BaseButton type="secondary" size="small" @click="triggerFileInput">
          更换头像
        </BaseButton>
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          @change="handleAvatarChange"
          style="display: none;"
        />
      </div>
      <div class="basic-info">
        <h3>{{ user.name }}</h3>
        <p class="role-badge" :class="`role-${user.role}`">{{ getRoleName(user.role) }}</p>
      </div>
    </div>

    <form @submit.prevent="handleSubmit" class="profile-form">
      <div class="form-row">
        <div class="form-group">
          <label>姓名</label>
          <BaseInput
            v-model="formData.name"
            placeholder="请输入姓名"
            :error="errors.name"
            @blur="validateField('name')"
          />
        </div>
        <div class="form-group">
          <label>用户名</label>
          <BaseInput
            v-model="formData.username"
            placeholder="请输入用户名"
            :error="errors.username"
            @blur="validateField('username')"
          />
        </div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>邮箱</label>
          <BaseInput
            v-model="formData.email"
            type="email"
            placeholder="请输入邮箱"
            :error="errors.email"
            @blur="validateField('email')"
          />
        </div>
        <div class="form-group">
          <label>电话</label>
          <BaseInput
            v-model="formData.phone"
            placeholder="请输入电话"
            :error="errors.phone"
            @blur="validateField('phone')"
          />
        </div>
      </div>

      <div class="form-group">
        <label>个人简介</label>
        <textarea
          v-model="formData.bio"
          placeholder="介绍一下自己..."
          class="bio-textarea"
          rows="4"
        ></textarea>
      </div>

      <div class="form-actions">
        <BaseButton type="secondary" @click="resetForm">重置</BaseButton>
        <BaseButton
          type="primary"
          :loading="saving"
          :disabled="!isFormChanged"
          @click="handleSubmit"
        >
          {{ saving ? '保存中...' : '保存修改' }}
        </BaseButton>
      </div>
    </form>
  </div>
</template>

<script>
import BaseInput from '../common/ui/BaseInput.vue'
import BaseButton from '../common/ui/BaseButton.vue'

export default {
  name: 'ProfileEditor',
  components: {
    BaseInput,
    BaseButton
  },
  props: {
    user: {
      type: Object,
      required: true
    }
  },
  emits: ['save', 'avatar-change'],
  data() {
    return {
      formData: {
        name: '',
        username: '',
        email: '',
        phone: '',
        bio: ''
      },
      originalData: {},
      errors: {},
      saving: false,
      avatarFile: null
    }
  },
  computed: {
    avatarUrl() {
      return this.user.avatar || '/default-avatar.png'
    },
    isFormChanged() {
      return JSON.stringify(this.formData) !== JSON.stringify(this.originalData)
    }
  },
  watch: {
    user: {
      handler(newUser) {
        this.initializeForm(newUser)
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    initializeForm(user) {
      this.formData = {
        name: user.name || '',
        username: user.username || '',
        email: user.email || '',
        phone: user.phone || '',
        bio: user.bio || ''
      }
      this.originalData = { ...this.formData }
      this.errors = {}
    },

    getRoleName(role) {
      const roleMap = {
        admin: '管理员',
        teacher: '教师',
        student: '学生'
      }
      return roleMap[role] || role
    },

    validateField(field) {
      const value = this.formData[field]?.trim() || ''
      this.errors[field] = ''

      switch (field) {
        case 'name':
          if (!value) this.errors[field] = '姓名不能为空'
          else if (value.length < 2) this.errors[field] = '姓名至少2个字符'
          break
        case 'username':
          if (!value) this.errors[field] = '用户名不能为空'
          else if (value.length < 3) this.errors[field] = '用户名至少3个字符'
          break
        case 'email':
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
          if (value && !emailRegex.test(value)) this.errors[field] = '邮箱格式不正确'
          break
        case 'phone':
          const phoneRegex = /^1[3-9]\d{9}$/
          if (value && !phoneRegex.test(value)) this.errors[field] = '手机号格式不正确'
          break
      }

      return !this.errors[field]
    },

    validateForm() {
      const fields = ['name', 'username', 'email', 'phone']
      return fields.every(field => this.validateField(field))
    },

    triggerFileInput() {
      this.$refs.fileInput.click()
    },

    handleAvatarChange(event) {
      const file = event.target.files[0]
      if (file) {
        this.avatarFile = file
        this.$emit('avatar-change', file)
      }
    },

    async handleSubmit() {
      if (!this.validateForm()) return

      this.saving = true
      try {
        await this.$emit('save', { ...this.formData })
        this.originalData = { ...this.formData }
      } catch (error) {
        console.error('Save error:', error)
      } finally {
        this.saving = false
      }
    },

    resetForm() {
      this.formData = { ...this.originalData }
      this.errors = {}
    }
  }
}
</script>

<style scoped>
.profile-editor {
  max-width: 600px;
  margin: 0 auto;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #eee;
}

.basic-info h3 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-admin {
  background-color: #dc3545;
  color: white;
}

.role-teacher {
  background-color: #28a745;
  color: white;
}

.role-student {
  background-color: #007bff;
  color: white;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
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

.bio-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  outline: none;
}

.bio-textarea:focus {
  border-color: #007bff;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}
</style>