<template>
  <div class="course-card" @click="handleClick">
    <div class="course-header">
      <h3>{{ course.name }}</h3>
      <span class="course-code">{{ course.code }}</span>
    </div>
    <div class="course-info">
      <p class="teacher">教师: {{ course.teacher }}</p>
      <p class="schedule">{{ course.schedule }}</p>
    </div>
    <div class="course-stats">
      <span class="stat">学生: {{ course.studentCount }}</span>
      <span class="stat">作业: {{ course.assignmentCount }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CourseCard',
  props: {
    course: {
      type: Object,
      required: true
    }
  },
  methods: {
    handleClick() {
      this.$emit('select', this.course)
    }
  }
}
</script>

<style scoped>
.course-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.course-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.course-code {
  color: #666;
  font-size: 0.9em;
}

.course-info {
  margin-bottom: 8px;
}

.course-stats {
  display: flex;
  gap: 16px;
  font-size: 0.9em;
  color: #666;
}
</style>