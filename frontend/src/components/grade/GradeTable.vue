<template>
  <div class="grade-table">
    <table>
      <thead>
        <tr>
          <th>学生姓名</th>
          <th v-for="category in gradeCategories" :key="category.id">
            {{ category.name }}
          </th>
          <th>总分</th>
          <th v-if="editable">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="student in students" :key="student.id">
          <td>{{ student.name }}</td>
          <td v-for="category in gradeCategories" :key="category.id">
            <span v-if="!editable">{{ getGrade(student.id, category.id) }}</span>
            <input
              v-else
              type="number"
              :value="getGrade(student.id, category.id)"
              @input="updateGrade(student.id, category.id, $event.target.value)"
              min="0"
              max="100"
            />
          </td>
          <td>{{ calculateTotal(student.id) }}</td>
          <td v-if="editable">
            <button @click="saveGrades(student.id)">保存</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'GradeTable',
  props: {
    students: {
      type: Array,
      default: () => []
    },
    gradeCategories: {
      type: Array,
      default: () => []
    },
    grades: {
      type: Object,
      default: () => ({})
    },
    editable: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      tempGrades: {}
    }
  },
  methods: {
    getGrade(studentId, categoryId) {
      return this.tempGrades[studentId]?.[categoryId] || this.grades[studentId]?.[categoryId] || ''
    },
    updateGrade(studentId, categoryId, value) {
      if (!this.tempGrades[studentId]) {
        this.tempGrades[studentId] = {}
      }
      this.tempGrades[studentId][categoryId] = value
    },
    calculateTotal(studentId) {
      const studentGrades = this.grades[studentId] || {}
      return Object.values(studentGrades).reduce((sum, grade) => sum + (parseFloat(grade) || 0), 0)
    },
    saveGrades(studentId) {
      this.$emit('save', studentId, this.tempGrades[studentId])
      delete this.tempGrades[studentId]
    }
  }
}
</script>

<style scoped>
.grade-table {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f5f5f5;
}

input {
  width: 60px;
}
</style>