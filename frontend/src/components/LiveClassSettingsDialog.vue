<template>
  <el-dialog
    v-model="visible"
    title="课堂设置"
    width="500px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="课堂标题" prop="title">
        <el-input 
          v-model="form.title" 
          placeholder="请输入课堂标题"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="课堂描述" prop="description">
        <el-input 
          v-model="form.description" 
          type="textarea"
          :rows="3"
          placeholder="请输入课堂描述（选填）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="预计时长">
        <el-select v-model="form.duration" placeholder="选择课堂时长">
          <el-option label="30分钟" :value="30" />
          <el-option label="45分钟" :value="45" />
          <el-option label="60分钟" :value="60" />
          <el-option label="90分钟" :value="90" />
          <el-option label="120分钟" :value="120" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="通知方式">
        <el-checkbox-group v-model="form.notifyMethods">
          <el-checkbox label="群消息">在班级群中发送课堂入口</el-checkbox>
          <el-checkbox label="群公告">更新群公告</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="loading">
          开始授课
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  conversation: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const formRef = ref(null)
const loading = ref(false)

const form = ref({
  title: '',
  description: '',
  duration: 45,
  notifyMethods: ['群消息', '群公告']
})

const rules = {
  title: [
    { required: true, message: '请输入课堂标题', trigger: 'blur' },
    { min: 2, max: 50, message: '标题长度在2-50个字符', trigger: 'blur' }
  ]
}

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 监听对话变化，自动填充标题
watch(() => props.conversation, (newVal) => {
  if (newVal && newVal.title) {
    form.value.title = `${newVal.title} - 在线授课`
  }
}, { immediate: true })

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
}

const handleConfirm = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    
    emit('confirm', {
      ...form.value,
      class_id: props.conversation?.class_id
    })
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid #e5e5e5;
  padding: 16px 20px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-dialog__footer) {
  border-top: 1px solid #e5e5e5;
  padding: 12px 20px;
}
</style>
