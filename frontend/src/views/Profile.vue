<template>
  <div class="profile-page">
    <el-card>
      <template #header>
        <h2>👤 账户信息管理</h2>
      </template>

      <el-form :model="profileForm" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="profileForm.username" disabled />
        </el-form-item>

        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="profileForm.real_name" />
        </el-form-item>

        <el-form-item label="角色">
          <el-tag :type="getRoleType(profileForm.role)">
            {{ getRoleLabel(profileForm.role) }}
          </el-tag>
        </el-form-item>

        <el-form-item label="电话" prop="phone">
          <el-input v-model="profileForm.phone" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="profileForm.email" />
        </el-form-item>

        <el-divider content-position="left">修改密码</el-divider>

        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password />
        </el-form-item>

        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="updateProfile" :loading="saving">
            保存修改
          </el-button>
          <el-button @click="$router.back()">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const formRef = ref(null)
const saving = ref(false)

const profileForm = ref({
  username: '',
  real_name: '',
  role: '',
  phone: '',
  email: ''
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const formRules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  new_password: [
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    {
      validator: (rule, value, callback) => {
        if (value && value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const getRoleLabel = (role) => {
  const labels = { admin: '管理员', teacher: '教师', student: '学生' }
  return labels[role] || role
}

const getRoleType = (role) => {
  const types = { admin: 'danger', teacher: 'warning', student: 'success' }
  return types[role] || 'info'
}

const loadProfile = async () => {
  try {
    const response = await api.get('/me')
    const user = response.data.user
    profileForm.value = {
      username: user.username,
      real_name: user.real_name,
      role: user.role,
      phone: user.phone || '',
      email: user.email || ''
    }
  } catch (error) {
    console.error('Failed to load profile:', error)
    ElMessage.error('加载账户信息失败')
  }
}

const updateProfile = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    saving.value = true
    try {
      // 更新基本信息
      await api.put('/profile', {
        real_name: profileForm.value.real_name,
        phone: profileForm.value.phone,
        email: profileForm.value.email
      })

      // 如果填写了密码，则修改密码
      if (passwordForm.value.old_password && passwordForm.value.new_password) {
        await api.post('/change-password', {
          old_password: passwordForm.value.old_password,
          new_password: passwordForm.value.new_password
        })
        ElMessage.success('信息和密码已更新')
        // 清空密码表单
        passwordForm.value = {
          old_password: '',
          new_password: '',
          confirm_password: ''
        }
      } else {
        ElMessage.success('信息已更新')
      }

      // 重新加载
      loadProfile()
    } catch (error) {
      console.error('Failed to update profile:', error)
      ElMessage.error(error.response?.data?.error || '更新失败')
    } finally {
      saving.value = false
    }
  })
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

h2 {
  margin: 0;
  font-size: 20px;
}
</style>
