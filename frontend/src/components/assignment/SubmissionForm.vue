<template>
  <BaseModal
    :visible="visible"
    title="提交作业"
    width="600px"
    @update:visible="$emit('update:visible', $event)"
  >
    <div class="submission-form">
      <div class="assignment-info">
        <h4>{{ assignment.title }}</h4>
        <p class="description">{{ assignment.description }}</p>
        <div class="meta">
          <span>截止时间: {{ formatDate(assignment.dueDate) }}</span>
          <span>总分: {{ assignment.totalScore }}</span>
        </div>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>作业文件</label>
          <div class="file-upload">
            <input
              ref="fileInput"
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt,.zip,.rar"
              @change="handleFileChange"
              style="display: none;"
            />
            <BaseButton type="secondary" @click="triggerFileInput">
              选择文件
            </BaseButton>
            <span v-if="selectedFiles.length === 0" class="file-hint">
              支持PDF、Word、TXT、压缩包等格式
            </span>
          </div>

          <div v-if="selectedFiles.length > 0" class="file-list">
            <div
              v-for="(file, index) in selectedFiles"
              :key="index"
              class="file-item"
            >
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">({{ formatFileSize(file.size) }})</span>
              <button type="button" @click="removeFile(index)" class="remove-btn">×</button>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>提交说明</label>
          <textarea
            v-model="comment"
            placeholder="添加提交说明（可选）"
            class="comment-textarea"
            rows="3"
          ></textarea>
        </div>

        <div class="form-actions">
          <BaseButton type="secondary" @click="$emit('update:visible', false)">
            取消
          </BaseButton>
          <BaseButton
            type="primary"
            :loading="submitting"
            :disabled="!canSubmit"
            @click="handleSubmit"
          >
            {{ submitting ? '提交中...' : '提交作业' }}
          </BaseButton>
        </div>
      </form>
    </div>
  </BaseModal>
</template>

<script>
import BaseModal from '../common/ui/BaseModal.vue'
import BaseButton from '../common/ui/BaseButton.vue'

export default {
  name: 'SubmissionForm',
  components: {
    BaseModal,
    BaseButton
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    assignment: {
      type: Object,
      required: true
    }
  },
  emits: ['update:visible', 'submit'],
  data() {
    return {
      selectedFiles: [],
      comment: '',
      submitting: false
    }
  },
  computed: {
    canSubmit() {
      return this.selectedFiles.length > 0 && !this.submitting
    }
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click()
    },

    handleFileChange(event) {
      const files = Array.from(event.target.files)
      // 检查文件大小（限制50MB）
      const maxSize = 50 * 1024 * 1024
      const validFiles = files.filter(file => {
        if (file.size > maxSize) {
          this.$message.warning(`${file.name} 文件过大，请选择小于50MB的文件`)
          return false
        }
        return true
      })

      this.selectedFiles.push(...validFiles)
    },

    removeFile(index) {
      this.selectedFiles.splice(index, 1)
    },

    formatFileSize(bytes) {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },

    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    async handleSubmit() {
      if (!this.canSubmit) return

      this.submitting = true
      try {
        const formData = new FormData()
        this.selectedFiles.forEach(file => {
          formData.append('files', file)
        })
        formData.append('comment', this.comment)
        formData.append('assignmentId', this.assignment.id)

        await this.$emit('submit', formData)
        this.$emit('update:visible', false)
        this.resetForm()
      } catch (error) {
        console.error('Submit error:', error)
      } finally {
        this.submitting = false
      }
    },

    resetForm() {
      this.selectedFiles = []
      this.comment = ''
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    }
  }
}
</script>

<style scoped>
.submission-form {
  padding: 0;
}

.assignment-info {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.assignment-info h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.description {
  color: #666;
  margin-bottom: 8px;
  line-height: 1.5;
}

.meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #666;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.file-upload {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-hint {
  color: #999;
  font-size: 14px;
}

.file-list {
  margin-top: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 4px;
}

.file-name {
  flex: 1;
  color: #333;
}

.file-size {
  color: #666;
  font-size: 12px;
}

.remove-btn {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.remove-btn:hover {
  background: #ffeaea;
}

.comment-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  outline: none;
}

.comment-textarea:focus {
  border-color: #007bff;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>