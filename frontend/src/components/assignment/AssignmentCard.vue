<template>
  <div class="assignment-card" :class="{ 'assignment-card--overdue': isOverdue }">
    <div class="assignment-header">
      <div class="assignment-title">
        <h3>{{ assignment.title }}</h3>
        <span class="course-name">{{ assignment.courseName }}</span>
      </div>
      <div class="assignment-status" :class="statusClass">
        {{ statusText }}
      </div>
    </div>

    <div class="assignment-content">
      <p class="assignment-description">{{ assignment.description }}</p>

      <div class="assignment-meta">
        <div class="meta-item">
          <span class="meta-label">截止时间:</span>
          <span class="meta-value">{{ formatDate(assignment.dueDate) }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">总分:</span>
          <span class="meta-value">{{ assignment.totalScore }}分</span>
        </div>
        <div v-if="assignment.submittedAt" class="meta-item">
          <span class="meta-label">提交时间:</span>
          <span class="meta-value">{{ formatDate(assignment.submittedAt) }}</span>
        </div>
        <div v-if="assignment.score !== null" class="meta-item">
          <span class="meta-label">得分:</span>
          <span class="meta-value score">{{ assignment.score }}/{{ assignment.totalScore }}</span>
        </div>
      </div>
    </div>

    <div class="assignment-actions">
      <BaseButton
        v-if="canSubmit"
        type="primary"
        size="small"
        @click="$emit('submit')"
      >
        提交作业
      </BaseButton>
      <BaseButton
        v-if="canViewSubmission"
        type="secondary"
        size="small"
        @click="$emit('view-submission')"
      >
        查看提交
      </BaseButton>
      <BaseButton
        v-if="canGrade"
        type="success"
        size="small"
        @click="$emit('grade')"
      >
        批改作业
      </BaseButton>
      <BaseButton
        type="secondary"
        size="small"
        @click="$emit('view-detail')"
      >
        查看详情
      </BaseButton>
    </div>
  </div>
</template>

<script>
import BaseButton from '../common/ui/BaseButton.vue'

export default {
  name: 'AssignmentCard',
  components: {
    BaseButton
  },
  props: {
    assignment: {
      type: Object,
      required: true
    },
    userRole: {
      type: String,
      default: 'student'
    }
  },
  emits: ['submit', 'view-submission', 'grade', 'view-detail'],
  computed: {
    isOverdue() {
      return new Date(assignment.dueDate) < new Date() && !assignment.submittedAt
    },
    statusText() {
      if (this.assignment.score !== null) return '已批改'
      if (this.assignment.submittedAt) return '已提交'
      if (this.isOverdue) return '已逾期'
      return '待提交'
    },
    statusClass() {
      if (this.assignment.score !== null) return 'status-graded'
      if (this.assignment.submittedAt) return 'status-submitted'
      if (this.isOverdue) return 'status-overdue'
      return 'status-pending'
    },
    canSubmit() {
      return this.userRole === 'student' &&
             !this.assignment.submittedAt &&
             !this.isOverdue
    },
    canViewSubmission() {
      return this.assignment.submittedAt
    },
    canGrade() {
      return this.userRole === 'teacher' &&
             this.assignment.submittedAt &&
             this.assignment.score === null
    }
  },
  methods: {
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.assignment-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: box-shadow 0.2s;
}

.assignment-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.assignment-card--overdue {
  border-color: #dc3545;
  background-color: #fff5f5;
}

.assignment-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.assignment-title h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #333;
}

.course-name {
  color: #666;
  font-size: 14px;
}

.assignment-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-graded {
  background-color: #28a745;
  color: white;
}

.status-submitted {
  background-color: #007bff;
  color: white;
}

.status-overdue {
  background-color: #dc3545;
  color: white;
}

.status-pending {
  background-color: #ffc107;
  color: #212529;
}

.assignment-content {
  margin-bottom: 16px;
}

.assignment-description {
  color: #555;
  margin-bottom: 12px;
  line-height: 1.5;
}

.assignment-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
  font-size: 14px;
}

.meta-item {
  display: flex;
  gap: 4px;
}

.meta-label {
  color: #666;
}

.meta-value {
  color: #333;
  font-weight: 500;
}

.meta-value.score {
  color: #28a745;
  font-weight: 600;
}

.assignment-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>