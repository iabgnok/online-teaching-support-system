<template>
  <div class="course-list-page">
    <h2>我的课程列表</h2>
     <el-table :data="classes" style="width: 100%" v-loading="loading">
        <el-table-column prop="course_code" label="课程代码" width="120" />
        <el-table-column prop="course_name" label="课程名称" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="teacher_name" label="教师" width="120" />
        <el-table-column prop="semester" label="学期" width="120" />
        <el-table-column prop="time" label="上课时间" width="200" />
        <el-table-column label="操作" width="120">
            <template #default="scope">
                <el-button size="small" type="primary" @click="viewCourse(scope.row.class_id)">进入课程</el-button>
            </template>
        </el-table-column>
     </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../../api'

const router = useRouter()
const classes = ref([])
const loading = ref(true)

const fetchClasses = async () => {
    try {
        const res = await api.get('/classes/my')
        classes.value = res.data
    } catch(e) { console.error(e)}
    finally { loading.value = false }
}

const viewCourse = (id) => {
    router.push(`/course/${id}`)
}

onMounted(() => {
    fetchClasses()
})
</script>

<style scoped>
.course-list-page {
    padding: 20px;
}
</style>
